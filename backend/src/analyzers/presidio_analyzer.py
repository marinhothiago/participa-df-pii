"""
Analisador de PII usando Microsoft Presidio.
"""

from typing import List, Dict, Any
try:
    from presidio_analyzer import AnalyzerEngine
except ImportError:
    AnalyzerEngine = None

class PresidioAnalyzer:
    """Detecta entidades PII usando o Presidio AnalyzerEngine."""
    def __init__(self):
        if AnalyzerEngine:
            self.engine = AnalyzerEngine()
        else:
            self.engine = None

    def analyze(self, text: str) -> List[Dict[str, Any]]:
        if not self.engine:
            return []
        results = self.engine.analyze(text=text, language="pt")
        return [
            {
                'entity': r.entity_type,
                'start': r.start,
                'end': r.end,
                'score': r.score,
                'value': text[r.start:r.end]
            }
            for r in results
        ]
