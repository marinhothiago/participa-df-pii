"""
Configuração global de fixtures para os testes.
O detector é carregado uma única vez para toda a sessão de testes.
"""
import sys
import os

# Garante que o path do backend está configurado
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest


# Singleton do detector para toda a sessão
_detector_instance = None


def get_shared_detector():
    """Retorna instância compartilhada do detector (singleton)."""
    global _detector_instance
    if _detector_instance is None:
        from src.detector import PIIDetector
        _detector_instance = PIIDetector()
    return _detector_instance


@pytest.fixture(scope="session")
def detector():
    """
    Fixture global do detector - carregado UMA VEZ para toda a sessão de testes.
    
    Usar scope="session" garante que o modelo NER (~1.3GB) é carregado apenas uma vez,
    reduzindo o tempo total de ~15 minutos para ~30 segundos.
    """
    return get_shared_detector()


@pytest.fixture(scope="session")
def shared_detector():
    """Alias para compatibilidade com testes existentes."""
    return get_shared_detector()
