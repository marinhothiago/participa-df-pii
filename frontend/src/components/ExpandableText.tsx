import { cn } from '@/lib/utils';
import { Check, ChevronUp, Copy, Maximize2 } from 'lucide-react';
import { useState } from 'react';

interface ExpandableTextProps {
    text: string;
    maxLines?: number;
    className?: string;
}

export function ExpandableText({ text, maxLines = 3, className }: ExpandableTextProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [copied, setCopied] = useState(false);

    // Calcula se precisa expandir - mais agressivo
    const needsExpand = text.length > 150 || text.split('\n').length > maxLines;

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Erro ao copiar:', err);
        }
    };

    return (
        <div className="space-y-2">
            <div
                className={cn(
                    'bg-muted/50 p-3 rounded-lg text-sm text-foreground break-words whitespace-pre-wrap',
                    isExpanded ? 'max-h-[400px] overflow-y-auto' : 'max-h-[80px] overflow-hidden',
                    className
                )}
                style={!isExpanded ? {
                    display: '-webkit-box',
                    WebkitLineClamp: maxLines,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden'
                } : undefined}
            >
                {text}
            </div>

            {/* Botões SEMPRE visíveis quando texto é longo */}
            <div className="flex gap-3 flex-wrap">
                {needsExpand && (
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className={cn(
                            "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all",
                            isExpanded
                                ? "bg-muted text-foreground hover:bg-muted/80"
                                : "bg-primary text-primary-foreground hover:bg-primary/90"
                        )}
                    >
                        {isExpanded ? (
                            <>
                                <ChevronUp className="h-3.5 w-3.5" />
                                Recolher Texto
                            </>
                        ) : (
                            <>
                                <Maximize2 className="h-3.5 w-3.5" />
                                Ver Texto Completo
                            </>
                        )}
                    </button>
                )}

                <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground transition-all"
                    title="Copiar texto completo"
                >
                    {copied ? (
                        <>
                            <Check className="h-3.5 w-3.5 text-green-600" />
                            Copiado!
                        </>
                    ) : (
                        <>
                            <Copy className="h-3.5 w-3.5" />
                            Copiar
                        </>
                    )}
                </button>
            </div>

            {!isExpanded && needsExpand && (
                <p className="text-xs text-orange-600 font-medium">
                    ⚠️ Clique em "Ver Texto Completo" para ver o contexto antes de validar
                </p>
            )}
        </div>
    );
}
