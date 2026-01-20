import { cn } from '@/lib/utils';
import { AlertCircle, BarChart3, Check, Loader2, TrendingUp } from 'lucide-react';
import { useEffect, useState } from 'react';

interface TrainingStatus {
    status: string;
    last_calibration: string | null;
    total_samples_used: number;
    accuracy_before: number;
    accuracy_after: number;
    improvement_percentage: number;
    time_since_last: string;
    by_source: Record<string, any>;
    recommendations: Array<{
        type: string;
        message: string;
        action: string;
    }>;
}

export function TrainingStatus() {
    const [status, setStatus] = useState<TrainingStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isAutoRefresh, setIsAutoRefresh] = useState(true);

    const fetchStatus = async () => {
        try {
            const data = await api.getTrainingStatus();
            if (data && !data.error) {
                setStatus(data);
                setError(null);
            } else {
                setError(data?.error || 'Erro ao carregar status');
            }
        } catch (err) {
            console.error('Erro ao buscar status:', err);
            setError('Erro ao carregar status de treinamento');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();

        // Auto-refresh a cada 10 segundos se estiver em progresso
        if (isAutoRefresh) {
            const interval = setInterval(fetchStatus, 10000);
            return () => clearInterval(interval);
        }
    }, [isAutoRefresh]);

    if (loading) {
        return (
            <div className="bg-card border border-border rounded-lg p-4 text-center">
                <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2 text-primary" />
                <p className="text-sm text-muted-foreground">Carregando status...</p>
            </div>
        );
    }

    if (error || !status) {
        return (
            <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center gap-2 text-destructive">
                    <AlertCircle className="h-4 w-4" />
                    <p className="text-sm">{error || 'Status indisponível'}</p>
                </div>
            </div>
        );
    }

    const statusColor =
        status.status === 'fresh' ? 'text-green-600' :
            status.status === 'recent' ? 'text-yellow-600' :
                status.status === 'stale' ? 'text-orange-600' :
                    'text-gray-500';

    const statusIcon =
        status.status === 'fresh' ? <Check className="h-4 w-4" /> :
            status.status === 'never_trained' ? <AlertCircle className="h-4 w-4" /> :
                <BarChart3 className="h-4 w-4" />;

    const statusLabel =
        status.status === 'fresh' ? 'Treinado Recentemente' :
            status.status === 'recent' ? 'Treinado Hoje' :
                status.status === 'stale' ? 'Treinado há tempo' :
                    'Nunca Treinado';

    return (
        <div className="space-y-4">
            {/* Card Principal */}
            <div className={cn(
                'bg-card border rounded-lg p-4',
                status.status === 'fresh' && 'border-green-500/30 bg-green-500/5',
                status.status === 'recent' && 'border-yellow-500/30 bg-yellow-500/5',
                status.status === 'stale' && 'border-orange-500/30 bg-orange-500/5',
            )}>
                <div className="flex items-start justify-between mb-4">
                    <div>
                        <h3 className="font-semibold text-sm mb-1">Status de Calibração</h3>
                        <div className={cn('flex items-center gap-2 text-sm', statusColor)}>
                            {statusIcon}
                            <span>{statusLabel}</span>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-2xl font-bold text-foreground">
                            {(status.accuracy_after * 100).toFixed(1)}%
                        </div>
                        <p className="text-xs text-muted-foreground">Acurácia Atual</p>
                    </div>
                </div>

                {/* Métricas */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                    <div className="bg-background/50 rounded p-2">
                        <p className="text-xs text-muted-foreground">Amostras</p>
                        <p className="text-lg font-semibold">{status.total_samples_used}</p>
                    </div>
                    <div className="bg-background/50 rounded p-2">
                        <p className="text-xs text-muted-foreground">Antes</p>
                        <p className="text-lg font-semibold">{(status.accuracy_before * 100).toFixed(1)}%</p>
                    </div>
                    <div className={cn(
                        "bg-background/50 rounded p-2 border",
                        status.improvement_percentage > 0 && "border-green-500/30 bg-green-500/10"
                    )}>
                        <p className="text-xs text-muted-foreground">Melhoria</p>
                        <p className={cn(
                            "text-lg font-semibold",
                            status.improvement_percentage > 0 ? "text-green-600" : "text-gray-500"
                        )}>
                            {status.improvement_percentage > 0 ? '+' : ''}{status.improvement_percentage.toFixed(1)}%
                        </p>
                    </div>
                </div>

                {/* Timestamp */}
                {status.last_calibration && (
                    <p className="text-xs text-muted-foreground">
                        Última calibração: {status.time_since_last}
                    </p>
                )}
            </div>

            {/* Por Fonte */}
            {Object.keys(status.by_source).length > 0 && (
                <div className="bg-card border border-border rounded-lg p-4">
                    <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" />
                        Calibradores por Fonte
                    </h4>
                    <div className="space-y-2">
                        {Object.entries(status.by_source).map(([source, data]: [string, any]) => (
                            <div key={source} className="bg-background/50 rounded p-2">
                                <div className="flex justify-between items-start mb-1">
                                    <span className="text-xs font-medium capitalize">{source}</span>
                                    <span className={cn(
                                        "text-xs font-semibold",
                                        data.avg_improvement > 0 ? "text-green-600" : "text-gray-500"
                                    )}>
                                        {data.avg_improvement > 0 ? '+' : ''}{(data.avg_improvement * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    {data.num_calibrations} treinamento(s) · {data.total_samples} amostras
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Recomendações */}
            {status.recommendations && status.recommendations.length > 0 && (
                <div className="bg-card border border-border rounded-lg p-4 space-y-2">
                    <h4 className="text-sm font-semibold mb-2">Recomendações</h4>
                    {status.recommendations.map((rec, idx) => (
                        <div
                            key={idx}
                            className={cn(
                                'text-xs p-2 rounded border-l-2',
                                rec.type === 'ready_for_finetuning' && 'bg-green-500/10 border-l-green-500 text-green-700',
                                rec.type === 'needs_attention' && 'bg-orange-500/10 border-l-orange-500 text-orange-700',
                                rec.type === 'collect_more_data' && 'bg-blue-500/10 border-l-blue-500 text-blue-700',
                            )}
                        >
                            <p>{rec.message}</p>
                            {rec.action && <p className="text-xs opacity-70 mt-1">→ {rec.action}</p>}
                        </div>
                    ))}
                </div>
            )}

            {/* Auto-Refresh Toggle */}
            <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer">
                <input
                    type="checkbox"
                    checked={isAutoRefresh}
                    onChange={(e) => setIsAutoRefresh(e.target.checked)}
                    className="rounded"
                />
                Atualizar automaticamente
            </label>
        </div>
    );
}
