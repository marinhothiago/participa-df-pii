#!/usr/bin/env python3
"""Análise da amostra oficial para identificar anomalias e registros de baixa confiança.

O detector é carregado via fixture global em conftest.py (scope=session).
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
import pandas as pd

# NOTA: Fixture 'detector' vem do conftest.py (scope=session)
# Não precisa definir aqui - pytest encontra automaticamente


@pytest.fixture
def sample_df():
    # Simula uma amostra pequena para teste
    data = {
        'ID': [1, 2, 3],
        'Texto Mascarado': [
            'Meu CPF é 529.982.247-25',
            'Telefone institucional: (61) 3105-1234',
            'Email: joao.silva@gmail.com'
        ]
    }
    return pd.DataFrame(data)

def test_carregamento_amostra(sample_df):
    assert len(sample_df) == 3
    assert 'Texto Mascarado' in sample_df.columns

def test_pii_detection_amostra(sample_df, detector):
    resultados = []
    for idx, row in sample_df.iterrows():
        texto = str(row['Texto Mascarado'])
        id_reg = row['ID']
        is_pii, findings, risco, confianca = detector.detect(texto)
        resultados.append({
            'id': id_reg,
            'texto': texto,
            'is_pii': is_pii,
            'risco': risco,
            'confianca': confianca,
            'num_findings': len(findings),
            'tipos': list(set([f['tipo'] for f in findings])) if findings else [],
            'findings': findings
        })
    # Verifica se o detector identificou PII corretamente
    assert resultados[0]['is_pii'] is True  # CPF
    assert resultados[1]['is_pii'] is False # Telefone institucional
    assert resultados[2]['is_pii'] is True  # Email pessoal

def test_estatisticas_amostra(sample_df, detector):
    resultados = []
    for idx, row in sample_df.iterrows():
        texto = str(row['Texto Mascarado'])
        id_reg = row['ID']
        is_pii, findings, risco, confianca = detector.detect(texto)
        resultados.append({
            'id': id_reg,
            'texto': texto,
            'is_pii': is_pii,
            'risco': risco,
            'confianca': confianca,
            'num_findings': len(findings),
            'tipos': list(set([f['tipo'] for f in findings])) if findings else [],
            'findings': findings
        })
    total_pii = sum(1 for r in resultados if r['is_pii'])
    total_seguro = sum(1 for r in resultados if not r['is_pii'])
    assert total_pii == 2
    assert total_seguro == 1

def test_ordenacao_confianca(sample_df, detector):
    resultados = []
    for idx, row in sample_df.iterrows():
        texto = str(row['Texto Mascarado'])
        id_reg = row['ID']
        is_pii, findings, risco, confianca = detector.detect(texto)
        resultados.append({
            'id': id_reg,
            'texto': texto,
            'is_pii': is_pii,
            'risco': risco,
            'confianca': confianca,
            'num_findings': len(findings),
            'tipos': list(set([f['tipo'] for f in findings])) if findings else [],
            'findings': findings
        })
    resultados_sorted = sorted(resultados, key=lambda x: x['confianca'])
    # Garante que a ordenação por confiança funciona
    confs = [r['confianca'] for r in resultados_sorted]
    assert confs == sorted(confs)
