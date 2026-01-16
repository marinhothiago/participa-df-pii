"""Módulo de detecção de Informações Pessoais Identificáveis (PII).

Versão: 9.0 - HACKATHON PARTICIPA-DF 2025
Abordagem: Ensemble híbrido com alta recall (estratégia OR)

Pipeline:
1. Regras determinísticas (regex + validação DV) → 70% dos PIIs
2. NER especializado (BERTimbau NER) → nomes e entidades
3. spaCy como backup → cobertura adicional
4. Ensemble OR → qualquer detector positivo = PII
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import logging
from text_unidecode import unidecode

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
    """Detector híbrido de PII com ensemble de alta recall.
    
    Estratégia: Ensemble OR - qualquer detector positivo classifica como PII.
    Isso maximiza recall (não deixar escapar nenhum PII) às custas de alguns
    falsos positivos, que é a estratégia correta para LAI/LGPD.
    """

    def __init__(self, usar_gpu: bool = True) -> None:
        """Inicializa o detector com todos os modelos NLP."""
        logger.info("🏆 [v9.0] VERSÃO HACKATHON - ENSEMBLE DE ALTA RECALL")
        
        self.validador = ValidadorDocumentos()
        self._inicializar_modelos(usar_gpu)
        self._inicializar_vocabularios()
        self._compilar_patterns()
    
    def _inicializar_modelos(self, usar_gpu: bool) -> None:
        """Carrega modelos NLP com fallback."""
        import spacy
        from transformers import pipeline, AutoModelForTokenClassification, AutoTokenizer
        
        # spaCy - modelo grande para português
        try:
            self.nlp_spacy = spacy.load("pt_core_news_lg")
            logger.info("✅ spaCy pt_core_news_lg carregado")
        except OSError:
            try:
                self.nlp_spacy = spacy.load("pt_core_news_md")
                logger.warning("⚠️ Usando pt_core_news_md (fallback)")
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
            logger.info("🚀 GPU detectada, usando CUDA para BERT")
        else:
            device = -1  # CPU
        
        try:
            # Modelo multilíngue NER - treinado em 10+ idiomas incluindo português
            # Labels: O, B-PER, I-PER, B-ORG, I-ORG, B-LOC, I-LOC, B-DATE, I-DATE
            self.nlp_bert = pipeline(
                "ner",
                model="Davlan/bert-base-multilingual-cased-ner-hrl",
                aggregation_strategy="simple",
                device=device
            )
            logger.info("✅ BERT NER multilíngue carregado (PER, ORG, LOC, DATE)")
        except Exception as e:
            self.nlp_bert = None
            logger.warning(f"⚠️ BERT NER não disponível: {e}. Usando apenas spaCy para NER.")
    
    def _inicializar_vocabularios(self) -> None:
        """Inicializa todos os vocabulários e listas de contexto."""
        
        # Palavras que NUNCA são PII
        self.blocklist_total: Set[str] = {
            # Saudações e formalidades
            "AGRADECO", "ATENCIOSAMENTE", "CORDIALMENTE", "RESPEITOSAMENTE",
            "BOM DIA", "BOA TARDE", "BOA NOITE", "PREZADOS", "PREZADO", "PREZADA",
            
            # Ações administrativas
            "SOLICITO", "INFORMO", "ENCAMINHO", "DESPACHO", "PROCESSO", "AUTOS",
            "REQUERIMENTO", "PROTOCOLO", "MANIFESTACAO", "DEMANDA",
            
            # Tratamentos
            "DRA", "DR", "SR", "SRA", "PROF", "PROFESSOR", "PROFESSORA",
            "DOUTOR", "DOUTORA", "EXCELENTISSIMO", "EXCELENTISSIMA",
            
            # Estrutura organizacional
            "SECRETARIA", "DEPARTAMENTO", "DIRETORIA", "GERENCIA", "COORDENACAO",
            "SUPERINTENDENCIA", "SUBSECRETARIA", "ASSESSORIA", "GABINETE",
            
            # Termos comuns em LAI
            "CIDADAO", "CIDADA", "REQUERENTE", "SOLICITANTE", "INTERESSADO",
            "DENUNCIANTE", "RECLAMANTE", "MANIFESTANTE",
            
            # Outros
            "LIGACOES", "TELEFONICAS", "MUDAS", "ILUMINACAO", "PUBLICA",
            "OUVIDORIA", "RECLAMACAO", "DENUNCIA", "ELOGIO", "SUGESTAO",
            "JANEIRO", "FEVEREIRO", "MARCO", "ABRIL", "MAIO", "JUNHO",
            "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
        }
        
        # Termos institucionais/públicos do GDF - EXPANDIDO
        self.termos_seguros: Set[str] = {
            # Órgãos do GDF
            "GDF", "PMDF", "PCDF", "CBMDF", "SEEDF", "SESDF", "SSP", "DETRAN",
            "BRB", "NOVACAP", "CGDF", "CLDF", "TCDF", "DODF", "SEI", "TERRACAP",
            "CAESB", "NEOENERGIA", "CEB", "METRÔ-DF", "METRO DF", "DFTRANS",
            "AGEFIS", "ADASA", "CODHAB", "EMATER", "FAPDF", "INESP",
            
            # Regiões Administrativas
            "BRASILIA", "PLANO PILOTO", "GAMA", "TAGUATINGA", "BRAZLANDIA",
            "SOBRADINHO", "PLANALTINA", "PARANOA", "NUCLEO BANDEIRANTE",
            "CEILANDIA", "GUARA", "CRUZEIRO", "SAMAMBAIA", "SANTA MARIA",
            "SAO SEBASTIAO", "RECANTO DAS EMAS", "LAGO SUL", "LAGO NORTE",
            "CANDANGOLANDIA", "RIACHO FUNDO", "SUDOESTE", "OCTOGONAL",
            "VARJAO", "PARK WAY", "SCIA", "ESTRUTURAL", "JARDIM BOTANICO",
            "ITAPOA", "SIA", "VICENTE PIRES", "FERCAL", "SOL NASCENTE",
            "POR DO SOL", "ARNIQUEIRA", "AGUAS CLARAS",
            
            # Endereços administrativos de Brasília
            "ASA SUL", "ASA NORTE", "EIXO MONUMENTAL", "ESPLANADA DOS MINISTERIOS",
            "W3", "L2", "SQS", "SQN", "SRES", "SHIS", "SHIN", "SHLN", "SGAS", "SGAN",
            "SRTVS", "SRTVN", "SCN", "SCS", "SBS", "SBN", "SDN", "SDS",
            
            # Tribunais e órgãos federais em Brasília
            "STF", "STJ", "TST", "TSE", "STM", "TJDFT", "TRF1", "TRT10",
            "MPF", "MPDFT", "DPU", "AGU", "CGU", "TCU", "SENADO", "CAMARA"
        }
        
        # Indicadores de servidor público
        self.indicadores_servidor: Set[str] = {
            "SERVIDOR", "SERVIDORA", "FUNCIONARIO", "FUNCIONARIA",
            "ANALISTA", "TECNICO", "TÉCNICO", "AUDITOR", "FISCAL",
            "PERITO", "DELEGADO", "DELEGADA", "ADMINISTRADOR", "ADMINISTRADORA",
            "COORDENADOR", "COORDENADORA", "DIRETOR", "DIRETORA",
            "SECRETARIO", "SECRETÁRIA", "SECRETARIA",
            "AGENTE", "MEDICO", "MÉDICO", "MEDICA", "MÉDICA",
            "ASSESSOR", "ASSESSORA", "CHEFE", "GERENTE",
            "SUPERINTENDENTE", "SUBSECRETARIO", "SUBSECRETÁRIA"
        }
        
        # Cargos que conferem imunidade em contexto funcional
        self.cargos_autoridade: Set[str] = {
            "DRA", "DR", "SR", "SRA", "PROF", "DOUTOR", "DOUTORA",
            "EXMO", "EXMA", "ILMO", "ILMA", "MM", "MERITISSIMO"
        }
        
        # Gatilhos que ANULAM imunidade (indicam contato pessoal)
        self.gatilhos_contato: Set[str] = {
            "FALAR COM", "TRATAR COM", "LIGAR PARA", "CONTATO COM",
            "TELEFONE DO", "TELEFONE DA", "CELULAR DO", "CELULAR DA",
            "WHATSAPP DO", "WHATSAPP DA", "EMAIL DO", "EMAIL DA",
            "FALAR COM O", "FALAR COM A", "CONTATO DO", "CONTATO DA",
            "PROCURAR", "CHAMAR", "AVISAR", "COMUNICAR COM",
            "ENDERECO DO", "ENDERECO DA", "RESIDENCIA DO", "RESIDENCIA DA",
            "CASA DO", "CASA DA", "MORA NA", "MORA NO", "RESIDE NA", "RESIDE NO"
        }
        
        # Contextos que indicam informação pessoal
        self.contextos_pii: Set[str] = {
            "MEU CPF", "MINHA IDENTIDADE", "MEU RG", "MINHA CNH",
            "MEU TELEFONE", "MEU CELULAR", "MEU EMAIL", "MEU E-MAIL",
            "MORO NA", "MORO NO", "RESIDO NA", "RESIDO NO",
            "MEU ENDERECO", "MINHA RESIDENCIA", "MINHA CASA",
            "MEU NOME COMPLETO", "ME CHAMO", "MEU NOME E",
            "MINHA CONTA", "MINHA AGENCIA", "MEU BANCO",
            "MEU PASSAPORTE", "MEU TITULO", "MEU PIS", "MEU NIT"
        }
        
        # Pesos por tipo de PII
        self.pesos_pii: Dict[str, int] = {
            # Crítico (5) - Identificação direta
            "CPF": 5, "RG": 5, "CNH": 5, "PASSAPORTE": 5,
            "TITULO_ELEITOR": 5, "PIS": 5, "CNS": 5, "CNPJ_PESSOAL": 5,
            "CERTIDAO": 5, "CTPS": 5, "REGISTRO_PROFISSIONAL": 5,
            
            # Alto (4) - Contato direto
            "EMAIL_PESSOAL": 4, "TELEFONE": 4,
            "ENDERECO_RESIDENCIAL": 4, "NOME": 4,
            "CONTA_BANCARIA": 4, "PIX": 4, "CARTAO_CREDITO": 4,
            
            # Moderado (3) - Identificação indireta
            "PLACA_VEICULO": 3, "CEP": 3,
            "DATA_NASCIMENTO": 3, "PROCESSO_CNJ": 3,
        }
    
    def _compilar_patterns(self) -> None:
        """Compila todos os patterns regex para performance."""
        
        self.patterns_compilados: Dict[str, re.Pattern] = {
            # === DOCUMENTOS DE IDENTIFICAÇÃO ===
            
            # CPF: 000.000.000-00 ou 00000000000
            'CPF': re.compile(
                r'\b(\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[\-\.\s]?\d{2})\b',
                re.IGNORECASE
            ),
            
            # CNPJ: 00.000.000/0000-00 ou 00000000000000
            'CNPJ': re.compile(
                r'\b(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[/\.\s]?\d{4}[\-\.\s]?\d{2})\b',
                re.IGNORECASE
            ),
            
            # RG: diversos formatos estaduais
            'RG': re.compile(
                r'(?i)(?:RG|R\.G\.|IDENTIDADE|CARTEIRA DE IDENTIDADE)[:\s]*'
                r'[\(\[]?[A-Z]{0,2}[\)\]]?[\s\-]*'
                r'(\d{1,2}[\.\s]?\d{3}[\.\s]?\d{3}[\-\.\s]?[\dXx])',
                re.IGNORECASE
            ),
            
            # CNH: 00000000000 (11 dígitos)
            'CNH': re.compile(
                r'(?i)(?:CNH|CARTEIRA DE MOTORISTA|HABILITACAO)[:\s]*'
                r'(\d{11})',
                re.IGNORECASE
            ),
            
            # PIS/PASEP/NIT: 000.00000.00-0
            'PIS': re.compile(
                r'\b(\d{3}[\.\s]?\d{5}[\.\s]?\d{2}[\-\.\s]?\d{1})\b',
                re.IGNORECASE
            ),
            
            # Título de Eleitor: 0000 0000 0000 (12 dígitos)
            'TITULO_ELEITOR': re.compile(
                r'(?i)(?:TITULO DE ELEITOR|TITULO ELEITORAL)[:\s]*'
                r'(\d{4}[\.\s]?\d{4}[\.\s]?\d{4})',
                re.IGNORECASE
            ),
            
            # CNS (Cartão SUS): 15 dígitos começando com 1, 2, 7, 8 ou 9
            'CNS': re.compile(
                r'\b([1-2789]\d{14})\b',
                re.IGNORECASE
            ),
            
            # Passaporte Brasileiro: AA000000 ou BR000000
            'PASSAPORTE': re.compile(
                r'(?i)(?:PASSAPORTE|PASSPORT)[:\s]*'
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
                r'([A-Z]{2})?[\s\-]*(\d{3,6})',
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
            
            # Telefone com DDI: +55 XX XXXXX-XXXX
            'TELEFONE_DDI': re.compile(
                r'(\+55[\s\-]?\(?\d{2}\)?[\s\-]?9?\d{4}[\s\-]?\d{4})',
                re.IGNORECASE
            ),
            
            # Celular: (XX) 9XXXX-XXXX
            'CELULAR': re.compile(
                r'(?<![+\d])[\(\[]?(\d{2})[\)\]]?[\s\-]?(9\d{4})[\s\-]?(\d{4})(?!\d)',
                re.IGNORECASE
            ),
            
            # Telefone fixo: (XX) XXXX-XXXX
            'TELEFONE_FIXO': re.compile(
                r'(?<![+\d])[\(\[]?(\d{2})[\)\]]?[\s\-]?([2-5]\d{3})[\s\-]?(\d{4})(?!\d)',
                re.IGNORECASE
            ),
            
            # === ENDEREÇOS ===
            
            # Endereço residencial com indicadores
            'ENDERECO_RESIDENCIAL': re.compile(
                r'(?i)(?:moro|resido|minha casa|meu endere[cç]o|endere[cç]o\s*:?)'
                r'[^\n]{0,80}?'
                r'(?:(?:rua|av|avenida|alameda|travessa|estrada|rodovia)[\s\.]+'
                r'[a-záéíóúàèìòùâêîôûãõ\s]+[\s,]+(?:n[ºo°]?[\s\.]*)?[\d]+|'
                r'(?:casa|apto?|apartamento|lote|bloco|quadra)[\s\.]*'
                r'(?:n[ºo°]?[\s\.]*)?[\d]+[a-z]?)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # CEP: 00000-000 ou 00.000-000
            'CEP': re.compile(
                r'\b(\d{2}\.?\d{3}[\-]?\d{3})\b',
                re.IGNORECASE
            ),
            
            # Placa de veículo (Mercosul e antiga)
            'PLACA_VEICULO': re.compile(
                r'\b([A-Z]{3}[\-\s]?\d[A-Z0-9]\d{2}|'  # Mercosul: AAA0A00
                r'[A-Z]{3}[\-\s]?\d{4})\b',            # Antiga: AAA-0000
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
                r'\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b',
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
                r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b',
                re.IGNORECASE
            ),
            
            # Processo judicial CNJ: 0000000-00.0000.0.00.0000
            'PROCESSO_CNJ': re.compile(
                r'\b(\d{7}[\-\.]\d{2}[\-\.]\d{4}[\-\.]\d[\-\.]\d{2}[\-\.]\d{4})\b',
                re.IGNORECASE
            ),
        }
    
    @lru_cache(maxsize=1024)
    def _normalizar(self, texto: str) -> str:
        """Normaliza texto para comparação (com cache)."""
        return unidecode(texto).upper().strip() if texto else ""
    
    def _eh_lixo(self, texto_entidade: str) -> bool:
        """Verifica se entidade é lixo (falso positivo)."""
        if not texto_entidade or len(texto_entidade) < 3:
            return True
        
        t_norm = self._normalizar(texto_entidade)
        
        # Blocklist direta
        if t_norm in self.blocklist_total:
            return True
        
        # Termos seguros
        if any(ts in t_norm for ts in self.termos_seguros):
            return True
        
        # Só números/símbolos
        if re.match(r'^[\d/\.\-\s]+$', texto_entidade):
            return True
        
        # Palavras genéricas
        palavras_bloqueadas = {
            "LIGACOES", "TELEFONICAS", "RECLAMACAO", "DENUNCIA",
            "PROTOCOLO", "PROCESSO", "MANIFESTACAO", "SOLICITACAO"
        }
        if any(p in t_norm for p in palavras_bloqueadas):
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
            "000.000.000-00", "111.111.111-11", "XXX.XXX.XXX-XX"
        }
        
        return any(p in contexto for p in palavras_negativas)
    
    def _detectar_regex(self, texto: str) -> List[PIIFinding]:
        """Detecção por regex com validação de dígito verificador."""
        findings = []
        
        for tipo, pattern in self.patterns_compilados.items():
            for match in pattern.finditer(texto):
                valor = match.group(1) if match.lastindex else match.group()
                
                # Validação específica por tipo
                if tipo == 'CPF':
                    if self._contexto_negativo_cpf(texto, valor):
                        continue
                    if not self.validador.validar_cpf(valor):
                        continue
                    findings.append(PIIFinding(
                        tipo="CPF", valor=valor, confianca=1.0,
                        peso=5, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'CNPJ':
                    # CNPJ de empresa não é PII, mas CNPJ de MEI pode ser
                    # Por segurança, não marcamos CNPJ como PII por padrão
                    if not self.validador.validar_cnpj(valor):
                        continue
                    # Só marca se tiver contexto de pessoa física
                    contexto = texto[max(0, match.start()-50):match.end()+50].upper()
                    if any(p in contexto for p in ["MEU CNPJ", "MINHA EMPRESA", "SOU MEI", "MEI"]):
                        findings.append(PIIFinding(
                            tipo="CNPJ_PESSOAL", valor=valor, confianca=0.8,
                            peso=4, inicio=match.start(), fim=match.end()
                        ))
                
                elif tipo == 'PIS':
                    if not self.validador.validar_pis(valor):
                        continue
                    findings.append(PIIFinding(
                        tipo="PIS", valor=valor, confianca=1.0,
                        peso=5, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'CNS':
                    if not self.validador.validar_cns(valor):
                        continue
                    findings.append(PIIFinding(
                        tipo="CNS", valor=valor, confianca=1.0,
                        peso=5, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'EMAIL_PESSOAL':
                    # Ignora emails institucionais
                    email_lower = valor.lower()
                    if any(d in email_lower for d in ['.gov.br', '.org.br', '.edu.br', 'empresa-df']):
                        continue
                    findings.append(PIIFinding(
                        tipo="EMAIL_PESSOAL", valor=valor, confianca=1.0,
                        peso=4, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo in ['CELULAR', 'TELEFONE_FIXO', 'TELEFONE_DDI']:
                    # Reconstrói o número
                    if tipo == 'TELEFONE_DDI':
                        # Verifica se é institucional
                        ctx = texto[max(0, match.start()-50):match.start()].lower()
                        if 'institucional' in ctx:
                            continue
                    
                    findings.append(PIIFinding(
                        tipo="TELEFONE", valor=valor, confianca=0.9,
                        peso=4, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'RG':
                    findings.append(PIIFinding(
                        tipo="RG", valor=valor, confianca=1.0,
                        peso=5, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'CNH':
                    findings.append(PIIFinding(
                        tipo="CNH", valor=valor, confianca=1.0,
                        peso=5, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'PASSAPORTE':
                    findings.append(PIIFinding(
                        tipo="PASSAPORTE", valor=valor, confianca=0.95,
                        peso=5, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'ENDERECO_RESIDENCIAL':
                    findings.append(PIIFinding(
                        tipo="ENDERECO_RESIDENCIAL", valor=valor, confianca=0.9,
                        peso=4, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'PLACA_VEICULO':
                    findings.append(PIIFinding(
                        tipo="PLACA_VEICULO", valor=valor, confianca=0.9,
                        peso=3, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'CONTA_BANCARIA':
                    findings.append(PIIFinding(
                        tipo="CONTA_BANCARIA", valor=valor, confianca=0.95,
                        peso=4, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'PIX_UUID':
                    findings.append(PIIFinding(
                        tipo="PIX", valor=valor, confianca=0.95,
                        peso=4, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'CARTAO_CREDITO':
                    # Valida com algoritmo de Luhn seria ideal
                    findings.append(PIIFinding(
                        tipo="CARTAO_CREDITO", valor=valor, confianca=0.85,
                        peso=4, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'DATA_NASCIMENTO':
                    findings.append(PIIFinding(
                        tipo="DATA_NASCIMENTO", valor=valor, confianca=0.85,
                        peso=3, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'TITULO_ELEITOR':
                    if not self.validador.validar_titulo_eleitor(valor):
                        continue
                    findings.append(PIIFinding(
                        tipo="TITULO_ELEITOR", valor=valor, confianca=0.95,
                        peso=5, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'CTPS':
                    findings.append(PIIFinding(
                        tipo="CTPS", valor=valor, confianca=0.95,
                        peso=5, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'CERTIDAO':
                    findings.append(PIIFinding(
                        tipo="CERTIDAO", valor=valor, confianca=0.90,
                        peso=5, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'REGISTRO_PROFISSIONAL':
                    findings.append(PIIFinding(
                        tipo="REGISTRO_PROFISSIONAL", valor=valor, confianca=0.90,
                        peso=5, inicio=match.start(), fim=match.end()
                    ))
                
                elif tipo == 'CEP':
                    # CEP só é PII se estiver em contexto de endereço pessoal
                    contexto = texto[max(0, match.start()-50):match.end()+50].upper()
                    if any(p in contexto for p in ["MORO", "RESIDO", "MINHA CASA", "MEU ENDERECO"]):
                        findings.append(PIIFinding(
                            tipo="CEP", valor=valor, confianca=0.80,
                            peso=3, inicio=match.start(), fim=match.end()
                        ))
                
                elif tipo == 'PROCESSO_CNJ':
                    findings.append(PIIFinding(
                        tipo="PROCESSO_CNJ", valor=valor, confianca=0.95,
                        peso=3, inicio=match.start(), fim=match.end()
                    ))
        
        return findings
    
    def _extrair_nomes_gatilho(self, texto: str) -> List[PIIFinding]:
        """Extrai nomes após gatilhos de contato (sempre PII)."""
        findings = []
        texto_upper = self._normalizar(texto)
        
        for gatilho in self.gatilhos_contato:
            if gatilho not in texto_upper:
                continue
            
            idx = texto_upper.find(gatilho) + len(gatilho)
            resto = texto[idx:idx+60].strip()
            
            # Procura nome após o gatilho
            match = re.search(
                r'\b(?:o|a|do|da)?\s*([A-Z][a-záéíóúàèìòùâêîôûãõ]+(?:\s+[A-Z][a-záéíóúàèìòùâêîôûãõ]+)*)',
                resto
            )
            
            if match:
                nome = match.group(1).strip()
                nome_upper = self._normalizar(nome)
                
                # Ignora cargos e termos genéricos
                if nome_upper in self.cargos_autoridade:
                    continue
                if nome_upper in self.indicadores_servidor:
                    continue
                if len(nome) <= 3:
                    continue
                
                findings.append(PIIFinding(
                    tipo="NOME", valor=nome, confianca=0.95,
                    peso=4, inicio=idx + match.start(), fim=idx + match.end()
                ))
        
        # Nomes após "contra" (reclamação contra Pedro)
        if "CONTRA" in texto_upper:
            idx = texto_upper.find("CONTRA") + 6
            resto = texto[idx:idx+50].strip().strip(".,;:'\"-")
            
            match = re.search(r"^([A-Z][a-záéíóúàèìòùâêîôûãõ]+)", resto)
            if match:
                nome = match.group(1).strip()
                nome_upper = self._normalizar(nome)
                
                if len(nome) > 3 and nome_upper not in self.blocklist_total:
                    findings.append(PIIFinding(
                        tipo="NOME", valor=nome, confianca=0.85,
                        peso=4, inicio=idx, fim=idx + len(nome)
                    ))
        
        return findings
    
    def _deve_ignorar_nome(self, texto: str, inicio: int) -> bool:
        """Determina se nome deve ser ignorado (imunidade funcional)."""
        # Contexto antes do nome
        pre_text = self._normalizar(texto[max(0, inicio-100):inicio])
        # Contexto após o nome (próximos 100 chars)
        pos_text = self._normalizar(texto[inicio:min(len(texto), inicio+100)])
        
        # Gatilho de contato ANULA imunidade
        for gatilho in self.gatilhos_contato:
            if gatilho in pre_text:
                return False
        
        # "Funcionário do mês" = imune (contexto de elogio)
        if "FUNCIONARIO DO MES" in pre_text or "FUNCIONARIA DO MES" in pre_text:
            return True
        
        # Cargo + instituição = imune
        for cargo in self.cargos_autoridade:
            if re.search(rf"\b{cargo}\.?\s*$", pre_text):
                instituicoes = {
                    "SECRETARIA", "ADMINISTRACAO", "DEPARTAMENTO", 
                    "DIRETORIA", "GDF", "SEEDF", "RESPONSAVEL"
                }
                if any(inst in pos_text for inst in instituicoes):
                    return True
        
        # Servidor em contexto funcional = imune
        if any(ind in pre_text for ind in self.indicadores_servidor):
            return True
        
        return False
    
    def _detectar_ner(self, texto: str) -> List[PIIFinding]:
        """Detecção de nomes usando modelos NER (BERT e spaCy)."""
        findings = []
        threshold = 0.75
        
        # BERT NER
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
                        if self._eh_lixo(palavra):
                            continue
                        if self._deve_ignorar_nome(texto, ent['start']):
                            continue
                        
                        findings.append(PIIFinding(
                            tipo="NOME", valor=palavra,
                            confianca=float(ent['score']), peso=4,
                            inicio=ent['start'], fim=ent['end']
                        ))
            except Exception as e:
                logger.warning(f"Erro no BERT NER: {e}")
        
        # spaCy NER (backup)
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
                    if self._eh_lixo(ent.text):
                        continue
                    if self._deve_ignorar_nome(texto, ent.start_char):
                        continue
                    
                    # Evita duplicatas com BERT
                    if not any(f.valor.lower() == ent.text.lower() for f in findings):
                        findings.append(PIIFinding(
                            tipo="NOME", valor=ent.text,
                            confianca=0.80, peso=4,
                            inicio=ent.start_char, fim=ent.end_char
                        ))
            except Exception as e:
                logger.warning(f"Erro no spaCy: {e}")
        
        return findings
    
    def detect(self, text: str) -> Tuple[bool, List[Dict], str, float]:
        """Detecta PII no texto usando ensemble de alta recall.
        
        Estratégia: OR - qualquer detector positivo = PII
        Isso maximiza recall para conformidade LAI/LGPD.
        
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
        
        # Filtra apenas PII relevantes (peso >= 3)
        pii_relevantes = [f for f in final_list if f.peso >= 3]
        
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
        
        # Converte para dict para compatibilidade
        findings_dict = [
            {
                "tipo": f.tipo,
                "valor": f.valor,
                "confianca": f.confianca  # Corrigido: era 'conf', frontend espera 'confianca'
            }
            for f in pii_relevantes
        ]
        
        return True, findings_dict, nivel_risco, max_confianca


# === FUNÇÃO DE CONVENIÊNCIA ===

def criar_detector(usar_gpu: bool = True) -> PIIDetector:
    """Factory function para criar detector configurado."""
    return PIIDetector(usar_gpu=usar_gpu)


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