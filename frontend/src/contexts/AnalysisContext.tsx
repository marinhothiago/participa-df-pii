import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { type AnalysisResult, type BatchResult, api } from '@/lib/api';

export interface AnalysisHistoryItem {
  id: string;
  pedidoId: string; // ID do pedido original da API/planilha
  requestNumber: number;
  timestamp: Date;
  date: string;
  time: string;
  type: 'individual' | 'batch';
  text: string;
  classification: 'PÚBLICO' | 'NÃO PÚBLICO';
  probability: number;
  riskLevel: 'critical' | 'high' | 'moderate' | 'low' | 'safe';
  risco: string; // Risco original da API
  details: { tipo: string; valor: string }[];
}

export interface RiskDistribution {
  critical: number;
  high: number;
  moderate: number;
  low: number;
  safe: number;
}

export interface PIITypeCounts {
  [key: string]: number;
}

export interface SessionMetrics {
  totalProcessed: number;
  publicCount: number;
  nonPublicCount: number;
  averageConfidence: number;
  riskDistribution: RiskDistribution;
  piiTypeCounts: PIITypeCounts;
}

export interface GlobalCounters {
  siteVisits: number;
  totalClassificationRequests: number;
}

interface AnalysisContextType {
  history: AnalysisHistoryItem[];
  metrics: SessionMetrics;
  counters: GlobalCounters;
  isProcessing: boolean;
  addAnalysisResult: (result: AnalysisResult, text: string, type: 'individual' | 'batch', pedidoId?: string) => void;
  addBatchResults: (results: BatchResult[]) => void;
  clearHistory: () => void;
  incrementClassificationRequests: (count?: number) => void;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

const VISIT_SESSION_KEY = 'participa_df_visited';

// Converte o risco da API para o nível interno
export function getRiskLevelFromRisco(risco: string): 'critical' | 'high' | 'moderate' | 'low' | 'safe' {
  const riscoUpper = risco?.toUpperCase() || '';
  if (riscoUpper === 'CRÍTICO' || riscoUpper === 'CRITICO') return 'critical';
  if (riscoUpper === 'ALTO') return 'high';
  if (riscoUpper === 'MODERADO') return 'moderate';
  if (riscoUpper === 'BAIXO') return 'low';
  if (riscoUpper === 'SEGURO') return 'safe';
  return 'safe';
}

// Fallback para cálculo por probabilidade (quando não há risco da API)
export function getRiskLevelFromProbability(probability: number, classification: string): 'critical' | 'high' | 'moderate' | 'low' | 'safe' {
  if (classification === 'PÚBLICO') {
    return 'safe';
  }
  if (probability >= 0.90) return 'critical';
  if (probability >= 0.70) return 'high';
  if (probability >= 0.40) return 'moderate';
  if (probability >= 0.20) return 'low';
  return 'safe';
}

export function getRiskColor(riskLevel: 'critical' | 'high' | 'moderate' | 'low' | 'safe'): string {
  switch (riskLevel) {
    case 'critical': return 'hsl(0, 80%, 25%)';  // Vermelho escuro
    case 'high': return 'hsl(0, 80%, 60%)';      // Vermelho claro
    case 'moderate': return 'hsl(45, 100%, 45%)'; // Amarelo
    case 'low': return 'hsl(210, 80%, 50%)';      // Azul
    case 'safe': return 'hsl(120, 60%, 40%)';     // Verde
  }
}

export function getRiskLabel(riskLevel: 'critical' | 'high' | 'moderate' | 'low' | 'safe'): string {
  switch (riskLevel) {
    case 'critical': return 'Crítico';
    case 'high': return 'Alto';
    case 'moderate': return 'Moderado';
    case 'low': return 'Baixo';
    case 'safe': return 'Seguro';
  }
}

export function getRiskBgClass(riskLevel: 'critical' | 'high' | 'moderate' | 'low' | 'safe'): string {
  switch (riskLevel) {
    case 'critical': return 'bg-red-800 text-white border-red-900';
    case 'high': return 'bg-red-100 text-red-700 border-red-300';
    case 'moderate': return 'bg-yellow-100 text-yellow-900 border-yellow-400';
    case 'low': return 'bg-blue-100 text-blue-700 border-blue-300';
    case 'safe': return 'bg-green-100 text-green-700 border-green-300';
  }
}

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
  const [counters, setCounters] = useState<GlobalCounters>({ siteVisits: 0, totalClassificationRequests: 0 });
  const [requestCounter, setRequestCounter] = useState(1);

  // Carregar contadores do backend e registrar visita (uma vez por sessão)
  useEffect(() => {
    const loadGlobalStats = async () => {
      // Buscar stats atuais do backend
      const stats = await api.getStats();
      setCounters({
        siteVisits: stats.site_visits,
        totalClassificationRequests: stats.classification_requests,
      });
      
      // Registrar visita uma vez por sessão
      const hasVisited = sessionStorage.getItem(VISIT_SESSION_KEY);
      if (!hasVisited) {
        sessionStorage.setItem(VISIT_SESSION_KEY, 'true');
        await api.registerVisit();
        // Atualizar contador local após registrar
        setCounters(prev => ({ ...prev, siteVisits: prev.siteVisits + 1 }));
      }
    };
    
    loadGlobalStats();
    
    // Atualizar stats a cada 30 segundos para refletir outras sessões
    const interval = setInterval(async () => {
      const stats = await api.getStats();
      setCounters({
        siteVisits: stats.site_visits,
        totalClassificationRequests: stats.classification_requests,
      });
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Função para atualizar o contador de requisições após análise
  // Agora apenas atualiza o estado local pois o backend já incrementa automaticamente
  const incrementClassificationRequests = useCallback((count: number = 1) => {
    setCounters(prev => ({
      ...prev,
      totalClassificationRequests: prev.totalClassificationRequests + count,
    }));
  }, []);

  const calculateMetrics = useCallback((historyItems: AnalysisHistoryItem[]): SessionMetrics => {
    const riskDistribution: RiskDistribution = {
      critical: 0,
      high: 0,
      moderate: 0,
      low: 0,
      safe: 0,
    };

    const piiTypeCounts: PIITypeCounts = {};
    let publicCount = 0;
    let nonPublicCount = 0;
    let totalConfidence = 0;

    historyItems.forEach(item => {
      if (item.classification === 'PÚBLICO') {
        publicCount++;
        // Usar probabilidade como recebida (já normalizada entre 0-1)
        totalConfidence += item.probability;
      } else {
        nonPublicCount++;
        totalConfidence += item.probability;
      }

      riskDistribution[item.riskLevel]++;

      item.details.forEach(detail => {
        const tipo = detail.tipo.toUpperCase();
        piiTypeCounts[tipo] = (piiTypeCounts[tipo] || 0) + 1;
      });
    });

    const averageConfidence = historyItems.length > 0 ? totalConfidence / historyItems.length : 0;

    return {
      totalProcessed: historyItems.length,
      publicCount,
      nonPublicCount,
      averageConfidence,
      riskDistribution,
      piiTypeCounts,
    };
  }, []);

  const metrics = calculateMetrics(history);

  const formatDateTime = (date: Date) => {
    return {
      date: date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' }),
      time: date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
    };
  };

  const addAnalysisResult = useCallback((result: AnalysisResult, text: string, type: 'individual' | 'batch', pedidoId?: string) => {
    const now = new Date();
    const { date, time } = formatDateTime(now);
    
    const classification = result.classificacao === 'PÚBLICO' ? 'PÚBLICO' : 'NÃO PÚBLICO';
    const probability = result.confianca ?? 0;
    const risco = result.risco ?? 'SEGURO';
    const riskLevel = getRiskLevelFromRisco(risco);

    const newItem: AnalysisHistoryItem = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      pedidoId: pedidoId || String(requestCounter),
      requestNumber: requestCounter,
      timestamp: now,
      date,
      time,
      type,
      text: text.slice(0, 200),
      classification,
      probability,
      riskLevel,
      risco,
      details: result.detalhes || [],
    };

    setRequestCounter(prev => prev + 1);
    setHistory(prev => [newItem, ...prev].slice(0, 100));
  }, [requestCounter]);

  const addBatchResults = useCallback((results: BatchResult[]) => {
    const now = new Date();
    const currentCounter = requestCounter;
    
    const newItems: AnalysisHistoryItem[] = results.map((result, index) => {
      const itemTime = new Date(now.getTime() + index);
      const { date, time } = formatDateTime(itemTime);
      
      const classification: 'PÚBLICO' | 'NÃO PÚBLICO' = result.classification === 'public' ? 'PÚBLICO' : 'NÃO PÚBLICO';
      const risco = result.risco ?? 'SEGURO';
      const riskLevel = getRiskLevelFromRisco(risco);

      const item: AnalysisHistoryItem = {
        id: `batch-${Date.now()}-${index}`,
        pedidoId: result.id, // ID original da API/planilha
        requestNumber: currentCounter + index,
        timestamp: itemTime,
        date,
        time,
        type: 'batch' as const,
        text: result.text_preview,
        classification,
        probability: result.probability,
        riskLevel,
        risco,
        details: result.entities.map(e => ({ tipo: e.type, valor: e.value })),
      };
      return item;
    });

    // Manter ordem original de processamento (sem ordenação)
    setRequestCounter(prev => prev + results.length);
    setHistory(prev => [...newItems, ...prev].slice(0, 100));
  }, [requestCounter]);

  const clearHistory = useCallback(() => {
    setHistory([]);
  }, []);

  return (
    <AnalysisContext.Provider value={{
      history,
      metrics,
      counters,
      isProcessing: false,
      addAnalysisResult,
      addBatchResults,
      clearHistory,
      incrementClassificationRequests,
    }}>
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const context = useContext(AnalysisContext);
  if (context === undefined) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
}
