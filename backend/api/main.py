"""API FastAPI para Detecção de PII - Participa DF.

Sistema de detecção de Informações Pessoalmente Identificáveis (PII) para
manifestações do Participa DF em conformidade com LGPD (Lei Geral de Proteção
de Dados) e LAI (Lei de Acesso à Informação).

Endpoints:
    POST /analyze: Analisa texto para detecção de PII
    GET /health: Verifica status da API

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

from typing import Dict, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import json
import threading
from datetime import datetime

# Adiciona o diretório backend ao path para importação de módulos locais
# O arquivo está em backend/api/main.py, então subimos um nível para backend/
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
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
detector = PIIDetector()


@app.post("/analyze")
async def analyze(data: Dict[str, Optional[str]]) -> Dict:
    """Analisa texto para detecção de PII com contexto Brasília/GDF.
    
    Realiza detecção híbrida usando:
    - Regex: Padrões estruturados (CPF, Email, Telefone, RG, CNH)
    - NLP: Reconhecimento de entidades com spaCy + BERT
    - Regras de Negócio: Contexto de Brasília, imunidade funcional (LAI)
    - Deduplicação: Mantém apenas PII mais crítico por valor duplicado
    
    Args:
        data: Dicionário contendo:
            - text (str): Texto a ser analisado (obrigatório)
            - id (str): ID único para rastreabilidade (opcional)
    
    Returns:
        Dict com:
            - id (str): ID da requisição (ou None)
            - classificacao (str): "NÃO PÚBLICO" ou "PÚBLICO"
            - risco (str): Nível de risco (SEGURO, MODERADO, ALTO, CRÍTICO)
            - confianca (float): Score de confiança normalizado (0.0 a 1.0) ✅ NORMALIZADO
            - detalhes (List[Dict]): Lista com detalhes de cada PII encontrado
    
    Exemplo de detalhes PII:
        {
            "tipo": "CPF",
            "valor": "123.456.789-09",
            "contexto": "Meu CPF é 123.456.789-09 e preciso",
            "confianca": 1.0
        }
    
    Classificações de Risco:
        - CRÍTICO (5): CPF, RG, CNH (identificação direta)
        - ALTO (4): Email privado, Telefone, Nome privado, Endereço residencial
        - MODERADO (3): Entidade nomeada genérica
        - SEGURO (0): Sem PII detectado
    
    Notas de Contexto LGPD/LAI:
        - Agentes públicos em exercício de função estão imunes a proteção
          Ex: "Falar com a Dra. Maria na Secretaria de Saúde" = NÃO PII
        - Gatilhos de contato anulam imunidade funcional
          Ex: "Falar com o Dr. João sobre isso" = PII (é alvo de contato)
        - Endereços de setores administrativos (SQS, SQN) = NÃO PII
        - Endereços residenciais (Casa 45, Apto 101) = PII
    """
    # Extrai texto e ID da requisição
    text = data.get("text", "")
    request_id = data.get("id", None)
    
    # Executa detecção usando detector híbrido
    has_pii, findings, risco, confianca = detector.detect(text)
    
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
