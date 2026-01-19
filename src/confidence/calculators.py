"""
Calculadora de confiança para detecção de PII.
"""

from typing import List, Dict, Any

class ConfidenceCalculator:
    """Calcula score de confiança para entidades PII detectadas."""
    def __init__(self):
        pass

    def calculate(self, entities: List[Dict[str, Any]]) -> float:
        """Retorna score de confiança agregado para as entidades."""
        # Exemplo: stub retorna 1.0 se houver entidades, 0.0 se não houver
        return 1.0 if entities else 0.0
