from .celery_worker import celery_app
from src.detector import PIIDetector
import pandas as pd
import os

@celery_app.task(bind=True)
def processar_lote(self, arquivo_path, tipo_arquivo='csv', params=None):
    """
    Processa um arquivo CSV/XLSX em lote usando o PIIDetector.
    Salva o resultado em arquivo e retorna o caminho.
    """
    detector = PIIDetector(usar_gpu=False)
    if tipo_arquivo == 'csv':
        df = pd.read_csv(arquivo_path)
    elif tipo_arquivo == 'xlsx':
        df = pd.read_excel(arquivo_path)
    else:
        raise ValueError('Tipo de arquivo não suportado')

    resultados = []
    for idx, row in df.iterrows():
        texto = row.get('texto') or row.get('Texto') or str(row)
        is_pii, findings, nivel_risco, confianca = detector.detect(texto)
        resultados.append({
            'linha': idx,
            'texto': texto,
            'is_pii': is_pii,
            'findings': findings,
            'nivel_risco': nivel_risco,
            'confianca': confianca
        })
    # Salva resultado
    saida_path = arquivo_path + '.resultado.json'
    import json
    with open(saida_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    return saida_path
