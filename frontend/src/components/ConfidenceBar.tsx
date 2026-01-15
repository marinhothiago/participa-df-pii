import { cn } from '@/lib/utils';

interface ConfidenceBarProps {
  value: number; // 0-1
  classification?: string;
  className?: string;
  showLabel?: boolean;
}

/**
 * Barra de confiança com preenchimento verde sólido
 * O preenchimento segue a porcentagem de confiança (0-100%)
 * 
 * Recebe valor entre 0-1 do backend
 */
export function ConfidenceBar({ value, classification, className, showLabel = true }: ConfidenceBarProps) {
  const percentage = value * 100;
  
  return (
    <div className={cn("flex items-center gap-2", className)}>
      {/* Track (fundo cinza) */}
      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden min-w-[60px]">
        {/* Thumb (preenchimento verde) */}
        <div 
          className="h-full rounded-full transition-all duration-300"
          style={{ 
            width: `${Math.min(percentage, 100)}%`,
            backgroundColor: 'hsl(120, 60%, 40%)'
          }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-medium text-muted-foreground w-10 text-right">
          {Math.min(percentage, 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
}

/**
 * Função utilitária para obter a cor de confiança (verde)
 */
export function getConfidenceColor(): string {
  return 'hsl(120, 60%, 40%)';
}

/**
 * Normaliza a probabilidade para exibição
 * Backend retorna valor entre 0-1, apenas multiplica por 100 para exibir %
 */
/**
 * Normaliza a probabilidade para exibição
 * Se classificação for 'PÚBLICO' e probabilidade 0, retorna 0.99 (caso especial LAI)
 * Caso contrário, garante valor entre 0-1
 */
export function normalizeConfidence(probability: number, classification?: string): number {
  if (classification === 'PÚBLICO' && probability === 0) {
    return 0.99;
  }
  return Math.min(Math.max(probability, 0), 1);
}
