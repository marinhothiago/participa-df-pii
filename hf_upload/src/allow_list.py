"""Configuração de termos e filtros para detecção de PII.

Este módulo define listas de termos que:
1. NUNCA são considerados PII (ALLOW_LIST_TERMS)
2. Invalidam um nome se encontrados dentro dele (BLOCK_IF_CONTAINS)

Estas listas são essenciais para evitar falsos positivos em contexto de
Brasília/GDF onde termos institucionais são frequentes.

Exemplos:
    - "Secretaria de Saúde" → Não é PII (instituição pública)
    - "CPF inválido" → CPF não é PII (contexto negativo)
    - "Dr. João da Silva" → "da Silva" não cancela "João"
"""

# ============================================================================
# ALLOW_LIST_TERMS: Termos que NUNCA são PII (público por LAI)
# ============================================================================

ALLOW_LIST_TERMS = {
    # ─────────────────────────────────────────────────────────────────────
    # Órgãos e Siglas do GDF (Governo do Distrito Federal)
    # ─────────────────────────────────────────────────────────────────────
    "CGDF",           # Controladoria Geral do DF
    "PMDF",           # Polícia Militar do DF
    "SEEDF",          # Secretaria de Estado de Educação do DF
    "SESDF",          # Secretaria de Estado de Saúde do DF
    "SSP",            # Secretaria de Estado de Segurança Pública
    "DETRAN",         # Departamento de Trânsito
    "BRB",            # Banco de Brasília
    "NOVACAP",        # Companhia de Concessões Rodoviárias
    "GDF",            # Governo do Distrito Federal
    "PCDF",           # Polícia Civil do DF
    "CBMDF",          # Corpo de Bombeiros Militar do DF
    "CLDF",           # Câmara Legislativa do Distrito Federal
    "TCDF",           # Tribunal de Contas do DF
    "DODF",           # Diário Oficial do Distrito Federal
    "SEI",            # Sistema Eletrônico de Informações
    "TERRACAP",       # Companhia Imobiliária de Brasília
    "CAESB",          # Companhia de Saneamento Ambiental do DF
    "NEOENERGIA",     # Distribuidora de Energia
    
    # ─────────────────────────────────────────────────────────────────────
    # Órgãos Federais e Nacionais
    # ─────────────────────────────────────────────────────────────────────
    "PROCON",         # Secretaria de Proteção ao Consumidor
    "MPDF",           # Ministério Público do DF
    "MPSP",           # Ministério Público de São Paulo
    "LAI",            # Lei de Acesso à Informação
    "ESIC",           # e-SIC (Sistema de Informações ao Cidadão)
    
    # ─────────────────────────────────────────────────────────────────────
    # Órgãos Públicos Genéricos (não PII)
    # ─────────────────────────────────────────────────────────────────────
    "PREFEITURA",     # Prefeitura em geral
    "SECRETARIA",     # Secretaria de Estado
    "MINISTÉRIO",     # Ministério Federal
    "DEPARTAMENTO",   # Departamento genérico
    "GOVERNO",        # Governo em geral
    "COORDENAÇÃO",    # Coordenação administrativa
    "DIRETORIA",      # Diretoria administrativa
    "GERENCIA",       # Gerência administrativa
    "NÚCLEO",         # Núcleo administrativo
    "FUNDAÇÃO",       # Fundação pública
    "AUTARQUIA",      # Autarquia pública
    "CÂMARA",         # Câmara legislativa
    "LEGISLATIVA",    # Poder legislativo
    "TRIBUNAL",       # Tribunal judiciário
    "JUSTIÇA",        # Sistema judiciário
    "PÚBLICO",        # Bem público
    "CONTROLADORIA",  # Órgão de controle
    "OUVIDORIA",      # Ouvidoria pública
    "HOSPITAL",       # Hospital público
    "UBS",            # Unidade Básica de Saúde
    "ESCOLA",         # Escola pública
    "POLÍCIA",        # Polícia em geral
    
    # ─────────────────────────────────────────────────────────────────────
    # Regiões Administrativas de Brasília (28 RAs)
    # ─────────────────────────────────────────────────────────────────────
    "BRASÍLIA",       # Região geral
    "PLANO PILOTO",   # Região central
    "GAMA",           # Região administrativa
    "TAGUATINGA",     # Região administrativa
    "BRAZLÂNDIA",     # Região administrativa
    "SOBRADINHO",     # Região administrativa
    "PLANALTINA",     # Região administrativa
    "PARANOÁ",        # Região administrativa
    "NÚCLEO BANDEIRANTE",  # Região administrativa
    "CEILÂNDIA",      # Região administrativa
    "GUARÁ",          # Região administrativa
    "CRUZEIRO",       # Região administrativa
    "SAMAMBAIA",      # Região administrativa
    "SANTA MARIA",    # Região administrativa
    "SÃO SEBASTIÃO",  # Região administrativa
    "RECANTO DAS EMAS",    # Região administrativa
    "LAGO SUL",       # Região administrativa
    "LAGO NORTE",     # Região administrativa
    "CANDANGOLÂNDIA", # Região administrativa
    "RIACHO FUNDO",   # Região administrativa
    "SUDOESTE",       # Região administrativa
    "OCTOGONAL",      # Região administrativa
    "VARJÃO",         # Região administrativa
    "PARK WAY",       # Região administrativa
    "SCIA",           # Região administrativa
    "ESTRUTURAL",     # Região administrativa
    "JARDIM BOTÂNICO",     # Região administrativa
    "ITAPOÃ",         # Região administrativa
    "SIA",            # Região administrativa
    "VICENTE PIRES",  # Região administrativa
    "FERCAL",         # Região administrativa
    "SOL NASCENTE",   # Região administrativa
    "PÔR DO SOL",     # Região administrativa
    "ARNIQUEIRA",     # Região administrativa
    
    # ─────────────────────────────────────────────────────────────────────
    # Setores Administrativos de Brasília (Código de Endereço)
    # ─────────────────────────────────────────────────────────────────────
    "ASA SUL",        # Asa Sul do Plano Piloto
    "ASA NORTE",      # Asa Norte do Plano Piloto
    "EIXO MONUMENTAL",     # Eixo principal
    "W3",             # Setor comercial/residencial
    "L2",             # Setor comercial/residencial
    "SQS",            # Superquadra Sul
    "SQN",            # Superquadra Norte
    "SRES",           # Setor Residencial Sul
    "SHIS",           # Setor Hoteleiro-Hospitalar
    "SCLN",           # Setor Comercial Local Norte
    "EQ",             # Entrequadra
    "SRV",            # Setor Residencial Vago
    
    # ─────────────────────────────────────────────────────────────────────
    # Termos Jurídicos, Documentais e Administrativos
    # ─────────────────────────────────────────────────────────────────────
    "CONSTITUIÇÃO",   # Lei fundamental
    "BOLETIM",        # Publicação oficial
    "OCORRÊNCIA",     # Registro de incidente
    "PROTOCOLO",      # Número de protocolo
    "PROCESSO",       # Número de processo
    "AUTOS",          # Documentos de processo
    "VALIDADOR",      # Sistema de validação
    "CÓDIGO",         # Código genérico
    "ASSUNTO",        # Tema/Assunto
    "DATA",           # Data genérica
    "HORA",           # Hora genérica
    "REGISTRO",       # Registro genérico
    "INFORMAÇÃO",     # Informação genérica
    "SOLICITAÇÃO",    # Solicitação genérica
    "IDENTIFICAÇÃO",  # Identificação genérica
    "FALE CONOSCO",   # Canal de contato
    
    # ─────────────────────────────────────────────────────────────────────
    # Termos de Localização Geográfica (não PII)
    # ─────────────────────────────────────────────────────────────────────
    "RUA",            # Via pública
    "AVENIDA",        # Via pública
    "QUADRA",         # Bloco Brasília
    "LOTE",           # Parcela de terra
    "BLOCO",          # Bloco predial
    "SETOR",          # Setor de endereço
    "BAIRRO",         # Bairro
    "CIDADE",         # Cidade
    "ESTADO",         # Estado
    "COMPLEMENTO",    # Complemento de endereço
    "LOGRADOURO",     # Via/Endereço
    "CEP",            # Código de Endereçamento Postal
    "TRECHO",         # Trecho de via
    "CHÁCARA",        # Propriedade rural
    "CONDOMÍNIO",     # Condomínio
}


# ============================================================================
# BLOCK_IF_CONTAINS: Palavras que invalidam um nome se encontradas nele
# ============================================================================

BLOCK_IF_CONTAINS = [
    "FEDERAL",        # Lei Federal, Polícia Federal
    "CONSTITUIÇÃO",   # Referência legal
    "MINISTÉRIO",     # Ministério público
    "PÚBLICO",        # Bem público
    "LEI",            # Lei genérica
    "DECRETO",        # Decreto
    "PORTARIA",       # Portaria
    "MUNICIPAL",      # Âmbito municipal
    "ESTADUAL",       # Âmbito estadual
    "NACIONAL",       # Âmbito nacional
]
