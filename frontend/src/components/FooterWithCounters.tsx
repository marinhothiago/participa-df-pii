import { Eye, BarChart3 } from 'lucide-react';
import { useAnalysis } from '@/contexts/AnalysisContext';

export function FooterWithCounters() {
  const { counters } = useAnalysis();
  
  return (
    <footer className="border-t border-border bg-primary text-primary-foreground">
      <div className="container mx-auto px-4 py-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-sm">
          {/* Esquerda: Autor */}
          <p className="text-primary-foreground/80 order-2 sm:order-1">
            Desenvolvido por: <span className="font-semibold text-primary-foreground">Thiago Marinho</span> © 2026
          </p>
          
          {/* Centro: Contadores */}
          <div className="flex items-center gap-4 text-xs order-1 sm:order-2">
            <div className="flex items-center gap-1.5 bg-primary-foreground/10 px-3 py-1 rounded-full">
              <Eye className="w-3.5 h-3.5" />
              <span>Acessos: <strong>{counters.siteVisits.toLocaleString()}</strong></span>
            </div>
            <div className="flex items-center gap-1.5 bg-primary-foreground/10 px-3 py-1 rounded-full">
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Requisições: <strong>{counters.totalClassificationRequests.toLocaleString()}</strong></span>
            </div>
          </div>
          
          {/* Direita: CGDF */}
          <p className="text-primary-foreground/80 order-3 text-center sm:text-right">
            Desafio Participa DF - Controladoria-Geral do Distrito Federal
          </p>
        </div>
      </div>
    </footer>
  );
}
