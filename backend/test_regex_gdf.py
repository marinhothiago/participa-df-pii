# Trigger CI - comentário para disparar workflow

import re
import sys
import os
import pytest

# Garante import do detector
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from src.detector import PIIDetector

# Casos reais e edge cases dos padrões GDF
CASES = [
    # PROCESSO_SEI
    ("Processo SEI 12345-1234567/2024-12", 'PROCESSO_SEI', True),
    ("Referência SEI 54321-7654321/2023-01", 'PROCESSO_SEI', True),
    ("Processo SEI 00015-01009853/2026-01", 'PROCESSO_SEI', True),
    ("Processo 12345-1234567/2024", 'PROCESSO_SEI', True),
    ("Processo 1234-123456/2024", 'PROCESSO_SEI', True),
    ("Processo 12345-1234567/2024", 'PROCESSO_SEI', True),
    # PROTOCOLO_LAI
    ("Protocolo LAI LAI-123456/2024", 'PROTOCOLO_LAI', True),
    ("Protocolo LAI LAI-12345/2024", 'PROTOCOLO_LAI', True),
    ("Protocolo LAI LAI-1234567/2024", 'PROTOCOLO_LAI', True),
    # PROTOCOLO_OUV
    ("Protocolo OUV OUV-654321/2022", 'PROTOCOLO_OUV', True),
    ("Protocolo OUV OUV-123456/2022", 'PROTOCOLO_OUV', True),
    ("Protocolo OUV OUV-1234567/2022", 'PROTOCOLO_OUV', True),
    # MATRICULA_SERVIDOR
    ("Matrícula do servidor: 98.123-3", 'MATRICULA_SERVIDOR', True),
    ("Matrícula funcional: 12345678A", 'MATRICULA_SERVIDOR', True),
    ("Matrícula: 1234567", 'MATRICULA_SERVIDOR', True),
    ("Matrícula: 12345678", 'MATRICULA_SERVIDOR', True),
    ("Matrícula: 123456", 'MATRICULA_SERVIDOR', False),  # Não deve pegar 6 dígitos puros
    ("Matrícula: 98.123-3A", 'MATRICULA_SERVIDOR', True),
    ("Matrícula: 98745632D", 'MATRICULA_SERVIDOR', True),
    # INSCRICAO_IMOVEL
    ("Inscrição do imóvel: inscrição:1234567", 'INSCRICAO_IMOVEL', True),
    ("Inscrição do imóvel: inscrição 1234567", 'INSCRICAO_IMOVEL', True),
    ("Inscrição do imóvel: inscrição-1234567", 'INSCRICAO_IMOVEL', True),
    ("Inscrição do imóvel: inscrição : 1234567", 'INSCRICAO_IMOVEL', True),
    ("Inscrição do imóvel: inscrição:123456", 'INSCRICAO_IMOVEL', True),
    ("Inscrição do imóvel: inscrição:123456789", 'INSCRICAO_IMOVEL', True),
    ("Inscrição do imóvel: inscrição:12345", 'INSCRICAO_IMOVEL', False),  # Menos de 6 dígitos
]

@pytest.mark.parametrize("texto,tipo,esperado", CASES)
def test_regex_gdf_padrao(texto, tipo, esperado):
    detector = PIIDetector()
    findings = detector._detectar_regex(texto)
    achou = any(f.tipo == tipo for f in findings)
    assert achou == esperado, f"Texto: {texto} | Tipo: {tipo} | Esperado: {esperado} | Achados: {findings}"