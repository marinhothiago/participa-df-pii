import { useCallback, useState } from 'react';
import { Upload, FileSpreadsheet, X, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { validateBatchFile, downloadExampleCsv, BatchFileValidationResult } from '@/lib/validateBatchFile';

interface FileDropzoneProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  disabled?: boolean;
}

export function FileDropzone({ onFileSelect, accept = '.csv,.xlsx', disabled }: FileDropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [exampleCsv, setExampleCsv] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragOver(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);


  const handleFile = useCallback(async (file: File) => {
    setError(null);
    setExampleCsv(null);
    const result: BatchFileValidationResult = await validateBatchFile(file);
    if (result.valid) {
      setSelectedFile(file);
      setError(null);
      setExampleCsv(null);
      onFileSelect(file);
    } else {
      setSelectedFile(null);
      setError(result.error);
      setExampleCsv(result.exampleCsv);
    }
  }, [onFileSelect]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  }, [disabled, handleFile]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  }, [handleFile]);

  const clearFile = useCallback(() => {
    setSelectedFile(null);
    setError(null);
    setExampleCsv(null);
  }, []);

  return (
    <div className="space-y-4">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          'relative border-2 border-dashed rounded-lg p-8 transition-all duration-200 text-center',
          isDragOver && !disabled && 'border-primary bg-primary/5',
          !isDragOver && !disabled && 'border-border hover:border-primary/50 hover:bg-accent/30',
          disabled && 'opacity-50 cursor-not-allowed',
        )}
      >
        <input
          type="file"
          accept={accept}
          onChange={handleFileInput}
          disabled={disabled}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
        />
        <div className="flex flex-col items-center gap-4">
          <div className={cn(
            'p-4 rounded-full transition-colors',
            isDragOver ? 'bg-primary/10' : 'bg-muted'
          )}>
            <Upload className={cn(
              'w-8 h-8',
              isDragOver ? 'text-primary' : 'text-muted-foreground'
            )} />
          </div>
          <div>
            <p className="text-base font-medium text-foreground">
              Arraste e solte seu arquivo aqui
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              ou clique para selecionar
            </p>
          </div>
          <p className="text-xs text-muted-foreground bg-muted px-3 py-1.5 rounded-full">
            Formatos aceitos: CSV, XLSX
          </p>
        </div>
      </div>

      {error && (
        <div className="flex flex-col items-center gap-2 p-3 bg-destructive/10 border border-destructive/30 rounded-lg animate-fade-in">
          <div className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-semibold">Erro no arquivo:</span>
          </div>
          <p className="text-sm text-destructive text-center">{error}</p>
          {exampleCsv && (
            <Button variant="outline" size="sm" onClick={downloadExampleCsv} className="mt-1">
              Baixar exemplo CSV
            </Button>
          )}
        </div>
      )}

      {selectedFile && !error && (
        <div className="flex items-center justify-between p-3 bg-accent/50 rounded-lg animate-fade-in">
          <div className="flex items-center gap-3">
            <FileSpreadsheet className="w-5 h-5 text-primary" />
            <div>
              <p className="text-sm font-medium text-foreground">{selectedFile.name}</p>
              <p className="text-xs text-muted-foreground">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={clearFile}
            className="h-8 w-8 text-muted-foreground hover:text-destructive"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      )}

      <p className="text-xs text-muted-foreground text-center">
        💡 Utilize o arquivo <code className="bg-muted px-1.5 py-0.5 rounded">AMOSTRA_e-SIC.xlsx</code> para testes ou baixe o exemplo CSV acima.
      </p>
    </div>
  );
}
