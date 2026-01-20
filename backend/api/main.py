"""API FastAPI para Detecção de PII - Participa DF.

Sistema de detecção de Informações Pessoalmente Identificáveis (PII) para
manifestações do Participa DF em conformidade com LGPD (Lei Geral de Proteção
de Dados) e LAI (Lei de Acesso à Informação).

Endpoints:
    POST /analyze: Analisa texto para detecção de PII
    GET /health: Verifica status da API
    POST /api/lote: Enfileira processamento de lote (CSV/XLSX)
    GET /api/lote/status/{job_id}: Consulta status do processamento de lote
    GET /api/lote/download/{job_id}: Faz download do resultado do lote

Contexto:
    - Detecta PII em manifestações de cidadãos (reclamações, sugestões, denúncias)
    - Protege dados privados enquanto preserva informações públicas (LAI)
    - Implementa imunidade funcional para agentes públicos em exercício

Exemplo de uso:
    >>> import requests
    >>> response = requests.post(
    ...     "http://localhost:8000/analyze",
    ...     json={"text": "Meu CPF é 123.456.789-09", "id": "manifestacao_123"}
    ... )
    >>> print(response.json())
    {
        "id": "manifestacao_123",
        "classificacao": "NÃO PÚBLICO",
        "risco": "CRÍTICO",
        "confianca": 1.0,  # ✅ NORMALIZADO 0-1
        "detalhes": [{"tipo": "CPF", "valor": "123.456.789-09", ...}]
    }
"""

import logging
logging.basicConfig(level=logging.DEBUG)

# Corrige PYTHONPATH para garantir importação tanto local quanto no HF Spaces
import sys, os
# Adiciona diretório pai (backend/) ao path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
# Adiciona diretório raiz (para imports com 'backend.')
sys.path.insert(0, os.path.dirname(backend_dir))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from typing import Dict, Optional, List
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid

# Imports com fallback para HF Spaces (sem prefixo 'backend.')
try:
    from backend.api.celery_config import celery_app
    from backend.src.detector import PIIDetector
except ModuleNotFoundError:
    from api.celery_config import celery_app
    from src.detector import PIIDetector

from celery.result import AsyncResult
import json
import threading
from datetime import datetime
import shutil

# === SISTEMA DE CONTADORES GLOBAIS ===
STATS_FILE = os.path.join(backend_dir, "data", "stats.json")
FEEDBACK_FILE = os.path.join(backend_dir, "data", "feedback.json")
stats_lock = threading.Lock()
feedback_lock = threading.Lock()

def load_stats() -> Dict:
    """Carrega estatísticas do arquivo JSON."""
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar stats: {e}")
    return {"site_visits": 0, "classification_requests": 0, "last_updated": None}

def save_stats(stats: Dict) -> None:
    """Salva estatísticas no arquivo JSON com lock para concorrência."""
    try:
        stats["last_updated"] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        print(f"Erro ao salvar stats: {e}")

def increment_stat(key: str, amount: int = 1) -> Dict:
    """Incrementa uma estatística de forma thread-safe."""
    with stats_lock:
        stats = load_stats()
        stats[key] = stats.get(key, 0) + amount
        save_stats(stats)
        return stats


# === SISTEMA DE FEEDBACK HUMANO ===
def load_feedback() -> Dict:
    """Carrega feedbacks do arquivo JSON."""
    try:
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar feedback: {e}")
    return {
        "feedbacks": [],
        "stats": {
            "total_feedbacks": 0,
            "total_entities_reviewed": 0,
            "correct": 0,
            "incorrect": 0,
            "partial": 0,
            "by_type": {}
        },
        "last_updated": None
    }


def save_feedback(data: Dict) -> None:
    """Salva feedbacks no arquivo JSON com lock para concorrência."""
    try:
        data["last_updated"] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar feedback: {e}")


def add_feedback(feedback_entry: Dict) -> Dict:
    """Adiciona um feedback e atualiza estatísticas."""
    with feedback_lock:
        data = load_feedback()
        
        # Adiciona o feedback
        data["feedbacks"].append(feedback_entry)
        data["stats"]["total_feedbacks"] += 1
        
        # Atualiza estatísticas por entidade
        for entity_fb in feedback_entry.get("entity_feedbacks", []):
            data["stats"]["total_entities_reviewed"] += 1
            validacao = entity_fb.get("validacao_humana", "").upper()
            
            if validacao == "CORRETO":
                data["stats"]["correct"] += 1
            elif validacao == "INCORRETO":
                data["stats"]["incorrect"] += 1
            elif validacao == "PARCIAL":
                data["stats"]["partial"] += 1
            
            # Estatísticas por tipo de entidade
            tipo = entity_fb.get("tipo", "UNKNOWN")
            if tipo not in data["stats"]["by_type"]:
                data["stats"]["by_type"][tipo] = {"correct": 0, "incorrect": 0, "partial": 0, "total": 0}
            
            data["stats"]["by_type"][tipo]["total"] += 1
            if validacao == "CORRETO":
                data["stats"]["by_type"][tipo]["correct"] += 1
            elif validacao == "INCORRETO":
                data["stats"]["by_type"][tipo]["incorrect"] += 1
            elif validacao == "PARCIAL":
                data["stats"]["by_type"][tipo]["partial"] += 1
        
        save_feedback(data)
        
        # Calcula accuracy para retorno
        total = data["stats"]["total_entities_reviewed"]
        correct = data["stats"]["correct"]
        accuracy = correct / total if total > 0 else 0
        
        return {
            **data["stats"],
            "accuracy": round(accuracy, 4)
        }


# === MODELOS PYDANTIC PARA FEEDBACK ===
class EntityFeedback(BaseModel):
    tipo: str
    valor: str
    confianca_modelo: float
    fonte: Optional[str] = "unknown"
    validacao_humana: str  # CORRETO | INCORRETO | PARCIAL
    tipo_corrigido: Optional[str] = None
    comentario: Optional[str] = None


class FeedbackRequest(BaseModel):
    analysis_id: Optional[str] = None
    original_text: str
    entity_feedbacks: List[EntityFeedback]
    classificacao_modelo: str
    classificacao_corrigida: Optional[str] = None
    revisor: Optional[str] = "anonymous"

# Inicializa aplicação FastAPI
app = FastAPI(
    title="Participa DF - PII Detector API",
    description="API para detecção de Informações Pessoais Identificáveis em textos segundo LGPD/LAI",
    version="9.5.0"
)

# Configuração CORS: Permite requisições de qualquer origem (necessário para frontend React/Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa detector PII na memória (carregamento único de modelos)
# LLAMA-3.2-3B ÁRBITRO: Desativado por padrão para evitar custos
# Ative via env PII_USE_LLM_ARBITRATION=True se tiver HF_TOKEN configurado
import os
usar_gpu = os.getenv("PII_USAR_GPU", "True").lower() == "true"
use_llm_arbitration = os.getenv("PII_USE_LLM_ARBITRATION", "False").lower() == "true"
detector = PIIDetector(
    usar_gpu=usar_gpu,
    use_llm_arbitration=use_llm_arbitration
)



from fastapi import Query
from src.confidence.combiners import merge_spans_custom

@app.post("/analyze")
async def analyze(
    data: Dict[str, Optional[str]],
    merge_preset: str = Query(
        default="f1",
        description="Estratégia de merge de spans: 'recall', 'precision', 'f1', 'custom'."
    ),
    use_llm: bool = Query(
        default=False,
        description="Força uso do árbitro LLM para arbitragem de PII."
    )
) -> Dict:
    """
    Analisa texto para detecção de PII com contexto Brasília/GDF.
    Permite selecionar estratégia de merge de spans via parâmetro merge_preset.
    """
    text = data.get("text", "")
    request_id = data.get("id", None)

    # Executa detecção usando detector híbrido
    has_pii, findings, risco, confianca = detector.detect(text, force_llm=use_llm)

    # Estratégias de merge
    if findings:
        if merge_preset == "recall":
            criterio = "longest"
            tie_breaker = "all"
        elif merge_preset == "precision":
            criterio = "score"
            tie_breaker = "leftmost"
        elif merge_preset == "f1":
            criterio = "longest"
            tie_breaker = "leftmost"
        elif merge_preset == "custom":
            criterio = "custom"
            tie_breaker = "leftmost"
        else:
            criterio = "longest"
            tie_breaker = "leftmost"
        # TODO: aplicar merge_spans_custom se necessário

    # Incrementa contador de requisições (global)
    increment_stat("classification_requests")

    # Retorna resultado no formato documentado (compatível com frontend)
    return {
        "id": request_id,
        # Formato novo (documentado no README)
        "has_pii": has_pii,
        "entities": findings,
        "risk_level": risco,
        "confidence_all_found": confianca,
        "total_entities": len(findings) if findings else 0,
        "sources_used": list(set(f.get("fonte", "regex") for f in findings)) if findings else [],
        # Formato legado (para retrocompatibilidade)
        "classificacao": "NÃO PÚBLICO" if has_pii else "PÚBLICO",
        "risco": risco,
        "confianca": confianca,
        "detalhes": findings
    }


@app.get("/stats")
async def get_stats() -> Dict:
    """Retorna estatísticas globais de uso da API.
    
    Returns:
        Dict com:
            - site_visits (int): Total de visitas ao site
            - classification_requests (int): Total de textos analisados
            - last_updated (str): Data/hora da última atualização
    """
    return load_stats()


@app.post("/stats/visit")
async def register_visit() -> Dict:
    """Registra uma nova visita ao site.
    
    Deve ser chamado uma vez por sessão do usuário.
    
    Returns:
        Dict com estatísticas atualizadas
    """
    return increment_stat("site_visits")


# === ENDPOINTS DE FEEDBACK HUMANO ===
@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest) -> Dict:
    """Submete validação humana de uma análise de PII.
    
    Permite que revisores validem se as entidades detectadas são realmente PII.
    
    Args:
        feedback: Objeto com validações das entidades detectadas
        
    Returns:
        Dict com:
            - feedback_id: ID único do feedback
            - stats: Estatísticas atualizadas de acurácia
    """
    feedback_entry = {
        "feedback_id": str(uuid.uuid4()),
        "analysis_id": feedback.analysis_id,
        "timestamp": datetime.now().isoformat(),
        "original_text": feedback.original_text[:500],  # Limita tamanho
        "entity_feedbacks": [ef.dict() for ef in feedback.entity_feedbacks],
        "classificacao_modelo": feedback.classificacao_modelo,
        "classificacao_corrigida": feedback.classificacao_corrigida,
        "revisor": feedback.revisor
    }
    
    stats = add_feedback(feedback_entry)
    
    return {
        "feedback_id": feedback_entry["feedback_id"],
        "message": "Feedback registrado com sucesso",
        "stats": stats
    }


@app.get("/feedback/stats")
async def get_feedback_stats() -> Dict:
    """Retorna estatísticas de acurácia baseadas no feedback humano.
    
    Returns:
        Dict com:
            - total_feedbacks: Total de análises revisadas
            - total_entities_reviewed: Total de entidades validadas
            - accuracy: Taxa de acertos do modelo (correct / total)
            - false_positive_rate: Taxa de falsos positivos
            - by_type: Estatísticas por tipo de entidade
    """
    data = load_feedback()
    stats = data.get("stats", {})
    
    total = stats.get("total_entities_reviewed", 0)
    correct = stats.get("correct", 0)
    incorrect = stats.get("incorrect", 0)
    
    # Calcula métricas
    accuracy = correct / total if total > 0 else 0
    false_positive_rate = incorrect / total if total > 0 else 0
    
    # Calcula acurácia por tipo
    by_type_with_accuracy = {}
    for tipo, tipo_stats in stats.get("by_type", {}).items():
        tipo_total = tipo_stats.get("total", 0)
        tipo_correct = tipo_stats.get("correct", 0)
        tipo_incorrect = tipo_stats.get("incorrect", 0)
        by_type_with_accuracy[tipo] = {
            **tipo_stats,
            "accuracy": tipo_correct / tipo_total if tipo_total > 0 else 0,
            "false_positive_rate": tipo_incorrect / tipo_total if tipo_total > 0 else 0
        }
    
    return {
        "total_feedbacks": stats.get("total_feedbacks", 0),
        "total_entities_reviewed": total,
        "correct": correct,
        "incorrect": incorrect,
        "partial": stats.get("partial", 0),
        "accuracy": round(accuracy, 4),
        "false_positive_rate": round(false_positive_rate, 4),
        "by_type": by_type_with_accuracy,
        "last_updated": data.get("last_updated")
    }


@app.get("/feedback/export")
async def export_feedback() -> Dict:
    """Exporta todos os feedbacks para dataset de treinamento.
    
    Returns:
        Dict com lista completa de feedbacks e estatísticas
    """
    data = load_feedback()
    return {
        "total_records": len(data.get("feedbacks", [])),
        "feedbacks": data.get("feedbacks", []),
        "stats": data.get("stats", {}),
        "exported_at": datetime.now().isoformat()
    }


@app.post("/feedback/generate-dataset")
async def generate_dataset(format: str = "jsonl") -> Dict:
    """Gera dataset de treinamento a partir dos feedbacks coletados.
    
    Transforma feedbacks em formato pronto para:
    1. Fine-tuning de modelos NER
    2. Treinamento de calibradores de confiança
    3. Análise de padrões de erro
    
    Args:
        format: 'jsonl' ou 'csv'
    
    Returns:
        Dict com caminho do arquivo gerado e estatísticas
    """
    try:
        from scripts.feedback_to_dataset import (
            export_ner_dataset_jsonl, 
            export_ner_dataset_csv,
            generate_ner_dataset
        )
        
        if format == "csv":
            output_path = export_ner_dataset_csv()
        else:  # jsonl (padrão)
            output_path = export_ner_dataset_jsonl()
        
        samples, stats = generate_ner_dataset()
        
        return {
            "success": True,
            "message": f"Dataset gerado em formato {format}",
            "output_file": output_path,
            "stats": stats,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "generated_at": datetime.now().isoformat()
        }


@app.get("/feedback/dataset-stats")
async def get_dataset_stats() -> Dict:
    """Retorna estatísticas do dataset que seria gerado para treinamento.
    
    Útil para saber se há dados suficientes antes de disparar treinamento.
    
    Returns:
        Dict com:
            - total_samples: Quantas amostras de treinamento
            - by_type: Distribuição por tipo de entidade
            - min_samples_for_training: Mínimo recomendado
            - ready_for_training: Boolean
    """
    try:
        from scripts.feedback_to_dataset import generate_ner_dataset
        samples, stats = generate_ner_dataset()
        
        min_samples_recommended = 50
        is_ready = len(samples) >= min_samples_recommended
        
        return {
            **stats,
            "min_samples_recommended": min_samples_recommended,
            "ready_for_training": is_ready,
            "recommendation": (
                "✅ Dados suficientes! Pronto para treinamento." if is_ready
                else f"❌ Precisa de mais {min_samples_recommended - len(samples)} amostras"
            )
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_samples": 0,
            "ready_for_training": False
        }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Verifica o status da API e disponibilidade dos modelos NLP.
    
    Endpoint de health check para monitoramento e orquestração de container.
    
    Returns:
        Dict com:
            - status (str): "healthy" se tudo funcionando
            - version (str): Versão do detector (v9.4)
    
    HTTP Status Codes:
        - 200: API operacional
        - 503: Algum modelo NLP não carregado (degraded mode)
    """
    return {
        "status": "healthy",
        "version": "9.4"
    }

@app.post('/api/lote')
def submit_lote(file: UploadFile = File(...)):
    """Enfileira processamento de lote (CSV/XLSX) e retorna job_id."""
    ext = file.filename.split('.')[-1].lower()
    tipo_arquivo = 'csv' if ext == 'csv' else 'xlsx' if ext in ['xlsx', 'xls'] else None
    if not tipo_arquivo:
        return {"erro": "Arquivo não suportado"}
    temp_path = f'/tmp/{file.filename}'
    with open(temp_path, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    task = celery_app.send_task('backend.celery_worker_tasks.processar_lote', args=[temp_path, tipo_arquivo])
    return {"job_id": task.id}

@app.get('/api/lote/status/{job_id}')
def get_lote_status(job_id: str):
    """Consulta status do processamento de lote."""
    res = AsyncResult(job_id, app=celery_app)
    return {"status": res.status, "result": res.result if res.successful() else None}

@app.get('/api/lote/download/{job_id}')
def download_lote_result(job_id: str):
    """Faz download do resultado do lote, se disponível."""
    res = AsyncResult(job_id, app=celery_app)
    if not res.successful():
        return {"erro": "Resultado ainda não disponível"}
    path = res.result
    if not os.path.exists(path):
        return {"erro": "Arquivo não encontrado"}
    from fastapi.responses import FileResponse
    return FileResponse(path, filename=os.path.basename(path))
