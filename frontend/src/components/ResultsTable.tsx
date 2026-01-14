import { useState } from 'react';
import { Eye, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { StatusBadge } from '@/components/StatusBadge';
import type { BatchResult } from '@/lib/api';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface ResultsTableProps {
  results: BatchResult[];
  pageSize?: number;
}

/**
 * Mapeamento de tipos de PII para nomes amigáveis ao usuário
 */
const piiTypeLabels: Record<string, string> = {
  'CPF': 'CPF',
  'EMAIL': 'Email',
  'TELEFONE': 'Telefone',
  'TELEFONE_DDI': 'Telefone (DDI)',
  'RG_CNH': 'RG/CNH',
  'PASSAPORTE': 'Passaporte',
  'CONTA_BANCARIA': 'Conta Bancária',
  'PIX': 'Chave PIX',
  'ENDERECO_RESIDENCIAL': 'Endereço',
  'NOME_PESSOAL': 'Nome Pessoal',
  'NOME_POR_IA': 'Nome (IA)',
  'NOME_CONTEXTO': 'Nome em Contexto',
  'CHAVE_PIX': 'Chave PIX'
};

export function ResultsTable({ results, pageSize = 5 }: ResultsTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedResult, setSelectedResult] = useState<BatchResult | null>(null);

  const totalPages = Math.ceil(results.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const paginatedResults = results.slice(startIndex, startIndex + pageSize);

  return (
    <>
      <div className="gov-card animate-slide-up overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="text-left py-3 px-4 text-sm font-semibold text-foreground">ID</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-foreground">Resumo do Texto</th>
                <th className="text-center py-3 px-4 text-sm font-semibold text-foreground">Classificação</th>
                <th className="text-center py-3 px-4 text-sm font-semibold text-foreground">Probabilidade</th>
                <th className="text-center py-3 px-4 text-sm font-semibold text-foreground">Ação</th>
              </tr>
            </thead>
            <tbody>
              {paginatedResults.map((result, index) => (
                <tr
                  key={result.id}
                  className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <td className="py-3 px-4">
                    <span className="font-mono text-sm text-muted-foreground">#{result.id}</span>
                  </td>
                  <td className="py-3 px-4">
                    <p className="text-sm text-foreground line-clamp-2 max-w-md">
                      {result.text_preview}
                    </p>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <StatusBadge status={result.classification} size="sm" />
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2 justify-center">
                      <Progress
                        value={result.probability * 100}
                        className="w-20 h-2"
                      />
                      <span className="text-sm font-medium text-foreground w-12 text-right">
                        {(result.probability * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedResult(result)}
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

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-muted/30">
            <p className="text-sm text-muted-foreground">
              Exibindo {startIndex + 1}-{Math.min(startIndex + pageSize, results.length)} de {results.length}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-sm text-foreground px-2">
                {currentPage} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Details Dialog */}
      <Dialog open={!!selectedResult} onOpenChange={() => setSelectedResult(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <span>Documento #{selectedResult?.id}</span>
              {selectedResult && <StatusBadge status={selectedResult.classification} size="sm" />}
            </DialogTitle>
          </DialogHeader>
          
          {selectedResult && (
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Texto Original</h4>
                <p className="text-sm text-foreground bg-muted/50 p-3 rounded-lg">
                  {selectedResult.text_preview}
                </p>
              </div>

              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Probabilidade de Restrição</h4>
                <div className="flex items-center gap-3">
                  <Progress value={selectedResult.probability * 100} className="flex-1 h-2" />
                  <span className="text-lg font-bold text-foreground">
                    {(selectedResult.probability * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {selectedResult.entities.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2">
                    Entidades Detectadas ({selectedResult.entities.length})
                  </h4>
                  <div className="space-y-2">
                    {selectedResult.entities.map((entity, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-destructive/5 rounded-lg border border-destructive/20">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium px-2 py-0.5 bg-destructive/10 text-destructive rounded">
                            {piiTypeLabels[entity.type] || entity.type}
                          </span>
                          <span className="text-sm font-mono text-foreground">{entity.value}</span>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {(entity.confidence * 100).toFixed(0)}% conf.
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
