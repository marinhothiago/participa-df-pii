import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""
Testes de edge cases para o PIIDetector.
NOTA: O motor é CONSERVADOR - prefere detectar um falso positivo do que deixar passar PII real.
Por isso, formatos que PARECEM ser documentos são detectados mesmo com dígitos faltando.

O detector é carregado via fixture global em conftest.py (scope=session).
"""

import pytest

# NOTA: Fixture 'detector' vem do conftest.py (scope=session)
# Não instanciar PIIDetector() aqui para evitar carregamento duplicado

@pytest.mark.parametrize("texto, esperado", [
    # CPF válidos, inválidos, truncados, com letras
    ("Meu CPF é 123.456.789-09", True),
    ("CPF: 111.111.111-11", False),  # inválido (todos iguais) - blocklist
    ("CPF: 123.456.789", False),  # truncado (9 dígitos)
    ("CPF: 123.456.789-0A", False),  # letra no DV
    ("CPF: 12345678909", True),
    ("CPF: 1234567890", True),  # 10 dígitos com contexto "CPF:" = motor detecta como PII (erro digitação)
    # CNPJ - Motor detecta como PII (pode identificar empresa relacionada a pessoa)
    ("CNPJ: 12.345.678/0001-95", True),  # CNPJ detectado
    ("CNPJ: 11.111.111/1111-11", False),  # CNPJ todos iguais = inválido
    ("CNPJ: 12345678000195", True),  # CNPJ sem formatação
    ("CNPJ: 1234567800019", True),  # 13 dígitos pode ser detectado como CNH pelo contexto
    # Email
    ("Email: joao@gmail.com", True),
    ("Email: maria@empresa.gov.br", False),  # institucional gov.br
    ("Email: joao@@gmail.com", False),  # email malformado
    ("Email: joao.gmail.com", False),  # sem @
    # Telefone
    ("Telefone: +55 61 91234-5678", True),
    ("Telefone: (61) 91234-5678", True),
    ("Telefone: 91234-5678", True),
    ("Telefone: 1234-5678", True),
    ("Telefone: +1 202 555-0199", True),  # Internacional
    ("Telefone: 555-0199", False),  # Muito curto
    # Nomes
    ("Nome: João da Silva", True),
    ("Nome: XxXxXxXxXxXx", False),  # nome corrompido
    ("Nome: Maria das Graças Souza", True),
    ("Nome: TESTE BLOQUEADO", False),  # blocklist
    # PIX
    ("PIX: 123e4567-e89b-12d3-a456-426614174000", True),  # UUID
    ("PIX: 123.456.789-09", True),  # CPF como chave PIX
    ("PIX: joao@gmail.com", True),  # Email como chave PIX
    ("PIX: +55 61 91234-5678", True),  # Telefone como chave PIX
    ("PIX: 123456", False),  # Número curto
    # PADRÕES_GDF - PROCESSO SEI é público (não PII), mas PROTOCOLO pode conter dados pessoais
    ("PROCESSO SEI: 12345-1234567/2024-12", False),  # Processo público
    ("PROTOCOLO LAI: LAI-123456/2024", True),  # Protocolo LAI detectado
    ("PROTOCOLO OUV: OUV-654321/2022", True),  # Protocolo Ouvidoria detectado
    ("MATRICULA SERVIDOR: 1234567", True),  # Matrícula identifica servidor = PII
    ("INSCRICAO IMOVEL: 123456789012345", True),  # Inscrição identifica dono = PII
    ("PROCESSO SEI: 12345-123456/2024", False),  # Processo público
    ("PROTOCOLO LAI: LAI-123/2024", False),  # Muito curto
    ("PROTOCOLO OUV: OUV-12/2022", False),  # Muito curto
    ("MATRICULA SERVIDOR: 1234", False),  # Muito curto
    ("INSCRICAO IMOVEL: 12345", False),  # Muito curto
    # Ruídos e edge cases
    ("CPF: 123.456.789-09, CNPJ: 12.345.678/0001-95, Email: joao@gmail.com", True),  # CPF + Email = PII
    ("Nome: João da Silva, Telefone: +55 61 91234-5678, PIX: 123e4567-e89b-12d3-a456-426614174000", True),
    ("Texto sem nenhum dado pessoal", False),
    ("Números aleatórios: 1234567890, 987654321", False),  # Sem contexto de documento
])
def test_edge_cases(detector, texto, esperado):
    """Testa edge cases de detecção de PII.
    
    Args:
        detector: Fixture do PIIDetector (conftest.py, scope=session)
    """
    is_pii, findings, nivel_risco, confianca = detector.detect(texto)
    achou = any(r for r in findings if r['tipo'] != 'NOME_CONTRA')
    assert achou == esperado, f"Texto: {texto} | Esperado: {esperado} | Achou: {findings}"