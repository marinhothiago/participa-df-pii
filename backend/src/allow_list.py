"""Configuração centralizada de termos e filtros para detecção de PII.

Versão: 9.4 - HACKATHON PARTICIPA-DF 2025

Este módulo é a ÚNICA FONTE DE VERDADE para listas de termos usados
pelo detector de PII. Todas as configurações de vocabulário estão aqui.

Listas disponíveis:
1. BLOCKLIST_TOTAL: Termos que NUNCA são PII (público por LAI)
2. TERMOS_SEGUROS: Termos institucionais/públicos do GDF
3. BLOCK_IF_CONTAINS: Palavras que invalidam um nome se encontradas nele
4. INDICADORES_SERVIDOR: Termos que indicam servidor público
5. CARGOS_AUTORIDADE: Cargos que conferem imunidade em contexto funcional
6. GATILHOS_CONTATO: Termos que ANULAM imunidade (indicam contato pessoal)
7. CONTEXTOS_PII: Contextos que indicam informação pessoal

Exemplos:
    - "Distrito Federal" → Não é PII (lugar)
    - "Lei Maria da Penha" → Não é PII (lei)
    - "Secretaria de Saúde" → Não é PII (instituição pública)
"""

from typing import Set, List, Dict

# ============================================================================
# BLOCKLIST_TOTAL: Termos que NUNCA são PII
# Unificação de ALLOW_LIST_TERMS + blocklist_total do detector
# ============================================================================

BLOCKLIST_TOTAL: Set[str] = {
    # ─────────────────────────────────────────────────────────────────────
    # Saudações e Formalidades
    # ─────────────────────────────────────────────────────────────────────
    "AGRADECO", "ATENCIOSAMENTE", "CORDIALMENTE", "RESPEITOSAMENTE",
    "BOM DIA", "BOA TARDE", "BOA NOITE", "PREZADOS", "PREZADO", "PREZADA",
    "ATENCIOSAMENTE", "CORDIAIS SAUDACOES", "RESPEITOSAMENTE",
    
    # ─────────────────────────────────────────────────────────────────────
    # Ações Administrativas
    # ─────────────────────────────────────────────────────────────────────
    "SOLICITO", "INFORMO", "ENCAMINHO", "DESPACHO", "PROCESSO", "AUTOS",
    "REQUERIMENTO", "PROTOCOLO", "MANIFESTACAO", "DEMANDA", "REQUEIRO",
    "AUTORIZO", "ACESSO", "INTEGRAL",
    
    # ─────────────────────────────────────────────────────────────────────
    # Tratamentos e Títulos Formais
    # ─────────────────────────────────────────────────────────────────────
    "DRA", "DR", "SR", "SRA", "PROF", "PROFESSOR", "PROFESSORA",
    "DOUTOR", "DOUTORA", "EXCELENTISSIMO", "EXCELENTISSIMA",
    "EXMO", "EXMA", "ILMO", "ILMA", "MM", "MERITISSIMO",
    "VOSSA SENHORIA", "VOSSA EXCELENCIA", "ILUSTRISSIMO",
    
    # ─────────────────────────────────────────────────────────────────────
    # Estrutura Organizacional
    # ─────────────────────────────────────────────────────────────────────
    "SECRETARIA", "DEPARTAMENTO", "DIRETORIA", "GERENCIA", "COORDENACAO",
    "SUPERINTENDENCIA", "SUBSECRETARIA", "ASSESSORIA", "GABINETE",
    "NUCLEO", "FUNDACAO", "AUTARQUIA", "CAMARA", "LEGISLATIVA",
    "TRIBUNAL", "JUSTICA", "CONTROLADORIA", "OUVIDORIA",
    
    # ─────────────────────────────────────────────────────────────────────
    # Termos Comuns em LAI
    # ─────────────────────────────────────────────────────────────────────
    "CIDADAO", "CIDADA", "REQUERENTE", "SOLICITANTE", "INTERESSADO",
    "DENUNCIANTE", "RECLAMANTE", "MANIFESTANTE",
    
    # ─────────────────────────────────────────────────────────────────────
    # Falsos Positivos de NER (parecem nomes mas não são)
    # ─────────────────────────────────────────────────────────────────────
    "MEU CPF", "MINHA CNH", "MEU RG", "MEU TELEFONE", "MEU EMAIL",
    "MEU ENDERECO", "MINHA IDENTIDADE", "MEU NOME", "MEU PIS",
    
    # ─────────────────────────────────────────────────────────────────────
    # Outros Termos Genéricos
    # ─────────────────────────────────────────────────────────────────────
    "LIGACOES", "TELEFONICAS", "MUDAS", "ILUMINACAO", "PUBLICA",
    "RECLAMACAO", "DENUNCIA", "ELOGIO", "SUGESTAO",
    "JANEIRO", "FEVEREIRO", "MARCO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
    
    # ─────────────────────────────────────────────────────────────────────
    # Órgãos e Siglas do GDF (Governo do Distrito Federal)
    # ─────────────────────────────────────────────────────────────────────
    "GDF", "PMDF", "PCDF", "CBMDF", "SEEDF", "SESDF", "SSP", "DETRAN",
    "BRB", "NOVACAP", "CGDF", "CLDF", "TCDF", "DODF", "SEI", "TERRACAP",
    "CAESB", "NEOENERGIA", "CEB", "METRO-DF", "METRO DF", "DFTRANS",
    "AGEFIS", "ADASA", "CODHAB", "EMATER", "FAPDF", "INESP",
    "PROCON", "MPDF", "MPSP", "LAI", "ESIC",
    
    # ─────────────────────────────────────────────────────────────────────
    # Instituições Públicas (NÃO são nomes de pessoas!)
    # ─────────────────────────────────────────────────────────────────────
    "ESCOLA", "ESCOLA CLASSE", "ESCOLA PARQUE", "CENTRO DE ENSINO",
    "CENTRO EDUCACIONAL", "CEF", "CEM", "CED", "EC", "EP",
    "HOSPITAL", "HOSPITAL REGIONAL", "HOSPITAL MATERNO", "HOSPITAL DE BASE",
    "HOSPITAL INFANTIL", "HOSPITAL UNIVERSITARIO", "HOSPITAL DE APOIO",
    "UBS", "UPA", "CENTRO DE SAUDE", "UNIDADE BASICA",
    "DELEGACIA", "BATALHAO", "CORPO DE BOMBEIROS", "QUARTEL",
    "CLASSE", "REGIONAL", "MATERNO", "INFANTIL", "BASE",
    "ADMINISTRACAO REGIONAL", "PREFEITURA",
    
    # ─────────────────────────────────────────────────────────────────────
    # Regiões Administrativas de Brasília (31 RAs)
    # ─────────────────────────────────────────────────────────────────────
    "BRASILIA", "PLANO PILOTO", "GAMA", "TAGUATINGA", "BRAZLANDIA",
    "SOBRADINHO", "PLANALTINA", "PARANOA", "NUCLEO BANDEIRANTE",
    "CEILANDIA", "GUARA", "CRUZEIRO", "SAMAMBAIA", "SANTA MARIA",
    "SAO SEBASTIAO", "RECANTO DAS EMAS", "LAGO SUL", "LAGO NORTE",
    "CANDANGOLANDIA", "RIACHO FUNDO", "SUDOESTE", "OCTOGONAL",
    "VARJAO", "PARK WAY", "SCIA", "ESTRUTURAL", "JARDIM BOTANICO",
    "ITAPOA", "SIA", "VICENTE PIRES", "FERCAL", "SOL NASCENTE",
    "POR DO SOL", "ARNIQUEIRA", "AGUAS CLARAS",
    
    # ─────────────────────────────────────────────────────────────────────
    # Endereços Administrativos de Brasília
    # ─────────────────────────────────────────────────────────────────────
    "ASA SUL", "ASA NORTE", "EIXO MONUMENTAL", "ESPLANADA DOS MINISTERIOS",
    "W3", "L2", "SQS", "SQN", "SRES", "SHIS", "SHIN", "SHLN", "SGAS", "SGAN",
    "SRTVS", "SRTVN", "SCN", "SCS", "SBS", "SBN", "SDN", "SDS", "SCLN", "EQ", "SRV",
    
    # ─────────────────────────────────────────────────────────────────────
    # Tribunais e Órgãos Federais em Brasília
    # ─────────────────────────────────────────────────────────────────────
    "STF", "STJ", "TST", "TSE", "STM", "TJDFT", "TRF1", "TRT10",
    "MPF", "MPDFT", "DPU", "AGU", "CGU", "TCU", "SENADO", "CAMARA",
    "CONGRESSO NACIONAL", "SUPREMO TRIBUNAL",
    
    # ─────────────────────────────────────────────────────────────────────
    # Lugares e Edificações
    # ─────────────────────────────────────────────────────────────────────
    "DISTRITO FEDERAL", "CENTRO ADMINISTRATIVO", "CENTRO METROPOLITANO",
    "PLANALTO CENTRAL", "PRACA DOS TRES PODERES", "PALACIO DO PLANALTO",
    
    # ─────────────────────────────────────────────────────────────────────
    # Universidades e Instituições de Ensino
    # ─────────────────────────────────────────────────────────────────────
    "UNIVERSIDADE DE BRASILIA", "UNB", "UFRJ", "USP", "UNICAMP", "UCB",
    "UFMG", "UFRGS", "UFSC", "UFPR", "UFG", "UFBA",
    
    # ─────────────────────────────────────────────────────────────────────
    # Termos Jurídicos e Documentais
    # ─────────────────────────────────────────────────────────────────────
    "CONSTITUICAO", "BOLETIM", "OCORRENCIA", "VALIDADOR",
    "CODIGO", "ASSUNTO", "DATA", "HORA", "REGISTRO", "INFORMACAO",
    "SOLICITACAO", "IDENTIFICACAO", "FALE CONOSCO",
    
    # ─────────────────────────────────────────────────────────────────────
    # Termos de Localização Geográfica
    # ─────────────────────────────────────────────────────────────────────
    "RUA", "AVENIDA", "QUADRA", "LOTE", "BLOCO", "SETOR", "BAIRRO",
    "CIDADE", "ESTADO", "COMPLEMENTO", "LOGRADOURO", "CEP",
    "TRECHO", "CHACARA", "CONDOMINIO",
    
    # ─────────────────────────────────────────────────────────────────────
    # Parâmetros de Qualidade da Água / Termos Técnicos
    # ─────────────────────────────────────────────────────────────────────
    "FOSFORO TOTAL", "NITROGENIO TOTAL", "NITROGENIO AMONIACAL",
    "OXIGENIO DISSOLVIDO", "SOLIDOS TOTAIS", "SOLIDOS SUSPENSOS",
    "SOLIDOS DISSOLVIDOS", "TEMPERATURA DA AMOSTRA", "DEMANDA BIOQUIMICA",
    "DBO", "DQO", "PH", "TURBIDEZ", "COLIFORMES",
    "CARBONO ORGANICO", "CLORETO", "SULFATO", "NITRATO", "FOSFATO", "AMONIA",
    
    # ─────────────────────────────────────────────────────────────────────
    # Leis e Referências Legais
    # ─────────────────────────────────────────────────────────────────────
    "LEI MARIA DA PENHA", "LEI DE ACESSO A INFORMACAO",
    "LEI GERAL DE PROTECAO DE DADOS", "LGPD",
    "ESTATUTO DA CRIANCA", "ESTATUTO DO IDOSO",
    "ESTATUTO DA ORDEM DOS ADVOGADOS",
    "CODIGO CIVIL", "CODIGO PENAL", "CODIGO DE PROCESSO",
    "CONSTITUICAO FEDERAL", "NOSSA CONSTITUICAO", "CLT",
    
    # ─────────────────────────────────────────────────────────────────────
    # Cargos e Profissões (não identificam pessoa específica)
    # ─────────────────────────────────────────────────────────────────────
    "RESIDENTE DE SAUDE", "RESIDENTE DE MEDICINA", "RESIDENTE DE ENFERMAGEM",
    "RESIDENTE DE SAUDE COLETIVA", "CARREIRAS MAGISTERIO", "CARREIRA MAGISTERIO",
    "ASSISTENCIA A EDUCACAO", "POLITICAS PUBLICAS", "GESTOR PPGG",
    
    # ─────────────────────────────────────────────────────────────────────
    # Organizações e Entidades (não são pessoas físicas)
    # ─────────────────────────────────────────────────────────────────────
    "ADVOGADOS ASSOCIADOS", "ESCRITORIO DE ADVOCACIA",
    "CONSELHO REGIONAL", "CONSELHO FEDERAL", "ORDEM DOS ADVOGADOS",
    "OAB", "CRM", "CREA", "CRO",
    "EMPREENDIMENTOS IMOBILIARIOS", "CONDOMINIO MUNICIPAL",
    "COOPERATIVAS FINANCEIRAS", "SICOOB", "ASSOCIACAO DE ENSINO",
    
    # ─────────────────────────────────────────────────────────────────────
    # Termos de Sistema
    # ─────────────────────────────────────────────────────────────────────
    "LIGACOES TELEFONICAS", "VALIDADOR MPSP",
    "SETOR DE RECURSOS HIDRICOS", "RECURSOS HIDRICOS",
    "INCISO XV", "INCISO II", "INCISO I", "PARAGRAFO UNICO", "ARTIGO", "ALINEA",
    
    # ─────────────────────────────────────────────────────────────────────
    # Doenças Epônimas (nomes próprios que são doenças, não pessoas)
    # ─────────────────────────────────────────────────────────────────────
    "HUNTINGTON", "PARKINSON", "ALZHEIMER", "CROHN", "HODGKIN",
    "KAWASAKI", "TOURETTE", "ADDISON", "CUSHING", "GRAVES",
    "HASHIMOTO", "MENIERE", "RAYNAUD", "SJOGREN", "WILSON",
    "CHAGAS", "HANSEN", "BASEDOW", "BELL", "DOWN",
}


# ============================================================================
# TERMOS_SEGUROS: Termos institucionais/públicos (match parcial permitido)
# Usado para verificar se termo está CONTIDO em outro
# ============================================================================

TERMOS_SEGUROS: Set[str] = {
    # Órgãos do GDF
    "GDF", "PMDF", "PCDF", "CBMDF", "SEEDF", "SESDF", "SSP", "DETRAN",
    "BRB", "NOVACAP", "CGDF", "CLDF", "TCDF", "DODF", "SEI", "TERRACAP",
    "CAESB", "NEOENERGIA", "CEB", "METRO-DF", "METRO DF", "DFTRANS",
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
    "MPF", "MPDFT", "DPU", "AGU", "CGU", "TCU", "SENADO", "CAMARA",
    
    # Lugares conhecidos
    "DISTRITO FEDERAL", "CENTRO ADMINISTRATIVO", "CENTRO METROPOLITANO",
}


# ============================================================================
# BLOCK_IF_CONTAINS: Palavras que invalidam um nome se encontradas DENTRO dele
# Se qualquer uma dessas aparecer no nome detectado, não é PII
# ============================================================================

BLOCK_IF_CONTAINS: List[str] = [
    # Referências legais
    "FEDERAL", "CONSTITUICAO", "MINISTERIO", "PUBLICO", "LEI",
    "DECRETO", "PORTARIA", "MUNICIPAL", "ESTADUAL", "NACIONAL",
    "ESTATUTO", "INCISO", "ARTIGO", "PARAGRAFO",
    
    # Organizações/Empresas
    "ADVOGADOS", "ASSOCIADOS", "LTDA", "S/A", "ME", "EPP", "EIRELI",
    "EMPREENDIMENTOS", "CONDOMINIO", "RESIDENCIAL", "SHOPPING",
    "COOPERATIVAS", "ASSOCIACAO",
    
    # Instituições de ensino
    "UNIVERSIDADE", "FACULDADE", "INSTITUTO", "ESCOLA", "CENTRO DE ENSINO",
    
    # Termos técnicos
    "TOTAL", "DISSOLVIDO", "AMONIACAL", "ORGANICO",
    
    # Cargos/funções
    "CARREIRAS", "RESIDENTE DE", "GESTOR PPGG", "CONTROLADORIA", "VALIDADOR",
    
    # Lugares
    "DISTRITO FEDERAL", "CENTRO ADMINISTRATIVO",
    
    # Órgãos
    "SECRETARIA", "TRIBUNAL", "MINISTERIO",
]


# ============================================================================
# INDICADORES_SERVIDOR: Termos que indicam servidor público
# ============================================================================

INDICADORES_SERVIDOR: Set[str] = {
    "SERVIDOR", "SERVIDORA", "FUNCIONARIO", "FUNCIONARIA",
    "ANALISTA", "TECNICO", "AUDITOR", "FISCAL",
    "PERITO", "DELEGADO", "DELEGADA", "ADMINISTRADOR", "ADMINISTRADORA",
    "COORDENADOR", "COORDENADORA", "DIRETOR", "DIRETORA",
    "SECRETARIO", "SECRETARIA",
    "AGENTE", "MEDICO", "MEDICA",
    "ASSESSOR", "ASSESSORA", "CHEFE", "GERENTE",
    "SUPERINTENDENTE", "SUBSECRETARIO", "SUBSECRETARIA",
}


# ============================================================================
# CARGOS_AUTORIDADE: Cargos que conferem imunidade em contexto funcional
# ============================================================================

CARGOS_AUTORIDADE: Set[str] = {
    "DRA", "DR", "SR", "SRA", "PROF", "DOUTOR", "DOUTORA",
    "EXMO", "EXMA", "ILMO", "ILMA", "MM", "MERITISSIMO",
}


# ============================================================================
# GATILHOS_CONTATO: Termos que ANULAM imunidade (indicam contato pessoal)
# ============================================================================

GATILHOS_CONTATO: Set[str] = {
    "FALAR COM", "TRATAR COM", "LIGAR PARA", "CONTATO COM",
    "TELEFONE DO", "TELEFONE DA", "CELULAR DO", "CELULAR DA",
    "WHATSAPP DO", "WHATSAPP DA", "EMAIL DO", "EMAIL DA",
    "FALAR COM O", "FALAR COM A", "CONTATO DO", "CONTATO DA",
    "PROCURAR", "CHAMAR", "AVISAR", "COMUNICAR COM",
    "ENDERECO DO", "ENDERECO DA", "RESIDENCIA DO", "RESIDENCIA DA",
    "CASA DO", "CASA DA", "MORA NA", "MORA NO", "RESIDE NA", "RESIDE NO",
    # Gatilhos para servidores identificados
    "CONTATO:", "SERVIDOR", "SERVIDORA", "SR.", "SRA.", "SENHOR", "SENHORA",
    "DIRETOR", "DIRETORA", "DADOS DO", "DADOS DA", "SOLICITO DADOS",
    "IDENTIFICADO COMO", "CIDADAO", "CIDADA",
}


# ============================================================================
# CONTEXTOS_PII: Contextos que indicam informação pessoal
# ============================================================================

CONTEXTOS_PII: Set[str] = {
    "MEU CPF", "MINHA IDENTIDADE", "MEU RG", "MINHA CNH",
    "MEU TELEFONE", "MEU CELULAR", "MEU EMAIL", "MEU E-MAIL",
    "MORO NA", "MORO NO", "RESIDO NA", "RESIDO NO",
    "MEU ENDERECO", "MINHA RESIDENCIA", "MINHA CASA",
    "MEU NOME COMPLETO", "ME CHAMO", "MEU NOME E",
    "MINHA CONTA", "MINHA AGENCIA", "MEU BANCO",
    "MEU PASSAPORTE", "MEU TITULO", "MEU PIS", "MEU NIT",
}


# ============================================================================
# PESOS_PII: Pesos por tipo de PII (baseado em categorias LGPD)
# ============================================================================

PESOS_PII: Dict[str, int] = {
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


# ============================================================================
# CONFIANCA_BASE: Confiança base por tipo de PII
# ============================================================================

CONFIANCA_BASE: Dict[str, float] = {
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
    "TELEFONE_INTERNACIONAL": 0.90,  # DDI de outros países (+1, +351, +54, etc.)
    "PLACA_VEICULO": 0.88,
    "PIX": 0.88,
    "RG": 0.85,
    "PASSAPORTE": 0.85,
    "ENDERECO_RESIDENCIAL": 0.85,
    "CONTA_BANCARIA": 0.85,
    "CERTIDAO": 0.85,
    "REGISTRO_PROFISSIONAL": 0.85,
    
    # LGPD - Dados Sensíveis
    "DADO_SAUDE": 0.95,
    "DADO_BIOMETRICO": 0.95,
    "MENOR_IDENTIFICADO": 0.95,
    
    # Identificadores funcionais
    "MATRICULA": 0.88,
    
    # Regex com dependência de contexto
    "CEP": 0.75,
    "DATA_NASCIMENTO": 0.70,
    
    # NER
    "NOME_BERT": 0.00,  # Usa score do modelo
    "NOME_SPACY": 0.70,
    "NOME_GATILHO": 0.85,
    "NOME": 0.82,
    
    # Dados de identificação indireta (Risco BAIXO)
    "IP_ADDRESS": 0.75,
    "COORDENADAS_GEO": 0.80,
    "USER_AGENT": 0.70,
}


# ============================================================================
# Exportar nomes alternativos para compatibilidade
# ============================================================================

# Alias para manter compatibilidade com código legado
ALLOW_LIST_TERMS = BLOCKLIST_TOTAL
