"""Módulo de detecção de Informações Pessoais Identificáveis (PII).

Versão: 9.4.3 - HACKATHON PARTICIPA-DF 2025
Abordagem: Ensemble híbrido com alta recall (estratégia OR)
Confiança: Sistema probabilístico com calibração e log-odds

Pipeline:
1. Regras determinísticas (regex + validação DV) → 70% dos PIIs
2. NER BERT Davlan (multilíngue) → nomes e entidades
3. NER NuNER (especializado pt-BR) → nomes brasileiros
4. spaCy como backup → cobertura adicional
5. Ensemble OR → qualquer detector positivo = PII
6. Cálculo probabilístico de confiança → calibração + log-odds

Correções v9.3:
- Regex de placa de veículo agora exclui padrões comuns (ANO, SEI, REF, ART, LEI)

Correções v9.4:
- Integração com allow_list.py expandida
- Melhoria na filtragem de falsos positivos de NER
- Novos termos: leis, lugares, organizações, termos técnicos

Correções v9.4.3:
- 5 níveis de risco LGPD completos: CRÍTICO(5), ALTO(4), MODERADO(3), BAIXO(2), SEGURO(0)
- Novos tipos de PII: IP_ADDRESS, COORDENADAS_GEO, USER_AGENT (peso=2)
- Telefones internacionais (+1, +351, etc.)
- Filtro peso >= 2 para incluir risco BAIXO
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import logging
from text_unidecode import unidecode

# === INTEGRAÇÃO GAZETTEER GDF ===
import json
import os
from functools import lru_cache

# Função singleton para carregar o gazetteer uma vez
@lru_cache(maxsize=1)
def carregar_gazetteer_gdf():
    caminho = os.path.join(os.path.dirname(__file__), '..', 'gazetteer_gdf.json')
    try:
        with open(caminho, encoding='utf-8') as f:
            gazetteer = json.load(f)
        # Extrai todos nomes, siglas e aliases em um set normalizado
        termos = set()
        for categoria in ['orgaos', 'programas', 'escolas', 'hospitais']:
            for item in gazetteer.get(categoria, []):
                termos.add(unidecode(item['nome']).upper().strip())
                if 'sigla' in item and item['sigla']:
                    termos.add(unidecode(item['sigla']).upper().strip())
                if 'aliases' in item:
                    for alias in item['aliases']:
                        termos.add(unidecode(alias).upper().strip())
        return termos
    except Exception as e:
        logging.warning(f"[GAZETTEER] Falha ao carregar gazetteer_gdf.json: {e}")
        return set()

# Módulo de allow_list (termos seguros que não são PII)
try:
    from .allow_list import (
        BLOCKLIST_TOTAL,
        TERMOS_SEGUROS,
        BLOCK_IF_CONTAINS,
        INDICADORES_SERVIDOR,
        CARGOS_AUTORIDADE,
        GATILHOS_CONTATO,
        CONTEXTOS_PII,
        PESOS_PII,
        CONFIANCA_BASE,
    )
    ALLOW_LIST_AVAILABLE = True
except ImportError:
    # Fallback mínimo se allow_list não estiver disponível
    BLOCKLIST_TOTAL = set()
    TERMOS_SEGUROS = set()
    BLOCK_IF_CONTAINS = []
    INDICADORES_SERVIDOR = set()
    CARGOS_AUTORIDADE = set()
    GATILHOS_CONTATO = set()
    CONTEXTOS_PII = set()
    PESOS_PII = {}
    CONFIANCA_BASE = {}
    ALLOW_LIST_AVAILABLE = False

# Módulo de confiança probabilística
try:
    from .confidence import (
        PIIConfidenceCalculator,
        get_calculator,
        DocumentConfidence as DocConf,
        PESOS_LGPD as PESOS_LGPD_CONF
    )
    CONFIDENCE_MODULE_AVAILABLE = True
except ImportError:
    CONFIDENCE_MODULE_AVAILABLE = False
    PIIConfidenceCalculator = None

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiscoLevel(Enum):
    """Níveis de risco para classificação."""
    CRITICO = 5
    ALTO = 4
    MODERADO = 3
    BAIXO = 2
    SEGURO = 0


@dataclass
class PIIFinding:
    """Estrutura para achados de PII."""
    tipo: str
    valor: str
    confianca: float
    peso: int
    inicio: int = 0
    fim: int = 0
    contexto: str = ""
    
    def __hash__(self):
        return hash((self.tipo, self.valor.lower().strip()))
    
    def __eq__(self, other):
        if not isinstance(other, PIIFinding):
            return False
        return self.valor.lower().strip() == other.valor.lower().strip()


class ValidadorDocumentos:
    """Validação de documentos brasileiros com dígito verificador."""
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Valida CPF com dígito verificador.
        
        Retorna True se o CPF é estruturalmente válido.
        CPFs com todos dígitos iguais são inválidos (exceto sequências específicas).
        """
        # Remove formatação
        numeros = re.sub(r'[^\d]', '', cpf)
        
        if len(numeros) != 11:
            return False
        
        # CPFs com todos dígitos iguais são inválidos
        if len(set(numeros)) == 1:
            return False
        
        # Calcula primeiro dígito verificador
        soma = sum(int(numeros[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        
        if int(numeros[9]) != dv1:
            return False
        
        # Calcula segundo dígito verificador
        soma = sum(int(numeros[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        
        return int(numeros[10]) == dv2
    
    @staticmethod
    def cpf_tem_formato_valido(cpf: str) -> bool:
        """Verifica se uma string tem formato de CPF (10-11 dígitos, não todos iguais).
        
        Sob a LGPD, um CPF com erro de digitação AINDA É dado pessoal porque
        pode identificar uma pessoa. Esta função verifica apenas o formato,
        não o dígito verificador.
        
        Aceita 10-11 dígitos para cobrir erros de digitação comuns onde
        um dígito foi omitido (ex: 129.180.122-6 em vez de 129.180.122-06).
        
        Args:
            cpf: String contendo possível CPF
            
        Returns:
            True se tem formato de CPF (10-11 dígitos, não trivial)
        """
        numeros = re.sub(r'[^\d]', '', cpf)
        
        # Aceita 10-11 dígitos (para cobrir erros de digitação)
        if len(numeros) < 10 or len(numeros) > 11:
            return False
        
        # Sequências triviais não são CPFs
        if len(set(numeros)) == 1:  # 111.111.111-11
            return False
            
        return True
    
    @staticmethod
    def cpf_dv_correto(cpf: str) -> bool:
        """Verifica se o dígito verificador do CPF está correto.
        
        Para CPFs com 10 dígitos (erro de digitação), retorna False
        pois não é possível validar DV, mas o CPF ainda pode ser válido
        sob a LGPD (dado que pode identificar uma pessoa).
        
        Args:
            cpf: String contendo CPF
            
        Returns:
            True se o DV está matematicamente correto, False caso contrário
        """
        numeros = re.sub(r'[^\d]', '', cpf)
        
        # CPF com 10 dígitos: DV indeterminado (falta um dígito)
        if len(numeros) != 11:
            return False  # Não consegue validar, mas ainda é PII
        
        # Calcula primeiro dígito verificador
        soma = sum(int(numeros[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        
        if int(numeros[9]) != dv1:
            return False
        
        # Calcula segundo dígito verificador
        soma = sum(int(numeros[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        
        return int(numeros[10]) == dv2
    
    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:
        """Valida CNPJ com dígito verificador."""
        numeros = re.sub(r'[^\d]', '', cnpj)
        
        if len(numeros) != 14:
            return False
        
        if len(set(numeros)) == 1:
            return False
        
        # Pesos para cálculo
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        # Primeiro dígito
        soma = sum(int(numeros[i]) * pesos1[i] for i in range(12))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        
        if int(numeros[12]) != dv1:
            return False
        
        # Segundo dígito
        soma = sum(int(numeros[i]) * pesos2[i] for i in range(13))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        
        return int(numeros[13]) == dv2
    
    @staticmethod
    def validar_pis(pis: str) -> bool:
        """Valida PIS/PASEP/NIT com dígito verificador."""
        numeros = re.sub(r'[^\d]', '', pis)
        
        if len(numeros) != 11:
            return False
        
        pesos = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(numeros[i]) * pesos[i] for i in range(10))
        resto = soma % 11
        dv = 0 if resto < 2 else 11 - resto
        
        return int(numeros[10]) == dv
    
    @staticmethod
    def validar_titulo_eleitor(titulo: str) -> bool:
        """Valida título de eleitor."""
        numeros = re.sub(r'[^\d]', '', titulo)
        
        if len(numeros) != 12:
            return False
        
        # Sequência do estado (posições 8-9)
        uf = int(numeros[8:10])
        if uf < 1 or uf > 28:
            return False
        
        return True
    
    @staticmethod
    def validar_cns(cns: str) -> bool:
        """Valida Cartão Nacional de Saúde (CNS)."""
        numeros = re.sub(r'[^\d]', '', cns)
        
        if len(numeros) != 15:
            return False
        
        # CNS definitivo começa com 1 ou 2
        # CNS provisório começa com 7, 8 ou 9
        primeiro = int(numeros[0])
        if primeiro not in [1, 2, 7, 8, 9]:
            return False
        
        # Validação do dígito verificador
        if primeiro in [1, 2]:
            # CNS definitivo
            soma = sum(int(numeros[i]) * (15 - i) for i in range(15))
            return soma % 11 == 0
        else:
            # CNS provisório
            soma = sum(int(numeros[i]) * (15 - i) for i in range(15))
            return soma % 11 == 0
        
        return True



class PIIDetector:
    """
    Detector híbrido de PII com ensemble de alta recall.
    Estratégia: Ensemble OR - qualquer detector positivo classifica como PII.
    Isso maximiza recall (não deixar escapar nenhum PII) às custas de alguns
    falsos positivos, que é a estratégia correta para LAI/LGPD.
    Confiança: Sistema probabilístico com:
    - Calibração isotônica de scores de modelos
    - Combinação via Log-Odds (Naive Bayes)
    - Validação de DV como fonte adicional
    """

    # Thresholds dinâmicos por tipo de entidade (pode ser ajustado via parâmetro futuramente)
    THRESHOLDS_DINAMICOS = {
        'PROCESSO_SEI': {'peso_min': 1, 'confianca_min': 0.5},
        'PROTOCOLO_LAI': {'peso_min': 1, 'confianca_min': 0.5},
        'PROTOCOLO_OUV': {'peso_min': 1, 'confianca_min': 0.5},
        'MATRICULA_SERVIDOR': {'peso_min': 1, 'confianca_min': 0.5},
        'INSCRICAO_IMOVEL': {'peso_min': 1, 'confianca_min': 0.5},
        # Outros tipos seguem padrão global
    }

    def __init__(self, usar_gpu: bool = True, use_probabilistic_confidence: bool = True, ensemble_weights: dict = None) -> None:
        """Inicializa o detector com todos os modelos NLP.
        
        Args:
            usar_gpu: Se deve usar GPU para modelos (default: True)
            use_probabilistic_confidence: Se deve usar sistema de confiança 
                probabilística (default: True)
            ensemble_weights: dicionário de pesos para fontes do ensemble (ex: {'bert': 1.0, 'spacy': 1.0, 'regex': 1.0})
        """
        logger.info("🏆 [v9.4.3] VERSÃO HACKATHON - ENSEMBLE 5 FONTES + CONFIANÇA PROBABILÍSTICA")
        
        self.validador = ValidadorDocumentos()
        self._inicializar_modelos(usar_gpu)
        self._inicializar_vocabularios()
        self._compilar_patterns()
        
        # Sistema de confiança probabilística
        self.use_probabilistic_confidence = use_probabilistic_confidence and CONFIDENCE_MODULE_AVAILABLE
        if self.use_probabilistic_confidence:
            self.confidence_calculator = get_calculator()
            logger.info("✅ Sistema de confiança probabilística ativado")
        else:
            self.confidence_calculator = None
            if use_probabilistic_confidence and not CONFIDENCE_MODULE_AVAILABLE:
                logger.warning("⚠️ Módulo de confiança não disponível, usando fallback")

        # Pesos customizados do ensemble
        self.ensemble_weights = ensemble_weights or {'bert': 1.0, 'spacy': 1.0, 'regex': 1.0}
    
    def _inicializar_modelos(self, usar_gpu: bool) -> None:
        """Carrega modelos NLP priorizando baixo uso de memória (pt_core_news_sm)."""
        import spacy
        from transformers import pipeline, AutoModelForTokenClassification, AutoTokenizer

        # spaCy - prioriza modelo grande, faz fallback se necessário
        try:
            self.nlp_spacy = spacy.load("pt_core_news_lg")
            logger.info("✅ spaCy pt_core_news_lg carregado")
        except OSError:
            try:
                self.nlp_spacy = spacy.load("pt_core_news_md")
                logger.warning("⚠️ Usando pt_core_news_md (fallback)")
            except OSError:
                try:
                    self.nlp_spacy = spacy.load("pt_core_news_sm")
                    logger.warning("⚠️ Usando pt_core_news_sm (último recurso)")
                except OSError:
                    self.nlp_spacy = None
                    logger.error("❌ Nenhum modelo spaCy disponível")
        
        # BERT NER - Modelo multilíngue treinado para NER
        # Suporta: PER (pessoas), ORG (organizações), LOC (locais), DATE (datas)
        # Funciona muito bem para português brasileiro
        
        # Detecta automaticamente se há GPU disponível
        import torch
        if usar_gpu and torch.cuda.is_available():
            device = 0  # GPU
            logger.info("🚀 GPU detectada, usando CUDA para modelos NER")
        else:
            device = -1  # CPU
        
        # Token Hugging Face seguro via .env
        # O token Hugging Face deve estar em os.environ['HF_TOKEN']
        try:
            # Modelo multilíngue NER - treinado em 10+ idiomas incluindo português
            # Labels: O, B-PER, I-PER, B-ORG, I-ORG, B-LOC, I-LOC, B-DATE, I-DATE
            self.nlp_bert = pipeline(
                "ner",
                model="Davlan/bert-base-multilingual-cased-ner-hrl",
                aggregation_strategy="simple",
                device=device
            )
            logger.info("✅ BERT Davlan NER multilíngue carregado (PER, ORG, LOC, DATE)")
        except Exception as e:
            self.nlp_bert = None
            logger.warning(f"⚠️ BERT NER não disponível: {e}. Usando apenas spaCy para NER.")

        # NuNER - Modelo especializado para português brasileiro
        # Melhor performance em nomes brasileiros (Maria das Graças, João de Souza)
        try:
            self.nlp_nuner = pipeline(
                "ner",
                model="monilouise/ner_news_portuguese",
                aggregation_strategy="simple",
                device=device
            )
            logger.info("✅ NuNER pt-BR carregado (especializado em português)")
        except Exception as e:
            self.nlp_nuner = None
            logger.warning(f"⚠️ NuNER não disponível: {e}. Continuando sem modelo pt-BR especializado.")
    
    def _inicializar_vocabularios(self) -> None:
        """Inicializa todos os vocabulários e listas de contexto.
        
        Todas as listas são importadas do módulo allow_list.py que é a
        ÚNICA FONTE DE VERDADE para configurações de termos.
        """
        
        # Importa listas do allow_list.py (centralizado)
        self.blocklist_total: Set[str] = BLOCKLIST_TOTAL.copy()
        self.termos_seguros: Set[str] = TERMOS_SEGUROS.copy()
        self.indicadores_servidor: Set[str] = INDICADORES_SERVIDOR.copy()
        self.cargos_autoridade: Set[str] = CARGOS_AUTORIDADE.copy()
        self.gatilhos_contato: Set[str] = GATILHOS_CONTATO.copy()
        self.contextos_pii: Set[str] = CONTEXTOS_PII.copy()
        self.pesos_pii: Dict[str, int] = PESOS_PII.copy()
        self.confianca_base: Dict[str, float] = CONFIANCA_BASE.copy()
        
        # Adiciona confiança para tipos não definidos no allow_list
        tipos_adicionais = {
            "NOME_CONTRA": 0.80,  # Padrão linguístico fraco
        }
        self.confianca_base.update(tipos_adicionais)
        
        if ALLOW_LIST_AVAILABLE:
            logger.info(f"✅ Allow_list carregada: {len(self.blocklist_total)} termos na blocklist")
    
    def _compilar_patterns(self) -> None:
        """Compila todos os patterns regex para performance."""
        
        self.patterns_compilados: Dict[str, re.Pattern] = {
            # === DOCUMENTOS DE IDENTIFICAÇÃO ===
            
            # CPF: 000.000.000-00 ou 00000000000
            # CPF: formato padrão e variações com erros de digitação
            # LGPD: dado com erro de digitação AINDA É PII pois pode identificar pessoa
            # Aceita: 123.456.789-00, 12345678900, 129.180.122-6 (10 dígitos com erro)
            'CPF': re.compile(
                r'\b(\d{3}[\.\s\-]?\d{3}[\.\s\-]?\d{3}[\-\.\s]?\d{1,2})\b',  # Aceita hífen, espaço, ponto em qualquer posição
                re.IGNORECASE
            ),
            
            # CNPJ: 00.000.000/0000-00 ou 00000000000000
            'CNPJ': re.compile(
                r'\b(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[/\.\s]?\d{4}[\-\.\s]?\d{2})\b',
                re.IGNORECASE
            ),
            
            # RG: diversos formatos estaduais (5 a 9 dígitos)
            # Formatos: RG nº 1.234.567-8, RG 123456-7 DETRAN-DF, RG: 12345678
            'RG': re.compile(
                r'(?i)(?:RG|R\.G\.|IDENTIDADE|CARTEIRA DE IDENTIDADE)[:\s]*'
                r'(?:n[ºo°]?\s*)?'  # Opcional "nº"
                r'[\(\[]?[A-Z]{0,2}[\)\]]?[\s\-]*'
                r'(\d{1,2}[\.\s]?\d{3}[\.\s]?\d{3}[\-\.\s]?[\dXx]?)',
                re.IGNORECASE
            ),
            
            # RG com órgão emissor explícito (DETRAN, SSP, etc)
            'RG_ORGAO': re.compile(
                r'(?i)(?:RG|R\.G\.|IDENTIDADE)[:\s]*'
                r'(?:n[ºo°]?\s*)?'  # Opcional "nº"
                r'(\d{5,9}[\-\.\s]?[\dXx]?)[\s\-/]*'
                r'(?:SSP|SDS|PC|IFP|DETRAN|SESP|DIC|DGPC|IML|IGP)[\s\-/]*[A-Z]{2}',
                re.IGNORECASE
            ),
            
            # CNH: 10-12 dígitos (aceita erros de digitação humana)
            # LGPD: dado pessoal mesmo com erro de digitação
            'CNH': re.compile(
                r'(?i)(?:CNH|CARTEIRA DE MOTORISTA|HABILITACAO|MINHA CNH)[:\s]*[eé]?[:\s]*'
                r'(\d{10,12})',
                re.IGNORECASE
            ),
            
            # PIS/PASEP/NIT: 000.00000.00-0 ou PIS: 123.45678.90-1
            'PIS': re.compile(
                r'(?i)(?:PIS|PASEP|NIT|PIS/PASEP)[:\s]*'
                r'(\d{3}[\.\s]?\d{5}[\.\s]?\d{2}[\-\.\s]?\d{1})',
                re.IGNORECASE
            ),
            
            # Título de Eleitor: 0000 0000 0000 (12 dígitos)
            # Formato: "Título de eleitor: 0123 4567 8901"
            'TITULO_ELEITOR': re.compile(
                r'(?i)(?:T[ÍI]TULO\s+(?:DE\s+)?ELEITOR|T[ÍI]TULO\s+ELEITORAL)[:\s]*'
                r'(\d{4}[\.\s]?\d{4}[\.\s]?\d{4})',
                re.IGNORECASE
            ),
            
            # CNS (Cartão SUS): 15 dígitos começando com 1, 2, 7, 8 ou 9
            # Com label: CNS: 123456789012345
            'CNS': re.compile(
                r'(?i)(?:CNS|CART[ÃA]O\s+SUS|CART[ÃA]O\s+NACIONAL\s+DE\s+SA[ÚU]DE)[:\s]*'
                r'([1-2789]\d{14})',
                re.IGNORECASE
            ),
            
            # Passaporte Brasileiro: AA000000, FN987654, BR654321
            # Aceita formatos com possessivo, label em inglês/português
            # "Meu passaporte é FN987654", "Passport number: BR654321"
            'PASSAPORTE': re.compile(
                r'(?i)(?:PASSAPORTE|PASSPORT|MEU PASSAPORTE)[:\s]*'
                r'(?:[ÉE]|NUMBER|N[ºO°]?)?[:\s]*'
                r'(?:BR)?[\s]?([A-Z]{2}\d{6})',
                re.IGNORECASE
            ),
            
            # CTPS: 0000000/00000-UF
            'CTPS': re.compile(
                r'(?i)(?:CTPS|CARTEIRA DE TRABALHO)[:\s]*'
                r'(\d{7}[/\-]\d{5}[\-]?[A-Z]{2})',
                re.IGNORECASE
            ),
            
            # Certidão (Nascimento, Casamento, Óbito): formato novo 32 dígitos
            'CERTIDAO': re.compile(
                r'\b(\d{6}[\.\s]?\d{2}[\.\s]?\d{2}[\.\s]?\d{4}[\.\s]?\d[\.\s]?'
                r'\d{5}[\.\s]?\d{3}[\.\s]?\d{7}[\-\.\s]?\d{2})\b',
                re.IGNORECASE
            ),
            
            # Registro profissional: CRM, OAB, CREA, etc.
            'REGISTRO_PROFISSIONAL': re.compile(
                r'(?i)\b(CRM|OAB|CREA|CRO|CRP|CRF|COREN|CRC)[/\-\s]*'
                r'([A-Z]{2})?[\s\-/]*(?:n[ºo°]?\s*)?(\d{2,6}(?:[.\-]\d+)?)',
                re.IGNORECASE
            ),
            
            # === CONTATO ===
            
            # Email pessoal (exclui gov.br e institucionais)
            'EMAIL_PESSOAL': re.compile(
                r'\b([a-zA-Z0-9._%+-]+@'
                r'(?!.*\.gov\.br)(?!.*\.org\.br)(?!.*\.edu\.br)'
                r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
                re.IGNORECASE
            ),
            
            # Telefone com DDI Brasil: +55 XX XXXXX-XXXX
            'TELEFONE_DDI': re.compile(
                r'(\+55[\s\-]?\(?\d{2}\)?[\s\-]?9?\d{4}[\s\-]?\d{4})',
                re.IGNORECASE
            ),
            
            # Telefone internacional (outros países)
            # +1 (EUA/Canadá), +351 (Portugal), +54 (Argentina), +34 (Espanha), etc.
            'TELEFONE_INTERNACIONAL': re.compile(
                r'(\+(?!55)\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4})',
                re.IGNORECASE
            ),
            
            # Celular: cobre todos formatos reais e-SIC, inclusive espaço entre o 9 e o número, sem hífen, sem espaço, DDD com/sem zero, blocos compactos
            'CELULAR': re.compile(
                r'(?<!\d)(?:0?(\d{2})[\s\-\)]*9[\s\-]?\d{4}[\s\-]?\d{4})(?!\d)',
                re.IGNORECASE
            ),

            # Telefone fixo: cobre formatos compactos, DDD com/sem zero, sem hífen/sem espaço
            'TELEFONE_FIXO': re.compile(
                r'(?<![+\d])[\(\[]?0?(\d{2})[\)\]]?[\s\-]*([2-5]\d{3})[\s\-]*\d{4}(?!\d)',
                re.IGNORECASE
            ),
            
            # Telefone com DDD separado por espaço (formato real e-SIC)
            # Ex: 89 34180-1890, 61 9 9999-8888
            'TELEFONE_DDD_ESPACO': re.compile(
                r'(?<!\d)(\d{2})[\s]+(\d{4,5})[\s\-]?(\d{4})(?!\d)',
                re.IGNORECASE
            ),
            
            # === ENDEREÇOS ===
            
            # Endereço residencial com indicadores
            'ENDERECO_RESIDENCIAL': re.compile(
                r'(?i)(?:moro|resido|minha casa|meu endere[cç]o|minha resid[eê]ncia|endere[cç]o\s*:?)'
                r'[^\n]{0,80}?'
                r'(?:(?:rua|av|avenida|alameda|travessa|estrada|rodovia)[\s\.]+'
                r'[a-záéíóúàèìòùâêîôûãõ\s]+[\s,]+(?:n[ºo°]?[\s\.]*)?[\d]+|'
                r'(?:casa|apto?|apartamento|lote|bloco|quadra)[\s\.]*'
                r'(?:n[ºo°]?[\s\.]*)?[\d]+[a-z]?)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Endereço de Brasília (QI, QR, QN, QS, etc) - com prefixo de moradia
            'ENDERECO_BRASILIA': re.compile(
                r'(?i)(?:moro|resido|minha casa|meu endere[cç]o|minha resid[eê]ncia|resid[eê]ncia:?)[^\n]{0,30}?'
                r'(?:Q[INRSEMSAB]\s*\d+|SQS\s*\d+|SQN\s*\d+|SRES\s*\d+|SHIS\s*QI\s*\d+|'
                r'SHIN\s*QI\s*\d+|QNM\s*\d+|QNN\s*\d+|Conjunto\s+[A-Z]\s+Casa\s+\d+)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Endereço SHIN/SHIS/SHLP específico (lagos, penínsulas) - muito específico, sempre PII
            'ENDERECO_SHIN_SHIS': re.compile(
                r'(?i)(?:mora|na)\s*(SHIN|SHIS|SHLP|SHLN)\s*QI\s*\d+\s*(?:Conjunto|Conj\.?)\s*\d+',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Endereço comercial específico (CRN, CLN, CLS, etc - com bloco/loja)
            # Usado quando menciona o imóvel específico do cidadão
            'ENDERECO_COMERCIAL_ESPECIFICO': re.compile(
                r'(?i)(?:(?:im[óo]vel|inquilin[oa]|propriet[áa]ri[oa]|loja|estabelecimento)[^\n]{0,50}?)?'
                r'(CRN|CLN|CLS|SCLN|SCRN|SCRS|SCLS)\s*\d+\s*(?:Bloco|Bl\.?)\s*[A-Z]\s*(?:loja|sala|apt\.?|apartamento)?\s*\d+',
                re.IGNORECASE | re.UNICODE
            ),
            
            # CEP: 00000-000 ou 00.000-000
            'CEP': re.compile(
                r'\b(\d{2}\.?\d{3}[\-]?\d{3})\b',
                re.IGNORECASE
            ),

                        # === PADRÕES GDF ===
                        # Processo SEI: 12345-1234567/2024-12
                        'PROCESSO_SEI': re.compile(
                            r'\b\d{4,5}-\d{6,8}/\d{4}(?:-\d{2})?\b',
                            re.IGNORECASE
                        ),
                        # Protocolo LAI: LAI-12345/2024 ou LAI-123456/2024
                        'PROTOCOLO_LAI': re.compile(
                            r'\bLAI-\d{5,7}/\d{4}\b',
                            re.IGNORECASE
                        ),
                        # Protocolo OUV: OUV-654321/2022 ou OUV-123456/2022
                        'PROTOCOLO_OUV': re.compile(
                            r'\bOUV-\d{5,7}/\d{4}\b',
                            re.IGNORECASE
                        ),
                        # Matrícula servidor: 98.123-3, 12345678A, 12345678, mas não 6 dígitos puros
                        'MATRICULA_SERVIDOR': re.compile(
                            r'\b\d{2}\.\d{3}-\d{1}\b|\b\d{7,8}[A-Z]?\b',
                            re.IGNORECASE
                        ),
                        # Ocorrência policial: 20 + 14 a 16 dígitos
                        'OCORRENCIA_POLICIAL': re.compile(
                            r'\b20\d{14,16}\b',
                            re.IGNORECASE
                        ),
                        # Inscrição imóvel: contexto "inscrição" (com ou sem dois pontos), 6 a 9 dígitos
                        'INSCRICAO_IMOVEL': re.compile(
                            r'(?i)inscri[cç][ãa]o\s*:?\s*\d{6,9}\b',
                            re.IGNORECASE
                        ),
            
            # Placa de veículo (Mercosul e antiga)
            # Excluímos padrões comuns que não são placas: ANO, SEI, REF, ART, LEI, DEC, etc.
            'PLACA_VEICULO': re.compile(
                r'(?<!\b(?:ANO|SEI|REF|ART|LEI|DEC|CAP|INC|PAR|SUS|SÃO)[ \-])'  # Negative lookbehind
                r'\b((?!ANO|SEI|REF|ART|LEI|DEC|CAP|INC|PAR|SUS|SÃO)[A-Z]{3}[\-]?\d[A-Z0-9]\d{2}|'  # Mercosul
                r'(?!ANO|SEI|REF|ART|LEI|DEC|CAP|INC|PAR|SUS|SÃO)[A-Z]{3}[\-]?\d{4}|'  # Antiga
                r'[A-Z]{3}\d{1}[A-Z]{1}\d{2})\b',  # Moto
                re.IGNORECASE
            ),
            
            # === FINANCEIRO ===
            
            # Conta bancária: agência e conta
            'CONTA_BANCARIA': re.compile(
                r'(?i)(?:ag[eê]ncia|ag\.?|conta|c/?c|c\.c\.?)[:\s]*'
                r'(\d{4,5})[\s\-]*(?:\d)?[\s\-/]*(\d{5,12})[\-]?\d?',
                re.IGNORECASE
            ),
            
            # Chave PIX (UUID, CPF, email, telefone já cobertos)
            'PIX_UUID': re.compile(
                r'\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-fA-F]{32})\b',
                re.IGNORECASE
            ),
            
            # Cartão de crédito/débito (16 dígitos)
            'CARTAO_CREDITO': re.compile(
                r'\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b',
                re.IGNORECASE
            ),
            
            # === OUTROS ===
            
            # Data de nascimento com contexto
            'DATA_NASCIMENTO': re.compile(
                r'(?i)(?:nasc|nascimento|nascido|data de nascimento|d\.?n\.?)[:\s]*'
                r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                re.IGNORECASE
            ),
            
            # IP Address (IPv4)
            'IP_ADDRESS': re.compile(
                r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|([0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{1,4})\b',
                re.IGNORECASE
            ),
            
            # Processo judicial CNJ: 0000000-00.0000.0.00.0000
            'PROCESSO_CNJ': re.compile(
                r'\b(\d{7}[\-\.]\d{2}[\-\.]\d{4}[\-\.]\d[\-\.]\d{2}[\-\.]\d{4})\b',
                re.IGNORECASE
            ),
            
            # === NOVOS - LGPD COMPLIANCE ===
            
            # Matrícula funcional (servidor público)
            # Formatos: 12345678, 98.123-3, mat. 1234567, 98745632D
            'MATRICULA': re.compile(
                r'(?i)(?:matr[ií]cula|mat\.?)[:\s]*(\d{2,3}[\.\-]?\d{3}[\-\.]?[\dA-Z]?|\d{5,9}[\-\.]?[\dA-Z]?)',
                re.IGNORECASE
            ),
            
            # Dados bancários - Múltiplos formatos
            # Formato 1: "Agência 0001 Conta corrente 123456-7"
            # Formato 2: "Conta: 12345-6 Ag: 1234"
            # Formato 3: "Ag 1234 CC 567890-1"
            'DADOS_BANCARIOS': re.compile(
                r'(?i)(?:'
                r'(?:ag[êe]ncia|ag\.?)[:\s]*(\d{4})[,\s]*(?:conta|cc|c/?c)[:\s]*(?:corrente\s*)?(\d{5,12}[\-]?[\dXx]?)|'
                r'(?:conta)[:\s]*(\d{4,12}[\-]?[\dXx]?)[,\s]*(?:ag[êe]ncia|ag\.?)[:\s]*(\d{4})|'
                r'(?:dep[óo]sito|transferir)[^\n]{0,30}(?:ag\.?|ag[êe]ncia)[:\s]*(\d{4})[,\s]*(?:cc|conta|c/?c)[:\s]*(\d{4,12}[\-]?[\dXx]?)'
                r')',
                re.IGNORECASE
            ),
            
            # Cartão (últimos 4 dígitos)
            'CARTAO_FINAL': re.compile(
                r'(?i)(?:cart[ãa]o|card)[^0-9]*(?:final|terminado em|[\*]+)[:\s]*(\d{4})',
                re.IGNORECASE
            ),
            
            # Dados sensíveis - Saúde (CID, diagnóstico, condições)
            'DADO_SAUDE': re.compile(
                r'(?i)(?:'
                r'CID[\s\-]?[A-Z]\d{1,3}(?:\.\d)?|'  # CID F32, CID G40.1
                r'(?:HIV|AIDS|cancer|câncer|c[aâ]ncer|diabetes|epilepsia|'
                r'esquizofrenia|depress[ãa]o|bipolar|transtorno)[^.]{0,30}(?:positivo|confirmado|diagn[oó]stico)|'
                r'prontu[aá]rio\s*(?:m[eé]dico)?\s*(?:n[ºo°]?\s*)?[\d/]+|'  # Prontuário nº 12345
                r'(?:diagn[oó]stico|tratamento)\s+(?:de\s+|realizado\s+de\s+)?(?:HIV|AIDS|cancer|câncer|c[aâ]ncer|diabetes|epilepsia)'
                r')',
                re.IGNORECASE
            ),
            
            # Dados biométricos
            'DADO_BIOMETRICO': re.compile(
                r'(?i)(?:'
                r'impress[ãa]o\s+digital|'
                r'foto\s*3\s*x\s*4|'
                r'reconhecimento\s+facial|'
                r'biometria\s+(?:coletada|registrada|cadastrada)'
                r')',
                re.IGNORECASE
            ),
            
            # Menor de idade identificado
            # Formatos: "João, 15 anos", "A aluna Maria, 10 anos", "criança José"
            'MENOR_IDENTIFICADO': re.compile(
                r'(?i)(?:'
                r'(?:crian[çc]a|menor|alun[oa]|estudante)\s+([A-Z][a-záéíóúàâêôãõç]+(?:\s+[A-Z][a-záéíóúàâêôãõç]+)*)[,\s]+(\d{1,2})\s*anos?|'
                r'([A-Z][a-záéíóúàâêôãõç]+)[,\s]+(\d{1,2})\s*anos[,\s]+(?:estudante|alun[oa]|crian[çc]a|menor)'
                r')',
                re.IGNORECASE | re.UNICODE
            ),
            
            # === DADOS DE RISCO BAIXO (peso=2) - Identificação indireta ===
            
            # Endereço IP (IPv4 e IPv6)
            # IPv4: 192.168.1.1, 10.0.0.1 (exclui localhost e ranges privados comuns)
            # IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334
            'IP_ADDRESS': re.compile(
                r'(?i)(?:IP|endere[cç]o\s*IP|IP\s*address)[:\s]*'
                r'((?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)|'
                r'(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4})',
                re.IGNORECASE
            ),
            
            # Coordenadas geográficas (latitude/longitude)
            # Formato: -15.7801, -47.9292 ou lat: -15.7801, long: -47.9292
            'COORDENADAS_GEO': re.compile(
                r'(?i)(?:'
                r'(?:lat(?:itude)?|coordenadas?)[:\s]*(-?\d{1,3}\.\d{4,7})[,\s]+'
                r'(?:lon(?:g(?:itude)?)?)?[:\s]*(-?\d{1,3}\.\d{4,7})|'
                r'(?:GPS|localiza[çc][ãa]o|posi[çc][ãa]o)[:\s]*'
                r'(-?\d{1,3}\.\d{4,7})[,\s]+(-?\d{1,3}\.\d{4,7})'
                r')',
                re.IGNORECASE
            ),
            
            # User-Agent / Identificador de dispositivo
            # Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...
            'USER_AGENT': re.compile(
                r'(?i)(?:user[\-\s]?agent|navegador|browser)[:\s]*'
                r'(Mozilla/\d\.\d\s*\([^)]+\)[^\n]{0,100}|Mobile Safari|Chrome Android|CriOS|FxiOS|Opera Mini|Edge Mobile)',
                re.IGNORECASE
            ),
        }
    
    @lru_cache(maxsize=1024)
    def _normalizar(self, texto: str) -> str:
        """Normaliza texto para comparação (com cache)."""
        return unidecode(texto).upper().strip() if texto else ""
    
    def _deve_ignorar_entidade(self, texto_entidade: str) -> bool:
        """Decide se uma entidade detectada deve ser ignorada (não é PII)."""
        if not texto_entidade or len(texto_entidade) < 3:
            return True
        # Ignorar nomes com caracteres corrompidos
        if '##' in texto_entidade or re.search(r'[^\w\sáéíóúàèìòùâêîôûãõÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕ\-]', texto_entidade):
            return True
        t_norm = self._normalizar(texto_entidade)
        # 1. Blocklist direta (match exato)
        if t_norm in self.blocklist_total:
            return True
        # 2. BLOCK_IF_CONTAINS: verifica se alguma PALAVRA bloqueada está no nome
        palavras_nome = set(t_norm.split())
        for blocked in BLOCK_IF_CONTAINS:
            blocked_norm = unidecode(blocked.upper())
            if blocked_norm in palavras_nome:
                return True
        # 3. Termos seguros (match parcial)
        if any(ts in t_norm for ts in self.termos_seguros):
            return True
        # 4. Gazetteer GDF (match exato ou parcial)
        termos_gazetteer = carregar_gazetteer_gdf()
        if t_norm in termos_gazetteer:
            logger.info(f"[GAZETTEER] Entidade '{texto_entidade}' ignorada por match exato no gazetteer GDF.")
            return True
        for termo_gdf in termos_gazetteer:
            if termo_gdf in t_norm:
                logger.info(f"[GAZETTEER] Entidade '{texto_entidade}' ignorada por match parcial no gazetteer GDF: '{termo_gdf}'")
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
        
        # Janela de contexto
        inicio = max(0, idx - 50)
        fim = min(len(texto), idx + len(cpf_valor) + 50)
        contexto = texto[inicio:fim].upper()
        
        palavras_negativas = {
            "INVALIDO", "INVÁLIDO", "FALSO", "FICTICIO", "FICTÍCIO",
            "EXEMPLO", "TESTE", "FAKE", "GENERICO", "GENÉRICO",
            "000.000.000-00", "111.111.111-11", "XXX.XXX.XXX-XX",
            # Contextos que não são CPF
            "PROCESSO", "PROTOCOLO", "SEI ", "N° SEI", "Nº SEI",
            "CODIGO DE BARRAS", "CÓDIGO DE BARRAS", "COD BARRAS"
        }
        
        return any(p in contexto for p in palavras_negativas)
    
    def _calcular_fator_contexto(self, texto: str, inicio: int, fim: int, tipo: str) -> float:
        """Calcula fator multiplicador de confiança baseado no contexto.
        
        Analisa o texto ao redor do achado para ajustar a confiança:
        - Boosts: Possessivos, labels, gatilhos de contato
        - Penalidades: Contexto de teste, negação, institucional
        
        Args:
            texto: Texto completo sendo analisado
            inicio: Posição inicial do achado
            fim: Posição final do achado
            tipo: Tipo de PII detectado
            
        Returns:
            float: Multiplicador entre 0.6 (penalidade máxima) e 1.2 (boost máximo)
        """
        janela = 60  # caracteres de contexto
        pre = self._normalizar(texto[max(0, inicio-janela):inicio])
        pos = self._normalizar(texto[fim:min(len(texto), fim+janela)])
        contexto_completo = pre + " " + pos
        
        fator = 1.0  # Neutro
        
        # === BOOSTS (aumentam confiança) ===
        
        # Possessivo imediato antes ("meu CPF", "minha identidade")
        if re.search(r'\b(MEU|MINHA|MEUS|MINHAS)\s*:?\s*$', pre):
            fator += 0.15
        
        # Label do tipo antes (ex: "CPF:", "Email:", "Tel:")
        labels_por_tipo = {
            "CPF": [r'CPF\s*:?\s*$', r'C\.?P\.?F\.?\s*:?\s*$'],
            "EMAIL_PESSOAL": [r'E-?MAIL\s*:?\s*$', r'CORREIO\s*:?\s*$'],
            "TELEFONE": [r'TEL\.?\s*:?\s*$', r'TELEFONE\s*:?\s*$', r'CELULAR\s*:?\s*$', r'FONE\s*:?\s*$'],
            "RG": [r'RG\s*:?\s*$', r'IDENTIDADE\s*:?\s*$'],
            "CNH": [r'CNH\s*:?\s*$', r'HABILITACAO\s*:?\s*$'],
            "PIS": [r'PIS\s*:?\s*$', r'NIT\s*:?\s*$'],
            "PASSAPORTE": [r'PASSAPORTE\s*:?\s*$'],
            "CONTA_BANCARIA": [r'CONTA\s*:?\s*$', r'AGENCIA\s*:?\s*$'],
        }
        if tipo in labels_por_tipo:
            for pattern in labels_por_tipo[tipo]:
                if re.search(pattern, pre):
                    fator += 0.10
                    break
        
        # Verbo declarativo antes ("é", "são", "foi")
        if re.search(r'\b(E|É|SAO|SÃO|FOI|FORAM|SERA|SERÁ)\s*:?\s*$', pre[-20:]):
            fator += 0.05
        
        # Gatilho de contato pessoal antes (para NOME)
        if tipo == "NOME":
            for gatilho in self.gatilhos_contato:
                if gatilho in pre:
                    fator += 0.10
                    break
        
        # === PENALIDADES (reduzem confiança) ===
        
        # Contexto de teste/exemplo
        if re.search(r'\b(EXEMPLO|TESTE|FICTICIO|FICTÍCIO|FAKE|GENERICO|GENÉRICO|MODELO)\b', contexto_completo):
            fator -= 0.25
        
        # Declarado inválido/falso
        if re.search(r'\b(INVALIDO|INVÁLIDO|FALSO|ERRADO|INCORRETO)\b', contexto_completo):
            fator -= 0.30
        
        # Negação antes ("não é meu CPF")
        if re.search(r'\b(NAO|NÃO|NEM)\s+(E|É|ERA|FOI|SAO|SÃO)\s*$', pre):
            fator -= 0.20
        
        # Contexto institucional (menos provável ser pessoal)
        if re.search(r'\b(DA EMPRESA|DO ORGAO|DO ÓRGÃO|INSTITUCIONAL|CORPORATIVO|DA SECRETARIA)\b', contexto_completo):
            fator -= 0.10
        
        # Muitos números próximos (pode ser tabela/lista, não PII isolado)
        numeros_proximos = len(re.findall(r'\d{4,}', contexto_completo))
        if numeros_proximos >= 4:
            fator -= 0.15
        
        # Clamp entre 0.6 e 1.2
        return max(0.6, min(1.2, fator))
    
    def _calcular_confianca(self, tipo: str, texto: str, inicio: int, fim: int, 
                            score_modelo: float = None) -> float:
        """Calcula confiança final: base * fator_contexto.
        
        Args:
            tipo: Tipo de PII
            texto: Texto completo
            inicio: Posição inicial
            fim: Posição final
            score_modelo: Score do modelo NER (se aplicável)
            
        Returns:
            float: Confiança final entre 0.0 e 1.0
        """
        # Base de confiança
        if score_modelo is not None:
            base = score_modelo  # BERT retorna seu próprio score
        else:
            base = self.confianca_base.get(tipo, 0.85)
        
        # Fator de contexto
        fator = self._calcular_fator_contexto(texto, inicio, fim, tipo)
        
        # Confiança final (capped em 1.0)
        return min(1.0, base * fator)
    
    def _detectar_regex(self, texto: str) -> List[PIIFinding]:
        """Detecção por regex com validação de dígito verificador e confiança composta."""
        findings = []
        
        for tipo, pattern in self.patterns_compilados.items():
            for match in pattern.finditer(texto):
                valor = match.group(1) if match.lastindex else match.group()
                inicio, fim = match.start(), match.end()
                
                # Validação específica por tipo
                if tipo == 'CPF':
                    if self._contexto_negativo_cpf(texto, valor):
                        continue
                    
                    # LGPD: CPF com erro de digitação AINDA É dado pessoal
                    # Verifica formato primeiro, depois ajusta confiança pelo DV
                    if not self.validador.cpf_tem_formato_valido(valor):
                        continue
                    
                    # Calcula confiança base
                    confianca = self._calcular_confianca("CPF", texto, inicio, fim)
                    
                    # Se DV não bate, pode ser erro de digitação - reduz confiança mas não descarta
                    if not self.validador.cpf_dv_correto(valor):
                        confianca *= 0.85  # Reduz 15% mas mantém como PII
                    
                    findings.append(PIIFinding(
                        tipo="CPF", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'CNPJ':
                    if not self.validador.validar_cnpj(valor):
                        continue
                    # Só marca se tiver contexto de pessoa física (MEI)
                    contexto = texto[max(0, inicio-50):fim+50].upper()
                    if any(p in contexto for p in ["MEU CNPJ", "MINHA EMPRESA", "SOU MEI", "MEI"]):
                        confianca = self._calcular_confianca("CNPJ_PESSOAL", texto, inicio, fim)
                        findings.append(PIIFinding(
                            tipo="CNPJ_PESSOAL", valor=valor, confianca=confianca,
                            peso=4, inicio=inicio, fim=fim
                        ))
                
                elif tipo == 'PIS':
                    # LGPD: PIS com erro de DV AINDA É dado pessoal
                    # Remove validação estrita de DV para ser mais robusto
                    confianca = self._calcular_confianca("PIS", texto, inicio, fim)
                    # Reduz confiança se DV não bater
                    if not self.validador.validar_pis(valor):
                        confianca *= 0.85
                    findings.append(PIIFinding(
                        tipo="PIS", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'CNS':
                    # LGPD: CNS com erro de DV AINDA É dado pessoal
                    confianca = self._calcular_confianca("CNS", texto, inicio, fim)
                    # Reduz confiança se DV não bater
                    if not self.validador.validar_cns(valor):
                        confianca *= 0.85
                    findings.append(PIIFinding(
                        tipo="CNS", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'EMAIL_PESSOAL':
                    email_lower = valor.lower()
                    if any(d in email_lower for d in ['.gov.br', '.org.br', '.edu.br', 'empresa-df']):
                        continue
                    confianca = self._calcular_confianca("EMAIL_PESSOAL", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="EMAIL_PESSOAL", valor=valor, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
                
                elif tipo in ['CELULAR', 'TELEFONE_FIXO', 'TELEFONE_DDI', 'TELEFONE_DDD_ESPACO', 'TELEFONE_INTERNACIONAL']:
                    # Verificar contexto institucional
                    ctx_antes = texto[max(0, inicio-80):inicio].lower()
                    ctx_depois = texto[fim:min(len(texto), fim+30)].lower()
                    
                    # Filtrar telefones institucionais
                    termos_institucionais = [
                        'institucional', 'fixo institucional', 'telefone institucional',
                        'celular institucional', 'para contato:', 'contato:',
                        'ramal', 'extensão', 'fale conosco', 'sac ', 'atendimento'
                    ]
                    
                    is_institucional = any(term in ctx_antes or term in ctx_depois 
                                          for term in termos_institucionais)
                    
                    # Também filtrar se for telefone fixo de prefixos conhecidos de órgãos públicos
                    if tipo == 'TELEFONE_FIXO':
                        # Prefixos comuns de órgãos do GDF: 3105, 3961, 3325, etc
                        if valor and any(prefix in valor for prefix in ['3105', '3961', '3325', '3429', '3340']):
                            if 'institucional' in ctx_antes or 'ramal' in ctx_depois:
                                continue
                    
                    if is_institucional:
                        continue
                    
                    # Telefone internacional tem tipo específico
                    tipo_final = "TELEFONE_INTERNACIONAL" if tipo == 'TELEFONE_INTERNACIONAL' else "TELEFONE"
                    confianca = self._calcular_confianca(tipo_final, texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo=tipo_final, valor=valor, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'RG':
                    confianca = self._calcular_confianca("RG", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="RG", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'RG_ORGAO':
                    confianca = self._calcular_confianca("RG", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="RG", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'CNH':
                    confianca = self._calcular_confianca("CNH", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="CNH", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'PASSAPORTE':
                    # Filtrar passaportes fictícios (AA000000, BR000000, etc)
                    numeros = re.sub(r'[^\d]', '', valor)
                    if numeros and len(set(numeros)) == 1:  # Todos dígitos iguais
                        continue
                    confianca = self._calcular_confianca("PASSAPORTE", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="PASSAPORTE", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'ENDERECO_RESIDENCIAL':
                    # Filtrar endereços institucionais (Secretarias, Ministérios, etc)
                    contexto = texto[max(0, inicio-60):fim+30].upper()
                    setores_institucionais = [
                        'SECRETARIA', 'MINISTERIO', 'MINISTÉRIO', 'TRIBUNAL',
                        'CAMARA', 'CÂMARA', 'SENADO', 'ASSEMBLEIA',
                        'AUTARQUIA', 'FUNDACAO', 'FUNDAÇÃO', 'EMPRESA',
                        'BANCO', 'HOSPITAL', 'UBS', 'UPA', 'ESCOLA', 'CEF ', 'CEM '
                    ]
                    # SBS, SCS, SCN, SAS, SES, SGN são setores comerciais/institucionais de Brasília
                    if any(s in contexto for s in setores_institucionais):
                        continue
                    if re.search(r'\b(SBS|SCS|SCN|SAS|SES|SGN)\b', contexto):
                        if 'MORO' not in contexto and 'RESIDO' not in contexto and 'MINHA' not in contexto:
                            continue
                    confianca = self._calcular_confianca("ENDERECO_RESIDENCIAL", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="ENDERECO_RESIDENCIAL", valor=valor, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'ENDERECO_BRASILIA':
                    confianca = self._calcular_confianca("ENDERECO_RESIDENCIAL", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="ENDERECO_RESIDENCIAL", valor=valor, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'ENDERECO_SHIN_SHIS':
                    # Endereço SHIN/SHIS/SHLP - áreas nobres do DF, sempre específico
                    confianca = self._calcular_confianca("ENDERECO_RESIDENCIAL", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="ENDERECO_RESIDENCIAL", valor=valor, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'ENDERECO_COMERCIAL_ESPECIFICO':
                    # Endereço comercial onde pessoa física é proprietária/inquilina
                    confianca = self._calcular_confianca("ENDERECO_RESIDENCIAL", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="ENDERECO_RESIDENCIAL", valor=valor, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'DADOS_BANCARIOS':
                    confianca = self._calcular_confianca("CONTA_BANCARIA", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="CONTA_BANCARIA", valor=valor, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'PLACA_VEICULO':
                    confianca = self._calcular_confianca("PLACA_VEICULO", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="PLACA_VEICULO", valor=valor, confianca=confianca,
                        peso=3, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'CONTA_BANCARIA':
                    confianca = self._calcular_confianca("CONTA_BANCARIA", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="CONTA_BANCARIA", valor=valor, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'PIX_UUID':
                    confianca = self._calcular_confianca("PIX", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="PIX", valor=valor, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'CARTAO_CREDITO':
                    confianca = self._calcular_confianca("CARTAO_CREDITO", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="CARTAO_CREDITO", valor=valor, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'DATA_NASCIMENTO':
                    confianca = self._calcular_confianca("DATA_NASCIMENTO", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="DATA_NASCIMENTO", valor=valor, confianca=confianca,
                        peso=3, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'TITULO_ELEITOR':
                    # LGPD: Título com erro de DV AINDA É dado pessoal
                    confianca = self._calcular_confianca("TITULO_ELEITOR", texto, inicio, fim)
                    # Reduz confiança se DV não bater
                    if not self.validador.validar_titulo_eleitor(valor):
                        confianca *= 0.85
                    findings.append(PIIFinding(
                        tipo="TITULO_ELEITOR", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'CTPS':
                    confianca = self._calcular_confianca("CTPS", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="CTPS", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'CERTIDAO':
                    confianca = self._calcular_confianca("CERTIDAO", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="CERTIDAO", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'REGISTRO_PROFISSIONAL':
                    confianca = self._calcular_confianca("REGISTRO_PROFISSIONAL", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="REGISTRO_PROFISSIONAL", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'CEP':
                    # CEP só é PII se estiver em contexto de endereço pessoal
                    contexto = texto[max(0, inicio-50):fim+50].upper()
                    if any(p in contexto for p in ["MORO", "RESIDO", "MINHA CASA", "MEU ENDERECO"]):
                        confianca = self._calcular_confianca("CEP", texto, inicio, fim)
                        findings.append(PIIFinding(
                            tipo="CEP", valor=valor, confianca=confianca,
                            peso=3, inicio=inicio, fim=fim
                        ))
                
                elif tipo == 'PROCESSO_CNJ':
                    confianca = self._calcular_confianca("PROCESSO_CNJ", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="PROCESSO_CNJ", valor=valor, confianca=confianca,
                        peso=3, inicio=inicio, fim=fim
                    ))
                
                # === NOVOS TIPOS - LGPD COMPLIANCE ===
                
                elif tipo == 'MATRICULA':
                    confianca = self._calcular_confianca("MATRICULA", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="MATRICULA", valor=valor, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'CARTAO_FINAL':
                    confianca = self._calcular_confianca("CARTAO_CREDITO", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="CARTAO_CREDITO", valor=valor, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
                
                elif tipo == 'DADO_SAUDE':
                    # Verificar se há contexto de pessoa específica (não genérico)
                    contexto = texto[max(0, inicio-100):fim+50].upper()
                    
                    # Contextos que indicam dado de saúde de pessoa específica
                    contextos_pii = [
                        'PACIENTE', 'MEU', 'MINHA', 'MEUS', 'MINHAS',
                        'DO SERVIDOR', 'DA SERVIDORA', 'DO CIDADAO', 'DA CIDADA',
                        'DO ALUNO', 'DA ALUNA', 'DO ESTUDANTE', 'DA ESTUDANTE',
                        'LAUDO', 'ATESTADO', 'PRONTUARIO'
                    ]
                    
                    # Contextos genéricos que NÃO são PII
                    contextos_genericos = [
                        'PERFIL', 'ESTATISTICA', 'ESTATISTICAS', 'INFORMACOES SOBRE',
                        'DADOS SOBRE', 'APOSENTADO', 'ISENCAO', 'ISENÇÃO',
                        'BENEFICIO', 'SOLICITACAO DE', 'SOLICITO INFORMACOES'
                    ]
                    
                    # Se for contexto genérico, não é PII
                    if any(cg in contexto for cg in contextos_genericos):
                        if not any(cp in contexto for cp in contextos_pii):
                            continue
                    
                    confianca = self._calcular_confianca("DADO_SAUDE", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="DADO_SAUDE", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim  # Peso alto - dado sensível LGPD
                    ))
                
                elif tipo == 'DADO_BIOMETRICO':
                    confianca = self._calcular_confianca("DADO_BIOMETRICO", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="DADO_BIOMETRICO", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim  # Peso alto - dado sensível LGPD
                    ))
                
                elif tipo == 'MENOR_IDENTIFICADO':
                    confianca = self._calcular_confianca("MENOR_IDENTIFICADO", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="MENOR_IDENTIFICADO", valor=valor, confianca=confianca,
                        peso=5, inicio=inicio, fim=fim  # Peso alto - menor é dado sensível
                    ))
                
                # === NOVOS TIPOS - RISCO BAIXO (peso=2) ===
                
                elif tipo == 'IP_ADDRESS':
                    # Filtrar IPs locais/privados que não identificam pessoa
                    if not any(valor.startswith(prefix) for prefix in ['127.', '0.', '255.']):
                        confianca = self._calcular_confianca("IP_ADDRESS", texto, inicio, fim)
                        findings.append(PIIFinding(
                            tipo="IP_ADDRESS", valor=valor, confianca=confianca,
                            peso=2, inicio=inicio, fim=fim  # Baixo - identificação indireta
                        ))
                
                elif tipo == 'COORDENADAS_GEO':
                    confianca = self._calcular_confianca("COORDENADAS_GEO", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="COORDENADAS_GEO", valor=valor, confianca=confianca,
                        peso=2, inicio=inicio, fim=fim  # Baixo - localização aproximada
                    ))
                
                elif tipo == 'USER_AGENT':
                    confianca = self._calcular_confianca("USER_AGENT", texto, inicio, fim)
                    findings.append(PIIFinding(
                        tipo="USER_AGENT", valor=valor, confianca=confianca,
                        peso=2, inicio=inicio, fim=fim  # Baixo - identificador técnico
                    ))
        
        return findings
    
    def _extrair_nomes_gatilho(self, texto: str) -> List[PIIFinding]:
        """Extrai nomes após gatilhos de contato (sempre PII) com confiança composta."""
        findings = []
        texto_upper = self._normalizar(texto)
        
        for gatilho in self.gatilhos_contato:
            if gatilho not in texto_upper:
                continue
            
            idx = texto_upper.find(gatilho) + len(gatilho)
            resto = texto[idx:idx+60].strip()
            
            # Melhorar parsing após "Me chamo" para evitar erro "Braga Gostaria"
            if "ME CHAMO" in gatilho:
                # Aceita apenas nomes com pelo menos 2 palavras e nenhuma palavra do tipo "GOSTARIA", "QUERO", "PRECISO"
                match = re.search(r'([A-Z][a-záéíóúàèìòùâêîôûãõ]+(?:\s+[A-Z][a-záéíóúàèìòùâêîôûãõ]+)+)', resto)
                if match:
                    nome = match.group(1).strip()
                    if any(w in nome.upper() for w in ["GOSTARIA", "QUERO", "PRECISO"]):
                        continue
                    if self._deve_ignorar_entidade(nome):
                        continue
                    inicio = idx + match.start()
                    fim = idx + match.end()
                    confianca = self._calcular_confianca("NOME", texto, inicio, fim)
                    confianca = min(1.0, confianca * 1.05)
                    findings.append(PIIFinding(
                        tipo="NOME", valor=nome, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
            else:
                match = re.search(
                    r'\b(?:o|a|do|da)?\s*([A-Z][a-záéíóúàèìòùâêîôûãõ]+(?:\s+[A-Z][a-záéíóúàèìòùâêîôûãõ]+)*)',
                    resto
                )
                if match:
                    nome = match.group(1).strip()
                    nome_upper = self._normalizar(nome)
                    if nome_upper in self.cargos_autoridade:
                        continue
                    if nome_upper in self.indicadores_servidor:
                        continue
                    if len(nome) <= 3:
                        continue
                    if " " not in nome:
                        continue
                    if self._deve_ignorar_entidade(nome):
                        continue
                    inicio = idx + match.start()
                    fim = idx + match.end()
                    confianca = self._calcular_confianca("NOME", texto, inicio, fim)
                    confianca = min(1.0, confianca * 1.05)
                    findings.append(PIIFinding(
                        tipo="NOME", valor=nome, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
        
        # Nomes após "contra" (reclamação contra Pedro)
        if "CONTRA" in texto_upper:
            idx = texto_upper.find("CONTRA") + 6
            resto = texto[idx:idx+50].strip().strip(".,;:'\"-")
            match = re.search(r"^([A-Z][a-záéíóúàèìòùâêîôûãõ]+)", resto)
            if match:
                nome = match.group(1).strip()
                if len(nome) <= 3:
                    pass  # Skip
                elif " " not in nome:
                    pass  # Precisa ter nome + sobrenome
                elif self._deve_ignorar_entidade(nome):
                    pass  # Na blocklist
                else:
                    inicio = idx
                    fim = idx + len(nome)
                    # Base menor para "contra" (0.80)
                    base = self.confianca_base.get("NOME_CONTRA", 0.80)
                    fator = self._calcular_fator_contexto(texto, inicio, fim, "NOME")
                    confianca = min(1.0, base * fator)
                    
                    findings.append(PIIFinding(
                        tipo="NOME", valor=nome, confianca=confianca,
                        peso=4, inicio=inicio, fim=fim
                    ))
        
        # Nomes após "identificado como" (mesmo nome único é PII nesse contexto)
        # Permite palavras intermediárias como "apenas", "somente", etc.
        padroes_identificacao = [
            r'IDENTIFICAD[OA](?:\s+(?:APENAS|SOMENTE|SO))?\s+COMO',
            r'CONHECID[OA](?:\s+(?:APENAS|SOMENTE|SO))?\s+COMO',
            r'CHAMAD[OA]\s+(?:DE|POR)',
            r'NOME\s+(?:DE|E)'
        ]
        for padrao in padroes_identificacao:
            match_gatilho = re.search(padrao, texto_upper)
            if not match_gatilho:
                continue
            
            idx = match_gatilho.end()
            resto = texto[idx:idx+40].strip()
            
            # Captura nome (pode ser único)
            match = re.search(r'^([A-Z][a-záéíóúàèìòùâêîôûãõ]+)', resto)
            if match:
                nome = match.group(1).strip()
                
                # Filtros básicos
                if len(nome) <= 2:
                    continue
                if self._deve_ignorar_entidade(nome):
                    continue
                
                inicio = idx + match.start()
                fim = idx + match.end()
                
                findings.append(PIIFinding(
                    tipo="NOME", valor=nome, confianca=0.82,
                    peso=4, inicio=inicio, fim=fim
                ))
        
        return findings
    
    def _deve_ignorar_nome(self, texto: str, inicio: int) -> bool:
        """Determina se nome deve ser ignorado (imunidade funcional)."""
        # Contexto antes do nome (últimos 100 chars)
        pre_text = self._normalizar(texto[max(0, inicio-100):inicio])
        # Contexto após o nome (próximos 150 chars para capturar instituições)
        pos_text = self._normalizar(texto[inicio:min(len(texto), inicio+150)])
        # Contexto total
        full_context = pre_text + " " + pos_text
        
        # Gatilho de contato ANULA imunidade
        for gatilho in self.gatilhos_contato:
            if gatilho in pre_text:
                return False
        
        # "Funcionário do mês" = imune (contexto de elogio)
        if "FUNCIONARIO DO MES" in full_context or "FUNCIONARIA DO MES" in full_context:
            return True
        
        # Título + nome + instituição = servidor público, IMUNE
        titulos = {"DR", "DRA", "DOUTOR", "DOUTORA", "PROF", "PROFESSOR", "PROFESSORA"}
        instituicoes = {
            "SECRETARIA", "ADMINISTRACAO", "ADMINISTRAÇÃO", "DEPARTAMENTO", 
            "DIRETORIA", "GDF", "SEEDF", "SESDF", "RESPONSAVEL", "SETOR",
            "HOSPITAL", "ESCOLA", "COORDENACAO", "COORDENAÇÃO", "REGIONAL",
            "GERENCIA", "GERÊNCIA", "GABINETE", "ASSESSORIA", "MINISTÉRIO"
        }
        
        # Verifica se há título imediatamente antes do nome
        has_titulo = any(titulo + " " in pre_text[-15:] or titulo + "." in pre_text[-15:] 
                         for titulo in titulos)
        
        # Verifica se há instituição no contexto
        has_instituicao = any(inst in pos_text for inst in instituicoes)
        
        # Título + Instituição = IMUNE (funcionário público)
        if has_titulo and has_instituicao:
            return True
        
        # Cargo + instituição = imune (formato "Encaminhar para Dr. X da Secretaria")
        for cargo in self.cargos_autoridade:
            if re.search(rf"\b{cargo}\.?\s*$", pre_text):
                if has_instituicao:
                    return True
        
        # Servidor em contexto funcional = imune
        # Mas APENAS se não houver gatilho de contato após
        has_servidor_context = any(ind in pre_text for ind in self.indicadores_servidor)
        has_servidor_after = any(ind in pos_text[:50] for ind in self.indicadores_servidor)
        
        if has_servidor_context or has_servidor_after:
            # Verifica se não há menção de dados pessoais após (anula imunidade)
            dados_pessoais_anuladores = {
                "TELEFONE PESSOAL", "CELULAR PESSOAL", "ENDERECO RESIDENCIAL", 
                "EMAIL PESSOAL", "MEU TELEFONE", "MEU EMAIL", "MEU CPF", "SEU CPF",
                "MEU RG", "SEU RG", "INFORMOU SEU", "INFORMOU MEU", "MEU ENDERECO",
                "MINHA MATRICULA", "MEU NUMERO", "MEU CONTATO", "SEU CONTATO"
            }
            if not any(cp in pos_text for cp in dados_pessoais_anuladores):
                return True
        
        return False
    
    def _detectar_ner(self, texto: str) -> List[PIIFinding]:
        """Detecção de nomes usando modelos NER (BERT e spaCy) com confiança composta."""
        findings = []
        threshold = 0.75
        
        # BERT NER (primário)
        if self.nlp_bert:
            try:
                entidades = self.nlp_bert(texto)
                for ent in entidades:
                    # Aceita PER (pessoa) do modelo
                    if ent['entity_group'] in ['PER', 'PESSOA', 'B-PER', 'I-PER']:
                        if ent['score'] < threshold:
                            continue
                        
                        palavra = ent['word'].strip()
                        
                        # Filtros de qualidade
                        if len(palavra) <= 3:
                            continue
                        if " " not in palavra:  # Precisa ter nome + sobrenome
                            continue
                        if self._deve_ignorar_entidade(palavra):
                            continue
                        if self._deve_ignorar_nome(texto, ent['start']):
                            continue
                        
                        inicio, fim = ent['start'], ent['end']
                        # BERT: usa score do modelo como base, aplica fator de contexto
                        score_bert = float(ent['score'])
                        fator = self._calcular_fator_contexto(texto, inicio, fim, "NOME")
                        confianca = min(1.0, score_bert * fator)
                        
                        findings.append(PIIFinding(
                            tipo="NOME", valor=palavra,
                            confianca=confianca, peso=4,
                            inicio=inicio, fim=fim
                        ))
            except Exception as e:
                logger.warning(f"Erro no BERT NER: {e}")
        
        # spaCy NER (complementar)
        if self.nlp_spacy:
            try:
                doc = self.nlp_spacy(texto)
                for ent in doc.ents:
                    if ent.label_ != 'PER':
                        continue
                    
                    # Filtros
                    if len(ent.text) <= 3:
                        continue
                    if " " not in ent.text:
                        continue
                    if self._deve_ignorar_entidade(ent.text):
                        continue
                    if self._deve_ignorar_nome(texto, ent.start_char):
                        continue
                    
                    # Evita duplicatas com BERT
                    if not any(f.valor.lower() == ent.text.lower() for f in findings):
                        inicio, fim = ent.start_char, ent.end_char
                        # spaCy: usa base fixa (0.70), aplica fator de contexto
                        base = self.confianca_base.get("NOME_SPACY", 0.70)
                        fator = self._calcular_fator_contexto(texto, inicio, fim, "NOME")
                        confianca = min(1.0, base * fator)
                        
                        findings.append(PIIFinding(
                            tipo="NOME", valor=ent.text,
                            confianca=confianca, peso=4,
                            inicio=inicio, fim=fim
                        ))
            except Exception as e:
                logger.warning(f"Erro no spaCy: {e}")
        
        return findings
    
    def detect(self, text: str) -> Tuple[bool, List[Dict], str, float]:
        """Detecta PII no texto usando ensemble de alta recall + confiança probabilística.
        
        Estratégia: OR - qualquer detector positivo = PII
        Isso maximiza recall para conformidade LAI/LGPD.
        
        Confiança: Usa sistema probabilístico com calibração isotônica e 
        combinação via Log-Odds quando disponível.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Tuple contendo:
            - is_pii (bool): True se contém PII
            - findings (List[Dict]): Lista de PIIs encontrados
            - nivel_risco (str): CRITICO, ALTO, MODERADO, BAIXO ou SEGURO
            - confianca (float): Score de confiança 0-1
        """
        if not text or not text.strip():
            return False, [], "SEGURO", 1.0
        
        # === USA SISTEMA PROBABILÍSTICO SE DISPONÍVEL ===
        if self.use_probabilistic_confidence and self.confidence_calculator:
            return self._detect_with_probabilistic_confidence(text)
        
        # === FALLBACK: SISTEMA LEGADO ===
        return self._detect_legacy(text)
    
    def _detect_with_probabilistic_confidence(self, text: str) -> Tuple[bool, List[Dict], str, float]:
        """Detecção com sistema de confiança probabilística.
        
        Usa calibração isotônica + combinação log-odds para calcular
        confiança de cada entidade e métricas de documento.
        
        Fontes do ensemble:
        1. Regex + DV validation
        2. BERT Davlan (multilíngue)
        3. NuNER (pt-BR especializado)
        4. spaCy (complementar)
        5. Gatilhos linguísticos
        """
        # Coleta fontes usadas
        sources_used = []
        if self.nlp_bert:
            sources_used.append("bert_ner")
        if self.nlp_nuner:
            sources_used.append("nuner")
        if self.nlp_spacy:
            sources_used.append("spacy")
        sources_used.append("regex")
        
        # === ENSEMBLE DE DETECÇÃO COM RASTREAMENTO DE FONTE ===
        all_raw_detections: List[Dict] = []
        
        # 1. Regex com validação de DV
        regex_weight = self.ensemble_weights.get('regex', 1.0)
        regex_findings = self._detectar_regex(text)
        for f in regex_findings:
            all_raw_detections.append({
                "tipo": f.tipo,
                "valor": f.valor,
                "start": f.inicio,
                "end": f.fim,
                "source": "regex",
                "score": f.confianca * regex_weight,
                "peso": f.peso * regex_weight
            })
        
        # 2. Nomes após gatilhos
        gatilho_findings = self._extrair_nomes_gatilho(text)
        for f in gatilho_findings:
            all_raw_detections.append({
                "tipo": f.tipo,
                "valor": f.valor,
                "start": f.inicio,
                "end": f.fim,
                "source": "gatilho",
                "score": f.confianca,
                "peso": f.peso
            })
        
        # 3. BERT Davlan NER (multilíngue)
        bert_weight = self.ensemble_weights.get('bert', 1.0)
        if self.nlp_bert:
            bert_findings = self._detectar_ner_bert_only(text)
            for f in bert_findings:
                all_raw_detections.append({
                    "tipo": f.tipo,
                    "valor": f.valor,
                    "start": f.inicio,
                    "end": f.fim,
                    "source": "bert_ner",
                    "score": f.confianca * bert_weight,
                    "peso": f.peso * bert_weight
                })
        
        # 4. NuNER pt-BR (especializado em português)
        if self.nlp_nuner:
            nuner_findings = self._detectar_ner_nuner_only(text)
            for f in nuner_findings:
                all_raw_detections.append({
                    "tipo": f.tipo,
                    "valor": f.valor,
                    "start": f.inicio,
                    "end": f.fim,
                    "source": "nuner",
                    "score": f.confianca,
                    "peso": f.peso
                })
        
        # 5. spaCy NER (complementar)
        spacy_weight = self.ensemble_weights.get('spacy', 1.0)
        if self.nlp_spacy:
            spacy_findings = self._detectar_ner_spacy_only(text)
            for f in spacy_findings:
                all_raw_detections.append({
                    "tipo": f.tipo,
                    "valor": f.valor,
                    "start": f.inicio,
                    "end": f.fim,
                    "source": "spacy",
                    "score": f.confianca * spacy_weight,
                    "peso": f.peso * spacy_weight
                })
        
        # Usa calculador probabilístico
        doc_confidence = self.confidence_calculator.process_raw_detections(
            raw_detections=all_raw_detections,
            sources_used=sources_used,
            text=text
        )
        
        # Converte para formato de retorno legado
        if not doc_confidence.has_pii:
            return False, [], "SEGURO", doc_confidence.confidence_no_pii
        
        # Pós-processamento de spans
        try:
            from src.confidence.combiners import pos_processar_spans
            spans = [(e.inicio, e.fim, e.tipo, e.valor) for e in doc_confidence.entities if hasattr(e, 'inicio') and hasattr(e, 'fim')]
            spans_proc = pos_processar_spans(spans, min_len=2, merge_overlap=True)
            findings_proc = []
            for s in spans_proc:
                for e in doc_confidence.entities:
                    if hasattr(e, 'inicio') and hasattr(e, 'fim') and e.inicio == s[0] and e.fim == s[1]:
                        findings_proc.append({
                            "tipo": e.tipo,
                            "valor": e.valor,
                            "confianca": e.confianca
                        })
                        break
            findings_dict = findings_proc if findings_proc else [
                {"tipo": entity.tipo, "valor": entity.valor, "confianca": entity.confianca} for entity in doc_confidence.entities
            ]
        except Exception as e:
            findings_dict = [
                {"tipo": entity.tipo, "valor": entity.valor, "confianca": entity.confianca} for entity in doc_confidence.entities
            ]
            logger.warning(f"[Pós-processamento] Falha ao aplicar pos_processar_spans: {e}")

        # Confiança do documento = confidence_all_found (ou min_entity como fallback)
        doc_conf = doc_confidence.confidence_all_found or doc_confidence.confidence_min_entity or 0.9
        
        return True, findings_dict, doc_confidence.risco, doc_conf
    
    def _detect_legacy(self, text: str) -> Tuple[bool, List[Dict], str, float]:
        """Sistema de detecção legado (fallback quando módulo probabilístico indisponível)."""
        # === ENSEMBLE DE DETECÇÃO ===
        all_findings: List[PIIFinding] = []
        
        # 1. Regex com validação de DV (mais preciso)
        regex_findings = self._detectar_regex(text)
        all_findings.extend(regex_findings)
        
        # 2. Nomes após gatilhos de contato (sempre PII)
        gatilho_findings = self._extrair_nomes_gatilho(text)
        all_findings.extend(gatilho_findings)
        
        # 3. NER (BERT + spaCy)
        ner_findings = self._detectar_ner(text)
        all_findings.extend(ner_findings)
        
        # === DEDUPLICAÇÃO COM PRIORIDADE ===
        final_dict: Dict[str, PIIFinding] = {}
        for finding in all_findings:
            key = finding.valor.lower().strip()
            
            if key not in final_dict:
                final_dict[key] = finding
            elif finding.peso > final_dict[key].peso:
                final_dict[key] = finding
            elif finding.peso == final_dict[key].peso and finding.confianca > final_dict[key].confianca:
                final_dict[key] = finding
        
        # === RESULTADO FINAL ===
        final_list = list(final_dict.values())
        

        # === THRESHOLD DINÂMICO POR TIPO ===
        pii_relevantes = []
        for f in final_list:
            tipo = getattr(f, 'tipo', None)
            conf = getattr(f, 'confianca', 1.0)
            peso = getattr(f, 'peso', 1)
            if tipo in self.THRESHOLDS_DINAMICOS:
                th = self.THRESHOLDS_DINAMICOS[tipo]
                if peso >= th['peso_min'] and conf >= th['confianca_min']:
                    pii_relevantes.append(f)
            else:
                if peso >= 2:
                    pii_relevantes.append(f)
        
        if not pii_relevantes:
            return False, [], "SEGURO", 1.0
        
        # Calcula risco máximo
        max_peso = max(f.peso for f in pii_relevantes)
        
        # Mapeamento de risco
        risco_map = {
            5: "CRITICO",
            4: "ALTO",
            3: "MODERADO",
            2: "BAIXO",
            0: "SEGURO"
        }
        nivel_risco = risco_map.get(max_peso, "MODERADO")
        
        # Confiança baseada no melhor achado
        max_confianca = max(f.confianca for f in pii_relevantes)
        
        # Pós-processamento de spans
        try:
            from src.confidence.combiners import pos_processar_spans
            spans = [(f.inicio, f.fim, f.tipo, f.valor) for f in pii_relevantes if hasattr(f, 'inicio') and hasattr(f, 'fim')]
            spans_proc = pos_processar_spans(spans, min_len=2, merge_overlap=True)
            findings_proc = []
            for s in spans_proc:
                for f in pii_relevantes:
                    if hasattr(f, 'inicio') and hasattr(f, 'fim') and f.inicio == s[0] and f.fim == s[1]:
                        findings_proc.append({
                            "tipo": f.tipo,
                            "valor": f.valor,
                            "confianca": f.confianca
                        })
                        break
            findings_dict = findings_proc if findings_proc else [
                {"tipo": f.tipo, "valor": f.valor, "confianca": f.confianca} for f in pii_relevantes
            ]
        except Exception as e:
            findings_dict = [
                {"tipo": f.tipo, "valor": f.valor, "confianca": f.confianca} for f in pii_relevantes
            ]
            logger.warning(f"[Pós-processamento] Falha ao aplicar pos_processar_spans: {e}")

        return True, findings_dict, nivel_risco, max_confianca
    
    def detect_extended(self, text: str) -> Dict:
        """Detecta PII com métricas de confiança probabilística extendidas.
        
        Retorna informações adicionais sobre confiança:
        - confidence_no_pii: P(não existe PII) quando nada detectado
        - confidence_all_found: P(encontramos todo PII) quando tem detecções
        - confidence_min_entity: Menor confiança entre entidades
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Dict com estrutura:
            {
                "has_pii": bool,
                "classificacao": "PÚBLICO" ou "NÃO PÚBLICO",
                "risco": "CRÍTICO"/"ALTO"/"MODERADO"/"BAIXO"/"SEGURO",
                "confidence": {
                    "no_pii": float (0-1),
                    "all_found": float ou None,
                    "min_entity": float ou None
                },
                "sources_used": ["bert_ner", "spacy", "regex", ...],
                "entities": [{"tipo", "valor", "confianca", ...}, ...],
                "total_entities": int
            }
        """
        if not text or not text.strip():
            return {
                "has_pii": False,
                "classificacao": "PÚBLICO",
                "risco": "SEGURO",
                "confidence": {
                    "no_pii": 0.9999999999,
                    "all_found": None,
                    "min_entity": None
                },
                "sources_used": [],
                "entities": [],
                "total_entities": 0
            }
        
        # Coleta fontes usadas
        sources_used = []
        if self.nlp_bert:
            sources_used.append("bert_ner")
        if self.nlp_spacy:
            sources_used.append("spacy")
        sources_used.append("regex")  # Sempre disponível
        
        # Se módulo de confiança não disponível, usa detect() e converte
        if not self.use_probabilistic_confidence:
            is_pii, findings, nivel_risco, conf = self.detect(text)
            return {
                "has_pii": is_pii,
                "classificacao": "NÃO PÚBLICO" if is_pii else "PÚBLICO",
                "risco": nivel_risco,
                "confidence": {
                    "no_pii": 1.0 - conf if not is_pii else 0.0,
                    "all_found": conf if is_pii else None,
                    "min_entity": conf if is_pii else None
                },
                "sources_used": sources_used,
                "entities": findings,
                "total_entities": len(findings)
            }
        
        # === ENSEMBLE DE DETECÇÃO COM RASTREAMENTO DE FONTE ===
        all_raw_detections: List[Dict] = []
        
        # 1. Regex com validação de DV
        regex_findings = self._detectar_regex(text)
        for f in regex_findings:
            all_raw_detections.append({
                "tipo": f.tipo,
                "valor": f.valor,
                "start": f.inicio,
                "end": f.fim,
                "source": "regex",
                "score": f.confianca,
                "peso": f.peso
            })
        
        # 2. Nomes após gatilhos
        gatilho_findings = self._extrair_nomes_gatilho(text)
        for f in gatilho_findings:
            all_raw_detections.append({
                "tipo": f.tipo,
                "valor": f.valor,
                "start": f.inicio,
                "end": f.fim,
                "source": "gatilho",
                "score": f.confianca,
                "peso": f.peso
            })
        
        # 3. NER (BERT + spaCy) - precisa rastrear separadamente
        if self.nlp_bert:
            bert_findings = self._detectar_ner_bert_only(text)
            for f in bert_findings:
                all_raw_detections.append({
                    "tipo": f.tipo,
                    "valor": f.valor,
                    "start": f.inicio,
                    "end": f.fim,
                    "source": "bert_ner",
                    "score": f.confianca,
                    "peso": f.peso
                })
        
        if self.nlp_spacy:
            spacy_findings = self._detectar_ner_spacy_only(text)
            for f in spacy_findings:
                all_raw_detections.append({
                    "tipo": f.tipo,
                    "valor": f.valor,
                    "start": f.inicio,
                    "end": f.fim,
                    "source": "spacy",
                    "score": f.confianca,
                    "peso": f.peso
                })
        
        # Usa calculador probabilístico
        doc_confidence = self.confidence_calculator.process_raw_detections(
            raw_detections=all_raw_detections,
            sources_used=sources_used,
            text=text
        )
        
        return doc_confidence.to_dict()
    
    def _detectar_ner_bert_only(self, texto: str) -> List[PIIFinding]:
        """Detecta apenas com BERT NER (para rastreamento de fonte)."""
        findings = []
        if not self.nlp_bert:
            return findings
        try:
            resultados = self.nlp_bert(texto)
            for ent in resultados:
                tipo = ent.get('entity_group', '')
                valor = ent.get('word', '')
                inicio = ent.get('start', 0)
                fim = ent.get('end', 0)
                score = ent.get('score', 0.0)
                # Filtros de qualidade
                if tipo not in ['PER', 'PESSOA', 'B-PER', 'I-PER', 'PERSON']:
                    continue
                if len(valor) <= 3:
                    continue
                if " " not in valor:
                    continue
                if self._deve_ignorar_entidade(valor):
                    continue
                if self._deve_ignorar_nome(texto, inicio):
                    continue
                base = self.confianca_base.get("NOME_BERT", 0.82)
                fator = self._calcular_fator_contexto(texto, inicio, fim, "NOME")
                confianca = min(1.0, base * fator)
                findings.append(PIIFinding(
                    tipo="NOME", valor=valor,
                    confianca=confianca, peso=4,
                    inicio=inicio, fim=fim
                ))
        except Exception as e:
            logger.warning(f"Erro no BERT NER: {e}")
        return findings
    
    def _detectar_ner_spacy_only(self, texto: str) -> List[PIIFinding]:
        """Detecta apenas com spaCy NER (para rastreamento de fonte)."""
        findings = []
        
        if not self.nlp_spacy:
            return findings
        
        try:
            doc = self.nlp_spacy(texto)
            for ent in doc.ents:
                if ent.label_ != 'PER':
                    continue
                
                # Filtros
                if len(ent.text) <= 3:
                    continue
                if " " not in ent.text:
                    continue
                if self._deve_ignorar_entidade(ent.text):
                    continue
                if self._deve_ignorar_nome(texto, ent.start_char):
                    continue
                
                inicio, fim = ent.start_char, ent.end_char
                base = self.confianca_base.get("NOME_SPACY", 0.70)
                fator = self._calcular_fator_contexto(texto, inicio, fim, "NOME")
                confianca = min(1.0, base * fator)
                
                findings.append(PIIFinding(
                    tipo="NOME", valor=ent.text,
                    confianca=confianca, peso=4,
                    inicio=inicio, fim=fim
                ))
        except Exception as e:
            logger.warning(f"Erro no spaCy: {e}")
        
        return findings
    
    def _detectar_ner_nuner_only(self, texto: str) -> List[PIIFinding]:
        """Detecta apenas com NuNER pt-BR (para rastreamento de fonte).
        
        NuNER é um modelo especializado em português brasileiro,
        com melhor performance em nomes compostos brasileiros como:
        - Maria das Graças
        - José de Souza Filho
        - Ana Carolina da Silva
        """
        findings = []
        
        if not self.nlp_nuner:
            return findings
        
        try:
            # Trunca texto se necessário
            texto_truncado = texto[:4096] if len(texto) > 4096 else texto
            
            resultados = self.nlp_nuner(texto_truncado)
            for ent in resultados:
                # NuNER usa labels diferentes - aceita PER, PESSOA, B-PER, I-PER, 'PERSON'
                if ent['entity_group'] not in ['PER', 'PESSOA', 'B-PER', 'I-PER', 'PERSON']:
                    continue
                
                nome = ent['word']
                score = ent['score']
                
                # Filtros de qualidade
                if len(nome) <= 3:
                    continue
                if " " not in nome:  # Precisa ter nome + sobrenome
                    continue
                if self._deve_ignorar_entidade(nome):
                    continue
                if self._deve_ignorar_nome(texto, ent['start']):
                    continue
                
                inicio, fim = ent['start'], ent['end']
                
                findings.append(PIIFinding(
                    tipo="NOME", valor=nome,
                    confianca=score, peso=4,
                    inicio=inicio, fim=fim
                ))
        except Exception as e:
            logger.warning(f"Erro no NuNER: {e}")
        
        return findings


# === FUNÇÃO DE CONVENIÊNCIA ===

def criar_detector(usar_gpu: bool = True, use_probabilistic_confidence: bool = True) -> PIIDetector:
    """Factory function para criar detector configurado.
    
    Args:
        usar_gpu: Se deve usar GPU para modelos (default: True)
        use_probabilistic_confidence: Se deve usar sistema de confiança 
            probabilística (default: True)
    """
    return PIIDetector(usar_gpu=usar_gpu, use_probabilistic_confidence=use_probabilistic_confidence)


# === TESTE RÁPIDO ===

if __name__ == "__main__":
    detector = criar_detector(usar_gpu=False)
    
    testes = [
        "Meu CPF é 529.982.247-25 e moro na Rua das Flores, 123",
        "A Dra. Maria da Secretaria de Administração informou que...",
        "Preciso falar com o João Silva sobre o processo",
        "O servidor José Santos do DETRAN atendeu a demanda",
        "Meu telefone é +55 61 99999-8888 para contato",
        "Email: joao.silva@gmail.com",
        "Protocolo SEI 00000-00000000/2024-00 do GDF",
    ]
    
    for texto in testes:
        is_pii, findings, risco, conf = detector.detect(texto)
        status = "🔴 PII" if is_pii else "🟢 SEGURO"
        print(f"\n{status} [{risco}] (conf: {conf:.2f})")
        print(f"Texto: {texto[:80]}...")
        if findings:
            for f in findings:
                print(f"  → {f['tipo']}: {f['valor']}")