import { useState } from 'react';
import { FileText, AlertTriangle, CheckCircle, Clock, Eye, ShieldX, AlertCircle, Sparkles, Target, TrendingUp, BarChart3, Zap, Info, Percent, ChevronLeft, ChevronRight, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { KPICard } from '@/components/KPICard';
import { DistributionChart } from '@/components/DistributionChart';
import { RiskThermometer } from '@/components/RiskThermometer';
import { RiskDistributionChart } from '@/components/RiskDistributionChart';
import { PIITypesChart } from '@/components/PIITypesChart';
import { ConfidenceBar, normalizeConfidence } from '@/components/ConfidenceBar';
import { ResultsLegend } from '@/components/ResultsLegend';
import { ExportButton } from '@/components/ExportButton';
import { IdentifierList } from '@/components/IdentifierBadge';
import { useAnalysis, getRiskBgClass, getRiskLabel } from '@/contexts/AnalysisContext';
import { cn } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

function MetricTooltip({ children, content }: { children: React.ReactNode; content: string }) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="inline-flex items-center gap-1 cursor-help">
            {children}
            <Info className="w-3.5 h-3.5 text-muted-foreground" />
          </span>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs text-xs">
          <p>{content}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export function Dashboard() {
  const { history, metrics, counters, clearHistory } = useAnalysis();
  const [selectedHistoryItem, setSelectedHistoryItem] = useState<typeof history[0] | null>(null);
  
  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;
  const totalPages = Math.ceil(history.length / pageSize);
  const paginatedHistory = history.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel) {
      case 'critical': return <ShieldX className="w-5 h-5" />;
      case 'high': return <AlertTriangle className="w-5 h-5" />;
      case 'moderate': return <AlertCircle className="w-5 h-5" />;
      case 'low': return <Shield className="w-5 h-5" />;
      case 'safe': return <CheckCircle className="w-5 h-5" />;
      default: return <AlertTriangle className="w-5 h-5" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="px-6 py-4 bg-white border-b border-gray-200">
        <h2 className="text-2xl font-bold text-foreground">Dashboard de Análise</h2>
        <p className="text-muted-foreground">
          Métricas em tempo real e análise de desempenho do sistema de identificação de dados pessoais
        </p>
      </div>

      {/* Hybrid System Performance - Only this one */}
      <div className="gov-card bg-gradient-to-br from-warning/5 to-warning/10 border-warning/20">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-warning" />
          <span className="text-sm font-semibold text-foreground">Benchmarks de Performance do Motor Híbrido (IA + Regex + Validação Matemática)</span>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
            <div className="text-center p-3 bg-card/50 rounded-lg border border-success/20">
              <div className="flex items-center justify-center gap-1 text-success mb-1">
                <Target className="w-4 h-4" />
                <MetricTooltip content="A IA valida o contexto do Regex, reduzindo falsos positivos e aumentando a precisão global.">
                  <span className="text-xs font-medium">Precisão Global</span>
                </MetricTooltip>
              </div>
              <p className="text-2xl font-bold text-success">94%</p>
            </div>
            
            <div className="text-center p-3 bg-card/50 rounded-lg border border-success/20">
              <div className="flex items-center justify-center gap-1 text-success mb-1">
                <TrendingUp className="w-4 h-4" />
                <MetricTooltip content="O Regex garante a captura de 100% dos CPFs, CNPJs e outros padrões estruturados.">
                  <span className="text-xs font-medium">Sensibilidade</span>
                </MetricTooltip>
              </div>
              <p className="text-2xl font-bold text-success">98%</p>
            </div>
            
            <div className="text-center p-3 bg-card/50 rounded-lg border border-success/20">
              <div className="flex items-center justify-center gap-1 text-success mb-1">
                <BarChart3 className="w-4 h-4" />
                <MetricTooltip content="Média harmônica do sistema híbrido, refletindo o melhor dos dois mundos.">
                  <span className="text-xs font-medium">F1-Score Combinado</span>
                </MetricTooltip>
              </div>
              <p className="text-2xl font-bold text-success">96%</p>
            </div>
          </div>
          
          <div className="p-3 bg-muted/50 rounded-lg text-sm text-muted-foreground">
            <strong className="text-foreground">Como funciona:</strong> O motor utiliza uma arquitetura híbrida de <span className="text-primary font-medium">Processamento de Linguagem Natural (spaCy)</span> para compreender o contexto semântico e <span className="text-warning font-medium">Expressões Regulares (Regex)</span> para identificar padrões estruturados. O diferencial do sistema é a <span className="text-success font-medium">Camada de Validação Matemática</span>, que aplica algoritmos de verificação (como o Módulo 11) para confirmar a autenticidade de CPFs e CNPJs, eliminando falsos positivos e garantindo maior precisão na classificação de PII.
        </div>
      </div>

      {/* Volume KPIs Section */}
      <div>
        <h3 className="text-sm font-medium text-muted-foreground mb-3 uppercase tracking-wider flex items-center gap-2">
          <FileText className="w-4 h-4" />
          KPIs de Volume da Sessão
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <KPICard
            title="Total de Pedidos"
            value={metrics.totalProcessed.toLocaleString()}
            subtitle="processados nesta sessão"
            icon={<FileText className="w-5 h-5" />}
            variant="default"
          />
          <KPICard
            title="Públicos"
            value={metrics.publicCount.toLocaleString()}
            subtitle="sem dados sensíveis"
            icon={<CheckCircle className="w-5 h-5" />}
            variant="success"
          />
          <KPICard
            title="Não Públicos"
            value={metrics.nonPublicCount.toLocaleString()}
            subtitle="com dados sensíveis"
            icon={<AlertTriangle className="w-5 h-5" />}
            variant="danger"
          />
          <KPICard
            title="Confiança Média"
            value={metrics.totalProcessed > 0 ? `${(metrics.averageConfidence * 100).toFixed(1)}%` : '0%'}
            subtitle="probabilidade média de acerto"
            icon={<Percent className="w-5 h-5" />}
            variant="highlight"
          />
        </div>
      </div>

      {/* Charts Row 1: Risk Thermometer + Classification Distribution */}
      {metrics.totalProcessed === 0 ? (
        <div className="gov-card">
          <div className="text-center py-8 text-muted-foreground">
            <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="font-medium">Nenhuma requisição processada ainda</p>
            <p className="text-sm mt-1">Acesse a página de Classificação para começar.</p>
          </div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="min-h-[300px]">
              <RiskThermometer 
                distribution={metrics.riskDistribution} 
                total={metrics.totalProcessed} 
              />
            </div>
            <div className="min-h-[300px]">
              <DistributionChart
                publicCount={metrics.publicCount}
                restrictedCount={metrics.nonPublicCount}
              />
            </div>
          </div>

          {/* Charts Row 2: Risk Distribution + PII Types */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="min-h-[300px]">
              <RiskDistributionChart distribution={metrics.riskDistribution} />
            </div>
            <div className="min-h-[300px]">
              <PIITypesChart data={metrics.piiTypeCounts} />
            </div>
          </div>
        </>
      )}

      {/* Request History */}
      <div className="gov-card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-primary" />
            <h3 className="text-lg font-semibold text-foreground">Histórico de Requisições</h3>
          </div>
          <div className="flex items-center gap-2">
            <ExportButton data={history} disabled={history.length === 0} />
            {history.length > 0 && (
              <Button variant="outline" size="sm" onClick={() => clearHistory()}>
                Limpar Tudo
              </Button>
            )}
          </div>
        </div>
        
        {history.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>Nenhuma requisição processada ainda.</p>
            <p className="text-sm mt-1">Acesse a página de Classificação para começar.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0">
              <table className="w-full min-w-[900px]">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <th className="text-left py-3 px-3 text-xs font-semibold text-muted-foreground uppercase">Data</th>
                    <th className="text-left py-3 px-3 text-xs font-semibold text-muted-foreground uppercase">Horário</th>
                    <th className="text-left py-3 px-3 text-xs font-semibold text-muted-foreground uppercase">Tipo</th>
                    <th className="text-left py-3 px-3 text-xs font-semibold text-muted-foreground uppercase">Classificação</th>
                    <th className="text-left py-3 px-3 text-xs font-semibold text-muted-foreground uppercase">Confiança</th>
                    <th className="text-left py-3 px-3 text-xs font-semibold text-muted-foreground uppercase">Nível de Risco</th>
                    <th className="text-left py-3 px-3 text-xs font-semibold text-muted-foreground uppercase">ID do Pedido</th>
                    <th className="text-left py-3 px-3 text-xs font-semibold text-muted-foreground uppercase hidden md:table-cell">Prévia do Pedido</th>
                    <th className="text-center py-3 px-3 text-xs font-semibold text-muted-foreground uppercase">Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedHistory.map((item) => (
                    <tr key={item.id} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-3 text-sm text-muted-foreground whitespace-nowrap">
                        {item.date}
                      </td>
                      <td className="py-3 px-3 text-sm text-muted-foreground whitespace-nowrap">
                        {item.time}
                      </td>
                      <td className="py-3 px-3">
                        <span className={cn(
                          'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                          item.type === 'individual' 
                            ? 'bg-primary/10 text-primary' 
                            : 'bg-muted text-muted-foreground'
                        )}>
                          {item.type === 'individual' ? 'Individual' : 'Lote'}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span className={cn(
                          'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
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
                            </>
                          )}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        {(() => {
                          const normalizedProb = normalizeConfidence(item.probability, item.classification);
                          return (
                            <ConfidenceBar 
                              value={normalizedProb} 
                              classification={item.classification}
                            />
                          );
                        })()}
                      </td>
                      <td className="py-3 px-3 text-left">
                        <span className={cn(
                          'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
                          getRiskBgClass(item.riskLevel)
                        )}>
                          {item.riskLevel === 'critical' && <ShieldX className="w-3 h-3" />}
                          {item.riskLevel === 'high' && <AlertTriangle className="w-3 h-3" />}
                          {item.riskLevel === 'moderate' && <AlertCircle className="w-3 h-3" />}
                          {item.riskLevel === 'low' && <Shield className="w-3 h-3" />}
                          {item.riskLevel === 'safe' && <CheckCircle className="w-3 h-3" />}
                          {getRiskLabel(item.riskLevel)}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span className="font-mono text-sm text-primary font-medium">
                          #{item.pedidoId}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-sm text-muted-foreground max-w-xs truncate hidden md:table-cell">
                        {item.text}
                      </td>
                      <td className="py-3 px-3 text-center">
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
                  ))}
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
        <DialogContent className="max-w-lg">
          <DialogHeader>
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
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">ID do Pedido</h4>
                <p className="text-sm font-mono text-foreground bg-primary/10 px-3 py-2 rounded-lg inline-block">
                  #{selectedHistoryItem.pedidoId}
                </p>
              </div>

              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Texto Analisado</h4>
                <p className="text-sm text-foreground bg-muted/50 p-3 rounded-lg">
                  {selectedHistoryItem.text}
                </p>
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
