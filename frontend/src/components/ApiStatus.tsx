import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { AlertCircle, CheckCircle2, Loader2, RefreshCw } from 'lucide-react';

interface ApiStatusProps {
  status: 'online' | 'offline' | 'loading' | 'waking';
  onRetry?: () => void;
}

export function ApiStatus({ status, onRetry }: ApiStatusProps) {
  const apiUrl = 'https://marinhothiago-desafio-participa-df.hf.space';

  return (
    <div className="flex items-center gap-2">
      <a
        href={apiUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2"
      >
        <div
          className={cn(
            'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium hover:opacity-80 transition-opacity',
            status === 'online' && 'bg-success/10 text-success',
            status === 'offline' && 'bg-destructive/10 text-destructive',
            status === 'loading' && 'bg-muted text-muted-foreground',
            status === 'waking' && 'bg-warning/10 text-warning',
          )}
        >
          {status === 'loading' && (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Conectando...</span>
            </>
          )}
          {status === 'online' && (
            <>
              <CheckCircle2 className="w-4 h-4" />
              <span>API Online</span>
            </>
          )}
          {status === 'offline' && (
            <>
              <AlertCircle className="w-4 h-4" />
              <span>API Offline</span>
            </>
          )}
          {status === 'waking' && (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Acordando...</span>
            </>
          )}
          <ExternalLink className="w-3 h-3 ml-1 opacity-70" />
        </div>
      </a>

      {(status === 'offline' || status === 'waking') && onRetry && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onRetry}
          className="h-8 w-8 p-0"
        >
          <RefreshCw className="w-4 h-4" />
        </Button>
      )}
    </div>
  );
}
