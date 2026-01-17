
import pytest
from src.detector import PIIDetector

detector = PIIDetector()

# Formato: (texto, contem_pii, descricao, categoria)
DATASET_LGPD = [
DATASET_LGPD: List[Tuple[str, bool, str, str]] = [
detector = PIIDetector()

# Teste unitário parametrizado para todo o dataset
@pytest.mark.parametrize("texto, contem_pii, descricao, categoria", DATASET_LGPD)
def test_pii_detector_dataset(texto, contem_pii, descricao, categoria):
    resultado, findings, risco, confianca = detector.detect(texto)
    assert resultado == contem_pii, f"Texto: {texto}\nDescrição: {descricao}\nCategoria: {categoria}\nEsperado: {contem_pii}\nObtido: {resultado}"
    
    # =========================================================================
    # GRUPO 1: TEXTOS REAIS DO e-SIC SEM PII (esperado: False)
    # =========================================================================
    ("Solicito cópia do cadastro que preenchi virtualmente solicitando a transferência de titularidade.", False, "Solicitação genérica cadastro", "e-SIC Real"),
    ("Gostaria de saber se irão implementar o reajuste no auxílio saúde.", False, "Pergunta sobre benefício", "e-SIC Real"),
    ("Prezados senhores, boa tarde! Solicito acesso integral aos autos do Processo SEI 00015-01009853/2026-01.", False, "Solicitação processo SEI", "e-SIC Real"),
    ("Solicito acesso a um laudo de adicional de periculosidade pago atualmente a um servidor.", False, "Solicitação laudo genérico", "e-SIC Real"),
    ("Gostaria de saber se a legislação que reduziu o ITBI é válida somente até 31/03/2025.", False, "Pergunta legislação", "e-SIC Real"),
    ("Solicito o quantitativo de penalidades administrativas/disciplinares aplicadas a servidores militares.", False, "Solicitação estatística", "e-SIC Real"),
    ("Bom dia!! Gostaria de uma fiscalização nas calçadas na SHDF 602 - 607, blocos R U J C F.", False, "Solicitação fiscalização", "e-SIC Real"),
    ("Isenção de imposto de renda para aposentado da SES-DF. Tratamento realizado de câncer.", False, "Solicitação isenção genérica", "e-SIC Real"),
    ("Quais são os contratos firmados pela Secretaria de Educação em 2022?", False, "Solicitação LAI contratos", "e-SIC Real"),
    ("Lista de escolas públicas do GDF.", False, "Solicitação lista escolas", "e-SIC Real"),
    ("Solicito informações sobre o perfil do cidadão acometido pela doença de Huntington no DF.", False, "Solicitação dados epidemiológicos", "e-SIC Real"),
    ("Respeitosamente, solicitam-se informações sobre Funções de Integridade.", False, "Solicitação integridade", "e-SIC Real"),
    ("Houve instituição do Programa de Integridade no Órgão/Entidade?", False, "Pergunta programa integridade", "e-SIC Real"),
    ("Quais são as empresas contratadas para merenda escolar?", False, "Solicitação LAI empresas", "e-SIC Real"),
    ("Qual o valor gasto com merenda escolar em 2025?", False, "Solicitação LAI valores", "e-SIC Real"),
    
    # =========================================================================
    # GRUPO 2: TEXTOS REAIS DO e-SIC COM PII (esperado: True)
    # =========================================================================
    # Casos REAIS extraídos da amostra - contêm dados pessoais identificáveis
    
    ("Venho solicitar junto a Caesb o histórico de consumo da inscrição:157028-1, sob o CPF: 129.180.122-6, Júlio Cesar Alves da Rosa.", True, "CPF + Nome real e-SIC", "e-SIC Real PII"),
    ("Histórico de consumo da Inscrição: 00569848-9, sob o CPF: 210.201.140-24, Maria Martins Mota Silva.", True, "CPF + Nome real e-SIC", "e-SIC Real PII"),
    ("Meus dados: Ruth Helena Franco CPF: 110.100.179-87 Tel. (54)99199-1000", True, "Dados pessoais completos e-SIC", "e-SIC Real PII"),
    ("Dr Joaquim fui orientada sobre a existência de dados abertos. Antonio Costa Gestor PPGG 21-1205-1999", True, "Nome + telefone e-SIC", "e-SIC Real PII"),
    ("Lúcio Miguel - MATRÍCULA 12345678 (TUTOR EDUCACAO SUPERIOR A15)", True, "Nome + matrícula e-SIC", "e-SIC Real PII"),
    ("Leonardo Rocha - MATRÍCULA 98745632D (PROF. EDUCACAO SUPERIOR F16)", True, "Nome + matrícula e-SIC", "e-SIC Real PII"),
    ("Declaração de exercício findo da servidora AURA Costa Mota (matrícula 98.123-3)", True, "Nome + matrícula e-SIC", "e-SIC Real PII"),
    ("Jorge Luiz Pereira Vieira, brasileiro, solteiro, advogado inscrito na OAB/SP sob nº 14.123, inscrito no CPF 101.000.800-73", True, "Dados pessoais completos e-SIC", "e-SIC Real PII"),
    ("E-mail: netolemos@me.pe Aplicativo de mensagem WhatsApp: 89 34180-1890", True, "Email + WhatsApp e-SIC", "e-SIC Real PII"),
    ("Meu nome é Walter Rodrigues Cruz. No dia 25 de setembro de 2019 solicitei...", True, "Nome completo e-SIC", "e-SIC Real PII"),
    ("O servidor da TCB responsável pelo projeto era o Sr. Antonio Vasconcelos.", True, "Nome servidor mencionado", "e-SIC Real PII"),
    ("Sou inquilina do imóvel localizado na CRN 104 Bloco I loja 15, em frente à L3 sul", True, "Endereço específico e-SIC", "e-SIC Real PII"),
    
        # =========================================================================
        # GRUPO EXTRA: PADRÕES GDF (esperado: True)
        # =========================================================================
        ("Processo SEI 12345-1234567/2024-12", True, "Processo SEI padrão GDF", "PADRÕES_GDF"),
        ("Referência SEI 54321-7654321/2023-01", True, "Processo SEI referência", "PADRÕES_GDF"),
        ("Protocolo LAI LAI-123456/2024", True, "Protocolo LAI padrão GDF", "PADRÕES_GDF"),
        ("Protocolo OUV OUV-654321/2022", True, "Protocolo OUV padrão GDF", "PADRÕES_GDF"),
        ("Matrícula do servidor: 98.123-3", True, "Matrícula servidor formato 1", "PADRÕES_GDF"),
        ("Matrícula funcional: 12345678A", True, "Matrícula servidor formato 2", "PADRÕES_GDF"),
        ("Ocorrência policial: 2012345678901234", True, "Ocorrência policial padrão GDF", "PADRÕES_GDF"),
        ("Inscrição do imóvel: inscrição:1234567", True, "Inscrição imóvel padrão GDF", "PADRÕES_GDF"),
    
        # Edge cases (esperado: False)
        ("O número 12345-1234567/2024-12 não é um processo SEI válido", False, "Processo SEI contexto negativo", "PADRÕES_GDF"),
        ("Meu telefone é 12345-1234567", False, "Número similar a SEI mas contexto telefone", "PADRÕES_GDF"),
        ("LAI-123456/2024 é só um exemplo, não é protocolo", False, "Protocolo LAI contexto exemplo", "PADRÕES_GDF"),
        ("OUV-654321/2022 é só referência, não protocolo", False, "Protocolo OUV contexto exemplo", "PADRÕES_GDF"),
        ("Matrícula: 123456", False, "Matrícula servidor incompleta", "PADRÕES_GDF"),
        ("Ocorrência: 20123456789012", False, "Ocorrência policial incompleta", "PADRÕES_GDF"),
        ("Inscrição: 12345", False, "Inscrição imóvel incompleta", "PADRÕES_GDF"),
    
    # =========================================================================
    # GRUPO 3: CPF - VÁLIDO E COM ERROS DE DIGITAÇÃO (LGPD: todos são PII)
    # =========================================================================
    # CPFs válidos matematicamente
    ("Meu CPF é 529.982.247-25", True, "CPF válido com possessivo", "CPF Válido"),
    ("CPF: 111.444.777-35", True, "CPF válido com label", "CPF Válido"),
    ("O contribuinte de CPF 123.456.789-09 solicitou...", True, "CPF válido em contexto", "CPF Válido"),
    ("Cadastro sob CPF nº 987.654.321-00", True, "CPF válido formal", "CPF Válido"),
    
    # CPFs com ERROS DE DIGITAÇÃO - AINDA SÃO PII pela LGPD!
    ("Meu CPF é 123.456.789-00", True, "CPF com DV errado - AINDA É PII", "CPF Erro Digitação"),
    ("CPF: 529.982.247-26", True, "CPF com DV errado por 1 dígito", "CPF Erro Digitação"),
    ("Informo meu CPF 12345678909", True, "CPF sem formatação", "CPF Erro Digitação"),
    ("CPF do requerente: 123456789-09", True, "CPF formatação parcial", "CPF Erro Digitação"),
    ("O CPF 129.180.122-6 precisa ser verificado", True, "CPF com dígito faltando (real e-SIC)", "CPF Erro Digitação"),
    ("CPF: 210.201.140-24 conforme cadastro", True, "CPF formato real e-SIC", "CPF Erro Digitação"),
    
    # CPFs claramente FICTÍCIOS/EXEMPLO - NÃO são PII
    ("Exemplo de CPF: 000.000.000-00", False, "CPF exemplo zeros", "CPF Fictício"),
    ("CPF fictício para teste: 111.111.111-11", False, "CPF repetido fictício", "CPF Fictício"),
    ("O formato do CPF é XXX.XXX.XXX-XX", False, "Formato explicativo", "CPF Fictício"),
    ("CPF inválido informado: 999.999.999-99", False, "CPF contexto inválido explícito", "CPF Fictício"),
    
    # =========================================================================
    # GRUPO 4: CNH - VÁLIDA E COM ERROS (LGPD: todos são PII)
    # =========================================================================
    ("CNH: 12345678901", True, "CNH 11 dígitos válida", "CNH Válida"),
    ("Minha carteira de motorista: 98765432100", True, "CNH formato sem separador", "CNH Válida"),
    ("Habilitação nº 01234567890", True, "CNH com label habilitação", "CNH Válida"),
    
    # CNH com erros de digitação - AINDA SÃO PII
    ("CNH: 1234567890", True, "CNH 10 dígitos (erro digitação) - AINDA É PII", "CNH Erro Digitação"),
    ("Minha CNH é 0987654321", True, "CNH 10 dígitos com possessivo - AINDA É PII", "CNH Erro Digitação"),
    ("O documento de identificação é o CNH 9876543210", True, "CNH 10 dígitos em contexto - AINDA É PII", "CNH Erro Digitação"),
    ("CNH 123456789012", True, "CNH 12 dígitos (digitou a mais) - AINDA É PII", "CNH Erro Digitação"),
    
    # =========================================================================
    # GRUPO 5: RG - VÁRIOS FORMATOS (LGPD: todos são PII)
    # =========================================================================
    ("RG: 1234567 SSP-DF", True, "RG com órgão emissor", "RG"),
    ("Minha identidade é RG 3.123.456 SSP/DF", True, "RG formato pontilhado", "RG"),
    ("RG nº 1.234.567-8 expedido pela SSP/DF", True, "RG completo", "RG"),
    ("Documento de identidade: 12345678", True, "RG sem formatação", "RG"),
    ("RG 123456-7 DETRAN-DF", True, "RG DETRAN", "RG"),
    
    # =========================================================================
    # GRUPO 6: TELEFONE - VÁRIOS FORMATOS (LGPD: pessoais são PII)
    # =========================================================================
    # Telefones PESSOAIS - são PII
    ("Meu telefone é (61) 99999-8888", True, "Celular com possessivo", "Telefone Pessoal"),
    ("Contato pessoal: 61 98765-4321", True, "Celular pessoal explícito", "Telefone Pessoal"),
    ("Ligar para +55 11 91234-5678", True, "Celular com DDI", "Telefone Pessoal"),
    ("WhatsApp: 61999887766", True, "WhatsApp sem formatação", "Telefone Pessoal"),
    ("Meu celular é 61 99988-7766, falar com José", True, "Celular + nome", "Telefone Pessoal"),
    ("Tel. (54)99199-1000", True, "Telefone formato real e-SIC", "Telefone Pessoal"),
    ("WhatsApp: 89 34180-1890", True, "WhatsApp formato real e-SIC", "Telefone Pessoal"),
    ("Telefone para retorno: (61) 98123-4567", True, "Telefone para contato", "Telefone Pessoal"),
    
    # Telefones com erros de formatação - AINDA SÃO PII
    ("Meu tel 6199998888", True, "Celular sem formatação", "Telefone Erro Formato"),
    ("Ligar 61-99999-8888", True, "Celular hífen errado", "Telefone Erro Formato"),
    ("Celular: (61)999998888", True, "Celular sem hífen interno", "Telefone Erro Formato"),
    ("Fone: 061 99999 8888", True, "Celular com DDD 0", "Telefone Erro Formato"),
    
    # Telefones INSTITUCIONAIS - NÃO são PII pessoal
    ("Telefone institucional: (61) 3105-1234", False, "Fixo institucional explícito", "Telefone Institucional"),
    ("Ligue para a ouvidoria: 0800 644 9100", False, "0800 institucional", "Telefone Institucional"),
    ("SAC: 4003-1234", False, "SAC comercial", "Telefone Institucional"),
    ("Central de atendimento: (61) 3312-5000", False, "Central institucional", "Telefone Institucional"),
    ("Disque 190 para emergências", False, "Número emergência", "Telefone Institucional"),
    ("Ramal: 1234", False, "Ramal interno", "Telefone Institucional"),
    
    # =========================================================================
    # GRUPO 7: EMAIL (LGPD: pessoais são PII)
    # =========================================================================
    # Emails PESSOAIS - são PII
    ("Email: joao.silva@gmail.com", True, "Gmail pessoal", "Email Pessoal"),
    ("Contato: maria_santos@hotmail.com", True, "Hotmail pessoal", "Email Pessoal"),
    ("Meu email é pedro123@yahoo.com.br", True, "Yahoo pessoal", "Email Pessoal"),
    ("E-mail: netolemos@me.pe", True, "Email real e-SIC", "Email Pessoal"),
    ("ana.costa@outlook.com para resposta", True, "Outlook pessoal", "Email Pessoal"),
    ("Enviar para carlos_alves@live.com", True, "Live pessoal", "Email Pessoal"),
    
    # Emails INSTITUCIONAIS - NÃO são PII pessoal
    ("Email institucional: ouvidoria@saude.df.gov.br", False, "Gov.br institucional", "Email Institucional"),
    ("Contato: atendimento@seedf.df.gov.br", False, "SEEDF institucional", "Email Institucional"),
    ("sic@cgdf.df.gov.br para solicitações", False, "SIC institucional", "Email Institucional"),
    ("faleconosco@detran.df.gov.br", False, "DETRAN institucional", "Email Institucional"),
    
    # =========================================================================
    # GRUPO 8: NOMES PRÓPRIOS (LGPD: são PII)
    # =========================================================================
    # Nomes com sobrenome - claramente PII
    ("Júlio Cesar Alves da Rosa solicitou acesso", True, "Nome completo 4 partes", "Nome Completo"),
    ("Maria Martins Mota Silva é a titular", True, "Nome completo 4 partes", "Nome Completo"),
    ("Ruth Helena Franco compareceu", True, "Nome completo 3 partes", "Nome Completo"),
    ("Jorge Luiz Pereira Vieira requer", True, "Nome completo 4 partes", "Nome Completo"),
    ("Walter Rodrigues Cruz informou", True, "Nome completo 3 partes", "Nome Completo"),
    ("O servidor Antonio Vasconcelos atendeu", True, "Nome servidor", "Nome Completo"),
    ("Dr Joaquim orientou sobre o procedimento", True, "Nome com título", "Nome Completo"),
    ("Antonio Costa, Gestor do PPGG", True, "Nome + cargo", "Nome Completo"),
    ("A paciente Ana Beatriz Silva aguarda", True, "Nome paciente", "Nome Completo"),
    ("Leonardo Rocha é o professor responsável", True, "Nome professor", "Nome Completo"),
    ("AURA Costa Mota solicitou declaração", True, "Nome em maiúsculas", "Nome Completo"),
    ("Lúcio Miguel atua como tutor", True, "Nome 2 partes", "Nome Completo"),
    
    # Nomes em contexto de identificação - PII mesmo com 1 nome
    ("A testemunha se identificou como Margarida Souza", True, "Nome testemunha", "Nome Contexto"),
    ("O denunciante, José Carlos, relatou", True, "Nome denunciante", "Nome Contexto"),
    ("Vítima: Ana Paula conforme B.O.", True, "Nome vítima", "Nome Contexto"),
    ("Responsável legal: Pedro Henrique", True, "Nome responsável", "Nome Contexto"),
    ("Falar com Sr. Roberto da Silva", True, "Nome para contato", "Nome Contexto"),
    ("Ligar para Fernanda Oliveira", True, "Nome gatilho contato", "Nome Contexto"),
    
    # Nomes genéricos/parciais SEM contexto identificador - NÃO são PII
    ("Silva é um sobrenome comum", False, "Sobrenome isolado", "Nome Genérico"),
    ("Atender cliente João", False, "Nome único genérico", "Nome Genérico"),
    ("Prezado Pedro, bom dia", False, "Nome em saudação", "Nome Genérico"),
    
    # =========================================================================
    # GRUPO 9: ENDEREÇOS (LGPD: residenciais são PII)
    # =========================================================================
    # Endereços RESIDENCIAIS - são PII
    ("Moro na QI 25 Conjunto 10 Casa 15, Guará", True, "Endereço residencial Guará", "Endereço Residencial"),
    ("Meu endereço: SQN 315 Bloco A Apt 201", True, "Endereço SQN com apto", "Endereço Residencial"),
    ("Resido na QR 308 Conjunto 5 Casa 20", True, "Endereço QR residencial", "Endereço Residencial"),
    ("Endereço: Rua das Flores, 123, Apt 45, Taguatinga", True, "Endereço rua completo", "Endereço Residencial"),
    ("Minha casa fica na SHIS QI 15 Conjunto 8 Casa 10", True, "Endereço SHIS residencial", "Endereço Residencial"),
    ("CRN 104 Bloco I loja 15, em frente à L3 sul", True, "Endereço comercial específico (real e-SIC)", "Endereço Residencial"),
    ("Moro no Condomínio Solar, Bloco B, Apto 302", True, "Endereço condomínio", "Endereço Residencial"),
    
    # Endereços PÚBLICOS/INSTITUCIONAIS - NÃO são PII
    ("Endereço da Secretaria: SBS Quadra 02 Bloco E", False, "Endereço institucional", "Endereço Institucional"),
    ("Hospital Regional da Asa Norte, SMHN", False, "Hospital público", "Endereço Institucional"),
    ("Escola Classe 15 de Ceilândia", False, "Escola pública", "Endereço Institucional"),
    ("Administração Regional de Taguatinga", False, "Órgão público", "Endereço Institucional"),
    ("SHDF 602 - 607, blocos R U J C F", False, "Setor público genérico", "Endereço Institucional"),
    
    # =========================================================================
    # GRUPO 10: DADOS FINANCEIROS/BANCÁRIOS (LGPD: são PII sensíveis)
    # =========================================================================
    ("Conta: 12345-6 Ag: 1234 Banco do Brasil", True, "Conta bancária completa", "Dados Bancários"),
    ("PIX CPF: 529.982.247-25", True, "Chave PIX CPF", "Dados Bancários"),
    ("Chave PIX: email@pessoal.com", True, "Chave PIX email", "Dados Bancários"),
    ("PIX telefone: 61999998888", True, "Chave PIX telefone", "Dados Bancários"),
    ("Cartão final 4532", True, "Final cartão", "Dados Bancários"),
    ("Agência 0001 Conta corrente 123456-7", True, "Dados bancários", "Dados Bancários"),
    
    # =========================================================================
    # GRUPO 11: MATRÍCULA FUNCIONAL (contexto específico GDF)
    # =========================================================================
    ("Matrícula 12345678 do servidor", True, "Matrícula servidor", "Matrícula"),
    ("MATRÍCULA 98745632D", True, "Matrícula com letra", "Matrícula"),
    ("Servidor de matrícula 98.123-3", True, "Matrícula formato ponto", "Matrícula"),
    ("O funcionário mat. 1234567 solicitou", True, "Matrícula abreviada", "Matrícula"),
    
    # =========================================================================
    # GRUPO 12: IMUNIDADE FUNCIONAL - AGENTES EM EXERCÍCIO (esperado: False)
    # =========================================================================
    # Servidores em contexto de função pública - NÃO são PII pessoal
    ("O secretário de Educação informou que...", False, "Cargo público", "Imunidade Cargo"),
    ("A diretora da escola comunicou...", False, "Cargo público", "Imunidade Cargo"),
    ("Conforme despacho do Subsecretário...", False, "Cargo público", "Imunidade Cargo"),
    ("O diretor do DETRAN esclareceu...", False, "Cargo público", "Imunidade Cargo"),
    ("A coordenadora do setor responsável...", False, "Cargo público", "Imunidade Cargo"),
    ("O servidor responsável pelo atendimento informou...", False, "Servidor em função", "Imunidade Função"),
    ("A funcionária do protocolo orientou...", False, "Funcionário em função", "Imunidade Função"),
    ("O agente público que nos atendeu...", False, "Agente em função", "Imunidade Função"),
    ("O funcionário do mês foi parabenizado", False, "Contexto de elogio", "Imunidade Elogio"),
    ("A servidora da Secretaria de Saúde do GDF", False, "Servidor + instituição", "Imunidade Instituição"),
    ("Dr. Carlos, chefe do departamento de TI", False, "Título + cargo", "Imunidade Cargo"),
    ("A Dra. Maria Oliveira da Secretaria de Saúde informou", False, "Título + instituição pública", "Imunidade Instituição"),
    
    # Quebra de imunidade - GATILHOS DE CONTATO tornam PII
    ("Falar com José Carlos da Secretaria", True, "Gatilho 'falar com'", "Quebra Imunidade"),
    ("Ligar para Ana Paula do DETRAN", True, "Gatilho 'ligar para'", "Quebra Imunidade"),
    ("Contato: Pedro Henrique, servidor do GDF", True, "Gatilho 'contato'", "Quebra Imunidade"),
    ("Entre em contato com Maria Silva", True, "Gatilho 'entre em contato'", "Quebra Imunidade"),
    
    # =========================================================================
    # GRUPO 13: DADOS SENSÍVEIS LGPD Art. 5º, II
    # =========================================================================
    # Dados de saúde - são PII sensíveis
    ("Paciente com HIV positivo", True, "Dado saúde HIV", "Dado Sensível Saúde"),
    ("Diagnóstico de câncer confirmado", True, "Dado saúde câncer", "Dado Sensível Saúde"),
    ("Prontuário médico nº 12345", True, "Prontuário médico", "Dado Sensível Saúde"),
    ("CID F32 - episódio depressivo", True, "CID transtorno mental", "Dado Sensível Saúde"),
    ("Tratamento realizado de câncer conforme solicitação", True, "Referência tratamento câncer", "Dado Sensível Saúde"),
    
    # Dados de criança/adolescente - são PII sensíveis
    ("João, 15 anos, estudante da EC 15", True, "Menor de idade identificado", "Dado Sensível Menor"),
    ("A aluna Maria, 10 anos, foi atendida", True, "Menor identificada", "Dado Sensível Menor"),
    
    # =========================================================================
    # GRUPO 14: CONTEXTOS ADMINISTRATIVOS SEGUROS
    # =========================================================================
    ("Solicito acesso aos autos do processo", False, "Solicitação genérica", "Administrativo"),
    ("Encaminhar para providências", False, "Despacho genérico", "Administrativo"),
    ("Conforme Lei nº 12.527/2011 (LAI)", False, "Referência legal", "Administrativo"),
    ("Processo SEI 00015-01009853/2023-11", False, "Número processo SEI", "Administrativo"),
    ("Protocolo 2024/000123", False, "Número protocolo", "Administrativo"),
    ("CNPJ 12.345.678/0001-99", False, "CNPJ empresa", "Administrativo"),
    ("Bom dia, prezados senhores", False, "Saudação", "Administrativo"),
    ("Atenciosamente, Ouvidoria GDF", False, "Despedida institucional", "Administrativo"),
    ("Conforme o Decreto 12.345/2024", False, "Referência decreto", "Administrativo"),
    ("Artigo 5º da Constituição Federal", False, "Referência legal", "Administrativo"),
    
    # =========================================================================
    # GRUPO 15: MÚLTIPLOS PII NO MESMO TEXTO
    # =========================================================================
    ("João Silva, CPF 529.982.247-25, tel (61) 99999-8888, email joao@gmail.com", True, "Nome+CPF+Tel+Email", "Múltiplos PII"),
    ("Requerente: Maria Santos, RG 1234567 SSP/DF, residente na SQN 315 Bloco A", True, "Nome+RG+Endereço", "Múltiplos PII"),
    ("CPF 123.456.789-09, matrícula 12345678, lotado na SEEDF", True, "CPF+Matrícula", "Múltiplos PII"),
    ("Contato: Pedro (61) 98765-4321, pedro.silva@hotmail.com", True, "Nome+Tel+Email", "Múltiplos PII"),
    
    # =========================================================================
    # GRUPO 16: SOLICITAÇÕES LAI - PEDIDOS DE DADOS (sem PII no texto)
    # =========================================================================
    ("Solicito a lista de servidores lotados na Secretaria de Saúde", False, "Solicitação lista genérica", "Solicitação LAI"),
    ("Informar o nome dos médicos plantonistas", False, "Solicitação nomes genérica", "Solicitação LAI"),
    ("Qual a remuneração dos servidores do cargo X?", False, "Solicitação remuneração genérica", "Solicitação LAI"),
    ("Solicito relação de pacientes atendidos", False, "Solicitação dados genérica", "Solicitação LAI"),
    ("Favor informar quantitativo de alunos matriculados", False, "Solicitação estatística", "Solicitação LAI"),
    ("Lista de beneficiários do programa X", False, "Solicitação lista genérica", "Solicitação LAI"),
    
    # MAS se a solicitação MENCIONA pessoa específica, aí é PII
    ("Solicito dados do servidor José Carlos Silva", True, "Solicitação com nome específico", "Solicitação com PII"),
    ("Informar remuneração do servidor mat. 12345678", True, "Solicitação com matrícula", "Solicitação com PII"),
    ("Qual o endereço residencial do diretor João Paulo?", True, "Solicitação com nome", "Solicitação com PII"),
    
    # =========================================================================
    # GRUPO 17: PASSAPORTE E DOCUMENTOS INTERNACIONAIS
    # =========================================================================
    ("Passaporte: AB123456", True, "Passaporte formato válido", "Passaporte"),
    ("Meu passaporte é FN987654", True, "Passaporte com possessivo", "Passaporte"),
    ("Passport number: BR654321", True, "Passaporte inglês", "Passaporte"),
    ("Passaporte: AA000000", False, "Passaporte fictício zeros", "Passaporte Fictício"),
    
    # =========================================================================
    # GRUPO 18: OUTROS DOCUMENTOS (PIS, TÍTULO ELEITOR, etc)
    # =========================================================================
    ("PIS: 123.45678.90-1", True, "PIS/PASEP", "Documento PIS"),
    ("Título de eleitor: 0123 4567 8901", True, "Título eleitor", "Documento Título"),
    ("CNS: 123456789012345", True, "Cartão SUS 15 dígitos", "Documento CNS"),
    ("CTPS: 1234567/00001-DF", True, "Carteira trabalho", "Documento CTPS"),
    ("OAB/SP nº 14.123", True, "OAB com número específico", "Documento OAB"),
    
    # =========================================================================
    # GRUPO 19: PLACAS DE VEÍCULO (identificam proprietário)
    # =========================================================================
    ("Placa do veículo: ABC-1234", True, "Placa formato antigo", "Placa Veículo"),
    ("Veículo placa ABC1D23", True, "Placa Mercosul", "Placa Veículo"),
    ("Meu carro placa JKL-5678", True, "Placa com possessivo", "Placa Veículo"),
    
    # =========================================================================
    # GRUPO 20: CASOS DE BORDA E EDGE CASES
    # =========================================================================
    # Textos ambíguos que parecem PII mas não são
    ("O processo 123.456.789-09 foi arquivado", False, "Número processo formato CPF", "Edge Case"),
    ("Código de barras: 12345678901", False, "Código numérico", "Edge Case"),
    ("Matéria publicada no DODF 123 de 2024", False, "Número publicação", "Edge Case"),
    ("CEP 70000-000 da Esplanada", False, "CEP genérico", "Edge Case"),
    
    # Textos com contexto negativo
    ("CPF inválido: o número informado não existe", False, "Contexto inválido explícito", "Edge Case"),
    ("O formato correto do CPF é XXX.XXX.XXX-XX", False, "Formato explicativo", "Edge Case"),
    ("Não foi possível localizar o CPF informado", False, "Contexto não encontrado", "Edge Case"),
    
    # Textos com ruído
    ("O@#$%email&*()inválido", False, "Email com caracteres especiais", "Edge Case"),
    ("123-456-789 não é um formato válido", False, "Número com hífen inválido", "Edge Case"),
    
    # =========================================================================
    # GRUPO 21: CASOS ESPECÍFICOS DO GDF/BRASÍLIA
    # =========================================================================
    ("Morador da Asa Norte há 20 anos", False, "Região sem endereço específico", "GDF Específico"),
    ("Atendimento na UBS 1 do Guará", False, "UBS pública", "GDF Específico"),
    ("Aluno do CEF 01 de Planaltina", False, "Escola pública", "GDF Específico"),
    ("Paciente do HRAN aguardando consulta", False, "Hospital público sigla", "GDF Específico"),
    ("Servidor da SEDESTMIDH", False, "Órgão GDF sigla", "GDF Específico"),
    ("Processo na CLDF sobre projeto de lei", False, "Órgão legislativo", "GDF Específico"),
    
    # =========================================================================
    # GRUPO 22: DADOS BIOMÉTRICOS E GENÉTICOS (LGPD Art. 5º, II)
    # =========================================================================
    ("Impressão digital coletada", True, "Dado biométrico", "Biométrico"),
    ("Foto 3x4 para documento", True, "Foto identificação", "Biométrico"),
    ("Reconhecimento facial realizado", True, "Biométrico facial", "Biométrico"),
    
    # =========================================================================
    # GRUPO 23: MAIS CASOS BASEADOS EM PADRÕES REAIS DO e-SIC
    # =========================================================================
    ("Considerando o processo 56478.000012/2026-05 da CGU, tal solicitação não se enquadra em informação pessoal sensível.", False, "Processo CGU sem PII", "e-SIC Real"),
    ("Há previsão de capacitação e treinamentos periódicos?", False, "Pergunta administrativa", "e-SIC Real"),
    ("Quais são os indicadores utilizados para monitoramento?", False, "Pergunta indicadores", "e-SIC Real"),
    ("A organização possui unidade responsável pela gestão de riscos?", False, "Pergunta estrutura", "e-SIC Real"),
    ("No referido imóvel há inúmeros vitrais, painéis Athos Bulsão", False, "Referência arte/patrimônio", "e-SIC Real"),
    ("No mês 10/2022 foi emitido uma nota de venda para o estado do Distrito Federal", False, "Referência fiscal genérica", "e-SIC Real"),
    ("Como devo proceder para realizar o pedido da restituição do ICMS ST?", False, "Pergunta procedimento", "e-SIC Real"),
    
    # =========================================================================
    # GRUPO 24: VARIAÇÕES DE FORMATAÇÃO DE DOCUMENTOS
    # =========================================================================
    # CPF com diferentes formatações
    ("cpf 52998224725", True, "CPF minúsculo sem formatação", "Formato Variado"),
    ("C.P.F.: 529.982.247-25", True, "CPF com pontos entre letras", "Formato Variado"),
    ("Cpf nº 529.982.247-25", True, "CPF capitalização mista", "Formato Variado"),
    
    # Telefone com diferentes formatações
    ("tel: 61 9 9999-8888", True, "Celular com espaço no 9", "Formato Variado"),
    ("fone (061) 99999-8888", True, "Celular com DDD 0", "Formato Variado"),
    ("telefone: 55 61 99999 8888", True, "Celular DDI espaços", "Formato Variado"),
    
    # =========================================================================
    # GRUPO 25: CASOS COMPLEXOS DE CONTEXTO
    # =========================================================================
    ("O cidadão, identificado apenas como José, compareceu", True, "Nome parcial em contexto de identificação", "Contexto Complexo"),
    ("A reclamação foi feita pela Sra. Ana Maria", True, "Nome com tratamento", "Contexto Complexo"),
    ("Conforme relatado pelo denunciante Pedro Henrique", True, "Nome em contexto de denúncia", "Contexto Complexo"),
    ("A declaração foi assinada por João Carlos Silva", True, "Nome em documento", "Contexto Complexo"),
    
    # Servidores que não devem ter imunidade em certos contextos
    ("O servidor João Carlos Silva solicitou férias", True, "Servidor em ação pessoal", "Contexto Complexo"),
    ("Maria Souza, servidora, informou seu CPF", True, "Servidora + dado pessoal", "Contexto Complexo"),
    
    # =========================================================================
    # GRUPO 26: MAIS 100 CASOS VARIADOS PARA ROBUSTEZ
    # =========================================================================
    
    # Mais CPFs
    ("Contribuinte CPF 321.654.987-00 em débito", True, "CPF contribuinte", "CPF Extra"),
    ("Titular do CPF 147.258.369-00", True, "CPF titular", "CPF Extra"),
    ("Cadastrado com CPF 963.852.741-00", True, "CPF cadastro", "CPF Extra"),
    
    # Mais telefones
    ("Retornar para 61-3333-4444", True, "Telefone fixo pessoal", "Telefone Extra"),
    ("Urgente: ligar (61) 98888-7777", True, "Telefone urgente", "Telefone Extra"),
    ("Número para recado: 61 99777-6666", True, "Telefone recado", "Telefone Extra"),
    
    # Mais emails
    ("Responder para fulano.tal@gmail.com", True, "Email resposta", "Email Extra"),
    ("Encaminhar cópia para beltrano@hotmail.com", True, "Email cópia", "Email Extra"),
    ("Notificar sicrano_123@yahoo.com.br", True, "Email notificação", "Email Extra"),
    
    # Mais nomes
    ("Comparecer: Francisco Souza Lima", True, "Nome comparecimento", "Nome Extra"),
    ("Beneficiário: Antônio Carlos Pereira", True, "Nome beneficiário", "Nome Extra"),
    ("Requerente: Fernanda Costa Santos", True, "Nome requerente", "Nome Extra"),
    ("Testemunha: Ricardo Almeida Neto", True, "Nome testemunha", "Nome Extra"),
    ("Declarante: Patrícia Lima Oliveira", True, "Nome declarante", "Nome Extra"),
    
    # Mais endereços
    ("Residência: QNM 15 Conjunto A Casa 01", True, "Endereço QNM", "Endereço Extra"),
    ("Mora na SHIN QI 03 Conjunto 05", True, "Endereço SHIN", "Endereço Extra"),
    ("Endereço: Quadra 204 Lote 15 Gama", True, "Endereço Gama", "Endereço Extra"),
    
    # Mais dados bancários
    ("Depósito na Ag 1234 CC 567890-1", True, "Dados bancários depósito", "Bancário Extra"),
    ("Transferir para conta 12345-X Ag 0001", True, "Dados bancários transferência", "Bancário Extra"),
    ("PIX CNPJ 12.345.678/0001-90", False, "PIX CNPJ empresa", "Bancário Extra"),
    
    # Mais matrículas
    ("Identificação funcional: mat. 87654321", True, "Matrícula identificação", "Matrícula Extra"),
    ("Servidor mat. 11111111-X", True, "Matrícula com X", "Matrícula Extra"),
    
    # Mais casos institucionais (não PII)
    ("A SEPLAG informou sobre o concurso", False, "Órgão informando", "Institucional Extra"),
    ("Conforme orientação da PGDF", False, "Órgão orientando", "Institucional Extra"),
    ("O TCDF determinou a correção", False, "Órgão determinando", "Institucional Extra"),
    ("A CAESB comunicou interrupção", False, "Empresa pública comunicando", "Institucional Extra"),
    
    # Mais processos/protocolos (não PII)
    ("SEI 00040-00098765/2025-00", False, "Processo SEI", "Protocolo Extra"),
    ("Protocolo nº 2025/001234", False, "Protocolo ano", "Protocolo Extra"),
    ("Referência: proc. 12345/2025", False, "Processo referência", "Protocolo Extra"),
    
    # Mais casos de saúde
    ("Laudo CID G40 - epilepsia", True, "CID neurológico", "Saúde Extra"),
    ("Diagnóstico CID J45 - asma", True, "CID respiratório", "Saúde Extra"),
    ("Prontuário nº 2025/12345", True, "Prontuário número", "Saúde Extra"),
    
    # Mais casos educação
    ("Boletim escolar do aluno matrícula 20251234", True, "Matrícula aluno", "Educação Extra"),
    ("Histórico do estudante RA 12345678901", True, "RA estudante", "Educação Extra"),
    
    # Mais contextos negativos
    ("O CPF não foi encontrado no sistema", False, "CPF não encontrado", "Contexto Negativo"),
    ("Telefone inválido: o número não existe", False, "Telefone inválido", "Contexto Negativo"),
    ("Email retornou erro: endereço incorreto", False, "Email erro", "Contexto Negativo"),
    
    # Mais saudações e formalidades
    ("Prezado(a) Senhor(a),", False, "Saudação formal", "Formalidade"),
    ("Vossa Excelência,", False, "Tratamento autoridade", "Formalidade"),
    ("Atenciosamente, Equipe de Atendimento", False, "Despedida genérica", "Formalidade"),
    ("Cordialmente, Ouvidoria", False, "Despedida cordial", "Formalidade"),
    
    # Mais referências legais
    ("Lei Federal 13.709/2018 (LGPD)", False, "Lei LGPD", "Legal Extra"),
    ("Decreto Distrital 39.736/2019", False, "Decreto DF", "Legal Extra"),
    ("Portaria 123/2025-SEEDF", False, "Portaria SEEDF", "Legal Extra"),
    ("Resolução 456/2025-TCDF", False, "Resolução TCDF", "Legal Extra"),
    
    # Mais siglas de órgãos
    ("SEDUH autorizou o alvará", False, "Órgão SEDUH", "Sigla Órgão"),
    ("SECEC promoveu evento", False, "Órgão SECEC", "Sigla Órgão"),
    ("SEJUS informou sobre visita", False, "Órgão SEJUS", "Sigla Órgão"),
    ("SEAGRI distribuiu sementes", False, "Órgão SEAGRI", "Sigla Órgão"),
    
    # Regiões administrativas
    ("Reunião na Administração do Riacho Fundo", False, "Admin Riacho Fundo", "Admin Regional"),
    ("Demanda da população do Varjão", False, "Região Varjão", "Admin Regional"),
    ("Obras em Vicente Pires", False, "Região Vicente Pires", "Admin Regional"),
    ("Atendimento no Itapoã", False, "Região Itapoã", "Admin Regional"),
    
    # Escolas e hospitais públicos
    ("CEF 04 do Guará oferece vagas", False, "Escola CEF Guará", "Instituição Pública"),
    ("CEM 01 do Gama realizará vestibular", False, "Escola CEM Gama", "Instituição Pública"),
    ("Hospital de Base sem leitos UTI", False, "Hospital Base", "Instituição Pública"),
    ("UPA de Samambaia lotada", False, "UPA Samambaia", "Instituição Pública"),
    
    # Datas e valores (não PII)
    ("Prazo: 30/12/2025", False, "Data prazo", "Data/Valor"),
    ("Valor: R$ 1.234,56", False, "Valor monetário", "Data/Valor"),
    ("Período: 01/01/2025 a 31/12/2025", False, "Período", "Data/Valor"),
    ("Quantidade: 1.000 unidades", False, "Quantidade", "Data/Valor"),
    
    # Mais casos complexos reais
    ("O Sr. José Carlos, morador da QNM 40, compareceu para registrar reclamação", True, "Complexo: nome + endereço", "Complexo Real"),
    ("Maria da Silva, CPF 123.456.789-09, solicita certidão", True, "Complexo: nome + CPF", "Complexo Real"),
    ("Atender João Paulo, telefone 61 99999-8888, sobre processo 12345/2025", True, "Complexo: nome + telefone + processo", "Complexo Real"),
    ("A servidora Ana Costa, mat. 123456, da SEEDF, está de férias", True, "Complexo: servidora + matrícula + órgão", "Complexo Real"),
    
    # Casos de imunidade mais elaborados
    ("O diretor-presidente da NOVACAP determinou a obra", False, "Cargo alto escalão", "Imunidade Alta"),
    ("Conforme decisão do secretário-adjunto de Saúde", False, "Cargo adjunto", "Imunidade Alta"),
    ("A superintendente da ADASA autorizou", False, "Cargo superintendente", "Imunidade Alta"),
    ("O controlador-geral do DF informou", False, "Cargo controlador", "Imunidade Alta"),
    
    # Mais textos sem PII
    ("A proposta foi aprovada por unanimidade", False, "Decisão administrativa", "Sem PII"),
    ("O prazo foi prorrogado por 30 dias", False, "Informação prazo", "Sem PII"),
    ("O recurso foi indeferido", False, "Decisão recurso", "Sem PII"),
    ("A documentação está incompleta", False, "Status documentação", "Sem PII"),
    ("Aguardando manifestação do interessado", False, "Status aguardando", "Sem PII"),
    
    # Textos longos reais do e-SIC (adaptados)
    ("Prezados bom dia, em visita ao Hospital de Apoio de Brasília fui orientada sobre a existência de dados abertos. Solicito informação quanto ao perfil do cidadão acometido pela doença.", False, "Solicitação dados epidemiológicos longa", "e-SIC Longo"),
    ("Respeitosamente, solicitam-se informações sobre funções de integridade e gestão de riscos no órgão, conforme determinações da CGU.", False, "Solicitação integridade longa", "e-SIC Longo"),
    ("Gostaria de saber se a legislação que reduziu o ITBI é válida somente até determinada data, e quais os requisitos para usufruir do benefício.", False, "Pergunta legislação longa", "e-SIC Longo"),
    
    # Mais casos com dados de contato
    ("Para esclarecimentos: (61) 99123-4567 falar com Roberto", True, "Telefone + nome esclarecimentos", "Contato Direto"),
    ("Dúvidas: maria.silva@email.com ou 61 98765-4321", True, "Email + telefone dúvidas", "Contato Direto"),
    ("Responsável: José Pereira - 61 3333-2222", True, "Nome + telefone responsável", "Contato Direto"),
    
    # Casos finais de cobertura
    ("O usuário de código 12345 foi atendido", False, "Código usuário genérico", "Código Sistema"),
    ("Ticket de atendimento nº 2025-001234", False, "Ticket suporte", "Código Sistema"),
    ("Chamado técnico 987654 em andamento", False, "Chamado técnico", "Código Sistema"),
    ("Ordem de serviço 2025/12345", False, "OS genérica", "Código Sistema"),
    
]


def executar_benchmark():
    # =============================
    # OVERLAP DE SPANS (avançado)
    # =============================
    from src.confidence.combiners import calcular_overlap_spans
    all_pred_spans = []
    all_true_spans = []

    from src.confidence.combiners import pos_processar_spans
    from tqdm import tqdm
    detector = PIIDetector(usar_gpu=False)
    for idx, (texto, esperado_pii, descricao, categoria) in enumerate(tqdm(DATASET_LGPD, desc="Benchmark LGPD")):
        achados = detector.detect(texto)[1]
        spans = [(a['inicio'], a['fim']) for a in achados if 'inicio' in a and 'fim' in a]
        # Pós-processamento: merge, normalização, remove spans curtos
        spans = pos_processar_spans(spans, min_len=2, merge_overlap=True)
        all_pred_spans.extend(spans)
        # Ground truth: se esperado_pii, marca o texto todo como span (proxy)
        if esperado_pii:
            all_true_spans.append((0, len(texto)))

    overlap_metrics = calcular_overlap_spans(all_pred_spans, all_true_spans)

    """Executa o benchmark completo e calcula métricas P1."""
    
    print("\n🚀 Inicializando detector...")
    detector = PIIDetector()
    
    print("\n📋 Executando benchmark LGPD...")
    print("=" * 80)
    print("🧪 BENCHMARK P1 - HACKATHON PARTICIPA DF 2025")
    print("=" * 80)
    print(f"Total de casos: {len(DATASET_LGPD)}")
    print("-" * 80)
    
    # Métricas
    vp = 0  # Verdadeiro Positivo: PII detectado corretamente
    vn = 0  # Verdadeiro Negativo: Não-PII classificado corretamente
    fp = 0  # Falso Positivo: Não-PII classificado como PII (alarme falso)
    fn = 0  # Falso Negativo: PII não detectado (vazamento!)
    
    # Listas para análise
    erros_fn = []
    erros_fp = []
    erros_por_categoria = defaultdict(int)
    
    for texto, esperado_pii, descricao, categoria in tqdm(DATASET_LGPD, desc="Avaliando Casos", leave=False):
        contem_pii, achados, nivel, confianca = detector.detect(texto)
        # Exibição detalhada linha a linha
        status = "✅ VP" if esperado_pii and contem_pii else (
            "✅ VN" if not esperado_pii and not contem_pii else (
            "❌ FN" if esperado_pii and not contem_pii else "❌ FP"))
        print(f"[{status}] {descricao} | Categoria: {categoria}")
        print(f"   Texto: {texto[:80]}{'...' if len(texto) > 80 else ''}")
        if achados:
            print("   Detectado: [" + ", ".join([
                f"{a['tipo']}: {a['valor'][:30]}" if a and 'tipo' in a and 'valor' in a and a['valor'] else str(a)
                for a in achados
            ]) + "]")
        print(f"   Esperado: {'PII' if esperado_pii else 'PÚBLICO'} | Detectado: {'PII' if contem_pii else 'PÚBLICO'} | Nível: {nivel} | Confiança: {confianca:.2f}")
        print("-" * 60)
        if esperado_pii and contem_pii:
            vp += 1
        elif not esperado_pii and not contem_pii:
            vn += 1
        elif esperado_pii and not contem_pii:
            fn += 1
            erros_fn.append((texto, descricao, categoria))
            erros_por_categoria[categoria] += 1
        else:  # not esperado_pii and contem_pii
            fp += 1
            encontrados = ", ".join([f"{a['tipo']}: {a['valor'][:30]}" for a in achados[:2]])
            erros_fp.append((texto, descricao, categoria, encontrados))
            erros_por_categoria[categoria] += 1
    
    # Cálculo das métricas
    total = vp + vn + fp + fn
    precisao = vp / (vp + fp) if (vp + fp) > 0 else 0
    sensibilidade = vp / (vp + fn) if (vp + fn) > 0 else 0
    f1_score = 2 * (precisao * sensibilidade) / (precisao + sensibilidade) if (precisao + sensibilidade) > 0 else 0
    acuracia = (vp + vn) / total if total > 0 else 0
    
    # Relatório
    print("\n" + "=" * 80)
    print("📊 RESULTADOS DO BENCHMARK LGPD")
    print("=" * 80)
    
    print(f"""
┌─────────────────────────────────────────────────────────────┐
│                    MÉTRICAS P1 (EDITAL)                     │
├─────────────────────────────────────────────────────────────┤
│  Total de casos:         {total:<6}                            │
│                                                             │
│  Verdadeiros Positivos:  {vp:<4}  (PII detectado corretamente) │
│  Verdadeiros Negativos:  {vn:<4}  (SEGURO detectado corretamente)│
│  Falsos Positivos:       {fp:<4}  (Alarme falso) ⚠️              │
│  Falsos Negativos:       {fn:<4}  (PII não detectado) ⚠️         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRECISÃO:         {precisao:.4f}  (VP / (VP + FP))              │
│  SENSIBILIDADE:    {sensibilidade:.4f}  (VP / (VP + FN))              │
│                                                             │
│  ════════════════════════════════════════════════           │
│  P1 (F1-SCORE):    {f1_score:.4f}  ← NOTA PRINCIPAL              │
│  ════════════════════════════════════════════════           │
│                                                             │
│  ACURÁCIA:         {acuracia:.4f}  ((VP + VN) / Total)           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                 CRITÉRIOS DE DESEMPATE                      │
│  1º Menor FN:   {fn:<4} (quanto menor, melhor)              │
│  2º Menor FP:   {fp:<4} (quanto menor, melhor)              │
│  3º Maior P1: {f1_score:.4f} (quanto maior, melhor)           │
└─────────────────────────────────────────────────────────────┘
""")

    # Relatório de overlap de spans
    print("\n" + "=" * 80)
    print("📏 OVERLAP DE SPANS (avançado)")
    print("=" * 80)
    print(f"Precision spans: {overlap_metrics['precision_spans']}")
    print(f"Recall spans:    {overlap_metrics['recall_spans']}")
    print(f"F1 spans:        {overlap_metrics['f1_spans']}")
    print(f"IoU médio:       {overlap_metrics['mean_iou']}")
    print(f"TP: {overlap_metrics['tp']} | FP: {overlap_metrics['fp']} | FN: {overlap_metrics['fn']}")
    
    # Análise de erros
    if fn > 0:
        print("\n⚠️  ATENÇÃO: Há Falsos Negativos - PIIs não detectados!")
        print("    Isso é CRÍTICO para conformidade LGPD/LAI.\n")
        for texto, desc, cat in erros_fn[:20]:
            print(f"    ❌ FN: {desc} [{cat}]")
            print(f"       Texto: {texto[:60]}...")
    
    if fp > 0:
        print("\n⚠️  ATENÇÃO: Há Falsos Positivos - Alarmes falsos!")
        print("    Textos seguros sendo classificados como PII.\n")
        for texto, desc, cat, encontrado in erros_fp[:15]:
            print(f"    ❌ FP: {desc} [{cat}]")
            print(f"       Texto: {texto[:60]}...")
            print(f"       → Detectado: {encontrado}")
    
    if erros_por_categoria:
        print("\n📋 ERROS POR CATEGORIA:")
        for cat, count in sorted(erros_por_categoria.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {cat}: {count} erro(s)")
    
    # Salva resultados
    resultados = {
        "timestamp": datetime.now().isoformat(),
        "total_casos": total,
        "metricas": {
            "precisao": round(precisao, 4),
            "sensibilidade": round(sensibilidade, 4),
            "f1_score": round(f1_score, 4),
            "acuracia": round(acuracia, 4)
        },
        "contagens": {
            "VP": vp, "VN": vn, "FP": fp, "FN": fn
        },
        "erros_por_categoria": dict(erros_por_categoria),
        "falsos_negativos": [{"texto": t[:100], "descricao": d, "categoria": c} 
                           for t, d, c in erros_fn],
        "falsos_positivos": [{"texto": t[:100], "descricao": d, "categoria": c, "detectado": e} 
                           for t, d, c, e in erros_fp]
    }
    
    os.makedirs("data/output", exist_ok=True)
    with open("data/output/benchmark_lgpd_results.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Resultados salvos em: data/output/benchmark_lgpd_results.json")
    
    # Avaliação final
    if f1_score >= 0.95:
        print("\n🏆 EXCELENTE! F1-Score >= 0.95 - Candidato a VENCEDOR!")
    elif f1_score >= 0.90:
        print("\n✅ MUITO BOM! F1-Score >= 0.90 - Forte candidato!")
    elif f1_score >= 0.85:
        print("\n⚠️ BOM. F1-Score >= 0.85 - Precisa melhorar para vencer.")
    else:
        print("\n❌ PRECISA MELHORAR. F1-Score < 0.85")
    
    return f1_score >= 0.80


if __name__ == "__main__":
    sucesso = executar_benchmark()
    sys.exit(0 if sucesso else 1)
