"""Suite de Testes para o Detector de PII - Participa DF.

Este módulo contém 100+ casos de teste cobrindo:
- Situações seguras (não PII)
- PII clássico (CPF, Email, Telefone, Nomes)
- Edge cases e pegadinhas
- Contexto específico de Brasília/GDF
- Testes de imunidade funcional (agentes públicos em exercício)
"""

import sys
import os
from typing import List, Dict, Tuple

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.detector import PIIDetector


# DATASET COM 100+ CASOS DE TESTE - CONTEXTO BRASÍLIA/GDF
dataset_teste = [
    # ============================================================================
    # GRUPO 1: SITUAÇÕES BUROCRÁTICAS SEGURAS (ESPERADO: 0)
    # ============================================================================
    {
        "texto": "Solicito acesso aos autos da Secretaria de Estado da Segurança Pública.",
        "esperado": 0,
        "categoria": "Administrativo"
    },
    {
        "texto": "Reclamação sobre LIGAÇÕES TELEFÔNICAS MUDAS na Asa Norte.",
        "esperado": 0,
        "categoria": "Administrativo"
    },
    {
        "texto": "Obras no Eixo Monumental atrapalhando o trânsito.",
        "esperado": 0,
        "categoria": "Administrativo"
    },
    {
        "texto": "Solicito cópia do cadastro que preenchi virtualmente.",
        "esperado": 0,
        "categoria": "Administrativo"
    },
    {
        "texto": "Bom dia, gostaria de saber sobre o processo SEI 00015-01009853/2023-11.",
        "esperado": 0,
        "categoria": "Administrativo - Protocolo"
    },
    {
        "texto": "Conforme a Lei nº 8.112/90 e o Decreto 12.345.",
        "esperado": 0,
        "categoria": "Administrativo - Legislação"
    },
    {
        "texto": "O valor da multa foi de R$ 1.250,00 a ser pago no BRB.",
        "esperado": 0,
        "categoria": "Administrativo - Financeiro"
    },
    {
        "texto": "Encaminho anexo para a ouvidoria do GDF.",
        "esperado": 0,
        "categoria": "Administrativo"
    },
    {
        "texto": "O email institucional é ouvidoria@saude.df.gov.br",
        "esperado": 0,
        "categoria": "Administrativo - Email institucional"
    },
    {
        "texto": "Telefone institucional: (61) 3105-1234.",
        "esperado": 0,
        "categoria": "Administrativo - Telefone institucional"
    },
    {
        "texto": "Encaminhar para a Secretaria de Saúde do GDF.",
        "esperado": 0,
        "categoria": "Administrativo"
    },
    {
        "texto": "A reunião será na Administração Regional de Taguatinga.",
        "esperado": 0,
        "categoria": "Administrativo - Local"
    },
    {
        "texto": "Solicito acesso ao processo SEI nº 00040-00012345/2024-12.",
        "esperado": 0,
        "categoria": "Administrativo - Protocolo SEI"
    },
    {
        "texto": "O CNPJ da empresa fornecedora é 12.345.678/0001-99.",
        "esperado": 0,
        "categoria": "Administrativo - CNPJ Empresa"
    },
    {
        "texto": "Encaminhar para a DELEGACIA DA MULHER (DEAM).",
        "esperado": 0,
        "categoria": "Administrativo - Sigla órgão"
    },

    # ============================================================================
    # GRUPO 2: PII CLÁSSICO - SEMPRE DEVE SER DETECTADO (ESPERADO: 1)
    # ============================================================================
    {
        "texto": "Meu CPF é 123.456.789-09 e preciso de ajuda urgente.",
        "esperado": 1,
        "categoria": "PII - CPF válido"
    },
    {
        "texto": "Pode falar com Carlos Eduardo da Silva no telefone.",
        "esperado": 1,
        "categoria": "PII - Nome pessoal"
    },
    {
        "texto": "Meu email pessoal é joao.silva123@gmail.com.",
        "esperado": 1,
        "categoria": "PII - Email privado"
    },
    {
        "texto": "A vítima foi identificada como Maria Antonieta de Las Nieves.",
        "esperado": 1,
        "categoria": "PII - Nome vítima"
    },
    {
        "texto": "Entrar em contato no (61) 98765-4321 após as 14h.",
        "esperado": 1,
        "categoria": "PII - Telefone celular"
    },
    {
        "texto": "Meu celular é 61 99988-7766, falar com José.",
        "esperado": 1,
        "categoria": "PII - Celular sem formatação"
    },
    {
        "texto": "Meu pix é o celular 61999887766.",
        "esperado": 1,
        "categoria": "PII - Celular (PIX)"
    },
    {
        "texto": "Minha identidade é RG 3.123.456 SSP/DF.",
        "esperado": 1,
        "categoria": "PII - RG"
    },
    {
        "texto": "O portador da identidade RG 1.234.567 está presente.",
        "esperado": 1,
        "categoria": "PII - RG"
    },
    {
        "texto": "A fatura deve ser paga por João da Silva Pereira.",
        "esperado": 1,
        "categoria": "PII - Nome completo"
    },
    {
        "texto": "O documento de identificação é o CNH 0987654321.",
        "esperado": 1,
        "categoria": "PII - CNH"
    },
    {
        "texto": "O número da minha CNH é 0987654321.",
        "esperado": 1,
        "categoria": "PII - CNH"
    },
    {
        "texto": "A vítima se chama Ana Clara Oliveira.",
        "esperado": 1,
        "categoria": "PII - Nome vítima"
    },
    {
        "texto": "O denunciante é o cidadão José Pereira.",
        "esperado": 1,
        "categoria": "PII - Nome denunciante"
    },
    {
        "texto": "Meu email pessoal: joao123@gmail.com",
        "esperado": 1,
        "categoria": "PII - Email privado"
    },
    {
        "texto": "CNH: 01234567890",
        "esperado": 1,
        "categoria": "PII - CNH"
    },
    {
        "texto": "RG: 1.234.567 SSP/DF",
        "esperado": 1,
        "categoria": "PII - RG"
    },

    # ============================================================================
    # GRUPO 3: IMUNIDADE FUNCIONAL - AGENTES PÚBLICOS EM EXERCÍCIO (ESPERADO: 0)
    # ============================================================================
    {
        "texto": "Falar com a Dra. Fernanda na Secretaria de Saúde do DF.",
        "esperado": 0,
        "categoria": "Imunidade - Cargo + instituição"
    },
    {
        "texto": "Encaminhar para o Dr. Paulo na Administração Regional do Plano Piloto.",
        "esperado": 0,
        "categoria": "Imunidade - Cargo + instituição"
    },
    {
        "texto": "O servidor público João Silva me atendeu ontem.",
        "esperado": 0,
        "categoria": "Imunidade - Servidor em função"
    },
    {
        "texto": "A Dra. Maria é a responsável pelo setor de ouvidoria.",
        "esperado": 0,
        "categoria": "Imunidade - Cargo + setor"
    },
    {
        "texto": "O perito técnico Dr. Roberto analisou meu caso.",
        "esperado": 0,
        "categoria": "Imunidade - Cargo + função"
    },
    {
        "texto": "O perito médico Dr. Roberto analisou meu caso.",
        "esperado": 0,
        "categoria": "Imunidade - Cargo + função"
    },
    {
        "texto": "O servidor Marcos Paulo da Silva é o responsável.",
        "esperado": 0,
        "categoria": "Imunidade - Servidor público em função"
    },
    {
        "texto": "A testemunha é o Sr. Antônio, morador da QR 408.",
        "esperado": 1,
        "categoria": "PII - Testemunha com endereço"
    },
    {
        "texto": "Favor encaminhar para o Administrador Regional do Guará.",
        "esperado": 0,
        "categoria": "Imunidade - Cargo público"
    },

    # ============================================================================
    # GRUPO 4: QUEBRA DE IMUNIDADE - GATILHOS DE CONTATO (ESPERADO: 1)
    # ============================================================================
    {
        "texto": "Preciso falar com o Sr. Carlos sobre minha reclamação.",
        "esperado": 1,
        "categoria": "Quebra imunidade - Gatilho 'falar com'"
    },
    {
        "texto": "Ligar para a Sra. Lúcia no telefone (61) 99999-8888.",
        "esperado": 1,
        "categoria": "Quebra imunidade - Gatilho 'ligar para'"
    },
    {
        "texto": "Falar com o perito Roberto sobre o laudo.",
        "esperado": 1,
        "categoria": "Quebra imunidade - Gatilho anula cargo"
    },
    {
        "texto": "Preciso do contato do servidor Marcos Paulo da Silva.",
        "esperado": 1,
        "categoria": "Quebra imunidade - Contexto de contato"
    },
    {
        "texto": "Entre em contato com Ana Silva para maiores informações.",
        "esperado": 1,
        "categoria": "Quebra imunidade - Gatilho 'contato'"
    },
    {
        "texto": "Encaminhar para o Dr. Lucas Silva responsável pelo departamento.",
        "esperado": 0,
        "categoria": "Imunidade - Sem quebra"
    },

    # ============================================================================
    # GRUPO 5: ENDEREÇOS - ADMINISTRATIVOS vs RESIDENCIAIS (ESPERADO: 0 ou 1)
    # ============================================================================
    {
        "texto": "Solicito envio para a SQS 302 Bloco K em Brasília.",
        "esperado": 0,
        "categoria": "Endereço administrativo - Setor público"
    },
    {
        "texto": "Endereço: Quadra 12 Conjunto B Casa 45, Samambaia.",
        "esperado": 1,
        "categoria": "Endereço residencial"
    },
    {
        "texto": "Moro na SQN 305 Bloco A Apto 101, Asa Norte.",
        "esperado": 1,
        "categoria": "Endereço residencial - SQN privado"
    },
    {
        "texto": "Minha casa é na SQS 402 Bloco C, Asa Sul.",
        "esperado": 1,
        "categoria": "Endereço residencial - SQS privado"
    },
    {
        "texto": "Moro na Quadra 10 Conjunto B Casa 20.",
        "esperado": 1,
        "categoria": "Endereço residencial"
    },
    {
        "texto": "Moro no Setor de Mansões Park Way, Quadra 5, Casa 10.",
        "esperado": 1,
        "categoria": "Endereço residencial - Park Way"
    },
    {
        "texto": "Moro na Rua das Pitangueiras, Casa 45, Fundos, Taguatinga.",
        "esperado": 1,
        "categoria": "Endereço residencial - Rua especificada"
    },
    {
        "texto": "Endereço comercial: SCLN 305 Bloco B Loja 20.",
        "esperado": 0,
        "categoria": "Endereço comercial"
    },
    {
        "texto": "Moro na Quadra 10 Conjunto A, mas o problema é na rua pública.",
        "esperado": 0,
        "categoria": "Endereço genérico"
    },

    # ============================================================================
    # GRUPO 6: EDGE CASES - CPF INVÁLIDO, FAKE, FORMATOS (ESPERADO: 0)
    # ============================================================================
    {
        "texto": "O número de teste é 111.111.111-11.",
        "esperado": 0,
        "categoria": "CPF inválido matematicamente"
    },
    {
        "texto": "O CPF informado é 123.456.789-00.",
        "esperado": 1,
        "categoria": "CPF válido matematicamente"
    },
    {
        "texto": "O número 123.456.789-00 é inválido.",
        "esperado": 0,
        "categoria": "CPF em contexto negativo"
    },
    {
        "texto": "Meu CPF é 000.000.000-00, por favor me ajudem.",
        "esperado": 1,
        "categoria": "CPF teste"
    },
    {
        "texto": "meu email é ana.souza@hotmail.com e meu zap é 61988887777",
        "esperado": 1,
        "categoria": "Email + telefone minúsculo"
    },
    {
        "texto": "Contato: (61) 99988-7766 (WhatsApp da Maria).",
        "esperado": 1,
        "categoria": "Telefone + nome contato"
    },

    # ============================================================================
    # GRUPO 7: NOVOS CASOS - CONTEXTO GDF/BRASÍLIA (50+ CASOS ADICIONAIS)
    # ============================================================================
    
    # Casos 1-5: Endereços administrativos Brasília
    {
        "texto": "A Secretaria de Saúde fica na Esplanada dos Ministérios.",
        "esperado": 0,
        "categoria": "Endereço administrativo público"
    },
    {
        "texto": "Solicito informações sobre a CAESB na EQ 14/16 Asa Norte.",
        "esperado": 0,
        "categoria": "Endereço institucional"
    },
    {
        "texto": "O GDF está localizado no Palácio do Buriti.",
        "esperado": 0,
        "categoria": "Prédio público famoso"
    },
    {
        "texto": "Encaminhar para SRVS (Bloco A) - Asa Sul.",
        "esperado": 0,
        "categoria": "Setor administrativo"
    },
    {
        "texto": "Moro no Plano Piloto, setor comercial sul.",
        "esperado": 0,
        "categoria": "Região pública"
    },

    # Casos 6-10: Nomes genéricos vs específicos
    {
        "texto": "Atender cliente do sexo masculino, nome: João.",
        "esperado": 0,
        "categoria": "Nome genérico em contexto administrativo"
    },
    {
        "texto": "A testemunha informa que seu nome é Margarida.",
        "esperado": 1,
        "categoria": "Nome testemunha"
    },
    {
        "texto": "Visitante registrado como 'Silva, José'.",
        "esperado": 1,
        "categoria": "Nome visitante"
    },
    {
        "texto": "Funcionário do mês: Francisco Costa.",
        "esperado": 0,
        "categoria": "Funcionário em público"
    },
    {
        "texto": "A vítima informou seu nome: Catarina Gomes.",
        "esperado": 1,
        "categoria": "Nome vítima"
    },

    # Casos 11-15: Documentos e formatos
    {
        "texto": "Passaporte: AA000000",
        "esperado": 0,
        "categoria": "Passaporte genérico"
    },
    {
        "texto": "Meu passaporte é BR1234567",
        "esperado": 1,
        "categoria": "Passaporte pessoal"
    },
    {
        "texto": "Creci do imóvel: 123456",
        "esperado": 0,
        "categoria": "Registro profissional"
    },
    {
        "texto": "OAB: 1234567/DF",
        "esperado": 0,
        "categoria": "Inscrição profissional OAB"
    },
    {
        "texto": "Minha inscrição estadual é 12.345.678.901.234",
        "esperado": 0,
        "categoria": "Documento fiscal"
    },

    # Casos 16-20: Contextos de manifestação/reclamação
    {
        "texto": "Denuncio o funcionário que me atendeu com falta de respeito.",
        "esperado": 0,
        "categoria": "Reclamação anônima"
    },
    {
        "texto": "O atendente que me atendeu chamava-se Rodrigo.",
        "esperado": 0,
        "categoria": "Nome funcionário em contexto de função"
    },
    {
        "texto": "Gostaria de reclamar com o responsável Sérgio Alves.",
        "esperado": 1,
        "categoria": "Contato específico para reclamação"
    },
    {
        "texto": "Necessito protocolo de atendimento para a reclamação contra Pedro.",
        "esperado": 1,
        "categoria": "Nome acusado"
    },
    {
        "texto": "Felicito o funcionário Leonardo pelo excelente atendimento.",
        "esperado": 0,
        "categoria": "Elogio funcionário"
    },

    # Casos 21-25: Telefones em vários formatos
    {
        "texto": "Celular institucional: +55 61 98765-4321",
        "esperado": 0,
        "categoria": "Telefone com DDI institucional"
    },
    {
        "texto": "Meu celular de emergência: +5561988887766",
        "esperado": 1,
        "categoria": "Telefone pessoal com DDI"
    },
    {
        "texto": "Entre em contato pelo ramal 1234.",
        "esperado": 0,
        "categoria": "Ramal administrativo"
    },
    {
        "texto": "Telefone para contato: (61) 3105-1234 ramal 567",
        "esperado": 0,
        "categoria": "Telefone institucional com ramal"
    },
    {
        "texto": "Meu número para urgência é 61 99777-6655",
        "esperado": 1,
        "categoria": "Telefone pessoal urgência"
    },

    # Casos 26-30: Emails em vários domínios
    {
        "texto": "Contacte: atendimento@seedf.df.gov.br",
        "esperado": 0,
        "categoria": "Email institucional SEEDF"
    },
    {
        "texto": "Envie para: saude.publica@saude.df.gov.br",
        "esperado": 0,
        "categoria": "Email institucional saúde"
    },
    {
        "texto": "Meu email de trabalho: maria.santos@empresa-df.com.br",
        "esperado": 0,
        "categoria": "Email corporativo"
    },
    {
        "texto": "Contato pessoal: lucas.oliveira@hotmail.com",
        "esperado": 1,
        "categoria": "Email pessoal hotmail"
    },
    {
        "texto": "Enviar para: patricia_costa@yahoo.com.br",
        "esperado": 1,
        "categoria": "Email pessoal yahoo"
    },

    # Casos 31-35: Dados financeiros/bancários
    {
        "texto": "Agência: 0001 Conta: 123456-7",
        "esperado": 0,
        "categoria": "Dados bancários genéricos"
    },
    {
        "texto": "Minha conta no BRB é 0000123456789",
        "esperado": 1,
        "categoria": "Número conta pessoal"
    },
    {
        "texto": "Transferência para: 12345-6 no Banco de Brasília",
        "esperado": 1,
        "categoria": "Conta bancária pessoal"
    },
    {
        "texto": "Pagar na conta da Prefeitura: CNPJ 07.154.321/0001-00",
        "esperado": 0,
        "categoria": "Conta instituição pública"
    },
    {
        "texto": "PIX (chave aleatória): 123e4567-e89b-12d3-a456-426614174000",
        "esperado": 1,
        "categoria": "PIX pessoal"
    },

    # Casos 36-40: Contexto de LAI (Lei de Acesso à Informação)
    {
        "texto": "Sob a LAI, solicito informações sobre funcionários da SEEDF.",
        "esperado": 0,
        "categoria": "Requisição LAI"
    },
    {
        "texto": "Conforme LAI, quem é o responsável por X?",
        "esperado": 0,
        "categoria": "Pergunta LAI"
    },
    {
        "texto": "Conforme LGPD, não posso fornecer dados de: João Silva, CPF 123.456.789-09",
        "esperado": 1,
        "categoria": "Referência LGPD com PII"
    },
    {
        "texto": "A informação é classificada como sigilosa sob LAI.",
        "esperado": 0,
        "categoria": "Classificação LAI"
    },
    {
        "texto": "Recurso à LAI contra negativa de informação.",
        "esperado": 0,
        "categoria": "Procedimento LAI"
    },

    # Casos 41-45: Situações com múltiplos PII
    {
        "texto": "CPF: 111.111.111-11 e telefone: (61) 99999-8888",
        "esperado": 1,
        "categoria": "CPF inválido + telefone válido"
    },
    {
        "texto": "Dados: email joao@gmail.com, celular 61987654321, endereço Rua A Casa 10",
        "esperado": 1,
        "categoria": "Múltiplos PII"
    },
    {
        "texto": "Entre em contato: (61) 98888-7777 ou envie para ana@hotmail.com",
        "esperado": 1,
        "categoria": "Telefone + email privado"
    },
    {
        "texto": "Testemunha: Pedro Silva, RG 1.234.567, morador de Taguatinga",
        "esperado": 1,
        "categoria": "Nome + RG + endereço"
    },
    {
        "texto": "Vítima: Maria das Graças, CPF 987.654.321-00, WhatsApp 61999887766",
        "esperado": 1,
        "categoria": "Nome + CPF + celular"
    },

    # Casos 46-50: Casos ambíguos/limítrofes
    {
        "texto": "Silva é um sobrenome comum em Brasília.",
        "esperado": 0,
        "categoria": "Nome genérico"
    },
    {
        "texto": "O setor de telefonia: SQN 307 oferece serviços.",
        "esperado": 0,
        "categoria": "Setor com nome similar a endereço"
    },
    {
        "texto": "Maria, que é funcionária, informou seu CPF: 555.555.555-55",
        "esperado": 0,
        "categoria": "CPF inválido de funcionário"
    },
    {
        "texto": "Encaminhar a Ana Silva, servidora, a correspondência.",
        "esperado": 0,
        "categoria": "Servidora em contexto de função"
    },
    {
        "texto": "O responsável Dr. Augusto da Administração Regional",
        "esperado": 0,
        "categoria": "Cargo + função pública"
    },
]


def rodar() -> None:
    """Executa suite completa de testes e exibe relatório detalhado."""
    detector = PIIDetector()
    acertos = 0
    total = len(dataset_teste)
    erros_detalhados = []
    erros_por_categoria = {}

    print(f"\n{'='*120}")
    print(f"🧪 EXECUTANDO SUITE DE TESTES - {total} CASOS")
    print(f"{'='*120}\n")
    print(f"{'TEXTO (Amostra)':<50} | {'REAL':<6} | {'IA':<6} | {'RESULTADO':<12} | CATEGORIA")
    print("-" * 120)

    for idx, item in enumerate(dataset_teste, 1):
        # Executa detecção
        res, findings, risco, score = detector.detect(item['texto'])
        ia = 1 if res else 0
        categoria = item.get('categoria', 'N/A')

        # Determina status e cor
        status = "✅ ACERTO" if ia == item['esperado'] else "❌ ERRO"
        cor = "\033[92m" if ia == item['esperado'] else "\033[91m"
        reset = "\033[0m"

        # Prepara mensagem de debug em caso de falha
        if status == "❌ ERRO":
            tipos_encontrados = [f['tipo'] for f in findings]
            debug_info = f" -> Tipos: {tipos_encontrados}" if tipos_encontrados else ""
            erros_detalhados.append({
                "caso": idx,
                "texto": item['texto'],
                "esperado": item['esperado'],
                "obtido": ia,
                "findings": findings,
                "categoria": categoria
            })
            # Agrupa erros por categoria
            if categoria not in erros_por_categoria:
                erros_por_categoria[categoria] = []
            erros_por_categoria[categoria].append(idx)
        else:
            debug_info = ""

        # Formata exibição do texto
        texto_display = (item['texto'][:47] + '...') if len(item['texto']) > 47 else item['texto']
        print(
            f"{cor}{texto_display:<50} | {item['esperado']:<6} | {ia:<6} | {status:<12} | {categoria}{reset}"
        )

        if ia == item['esperado']:
            acertos += 1

    # Relatório final
    acc = (acertos / total) * 100
    print("-" * 120)
    print(f"\n{'='*120}")
    print(f"📊 RESUMO FINAL")
    print(f"{'='*120}")
    print(f"✅ ACERTOS: {acertos}/{total}")
    print(f"❌ ERROS: {len(erros_detalhados)}/{total}")
    print(f"📈 ACURÁCIA: {acc:.1f}%\n")

    # Status final
    if acc == 100.0:
        print("🚀 PARABÉNS! MODELO PRONTO PARA HACKATHON PARTICIPA DF!")
    elif acc >= 95.0:
        print("✨ EXCELENTE DESEMPENHO! Apenas pequenos ajustes necessários.")
    elif acc >= 90.0:
        print("⚠️ BOM DESEMPENHO! Revisar os erros abaixo para melhorar.")
    else:
        print("🔧 NECESSÁRIA REVISÃO SIGNIFICATIVA DOS ERROS.")

    # Exibe erros detalhados
    if erros_detalhados:
        print(f"\n{'='*120}")
        print(f"❌ DETALHES DOS {len(erros_detalhados)} ERROS")
        print(f"{'='*120}\n")

        # Agrupa por categoria
        print("📋 ERROS POR CATEGORIA:")
        for cat in sorted(erros_por_categoria.keys()):
            count = len(erros_por_categoria[cat])
            print(f"  • {cat}: {count} erro(s) - casos {erros_por_categoria[cat]}")

        print(f"\n📝 PRIMEIROS 10 ERROS DETALHADOS:\n")
        for erro in erros_detalhados[:10]:
            print(f"  Caso {erro['caso']} [{erro['categoria']}]:")
            print(f"    Texto: '{erro['texto']}'")
            print(f"    Esperado: {erro['esperado']}, Obtido: {erro['obtido']}")
            if erro['findings']:
                print(f"    Findings: {[f['tipo'] + ':' + f['valor'][:20] for f in erro['findings']]}")
            print()


if __name__ == "__main__":
    rodar()
