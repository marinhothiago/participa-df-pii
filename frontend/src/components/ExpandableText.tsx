import { cn } from '@/lib/utils';
import { Check, ChevronDown, ChevronUp, Copy } from 'lucide-react';
import { useState } from 'react';

interface ExpandableTextProps {
    text: string;
    maxLines?: number;
    className?: string;
}

export function ExpandableText({ text, maxLines = 3, className }: ExpandableTextProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [copied, setCopied] = useState(false);

    // Calcula se precisa expandir (conta linhas)
    const lines = text.split('\n');
    const needsExpand = lines.length > maxLines || text.length > 300;

    const displayText = isExpanded ? text : lines.slice(0, maxLines).join('\n');

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
                    isExpanded && 'max-h-96 overflow-y-auto',
                    !isExpanded && `line-clamp-${maxLines}`,
                    className
                )}
            >
                {displayText}
                {!isExpanded && needsExpand && (
                    <div className="mt-2 text-xs text-muted-foreground italic">
                        ... (clique para expandir)
                    </div>
                )}
            </div>

            {needsExpand && (
                <div className="flex gap-2">
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="flex items-center gap-1 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                    >
                        {isExpanded ? (
                            <>
                                <ChevronUp className="h-4 w-4" />
                                Recolher
                            </>
                        ) : (
                            <>
                                <ChevronDown className="h-4 w-4" />
                                Expandir Texto Completo
                            </>
                        )}
                    </button>

                    <button
                        onClick={handleCopy}
                        className="flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
                        title="Copiar texto"
                    >
                        {copied ? (
                            <>
                                <Check className="h-4 w-4" />
                                Copiado
                            </>
                        ) : (
                            <>
                                <Copy className="h-4 w-4" />
                                Copiar
                            </>
                        )}
                    </button>
                </div>
            )}
        </div>
    );
}
