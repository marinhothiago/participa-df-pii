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
from fastapi import FastAPI, UploadFile, File, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
import atexit
from collections import defaultdict
import time

# ═══════════════════════════════════════════════════════════════════════════════
# RATE LIMITING POR IP
# ═══════════════════════════════════════════════════════════════════════════════
# Configuração: máximo de requisições por IP por janela de tempo
# NOTA: Limite alto (300) para suportar upload de arquivos em lote (até 200 linhas)
RATE_LIMIT_REQUESTS = 300  # Máximo de requisições por minuto
RATE_LIMIT_WINDOW = 60     # Janela de tempo em segundos (1 minuto)
MIN_TEXT_LENGTH = 10       # Comprimento mínimo do texto para análise válida
MAX_BATCH_SIZE = 200       # Máximo de itens por requisição batch

# Armazena contagem de requisições por IP: {ip: [(timestamp, count), ...]}
rate_limit_store: Dict[str, list] = defaultdict(list)
rate_limit_lock = threading.Lock()

# ═══════════════════════════════════════════════════════════════════════════════
# DETECÇÃO DE BOTS E CRAWLERS
# ═══════════════════════════════════════════════════════════════════════════════
# Padrões de User-Agent conhecidos de bots/crawlers
BOT_USER_AGENTS = [
    "bot", "crawler", "spider", "scraper", "curl", "wget", "python-requests",
    "httpx", "aiohttp", "go-http-client", "java", "perl", "ruby", "php",
    "headless", "phantom", "selenium", "puppeteer", "playwright",
    "googlebot", "bingbot", "yandex", "baidu", "duckduck", "facebookexternal",
    "twitterbot", "linkedinbot", "slackbot", "telegrambot", "whatsapp",
    "applebot", "semrush", "ahrefs", "mj12bot", "dotbot", "petalbot",
    "dataforseo", "bytespider", "gptbot", "claudebot", "anthropic",
]

# Armazena requisições suspeitas para análise: {ip: {ua, count, first_seen, texts}}
suspicious_requests: Dict[str, Dict] = defaultdict(lambda: {"ua": "", "count": 0, "first_seen": None, "texts": []})
suspicious_lock = threading.Lock()


def is_bot_user_agent(user_agent: str) -> bool:
    """Verifica se o User-Agent parece ser de um bot/crawler."""
    ua_lower = user_agent.lower()
    return any(bot in ua_lower for bot in BOT_USER_AGENTS)


def track_suspicious_request(ip: str, user_agent: str, text: str) -> None:
    """Registra requisição suspeita para análise posterior."""
    with suspicious_lock:
        entry = suspicious_requests[ip]
        entry["ua"] = user_agent
        entry["count"] += 1
        if entry["first_seen"] is None:
            entry["first_seen"] = datetime.now().isoformat()
        # Guarda apenas os primeiros 5 textos para análise
        if len(entry["texts"]) < 5:
            entry["texts"].append(text[:100])

# === HUGGINGFACE HUB PARA PERSISTÊNCIA ===
try:
    from huggingface_hub import hf_hub_download, HfApi
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    print("⚠️ huggingface_hub não disponível - usando storage local")

# Configuração do HF Dataset para persistência
HF_TOKEN = os.environ.get("HF_TOKEN")
HF_STATS_REPO = os.environ.get("HF_STATS_REPO", "marinhothiago/desafio-participa-df")
USE_HF_STORAGE = HF_HUB_AVAILABLE and HF_TOKEN is not None

# Chave secreta para endpoints administrativos
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")

if USE_HF_STORAGE:
    print(f"✅ Persistência HuggingFace ativada: {HF_STATS_REPO}")
    print(f"   📦 Modo BATCH: commits a cada 5 minutos (evita rate limit)")
else:
    print("📁 Usando storage local (HF_TOKEN não configurado)")

# === SISTEMA DE CONTADORES GLOBAIS ===
STATS_FILE = os.path.join(backend_dir, "data", "stats.json")
FEEDBACK_FILE = os.path.join(backend_dir, "data", "feedback.json")
TRAINING_STATUS_FILE = os.path.join(backend_dir, "data", "training_status.json")
stats_lock = threading.Lock()
feedback_lock = threading.Lock()

# Cache local para reduzir chamadas ao HF
_stats_cache: Dict = None
_stats_cache_time: float = 0
_feedback_cache: Dict = None
_feedback_cache_time: float = 0
STATS_CACHE_TTL = 60  # segundos
FEEDBACK_CACHE_TTL = 30  # segundos

# === SISTEMA DE BATCH PARA HF (evita rate limit de 128 commits/hora) ===
import time as _time_module
_pending_hf_sync: Dict[str, bool] = {"stats.json": False, "feedback.json": False}
_last_hf_sync: float = _time_module.time()  # ← Inicia com tempo atual para esperar 5min antes do 1º sync
HF_SYNC_INTERVAL = 300  # 5 minutos entre commits (máx 12/hora)
_sync_lock = threading.Lock()

def _sync_to_hf_if_needed(force: bool = False) -> None:
    """Sincroniza arquivos pendentes com HF Dataset (batch)."""
    global _last_hf_sync, _pending_hf_sync
    import time
    
    if not USE_HF_STORAGE:
        return
    
    with _sync_lock:
        now = time.time()
        time_since_last = now - _last_hf_sync
        
        # Só sincroniza se passou tempo suficiente ou forçado
        if not force and time_since_last < HF_SYNC_INTERVAL:
            return
        
        # Verifica se há algo pendente
        files_to_sync = [f for f, pending in _pending_hf_sync.items() if pending]
        if not files_to_sync:
            return
        
        print(f"🔄 Sincronizando {len(files_to_sync)} arquivo(s) com HuggingFace...")
        
        try:
            import tempfile
            api = HfApi(token=HF_TOKEN)
            
            # Prepara arquivos para upload em batch
            operations = []
            for filename in files_to_sync:
                local_path = STATS_FILE if filename == "stats.json" else FEEDBACK_FILE
                if os.path.exists(local_path):
                    with open(local_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Cria arquivo temporário
                    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
                    json.dump(data, temp_file, indent=2, ensure_ascii=False)
                    temp_file.close()
                    
                    from huggingface_hub import CommitOperationAdd
                    operations.append(CommitOperationAdd(
                        path_in_repo=filename,
                        path_or_fileobj=temp_file.name
                    ))
            
            if operations:
                # Commit único com todos os arquivos
                stats = _stats_cache or {}
                api.create_commit(
                    repo_id=HF_STATS_REPO,
                    repo_type="dataset",
                    operations=operations,
                    commit_message=f"Batch sync: {stats.get('site_visits', 0)} visits, {stats.get('classification_requests', 0)} requests"
                )
                
                # Limpa arquivos temporários
                for op in operations:
                    try:
                        os.unlink(op.path_or_fileobj)
                    except:
                        pass
                
                # Marca como sincronizado
                for filename in files_to_sync:
                    _pending_hf_sync[filename] = False
                
                _last_hf_sync = now
                print(f"✅ Sincronizado com HuggingFace: {', '.join(files_to_sync)}")
        
        except Exception as e:
            print(f"⚠️ Erro ao sincronizar com HF: {e}")

def _mark_pending_sync(filename: str) -> None:
    """Marca arquivo como pendente de sincronização."""
    global _pending_hf_sync
    _pending_hf_sync[filename] = True
    # Tenta sincronizar (só vai se passou tempo suficiente)
    _sync_to_hf_if_needed()

def _force_sync_on_shutdown() -> None:
    """Força sincronização ao encerrar a aplicação."""
    print("🛑 Encerrando - sincronizando dados pendentes...")
    _sync_to_hf_if_needed(force=True)

# Registra sincronização ao encerrar
atexit.register(_force_sync_on_shutdown)

def _load_from_hf(filename: str) -> Dict:
    """Carrega arquivo JSON do HuggingFace Dataset."""
    try:
        path = hf_hub_download(
            repo_id=HF_STATS_REPO,
            filename=filename,
            repo_type="dataset",
            token=HF_TOKEN
        )
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erro ao carregar {filename} do HF: {e}")
        return None

def load_stats() -> Dict:
    """Carrega estatísticas (cache > local > HF)."""
    global _stats_cache, _stats_cache_time
    import time
    
    # Verifica cache primeiro
    if _stats_cache is not None and (time.time() - _stats_cache_time) < STATS_CACHE_TTL:
        return _stats_cache.copy()
    
    stats = None
    
    # Tenta carregar do arquivo local primeiro (mais rápido)
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                stats = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar stats local: {e}")
    
    # Fallback para HF se local não existe
    if stats is None and USE_HF_STORAGE:
        stats = _load_from_hf("stats.json")
        # Salva localmente para próximas leituras
        if stats:
            try:
                os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
                with open(STATS_FILE, 'w') as f:
                    json.dump(stats, f, indent=2)
            except:
                pass
    
    if stats is None:
        stats = {"site_visits": 0, "classification_requests": 0, "last_updated": None}
    
    # Atualiza cache
    _stats_cache = stats.copy()
    _stats_cache_time = time.time()
    
    return stats

def save_stats(stats: Dict) -> None:
    """Salva estatísticas (local imediato + HF em batch)."""
    global _stats_cache, _stats_cache_time
    import time
    
    stats["last_updated"] = datetime.now().isoformat()
    
    # Sempre salva localmente (imediato)
    try:
        os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        print(f"Erro ao salvar stats local: {e}")
    
    # Marca para sincronização em batch com HF
    if USE_HF_STORAGE:
        _mark_pending_sync("stats.json")
    
    # Atualiza cache
    _stats_cache = stats.copy()
    _stats_cache_time = time.time()

def increment_stat(key: str, amount: int = 1) -> Dict:
    """Incrementa uma estatística de forma thread-safe."""
    with stats_lock:
        stats = load_stats()
        stats[key] = stats.get(key, 0) + amount
        save_stats(stats)
        return stats


# === SISTEMA DE FEEDBACK HUMANO ===
def load_feedback() -> Dict:
    """Carrega feedbacks (cache > local > HF)."""
    global _feedback_cache, _feedback_cache_time
    import time
    
    # Verifica cache primeiro
    if _feedback_cache is not None and (time.time() - _feedback_cache_time) < FEEDBACK_CACHE_TTL:
        return _feedback_cache.copy()
    
    data = None
    
    # Tenta carregar do arquivo local primeiro (mais rápido)
    try:
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar feedback local: {e}")
    
    # Fallback para HF se local não existe
    if data is None and USE_HF_STORAGE:
        data = _load_from_hf("feedback.json")
        # Salva localmente para próximas leituras
        if data:
            try:
                os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
                with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except:
                pass
    
    if data is None:
        data = {
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
    
    # Atualiza cache
    _feedback_cache = data.copy()
    _feedback_cache_time = time.time()
    
    return data


def save_feedback(data: Dict) -> None:
    """Salva feedbacks (local imediato + HF em batch)."""
    global _feedback_cache, _feedback_cache_time
    import time
    
    data["last_updated"] = datetime.now().isoformat()
    
    # Sempre salva localmente (imediato)
    try:
        os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar feedback local: {e}")
    
    # Marca para sincronização em batch com HF
    if USE_HF_STORAGE:
        _mark_pending_sync("feedback.json")
    
    # Atualiza cache
    _feedback_cache = data.copy()
    _feedback_cache_time = time.time()


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



from src.confidence.combiners import merge_spans_custom


def analyze_single_text(text: str, request_id: Optional[str] = None, force_llm: bool = False, merge_preset: str = "f1") -> Dict:
    """
    Função auxiliar para analisar um único texto.
    Usada tanto pelo /analyze quanto pelo /analyze/batch.
    
    Args:
        text: Texto a ser analisado
        request_id: ID opcional da requisição
        force_llm: Forçar uso do árbitro LLM
        merge_preset: Estratégia de merge de spans
    
    Returns:
        Dict com resultado da análise no formato padrão
    """
    # Validação de texto mínimo
    text_length = len(text.strip()) if text else 0
    if text_length < MIN_TEXT_LENGTH:
        return {
            "id": request_id,
            "has_pii": False,
            "entities": [],
            "risk_level": "BAIXO",
            "confidence_all_found": 1.0,
            "total_entities": 0,
            "sources_used": [],
            "classificacao": "PÚBLICO",
            "risco": "BAIXO",
            "confianca": 1.0,
            "detalhes": [],
            "_warning": f"Texto muito curto ({text_length} caracteres). Mínimo: {MIN_TEXT_LENGTH} caracteres.",
            "_valid_for_stats": False
        }
    
    # Executa detecção usando detector híbrido
    has_pii, findings, risco, confianca = detector.detect(text, force_llm=force_llm)
    
    # Estratégias de merge (mantido para compatibilidade)
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
    
    return {
        "id": request_id,
        "has_pii": has_pii,
        "entities": findings,
        "risk_level": risco,
        "confidence_all_found": confianca,
        "total_entities": len(findings) if findings else 0,
        "sources_used": list(set(f.get("fonte", "regex") for f in findings)) if findings else [],
        "classificacao": "NÃO PÚBLICO" if has_pii else "PÚBLICO",
        "risco": risco,
        "confianca": confianca,
        "detalhes": findings,
        "_valid_for_stats": True
    }


def check_rate_limit(ip: str) -> tuple[bool, int]:
    """
    Verifica se o IP excedeu o rate limit.
    
    Args:
        ip: Endereço IP do cliente
        
    Returns:
        Tuple (is_allowed, remaining_requests)
        - is_allowed: True se a requisição é permitida
        - remaining_requests: Quantas requisições restam na janela
    """
    current_time = time.time()
    window_start = current_time - RATE_LIMIT_WINDOW
    
    with rate_limit_lock:
        # Remove timestamps antigos fora da janela
        rate_limit_store[ip] = [
            ts for ts in rate_limit_store[ip] 
            if ts > window_start
        ]
        
        # Conta requisições na janela atual
        request_count = len(rate_limit_store[ip])
        remaining = max(0, RATE_LIMIT_REQUESTS - request_count)
        
        if request_count >= RATE_LIMIT_REQUESTS:
            return False, 0
        
        # Adiciona timestamp da requisição atual
        rate_limit_store[ip].append(current_time)
        return True, remaining - 1


@app.post("/analyze")
async def analyze(
    request: Request,
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
    # Log para debug de requisições
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    text = data.get("text", "")
    text_preview = text[:50].replace("\n", " ") if text else ""
    request_id = data.get("id", None)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DETECÇÃO DE BOTS: Registra requisições suspeitas para análise
    # ═══════════════════════════════════════════════════════════════════════════
    is_bot = is_bot_user_agent(user_agent)
    if is_bot:
        logging.warning(f"🤖 BOT DETECTADO | IP: {client_ip} | UA: {user_agent[:80]} | Text: '{text_preview}...'")
        track_suspicious_request(client_ip, user_agent, text)
    else:
        logging.info(f"📊 POST /analyze | IP: {client_ip} | UA: {user_agent[:60]} | Text: '{text_preview}...'")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RATE LIMITING: Verifica se IP excedeu limite de requisições
    # ═══════════════════════════════════════════════════════════════════════════
    is_allowed, remaining = check_rate_limit(client_ip)
    if not is_allowed:
        logging.warning(f"⚠️ Rate limit excedido para IP: {client_ip}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": f"Limite de {RATE_LIMIT_REQUESTS} requisições por minuto excedido. Tente novamente em breve.",
                "retry_after": RATE_LIMIT_WINDOW
            },
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
        )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ANÁLISE: Usa função auxiliar para processar o texto
    # ═══════════════════════════════════════════════════════════════════════════
    result = analyze_single_text(text, request_id, force_llm=use_llm, merge_preset=merge_preset)
    
    # Só conta nas estatísticas se for texto válido (não-bot e tamanho mínimo)
    if result.get("_valid_for_stats") and not is_bot:
        increment_stat("classification_requests")
    
    # Remove campo interno antes de retornar
    result.pop("_valid_for_stats", None)
    
    return result


@app.post("/analyze/batch")
async def analyze_batch(
    request: Request,
    data: Dict[str, List],
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
    Analisa múltiplos textos em uma única requisição.
    Ideal para processamento de arquivos em lote.
    
    Body:
        {"items": [{"id": "1", "text": "..."}, {"id": "2", "text": "..."}, ...]}
    
    Limite: 200 itens por requisição.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    items = data.get("items", [])
    
    logging.info(f"📦 POST /analyze/batch | IP: {client_ip} | Items: {len(items)}")
    
    # Validação do tamanho do batch
    if len(items) > MAX_BATCH_SIZE:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content={
                "error": "batch_too_large",
                "message": f"Máximo de {MAX_BATCH_SIZE} itens por requisição. Recebido: {len(items)}",
                "max_batch_size": MAX_BATCH_SIZE
            }
        )
    
    # Rate limiting: conta como 1 requisição + número de itens / 10
    # Isso permite batches grandes sem bloquear, mas limita abuso
    rate_cost = 1 + (len(items) // 10)
    for _ in range(rate_cost):
        is_allowed, _ = check_rate_limit(client_ip)
        if not is_allowed:
            logging.warning(f"⚠️ Rate limit excedido para IP: {client_ip} (batch)")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Limite de requisições excedido. Tente novamente em breve.",
                    "retry_after": RATE_LIMIT_WINDOW
                },
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
            )
    
    # Processa todos os itens
    results = []
    valid_count = 0
    
    for item in items:
        item_id = item.get("id")
        item_text = item.get("text", "")
        
        result = analyze_single_text(item_text, item_id, force_llm=use_llm, merge_preset=merge_preset)
        
        if result.get("_valid_for_stats"):
            valid_count += 1
        
        # Remove campo interno
        result.pop("_valid_for_stats", None)
        results.append(result)
    
    # Conta apenas textos válidos nas estatísticas
    if valid_count > 0 and not is_bot_user_agent(user_agent):
        increment_stat("classification_requests", valid_count)
    
    return {
        "total": len(results),
        "valid_texts": valid_count,
        "results": results
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


from fastapi import Header, HTTPException

@app.post("/admin/reset-stats")
async def reset_stats(x_admin_key: str = Header(None, alias="X-Admin-Key")) -> Dict:
    """Reseta todos os contadores e feedbacks.
    
    Requer header X-Admin-Key com a chave secreta configurada em ADMIN_KEY.
    
    Returns:
        Dict com confirmação do reset
    """
    global _stats_cache, _feedback_cache, _stats_cache_time, _feedback_cache_time
    
    # Validar chave de admin
    if not ADMIN_KEY:
        raise HTTPException(status_code=503, detail="ADMIN_KEY não configurada no servidor")
    
    if not x_admin_key or x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Chave de administrador inválida")
    
    # Resetar stats
    empty_stats = {"site_visits": 0, "classification_requests": 0, "last_updated": None}
    with stats_lock:
        save_stats(empty_stats)
        _stats_cache = None
        _stats_cache_time = 0
    
    # Resetar feedbacks
    empty_feedback = {"feedbacks": [], "total_count": 0}
    with feedback_lock:
        save_feedback(empty_feedback)
        _feedback_cache = None
        _feedback_cache_time = 0
    
    # Forçar sync imediato com HF
    if USE_HF_STORAGE:
        _sync_to_hf_if_needed(force=True)
    
    print("🗑️ ADMIN: Todos os contadores e feedbacks foram resetados")
    
    return {
        "success": True,
        "message": "Todos os contadores e feedbacks foram resetados",
        "stats": empty_stats,
        "feedback": empty_feedback
    }


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
    
    # ✨ Recalibração automática a cada feedback
    try:
        try:
            from src.confidence.auto_recalibrate import recalibrate_from_feedbacks
        except ImportError:
            from backend.src.confidence.auto_recalibrate import recalibrate_from_feedbacks
        
        feedback_data = load_feedback()
        total_fb = len(feedback_data.get("feedbacks", []))
        logging.info(f"📥 Recalibração: {total_fb} feedbacks total no arquivo")
        
        recalibration_result = recalibrate_from_feedbacks(feedback_data)
        logging.info(f"🔄 Recalibração automática: {recalibration_result.get('message')}")
        if recalibration_result.get('success'):
            logging.info(f"   ✅ {recalibration_result.get('total_samples')} amostras processadas")
            logging.info(f"   📊 By source: {recalibration_result.get('by_source')}")
    except Exception as e:
        import traceback
        logging.error(f"❌ Erro na recalibração automática: {e}")
        logging.error(traceback.format_exc())
    
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


@app.get("/feedback/training-status")
async def get_training_status() -> Dict:
    """Retorna status de treinamento e calibração automática.
    
    Combina dados de:
    - feedback.json: Estatísticas de feedback dos usuários (persistente)
    - training_status.json: Histórico de calibração do modelo
    
    Mostra:
    - Total de feedbacks coletados
    - Acurácia do modelo baseada em feedback humano
    - Distribuição de validações (correto/incorreto/parcial)
    - Estatísticas por tipo de PII
    - Recomendações automáticas
    
    Returns:
        Dict com status completo do treinamento
    """
    try:
        # Carregar estatísticas de feedback (persistentes)
        feedback_data = load_feedback()
        stats = feedback_data.get("stats", {})
        
        total_entities = stats.get("total_entities_reviewed", 0)
        correct = stats.get("correct", 0)
        incorrect = stats.get("incorrect", 0)
        partial = stats.get("partial", 0)
        
        # Calcular acurácia baseada em feedback humano
        accuracy = correct / total_entities if total_entities > 0 else 0
        
        # Gerar status baseado na quantidade de dados
        if total_entities == 0:
            status = "never_trained"
            time_since_last = "Nenhum feedback ainda"
        elif total_entities < 20:
            status = "learning"
            time_since_last = f"{total_entities} feedbacks coletados"
        elif total_entities < 50:
            status = "improving"
            time_since_last = f"{total_entities} feedbacks coletados"
        else:
            status = "ready" if accuracy >= 0.85 else "needs_attention"
            time_since_last = f"{total_entities} feedbacks coletados"
        
        # Gerar recomendações dinâmicas
        recommendations = []
        
        if total_entities == 0:
            recommendations.append({
                "type": "get_started",
                "message": "📝 Comece a avaliar detecções para treinar o modelo",
                "action": "Use o painel de feedback nas análises",
            })
        elif total_entities < 20:
            needed = 20 - total_entities
            recommendations.append({
                "type": "collect_more_data",
                "message": f"📊 Precisamos de mais {needed} avaliações para calibração inicial",
                "action": "Continue avaliando detecções",
            })
        elif total_entities < 50:
            needed = 50 - total_entities
            recommendations.append({
                "type": "collect_more_data",
                "message": f"📊 Mais {needed} avaliações para treinamento robusto",
                "action": "Continue coletando feedbacks",
            })
        
        if accuracy < 0.85 and total_entities >= 20:
            recommendations.append({
                "type": "needs_attention",
                "message": f"⚠️ Acurácia atual: {accuracy*100:.1f}%. Investigar tipos problemáticos.",
                "action": "Revisar tipos com mais erros",
            })
        
        if accuracy >= 0.90 and total_entities >= 50:
            recommendations.append({
                "type": "ready_for_finetuning",
                "message": "✅ Dados suficientes e acurácia boa! Modelo calibrado.",
                "action": "Sistema pronto para uso em produção",
            })
        
        # Tentar carregar também o training_status.json (calibração manual)
        training_data = {}
        try:
            try:
                from src.confidence.training import get_training_tracker
            except ImportError:
                from backend.src.confidence.training import get_training_tracker
            
            tracker = get_training_tracker()
            training_data = tracker.data
        except Exception:
            pass
        
        return {
            "status": status,
            "last_calibration": training_data.get("last_calibration"),
            "total_samples_used": total_entities,
            "total_feedbacks": stats.get("total_feedbacks", 0),
            "accuracy_before": training_data.get("accuracy_before", 0),
            "accuracy_after": accuracy,
            "improvement_percentage": round((accuracy - training_data.get("accuracy_before", 0)) * 100, 2) if accuracy > 0 else 0,
            "time_since_last": time_since_last,
            "by_source": stats.get("by_type", {}),
            "validation_breakdown": {
                "correct": correct,
                "incorrect": incorrect,
                "partial": partial,
            },
            "recommendations": recommendations,
        }
    except Exception as e:
        import traceback
        logger.error(f"Erro ao obter status de treinamento: {e}\n{traceback.format_exc()}")
        return {
            "error": str(e),
            "status": "error",
            "message": "Erro ao obter status de treinamento"
        }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Verifica o status da API e disponibilidade dos modelos NLP.
    
    Endpoint de health check para monitoramento e orquestração de container.
    NÃO incrementa contadores de estatísticas.
    
    Returns:
        Dict com:
            - status (str): "healthy" se tudo funcionando
            - version (str): Versão do detector (v9.6)
    
    HTTP Status Codes:
        - 200: API operacional
        - 503: Algum modelo NLP não carregado (degraded mode)
    """
    # Health check NÃO incrementa contadores - apenas retorna status
    return {
        "status": "healthy",
        "version": "9.6"
    }


@app.get("/rate-limit/status")
async def rate_limit_status(request: Request) -> Dict:
    """Verifica status do rate limit para o IP do cliente.
    
    Returns:
        Dict com:
            - ip (str): IP do cliente
            - requests_in_window (int): Requisições feitas na janela atual
            - limit (int): Limite máximo de requisições
            - remaining (int): Requisições restantes
            - window_seconds (int): Tamanho da janela em segundos
            - min_text_length (int): Comprimento mínimo de texto aceito
            - max_batch_size (int): Máximo de itens por requisição batch
    """
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    window_start = current_time - RATE_LIMIT_WINDOW
    
    with rate_limit_lock:
        # Conta requisições na janela atual
        requests_in_window = len([
            ts for ts in rate_limit_store.get(client_ip, [])
            if ts > window_start
        ])
    
    return {
        "ip": client_ip,
        "requests_in_window": requests_in_window,
        "limit": RATE_LIMIT_REQUESTS,
        "remaining": max(0, RATE_LIMIT_REQUESTS - requests_in_window),
        "window_seconds": RATE_LIMIT_WINDOW,
        "min_text_length": MIN_TEXT_LENGTH,
        "max_batch_size": MAX_BATCH_SIZE
    }


@app.get("/admin/suspicious-requests")
async def get_suspicious_requests(key: str = Query(..., description="Chave de administrador")) -> Dict:
    """
    [ADMIN] Lista requisições suspeitas de bots detectados.
    
    Requer a chave de administrador configurada em ADMIN_KEY.
    
    Returns:
        Dict com:
            - total_ips (int): Quantidade de IPs suspeitos
            - requests (Dict): Mapa de IP -> detalhes das requisições
    """
    if not ADMIN_KEY or key != ADMIN_KEY:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=403,
            content={"error": "forbidden", "message": "Chave de administrador inválida"}
        )
    
    with suspicious_lock:
        # Copia dados para evitar race condition
        data = dict(suspicious_requests)
    
    return {
        "total_ips": len(data),
        "bot_patterns": BOT_USER_AGENTS[:10],  # Mostra os primeiros 10 padrões
        "requests": data
    }


@app.delete("/admin/suspicious-requests")
async def clear_suspicious_requests(key: str = Query(..., description="Chave de administrador")) -> Dict:
    """
    [ADMIN] Limpa o registro de requisições suspeitas.
    
    Requer a chave de administrador configurada em ADMIN_KEY.
    """
    if not ADMIN_KEY or key != ADMIN_KEY:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=403,
            content={"error": "forbidden", "message": "Chave de administrador inválida"}
        )
    
    with suspicious_lock:
        count = len(suspicious_requests)
        suspicious_requests.clear()
    
    return {
        "cleared": count,
        "message": f"Removidos {count} IPs suspeitos do registro"
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
    return FileResponse(path, filename=os.path.basename(path))
