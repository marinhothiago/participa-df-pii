#!/usr/bin/env python3
"""Análise da amostra oficial para identificar anomalias e registros de baixa confiança."""

import pandas as pd
from src.detector import PIIDetector

def main():
    # Carregar amostra
    df = pd.read_excel('data/input/AMOSTRA_e-SIC.xlsx')
    print(f'Total de registros: {len(df)}')
    print(f'Colunas: {df.columns.tolist()}')
    print()

    # Inicializar detector
    detector = PIIDetector()

    # Analisar cada registro
    resultados = []
    for idx, row in df.iterrows():
        texto = str(row['Texto Mascarado']) if 'Texto Mascarado' in df.columns else str(row.iloc[1])
        id_reg = row['ID'] if 'ID' in df.columns else idx
        
        is_pii, findings, risco, confianca = detector.detect(texto)
        
        resultados.append({
            'id': id_reg,
            'texto': texto[:100],
            'texto_full': texto,
            'is_pii': is_pii,
            'risco': risco,
            'confianca': confianca,
            'num_findings': len(findings),
            'tipos': list(set([f['tipo'] for f in findings])) if findings else [],
            'findings': findings
        })

    # Estatísticas gerais
    print('=' * 80)
    print('ESTATISTICAS GERAIS')
    print('=' * 80)
    total_pii = sum(1 for r in resultados if r['is_pii'])
    total_seguro = sum(1 for r in resultados if not r['is_pii'])
    print(f'Total com PII: {total_pii} ({100*total_pii/len(resultados):.1f}%)')
    print(f'Total SEGURO: {total_seguro} ({100*total_seguro/len(resultados):.1f}%)')
    print()

    # Distribuição por risco
    print('Distribuicao por nivel de risco:')
    riscos = {}
    for r in resultados:
        riscos[r['risco']] = riscos.get(r['risco'], 0) + 1
    for risco, count in sorted(riscos.items()):
        print(f'  {risco}: {count}')
    print()

    # Tipos de PII encontrados
    print('Tipos de PII encontrados:')
    tipos_count = {}
    for r in resultados:
        for t in r['tipos']:
            tipos_count[t] = tipos_count.get(t, 0) + 1
    for tipo, count in sorted(tipos_count.items(), key=lambda x: -x[1]):
        print(f'  {tipo}: {count}')
    print()

    # Ordenar por confiança (menor primeiro)
    resultados_sorted = sorted(resultados, key=lambda x: x['confianca'])

    print('=' * 80)
    print('TOP 15 REGISTROS COM MENOR CONFIANCA (potenciais problemas)')
    print('=' * 80)
    for r in resultados_sorted[:15]:
        print(f"ID {r['id']}: conf={r['confianca']:.4f} | risco={r['risco']} | PII={r['is_pii']}")
        print(f"   Tipos: {r['tipos']}")
        print(f"   Texto: {r['texto'][:75]}...")
        if r['findings']:
            for f in r['findings'][:3]:
                val = f['valor'][:40] if len(f['valor']) > 40 else f['valor']
                print(f"   -> {f['tipo']}: '{val}' (conf={f['confianca']:.4f})")
        print()

    # Registros SEGUROS (sem PII) - verificar se algum deveria ter PII
    print('=' * 80)
    print('REGISTROS CLASSIFICADOS COMO SEGURO (verificar FN)')
    print('=' * 80)
    seguros = [r for r in resultados if not r['is_pii']]
    for r in seguros[:10]:
        print(f"ID {r['id']}: {r['texto'][:80]}...")
        print()

if __name__ == '__main__':
    main()
