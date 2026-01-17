def pos_processar_spans(spans, min_len=2, merge_overlap=True, split_on=None):
    """
    Pós-processamento de spans:
    - Remove spans muito curtos (min_len)
    - Faz merge de spans sobrepostos/adjacentes se merge_overlap=True
    - Split de spans em delimitadores (split_on: regex ou função)
    Retorna lista de spans pós-processados.
    """
    # Remove spans muito curtos
    spans = [s for s in spans if (s[1] - s[0]) >= min_len]
    if not spans:
        return []
    # Merge de spans sobrepostos/adjacentes
    if merge_overlap:
        spans = sorted(spans, key=lambda x: x[0])
        merged = []
        for s in spans:
            if not merged:
                merged.append(s)
            else:
                last = merged[-1]
                if s[0] <= last[1]:  # sobreposição ou adjacente
                    merged[-1] = (last[0], max(last[1], s[1]))
                else:
                    merged.append(s)
        spans = merged
    # Split de spans em delimitadores
    if split_on:
        new_spans = []
        for s in spans:
            # split_on pode ser regex ou função
            if callable(split_on):
                parts = split_on(s)
            else:
                import re
                parts = []
                texto = s[2] if len(s) > 2 else ''
                for m in re.finditer(split_on, texto):
                    parts.append((m.start(), m.end()))
            if parts:
                new_spans.extend(parts)
            else:
                new_spans.append(s)
        spans = new_spans
    return spans
def calcular_overlap_spans(pred_spans, true_spans):
    """
    Calcula métricas de overlap entre spans previstos e spans verdadeiros.
    - pred_spans: lista de (start, end)
    - true_spans: lista de (start, end)
    Retorna: dict com IoU médio, recall de spans, precision de spans, F1 de spans
    """
    def iou(span1, span2):
        s1, e1 = span1
        s2, e2 = span2
        inter = max(0, min(e1, e2) - max(s1, s2))
        union = max(e1, e2) - min(s1, s2)
        return inter / union if union > 0 else 0.0

    matches = []
    used_true = set()
    for p in pred_spans:
        best_iou = 0
        best_idx = -1
        for idx, t in enumerate(true_spans):
            if idx in used_true:
                continue
            score = iou(p, t)
            if score > best_iou:
                best_iou = score
                best_idx = idx
        if best_iou > 0.5:
            matches.append((p, true_spans[best_idx], best_iou))
            used_true.add(best_idx)

    tp = len(matches)
    fp = len(pred_spans) - tp
    fn = len(true_spans) - tp
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    mean_iou = sum(m[2] for m in matches) / tp if tp > 0 else 0.0
    return {
        'precision_spans': round(precision, 4),
        'recall_spans': round(recall, 4),
        'f1_spans': round(f1, 4),
        'mean_iou': round(mean_iou, 4),
        'tp': tp, 'fp': fp, 'fn': fn
    }
"""
Combinadores de probabilidades para ensemble de detecção.

Implementa:
- Combinação via Log-Odds (Naive Bayes)
- Cálculo de confidence_no_pii
- Cálculo de confidence_all_found
"""

import math
from typing import List, Dict, Tuple, Optional
import logging

from .types import SourceDetection, DetectionSource
from .config import FN_RATES, FP_RATES, PRIOR_PII

logger = logging.getLogger(__name__)


class ProbabilityCombiner:
    """Combina probabilidades de múltiplas fontes via Log-Odds.
    
    A combinação via log-odds (Naive Bayes) é robusta quando as fontes
    são razoavelmente independentes. Cada fonte contribui com sua
    likelihood ratio para o odds final.
    
    Fórmula:
        logit = log(prior_odds) + Σ log(p_fonte / fp_rate_fonte)
        confidence = exp(logit) / (1 + exp(logit))
    """
    
    def __init__(
        self, 
        fn_rates: Optional[Dict[str, float]] = None,
        fp_rates: Optional[Dict[str, float]] = None,
        prior: float = PRIOR_PII
    ):
        """Inicializa o combinador.
        
        Args:
            fn_rates: Taxas de false negative por fonte
            fp_rates: Taxas de false positive por fonte
            prior: Probabilidade base de existir PII antes de ver evidência
        """
        self.fn_rates = fn_rates or FN_RATES
        self.fp_rates = fp_rates or FP_RATES
        self.prior = prior
    
    def combine_detections(
        self, 
        detections: List[SourceDetection],
        prior: Optional[float] = None
    ) -> float:
        """Combina detecções de múltiplas fontes em confiança única.
        
        Args:
            detections: Lista de detecções de diferentes fontes
            prior: Prior específico (sobrescreve o default)
            
        Returns:
            Confiança combinada (0-1)
        """
        if not detections:
            return 0.0
        
        prior = prior or self.prior
        prior = max(0.001, min(0.999, prior))  # Clamp
        
        # Começa com log-odds do prior
        prior_odds = prior / (1 - prior)
        log_odds = math.log(prior_odds)
        
        for detection in detections:
            if not detection.is_positive:
                continue  # Ignora detecções negativas
            
            # Score calibrado da fonte
            p = detection.calibrated_score
            p = max(0.0001, min(0.9999, p))  # Clamp para evitar log(0)
            
            # Taxa de FP da fonte
            source_name = detection.source.value if isinstance(detection.source, DetectionSource) else str(detection.source)
            fp_rate = self.fp_rates.get(source_name, 0.01)
            fp_rate = max(0.00001, fp_rate)  # Evita divisão por zero
            
            # Likelihood ratio: P(observar | é PII) / P(observar | não é PII)
            # P(observar | é PII) ≈ p (score calibrado)
            # P(observar | não é PII) ≈ fp_rate
            likelihood_ratio = p / fp_rate
            
            log_odds += math.log(likelihood_ratio)
        
        # Converte log-odds de volta para probabilidade
        # Clamp para evitar overflow
        log_odds = min(log_odds, 20)  # exp(20) ≈ 485 milhões
        
        final_odds = math.exp(log_odds)
        confidence = final_odds / (1 + final_odds)
        
        return confidence
    
    def combine_by_source(
        self, 
        source_scores: Dict[str, float]
    ) -> float:
        """Combina scores de múltiplas fontes (interface simplificada).
        
        Args:
            source_scores: Dict de {nome_fonte: score_calibrado}
            
        Returns:
            Confiança combinada (0-1)
        """
        detections = []
        for source, score in source_scores.items():
            try:
                source_enum = DetectionSource(source)
            except ValueError:
                source_enum = source
            
            detections.append(SourceDetection(
                source=source_enum,
                raw_score=score,
                calibrated_score=score,
                is_positive=True
            ))
        
        return self.combine_detections(detections)
    
    def confidence_no_pii(
        self, 
        sources_used: List[str]
    ) -> float:
        """Calcula confiança de que NÃO existe PII no texto.
        
        Quando nenhuma fonte detecta nada, a probabilidade de que 
        realmente não existe PII é:
        
            P(no PII) = 1 - P(todas as fontes erraram)
            P(todas erraram) = Π fn_rate_i (produto das taxas de FN)
        
        Com ensemble de 4 fontes bem calibradas, chegamos a ~0.999999998
        
        Args:
            sources_used: Lista de fontes que participaram da análise
            
        Returns:
            Confiança de que não existe PII (0-1)
        """
        if not sources_used:
            return 0.5  # Sem fontes, incerteza total
        
        # Probabilidade de TODAS as fontes terem perdido um PII real
        p_miss_all = 1.0
        
        for source in sources_used:
            fn_rate = self.fn_rates.get(source, 0.1)  # Default conservador
            p_miss_all *= fn_rate
        
        # P(não existe PII) = 1 - P(perdemos algo)
        # Mas também precisamos considerar o prior de existir PII
        # P(no PII | nenhuma detecção) ∝ P(nenhuma detecção | no PII) * P(no PII)
        
        # P(nenhuma detecção | no PII) ≈ 1 - Σ fp_rate_i (aproximação)
        p_no_detection_given_no_pii = 1.0
        for source in sources_used:
            fp_rate = self.fp_rates.get(source, 0.01)
            p_no_detection_given_no_pii *= (1 - fp_rate)
        
        # P(nenhuma detecção | has PII) = Π fn_rate_i
        p_no_detection_given_has_pii = p_miss_all
        
        # Bayes: P(no PII | nenhuma detecção)
        prior_no_pii = 1 - self.prior
        
        numerator = p_no_detection_given_no_pii * prior_no_pii
        denominator = (
            p_no_detection_given_no_pii * prior_no_pii + 
            p_no_detection_given_has_pii * self.prior
        )
        
        if denominator == 0:
            return 0.5
        
        confidence = numerator / denominator
        
        # Clamp para evitar 1.0 exato (nunca temos certeza absoluta)
        return min(confidence, 0.9999999999)
    
    def confidence_all_found(
        self, 
        entity_confidences: List[float],
        num_sources_agreed: int = 1
    ) -> float:
        """Calcula confiança de que encontramos TODOS os PIIs.
        
        Quando PIIs são detectados, queremos saber a probabilidade de
        não ter perdido nenhum. Isso depende:
        1. Da menor confiança entre entidades (elo mais fraco)
        2. Do número de fontes que concordaram
        
        Args:
            entity_confidences: Lista de confianças de cada entidade
            num_sources_agreed: Número de fontes que concordaram
            
        Returns:
            Confiança de ter encontrado tudo (0-1)
        """
        if not entity_confidences:
            return 0.0
        
        # Confiança mínima entre entidades
        min_conf = min(entity_confidences)
        
        # Média das confianças
        avg_conf = sum(entity_confidences) / len(entity_confidences)
        
        # Boost por múltiplas fontes concordando
        agreement_boost = 1.0 + (num_sources_agreed - 1) * 0.02
        agreement_boost = min(agreement_boost, 1.1)  # Cap de 10%
        
        # Combina: 70% peso na mínima, 30% na média
        # Mais conservador - priorizamos não perder nada
        base_confidence = 0.7 * min_conf + 0.3 * avg_conf
        
        # Aplica boost de concordância
        confidence = base_confidence * agreement_boost
        
        return min(confidence, 0.9999)


class EntityAggregator:
    """Agrega detecções de mesma entidade de diferentes fontes."""
    
    def __init__(self, combiner: Optional[ProbabilityCombiner] = None):
        self.combiner = combiner or ProbabilityCombiner()
    
    def aggregate_by_position(
        self, 
        detections: List[Dict]
    ) -> List[Dict]:
        """Agrega detecções que se sobrepõem na mesma posição.
        
        Args:
            detections: Lista de detecções com campos:
                - start, end: posições
                - source: fonte da detecção
                - score: score da fonte
                
        Returns:
            Lista de detecções agregadas
        """
        if not detections:
            return []
        
        # Agrupa por sobreposição de posição
        groups: List[List[Dict]] = []
        
        for det in sorted(detections, key=lambda x: x.get('start', 0)):
            merged = False
            for group in groups:
                # Verifica se sobrepõe com algum do grupo
                for existing in group:
                    if self._overlaps(det, existing):
                        group.append(det)
                        merged = True
                        break
                if merged:
                    break
            
            if not merged:
                groups.append([det])
        
        # Combina cada grupo
        aggregated = []
        for group in groups:
            if len(group) == 1:
                aggregated.append(group[0])
            else:
                aggregated.append(self._merge_group(group))
        
        return aggregated
    
    def _overlaps(self, det1: Dict, det2: Dict) -> bool:
        """Verifica se duas detecções se sobrepõem."""
        start1, end1 = det1.get('start', 0), det1.get('end', 0)
        start2, end2 = det2.get('start', 0), det2.get('end', 0)
        
        return not (end1 <= start2 or end2 <= start1)
    
    def _merge_group(self, group: List[Dict]) -> Dict:
        """Merge de um grupo de detecções sobrepostas."""
        # Pega a maior span
        start = min(d.get('start', 0) for d in group)
        end = max(d.get('end', 0) for d in group)
        
        # Coleta sources e scores
        sources = []
        source_scores = {}
        
        for det in group:
            source = det.get('source', 'unknown')
            score = det.get('score', 0.5)
            
            if source not in sources:
                sources.append(source)
                source_scores[source] = score
            else:
                # Se mesma fonte aparece 2x, pega o maior score
                source_scores[source] = max(source_scores[source], score)
        
        # Combina scores
        combined_conf = self.combiner.combine_by_source(source_scores)
        
        # Pega o valor mais longo/completo, ignorando None
        best_det = max(group, key=lambda d: len(d.get('valor') or ''))
        
        return {
            'tipo': best_det.get('tipo'),
            'valor': best_det.get('valor'),
            'start': start,
            'end': end,
            'confianca': combined_conf,
            'sources': sources,
            'peso': best_det.get('peso', 3),
        }

def merge_spans_custom(spans, criterio='longest', fontes_preferidas=None, tie_breaker='leftmost'):
    """
    Merge customizável de spans com critérios flexíveis.
    spans: lista de dicts ou tuplas (start, end, tipo, valor, score, fonte)
    criterio: 'longest', 'score', 'fonte', 'custom'
    fontes_preferidas: lista de fontes em ordem de prioridade
    tie_breaker: 'leftmost', 'rightmost', 'all'
    Retorna lista de spans pós-merge.
    """
    if not spans:
        return []
    # Normaliza para dict
    norm_spans = []
    for s in spans:
        if isinstance(s, dict):
            norm_spans.append(s)
        else:
            # (start, end, tipo, valor, score, fonte)
            d = {'start': s[0], 'end': s[1], 'tipo': s[2] if len(s)>2 else None, 'valor': s[3] if len(s)>3 else None,
                 'score': s[4] if len(s)>4 else 1.0, 'fonte': s[5] if len(s)>5 else None}
            norm_spans.append(d)
    # Ordena por início
    norm_spans = sorted(norm_spans, key=lambda x: (x['start'], -x['end']))
    merged = []
    used = set()
    for i, s in enumerate(norm_spans):
        if i in used:
            continue
        overlaps = [i]
        for j in range(i+1, len(norm_spans)):
            s2 = norm_spans[j]
            if s2['start'] < s['end'] and s2['end'] > s['start']:
                overlaps.append(j)
        if len(overlaps) == 1:
            merged.append(s)
            continue
        # Resolve overlap
        group = [norm_spans[k] for k in overlaps]
        if criterio == 'longest':
            chosen = max(group, key=lambda x: x['end']-x['start'])
        elif criterio == 'score':
            chosen = max(group, key=lambda x: x.get('score', 1.0))
        elif criterio == 'fonte' and fontes_preferidas:
            chosen = min(group, key=lambda x: fontes_preferidas.index(x.get('fonte', ''))) if any(x.get('fonte') in fontes_preferidas for x in group) else group[0]
        elif criterio == 'custom' and callable(fontes_preferidas):
            chosen = fontes_preferidas(group)
        else:
            chosen = group[0]
        merged.append(chosen)
        for k in overlaps:
            used.add(k)
    # Tie-breaker
    if tie_breaker == 'all':
        return merged
    elif tie_breaker == 'leftmost':
        return sorted(merged, key=lambda x: (x['start'], x['end']))
    elif tie_breaker == 'rightmost':
        return sorted(merged, key=lambda x: (-x['end'], -x['start']))
    return merged
