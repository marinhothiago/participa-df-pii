"""
Configurações de taxas de erro para o sistema de confiança.

Taxas baseadas em benchmarks de produção de sistemas similares.
Devem ser ajustadas com dados reais do corpus brasileiro.
"""

from typing import Dict


# =============================================================================
# TAXAS DE FALSE NEGATIVE (quanto cada fonte PERDE)
# =============================================================================
# Quanto menor, mais a fonte consegue capturar (alta recall)

FN_RATES: Dict[str, float] = {
    # BERT NER multilíngue bem treinado perde ~0.8% de entidades
    "bert_ner": 0.008,
    
    # NuNER pt-BR é especializado em português, perde ~0.6%
    "nuner": 0.006,
    
    # spaCy pt_core_news_lg é complementar, perde ~1.5%
    "spacy": 0.015,
    
    # Regex bem escritos com validação pegam quase tudo com formato
    "regex": 0.003,
    
    # DV falha só se o número for inválido mas ainda for PII real (raríssimo)
    "dv_validation": 0.0001,
    
    # Gatilhos linguísticos ("falar com", "ligar para") pegam ~2% a menos
    "gatilho": 0.02,
}


# =============================================================================
# TAXAS DE FALSE POSITIVE (quanto cada fonte dá ALARME FALSO)
# =============================================================================
# Quanto menor, mais precisa a fonte

FP_RATES: Dict[str, float] = {
    # BERT pode confundir nomes comuns com entidades
    "bert_ner": 0.02,
    
    # NuNER entende melhor o contexto pt-BR, menos FP
    "nuner": 0.015,
    
    # spaCy tem FP um pouco maior em português
    "spacy": 0.03,
    
    # Regex específicos para CPF/CNPJ têm FP muito baixo
    "regex": 0.0002,
    
    # DV válido em sequência aleatória é raríssimo (1 em 100.000)
    "dv_validation": 0.00001,
    
    # Gatilhos podem pegar contexto errado
    "gatilho": 0.05,
}


# =============================================================================
# PRIOR DE PII (probabilidade base antes de ver evidência)
# =============================================================================
# Em corpus de manifestações públicas, ~1% dos textos contém PII pessoal

PRIOR_PII = 0.01


# =============================================================================
# CONFIANÇA BASE POR MÉTODO DE DETECÇÃO
# =============================================================================
# Usado quando não há calibração isotônica disponível

BASE_CONFIDENCE: Dict[str, float] = {
    # Regex + Validação DV (alta confiança)
    "CPF": 0.98,
    "PIS": 0.98,
    "CNS": 0.98,
    "CNH": 0.98,
    "TITULO_ELEITOR": 0.98,
    "CTPS": 0.98,
    "CARTAO_CREDITO": 0.95,
    "CNPJ_PESSOAL": 0.90,
    
    # Regex estrutural (sem DV)
    "EMAIL_PESSOAL": 0.95,
    "PROCESSO_CNJ": 0.90,
    "TELEFONE": 0.88,
    "PLACA_VEICULO": 0.88,
    "PIX": 0.88,
    "RG": 0.85,
    "PASSAPORTE": 0.85,
    "ENDERECO_RESIDENCIAL": 0.85,
    "CONTA_BANCARIA": 0.85,
    "CERTIDAO": 0.85,
    "REGISTRO_PROFISSIONAL": 0.85,
    
    # Regex com dependência de contexto
    "CEP": 0.75,
    "DATA_NASCIMENTO": 0.70,
    
    # NER
    "NOME_BERT": 0.85,    # Será sobrescrito pelo score do modelo
    "NOME_SPACY": 0.70,
    "NOME_GATILHO": 0.85,
}


# =============================================================================
# PESOS DE RISCO LGPD
# =============================================================================

PESOS_LGPD: Dict[str, int] = {
    # Crítico (5) - Identificação direta única
    "CPF": 5, "RG": 5, "CNH": 5, "PASSAPORTE": 5,
    "TITULO_ELEITOR": 5, "PIS": 5, "CNS": 5, "CNPJ_PESSOAL": 5,
    "CERTIDAO": 5, "CTPS": 5, "REGISTRO_PROFISSIONAL": 5,
    
    # Alto (4) - Contato direto ou identificação combinada
    "EMAIL_PESSOAL": 4, "TELEFONE": 4,
    "ENDERECO_RESIDENCIAL": 4, "NOME": 4,
    "CONTA_BANCARIA": 4, "PIX": 4, "CARTAO_CREDITO": 4,
    
    # Moderado (3) - Identificação indireta
    "PLACA_VEICULO": 3, "CEP": 3,
    "DATA_NASCIMENTO": 3, "PROCESSO_CNJ": 3,
    
    # Baixo (2) - Identificação técnica/indireta
    "IP_ADDRESS": 2, "COORDENADAS_GEO": 2, "USER_AGENT": 2,
}


# =============================================================================
# THRESHOLDS DE CONFIANÇA PARA WORKFLOW
# =============================================================================

CONFIDENCE_THRESHOLDS = {
    # Liberação automática - confiança muito alta
    "auto_release": 0.99999,
    
    # Revisão leve (amostragem) - confiança alta
    "light_review": 0.9999,
    
    # Revisão obrigatória - confiança moderada
    "mandatory_review": 0.999,
    
    # Flag de alto risco - confiança baixa
    "high_risk": 0.99,
    
    # Níveis de confiança para classificação de entidades
    "very_high": 0.95,
    "high": 0.85,
    "medium": 0.70,
    "low": 0.50,
    "very_low": 0.30,
}


# =============================================================================
# MAPEAMENTO DE RISCO
# =============================================================================

RISCO_MAP = {
    5: "CRÍTICO",
    4: "ALTO",
    3: "MODERADO",
    2: "BAIXO",
    0: "SEGURO",
}


# =============================================================================
# TIPOS QUE SUPORTAM VALIDAÇÃO DE DV
# =============================================================================

DV_SUPPORTED_TYPES = {
    "CPF",
    "CNPJ",
    "CNPJ_PESSOAL",
    "PIS",
    "CNS",
    "TITULO_ELEITOR",
    "CARTAO_CREDITO",
}


# =============================================================================
# PALAVRAS-CHAVE DE CONTEXTO POR TIPO
# =============================================================================
# Usadas para dar boost ou penalidade na confiança

CONTEXT_KEYWORDS: Dict[str, list] = {
    "CPF": ["cpf", "cadastro", "documento", "pessoa física", "contribuinte"],
    "CNPJ": ["cnpj", "empresa", "pessoa jurídica", "razão social"],
    "CNPJ_PESSOAL": ["mei", "microempreendedor", "cnpj", "empresa"],
    "EMAIL_PESSOAL": ["email", "e-mail", "correio", "contato", "enviar"],
    "TELEFONE": ["telefone", "celular", "ligar", "whatsapp", "contato", "fone"],
    "NOME": ["nome", "senhor", "senhora", "sr.", "sra.", "chamado", "chama"],
    "ENDERECO_RESIDENCIAL": ["endereço", "rua", "avenida", "mora", "reside", "casa"],
    "DATA_NASCIMENTO": ["nascimento", "nasceu", "idade", "aniversário", "data de"],
    "RG": ["rg", "identidade", "carteira", "registro geral"],
    "CNH": ["cnh", "habilitação", "motorista", "carteira de"],
    "PIS": ["pis", "pasep", "nis", "trabalhador"],
    "CNS": ["cns", "cartão sus", "carteira nacional saúde"],
    "TITULO_ELEITOR": ["título", "eleitor", "votação", "zona eleitoral"],
    "CONTA_BANCARIA": ["conta", "banco", "agência", "depósito", "transferência"],
    "PIX": ["pix", "chave pix", "transferência", "pagamento"],
    "CARTAO_CREDITO": ["cartão", "crédito", "débito", "visa", "mastercard"],
}
