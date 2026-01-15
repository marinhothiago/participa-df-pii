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
        "confianca": 5.0,
        "detalhes": [{"tipo": "CPF", "valor": "123.456.789-09", ...}]
    }
"""

from typing import Dict, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Adiciona o diretório src ao path para importação de módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.detector import PIIDetector

# Inicializa aplicação FastAPI
app = FastAPI(
    title="Participa DF - PII Detector API",
    description="API para detecção de Informações Pessoais Identificáveis em textos segundo LGPD/LAI",
    version="8.5"
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
            - confianca (float): Score de confiança (0.0 a 5.0)
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
    
    # Retorna resultado em formato padronizado
    return {
        "id": request_id,
        "classificacao": "NÃO PÚBLICO" if has_pii else "PÚBLICO",
        "risco": risco,
        "confianca": confianca,
        "detalhes": findings
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Verifica o status da API e disponibilidade dos modelos NLP.
    
    Endpoint de health check para monitoramento e orquestração de container.
    
    Returns:
        Dict com:
            - status (str): "healthy" se tudo funcionando
            - version (str): Versão do detector (v8.5)
    
    HTTP Status Codes:
        - 200: API operacional
        - 503: Algum modelo NLP não carregado (degraded mode)
    """
    return {
        "status": "healthy",
        "version": "8.5"
    }
