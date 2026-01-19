import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

@pytest.fixture
def mock_dados():
    return [
        {"id": 1, "confianca": "95.0", "classificacao": "PÚBLICO", "identificadores": "Nome: João"},
        {"id": 2, "confianca": "88.0", "classificacao": "NÃO PÚBLICO", "identificadores": "CPF: 123.456.789-09"},
        {"id": 3, "confianca": "45.0", "classificacao": "PÚBLICO", "identificadores": "Email: joao@email.com"},
        {"id": 4, "confianca": "72.0", "classificacao": "NÃO PÚBLICO", "identificadores": "Telefone: (61) 99999-8888"},
        {"id": 5, "confianca": "99.0", "classificacao": "PÚBLICO", "identificadores": "Nome: Maria"},
    ]

def test_estatisticas_confianca(mock_dados):
    confs = [float(d['confianca']) for d in mock_dados]
    media = sum(confs) / len(confs)
    confs_sorted = sorted(confs)
    mediana = confs_sorted[len(confs_sorted)//2]
    acima_85 = sum(1 for c in confs if c >= 85)
    acima_90 = sum(1 for c in confs if c >= 90)
    abaixo_50 = sum(1 for c in confs if c < 50)
    publicos = sum(1 for d in mock_dados if 'PÚBLICO' in d['classificacao'] and 'NÃO' not in d['classificacao'])
    nao_publicos = sum(1 for d in mock_dados if 'NÃO PÚBLICO' in d['classificacao'])
    assert media == pytest.approx(79.8, 0.1)
    assert mediana == 88.0
    assert acima_85 == 3
    assert acima_90 == 2
    assert abaixo_50 == 1
    assert publicos == 3
    assert nao_publicos == 2

def test_filtragem_baixa_confianca(mock_dados):
    abaixo_50 = [d for d in mock_dados if float(d['confianca']) < 50]
    assert len(abaixo_50) == 1
    assert abaixo_50[0]['id'] == 3
