import pytest
from src.detector import PIIDetector

detector = PIIDetector(usar_gpu=False)

@pytest.mark.parametrize("texto, esperado", [
    # CPF válidos, inválidos, truncados, com letras
    ("Meu CPF é 123.456.789-09", True),
    ("CPF: 111.111.111-11", False),  # inválido (todos iguais)
    ("CPF: 123.456.789", False),  # truncado
    ("CPF: 123.456.789-0A", False),  # letra no DV
    ("CPF: 12345678909", True),
    ("CPF: 1234567890", False),
    # CNPJ
    ("CNPJ: 12.345.678/0001-95", True),
    ("CNPJ: 11.111.111/1111-11", False),
    ("CNPJ: 12345678000195", True),
    ("CNPJ: 1234567800019", False),
    # Email
    ("Email: joao@gmail.com", True),
    ("Email: maria@empresa.gov.br", False),  # institucional
    ("Email: joao@@gmail.com", False),
    ("Email: joao.gmail.com", False),
    # Telefone
    ("Telefone: +55 61 91234-5678", True),
    ("Telefone: (61) 91234-5678", True),
    ("Telefone: 91234-5678", True),
    ("Telefone: 1234-5678", True),
    ("Telefone: +1 202 555-0199", True),
    ("Telefone: 555-0199", False),
    # Nomes
    ("Nome: João da Silva", True),
    ("Nome: XxXxXxXxXxXx", False),  # nome corrompido
    ("Nome: Maria das Graças Souza", True),
    ("Nome: TESTE BLOQUEADO", False),  # blocklist
    # PIX
    ("PIX: 123e4567-e89b-12d3-a456-426614174000", True),
    ("PIX: 123.456.789-09", True),  # CPF
    ("PIX: joao@gmail.com", True),
    ("PIX: +55 61 91234-5678", True),
    ("PIX: 123456", False),
    # PADRÕES_GDF
    ("PROCESSO SEI: 12345-1234567/2024-12", True),
    ("PROTOCOLO LAI: LAI-123456/2024", True),
    ("PROTOCOLO OUV: OUV-654321/2022", True),
    ("MATRICULA SERVIDOR: 1234567", True),
    ("INSCRICAO IMOVEL: 123456789012345", True),
    ("PROCESSO SEI: 12345-123456/2024", True),
    ("PROTOCOLO LAI: LAI-123/2024", False),
    ("PROTOCOLO OUV: OUV-12/2022", False),
    ("MATRICULA SERVIDOR: 1234", False),
    ("INSCRICAO IMOVEL: 12345", False),
    # Ruídos e edge cases
    ("CPF: 123.456.789-09, CNPJ: 12.345.678/0001-95, Email: joao@gmail.com", True),
    ("Nome: João da Silva, Telefone: +55 61 91234-5678, PIX: 123e4567-e89b-12d3-a456-426614174000", True),
    ("Texto sem nenhum dado pessoal", False),
    ("Números aleatórios: 1234567890, 987654321", False),
])
def test_edge_cases(texto, esperado):
    is_pii, findings, nivel_risco, confianca = detector.detect(texto)
    achou = any(r for r in findings if r['tipo'] != 'NOME_CONTRA')
    assert achou == esperado, f"Texto: {texto} | Esperado: {esperado} | Achou: {findings}"