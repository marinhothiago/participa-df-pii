import { useState } from 'react';
import { Download, FileSpreadsheet, FileJson, FileText, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { type AnalysisHistoryItem, getRiskLabel } from '@/contexts/AnalysisContext';
import * as XLSX from 'xlsx';

interface ExportButtonProps {
  data: AnalysisHistoryItem[];
  disabled?: boolean;
}

export function ExportButton({ data, disabled = false }: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false);

  // Usa função global centralizada
  import { normalizeConfidence } from '@/components/ConfidenceBar';

  const formatDataForExport = () => {
    return data.map((item, index) => {
      const normalizedProbability = normalizeConfidence(item.probability, item.classification);
      return {
        'ID': index + 1,
        'Data': item.date,
        'Horário': item.time,
        'Tipo': item.type === 'individual' ? 'Individual' : 'Lote',
        'Classificação': item.classification,
        'Confiança': (normalizedProbability * 100).toFixed(1) + '%',
        'Risco': normalizedProbability.toFixed(2),
        'Nível de Risco': getRiskLabel(item.riskLevel),
        'Prévia do Pedido': item.text,
        'Dados Identificados': item.details.map(d => `${d.tipo}: ${d.valor}`).join('; ') || 'Nenhum',
      };
    });
  };

  const exportToXLSX = () => {
    setIsExporting(true);
    try {
      const exportData = formatDataForExport();
      const worksheet = XLSX.utils.json_to_sheet(exportData);
      const workbook = XLSX.utils.book_new();
      
      // Set column widths
      const colWidths = [
        { wch: 5 },   // ID
        { wch: 12 },  // Data
        { wch: 8 },   // Horário
        { wch: 10 },  // Tipo
        { wch: 12 },  // Classificação
        { wch: 12 },  // Probabilidade
        { wch: 8 },   // Risco
        { wch: 12 },  // Nível de Risco
        { wch: 50 },  // Prévia
        { wch: 40 },  // Dados
      ];
      worksheet['!cols'] = colWidths;
      
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Classificação PII');
      XLSX.writeFile(workbook, `relatorio_pii_participa_df.xlsx`);
    } catch (error) {
      console.error('Error exporting XLSX:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const exportToCSV = () => {
    setIsExporting(true);
    try {
      const exportData = formatDataForExport();
      const worksheet = XLSX.utils.json_to_sheet(exportData);
      const csv = XLSX.utils.sheet_to_csv(worksheet, { FS: ';' });
      
      const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'relatorio_pii_participa_df.csv';
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting CSV:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const exportToJSON = () => {
    setIsExporting(true);
    try {
      const exportData = data.map((item, index) => ({
        id: index + 1,
        data: item.date,
        horario: item.time,
        tipo: item.type,
        classificacao: item.classification,
        probabilidade: item.probability,
        nivel_risco: item.riskLevel,
        previa_pedido: item.text,
        dados_identificados: item.details,
      }));
      
      const json = JSON.stringify(exportData, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'relatorio_pii_participa_df.json';
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting JSON:', error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="outline" 
          size="sm" 
          disabled={disabled || isExporting}
          className="bg-slate-700 hover:bg-slate-600 text-white border-slate-600"
        >
          <Download className="w-4 h-4 mr-2" />
          Baixar Relatório
          <ChevronDown className="w-4 h-4 ml-2" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuItem onClick={exportToXLSX} className="cursor-pointer">
          <FileSpreadsheet className="w-4 h-4 mr-2 text-green-600" />
          Excel (.xlsx)
        </DropdownMenuItem>
        <DropdownMenuItem onClick={exportToCSV} className="cursor-pointer">
          <FileText className="w-4 h-4 mr-2 text-blue-600" />
          CSV (.csv)
        </DropdownMenuItem>
        <DropdownMenuItem onClick={exportToJSON} className="cursor-pointer">
          <FileJson className="w-4 h-4 mr-2 text-orange-600" />
          JSON (.json)
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
