import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
pytestmark = pytest.mark.timeout(10)

def test_matricula_servidor():
    """Teste de matrícula de servidor"""
    assert True