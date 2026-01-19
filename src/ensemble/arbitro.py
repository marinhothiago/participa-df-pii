"""
Árbitro de decisão para ensemble de detectores PII.
"""

from typing import List, Dict, Any

class Arbitro:
    """Decide o resultado final do ensemble de detectores."""
    def __init__(self):
        pass

    def decidir(self, resultados: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Combina resultados de múltiplos detectores (OR lógico)."""
        # Exemplo: stub faz flatten dos resultados
        final = []
        for r in resultados:
            final.extend(r)
        return final
