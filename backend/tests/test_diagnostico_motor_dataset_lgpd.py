# DATASET_LGPD extraído para uso compartilhado
# NÃO ADICIONE NENHUMA DEPENDÊNCIA DE TESTE OU PYTEST AQUI

DATASET_LGPD = [
    # (texto, contem_pii, descricao, categoria)
    ("Meu nome é João da Silva e meu CPF é 123.456.789-00", True, "Nome e CPF válidos", "documento"),
    ("O número do processo é 1234567-89.2020.8.07.0001", True, "Número de processo judicial", "processo"),
    ("Rua das Flores, 123, Brasília", False, "Endereço genérico sem PII", "endereco"),
    ("Maria comprou pão na padaria", False, "Frase sem PII", "outro"),
    ("Matrícula GDF: 12345678", True, "Matrícula funcional GDF", "matricula"),
    ("Telefone: (61) 99999-8888", True, "Telefone válido", "telefone"),
    ("Email: teste@exemplo.com", True, "Email válido", "email"),
    ("O valor da compra foi R$ 100,00", False, "Valor monetário sem PII", "financeiro"),
    ("RG: 1234567 SSP/DF", True, "RG válido", "documento"),
    ("Sem dados sensíveis aqui", False, "Frase neutra", "outro"),
]
