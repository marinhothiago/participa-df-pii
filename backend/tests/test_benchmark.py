import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import os
import sys
import json
from datetime import datetime
from collections import defaultdict
import pytest
from src.detector import PIIDetector
from backend.tests.test_diagnostico_motor_dataset_lgpd import DATASET_LGPD

detector = PIIDetector()

@pytest.mark.parametrize("texto, contem_pii, descricao, categoria", DATASET_LGPD)
def test_pii_detector_dataset(texto, contem_pii, descricao, categoria):
    """Teste unitário parametrizado para todo o dataset."""
    resultado, findings, risco, confianca = detector.detect(texto)
    assert resultado == contem_pii, f"Texto: {texto}\nDescrição: {descricao}\nCategoria: {categoria}\nEsperado: {contem_pii}\nObtido: {resultado}"