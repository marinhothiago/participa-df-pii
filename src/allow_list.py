# Lista de termos isolados que NUNCA devem ser considerados PII
ALLOW_LIST_TERMS = {
    # Órgãos, Siglas e Entidades
    "CGDF", "PMDF", "SEEDF", "SESDF", "SSP", "DETRAN", "BRB", "NOVACAP", "GDF",
    "PROCON", "MPDF", "MPSP", "SEI", "LAI", "ESIC", "GAMPES", "PREFEITURA", 
    "SECRETARIA", "MINISTÉRIO", "DEPARTAMENTO", "GOVERNO", "COORDENAÇÃO", 
    "DIRETORIA", "GERENCIA", "NÚCLEO", "FUNDAÇÃO", "AUTARQUIA", "CÂMARA", 
    "LEGISLATIVA", "TRIBUNAL", "JUSTIÇA", "PÚBLICO", "DISTRITO", "FEDERAL", 
    "MUNICIPAL", "CONTROLADORIA", "OUVIDORIA", "HOSPITAL", "UBS", "ESCOLA", "POLICIA",

    # Termos Jurídicos e Documentais
    "CONSTITUIÇÃO", "BOLETIM", "OCORRÊNCIA", "PROTOCOLO", "PROCESSO", "AUTOS", 
    "VALIDADOR", "CÓDIGO", "ASSUNTO", "DATA", "HORA", "REGISTRO", "INFORMAÇÃO", 
    "SOLICITAÇÃO", "IDENTIFICAÇÃO", "FALE", "CONOSCO",

    # Localidades e Logradouros
    "BRASÍLIA", "TAGUATINGA", "CEILÂNDIA", "TABOÃO", "SERRA", "HORTOLÂNDIA", 
    "SÃO", "PAULO", "RUA", "AVENIDA", "QUADRA", "LOTE", "BLOCO", "SETOR", 
    "BAIRRO", "CIDADE", "ESTADO", "COMPLEMENTO", "LOGRADOURO", "CEP", 
    "TRECHO", "CHÁCARA", "CONDOMÍNIO"
}

# Termos que, se aparecerem dentro de um nome detectado, invalidam esse nome (Filtro de Elite)
BLOCK_IF_CONTAINS = [
    "FEDERAL", "CONSTITUIÇÃO", "MINISTÉRIO", "PÚBLICO", "LEI", "DECRETO", 
    "PORTARIA", "MUNICIPAL", "ESTADUAL", "NACIONAL"
]