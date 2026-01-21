import { useAnalysis } from '@/contexts/AnalysisContext';
import { BarChart3, Eye, Linkedin } from 'lucide-react';

export function FooterWithCounters() {
  const { counters } = useAnalysis();

  return (
    <footer className="border-t border-border bg-primary text-primary-foreground">
      <div className="container mx-auto px-4 py-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-sm">
          {/* Esquerda: Autor */}
          <p className="text-primary-foreground/80 order-2 sm:order-1 flex items-center gap-2">
            Desenvolvido por:{' '}
            <a
              href="https://www.linkedin.com/in/thiagomarinh0/"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-primary-foreground hover:text-primary-foreground/80 transition-colors"
            >
              Thiago Marinho
            </a>
            © 2026
            <a
              href="https://www.linkedin.com/in/thiagomarinh0/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center bg-white text-primary rounded p-1 hover:opacity-80 transition-opacity"
              title="Visite meu LinkedIn"
            >
              <Linkedin className="w-4 h-4" />
            </a>
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
