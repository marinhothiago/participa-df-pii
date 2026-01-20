"""Recalibração automática baseada em feedbacks.

Quando novos feedbacks são recebidos, treina calibradores IsotonicCalibrator
para melhorar scores de confiança.
"""

import logging
from typing import Dict, List, Tuple
from src.confidence.calibration import get_calibrator_registry, IsotonicCalibrator
from src.confidence.training import record_calibration_event, get_training_tracker

logger = logging.getLogger(__name__)


def recalibrate_from_feedbacks(feedbacks_data: Dict) -> Dict:
    """Treina calibradores com dados de feedback.
    
    Args:
        feedbacks_data: Dict carregado de feedback.json com feedbacks e stats
    
    Returns:
        Dict com resultado do treinamento
    """
    feedbacks = feedbacks_data.get("feedbacks", [])
    
    if len(feedbacks) < 10:
        return {
            "success": False,
            "message": f"Apenas {len(feedbacks)} feedbacks. Mínimo 10 necessários.",
            "samples_count": len(feedbacks),
        }
    
    # Extrai dados de treinamento
    training_data_by_source = _extract_training_data(feedbacks)
    
    if not training_data_by_source:
        return {
            "success": False,
            "message": "Nenhum dado de treinamento extraído dos feedbacks.",
            "samples_count": len(feedbacks),
        }
    
    # Treina calibradores
    registry = get_calibrator_registry()
    total_samples = 0
    results_by_source = {}
    
    for source, (raw_scores, true_labels, by_type) in training_data_by_source.items():
        if len(raw_scores) < 5:
            continue
        
        # Calcula acurácia antes
        accuracy_before = _calculate_accuracy(raw_scores, true_labels)
        
        # Treina calibrador
        calibrator = registry.get(source)
        calibrator.fit(raw_scores, true_labels)
        
        # Calcula acurácia depois (simulada com dados de treino)
        # Na prática, isso seria validação com holdout set
        calibrated_scores = [calibrator.calibrate(s) for s in raw_scores]
        accuracy_after = _calculate_accuracy(calibrated_scores, true_labels)
        
        total_samples += len(raw_scores)
        results_by_source[source] = {
            "samples": len(raw_scores),
            "accuracy_before": round(accuracy_before, 4),
            "accuracy_after": round(accuracy_after, 4),
            "improvement": round(accuracy_after - accuracy_before, 4),
            "by_type": by_type,
        }
        
        logger.info(
            f"✅ Calibrador '{source}' treinado: "
            f"{len(raw_scores)} amostras | "
            f"Melhoria: {accuracy_after - accuracy_before:+.2%}"
        )
        
        # Registra evento
        record_calibration_event(
            source=source,
            num_samples=len(raw_scores),
            accuracy_before=accuracy_before,
            accuracy_after=accuracy_after,
            by_type=by_type,
        )
    
    tracker = get_training_tracker()
    status = tracker.get_status()
    
    return {
        "success": True,
        "message": "✅ Recalibração automática concluída",
        "total_samples": total_samples,
        "by_source": results_by_source,
        "training_status": status,
    }


def _extract_training_data(
    feedbacks: List[Dict],
) -> Dict[str, Tuple[List[float], List[int], Dict]]:
    """Extrai dados de treinamento dos feedbacks.
    
    Returns:
        Dict mapeando fonte -> (raw_scores, true_labels, by_type_stats)
    """
    data_by_source = {}
    by_type_global = {}
    
    for feedback in feedbacks:
        entity_feedbacks = feedback.get("entity_feedbacks", [])
        
        for entity_fb in entity_feedbacks:
            tipo = entity_fb.get("tipo", "UNKNOWN")
            source = entity_fb.get("fonte", "unknown").lower()
            confidence = entity_fb.get("confianca_modelo", 0.5)
            validacao = entity_fb.get("validacao_humana", "").upper()
            
            # Converte validação para label
            if validacao == "CORRETO":
                label = 1
            elif validacao == "INCORRETO":
                label = 0
            elif validacao == "PARCIAL":
                label = 0  # Treata parcial como incorreto para calibração
            else:
                continue
            
            # Adiciona à fonte
            if source not in data_by_source:
                data_by_source[source] = ([], [], {})
            
            scores, labels, by_type = data_by_source[source]
            scores.append(confidence)
            labels.append(label)
            
            # Estatísticas por tipo
            if tipo not in by_type:
                by_type[tipo] = {"total": 0, "correct": 0}
            by_type[tipo]["total"] += 1
            if label == 1:
                by_type[tipo]["correct"] += 1
            
            # Global
            if tipo not in by_type_global:
                by_type_global[tipo] = {"total": 0, "correct": 0}
            by_type_global[tipo]["total"] += 1
            if label == 1:
                by_type_global[tipo]["correct"] += 1
    
    # Limpa dados vazios e adiciona by_type global
    cleaned = {}
    for source, (scores, labels, by_type) in data_by_source.items():
        if scores:
            cleaned[source] = (scores, labels, by_type_global)
    
    return cleaned


def _calculate_accuracy(scores: List[float], labels: List[int]) -> float:
    """Calcula acurácia com threshold 0.5."""
    if not scores:
        return 0
    
    correct = sum(
        1 for score, label in zip(scores, labels)
        if (score >= 0.5 and label == 1) or (score < 0.5 and label == 0)
    )
    
    return correct / len(scores)
