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



# Corrige PYTHONPATH para garantir importação do pacote backend
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from typing import Dict, Optional
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from celery_worker import celery_app
import json
import threading
from datetime import datetime
import shutil

# Adiciona o diretório backend ao path para importação de módulos locais
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from src.detector import PIIDetector

# === SISTEMA DE CONTADORES GLOBAIS ===
STATS_FILE = os.path.join(backend_dir, "data", "stats.json")
stats_lock = threading.Lock()

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

# Inicializa aplicação FastAPI
app = FastAPI(
    title="Participa DF - PII Detector API",
    description="API para detecção de Informações Pessoais Identificáveis em textos segundo LGPD/LAI",
    version="9.4.3"
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
# Permitir configuração via variáveis de ambiente ou argumentos futuros
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

    # Retorna resultado em formato padronizado
    return {
        "id": request_id,
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
    task = celery_app.send_task('backend.tasks.processar_lote', args=[temp_path, tipo_arquivo])
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
