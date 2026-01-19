// ============================================
// Motor PII - Participa DF
// Camada de Serviços para API de Detecção
// ============================================

// URL da API - com detecção automática de backend local
const PRODUCTION_API_URL = 'https://marinhothiago-desafio-participa-df.hf.space';
const LOCAL_API_URL = 'http://localhost:7860'; // Porta padrão do backend (HuggingFace Spaces)
const API_TIMEOUT = 15000; // 15 segundos (modelo de IA pode demorar)
const MAX_RETRIES = 1; // Retry automático uma vez se falhar
const LOCAL_DETECTION_TIMEOUT = 2000; // 2 segundos para detectar backend local

// Detecção automática de backend local
let API_BASE_URL = PRODUCTION_API_URL;
let detectionAttempted = false;

async function detectLocalBackend(): Promise<void> {
  if (detectionAttempted) return;
  detectionAttempted = true;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), LOCAL_DETECTION_TIMEOUT);

    const response = await fetch(`${LOCAL_API_URL}/health`, {
      signal: controller.signal,
      headers: { 'Content-Type': 'application/json' }
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      API_BASE_URL = LOCAL_API_URL;
      console.log(`✅ Backend local detectado! Usando ${LOCAL_API_URL}`);
    }
  } catch (error) {
    // Fallback para produção (normal se backend local não está disponível)
    console.log('ℹ️ Backend local não disponível, usando HuggingFace Spaces');
  }
}

// Iniciar detecção ao carregar o módulo
detectLocalBackend();

// Interface para resposta da API /analyze (conforme documentação técnica)

// Novo formato de resposta da API
export interface AnalyzeResponseV2 {
  has_pii: boolean;
  entities: Array<{
    tipo: string;
    valor: string;
    confianca: number;
    fonte?: string;
  }>;
  risk_level: string;
  confidence_all_found: number;
  total_entities: number;
  sources_used: string[];
}

export interface Entity {
  type: string;
  value: string;
  confidence: number;
}

export interface AnalysisDetail {
  tipo: string;
  valor: string;
  confianca?: number; // ✅ Campo corrigido
}

export interface AnalysisResult {
  classificacao: 'PÚBLICO' | 'NÃO PÚBLICO';
  confianca: number;
  risco: string;
  detalhes: AnalysisDetail[];
}

export type RiskLevel = 'critical' | 'high' | 'moderate' | 'low' | 'safe';

export function getRiskLevelFromString(risco: string): RiskLevel {
  const riscoUpper = risco?.toUpperCase() || '';
  if (riscoUpper === 'CRÍTICO' || riscoUpper === 'CRITICO') return 'critical';
  if (riscoUpper === 'ALTO') return 'high';
  if (riscoUpper === 'MODERADO') return 'moderate';
  if (riscoUpper === 'BAIXO') return 'low';
  if (riscoUpper === 'SEGURO') return 'safe';
  return 'safe';
}

export function getRiskLevel(probability: number, classification: string): RiskLevel {
  if (classification === 'PÚBLICO' || classification === 'public') {
    return 'safe';
  }
  if (probability >= 0.95) return 'critical';
  if (probability >= 0.85) return 'high';
  if (probability >= 0.60) return 'moderate';
  return 'safe';
}

export function getRiskInfo(riskLevel: RiskLevel): { label: string; color: string; bgColor: string } {
  switch (riskLevel) {
    case 'critical':
      return {
        label: 'Risco Crítico: Dados Sensíveis Expostos',
        color: 'text-white',
        bgColor: 'bg-red-800'
      };
    case 'high':
      return {
        label: 'Risco Alto: Identificadores Pessoais',
        color: 'text-red-700',
        bgColor: 'bg-red-100'
      };
    case 'moderate':
      return {
        label: 'Atenção: Verifique o Contexto',
        color: 'text-yellow-900',
        bgColor: 'bg-yellow-100'
      };
    case 'low':
      return {
        label: 'Risco Baixo: Verificação Sugerida',
        color: 'text-blue-700',
        bgColor: 'bg-blue-100'
      };
    case 'safe':
      return {
        label: 'Documento Seguro para Publicação',
        color: 'text-green-700',
        bgColor: 'bg-green-100'
      };
  }
}

export interface BatchResult {
  id: string;
  text_preview: string;
  fullText: string;
  classification: 'public' | 'restricted';
  probability: number;
  risco: string;
  entities: Entity[];
}

// Tipos de erro customizados
export type ApiErrorType = 'TIMEOUT' | 'OFFLINE' | 'WAKING_UP' | 'CORS' | 'UNKNOWN';

export class ApiError extends Error {
  type: ApiErrorType;

  constructor(type: ApiErrorType, message: string) {
    super(message);
    this.type = type;
    this.name = 'ApiError';
  }
}

// Mensagens amigáveis para o usuário
export function getErrorMessage(error: ApiError): string {
  switch (error.type) {
    case 'WAKING_UP':
      return 'O motor de IA está acordando, por favor aguarde uns instantes...';
    case 'TIMEOUT':
      return 'A API demorou muito para responder. O modelo pode estar processando. Tente novamente.';
    case 'OFFLINE':
      return 'Não foi possível conectar à API. Verifique sua conexão ou tente mais tarde.';
    case 'CORS':
      return 'Erro de permissão ao acessar a API. Contate o administrador.';
    default:
      return 'Ocorreu um erro inesperado. Tente novamente.';
  }
}

class ApiClient {
  private async request<T>(
    endpoint: string,
    options?: RequestInit,
    retryCount = 0
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...options?.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        // Se for 503 ou 502, o servidor pode estar acordando
        if (response.status === 503 || response.status === 502) {
          if (retryCount < MAX_RETRIES) {
            // Aguarda 3 segundos e tenta novamente
            await new Promise(resolve => setTimeout(resolve, 3000));
            return this.request<T>(endpoint, options, retryCount + 1);
          }
          throw new ApiError('WAKING_UP', 'Servidor iniciando');
        }
        throw new ApiError('UNKNOWN', `HTTP error: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof ApiError) {
        throw error;
      }

      if (error instanceof Error) {
        // Timeout
        if (error.name === 'AbortError') {
          if (retryCount < MAX_RETRIES) {
            // Tenta novamente uma vez
            return this.request<T>(endpoint, options, retryCount + 1);
          }
          throw new ApiError('TIMEOUT', 'Requisição expirou');
        }

        // Erro de rede (offline ou CORS)
        if (error.message === 'Failed to fetch') {
          if (retryCount < MAX_RETRIES) {
            // Aguarda 2 segundos e tenta novamente (modelo pode estar acordando)
            await new Promise(resolve => setTimeout(resolve, 2000));
            return this.request<T>(endpoint, options, retryCount + 1);
          }
          throw new ApiError('OFFLINE', 'Sem conexão');
        }

        // CORS error
        if (error.message.includes('CORS')) {
          throw new ApiError('CORS', 'Erro de CORS');
        }
      }

      throw new ApiError('UNKNOWN', 'Erro desconhecido');
    }
  }

  async checkConnection(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 8000);

      // Tenta o endpoint /analyze com um texto curto para verificar se está online
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ text: 'teste' }),
      });

      clearTimeout(timeoutId);
      // Se responder (mesmo com erro de validação), está online
      return response.ok || response.status < 500;
    } catch {
      return false;
    }
  }

  async analyzeText(text: string): Promise<AnalysisResult> {
    // Novo endpoint: /analyze com body { "text": "..." }
    const response = await this.request<AnalyzeResponseV2>('/analyze', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });

    // Mapear resposta da nova API para o formato interno
    const classificacao = response.has_pii ? 'NÃO PÚBLICO' as const : 'PÚBLICO' as const;
    const risco = response.risk_level?.toUpperCase() || 'BAIXO';

    return {
      classificacao,
      confianca: response.confidence_all_found ?? 0,
      risco,
      detalhes: response.entities?.map(d => ({
        tipo: d.tipo,
        valor: d.valor,
        confianca: d.confianca ?? 0.95,
      })) || [],
    };
  }

  async analyzeBatch(
    items: Array<{ id: string; text: string }>,
    onProgress?: (current: number, total: number) => void
  ): Promise<BatchResult[]> {
    const results: BatchResult[] = [];

    for (let i = 0; i < items.length; i++) {
      const { id, text } = items[i];

      try {
        // Envia o ID junto com o texto para a API
        const response = await this.request<AnalyzeResponseV2>('/analyze', {
          method: 'POST',
          body: JSON.stringify({ id, text }),
        });

        // Mapear resposta da nova API para o formato interno
        const classificacao = response.has_pii ? 'restricted' : 'public';
        const risco = response.risk_level?.toUpperCase() || 'BAIXO';

        const batchResult: BatchResult = {
          id, // Usa o ID original da planilha
          text_preview: text.length > 100 ? text.slice(0, 100) + '...' : text,
          fullText: text,
          classification: classificacao,
          probability: response.confidence_all_found ?? 0,
          risco,
          entities: response.entities?.map(d => ({
            type: d.tipo,
            value: d.valor,
            confidence: d.confianca ?? 0.95,
          })) || [],
        };

        results.push(batchResult);

        if (onProgress) {
          onProgress(i + 1, items.length);
        }
      } catch (error) {
        // Em caso de erro, adiciona resultado com erro
        const errorType = error instanceof ApiError ? error.type : 'UNKNOWN';
        results.push({
          id, // Mantém o ID original mesmo em caso de erro
          text_preview: text.length > 100 ? text.slice(0, 100) + '...' : text,
          fullText: text,
          classification: 'restricted',
          probability: 0,
          risco: `ERRO_${errorType}`,
          entities: [],
        });

        if (onProgress) {
          onProgress(i + 1, items.length);
        }
      }
    }

    return results;
  }

  // === ESTATÍSTICAS GLOBAIS ===

  async getStats(): Promise<{ site_visits: number; classification_requests: number; last_updated: string | null }> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(`${API_BASE_URL}/stats`, {
        signal: controller.signal,
        headers: { 'Accept': 'application/json' },
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Erro ao buscar stats:', error);
    }
    return { site_visits: 0, classification_requests: 0, last_updated: null };
  }

  async registerVisit(): Promise<void> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      await fetch(`${API_BASE_URL}/stats/visit`, {
        method: 'POST',
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json' },
      });

      clearTimeout(timeoutId);
    } catch (error) {
      console.error('Erro ao registrar visita:', error);
    }
  }
}

export const api = new ApiClient();
