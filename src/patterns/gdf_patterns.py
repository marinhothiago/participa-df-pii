"""
Padrões regex específicos para entidades do GDF.
"""

import re

# Exemplos de padrões (ajuste conforme necessário)
PATTERNS = {
    'matricula_gdf': r'\b\d{7,8}\b',
    'processo_gdf': r'\b\d{6}-\d{4}/\d{2}\b',
}

def get_pattern(name: str):
    """Retorna o padrão regex pelo nome."""
    return PATTERNS.get(name)
