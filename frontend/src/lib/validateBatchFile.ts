// Função utilitária para validação robusta de arquivos de lote (CSV/XLSX)
// Regras: formato, colunas obrigatórias, tipos, mensagens de erro detalhadas e exemplo de template

import * as XLSX from 'xlsx';

export type BatchFileValidationResult =
  | { valid: true; rows: { id: string; text: string }[] }
  | { valid: false; error: string; exampleCsv: string };

const REQUIRED_HEADERS = ['id', 'text'];

// Exemplo de template CSV para download em caso de erro
const EXAMPLE_CSV = 'id,text\n12345,Exemplo de texto para análise';

function normalizeHeader(header: string) {
  return header.trim().toLowerCase().replace(/\s+/g, '');
}

export async function validateBatchFile(file: File): Promise<BatchFileValidationResult> {
  // 1. Verifica extensão
  const ext = file.name.split('.').pop()?.toLowerCase();
  if (!['csv', 'xlsx'].includes(ext || '')) {
    return {
      valid: false,
      error: 'Formato não suportado. Envie um arquivo .csv ou .xlsx.',
      exampleCsv: EXAMPLE_CSV,
    };
  }

  // 2. Lê o arquivo
  let workbook: XLSX.WorkBook;
  try {
    const data = await file.arrayBuffer();
    workbook = XLSX.read(data, { type: 'array' });
  } catch (e) {
    return {
      valid: false,
      error: 'Não foi possível ler o arquivo. Verifique se está corrompido.',
      exampleCsv: EXAMPLE_CSV,
    };
  }

  // 3. Extrai a primeira planilha
  const sheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[sheetName];
  if (!sheet) {
    return {
      valid: false,
      error: 'Arquivo sem dados. Adicione pelo menos uma linha.',
      exampleCsv: EXAMPLE_CSV,
    };
  }

  // 4. Converte para JSON
  const rows: any[] = XLSX.utils.sheet_to_json(sheet, { defval: '', raw: false });
  if (!rows.length) {
    return {
      valid: false,
      error: 'Arquivo sem linhas de dados.',
      exampleCsv: EXAMPLE_CSV,
    };
  }

  // 5. Valida headers
  const headers = Object.keys(rows[0]).map(normalizeHeader);
  const missing = REQUIRED_HEADERS.filter(
    (h) => !headers.includes(normalizeHeader(h))
  );
  if (missing.length) {
    return {
      valid: false,
      error: `Colunas obrigatórias ausentes: ${missing.join(', ')}. O arquivo deve conter as colunas: id, text.`,
      exampleCsv: EXAMPLE_CSV,
    };
  }

  // 6. Valida cada linha
  const parsedRows: { id: string; text: string }[] = [];
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const id = row['id'] ?? row['ID'] ?? row['Id'] ?? row['Id '];
    const text = row['text'] ?? row['Text'] ?? row['texto'] ?? row['Texto'];
    if (!id || !text) {
      return {
        valid: false,
        error: `Linha ${i + 2}: id/texto ausente. Cada linha deve ter um id e um texto para análise.`,
        exampleCsv: EXAMPLE_CSV,
      };
    }
    parsedRows.push({ id: String(id).trim(), text: String(text).trim() });
  }

  // 7. Sucesso
  return { valid: true, rows: parsedRows };
}

// Função utilitária para baixar o template CSV
export function downloadExampleCsv() {
  const blob = new Blob([EXAMPLE_CSV], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'exemplo_lote.csv';
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 100);
}
