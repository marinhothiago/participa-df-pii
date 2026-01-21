/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * Classification.tsx - Página Principal de Análise de PIIs
 * ═══════════════════════════════════════════════════════════════════════════════
 * 
 * Esta página implementa a interface principal do Motor PII, permitindo:
 * 
 * 1. ANÁLISE INDIVIDUAL
 *    - Entrada de texto livre para análise em tempo real
 *    - Feedback do resultado com indicadores visuais de risco
 *    - Detalhamento de entidades encontradas (CPF, Nome, Telefone, etc.)
 * 
 * 2. PROCESSAMENTO EM LOTE
 *    - Upload de arquivos CSV/XLSX via drag & drop
 *    - Processamento paralelo com barra de progresso
 *    - Exportação de resultados em JSON/CSV
 * 
 * 3. HISTÓRICO DE ANÁLISES
 *    - Tabela paginada com todas as análises da sessão
 *    - Filtros e busca por texto/entidade
 *    - Modal de detalhes com explicabilidade (XAI)
 * 
 * 4. MÉTRICAS EM TEMPO REAL
 *    - KPIs de volume processado
 *    - Distribuição de riscos
 *    - Tipos de PII mais frequentes
 * 
 * Componentes utilizados:
 * - FileDropzone: Upload com drag & drop
 * - ConfidenceBar: Barra de confiança calibrada
 * - IdentifierList: Badges de entidades PII
 * - FeedbackPanel: Coleta de feedback do usuário
 * 
 * @see /lib/api.ts para interfaces de resposta da API
 * @see /contexts/AnalysisContext.tsx para estado global
 * ═══════════════════════════════════════════════════════════════════════════════
 */

import { ApiWakingUpMessage } from '@/components/ApiWakingUpMessage';
import { ConfidenceBar } from '@/components/ConfidenceBar';
import { ExpandableText } from '@/components/ExpandableText';
import { ExportButton } from '@/components/ExportButton';
import { FeedbackPanel } from '@/components/FeedbackPanel';
import { FileDropzone } from '@/components/FileDropzone';
import { IdentifierList } from '@/components/IdentifierBadge';
import { KPICard } from '@/components/KPICard';
import { ResultsLegend } from '@/components/ResultsLegend';
import { TrainingStatus } from '@/components/TrainingStatus';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { getRiskBgClass, getRiskLabel, getRiskLevelFromRisco, useAnalysis } from '@/contexts/AnalysisContext';
import { api, ApiError, getErrorMessage, type AnalysisResult } from '@/lib/api';
import { parseFile } from '@/lib/fileParser';
import { cn } from '@/lib/utils';
import { AlertCircle, AlertTriangle, CheckCircle, ChevronLeft, ChevronRight, Download, Eye, FileText, FolderUp, HelpCircle, Info, List, Loader2, Percent, RefreshCw, Search, Shield, ShieldAlert, ShieldX, Upload } from 'lucide-react';
import { useState } from 'react';

/**
 * Componente principal da página de classificação.
 * Gerencia estados de análise individual, processamento em lote e histórico.
 */
export function Classification() {
  const { history, metrics, addAnalysisResult, addBatchResults, clearHistory, incrementClassificationRequests } = useAnalysis();

  // ═══════════════════════════════════════════════════════════════════════════
  // ESTADOS - Análise Individual
  // ═══════════════════════════════════════════════════════════════════════════
  const [text, setText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [analysisError, setAnalysisError] = useState<{ message: string; isWaking: boolean } | null>(null);

  // ═══════════════════════════════════════════════════════════════════════════
  // ESTADOS - Processamento em Lote
  // ═══════════════════════════════════════════════════════════════════════════
  const [isProcessing, setIsProcessing] = useState(false);
  const [batchError, setBatchError] = useState<{ message: string; isWaking: boolean } | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [batchProgress, setBatchProgress] = useState<{ current: number; total: number } | null>(null);

  // ═══════════════════════════════════════════════════════════════════════════
  // ESTADOS - Paginação e Histórico
  // ═══════════════════════════════════════════════════════════════════════════
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;
  const totalPages = Math.ceil(history.length / pageSize);
  const paginatedHistory = history.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  // Modal de detalhes do histórico
  const [selectedHistoryItem, setSelectedHistoryItem] = useState<typeof history[0] | null>(null);

  // ═══════════════════════════════════════════════════════════════════════════
  // HANDLERS - Análise Individual
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Executa análise de texto individual via API.
   * Atualiza métricas e histórico automaticamente.
   */
  const handleAnalyze = async () => {
    if (!text.trim()) return;

    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysisResult(null);

    const textoParaAnalise = text;
    setText(''); // Limpa o campo imediatamente após o clique

    try {
      const data = await api.analyzeText(textoParaAnalise);
      setAnalysisResult(data);
      // Add to global history
      addAnalysisResult(data, textoParaAnalise, 'individual');
      // Increment classification requests counter
      incrementClassificationRequests(1);
      // Reset to first page to see new result
      setCurrentPage(1);
    } catch (err) {
      if (err instanceof ApiError) {
        const isWaking = err.type === 'WAKING_UP' || err.type === 'TIMEOUT';
        setAnalysisError({ message: getErrorMessage(err), isWaking });
      } else {
        setAnalysisError({ message: 'Erro ao processar o texto. Tente novamente.', isWaking: false });
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const clearAnalysis = () => {
    setText('');
    setAnalysisResult(null);
    setAnalysisError(null);
  };

  // Batch Processing Handlers
  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setBatchError(null);
  };

  const handleProcess = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setBatchError(null);
    setBatchProgress(null);

    try {
      const parseResult = await parseFile(selectedFile);

      if (!parseResult.success) {
        setBatchError({ message: parseResult.error || 'Erro ao processar o arquivo.', isWaking: false });
        setIsProcessing(false);
        return;
      }

      if (parseResult.rows.length === 0) {
        setBatchError({ message: 'Nenhum texto encontrado no arquivo para análise.', isWaking: false });
        setIsProcessing(false);
        return;
      }

      // Mapeia as linhas para o formato esperado pela API (id + text)
      const items = parseResult.rows.map(row => ({
        id: row.id,
        text: row.text,
      }));

      setBatchProgress({ current: 0, total: items.length });

      const data = await api.analyzeBatch(items, (current, total) => {
        setBatchProgress({ current, total });
      });

      setBatchProgress(null);

      // Add batch results to global history
      addBatchResults(data);

      // Increment classification requests counter
      incrementClassificationRequests(items.length);

      // Reset to first page to see new results
      setCurrentPage(1);

      // Clear file selection after successful processing
      setSelectedFile(null);
    } catch (err) {
      setBatchProgress(null);
      if (err instanceof ApiError) {
        const isWaking = err.type === 'WAKING_UP' || err.type === 'TIMEOUT';
        setBatchError({ message: getErrorMessage(err), isWaking });
      } else {
        setBatchError({ message: 'Erro ao processar o arquivo. Verifique o formato e tente novamente.', isWaking: false });
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const clearBatch = () => {
    setSelectedFile(null);
    setBatchError(null);
    setBatchProgress(null);
  };

  const handleClearAll = () => {
    clearHistory();
    setCurrentPage(1);
  };

  // Helper functions for analysis result
  const getClassification = (result: AnalysisResult) => {
    // Deriva da nova API: has_pii
    if ('has_pii' in result) {
      return result.has_pii ? 'NÃO PÚBLICO' : 'PÚBLICO';
    }
    return result.classificacao;
  };
  const getProbability = (result: AnalysisResult) => {
    // Sempre prioriza confidence_all_found
    if ('confidence_all_found' in result) {
      return result.confidence_all_found ?? 0;
    }
    return result.confianca ?? 0;
  };

  const getDetails = (result: AnalysisResult) => {
    // Sempre prioriza entities
    if ('entities' in result) {
      return result.entities || [];
    }
    return result.detalhes || [];
  };

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel) {
      case 'critical':
        return <ShieldX className="w-5 h-5" />;
      case 'high':
        return <ShieldAlert className="w-5 h-5" />;
      case 'moderate':
        return <AlertCircle className="w-5 h-5" />;
      case 'low':
        return <Info className="w-5 h-5" />;
      case 'safe':
        return <Shield className="w-5 h-5" />;
      default:
        return <AlertTriangle className="w-5 h-5" />;
    }
  };

  const getRiskInfo = (risco: string) => {
    const riskLevel = getRiskLevelFromRisco(risco);
    return {
      level: riskLevel,
      label: getRiskLabel(riskLevel),
      bgClass: getRiskBgClass(riskLevel),
    };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-foreground mb-6 mt-12">Classificação de Pedidos LAI</h2>
        <p className="text-muted-foreground">Identifique dados pessoais em pedidos de Lei de Acesso à Informação</p>
      </div>

      {/* KPI Cards - Real Session Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KPICard
          title="Total de Pedidos"
          value={metrics.totalProcessed.toLocaleString()}
          subtitle="processados nesta sessão"
          icon={<FileText className="w-5 h-5" />}
          variant="default"
          tooltip="Quantidade total de pedidos de acesso à informação analisados pelo motor de IA durante esta sessão de uso."
        />
        <KPICard
          title="Públicos"
          value={metrics.publicCount.toLocaleString()}
          subtitle="sem dados sensíveis"
          icon={<CheckCircle className="w-5 h-5" />}
          variant="success"
          tooltip="Pedidos que NÃO contêm dados pessoais identificáveis (PII) e podem ser divulgados publicamente conforme a LAI."
        />
        <KPICard
          title="Não Públicos"
          value={metrics.nonPublicCount.toLocaleString()}
          subtitle="com dados sensíveis"
          icon={<AlertTriangle className="w-5 h-5" />}
          variant="danger"
          tooltip="Pedidos que CONTÊM dados pessoais sensíveis (CPF, nome, endereço, etc.) e requerem tratamento especial conforme a LGPD."
        />
        <KPICard
          title="Confiança Média"
          value={metrics.totalProcessed > 0 ? `${(metrics.averageConfidence * 100).toFixed(1)}%` : '0%'}
          subtitle="probabilidade média de acerto"
          icon={<Percent className="w-5 h-5" />}
          variant="highlight"
          tooltip="Média da confiança do modelo em suas classificações. Valores acima de 90% indicam alta certeza nas predições."
        />
      </div>

      {/* Training Status Dashboard */}
      <div className="bg-gradient-to-r from-primary/5 to-primary/10 rounded-lg border border-primary/20 p-4">
        <h3 className="text-sm font-semibold mb-3 text-foreground">🤖 Status de Aprendizado em Tempo Real</h3>
        <TrainingStatus />
      </div>

      {/* Two Column Layout: Individual + Batch */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Individual Analysis */}
        <div className="gov-card">
          <div className="flex items-center gap-2 mb-4">
            <Search className="w-5 h-5 text-primary" />
            <h3 className="text-lg font-semibold text-foreground">Classificação Individual</h3>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <FileText className="w-4 h-4" />
              <span>Cole o texto do pedido LAI para análise</span>
            </div>

            <Textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Cole o texto do pedido aqui...

Exemplo: Solicito informações sobre o contrato nº 2024/001, firmado com o servidor João da Silva, CPF 123.456.789-00."
              className="min-h-[140px] resize-none text-sm"
              disabled={isAnalyzing}
            />

            <div className="flex gap-2">
              <Button
                onClick={handleAnalyze}
                disabled={!text.trim() || isAnalyzing}
                size="sm"
                className="flex-1"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Analisando...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    Analisar Privacidade
                  </>
                )}
              </Button>

              {(text || analysisResult) && (
                <Button variant="outline" size="sm" onClick={clearAnalysis} disabled={isAnalyzing}>
                  Limpar
                </Button>
              )}
            </div>

            {analysisError && (
              analysisError.isWaking ? (
                <ApiWakingUpMessage
                  variant="inline"
                  onRetry={handleAnalyze}
                  isRetrying={isAnalyzing}
                />
              ) : (
                <div className="flex items-center gap-2 p-2 bg-destructive/10 border border-destructive/20 rounded text-destructive text-xs">
                  <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                  {analysisError.message}
                  <Button variant="ghost" size="sm" onClick={handleAnalyze} className="ml-auto h-6 px-2">
                    <RefreshCw className="w-3 h-3" />
                  </Button>
                </div>
              )
            )}

            {/* Individual Analysis Result Inline */}
            {analysisResult && (
              <div className="space-y-3 pt-2 border-t border-border">
                {(() => {
                  const classification = getClassification(analysisResult);
                  const probability = getProbability(analysisResult);
                  const risco = analysisResult.risco ?? 'SEGURO';
                  const riskInfo = getRiskInfo(risco);

                  return (
                    <div className={cn(
                      'p-3 rounded-lg flex items-center gap-3 border',
                      riskInfo.bgClass
                    )}>
                      {getRiskIcon(riskInfo.level)}
                      <div className="flex-1">
                        <p className="font-semibold text-sm">
                          {classification === 'PÚBLICO' ? 'Público' : 'Não Público'} - {riskInfo.label}
                        </p>
                        <p className="text-xs opacity-90">
                          Confiança: {((probability as number) * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold">{((probability as number) * 100).toFixed(0)}%</p>
                      </div>
                    </div>
                  );
                })()}

                {/* Details Badges - usando novo componente */}
                {(getDetails(analysisResult) as { tipo: string; valor: string; confianca: number }[])?.length > 0 && (
                  <IdentifierList
                    identificadores={getDetails(analysisResult) as { tipo: string; valor: string; confianca: number }[]}
                    showConfidence={true}
                    size="sm"
                  />
                )}
              </div>
            )}
          </div>
        </div>

        {/* Batch Processing */}
        <div className="gov-card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FolderUp className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-semibold text-foreground">Classificação em Lote</h3>
            </div>
            <Button
              variant="outline"
              size="sm"
              asChild
            >
              <a
                href="https://www.cg.df.gov.br/documents/d/cg/amostra_e-sic"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Download className="w-4 h-4 mr-2" />
                Baixar Amostra
              </a>
            </Button>
          </div>

          <FileDropzone
            onFileSelect={handleFileSelect}
            disabled={isProcessing}
          />

          {selectedFile && (
            <div className="mt-4 flex gap-2">
              <Button
                onClick={handleProcess}
                disabled={isProcessing}
                size="sm"
                className="flex-1"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processando...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Analisar Privacidade
                  </>
                )}
              </Button>
              <Button variant="outline" size="sm" onClick={clearBatch} disabled={isProcessing}>
                Cancelar
              </Button>
            </div>
          )}

          {/* Batch Progress */}
          {batchProgress && (
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Processando...</span>
                <span className="font-medium">{batchProgress.current} / {batchProgress.total}</span>
              </div>
              <Progress value={(batchProgress.current / batchProgress.total) * 100} className="h-2" />
            </div>
          )}

          {batchError && (
            batchError.isWaking ? (
              <div className="mt-4">
                <ApiWakingUpMessage
                  variant="inline"
                  onRetry={handleProcess}
                  isRetrying={isProcessing}
                />
              </div>
            ) : (
              <div className="mt-4 flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{batchError.message}</span>
                <Button variant="ghost" size="sm" onClick={handleProcess} className="ml-auto">
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            )
          )}
        </div>
      </div>

      {/* Unified Results Section */}
      <div className="gov-card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <List className="w-5 h-5 text-primary" />
            <h3 className="text-lg font-semibold text-foreground">Resultados da Classificação</h3>
          </div>
          <div className="flex items-center gap-2">
            <ExportButton data={history} disabled={history.length === 0} />
            {history.length > 0 && (
              <Button variant="outline" size="sm" onClick={handleClearAll}>
                Limpar Tudo
              </Button>
            )}
          </div>
        </div>
        <p className="text-sm text-muted-foreground mb-4">
          Lista de pedidos analisados e suas respectivas classificações.
        </p>

        {history.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="font-medium">Nenhuma requisição processada ainda</p>
            <p className="text-sm mt-1">Utilize a classificação individual ou em lote acima para começar.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0">
              <table className="w-full min-w-[900px]">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <th className="text-center py-3 px-4 text-xs font-semibold text-muted-foreground uppercase w-16">#</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-muted-foreground uppercase">Data</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-muted-foreground uppercase">Horário</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-muted-foreground uppercase">Tipo</th>
                    <th className="text-center py-3 px-4 text-xs font-semibold text-muted-foreground uppercase">Classificação</th>
                    <th className="text-center py-3 px-4 text-xs font-semibold text-muted-foreground uppercase">Confiança</th>
                    <th className="text-center py-3 px-4 text-xs font-semibold text-muted-foreground uppercase">Nível de Risco</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-muted-foreground uppercase">ID do Pedido</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-muted-foreground uppercase hidden lg:table-cell">Prévia do Pedido</th>
                    <th className="text-center py-3 px-4 text-xs font-semibold text-muted-foreground uppercase">Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedHistory.map((item, index) => {
                    // Calcula o ID sequencial baseado na página atual
                    const sequentialId = ((currentPage - 1) * pageSize) + index + 1;

                    // Verifica se tem explicações para tooltip (com verificação de segurança)
                    const hasExplicacoes = item.details?.some(d => d.explicacao) ?? false;

                    return (
                      <tr key={item.id} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                        <td className="py-3 px-4 text-center">
                          <span className="font-mono text-sm text-muted-foreground font-medium">
                            {sequentialId}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm text-muted-foreground whitespace-nowrap">
                          {item.date}
                        </td>
                        <td className="py-3 px-4 text-sm text-muted-foreground whitespace-nowrap">
                          {item.time}
                        </td>
                        <td className="py-3 px-4">
                          <span className={cn(
                            'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                            item.type === 'individual'
                              ? 'bg-primary/10 text-primary'
                              : 'bg-muted text-muted-foreground'
                          )}>
                            {item.type === 'individual' ? 'Individual' : 'Lote'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <span className={cn(
                                  'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium cursor-help',
                                  item.classification === 'PÚBLICO'
                                    ? 'bg-green-600/10 text-green-600'
                                    : 'bg-red-600/10 text-red-600'
                                )}>
                                  {item.classification === 'PÚBLICO' ? (
                                    <>
                                      <CheckCircle className="w-3 h-3" />
                                      Público
                                    </>
                                  ) : (
                                    <>
                                      <AlertTriangle className="w-3 h-3" />
                                      Não Público
                                      {hasExplicacoes && <HelpCircle className="w-3 h-3 ml-1 opacity-60" />}
                                    </>
                                  )}
                                </span>
                              </TooltipTrigger>
                              {hasExplicacoes && (
                                <TooltipContent side="bottom" className="max-w-md p-3">
                                  <div className="space-y-2">
                                    <p className="font-semibold text-xs uppercase text-muted-foreground">
                                      Explicação (XAI)
                                    </p>
                                    {(item.details ?? []).filter(d => d.explicacao).map((d, i) => (
                                      <div key={i} className="text-xs">
                                        <span className="font-semibold text-primary">{d.tipo}:</span>
                                        <ul className="ml-2 mt-1 space-y-0.5">
                                          {d.explicacao?.motivos?.map((m, j) => (
                                            <li key={j} className="text-muted-foreground">{m}</li>
                                          ))}
                                          {d.explicacao?.validacoes?.map((v, j) => (
                                            <li key={`v-${j}`} className="text-green-600">{v}</li>
                                          ))}
                                        </ul>
                                        <p className="text-muted-foreground mt-1">
                                          Fonte: {d.explicacao?.fontes?.join(', ') ?? 'N/A'}
                                        </p>
                                      </div>
                                    ))}
                                  </div>
                                </TooltipContent>
                              )}
                            </Tooltip>
                          </TooltipProvider>
                        </td>
                        <td className="py-3 px-4">
                          <ConfidenceBar
                            value={item.probability}
                            classification={item.classification}
                            className="justify-center"
                          />
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className={cn(
                            'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border',
                            getRiskBgClass(item.riskLevel)
                          )}>
                            {item.riskLevel === 'critical' && <ShieldX className="w-3 h-3" />}
                            {item.riskLevel === 'high' && <ShieldAlert className="w-3 h-3" />}
                            {item.riskLevel === 'moderate' && <AlertCircle className="w-3 h-3" />}
                            {item.riskLevel === 'low' && <Info className="w-3 h-3" />}
                            {item.riskLevel === 'safe' && <CheckCircle className="w-3 h-3" />}
                            {getRiskLabel(item.riskLevel)}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-mono text-sm text-primary font-medium">
                            #{item.pedidoId}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm text-muted-foreground max-w-xs truncate hidden lg:table-cell">
                          {item.text}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedHistoryItem(item)}
                            className="text-primary hover:text-primary hover:bg-primary/10"
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            Detalhes
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground">
                  Exibindo {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, history.length)} de {history.length} resultados
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                  >
                    <ChevronLeft className="w-4 h-4 mr-1" />
                    Anterior
                  </Button>
                  <div className="flex items-center gap-1">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum: number;
                      if (totalPages <= 5) {
                        pageNum = i + 1;
                      } else if (currentPage <= 3) {
                        pageNum = i + 1;
                      } else if (currentPage >= totalPages - 2) {
                        pageNum = totalPages - 4 + i;
                      } else {
                        pageNum = currentPage - 2 + i;
                      }
                      return (
                        <Button
                          key={pageNum}
                          variant={currentPage === pageNum ? "default" : "outline"}
                          size="sm"
                          onClick={() => setCurrentPage(pageNum)}
                          className="w-8 h-8 p-0"
                        >
                          {pageNum}
                        </Button>
                      );
                    })}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                  >
                    Próximo
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              </div>
            )}
          </>
        )}

        {/* Legend */}
        <div className="mt-4 pt-4 border-t border-border">
          <ResultsLegend showClassification showRisk showConfidence />
        </div>
      </div>

      {/* History Item Details Dialog */}
      <Dialog open={!!selectedHistoryItem} onOpenChange={() => setSelectedHistoryItem(null)}>
        <DialogContent className="max-w-lg max-h-[90vh] flex flex-col">
          <DialogHeader className="flex-shrink-0">
            <DialogTitle className="flex items-center gap-3">
              <span>Detalhes da Análise</span>
              {selectedHistoryItem && (
                <span className={cn(
                  'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
                  selectedHistoryItem.classification === 'PÚBLICO'
                    ? 'bg-green-600/10 text-green-600'
                    : 'bg-red-600/10 text-red-600'
                )}>
                  {selectedHistoryItem.classification}
                </span>
              )}
            </DialogTitle>
          </DialogHeader>

          {selectedHistoryItem && (
            <div className="flex-1 overflow-y-auto space-y-4 pr-2">
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">ID do Pedido</h4>
                <p className="text-sm font-mono text-foreground bg-primary/10 px-3 py-2 rounded-lg inline-block">
                  #{selectedHistoryItem.pedidoId}
                </p>
              </div>

              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Texto Analisado</h4>
                <ExpandableText
                  text={selectedHistoryItem.text}
                  maxLines={3}
                />
              </div>

              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Nível de Risco</h4>
                <div className={cn(
                  'p-3 rounded-lg flex items-center gap-3',
                  getRiskBgClass(selectedHistoryItem.riskLevel)
                )}>
                  {getRiskIcon(selectedHistoryItem.riskLevel)}
                  <div className="flex-1">
                    <p className="font-semibold text-sm">{getRiskLabel(selectedHistoryItem.riskLevel)}</p>
                    <p className="text-xs opacity-90">
                      Probabilidade: {(selectedHistoryItem.probability * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>

              {selectedHistoryItem.details.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2">
                    Dados Pessoais Identificados ({selectedHistoryItem.details.length})
                  </h4>
                  <IdentifierList
                    identificadores={selectedHistoryItem.details}
                    showConfidence={true}
                    size="md"
                  />
                </div>
              )}

              {/* Seção de Explicabilidade (XAI) */}
              {selectedHistoryItem.details.some(d => d.explicacao) && (
                <div className="bg-muted/30 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
                    <HelpCircle className="w-4 h-4" />
                    Explicabilidade (XAI)
                  </h4>
                  <div className="space-y-3">
                    {selectedHistoryItem.details.filter(d => d.explicacao).map((d, i) => (
                      <div key={i} className="bg-background rounded-lg p-3 border border-border">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-semibold text-primary text-sm">{d.tipo}</span>
                          <code className="text-xs bg-muted px-2 py-0.5 rounded">{d.valor}</code>
                          {d.explicacao?.confianca_percent && (
                            <span className="text-xs text-muted-foreground ml-auto">
                              {d.explicacao.confianca_percent}
                            </span>
                          )}
                        </div>

                        {d.explicacao?.motivos && d.explicacao.motivos.length > 0 && (
                          <div className="mb-2">
                            <p className="text-xs font-medium text-muted-foreground mb-1">Motivos:</p>
                            <ul className="text-xs space-y-0.5">
                              {d.explicacao.motivos.map((m, j) => (
                                <li key={j} className="text-foreground">{m}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {d.explicacao?.validacoes && d.explicacao.validacoes.length > 0 && (
                          <div className="mb-2">
                            <p className="text-xs font-medium text-muted-foreground mb-1">Validações:</p>
                            <ul className="text-xs space-y-0.5">
                              {d.explicacao.validacoes.map((v, j) => (
                                <li key={j} className="text-green-600">{v}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {d.explicacao?.fontes && d.explicacao.fontes.length > 0 && (
                          <p className="text-xs text-muted-foreground">
                            <span className="font-medium">Fontes:</span> {d.explicacao.fontes.join(', ')}
                          </p>
                        )}

                        {d.explicacao?.contexto && d.explicacao.contexto.length > 0 && (
                          <p className="text-xs text-muted-foreground mt-1">
                            <span className="font-medium">Contexto:</span> {d.explicacao.contexto.join(', ')}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Painel de Feedback Humano */}
              {selectedHistoryItem.details.length > 0 && (
                <div className="pt-4 border-t border-border">
                  <FeedbackPanel
                    analysisId={selectedHistoryItem.pedidoId}
                    originalText={selectedHistoryItem.text}
                    entities={selectedHistoryItem.details.map(d => ({
                      tipo: d.tipo,
                      valor: d.valor,
                      confianca: (d as { confianca?: number }).confianca,
                    }))}
                    classificacao={selectedHistoryItem.classification}
                    onFeedbackSubmitted={() => { }}
                  />
                </div>
              )}

              <div className="text-xs text-muted-foreground pt-2 border-t border-border">
                Analisado em: {selectedHistoryItem.date} às {selectedHistoryItem.time}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
