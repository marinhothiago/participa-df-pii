import { api, type EntityFeedback, type FeedbackRequest } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Check, ChevronDown, ChevronUp, Loader2, MessageSquare, RefreshCw, X } from 'lucide-react';
import { useEffect, useState } from 'react';

// Chave para armazenar feedbacks no localStorage
const FEEDBACK_STORAGE_KEY = 'participa_df_feedbacks';

// Função para gerar hash simples do texto (para identificar análises únicas)
function hashText(text: string): string {
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
        const char = text.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    return hash.toString(36);
}

// Função para carregar feedbacks salvos
function loadSavedFeedbacks(): Record<string, { timestamp: string; entityCount: number }> {
    try {
        const saved = localStorage.getItem(FEEDBACK_STORAGE_KEY);
        return saved ? JSON.parse(saved) : {};
    } catch {
        return {};
    }
}

// Função para salvar feedback
function saveFeedback(textHash: string, entityCount: number): void {
    try {
        const feedbacks = loadSavedFeedbacks();
        feedbacks[textHash] = {
            timestamp: new Date().toISOString(),
            entityCount,
        };
        localStorage.setItem(FEEDBACK_STORAGE_KEY, JSON.stringify(feedbacks));
    } catch {
        console.error('Erro ao salvar feedback no localStorage');
    }
}

// Função para verificar se já enviou feedback
function hasSentFeedback(textHash: string): { sent: boolean; timestamp?: string; entityCount?: number } {
    const feedbacks = loadSavedFeedbacks();
    const feedback = feedbacks[textHash];
    if (feedback) {
        return { sent: true, timestamp: feedback.timestamp, entityCount: feedback.entityCount };
    }
    return { sent: false };
}

// Tipos de PII disponíveis para reclassificação
const PII_TYPES = [
    'CPF', 'CNPJ', 'RG', 'CNH', 'PIS', 'CNS', 'TITULO_ELEITOR', 'PASSAPORTE', 'CTPS',
    'EMAIL', 'TELEFONE', 'CELULAR', 'TELEFONE_INTERNACIONAL',
    'ENDERECO', 'CEP', 'ENDERECO_BRASILIA',
    'NOME', 'NOME_COMPLETO',
    'PIX', 'CONTA_BANCARIA', 'CARTAO_CREDITO',
    'PLACA_VEICULO', 'PROCESSO_CNJ', 'MATRICULA',
    'CID', 'DADO_BIOMETRICO', 'MENOR_IDENTIFICADO',
    'IP_ADDRESS', 'COORDENADAS_GPS', 'USER_AGENT',
    'OUTRO'
];

interface EntityFeedbackItemProps {
    entity: {
        tipo: string;
        valor: string;
        confianca?: number;
        fonte?: string;
    };
    onFeedback: (feedback: EntityFeedback) => void;
    disabled?: boolean;
}

function EntityFeedbackItem({ entity, onFeedback, disabled = false }: EntityFeedbackItemProps) {
    const [selectedValidation, setSelectedValidation] = useState<'CORRETO' | 'INCORRETO' | 'PARCIAL' | null>(null);
    const [showReclassify, setShowReclassify] = useState(false);
    const [newType, setNewType] = useState<string>('');
    const [comment, setComment] = useState('');

    const handleValidation = (validacao: 'CORRETO' | 'INCORRETO' | 'PARCIAL') => {
        if (validacao === 'PARCIAL') {
            setShowReclassify(!showReclassify);
            setSelectedValidation(validacao);
        } else {
            setSelectedValidation(validacao);
            setShowReclassify(false);
            onFeedback({
                tipo: entity.tipo,
                valor: entity.valor,
                confianca_modelo: entity.confianca ?? 0,
                fonte: entity.fonte,
                validacao_humana: validacao,
                comentario: comment || undefined,
            });
        }
    };

    const handleReclassify = () => {
        onFeedback({
            tipo: entity.tipo,
            valor: entity.valor,
            confianca_modelo: entity.confianca ?? 0,
            fonte: entity.fonte,
            validacao_humana: 'PARCIAL',
            tipo_corrigido: newType || undefined,
            comentario: comment || undefined,
        });
        setShowReclassify(false);
    };

    return (
        <div className={cn(
            "rounded-lg border transition-colors",
            selectedValidation === 'CORRETO' && "bg-green-500/10 border-green-500/30",
            selectedValidation === 'INCORRETO' && "bg-red-500/10 border-red-500/30",
            selectedValidation === 'PARCIAL' && "bg-yellow-500/10 border-yellow-500/30",
            !selectedValidation && "bg-muted/50 border-border"
        )}>
            <div className="flex items-center justify-between gap-2 p-2">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-muted-foreground">{entity.tipo}</span>
                        {entity.confianca !== undefined && (
                            <span className="text-xs text-muted-foreground">
                                ({(entity.confianca * 100).toFixed(0)}%)
                            </span>
                        )}
                    </div>
                    <p className="text-sm font-mono truncate" title={entity.valor}>
                        {entity.valor}
                    </p>
                </div>

                <div className="flex items-center gap-1">
                    <button
                        type="button"
                        title="Correto - É PII"
                        className={cn(
                            "h-7 w-7 rounded border flex items-center justify-center text-xs",
                            selectedValidation === 'CORRETO'
                                ? "bg-green-600 text-white border-green-600"
                                : "bg-background border-input hover:bg-accent"
                        )}
                        onClick={() => handleValidation('CORRETO')}
                        disabled={disabled}
                    >
                        <Check className="h-3 w-3" />
                    </button>

                    <button
                        type="button"
                        title="Incorreto - Falso Positivo"
                        className={cn(
                            "h-7 w-7 rounded border flex items-center justify-center text-xs",
                            selectedValidation === 'INCORRETO'
                                ? "bg-red-600 text-white border-red-600"
                                : "bg-background border-input hover:bg-accent"
                        )}
                        onClick={() => handleValidation('INCORRETO')}
                        disabled={disabled}
                    >
                        <X className="h-3 w-3" />
                    </button>

                    <button
                        type="button"
                        title="Reclassificar"
                        className={cn(
                            "h-7 w-7 rounded border flex items-center justify-center text-xs",
                            selectedValidation === 'PARCIAL'
                                ? "bg-yellow-600 text-white border-yellow-600"
                                : "bg-background border-input hover:bg-accent"
                        )}
                        onClick={() => handleValidation('PARCIAL')}
                        disabled={disabled}
                    >
                        {showReclassify ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                    </button>
                </div>
            </div>

            {showReclassify && (
                <div className="px-2 pb-2 pt-1 border-t border-border/50 space-y-2">
                    <div className="flex items-center gap-2">
                        <select
                            value={newType}
                            onChange={(e) => setNewType(e.target.value)}
                            className="h-7 text-xs flex-1 rounded border border-input bg-background px-2"
                        >
                            <option value="">Tipo correto...</option>
                            {PII_TYPES.map((type) => (
                                <option key={type} value={type}>{type}</option>
                            ))}
                        </select>
                        <button
                            type="button"
                            className="h-7 px-2 text-xs rounded bg-primary text-primary-foreground hover:bg-primary/90"
                            onClick={handleReclassify}
                        >
                            OK
                        </button>
                    </div>
                    <input
                        type="text"
                        placeholder="Comentário..."
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        className="w-full h-7 text-xs rounded border border-input bg-background px-2"
                    />
                </div>
            )}
        </div>
    );
}

interface FeedbackPanelProps {
    analysisId?: string;
    originalText: string;
    entities: Array<{
        tipo: string;
        valor: string;
        confianca?: number;
        fonte?: string;
    }>;
    classificacao: string;
    onFeedbackSubmitted?: () => void;
}

export function FeedbackPanel({
    analysisId,
    originalText,
    entities,
    classificacao,
    onFeedbackSubmitted
}: FeedbackPanelProps) {
    const [entityFeedbacks, setEntityFeedbacks] = useState<EntityFeedback[]>([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [status, setStatus] = useState<'idle' | 'success' | 'error' | 'already_sent'>('idle');
    const [statusMessage, setStatusMessage] = useState('');
    const [classificacaoCorrigida, setClassificacaoCorrigida] = useState<string | null>(null);
    const [isEditing, setIsEditing] = useState(false);

    // Verificar se já enviou feedback para este texto
    const textHash = hashText(originalText);
    
    useEffect(() => {
        const previousFeedback = hasSentFeedback(textHash);
        if (previousFeedback.sent && !isEditing) {
            setStatus('already_sent');
            const date = previousFeedback.timestamp 
                ? new Date(previousFeedback.timestamp).toLocaleString('pt-BR')
                : '';
            setStatusMessage(`Enviado em ${date} (${previousFeedback.entityCount} entidades)`);
        }
    }, [textHash, isEditing]);

    const handleEntityFeedback = (feedback: EntityFeedback) => {
        setEntityFeedbacks(prev => {
            const filtered = prev.filter(f => f.valor !== feedback.valor);
            return [...filtered, feedback];
        });
    };

    const handleSubmit = async () => {
        if (entityFeedbacks.length === 0) {
            setStatus('error');
            setStatusMessage('Valide pelo menos uma entidade');
            return;
        }

        setIsSubmitting(true);
        setStatus('idle');

        try {
            const feedbackRequest: FeedbackRequest = {
                analysis_id: analysisId,
                original_text: originalText,
                entity_feedbacks: entityFeedbacks,
                classificacao_modelo: classificacao,
                classificacao_corrigida: classificacaoCorrigida ?? undefined,
            };

            const response = await api.submitFeedback(feedbackRequest);

            // Salvar no localStorage que já enviou feedback
            saveFeedback(textHash, entityFeedbacks.length);

            setStatus('success');
            setStatusMessage(`Acurácia: ${(response.stats.accuracy * 100).toFixed(1)}%`);
            setIsEditing(false);

            // Dispara evento para atualizar TrainingStatus
            window.dispatchEvent(new CustomEvent('feedbackSubmitted'));

            onFeedbackSubmitted?.();
        } catch (error) {
            setStatus('error');
            setStatusMessage('Erro ao enviar. Tente novamente.');
            console.error('Erro ao enviar feedback:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleResubmit = () => {
        setIsEditing(true);
        setStatus('idle');
        setEntityFeedbacks([]);
    };

    const validatedCount = entityFeedbacks.length;

    // Estado: Já foi enviado anteriormente
    if (status === 'already_sent') {
        return (
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                        <Check className="h-5 w-5 text-blue-600" />
                        <p className="text-sm font-medium text-blue-600">Feedback já enviado</p>
                    </div>
                </div>
                <p className="text-xs text-muted-foreground mb-3">{statusMessage}</p>
                <button
                    type="button"
                    onClick={handleResubmit}
                    className="w-full h-8 rounded text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                >
                    <RefreshCw className="h-3 w-3" />
                    Reenviar Feedback
                </button>
            </div>
        );
    }

    // Estado: Feedback enviado com sucesso agora
    if (status === 'success') {
        return (
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 text-center">
                <Check className="h-6 w-6 text-green-600 mx-auto mb-1" />
                <p className="text-sm font-medium text-green-600">Feedback enviado!</p>
                <p className="text-xs text-muted-foreground">{statusMessage}</p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4 text-primary" />
                    <span className="text-sm font-medium">Validar Detecção</span>
                </div>
                <span className="text-xs text-muted-foreground">
                    {validatedCount}/{entities.length}
                </span>
            </div>

            {status === 'error' && (
                <div className="text-xs text-red-500 bg-red-500/10 p-2 rounded">
                    {statusMessage}
                </div>
            )}

            <div className="space-y-2 max-h-48 overflow-y-auto">
                {entities.map((entity, index) => (
                    <EntityFeedbackItem
                        key={`${entity.tipo}-${index}`}
                        entity={entity}
                        onFeedback={handleEntityFeedback}
                        disabled={isSubmitting}
                    />
                ))}
            </div>

            {classificacao === 'NÃO PÚBLICO' && (
                <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer">
                    <input
                        type="checkbox"
                        className="rounded"
                        onChange={(e) => setClassificacaoCorrigida(e.target.checked ? 'PÚBLICO' : null)}
                    />
                    Este texto é na verdade <strong>PÚBLICO</strong>
                </label>
            )}

            <button
                type="button"
                onClick={handleSubmit}
                disabled={isSubmitting || entityFeedbacks.length === 0}
                className={cn(
                    "w-full h-9 rounded text-sm font-medium transition-colors",
                    entityFeedbacks.length === 0
                        ? "bg-muted text-muted-foreground cursor-not-allowed"
                        : "bg-primary text-primary-foreground hover:bg-primary/90"
                )}
            >
                {isSubmitting ? (
                    <span className="flex items-center justify-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Enviando...
                    </span>
                ) : (
                    `Enviar (${validatedCount})`
                )}
            </button>
        </div>
    );
}
