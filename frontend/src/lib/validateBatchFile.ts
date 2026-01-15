// Função utilitária para validação robusta de arquivos de lote (CSV/XLSX)
// Regras: formato, colunas obrigatórias, tipos, mensagens de erro detalhadas e exemplo de template

import * as XLSX from 'xlsx';

export type BatchFileValidationResult =
  | { valid: true; rows: { id: string; text: string }[] }
  | { valid: false; error: string; exampleCsv: string };


// Variações aceitas para as colunas obrigatórias
const ID_ALIASES = ['id', 'identificador', 'protocolo', 'idpedido', 'id_pedido'];
const TEXT_ALIASES = [
  'text', 'texto', 'texto_mascarado', 'texto mascarado', 'mascarado', 'mensagem', 'solicitacao', 'descrição', 'descricao', 'conteudo', 'conteúdo'
];

const EXAMPLE_CSV = 'id,texto mascarado\n12345,Exemplo de texto para análise';

function normalizeHeader(header: string) {
  return header.trim().toLowerCase().replace(/[^a-z0-9]/g, '');
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

  // 5. Detecta colunas id/texto por aliases
  const headerMap = Object.keys(rows[0]).reduce((acc, h) => {
    acc[normalizeHeader(h)] = h;
    return acc;
  }, {} as Record<string, string>);

  // Busca o header real para id/texto
  const idHeader = ID_ALIASES.map(normalizeHeader).find((alias) => alias in headerMap);
  const textHeader = TEXT_ALIASES.map(normalizeHeader).find((alias) => alias in headerMap);

  if (!idHeader || !textHeader) {
    return {
      valid: false,
      error: `Colunas obrigatórias ausentes. O arquivo deve conter uma coluna de id (ex: id, protocolo) e uma de texto (ex: texto, texto mascarado). Veja o exemplo.`,
      exampleCsv: EXAMPLE_CSV,
    };
  }

  // 6. Valida cada linha
  const parsedRows: { id: string; text: string }[] = [];
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const id = row[headerMap[idHeader]];
    const text = row[headerMap[textHeader]];
    if (!id || !text) {
      return {
        valid: false,
        error: `Linha ${i + 2}: id/texto ausente. Cada linha deve ter um id e um texto para análise.`,
        exampleCsv: EXAMPLE_CSV,
      };
    }
    parsedRows.push({ id: String(id).trim(), text: String(text).trim() });
  }

  // 7. Sucesso: informa ao usuário quais colunas foram reconhecidas
  return {
    valid: true,
    rows: parsedRows,
    // info extra pode ser usada na UI futuramente
    // idColumn: headerMap[idHeader],
    // textColumn: headerMap[textHeader],
  };
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
