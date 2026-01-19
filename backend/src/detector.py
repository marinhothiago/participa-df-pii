"""
Módulo de detecção de Informações Pessoais Identificáveis (PII).
Versão: 9.5.0 - HACKATHON PARTICIPA-DF 2025
Abordagem: Ensemble híbrido com alta recall (estratégia OR) + Árbitro LLM
Confiança: Sistema probabilístico com calibração e log-odds

Pipeline:
1. Regras determinísticas (regex + validação DV) → 70% dos PIIs
2. NER BERT Davlan (multilíngue) → nomes e entidades
3. NER NuNER (especializado pt-BR) → nomes brasileiros
4. spaCy como backup → cobertura adicional
5. Ensemble OR → qualquer detector positivo = PII
6. Árbitro LLM (Llama-70B) → casos ambíguos
7. Cálculo probabilístico de confiança → calibração + log-odds
"""

import re
import os
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache

import torch
from transformers import pipeline
from text_unidecode import unidecode

try:
    import requests
except ImportError:
    requests = None

# Logger padrão para debug
logger = logging.getLogger("detector")

# Device para pipelines transformers (GPU se disponível, senão CPU)
DEVICE = 0 if torch.cuda.is_available() else -1

# === IMPORTS DO PROJETO ===
try:
    from .allow_list import (
        BLOCKLIST_TOTAL, TERMOS_SEGUROS, INDICADORES_SERVIDOR, CARGOS_AUTORIDADE,
        GATILHOS_CONTATO, CONTEXTOS_PII, PESOS_PII, CONFIANCA_BASE, ALLOW_LIST_AVAILABLE
    )
except ImportError:
    # Fallback se allow_list não existir
    BLOCKLIST_TOTAL = set()
    TERMOS_SEGUROS = set()
    INDICADORES_SERVIDOR = set()
    CARGOS_AUTORIDADE = set()
    GATILHOS_CONTATO = set()
    CONTEXTOS_PII = set()
    PESOS_PII = {}
    CONFIANCA_BASE = {}
    ALLOW_LIST_AVAILABLE = False

# BLOCK_IF_CONTAINS - termos que invalidam nome se presentes
BLOCK_IF_CONTAINS = {
    "SECRETARIA", "MINISTÉRIO", "MINISTERIO", "GOVERNO", "FEDERAL",
    "ESTADUAL", "MUNICIPAL", "DISTRITAL", "ADMINISTRAÇÃO", "ADMINISTRACAO",
    "DEPARTAMENTO", "DIRETORIA", "COORDENAÇÃO", "COORDENACAO", "GERÊNCIA",
    "GERENCIA", "ASSESSORIA", "GABINETE", "TRIBUNAL", "CÂMARA", "CAMARA",
    "SENADO", "ASSEMBLEIA", "AUTARQUIA", "FUNDAÇÃO", "FUNDACAO", "EMPRESA",
    "INSTITUTO", "AGÊNCIA", "AGENCIA", "CONSELHO", "COMISSÃO", "COMISSAO",
    "GDF", "SEEDF", "SESDF", "SEDF", "SEJUS", "PCDF", "PMDF", "CBMDF",
    "DETRAN", "CAESB", "CEB", "NOVACAP", "TERRACAP", "BRB", "METRÔ", "METRO"
}

try:
    from .gazetteer_gdf import carregar_gazetteer_gdf
except ImportError:
    # Fallback: tenta importar do mesmo diretório se não for pacote
    try:
        from gazetteer_gdf import carregar_gazetteer_gdf
    except ImportError:
        def carregar_gazetteer_gdf():
            return []

try:
    from .confidence.validators import DVValidator
except ImportError:
    DVValidator = None

try:
    from .confidence.types import PIIFinding
except ImportError:
    PIIFinding = dict

# === INTEGRAÇÃO PRESIDIO FRAMEWORK ===
try:
    from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, EntityRecognizer
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    AnalyzerEngine = None
    Pattern = None
    PatternRecognizer = None
    EntityRecognizer = None


# === ÁRBITRO LLM ===

def arbitrate_with_llama(texto: str, achados: List[Dict], contexto_extra: str = None) -> Tuple[str, str]:
    """
    Usa Llama-70B via Hugging Face Inference API para arbitrar casos ambíguos de PII.
    
    Args:
        texto: Texto sendo analisado
        achados: Lista de PIIs detectados pelo ensemble
        contexto_extra: Contexto adicional opcional
        
    Returns:
        Tuple[str, str]: (decisão, explicação)
            - decisão: 'PII', 'Público' ou 'Indefinido'
            - explicação: Justificativa do LLM
    """
    if requests is None:
        raise RuntimeError("Módulo 'requests' não instalado. Execute: pip install requests")
    
    HF_TOKEN = os.getenv("HF_TOKEN")
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN não encontrado no ambiente. Configure no .env")
    
    endpoint = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-70b-chat-hf"
    
    # Formata achados para o prompt
    achados_str = "\n".join([
        f"  - Tipo: {a.get('tipo')}, Valor: {a.get('valor')}, Confiança: {a.get('confianca', 0):.2f}"
        for a in achados
    ]) if achados else "  Nenhum PII detectado pelo ensemble."
    
    prompt = f"""[INST] Você é um especialista em LGPD e proteção de dados pessoais no Brasil.

Analise o texto abaixo e decida se ele contém dados pessoais identificáveis (PII) que precisam ser protegidos conforme a LGPD.

TEXTO A ANALISAR:
"{texto[:1500]}"

ACHADOS DO SISTEMA AUTOMÁTICO:
{achados_str}

{f"CONTEXTO ADICIONAL: {contexto_extra}" if contexto_extra else ""}

INSTRUÇÕES:
1. Considere que nomes de servidores públicos em contexto funcional NÃO são PII
2. Dados como CPF, telefone pessoal, email pessoal, endereço residencial SÃO PII
3. Nomes de cidadãos comuns (não servidores) em manifestações SÃO PII
4. Dados de saúde, biométricos e de menores são dados SENSÍVEIS (proteção extra)

Responda APENAS com:
DECISÃO: [PII ou PÚBLICO]
EXPLICAÇÃO: [sua justificativa em 2-3 linhas]
[/INST]"""

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.1,
            "do_sample": False
        }
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        # Extrai resposta do LLM
        if isinstance(result, list) and len(result) > 0:
            answer = result[0].get("generated_text", "")
        else:
            answer = result.get("generated_text", "")
        
        # Remove o prompt da resposta se presente
        if "[/INST]" in answer:
            answer = answer.split("[/INST]")[-1].strip()
        
        # Parse da decisão
        answer_upper = answer.upper()
        if "DECISÃO: PII" in answer_upper or "DECISAO: PII" in answer_upper:
            decision = "PII"
        elif "DECISÃO: PÚBLICO" in answer_upper or "DECISAO: PUBLICO" in answer_upper:
            decision = "Público"
        elif "PII" in answer_upper and "PÚBLICO" not in answer_upper:
            decision = "PII"
        elif "PÚBLICO" in answer_upper or "PUBLICO" in answer_upper:
            decision = "Público"
        else:
            decision = "Indefinido"
        
        return decision, answer
        
    except requests.exceptions.Timeout:
        logger.warning("Timeout na chamada ao Llama-70B")
        return "Indefinido", "Timeout na API do Hugging Face"
    except requests.exceptions.RequestException as e:
        logger.warning(f"Erro na chamada ao Llama-70B: {e}")
        return "Indefinido", f"Erro na API: {str(e)}"
    except Exception as e:
        logger.error(f"Erro inesperado no árbitro LLM: {e}")
        return "Indefinido", f"Erro inesperado: {str(e)}"


class PIIDetector:
    def _aplicar_votacao(self, findings: list) -> list:
        """
        Votação PERMISSIVA - prioriza não perder PII (minimizar FN).
        Filosofia: É melhor ter um FP do que um FN (critério de desempate).
        """
        if not findings:
            return []

        # Tipos com validação de DV - SEMPRE aceitar
        TIPOS_ALTA_CONFIANCA = {'CPF', 'CNPJ', 'PIS', 'CNS', 'TITULO_ELEITOR', 'RG', 'CNH', 'PASSAPORTE', 'CTPS'}
        # Tipos sensíveis LGPD - SEMPRE aceitar (peso 5)
        TIPOS_SENSIVEIS = {'DADO_SAUDE', 'DADO_BIOMETRICO', 'MENOR_IDENTIFICADO'}

        por_valor = {}
        for f in findings:
            key = f.get('valor', '').lower().strip()
            if not key:
                continue
            if key not in por_valor:
                por_valor[key] = {'fontes': set(), 'items': []}
            por_valor[key]['fontes'].add(f.get('source', 'unknown'))
            por_valor[key]['items'].append(f)

        confirmados = []
        rejeitados_para_llm = []

        for key, data in por_valor.items():
            fontes = data['fontes']
            items = data['items']
            melhor = max(items, key=lambda x: x.get('confianca', 0))
            tipo = melhor.get('tipo')
            confianca = melhor.get('confianca', 0)
            source = melhor.get('source')
            peso = melhor.get('peso', 0)

            aceitar = False
            motivo = ""

            # REGRA 1: Documentos com DV - SEMPRE aceitar
            if tipo in TIPOS_ALTA_CONFIANCA:
                aceitar = True
                motivo = "documento_validado"
            # REGRA 2: Dados sensíveis - SEMPRE aceitar
            elif tipo in TIPOS_SENSIVEIS:
                aceitar = True
                motivo = "dado_sensivel_lgpd"
            # REGRA 3: Peso alto (≥4) - SEMPRE aceitar
            elif peso >= 4:
                aceitar = True
                motivo = "peso_alto"
            # REGRA 4: Gatilho linguístico - SEMPRE aceitar
            elif source == 'gatilho':
                aceitar = True
                motivo = "gatilho_linguistico"
            # REGRA 5: Múltiplas fontes concordam - aceitar
            elif len(fontes) >= 2:
                aceitar = True
                motivo = f"votacao_{len(fontes)}_fontes"
            # REGRA 6: Confiança ≥ 0.85 - aceitar
            elif confianca >= 0.85:
                aceitar = True
                motivo = "alta_confianca"
            # REGRA 7: Confiança ≥ 0.70 - aceitar com ressalva (evitar FN)
            elif confianca >= 0.70:
                aceitar = True
                motivo = "confianca_moderada_evitar_fn"
            # REGRA 8: Confiança baixa - candidato a LLM
            else:
                rejeitados_para_llm.append(melhor)
                motivo = "baixa_confianca_pendente_llm"

            if aceitar:
                melhor['votacao_motivo'] = motivo
                confirmados.append(melhor)

        # Itens rejeitados podem ser recuperados pelo LLM
        self._pendentes_llm = rejeitados_para_llm
        return confirmados

    def __init__(
        self,
        usar_gpu: bool = True,
        use_probabilistic_confidence: bool = True,
        use_llm_arbitration: bool = False
    ):
        """
        Inicializa o detector de PII.
        
        Args:
            usar_gpu: Se deve usar GPU para modelos NER
            use_probabilistic_confidence: Se deve usar sistema de confiança probabilística
            use_llm_arbitration: Se deve usar Llama-70B para arbitrar casos ambíguos
        """
        # Configurações
        self.usar_gpu = usar_gpu
        self.use_probabilistic_confidence = use_probabilistic_confidence
        self.use_llm_arbitration = use_llm_arbitration
        
        # Thresholds dinâmicos por tipo de PII
        self.THRESHOLDS_DINAMICOS = {
            "CPF": {"peso_min": 4, "confianca_min": 0.80},
            "CNPJ": {"peso_min": 2, "confianca_min": 0.80},
            "CNPJ_PESSOAL": {"peso_min": 3, "confianca_min": 0.80},
            "NOME": {"peso_min": 2, "confianca_min": 0.70},
            "EMAIL_PESSOAL": {"peso_min": 2, "confianca_min": 0.75},
            "EMAIL_ADDRESS": {"peso_min": 2, "confianca_min": 0.75},
            "TELEFONE": {"peso_min": 2, "confianca_min": 0.75},
            "RG": {"peso_min": 3, "confianca_min": 0.80},
            "CNH": {"peso_min": 3, "confianca_min": 0.80},
            "CARTAO_CREDITO": {"peso_min": 3, "confianca_min": 0.80},
            "ENDERECO_RESIDENCIAL": {"peso_min": 2, "confianca_min": 0.75},
            "DADO_SAUDE": {"peso_min": 4, "confianca_min": 0.75},
            "MENOR_IDENTIFICADO": {"peso_min": 4, "confianca_min": 0.75},
        }
        
        # Pesos do ensemble
        self.ensemble_weights = {
            'regex': 1.0,
            'bert': 1.0,
            'nuner': 0.95,
            'spacy': 0.85,
            'gatilho': 1.1,
        }
        
        # Inicializa estruturas
        self.patterns_compilados: Dict[str, re.Pattern] = {}
        self.pattern_recognizers = {}
        self.presidio_analyzer = None
        self.confidence_calculator = None
        
        # Modelos NER
        self.nlp_bert = None
        self.nlp_nuner = None
        self.nlp_spacy = None
        
        # Validador de DV
        if DVValidator:
            try:
                self.validador = DVValidator()
            except Exception:
                self.validador = None
        else:
            self.validador = None
        
        # Inicializa vocabulários
        self._inicializar_vocabularios()
        
        # Compila patterns regex
        self._compilar_patterns()
        
        # Carrega modelos NER
        self._carregar_modelos_ner()
        
        # Inicializa Presidio se disponível
        if PRESIDIO_AVAILABLE:
            self._inicializar_presidio()
    
    def _inicializar_vocabularios(self) -> None:
        """Inicializa todos os vocabulários e listas de contexto."""
        
        self.blocklist_total: Set[str] = BLOCKLIST_TOTAL.copy() if BLOCKLIST_TOTAL else set()
        self.termos_seguros: Set[str] = TERMOS_SEGUROS.copy() if TERMOS_SEGUROS else set()
        self.indicadores_servidor: Set[str] = INDICADORES_SERVIDOR.copy() if INDICADORES_SERVIDOR else set()
        self.cargos_autoridade: Set[str] = CARGOS_AUTORIDADE.copy() if CARGOS_AUTORIDADE else set()
        self.gatilhos_contato: Set[str] = GATILHOS_CONTATO.copy() if GATILHOS_CONTATO else set()
        self.contextos_pii: Set[str] = CONTEXTOS_PII.copy() if CONTEXTOS_PII else set()
        self.pesos_pii: Dict[str, int] = PESOS_PII.copy() if PESOS_PII else {}
        
        # Confiança base por tipo
        self.confianca_base: Dict[str, float] = CONFIANCA_BASE.copy() if CONFIANCA_BASE else {
            "CPF": 0.95,
            "CNPJ": 0.95,
            "CNPJ_PESSOAL": 0.90,
            "EMAIL_PESSOAL": 0.90,
            "TELEFONE": 0.85,
            "RG": 0.90,
            "CNH": 0.90,
            "PIS": 0.95,
            "CNS": 0.95,
            "PASSAPORTE": 0.90,
            "TITULO_ELEITOR": 0.95,
            "NOME": 0.80,
            "NOME_BERT": 0.82,
            "NOME_SPACY": 0.70,
            "NOME_NUNER": 0.85,
            "NOME_CONTRA": 0.80,
            "ENDERECO_RESIDENCIAL": 0.85,
            "CONTA_BANCARIA": 0.90,
            "CARTAO_CREDITO": 0.95,
            "DATA_NASCIMENTO": 0.85,
            "DADO_SAUDE": 0.90,
            "DADO_BIOMETRICO": 0.90,
            "MENOR_IDENTIFICADO": 0.90,
            "IP_ADDRESS": 0.75,
            "COORDENADAS_GEO": 0.80,
            "PIX": 0.90,
            "CEP": 0.70,
            "PLACA_VEICULO": 0.85,
            "PROCESSO_SEI": 0.80,
            "PROTOCOLO_LAI": 0.80,
            "MATRICULA": 0.80,
        }
        
        if ALLOW_LIST_AVAILABLE:
            logger.info(f"✅ Allow_list carregada: {len(self.blocklist_total)} termos na blocklist")
    
    def _compilar_patterns(self) -> None:
        """Compila todos os patterns regex para performance."""
        
        # Definição de patterns: nome -> (regex, flags)
        patterns_def = {
            # === DOCUMENTOS DE IDENTIFICAÇÃO ===
            
            'CPF': (
                r'\b(\d{3}[\.\s\-]?\d{3}[\.\s\-]?\d{3}[\-\.\s]?\d{1,2})\b',
                re.IGNORECASE
            ),
            
            'CNPJ': (
                r'(\b\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[/\.\s]?\d{4}[\-\.\s]?\d{2}\b|\b\d{14}\b)',
                re.IGNORECASE
            ),
            
            'RG': (
                r'(?:RG|R\.G\.|IDENTIDADE|CARTEIRA DE IDENTIDADE)[\s:]*'
                r'(?:n[ºo°]?\s*)?'
                r'[\(\[]?[A-Z]{0,2}[\)\]]?[\s\-]*'
                r'(\d{1,2}[\.\s]?\d{3}[\.\s]?\d{3}[\-\.\s]?[\dXx]?)',
                re.IGNORECASE
            ),
            
            'RG_ORGAO': (
                r'(?:RG|R\.G\.|IDENTIDADE)[\s:]*'
                r'(?:n[ºo°]?\s*)?'
                r'(\d{5,9}[\-\.\s]?[\dXx]?)[\s\/\-]*'
                r'(?:SSP|SDS|PC|IFP|DETRAN|SESP|DIC|DGPC|IML|IGP)[\s\/\-]*[A-Z]{2}',
                re.IGNORECASE
            ),
            
            'CNH': (
                r'(?:CNH|CARTEIRA DE MOTORISTA|HABILITACAO|MINHA CNH)[\s:]*(\d{10,12})',
                re.IGNORECASE
            ),
            
            'PIS': (
                r'(?:PIS|PASEP|NIT|PIS/PASEP)[\s:]*(\d{3}[\.\s]?\d{5}[\.\s]?\d{2}[\-\.\s]?\d{1})',
                re.IGNORECASE
            ),
            
            'TITULO_ELEITOR': (
                r'(?:T[ÍI]TULO\s+(?:DE\s+)?ELEITOR|T[ÍI]TULO\s+ELEITORAL)[\s:]*'
                r'(\d{4}[\.\s]?\d{4}[\.\s]?\d{4})',
                re.IGNORECASE
            ),
            
            'CNS': (
                r'(?:CNS|CART[ÃA]O\s+SUS|CART[ÃA]O\s+NACIONAL\s+DE\s+SA[ÚU]DE)[\s:]*'
                r'([1-2789]\d{14})',
                re.IGNORECASE
            ),
            
            'PASSAPORTE': (
                r'(?:PASSAPORTE|PASSPORT|MEU PASSAPORTE)[\s:]*'
                r'(?:[ÉE]|NUMBER|N[ºO°]?)?[\s:]*'
                r'(?:BR)?[\s]?([A-Z]{2}\d{6})',
                re.IGNORECASE
            ),
            
            'CTPS': (
                r'(?:CTPS|CARTEIRA DE TRABALHO)[\s:]*(\d{7}[/\-]\d{5}[\-]?[A-Z]{2})',
                re.IGNORECASE
            ),
            
            'CERTIDAO': (
                r'\b(\d{6}[\.\s]?\d{2}[\.\s]?\d{2}[\.\s]?\d{4}[\.\s]?\d[\.\s]?'
                r'\d{5}[\.\s]?\d{3}[\.\s]?\d{7}[\-\.\s]?\d{2})\b',
                re.IGNORECASE
            ),
            
            'REGISTRO_PROFISSIONAL': (
                r'\b(CRM|OAB|CREA|CRO|CRP|CRF|COREN|CRC)[\/\-\s]*'
                r'([A-Z]{2})?[\s\/\-]*(?:n[ºo°]?\s*)?(\d{2,6}(?:[.\-]\d+)?)',
                re.IGNORECASE
            ),
            
            # === CONTATO ===
            
            'EMAIL_PESSOAL': (
                r'\b([a-zA-Z0-9._%+-]+@'
                r'(?!.*\.gov\.br)(?!.*\.org\.br)(?!.*\.edu\.br)'
                r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
                re.IGNORECASE
            ),
            
            'TELEFONE_DDI': (
                r'(\+55[\s\-]?\(?\d{2}\)?[\s\-]?9?\d{4}[\s\-]?\d{4})',
                re.IGNORECASE
            ),
            
            'TELEFONE_INTERNACIONAL': (
                r'(\+(?!55)\d{1,3}[\s\-]?\d{1,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4})',
                re.IGNORECASE
            ),
            
            'CELULAR': (
                r'(?<!\d)(?:0?(\d{2})[\s\-\)]*9[\s\-]?\d{4}[\s\-]?\d{4})(?!\d)',
                re.IGNORECASE
            ),
            
            'TELEFONE_CURTO': (
                r'(?<!\d)(9?\d{4})-(\d{4})(?!\d)',
                re.IGNORECASE
            ),
            
            'TELEFONE_FIXO': (
                r'(?<![+\d])([\(\[]?0?(\d{2})[\)\]]?[\s\-]+([2-5]\d{3})[\s\-]?\d{4})(?!\d)',
                re.IGNORECASE
            ),
            
            'TELEFONE_DDD_ESPACO': (
                r'(?<!\d)(\d{2})[\s]+(\d{4,5})[\s\-](\d{4})(?!\d)',
                re.IGNORECASE
            ),
            
            # NOVO: TELEFONE SEM DDD (ex: 91234-5678 ou 1234-5678)
            'TELEFONE_LOCAL': (
                r'(?<!\d)(9?\d{4})-(\d{4})(?!\d)',
                re.IGNORECASE
            ),
            
            # === ENDEREÇOS ===
            
            'ENDERECO_RESIDENCIAL': (
                r'(?:moro|resido|minha casa|meu endere[cç]o|minha resid[eê]ncia|endere[cç]o\s*:?)'
                r'[^\n]{0,80}?'
                r'(?:(?:rua|av|avenida|alameda|travessa|estrada|rodovia)[\s\.]+'
                r'[a-záéíóúàèìòùâêîôûãõ\s]+[\s,]+(?:n[ºo°]?[\s\.]*)?[\d]+|'
                r'(?:casa|apto?|apartamento|lote|bloco|quadra)[\s\.]*'
                r'(?:n[ºo°]?[\s\.]*)?[\d]+[a-z]?)',
                re.IGNORECASE | re.UNICODE
            ),
            
            'ENDERECO_BRASILIA': (
                r'(?:moro|resido|minha casa|meu endere[cç]o|minha resid[eê]ncia|resid[eê]ncia:?)[^\n]{0,30}?'
                r'(?:Q[INRSEMSAB]\s*\d+|SQS\s*\d+|SQN\s*\d+|SRES\s*\d+|SHIS\s*QI\s*\d+|'
                r'SHIN\s*QI\s*\d+|QNM\s*\d+|QNN\s*\d+|Conjunto\s+[A-Z]\s+Casa\s+\d+)',
                re.IGNORECASE | re.UNICODE
            ),
            
            'ENDERECO_SHIN_SHIS': (
                r'(?:mora|na)\s*(SHIN|SHIS|SHLP|SHLN)\s*QI\s*\d+\s*(?:Conjunto|Conj\.?)\s*\d+',
                re.IGNORECASE | re.UNICODE
            ),
            
            'ENDERECO_COMERCIAL_ESPECIFICO': (
                r'(?:(?:im[óo]vel|inquilin[oa]|propriet[áa]ri[oa]|loja|estabelecimento)[^\n]{0,50}?)?'
                r'(CRN|CLN|CLS|SCLN|SCRN|SCRS|SCLS)\s*\d+\s*(?:Bloco|Bl\.?)\s*[A-Z]\s*'
                r'(?:loja|sala|apt\.?|apartamento)?\s*\d+',
                re.IGNORECASE | re.UNICODE
            ),
            
            'CEP': (
                r'\b(\d{2}\.?\d{3}[\-]?\d{3})\b',
                re.IGNORECASE
            ),
            
            # === PADRÕES GDF ===
            
            'PROCESSO_SEI': (
                r'\b\d{4,5}-\d{5,8}/\d{4}(?:-\d{2})?\b',
                re.IGNORECASE
            ),
            
            'PROTOCOLO_LAI': (
                r'\bLAI-\d{5,8}/\d{4}\b',
                re.IGNORECASE
            ),
            
            'PROTOCOLO_OUV': (
                r'\bOUV-\d{5,8}/\d{4}\b',
                re.IGNORECASE
            ),
            
            'MATRICULA_SERVIDOR': (
                r'(\b\d{2}\.\d{3}-\d{1}[A-Z]?\b|\b\d{7,8}[A-Z]?\b)',
                re.IGNORECASE
            ),
            
            'OCORRENCIA_POLICIAL': (
                r'\b20\d{14,16}\b',
                re.IGNORECASE
            ),
            
            # INSCRICAO_IMOVEL: 15 dígitos isolados OU label + 6-9 dígitos
            'INSCRICAO_IMOVEL_15': (
                r'\b(\d{15})\b',
                re.IGNORECASE
            ),
            'INSCRICAO_IMOVEL_LABEL': (
                r'inscri[cç][ãa]o(?:\s*im[oó]vel)?\s*[:\-]?\s*(\d{6,9})',
                re.IGNORECASE
            ),
            
            'PLACA_VEICULO': (
                r'\b((?!ANO|SEI|REF|ART|LEI|DEC|CAP|INC|PAR|SUS|SÃO)[A-Z]{3}[\-]?\d[A-Z0-9]\d{2}|'
                r'(?!ANO|SEI|REF|ART|LEI|DEC|CAP|INC|PAR|SUS|SÃO)[A-Z]{3}[\-]?\d{4}|'
                r'[A-Z]{3}\d{1}[A-Z]{1}\d{2})\b',
                re.IGNORECASE
            ),
            
            # === FINANCEIRO ===
            
            'CONTA_BANCARIA': (
                r'(?:ag[eê]ncia|ag\.?|conta|c/?c|c\.c\.?)[\s:]*'
                r'(\d{4,5})[\s\-]*(?:\d)?[\s\-/]*(\d{5,12})[\-]?\d?',
                re.IGNORECASE
            ),
            
            'PIX_UUID': (
                r'\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-fA-F]{32})\b',
                re.IGNORECASE
            ),
            
            'CARTAO_CREDITO': (
                r'\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b',
                re.IGNORECASE
            ),
            
            'CARTAO_FINAL': (
                r'(?:cart[ãa]o|card)[^0-9]*(?:final|terminado em|[\*]+)[\s:]*(\d{4})',
                re.IGNORECASE
            ),
            
            # === OUTROS ===
            
            'DATA_NASCIMENTO': (
                r'(?:nasc|nascimento|nascido|data de nascimento|d\.?n\.?)[\s:]*'
                r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                re.IGNORECASE
            ),
            
            'IP_ADDRESS': (
                r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b',
                re.IGNORECASE
            ),
            
            'PROCESSO_CNJ': (
                r'\b(\d{7}[\-\.]\d{2}[\-\.]\d{4}[\-\.]\d[\-\.]\d{2}[\-\.]\d{4})\b',
                re.IGNORECASE
            ),
            
            'MATRICULA': (
                r'(?:matr[ií]cula|mat\.?)[\s:]*(\d{2,3}[\.\-]?\d{3}[\-\.]?[\dA-Z]?|\d{5,9}[\-\.]?[\dA-Z]?)',
                re.IGNORECASE
            ),
            
            'DADOS_BANCARIOS': (
                r'(?:'
                r'(?:ag[êe]ncia|ag\.?|conta|c/?c|c\.c\.?)[\s:]*'
                r'(\d{4,5})[\s\-]*(?:\d)?[\s\-/]*(\d{5,12})[\-]?\d?|'
                r'(?:conta)[\s:]*(\d{4,12}[\-]?[\dXx]?)[\s,]*(?:ag[êe]ncia|ag\.?)[\s:]*(\d{4})|'
                r'(?:dep[óo]sito|transferir)[^\n]{0,30}(?:ag\.?|ag[êe]ncia)[\s:]*(\d{4})[\s,]*(?:cc|conta|c/?c)[\s:]*(\d{4,12}[\-]?[\dXx]?)'
                r')',
                re.IGNORECASE
            ),
            
            # === DADOS SENSÍVEIS LGPD ===
            
            'DADO_SAUDE': (
                r'(?:'
                r'CID[\s\-]?[A-Z]\d{1,3}(?:\.\d)?|'
                r'(?:HIV|AIDS|cancer|câncer|diabetes|epilepsia|'
                r'esquizofrenia|depress[ãa]o|bipolar|transtorno)[^.]{0,30}(?:positivo|confirmado|diagn[oó]stico)|'
                r'prontu[aá]rio\s*(?:m[eé]dico)?\s*(?:n[ºo°]?\s*)?[\d/]+|'
                r'(?:diagn[oó]stico|tratamento)\s+(?:de\s+|realizado\s+de\s+)?(?:HIV|AIDS|cancer|câncer|diabetes|epilepsia)'
                r')',
                re.IGNORECASE
            ),
            
            'DADO_BIOMETRICO': (
                r'(?:'
                r'impress[ãa]o\s+digital|'
                r'foto\s*3\s*x\s*4|'
                r'reconhecimento\s+facial|'
                r'biometria\s+(?:coletada|registrada|cadastrada)'
                r')',
                re.IGNORECASE
            ),
            
            'MENOR_IDENTIFICADO': (
                r'(?:'
                r'(?:crian[çc]a|menor|alun[oa]|estudante)\s+([A-Z][a-záéíóúàâêôãõç]+(?:\s+[A-Z][a-záéíóúàâêôãõç]+)*)[\s,]+(\d{1,2})\s*anos?|'
                r'([A-Z][a-záéíóúàâêôãõç]+)[\s,]+(\d{1,2})\s*anos[\s,]+(?:estudante|alun[oa]|crian[çc]a|menor)'
                r')',
                re.IGNORECASE | re.UNICODE
            ),
            
            'COORDENADAS_GEO': (
                r'(?:'
                r'(?:lat(?:itude)?|coordenadas?)[\s:]*(-?\d{1,3}\.\d{4,7})[\s,]+'
                r'(?:lon(?:g(?:itude)?)?)?[\s:]*(-?\d{1,3}\.\d{4,7})|'
                r'(?:GPS|localiza[çc][ãa]o|posi[çc][ãa]o)[\s:]*'
                r'(-?\d{1,3}\.\d{4,7})[\s,]+(-?\d{1,3}\.\d{4,7})'
                r')',
                re.IGNORECASE
            ),
            
            'USER_AGENT': (
                r'(?:user[\-\s]?agent|navegador|browser)[\s:]*'
                r'(Mozilla/\d\.\d\s*\([^)]+\)[^\n]{0,100})',
                re.IGNORECASE
            ),
        }
        
        # Compila cada pattern
        for nome, (regex, flags) in patterns_def.items():
            try:
                self.patterns_compilados[nome] = re.compile(regex, flags)
            except re.error as e:
                logger.error(f"Erro compilando pattern {nome}: {e}")
    
    def _carregar_modelos_ner(self) -> None:
        """Carrega modelos NER (BERT, NuNER, spaCy)."""
        device = 0 if torch.cuda.is_available() and self.usar_gpu else -1
        
        # BERT Davlan (multilíngue)
        try:
            self.nlp_bert = pipeline(
                "ner",
                model="Davlan/bert-base-multilingual-cased-ner-hrl",
                aggregation_strategy="simple",
                device=device
            )
            logger.info("✅ BERT Davlan NER multilíngue carregado")
        except Exception as e:
            self.nlp_bert = None
            logger.warning(f"⚠️ BERT NER indisponível: {e}")
        
        # NuNER pt-BR (especializado português)
        try:
            self.nlp_nuner = pipeline(
                "ner",
                model="monilouise/ner_news_portuguese",
                aggregation_strategy="simple",
                device=device
            )
            logger.info("✅ NuNER pt-BR carregado")
        except Exception as e:
            self.nlp_nuner = None
            logger.warning(f"⚠️ NuNER indisponível: {e}")
        
        # spaCy (backup)
        try:
            import spacy
            self.nlp_spacy = spacy.load("pt_core_news_lg")
            logger.info("✅ spaCy pt_core_news_lg carregado")
        except Exception as e:
            self.nlp_spacy = None
            logger.warning(f"⚠️ spaCy indisponível: {e}")
    
    def _inicializar_presidio(self) -> None:
        """Inicializa o Presidio Analyzer com recognizers customizados."""
        try:
            self.presidio_analyzer = AnalyzerEngine()
            
            # Registra patterns customizados
            for nome, pattern_compilado in self.patterns_compilados.items():
                pattern = Pattern(
                    name=nome,
                    regex=pattern_compilado.pattern,
                    score=self.confianca_base.get(nome, 0.85)
                )
                recognizer = PatternRecognizer(
                    supported_entity=nome,
                    patterns=[pattern]
                )
                self.presidio_analyzer.registry.add_recognizer(recognizer)
            
            logger.info("✅ Presidio Analyzer inicializado")
        except Exception as e:
            self.presidio_analyzer = None
            logger.warning(f"⚠️ Presidio indisponível: {e}")
    
    @lru_cache(maxsize=1024)
    def _normalizar(self, texto: str) -> str:
        """Normaliza texto para comparação (com cache)."""
        return unidecode(texto).upper().strip() if texto else ""
    
    def _deve_ignorar_entidade(self, texto_entidade: str) -> bool:
        """Decide se uma entidade detectada deve ser ignorada (não é PII)."""
        if not texto_entidade or len(texto_entidade) < 3:
            return True
        
        # Ignorar nomes com caracteres corrompidos
        if '##' in texto_entidade:
            return True
        if re.search(r'[^\w\sáéíóúàèìòùâêîôûãõÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕ\-]', texto_entidade):
            return True
        
        t_norm = self._normalizar(texto_entidade)
        
        # 1. Blocklist direta
        if t_norm in self.blocklist_total:
            return True
        
        # 2. BLOCK_IF_CONTAINS
        palavras_nome = set(t_norm.split())
        for blocked in BLOCK_IF_CONTAINS:
            blocked_norm = self._normalizar(blocked)
            if blocked_norm in palavras_nome:
                return True
        
        # 3. Termos seguros (match parcial)
        if any(ts in t_norm for ts in self.termos_seguros):
            return True
        
        # 4. Gazetteer GDF
        termos_gazetteer = carregar_gazetteer_gdf()
        if t_norm in termos_gazetteer:
            return True
        for termo_gdf in termos_gazetteer:
            if termo_gdf in t_norm:
                return True
        
        # 5. Só números/símbolos
        if re.match(r'^[\d/\.\-\s]+$', texto_entidade):
            return True
        
        return False
    
    def _contexto_negativo_cpf(self, texto: str, cpf_valor: str) -> bool:
        """Verifica se CPF está em contexto que invalida (exemplo, fictício, etc)."""
        idx = texto.find(cpf_valor)
        if idx == -1:
            return False
        
        inicio = max(0, idx - 50)
        fim = min(len(texto), idx + len(cpf_valor) + 50)
        contexto = texto[inicio:fim].upper()
        
        palavras_negativas = {
            "INVALIDO", "INVÁLIDO", "FALSO", "FICTICIO", "FICTÍCIO",
            "EXEMPLO", "TESTE", "FAKE", "GENERICO", "GENÉRICO",
            "000.000.000-00", "111.111.111-11", "XXX.XXX.XXX-XX",
            "PROCESSO", "PROTOCOLO", "SEI ", "N° SEI", "Nº SEI",
            "CODIGO DE BARRAS", "CÓDIGO DE BARRAS", "COD BARRAS"
        }
        
        return any(p in contexto for p in palavras_negativas)
    
    def _calcular_fator_contexto(self, texto: str, inicio: int, fim: int, tipo: str) -> float:
        """Calcula fator multiplicador de confiança baseado no contexto."""
        janela = 60
        pre = self._normalizar(texto[max(0, inicio-janela):inicio])
        pos = self._normalizar(texto[fim:min(len(texto), fim+janela)])
        contexto_completo = pre + " " + pos
        
        fator = 1.0
        
        # === BOOSTS ===
        if re.search(r'\b(MEU|MINHA|MEUS|MINHAS)\s*:?\s*$', pre):
            fator += 0.15
        
        labels_por_tipo = {
            "CPF": [r'CPF\s*:?\s*$', r'C\.?P\.?F\.?\s*:?\s*$'],
            "EMAIL_PESSOAL": [r'E-?MAIL\s*:?\s*$', r'CORREIO\s*:?\s*$'],
            "TELEFONE": [r'TEL\.?\s*:?\s*$', r'TELEFONE\s*:?\s*$', r'CELULAR\s*:?\s*$'],
            "RG": [r'RG\s*:?\s*$', r'IDENTIDADE\s*:?\s*$'],
            "CNH": [r'CNH\s*:?\s*$', r'HABILITACAO\s*:?\s*$'],
        }
        if tipo in labels_por_tipo:
            for pattern in labels_por_tipo[tipo]:
                if re.search(pattern, pre):
                    fator += 0.10
                    break
        
        if re.search(r'\b(E|É|SAO|SÃO|FOI|FORAM)\s*:?\s*$', pre[-20:]):
            fator += 0.05
        
        if tipo == "NOME":
            for gatilho in self.gatilhos_contato:
                if gatilho in pre:
                    fator += 0.10
                    break
        
        # === PENALIDADES ===
        if re.search(r'\b(EXEMPLO|TESTE|FICTICIO|FICTÍCIO|FAKE|GENERICO|GENÉRICO)\b', contexto_completo):
            fator -= 0.25
        
        if re.search(r'\b(INVALIDO|INVÁLIDO|FALSO|ERRADO|INCORRETO)\b', contexto_completo):
            fator -= 0.30
        
        if re.search(r'\b(NAO|NÃO|NEM)\s+(E|É|ERA|FOI)\s*$', pre):
            fator -= 0.20
        
        if re.search(r'\b(DA EMPRESA|DO ORGAO|DO ÓRGÃO|INSTITUCIONAL|CORPORATIVO)\b', contexto_completo):
            fator -= 0.10
        
        numeros_proximos = len(re.findall(r'\d{4,}', contexto_completo))
        if numeros_proximos >= 4:
            fator -= 0.15
        
        return max(0.6, min(1.2, fator))
    
    def _calcular_confianca(self, tipo: str, texto: str, inicio: int, fim: int,
                            score_modelo: float = None) -> float:
        """Calcula confiança final: base * fator_contexto."""
        if score_modelo is not None:
            base = score_modelo
        else:
            base = self.confianca_base.get(tipo, 0.85)
        
        fator = self._calcular_fator_contexto(texto, inicio, fim, tipo)
        return min(1.0, base * fator)
    
    def _validar_cpf(self, cpf: str) -> bool:
        """Valida CPF com dígito verificador."""
        if self.validador and hasattr(self.validador, 'validar_cpf'):
            return self.validador.validar_cpf(cpf)
        
        # Validação básica de formato
        numeros = re.sub(r'[^\d]', '', cpf)
        if len(numeros) < 10 or len(numeros) > 11:
            return False
        if len(set(numeros)) == 1:  # Todos dígitos iguais
            return False
        return True
    
    def _validar_cnpj(self, cnpj: str) -> bool:
        """Valida CNPJ com dígito verificador."""
        if self.validador and hasattr(self.validador, 'validar_cnpj'):
            return self.validador.validar_cnpj(cnpj)
        
        numeros = re.sub(r'[^\d]', '', cnpj)
        return len(numeros) == 14 and len(set(numeros)) > 1
    
    def _detectar_regex(self, texto: str) -> List[Dict]:
        """Detecção por regex com validação de dígito verificador."""
        findings = []
        for tipo, pattern in self.patterns_compilados.items():
            for match in pattern.finditer(texto):
                valor = match.group(1) if match.lastindex else match.group()
                inicio, fim = match.start(), match.end()

                # --- PATCH: INSCRICAO_IMOVEL ---
                if tipo in ['INSCRICAO_IMOVEL_15', 'INSCRICAO_IMOVEL_LABEL']:
                    findings.append({
                        "tipo": "INSCRICAO_IMOVEL", "valor": valor,
                        "confianca": self._calcular_confianca("INSCRICAO_IMOVEL", texto, inicio, fim) if hasattr(self, '_calcular_confianca') else 0.85,
                        "peso": 4, "inicio": inicio, "fim": fim
                    })
                    continue

                # Validações específicas por tipo
                if tipo == 'CPF':
                    if self._contexto_negativo_cpf(texto, valor):
                        continue
                    if not self._validar_cpf(valor):
                        continue
                    confianca = self._calcular_confianca("CPF", texto, inicio, fim)
                    findings.append({
                        "tipo": "CPF", "valor": valor, "confianca": confianca,
                        "peso": 5, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'CNPJ':
                    if not self._validar_cnpj(valor):
                        continue
                    contexto = texto[max(0, inicio-50):fim+50].upper()
                    if any(p in contexto for p in ["MEU CNPJ", "MINHA EMPRESA", "SOU MEI"]):
                        findings.append({
                            "tipo": "CNPJ_PESSOAL", "valor": valor,
                            "confianca": self._calcular_confianca("CNPJ_PESSOAL", texto, inicio, fim),
                            "peso": 4, "inicio": inicio, "fim": fim
                        })
                    else:
                        findings.append({
                            "tipo": "CNPJ", "valor": valor,
                            "confianca": self._calcular_confianca("CNPJ", texto, inicio, fim),
                            "peso": 3, "inicio": inicio, "fim": fim
                        })

                elif tipo == 'EMAIL_PESSOAL':
                    email_lower = valor.lower()
                    if any(d in email_lower for d in ['.gov.br', '.org.br', '.edu.br']):
                        continue
                    findings.append({
                        "tipo": "EMAIL_PESSOAL", "valor": valor,
                        "confianca": self._calcular_confianca("EMAIL_PESSOAL", texto, inicio, fim),
                        "peso": 4, "inicio": inicio, "fim": fim
                    })

                elif tipo in ['CELULAR', 'TELEFONE_FIXO', 'TELEFONE_DDI', 'TELEFONE_DDD_ESPACO', 'TELEFONE_LOCAL', 'TELEFONE_INTERNACIONAL']:
                    ctx_antes = texto[max(0, inicio-80):inicio].lower()
                    ctx_depois = texto[fim:min(len(texto), fim+30)].lower()

                    termos_institucionais = [
                        'institucional', 'ramal', 'extensão', 'fale conosco', 'sac', 'atendimento'
                    ]
                    if any(term in ctx_antes or term in ctx_depois for term in termos_institucionais):
                        continue

                    findings.append({
                        "tipo": "TELEFONE", "valor": valor,
                        "confianca": self._calcular_confianca("TELEFONE", texto, inicio, fim),
                        "peso": 4, "inicio": inicio, "fim": fim
                    })

                elif tipo in ['RG', 'RG_ORGAO']:
                    findings.append({
                        "tipo": "RG", "valor": valor,
                        "confianca": self._calcular_confianca("RG", texto, inicio, fim),
                        "peso": 5, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'CNH':
                    findings.append({
                        "tipo": "CNH", "valor": valor,
                        "confianca": self._calcular_confianca("CNH", texto, inicio, fim),
                        "peso": 5, "inicio": inicio, "fim": fim
                    })

                elif tipo in ['ENDERECO_RESIDENCIAL', 'ENDERECO_BRASILIA', 'ENDERECO_SHIN_SHIS']:
                    contexto = texto[max(0, inicio-60):fim+30].upper()
                    setores_institucionais = [
                        'SECRETARIA', 'MINISTERIO', 'TRIBUNAL', 'CAMARA', 'SENADO',
                        'AUTARQUIA', 'FUNDACAO', 'EMPRESA', 'BANCO', 'HOSPITAL', 'ESCOLA'
                    ]
                    if any(s in contexto for s in setores_institucionais):
                        if 'MORO' not in contexto and 'RESIDO' not in contexto:
                            continue

                    findings.append({
                        "tipo": "ENDERECO_RESIDENCIAL", "valor": valor,
                        "confianca": self._calcular_confianca("ENDERECO_RESIDENCIAL", texto, inicio, fim),
                        "peso": 4, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'DADO_SAUDE':
                    contexto = texto[max(0, inicio-100):fim+50].upper()
                    contextos_pii = ['PACIENTE', 'MEU', 'MINHA', 'LAUDO', 'ATESTADO', 'PRONTUARIO']
                    contextos_genericos = ['ESTATISTICA', 'INFORMACOES SOBRE', 'DADOS SOBRE']

                    if any(cg in contexto for cg in contextos_genericos):
                        if not any(cp in contexto for cp in contextos_pii):
                            continue

                    findings.append({
                        "tipo": "DADO_SAUDE", "valor": valor,
                        "confianca": self._calcular_confianca("DADO_SAUDE", texto, inicio, fim),
                        "peso": 5, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'MENOR_IDENTIFICADO':
                    findings.append({
                        "tipo": "MENOR_IDENTIFICADO", "valor": valor,
                        "confianca": self._calcular_confianca("MENOR_IDENTIFICADO", texto, inicio, fim),
                        "peso": 5, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'CARTAO_CREDITO':
                    findings.append({
                        "tipo": "CARTAO_CREDITO", "valor": valor,
                        "confianca": self._calcular_confianca("CARTAO_CREDITO", texto, inicio, fim),
                        "peso": 4, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'DATA_NASCIMENTO':
                    findings.append({
                        "tipo": "DATA_NASCIMENTO", "valor": valor,
                        "confianca": self._calcular_confianca("DATA_NASCIMENTO", texto, inicio, fim),
                        "peso": 3, "inicio": inicio, "fim": fim
                    })

                elif tipo in ['PIS', 'CNS', 'TITULO_ELEITOR', 'PASSAPORTE', 'CTPS', 'CERTIDAO']:
                    findings.append({
                        "tipo": tipo, "valor": valor,
                        "confianca": self._calcular_confianca(tipo, texto, inicio, fim),
                        "peso": 5, "inicio": inicio, "fim": fim
                    })

                elif tipo in ['PROCESSO_SEI', 'PROTOCOLO_LAI', 'PROTOCOLO_OUV', 'MATRICULA_SERVIDOR']:
                    findings.append({
                        "tipo": tipo, "valor": valor,
                        "confianca": self._calcular_confianca(tipo, texto, inicio, fim),
                        "peso": 3, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'CONTA_BANCARIA':
                    findings.append({
                        "tipo": "CONTA_BANCARIA", "valor": valor,
                        "confianca": self._calcular_confianca("CONTA_BANCARIA", texto, inicio, fim),
                        "peso": 4, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'PIX_UUID':
                    findings.append({
                        "tipo": "PIX", "valor": valor,
                        "confianca": self._calcular_confianca("PIX", texto, inicio, fim),
                        "peso": 4, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'IP_ADDRESS':
                    if not any(valor.startswith(prefix) for prefix in ['127.', '0.', '255.']):
                        findings.append({
                            "tipo": "IP_ADDRESS", "valor": valor,
                            "confianca": self._calcular_confianca("IP_ADDRESS", texto, inicio, fim),
                            "peso": 2, "inicio": inicio, "fim": fim
                        })

                elif tipo == 'PLACA_VEICULO':
                    findings.append({
                        "tipo": "PLACA_VEICULO", "valor": valor,
                        "confianca": self._calcular_confianca("PLACA_VEICULO", texto, inicio, fim),
                        "peso": 3, "inicio": inicio, "fim": fim
                    })
        return findings
    
    def _extrair_nomes_gatilho(self, texto: str) -> List[Dict]:
        """Extrai nomes após gatilhos de contato (sempre PII)."""
        findings = []
        texto_upper = self._normalizar(texto)
        
        for gatilho in self.gatilhos_contato:
            if gatilho not in texto_upper:
                continue
            
            idx = texto_upper.find(gatilho) + len(gatilho)
            resto = texto[idx:idx+60].strip()
            
            if "ME CHAMO" in gatilho:
                match = re.search(r'([A-Z][a-záéíóúàèìòùâêîôûãõç]+(?:\s+[A-Z][a-záéíóúàèìòùâêîôûãõç]+)*)', resto)
                if match:
                    nome = match.group(1).strip()
                    if any(w in nome.upper() for w in ["GOSTARIA", "QUERO", "PRECISO"]):
                        continue
                    if self._deve_ignorar_entidade(nome):
                        continue
                    if len(nome) <= 3 or " " not in nome:
                        continue
                    
                    inicio = idx + match.start()
                    fim = idx + match.end()
                    confianca = min(1.0, self._calcular_confianca("NOME", texto, inicio, fim) * 1.05)
                    findings.append({
                        "tipo": "NOME", "valor": nome, "confianca": confianca,
                        "peso": 4, "inicio": inicio, "fim": fim
                    })
            else:
                match = re.search(
                    r'\b(?:o|a|do|da)?\s*([A-Z][a-záéíóúàèìòùâêîôûãõç]+(?:\s+[A-Z][a-záéíóúàèìòùâêîôûãõç]+)*)',
                    resto
                )
                if match:
                    nome = match.group(1).strip()
                    nome_upper = self._normalizar(nome)
                    
                    if nome_upper in self.cargos_autoridade:
                        continue
                    if nome_upper in self.indicadores_servidor:
                        continue
                    if len(nome) <= 3 or " " not in nome:
                        continue
                    if self._deve_ignorar_entidade(nome):
                        continue
                    
                    inicio = idx + match.start()
                    fim = idx + match.end()
                    confianca = min(1.0, self._calcular_confianca("NOME", texto, inicio, fim) * 1.05)
                    findings.append({
                        "tipo": "NOME", "valor": nome, "confianca": confianca,
                        "peso": 4, "inicio": inicio, "fim": fim
                    })
        
        return findings
    
    def _deve_ignorar_nome(self, texto: str, inicio: int) -> bool:
        """Determina se nome deve ser ignorado (imunidade funcional)."""
        pre_text = self._normalizar(texto[max(0, inicio-100):inicio])
        pos_text = self._normalizar(texto[inicio:min(len(texto), inicio+150)])
        full_context = pre_text + " " + pos_text
        
        # Gatilho de contato ANULA imunidade
        for gatilho in self.gatilhos_contato:
            if gatilho in pre_text:
                return False
        
        if "FUNCIONARIO DO MES" in full_context or "FUNCIONARIA DO MES" in full_context:
            return True
        
        titulos = {"DR", "DRA", "DOUTOR", "DOUTORA", "PROF", "PROFESSOR", "PROFESSORA"}
        instituicoes = {
            "SECRETARIA", "ADMINISTRACAO", "ADMINISTRAÇÃO", "DEPARTAMENTO",
            "DIRETORIA", "GDF", "SEEDF", "SESDF", "RESPONSAVEL", "SETOR",
            "HOSPITAL", "ESCOLA", "COORDENACAO", "COORDENAÇÃO", "REGIONAL"
        }
        
        has_titulo = any(titulo + " " in pre_text[-15:] or titulo + "." in pre_text[-15:]
                        for titulo in titulos)
        has_instituicao = any(inst in pos_text for inst in instituicoes)
        
        if has_titulo and has_instituicao:
            return True
        
        for cargo in self.cargos_autoridade:
            if re.search(rf"\b{cargo}\.?\s*$", pre_text):
                if has_instituicao:
                    return True
        
        has_servidor_context = any(ind in pre_text for ind in self.indicadores_servidor)
        has_servidor_after = any(ind in pos_text[:50] for ind in self.indicadores_servidor)
        
        if has_servidor_context or has_servidor_after:
            dados_pessoais_anuladores = {
                "TELEFONE PESSOAL", "CELULAR PESSOAL", "ENDERECO RESIDENCIAL",
                "EMAIL PESSOAL", "MEU TELEFONE", "MEU EMAIL", "MEU CPF"
            }
            if not any(cp in pos_text for cp in dados_pessoais_anuladores):
                return True
        
        return False
    
    def _detectar_ner_bert_only(self, texto: str) -> List[Dict]:
        """Detecta apenas com BERT NER."""
        findings = []
        if not self.nlp_bert:
            return findings
        
        try:
            # Trunca texto se necessário
            texto_truncado = texto[:4096] if len(texto) > 4096 else texto
            resultados = self.nlp_bert(texto_truncado)
            
            for ent in resultados:
                if ent['entity_group'] not in ['PER', 'PESSOA', 'B-PER', 'I-PER', 'PERSON']:
                    continue
                if ent['score'] < 0.75:
                    continue
                
                nome = ent['word'].strip()
                if len(nome) <= 3 or " " not in nome:
                    continue
                if self._deve_ignorar_entidade(nome):
                    continue
                if self._deve_ignorar_nome(texto, ent['start']):
                    continue
                
                inicio, fim = ent['start'], ent['end']
                score_bert = float(ent['score'])
                fator = self._calcular_fator_contexto(texto, inicio, fim, "NOME")
                confianca = min(1.0, score_bert * fator)
                
                findings.append({
                    "tipo": "NOME", "valor": nome, "confianca": confianca,
                    "peso": 4, "inicio": inicio, "fim": fim, "source": "bert"
                })
        except Exception as e:
            logger.warning(f"Erro no BERT NER: {e}")
        
        return findings
    
    def _detectar_ner_nuner_only(self, texto: str) -> List[Dict]:
        """Detecta apenas com NuNER pt-BR."""
        findings = []
        if not self.nlp_nuner:
            return findings
        
        try:
            texto_truncado = texto[:4096] if len(texto) > 4096 else texto
            resultados = self.nlp_nuner(texto_truncado)
            
            for ent in resultados:
                if ent['entity_group'] not in ['PER', 'PESSOA', 'B-PER', 'I-PER', 'PERSON']:
                    continue
                
                nome = ent['word']
                if len(nome) <= 3 or " " not in nome:
                    continue
                if self._deve_ignorar_entidade(nome):
                    continue
                if self._deve_ignorar_nome(texto, ent['start']):
                    continue
                
                inicio, fim = ent['start'], ent['end']
                findings.append({
                    "tipo": "NOME", "valor": nome, "confianca": float(ent['score']),
                    "peso": 4, "inicio": inicio, "fim": fim, "source": "nuner"
                })
        except Exception as e:
            logger.warning(f"Erro no NuNER: {e}")
        
        return findings
    
    def _detectar_ner_spacy_only(self, texto: str) -> List[Dict]:
        """Detecta apenas com spaCy NER."""
        findings = []
        if not self.nlp_spacy:
            return findings
        
        try:
            doc = self.nlp_spacy(texto)
            for ent in doc.ents:
                if ent.label_ != 'PER':
                    continue
                if len(ent.text) <= 3 or " " not in ent.text:
                    continue
                if self._deve_ignorar_entidade(ent.text):
                    continue
                if self._deve_ignorar_nome(texto, ent.start_char):
                    continue
                
                inicio, fim = ent.start_char, ent.end_char
                base = self.confianca_base.get("NOME_SPACY", 0.70)
                fator = self._calcular_fator_contexto(texto, inicio, fim, "NOME")
                confianca = min(1.0, base * fator)
                
                findings.append({
                    "tipo": "NOME", "valor": ent.text, "confianca": confianca,
                    "peso": 4, "inicio": inicio, "fim": fim, "source": "spacy"
                })
        except Exception as e:
            logger.warning(f"Erro no spaCy: {e}")
        
        return findings
    
    def _detectar_ner(self, texto: str) -> List[Dict]:
        """Detecta nomes usando todos os modelos NER disponíveis."""
        findings = []
        findings.extend(self._detectar_ner_bert_only(texto))
        findings.extend(self._detectar_ner_nuner_only(texto))
        findings.extend(self._detectar_ner_spacy_only(texto))
        return findings
    
    def _caso_ambiguo(self, findings: List[Dict], confianca: float) -> bool:
        """Determina se o caso precisa de arbitragem LLM."""
        # Sem findings = não precisa arbitrar
        if not findings:
            return False
        
        # Confiança intermediária (zona de incerteza)
        if 0.5 < confianca < 0.8:
            return True
        
        # Apenas nomes detectados (sem documentos concretos)
        tipos = {f.get('tipo') for f in findings}
        if tipos == {'NOME'}:
            return True
        
        # Muitos achados de baixa confiança
        baixa_confianca = [f for f in findings if f.get('confianca', 1.0) < 0.75]
        if len(baixa_confianca) >= 3:
            return True
        
        return False
    
    def detect(self, text: str, force_llm: bool = False) -> Tuple[bool, List[Dict], str, float]:
        """
        Detecta PII priorizando minimização de FN (recall máximo, permissivo).
        """
        if not text or not text.strip():
            return False, [], "SEGURO", 1.0

        # === ENSEMBLE DE DETECÇÃO ===
        all_findings = []
        # 1. Regex
        regex_findings = self._detectar_regex(text)
        for f in regex_findings:
            f['source'] = 'regex'
        all_findings.extend(regex_findings)
        # 2. Gatilhos
        gatilho_findings = self._extrair_nomes_gatilho(text)
        for f in gatilho_findings:
            f['source'] = 'gatilho'
        all_findings.extend(gatilho_findings)
        # 3. NER
        ner_findings = self._detectar_ner(text)
        all_findings.extend(ner_findings)

        # === VOTAÇÃO (permissiva) ===
        self._pendentes_llm = []  # Reset
        all_findings = self._aplicar_votacao(all_findings)

        # === LLM PARA RECUPERAR PENDENTES (evitar FN) ===
        if (self.use_llm_arbitration or force_llm) and self._pendentes_llm:
            try:
                for pendente in self._pendentes_llm:
                    # Pergunta ao LLM se deve incluir
                    decision, explanation = arbitrate_with_llama(
                        text,
                        [pendente],
                        contexto_extra="Este item teve baixa confiança. Confirme se é PII."
                    )
                    if decision == "PII":
                        pendente['llm_recuperado'] = True
                        pendente['llm_explanation'] = explanation
                        all_findings.append(pendente)
                        logger.info(f"[LLM] Recuperou PII: {pendente.get('tipo')}={pendente.get('valor')[:20]}")
            except Exception as e:
                # Em caso de erro, INCLUIR para evitar FN (critério 1)
                logger.warning(f"Erro no LLM, incluindo pendentes para evitar FN: {e}")
                all_findings.extend(self._pendentes_llm)
        elif self._pendentes_llm:
            # Sem LLM disponível: incluir tudo para evitar FN
            all_findings.extend(self._pendentes_llm)

        # === DEDUPLICAÇÃO ===
        final_dict = {}
        for finding in all_findings:
            key = finding.get('valor', '').lower().strip()
            peso = finding.get('peso', 0)
            if key and (key not in final_dict or peso > final_dict[key].get('peso', 0)):
                final_dict[key] = finding
        final_list = list(final_dict.values())

        # === FILTRAGEM POR THRESHOLD (permissiva) ===
        pii_relevantes = []
        for f in final_list:
            tipo = f.get('tipo')
            conf = f.get('confianca', 1.0)
            peso = f.get('peso', 1)
            # Threshold reduzido para evitar FN
            if tipo in self.THRESHOLDS_DINAMICOS:
                th = self.THRESHOLDS_DINAMICOS[tipo]
                peso_min_ajustado = max(1, th['peso_min'] - 1)
                conf_min_ajustada = th['confianca_min'] * 0.9
                if peso >= peso_min_ajustado and conf >= conf_min_ajustada:
                    pii_relevantes.append(f)
            elif peso >= 1:  # Era 2, agora 1 (mais permissivo)
                pii_relevantes.append(f)

        # === RESULTADO ===
        if not pii_relevantes:
            # Última chance: LLM analisa texto completo
            if (self.use_llm_arbitration or force_llm) and len(text) > 50:
                try:
                    decision, explanation = arbitrate_with_llama(text, [])
                    if decision == "PII":
                        return True, [{
                            "tipo": "PII_LLM",
                            "valor": "(detectado por LLM)",
                            "confianca": 0.80,
                            "llm_explanation": explanation
                        }], "MODERADO", 0.80
                except Exception as e:
                    logger.warning(f"Erro no LLM final: {e}")
            return False, [], "SEGURO", 1.0

        # Cálculo de risco
        max_peso = max(f.get('peso', 0) for f in pii_relevantes)
        max_confianca = max(f.get('confianca', 0) for f in pii_relevantes)
        risco_map = {5: "CRITICO", 4: "ALTO", 3: "MODERADO", 2: "BAIXO", 1: "BAIXO", 0: "SEGURO"}
        nivel_risco = risco_map.get(max_peso, "MODERADO")
        findings_output = [{
            "tipo": f.get("tipo"),
            "valor": f.get("valor"),
            "confianca": f.get("confianca"),
        } for f in pii_relevantes]
        return True, findings_output, nivel_risco, max_confianca
    
    def detect_extended(self, text: str) -> Dict:
        """Detecta PII com métricas de confiança extendidas."""
        if not text or not text.strip():
            return {
                "has_pii": False,
                "classificacao": "PÚBLICO",
                "risco": "SEGURO",
                "confidence": {"no_pii": 0.9999, "all_found": None, "min_entity": None},
                "sources_used": [],
                "entities": [],
                "total_entities": 0
            }
        
        sources_used = []
        if self.nlp_bert:
            sources_used.append("bert_ner")
        if self.nlp_nuner:
            sources_used.append("nuner")
        if self.nlp_spacy:
            sources_used.append("spacy")
        sources_used.append("regex")
        
        is_pii, findings, nivel_risco, conf = self.detect(text)
        
        return {
            "has_pii": is_pii,
            "classificacao": "NÃO PÚBLICO" if is_pii else "PÚBLICO",
            "risco": nivel_risco,
            "confidence": {
                "no_pii": 1.0 - conf if not is_pii else 0.0,
                "all_found": conf if is_pii else None,
                "min_entity": min((f.get('confianca', 1.0) for f in findings), default=None) if findings else None
            },
            "sources_used": sources_used,
            "entities": findings,
            "total_entities": len(findings)
        }


# === FUNÇÕES DE CONVENIÊNCIA ===

def criar_detector(
    usar_gpu: bool = True,
    use_probabilistic_confidence: bool = True,
    use_llm_arbitration: bool = False
) -> PIIDetector:
    """
    Factory function para criar detector configurado.
    
    Args:
        usar_gpu: Se deve usar GPU para modelos
        use_probabilistic_confidence: Se deve usar sistema de confiança probabilística
        use_llm_arbitration: Se deve usar Llama-70B para arbitrar casos ambíguos
    """
    return PIIDetector(
        usar_gpu=usar_gpu,
        use_probabilistic_confidence=use_probabilistic_confidence,
        use_llm_arbitration=use_llm_arbitration
    )


def detect_pii_presidio(text: str, entities: List[str] = None, language: str = 'pt') -> List[Dict]:
    """
    Detecta entidades PII usando o Presidio Analyzer.
    
    Args:
        text: Texto de entrada
        entities: Lista de entidades a buscar (opcional)
        language: Idioma (default: 'pt')
        
    Returns:
        Lista de dicts com entidade, score, início, fim
    """
    if not PRESIDIO_AVAILABLE:
        raise RuntimeError("Presidio não está instalado. Execute: pip install presidio-analyzer")
    
    analyzer = AnalyzerEngine()
    results = analyzer.analyze(text=text, entities=entities, language=language)
    
    return [
        {
            'entity': r.entity_type,
            'score': r.score,
            'start': r.start,
            'end': r.end
        }
        for r in results
    ]


# === TESTE RÁPIDO ===

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DO DETECTOR DE PII v9.5.0")
    print("=" * 60)
    
    # Cria detector (sem LLM por padrão para testes rápidos)
    detector = criar_detector(usar_gpu=False, use_llm_arbitration=False)
    
    testes = [
        "Meu CPF é 529.982.247-25 e moro na Rua das Flores, 123",
        "A Dra. Maria da Secretaria de Administração informou que...",
        "Preciso falar com o João Silva sobre o processo",
        "O servidor José Santos do DETRAN atendeu a demanda",
        "Meu telefone é +55 61 99999-8888 para contato",
        "Email: joao.silva@gmail.com",
        "Protocolo SEI 00040-00058978/2024-00 do GDF",
        "Me chamo Carlos Eduardo da Silva e preciso de ajuda",
        "O paciente tem diagnóstico de diabetes tipo 2",
    ]
    
    print()
    for texto in testes:
        is_pii, findings, risco, conf = detector.detect(texto)
        status = "🔴 PII" if is_pii else "🟢 SEGURO"
        print(f"{status} [{risco}] (conf: {conf:.2f})")
        print(f"   Texto: {texto[:70]}...")
        if findings:
            for f in findings:
                validated = "✓" if f.get('llm_validated') else ""
                print(f"   → {f['tipo']}: {f['valor']} ({f['confianca']:.2f}) {validated}")
        print()
    
    # Teste com LLM (se configurado)
    print("-" * 60)
    print("TESTE COM ÁRBITRO LLM")
    print("-" * 60)
    
    if os.getenv("HF_TOKEN"):
        detector_llm = criar_detector(usar_gpu=False, use_llm_arbitration=True)
        
        texto_ambiguo = "O cidadão mencionou que trabalha na empresa do Pedro."
        is_pii, findings, risco, conf = detector_llm.detect(texto_ambiguo)
        
        print(f"Texto: {texto_ambiguo}")
        print(f"Resultado: {'PII' if is_pii else 'Público'} (risco: {risco}, conf: {conf:.2f})")
        if findings:
            for f in findings:
                print(f"  → {f['tipo']}: {f['valor']}")
                if f.get('llm_explanation'):
                    print(f"    LLM: {f['llm_explanation'][:100]}...")
    else:
        print("⚠️ HF_TOKEN não configurado - árbitro LLM não disponível")
        print("   Configure a variável de ambiente HF_TOKEN para habilitar")