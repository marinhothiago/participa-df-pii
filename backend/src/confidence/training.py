"""Sistema de rastreamento de treinamento e calibração.

Mantém histórico de:
- Quando calibradores foram treinados
- Quantas amostras foram usadas
- Acurácia antes/depois
- Recomendações para fine-tuning
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)

# Lock para thread-safety
training_lock = threading.Lock()


class TrainingTracker:
    """Rastreia status de treinamento e calibração."""
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.data = self._load()
    
    def _load(self) -> Dict:
        """Carrega histórico de treinamento."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Erro ao carregar training status: {e}")
        
        return {
            "last_calibration": None,
            "total_samples_used": 0,
            "accuracy_before": 0,
            "accuracy_after": 0,
            "calibrations": [],
            "by_source": {},
            "recommendations": [],
        }
    
    def _save(self) -> None:
        """Salva histórico de treinamento."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar training status: {e}")
    
    def record_calibration(
        self,
        source: str,
        num_samples: int,
        accuracy_before: float,
        accuracy_after: float,
        by_type: Dict[str, Dict] = None
    ) -> None:
        """Registra uma calibração realizada.
        
        Args:
            source: Fonte do detector (bert_ner, spacy, etc)
            num_samples: Número de amostras usadas
            accuracy_before: Acurácia antes da calibração
            accuracy_after: Acurácia após calibração
            by_type: Estatísticas por tipo de PII
        """
        with training_lock:
            now = datetime.now().isoformat()
            
            # Atualiza dados globais
            self.data["last_calibration"] = now
            self.data["total_samples_used"] = num_samples
            self.data["accuracy_before"] = round(accuracy_before, 4)
            self.data["accuracy_after"] = round(accuracy_after, 4)
            
            # Calcula melhoria
            improvement = accuracy_after - accuracy_before
            
            # Adiciona ao histórico
            record = {
                "timestamp": now,
                "source": source,
                "num_samples": num_samples,
                "accuracy_before": round(accuracy_before, 4),
                "accuracy_after": round(accuracy_after, 4),
                "improvement": round(improvement, 4),
                "by_type": by_type or {},
            }
            
            self.data["calibrations"].append(record)
            
            # Atualiza por fonte
            if source not in self.data["by_source"]:
                self.data["by_source"][source] = {
                    "last_calibration": None,
                    "num_calibrations": 0,
                    "total_samples": 0,
                    "avg_improvement": 0,
                }
            
            source_data = self.data["by_source"][source]
            source_data["last_calibration"] = now
            source_data["num_calibrations"] = source_data.get("num_calibrations", 0) + 1
            source_data["total_samples"] += num_samples
            
            # Calcula média de melhoria
            improvements = [
                r["improvement"] for r in self.data["calibrations"]
                if r["source"] == source
            ]
            source_data["avg_improvement"] = round(sum(improvements) / len(improvements), 4)
            
            # Gera recomendações
            self._generate_recommendations()
            
            self._save()
            
            logger.info(
                f"✅ Calibração registrada: {source} | "
                f"Amostras: {num_samples} | "
                f"Melhoria: {improvement:+.2%}"
            )
    
    def _generate_recommendations(self) -> None:
        """Gera recomendações de ação."""
        recommendations = []
        
        # Se accuracy está bom, pode fazer fine-tuning
        if self.data["accuracy_after"] >= 0.90 and self.data["total_samples_used"] >= 50:
            recommendations.append({
                "type": "ready_for_finetuning",
                "message": "✅ Dados suficientes e acurácia boa. Pronto para fine-tuning do modelo!",
                "action": "POST /feedback/generate-dataset",
            })
        
        # Se há muitos falsos positivos
        if self.data["accuracy_after"] < 0.85:
            recommendations.append({
                "type": "needs_attention",
                "message": "⚠️ Acurácia baixa. Investigar tipos de PII problemáticos.",
                "action": "Revisar feedback stats por tipo",
            })
        
        # Se não há dados suficientes
        if self.data["total_samples_used"] < 50:
            needed = 50 - self.data["total_samples_used"]
            recommendations.append({
                "type": "collect_more_data",
                "message": f"📊 Precisam de {needed} mais amostras para treinamento robusto",
                "action": "Continuar coletando feedbacks",
            })
        
        self.data["recommendations"] = recommendations
    
    def get_status(self) -> Dict:
        """Retorna status atual de treinamento."""
        status = {
            **self.data,
            "status": self._compute_status(),
            "improvement_percentage": round(
                (self.data["accuracy_after"] - self.data["accuracy_before"]) * 100, 2
            ) if self.data["accuracy_after"] > 0 else 0,
        }
        
        # Adiciona tempo desde último treinamento
        if self.data["last_calibration"]:
            last = datetime.fromisoformat(self.data["last_calibration"])
            now = datetime.now()
            delta = now - last
            
            if delta.total_seconds() < 60:
                status["time_since_last"] = "segundos atrás"
            elif delta.total_seconds() < 3600:
                mins = int(delta.total_seconds() / 60)
                status["time_since_last"] = f"{mins} minutos atrás"
            elif delta.total_seconds() < 86400:
                hours = int(delta.total_seconds() / 3600)
                status["time_since_last"] = f"{hours} horas atrás"
            else:
                days = int(delta.total_seconds() / 86400)
                status["time_since_last"] = f"{days} dias atrás"
        else:
            status["time_since_last"] = "nunca"
        
        return status
    
    def _compute_status(self) -> str:
        """Computa status do treinamento."""
        if not self.data["last_calibration"]:
            return "never_trained"  # Nunca treinado
        
        last = datetime.fromisoformat(self.data["last_calibration"])
        now = datetime.now()
        delta = now - last
        
        # Se treinado em menos de 1 hora, está "fresh"
        if delta.total_seconds() < 3600:
            return "fresh"
        
        # Se treinado em menos de 1 dia
        if delta.total_seconds() < 86400:
            return "recent"
        
        # Se treinado há mais de 1 dia
        return "stale"


# Singleton global
_training_tracker: Optional[TrainingTracker] = None


def get_training_tracker() -> TrainingTracker:
    """Obtém o rastreador global de treinamento."""
    global _training_tracker
    if _training_tracker is None:
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        tracker_path = os.path.join(backend_dir, "data", "training_status.json")
        _training_tracker = TrainingTracker(tracker_path)
    return _training_tracker


def record_calibration_event(
    source: str,
    num_samples: int,
    accuracy_before: float,
    accuracy_after: float,
    by_type: Dict[str, Dict] = None
) -> None:
    """Função auxiliar para registrar evento de calibração."""
    tracker = get_training_tracker()
    tracker.record_calibration(source, num_samples, accuracy_before, accuracy_after, by_type)
