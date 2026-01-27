"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     DETECTOR DE PII - HACKATHON PARTICIPA-DF 2025                           ║
║     Versão: 9.6.1 - Versão Final para Inscrição                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

ARQUITETURA COMPLETA DO PIPELINE DE DETECÇÃO
============================================

┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 1: REGEX + VALIDAÇÃO DE DV (Dígito Verificador)                      │
│ ─────────────────────────────────────────────────────────────────────────── │
│ • 53 patterns regex para documentos brasileiros e GDF                       │
│ • Validação de CPF (mod 11) - rejeita sequências inválidas                 │
│ • Validação de CNPJ (mod 11 duplo) - rejeita sequências inválidas          │
│ • Patterns específicos GDF: PROCESSO_SEI, PROTOCOLO_LAI, MATRICULA_GDF     │
│ • Performance: ~70% dos PIIs detectados nesta etapa                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 2: GATILHOS CONTEXTUAIS                                               │
│ ─────────────────────────────────────────────────────────────────────────── │
│ • Detecta nomes após palavras-chave: "contribuinte", "reclamante", etc.    │
│ • Allow-list de órgãos GDF (gazetteer) para evitar falsos positivos        │
│ • Blocklist de termos institucionais                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 3: NER (Named Entity Recognition) - ENSEMBLE DE 3 MODELOS            │
│ ─────────────────────────────────────────────────────────────────────────── │
│ • BERT Davlan: Davlan/bert-base-multilingual-cased-ner-hrl (peso 1.0)      │
│ • BERT pt-BR: monilouise/ner_news_portuguese (peso 1.0)                    │
│ • spaCy: pt_core_news_lg (backup, peso 0.85)                               │
│ • Estratégia: Votação permissiva (OR) - qualquer modelo = aceita           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 4: PRESIDIO ANALYZER (Complementar)                                   │
│ ─────────────────────────────────────────────────────────────────────────── │
│ • Recognizers customizados para GDF (PROCESSO_SEI, MATRICULA_GDF, etc.)    │
│ • Entidades complementares: IP_ADDRESS, IBAN_CODE, CREDIT_CARD             │
│ • NÃO duplica detecção de PERSON/PHONE (já cobertos pelo NER)              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 5: VOTAÇÃO DO ENSEMBLE                                                │
│ ─────────────────────────────────────────────────────────────────────────── │
│ • Pesos configuráveis por fonte (regex=1.0, bert=1.0, gatilho=1.1)         │
│ • Critério permissivo: peso >= 1 e confiança >= threshold                  │
│ • Items com baixa confiança → pendentes para LLM                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 6: ÁRBITRO LLM (Llama-3.2-3B-Instruct) - ATIVADO POR PADRÃO          │
│ ─────────────────────────────────────────────────────────────────────────── │
│ • Analisa casos ambíguos (pendentes da votação)                            │
│ • Avalia RISCO DE REIDENTIFICAÇÃO:                                         │
│   - Número isolado = BAIXA criticidade                                     │
│   - Número + Nome/CPF no mesmo parágrafo = ALTA criticidade                │
│ • Distingue contexto funcional vs pessoal                                  │
│ • Última chance: analisa texto completo se nenhum PII encontrado           │
│ • Requer HF_TOKEN configurado (Hugging Face API)                           │
│ • Pode ser desativado: PII_USE_LLM_ARBITRATION=false                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 7: DEDUPLICAÇÃO AVANÇADA                                              │
│ ─────────────────────────────────────────────────────────────────────────── │
│ • Remove substrings de nomes ("Ruth Helena" se existe "Ruth Helena Franco")│
│ • Remove fragmentos de telefone (DDD isolado, pedaços do número)           │
│ • Prioriza detecções mais específicas                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 8: CÁLCULO DE CONFIANÇA PROBABILÍSTICA                               │
│ ─────────────────────────────────────────────────────────────────────────── │
│ • Base por tipo (CPF=0.92, NOME=0.85, etc.)                                │
│ • Fator de contexto (±20% baseado em palavras próximas)                    │
│ • Log-odds para combinação calibrada                                       │
│ • Threshold dinâmico por tipo de PII                                       │
└─────────────────────────────────────────────────────────────────────────────┘

RESULTADOS DA AUDITORIA LGPD
============================
• Gabarito: 156 PIIs mapeados manualmente em 99 registros
• VP: 156 | FN: 0 | FP: 0
• Precision: 100% | Recall: 100% | F1: 100%

CONFIGURAÇÃO
============
• use_llm_arbitration: True (padrão) - requer HF_TOKEN
• PII_USE_LLM_ARBITRATION: variável de ambiente para desativar em CI/testes
• HF_MODEL: modelo LLM (padrão: meta-llama/Llama-3.2-3B-Instruct)
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
    from .gazetteer.gazetteer_gdf import carregar_gazetteer_gdf
except ImportError:
    try:
        from gazetteer.gazetteer_gdf import carregar_gazetteer_gdf
    except ImportError:
        import sys, os, json
        def carregar_gazetteer_gdf():
            base_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(base_dir, 'gazetteer', 'gazetteer_gdf.json')
            if not os.path.exists(json_path):
                json_path = os.path.join(base_dir, '..', 'gazetteer', 'gazetteer_gdf.json')
            if not os.path.exists(json_path):
                return set()
            with open(json_path, encoding='utf-8') as f:
                data = json.load(f)
            termos = set()
            for org in data.get('orgaos', []):
                termos.add(org.get('nome', '').strip().lower())
                termos.add(org.get('sigla', '').strip().lower())
                for alias in org.get('aliases', []):
                    termos.add(alias.strip().lower())
            for tipo in ['escolas', 'hospitais', 'programas']:
                for item in data.get(tipo, []):
                    termos.add(item.get('nome', '').strip().lower())
                    termos.add(item.get('sigla', '').strip().lower())
                    for alias in item.get('aliases', []):
                        termos.add(alias.strip().lower())
            return termos

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
    Usa Llama via Hugging Face Inference API para arbitrar casos ambíguos de PII.
    
    O LLM atua como árbitro final em casos onde a votação do ensemble não é conclusiva,
    analisando o contexto para decidir se há risco de reidentificação.
    
    Args:
        texto: Texto sendo analisado
        achados: Lista de PIIs detectados pelo ensemble
        contexto_extra: Contexto adicional opcional
        
    Returns:
        Tuple[str, str]: (decisão, explicação)
            - decisão: 'PII', 'Público' ou 'Indefinido'
            - explicação: Justificativa do LLM
    """
    HF_TOKEN = os.getenv("HF_TOKEN")
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN não encontrado no ambiente. Configure no .env")
    
    # Modelo padrão: Llama-3.2-3B-Instruct (rápido e eficiente)
    # Pode ser sobrescrito via variável de ambiente HF_MODEL
    model = os.getenv("HF_MODEL", "meta-llama/Llama-3.2-3B-Instruct")
    
    # Formata achados para o prompt
    achados_str = "\n".join([
        f"  - Tipo: {a.get('tipo')}, Valor: {a.get('valor')}, Confiança: {a.get('confianca', 0):.2f}"
        for a in achados
    ]) if achados else "  Nenhum PII detectado pelo ensemble."
    
    system_prompt = """Você é um especialista em LGPD (Lei Geral de Proteção de Dados) e proteção de dados pessoais no Brasil.
Sua tarefa é analisar textos e avaliar o RISCO DE REIDENTIFICAÇÃO de pessoas.

=== REGRAS DE CLASSIFICAÇÃO ===

1. NÚMEROS ISOLADOS (BAIXA CRITICIDADE):
   - Um número de processo, matrícula ou protocolo SOZINHO tem baixa criticidade
   - Números sem contexto identificador são difíceis de vincular a uma pessoa
   - Exemplo: "Processo 00001-123456/2024-00" sozinho = BAIXO RISCO

2. COMBINAÇÃO DE DADOS (ALTA CRITICIDADE - REIDENTIFICAÇÃO):
   - Número + Nome no mesmo parágrafo = RISCO DE REIDENTIFICAÇÃO
   - Número + CPF = ALTA CRITICIDADE (identificação direta)
   - Nome + Endereço = ALTA CRITICIDADE
   - Qualquer dado + contexto que permita identificar = PII CRÍTICO
   - Exemplo: "Maria Silva, CPF 123.456.789-00, processo 00001" = CRÍTICO

3. CONTEXTO FUNCIONAL vs PESSOAL:
   - Servidor público em ato funcional (assinatura, despacho) = PÚBLICO
   - Cidadão em manifestação/reclamação = PII (proteger)
   - Servidor mencionado como pessoa física = PII

4. DADOS SENSÍVEIS (SEMPRE PII - LGPD Art. 11):
   - Origem racial/étnica
   - Opinião política, religiosa ou filosófica
   - Dados de saúde (CID, diagnósticos, medicamentos)
   - Dados biométricos
   - Dados de menores de idade

5. VALIDAÇÃO DE DOCUMENTOS:
   - CPF com dígito verificador válido = maior confiança
   - CPF com DV inválido pode ser erro de digitação ou falso positivo
   - Sequências numéricas repetitivas (111.111.111-11) = inválido

=== SAÍDA ESPERADA ===
Responda APENAS no formato:
DECISÃO: [PII ou PÚBLICO]
RISCO: [CRÍTICO, ALTO, MODERADO, BAIXO]
EXPLICAÇÃO: [justificativa em 1-2 linhas, mencione se há risco de reidentificação]"""

    user_prompt = f"""Analise este texto:
"{texto[:1500]}"

ACHADOS DO SISTEMA AUTOMÁTICO:
{achados_str}

{f"CONTEXTO: {contexto_extra}" if contexto_extra else ""}"""

    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(token=HF_TOKEN)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = client.chat_completion(
            messages=messages,
            model=model,
            max_tokens=150,
            temperature=0.1
        )
        
        answer = response.choices[0].message.content.strip()
        
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
        
        # Extrai nível de risco se presente
        risco = "MODERADO"
        for nivel in ["CRÍTICO", "CRITICO", "ALTO", "MODERADO", "BAIXO"]:
            if f"RISCO: {nivel}" in answer_upper:
                risco = nivel.replace("Í", "I")
                break
        
        logger.info(f"[LLM Árbitro] Decisão: {decision}, Risco: {risco} para texto: {texto[:50]}...")
        return decision, answer
        
    except ImportError:
        logger.warning("huggingface_hub não instalado. Execute: pip install huggingface_hub")
        return "Indefinido", "Biblioteca huggingface_hub não instalada"
    except Exception as e:
        logger.warning(f"Erro na chamada ao LLM ({model}): {e}")
        return "Indefinido", f"Erro na API: {str(e)}"


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
            valor = f.get('valor', '')
            if valor is None or not isinstance(valor, str):
                continue
            key = valor.lower().strip()
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

    def _deduplicate_findings(self, findings: List[Dict]) -> List[Dict]:
        """
        Deduplicação avançada de entidades detectadas.
        
        Remove:
        1. Duplicatas exatas (mesmo valor)
        2. Substrings (ex: "Ruth Helena" contido em "Ruth Helena Franco")
        3. Fragmentos de telefone/documento
        4. Valores com palavras-chave erradas (ex: "Ruth Helena Franco CPF")
        
        Mantém sempre o valor mais completo/longo com maior peso.
        """
        if not findings:
            return []
        
        # Primeiro passo: agrupar por tipo similar
        grupos_tipo = {}
        for f in findings:
            tipo = f.get('tipo', 'UNKNOWN')
            # Normaliza tipos de NOME
            tipo_base = 'NOME' if 'NOME' in tipo else tipo
            if tipo_base not in grupos_tipo:
                grupos_tipo[tipo_base] = []
            grupos_tipo[tipo_base].append(f)
        
        resultado_final = []
        
        for tipo_base, grupo in grupos_tipo.items():
            if tipo_base == 'NOME':
                # Deduplicação especial para nomes - remover substrings
                deduplicados = self._deduplicate_names(grupo)
            elif tipo_base in ('TELEFONE', 'CELULAR'):
                # Deduplicação especial para telefones - remover fragmentos
                deduplicados = self._deduplicate_phones(grupo)
            elif tipo_base == 'ENDERECO_RESIDENCIAL':
                # Deduplicação especial para endereços - remover substrings
                deduplicados = self._deduplicate_addresses(grupo)
            else:
                # Deduplicação padrão por valor exato
                deduplicados = self._deduplicate_exact(grupo)
            
            resultado_final.extend(deduplicados)
        
        return resultado_final
    
    def _deduplicate_names(self, findings: List[Dict]) -> List[Dict]:
        """
        Deduplicação de nomes - remove substrings e valores com erros.
        
        Exemplos de remoção:
        - "Ruth Helena" se existe "Ruth Helena Franco" (substring)
        - "Ruth Helena Franco CPF" (contém palavra-chave errada)
        - "Júlio Cesar Alves da" se existe "Júlio Cesar Alves da Rosa" (incompleto)
        """
        if not findings:
            return []
        
        # Palavras que não devem aparecer em nomes
        PALAVRAS_INVALIDAS = {
            'cpf', 'cnpj', 'rg', 'tel', 'telefone', 'celular', 'email', 'e-mail',
            'endereço', 'endereco', 'cep', 'processo', 'sei', 'observação', 'observacao',
            'dados', 'meus', 'atenciosamente', 'att', 'obrigado', 'obrigada',
            # Saudações que não são nomes
            'grata', 'grato', 'cordialmente', 'respeitosamente', 'prezados', 'prezadas',
            # Títulos/cargos que não são nomes
            'residente', 'estudante', 'professor', 'professora', 'doutor', 'doutora',
            # Termos legais que não são nomes
            'inciso', 'artigo', 'parágrafo', 'estatuto', 'ordem', 'advogados', 'brasil',
            'lei', 'decreto', 'portaria', 'resolução', 'resolucao',
            # Frases comuns truncadas
            'gostaria', 'solicito', 'venho', 'requerer', 'informar',
            # Termos de departamentos/setores que não são nomes
            'setor', 'recursos', 'hídricos', 'departamento', 'coordenação', 'diretoria',
            # Termos de lugares/edifícios que não são nomes de pessoas
            'centro', 'atlântica', 'atlantica', 'edifício', 'edificio', 'shopping', 'mall',
            # Palavras truncadas (nome parcial)
            'set'
        }
        
        # Limpa nomes com palavras inválidas e normaliza
        cleaned = []
        for f in findings:
            valor = f.get('valor', '').strip()
            valor_lower = valor.lower()
            
            # Rejeita se contém palavras inválidas (match de palavra inteira, não substring)
            # Importante: "Jorge" não deve ser rejeitado por conter "rg"
            palavras_do_valor = set(valor_lower.split())
            if palavras_do_valor & PALAVRAS_INVALIDAS:  # Interseção de conjuntos
                logger.debug(f"[DEDUP] Nome rejeitado por palavra inválida: {valor}")
                continue
            
            # Para nomes vindos de gatilho (auto-identificação), aceitar mesmo com 1 palavra
            # "Me chamo Braga" é PII mesmo sendo nome simples
            source = f.get('source', '')
            if source == 'gatilho':
                # Gatilho - aceitar nomes de 1 palavra se tiver >= 4 caracteres
                palavras = [p for p in valor.split() if len(p) > 1]
                if len(palavras) >= 1 and len(valor) >= 4:
                    cleaned.append(f)
                else:
                    logger.debug(f"[DEDUP] Nome de gatilho rejeitado por ser muito curto: {valor}")
                continue
            
            # Nomes de outras fontes - rejeita se menos de 2 palavras
            palavras = [p for p in valor.split() if len(p) > 1]
            if len(palavras) < 2:
                logger.debug(f"[DEDUP] Nome rejeitado por ser muito curto: {valor}")
                continue
            
            cleaned.append(f)
        
        if not cleaned:
            return []
        
        # Ordena por tamanho do valor (maior primeiro) e peso
        sorted_findings = sorted(
            cleaned,
            key=lambda x: (len(x.get('valor', '')), x.get('peso', 0)),
            reverse=True
        )
        
        # Remove substrings - mantém apenas os mais longos
        resultado = []
        valores_aceitos = []  # Lista de valores já aceitos (normalizados)
        
        for f in sorted_findings:
            valor = f.get('valor', '').strip()
            valor_norm = ' '.join(valor.lower().split())  # Normaliza espaços
            
            # Verifica se é substring de algum valor já aceito
            is_substring = False
            for aceito in valores_aceitos:
                if valor_norm in aceito or aceito in valor_norm:
                    # Se o atual é maior, substitui
                    if len(valor_norm) > len(aceito):
                        # Remove o menor e adiciona o maior
                        valores_aceitos.remove(aceito)
                        valores_aceitos.append(valor_norm)
                        # Atualiza resultado
                        resultado = [r for r in resultado if ' '.join(r.get('valor', '').lower().split()) != aceito]
                        resultado.append(f)
                    is_substring = True
                    break
            
            if not is_substring:
                valores_aceitos.append(valor_norm)
                resultado.append(f)
        
        logger.debug(f"[DEDUP] Nomes: {len(findings)} -> {len(resultado)}")
        return resultado
    
    def _deduplicate_phones(self, findings: List[Dict]) -> List[Dict]:
        """
        Deduplicação de telefones - remove fragmentos.
        
        Exemplos:
        - "(54)99199-1000" é mantido
        - "54", "99199" são removidos se são fragmentos do número completo
        """
        if not findings:
            return []
        
        # Extrai apenas dígitos para comparação
        def digits_only(valor: str) -> str:
            return ''.join(c for c in valor if c.isdigit())
        
        # Ordena por quantidade de dígitos (mais dígitos = mais completo)
        sorted_findings = sorted(
            findings,
            key=lambda x: (len(digits_only(x.get('valor', ''))), x.get('peso', 0)),
            reverse=True
        )
        
        resultado = []
        digitos_aceitos = []
        
        for f in sorted_findings:
            valor = f.get('valor', '')
            digitos = digits_only(valor)
            
            # Ignora se muito curto (menos de 4 dígitos)
            if len(digitos) < 4:
                logger.debug(f"[DEDUP] Telefone rejeitado por ser muito curto: {valor}")
                continue
            
            # Verifica se é fragmento de algum número já aceito
            is_fragment = False
            for aceito in digitos_aceitos:
                if digitos in aceito:
                    is_fragment = True
                    break
            
            if not is_fragment:
                digitos_aceitos.append(digitos)
                resultado.append(f)
        
        logger.debug(f"[DEDUP] Telefones: {len(findings)} -> {len(resultado)}")
        return resultado
    
    def _deduplicate_addresses(self, findings: List[Dict]) -> List[Dict]:
        """
        Deduplicação de endereços - remove substrings contidos em outros.
        Mantém apenas o endereço mais completo.
        """
        if not findings:
            return []
        
        # Ordena por comprimento decrescente
        ordenados = sorted(findings, key=lambda x: len(x.get('valor', '')), reverse=True)
        resultado = []
        
        for f in ordenados:
            valor = f.get('valor', '').lower().strip()
            # Verifica se este valor é substring de algum já aceito
            eh_substring = False
            for r in resultado:
                r_valor = r.get('valor', '').lower().strip()
                if valor in r_valor:
                    eh_substring = True
                    break
            if not eh_substring:
                resultado.append(f)
        
        logger.debug(f"[DEDUP] Endereços: {len(findings)} -> {len(resultado)}")
        return resultado
    
    def _deduplicate_exact(self, findings: List[Dict]) -> List[Dict]:
        """Deduplicação por valor exato - mantém o de maior peso."""
        if not findings:
            return []
        
        por_valor = {}
        for f in findings:
            key = f.get('valor', '').lower().strip()
            peso = f.get('peso', 0)
            if key and (key not in por_valor or peso > por_valor[key].get('peso', 0)):
                por_valor[key] = f
        
        return list(por_valor.values())

    def _gerar_explicacao(self, finding: Dict, texto: str) -> Dict:
        """
        Gera explicação detalhada para um PII detectado (XAI - Explainable AI).
        
        Retorna um dicionário com:
        - motivos: lista de razões para a detecção
        - fontes: quais engines detectaram
        - validacoes: validações aplicadas (DV, formato, etc.)
        - contexto: contexto que reforçou a detecção
        """
        tipo = finding.get('tipo', '')
        valor = finding.get('valor', '')
        confianca = finding.get('confianca', 0)
        source = finding.get('source', 'unknown')
        peso = finding.get('peso', 0)
        inicio = finding.get('inicio', 0)
        fim = finding.get('fim', len(valor))
        votacao_motivo = finding.get('votacao_motivo', '')
        
        motivos = []
        validacoes = []
        contexto_detectado = []
        
        # === VALIDAÇÕES POR TIPO ===
        if tipo == 'CPF':
            motivos.append("✓ Formato XXX.XXX.XXX-XX identificado")
            # Verificar DV
            digitos = ''.join(c for c in valor if c.isdigit())
            if len(digitos) >= 11:
                if self._validar_cpf(digitos[:11]):
                    validacoes.append("✓ Dígito verificador válido (mod 11)")
                else:
                    validacoes.append("⚠ Dígito verificador inválido (possível erro de digitação)")
        
        elif tipo == 'CNPJ':
            motivos.append("✓ Formato XX.XXX.XXX/XXXX-XX identificado")
            digitos = ''.join(c for c in valor if c.isdigit())
            if len(digitos) >= 14:
                if self._validar_cnpj(digitos[:14]):
                    validacoes.append("✓ Dígito verificador válido")
                else:
                    validacoes.append("⚠ Dígito verificador inválido")
        
        elif tipo in ['TELEFONE', 'CELULAR']:
            digitos = ''.join(c for c in valor if c.isdigit())
            if len(digitos) >= 10:
                motivos.append("✓ Telefone com DDD identificado")
            elif len(digitos) >= 8:
                motivos.append("✓ Telefone sem DDD identificado")
            if digitos.startswith('9') or (len(digitos) >= 3 and digitos[2] == '9'):
                validacoes.append("✓ Padrão de celular (começa com 9)")
        
        elif tipo == 'EMAIL_PESSOAL':
            motivos.append("✓ Formato de email identificado")
            if not any(d in valor.lower() for d in ['.gov.br', '.org.br', '.edu.br']):
                validacoes.append("✓ Domínio pessoal (não institucional)")
        
        elif tipo == 'NOME':
            motivos.append("✓ Nome próprio identificado")
            if source == 'bert':
                validacoes.append("✓ Confirmado por modelo BERT NER")
            elif source == 'nuner':
                validacoes.append("✓ Confirmado por modelo NuNER")
            elif source == 'spacy':
                validacoes.append("✓ Confirmado por spaCy NER")
        
        elif tipo == 'ENDERECO_RESIDENCIAL':
            motivos.append("✓ Endereço residencial identificado")
            if any(s in valor.upper() for s in ['SQN', 'SQS', 'SHIN', 'SHIS', 'QNM', 'CLSW']):
                validacoes.append("✓ Padrão de endereço de Brasília/DF")
        
        elif tipo == 'PROCESSO_SEI':
            motivos.append("✓ Número de processo SEI/GDF identificado")
            validacoes.append("✓ Formato XXXXX-XXXXXXXX/AAAA-XX")
        
        elif tipo == 'DADO_SAUDE':
            motivos.append("✓ Dado de saúde sensível (LGPD Art. 5º, II)")
            validacoes.append("⚠ Categoria especial - proteção reforçada")
        
        elif tipo == 'MENOR_IDENTIFICADO':
            motivos.append("✓ Menor de idade identificado")
            validacoes.append("⚠ Proteção especial (ECA + LGPD)")
        
        elif tipo == 'CONTA_BANCARIA':
            motivos.append("✓ Dados bancários identificados")
            validacoes.append("✓ Contexto bancário detectado")
        
        elif tipo in ['RG', 'CNH', 'PIS', 'CTPS', 'PASSAPORTE']:
            motivos.append(f"✓ Documento {tipo} identificado")
            validacoes.append("✓ Formato válido")
        
        else:
            motivos.append(f"✓ {tipo} identificado por padrão")
        
        # === ANÁLISE DE CONTEXTO ===
        if inicio > 0 or fim < len(texto):
            ctx_antes = texto[max(0, inicio-50):inicio].lower()
            ctx_depois = texto[fim:min(len(texto), fim+50)].lower()
            
            # Detectar gatilhos de contexto
            gatilhos_pessoais = ['meu', 'minha', 'moro', 'resido', 'telefone', 'celular', 'contato', 'cpf', 'email']
            for g in gatilhos_pessoais:
                if g in ctx_antes or g in ctx_depois:
                    contexto_detectado.append(f"✓ Contexto pessoal: '{g}' encontrado")
                    break
        
        # === INFORMAÇÃO SOBRE FONTE ===
        fontes_info = []
        if source == 'regex':
            fontes_info.append("Regex (padrão)")
        elif source == 'bert':
            fontes_info.append("BERT NER (monilouise/ner_news_portuguese)")
        elif source == 'nuner':
            fontes_info.append("NuNER (numind/NuNER_Zero)")
        elif source == 'spacy':
            fontes_info.append("spaCy (pt_core_news_lg)")
        elif source == 'presidio':
            fontes_info.append("Presidio Analyzer")
        elif source == 'gatilho':
            fontes_info.append("Gatilho linguístico contextual")
        else:
            fontes_info.append(source)
        
        # === MOTIVO DA VOTAÇÃO ===
        if votacao_motivo:
            motivo_legivel = {
                'documento_validado': '✓ Documento com validação de integridade',
                'dado_sensivel_lgpd': '✓ Dado sensível LGPD (proteção especial)',
                'peso_alto': '✓ Alta relevância (peso ≥ 4)',
                'gatilho_linguistico': '✓ Contexto linguístico confirma PII',
                'votacao_2_fontes': '✓ Confirmado por 2+ engines',
                'votacao_3_fontes': '✓ Confirmado por 3+ engines',
                'alta_confianca': '✓ Alta confiança (≥ 85%)',
                'confianca_moderada_evitar_fn': '⚠ Confiança moderada (70-85%)',
            }.get(votacao_motivo, votacao_motivo)
            motivos.append(motivo_legivel)
        
        return {
            'motivos': motivos,
            'fontes': fontes_info,
            'validacoes': validacoes,
            'contexto': contexto_detectado,
            'confianca_percent': f"{confianca*100:.1f}%",
            'peso': peso
        }

    def _adicionar_explicacoes(self, findings: List[Dict], texto: str) -> List[Dict]:
        """Adiciona explicações a todos os findings."""
        for f in findings:
            f['explicacao'] = self._gerar_explicacao(f, texto)
        return findings

    def __init__(
        self,
        usar_gpu: bool = True,
        use_probabilistic_confidence: bool = True,
        use_llm_arbitration: bool = True
    ):
        """
        Inicializa o detector de PII.
        
        Args:
            usar_gpu: Se deve usar GPU para modelos NER
            use_probabilistic_confidence: Se deve usar sistema de confiança probabilística
            use_llm_arbitration: Se deve usar Llama-3.2-3B para arbitrar casos ambíguos (ATIVADO por padrão - requer HF_TOKEN)
        """
        # Configurações
        self.usar_gpu = usar_gpu
        self.use_probabilistic_confidence = use_probabilistic_confidence
        self.use_llm_arbitration = use_llm_arbitration
        
        # Thresholds dinâmicos por tipo de PII
        self.THRESHOLDS_DINAMICOS = {
            "CPF": {"peso_min": 3, "confianca_min": 0.60},  # Mais permissivo - LGPD aceita formato
            "CNPJ": {"peso_min": 2, "confianca_min": 0.55},  # Mais permissivo - LGPD aceita formato
            "CNPJ_PESSOAL": {"peso_min": 2, "confianca_min": 0.55},  # Mais permissivo
            "PROCESSO_SEI": {"peso_min": 1, "confianca_min": 0.55},  # Permissivo - referência a processo
            "PROTOCOLO_LAI": {"peso_min": 1, "confianca_min": 0.55},  # Permissivo
            "PROTOCOLO_OUV": {"peso_min": 1, "confianca_min": 0.55},  # Permissivo
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

            # CPF: aceita 1 ou 2 dígitos finais (para erro de digitação)
            'CPF': (
                r'\b(\d{3}[\.\s\-]?\d{3}[\.\s\-]?\d{3}[\-\.\s]?\d{1,2})\b',
                re.IGNORECASE
            ),

            'CNPJ': (
                r'(\b\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[/\.\s]?\d{4}[\-\.\s]?\d{2}\b|\b\d{14}\b)',
                re.IGNORECASE
            ),

            'PROCESSO_SEI': (
                # Padrões abrangentes para processos SEI/GDF:
                # - 00015-01009853/2026-01 (5-8/4-2)
                # - 56478.000012/2026-05 (5.6/4-2 com ponto)
                # - 0315-000009878/2023-15 (4-9/4-2)  
                # - 589642/2018-58 (6/4-2 sem hífen inicial)
                # - 0032185265/2024 (10/4 sem hífen)
                # - 1002-853241/2019 (4-6/4)
                r'(?:'
                r'\d{4,5}[-\.]\d{5,10}/\d{4}(?:-\d{2})?|'     # Com hífen/ponto: XXXXX-XXXXXXXX/YYYY-ZZ
                r'\d{5,13}/\d{4}(?:-\d{2})?|'                  # Sem hífen: XXXXX.../YYYY-ZZ  
                r'\d{4}-\d{5,10}/\d{4}(?:-\d{2})?'             # 4 dígitos iniciais: XXXX-XXXXX/YYYY-ZZ
                r')',
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

            # PATCH: CNH agora EXIGE contexto explícito para evitar falsos positivos
            # Aceita 9-12 dígitos quando tem CNH/MINHA/MEU no contexto
            'CNH': (
                r'(?:CNH|CARTEIRA DE MOTORISTA|HABILITA[CÇ][AÃ]O|MINHA CNH|MEU DOCUMENTO)[^\d]{0,15}([0-9]{9,12})(?!\d)',
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
            
            # Registro Acadêmico (RA) - usado em universidades
            'REGISTRO_ACADEMICO': (
                r'(?:RA|REGISTRO\s+ACAD[ÊE]MICO|MATR[ÍI]CULA\s+ESTUDANTE)[\s:]*'
                r'(\d{8,14})',
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
                # Formatos:
                # - CTPS: 1234567/12345-DF (clássico)
                # - CTPS: 65421 - Série: 00123/DF (com série separada)
                # - CTPS 12345678 (apenas números)
                r'(?:CTPS|CARTEIRA DE TRABALHO)[\s:]*'
                r'(?:(\d{5,7}[/\-]\d{4,5}[\-]?[A-Z]{2})|'
                r'(\d{4,7})[\s\-]+(?:S[ée]rie[\s:]*)?(\d{4,5})[/\-]?([A-Z]{2})?|'
                r'(\d{5,8}))',
                re.IGNORECASE
            ),
            
            'CERTIDAO': (
                r'\b(\d{6}[\.\s]?\d{2}[\.\s]?\d{2}[\.\s]?\d{4}[\.\s]?\d[\.\s]?'
                r'\d{5}[\.\s]?\d{3}[\.\s]?\d{7}[\-\.\s]?\d{2})\b',
                re.IGNORECASE
            ),
            
            'REGISTRO_PROFISSIONAL': (
                r'\b(CRM|OAB|CREA|CRO|CRP|CRF|COREN|CRC)[\/\-\s]*'
                r'([A-Z]{2})?[\s\/\-]*(?:sob\s+)?(?:n[ºo°]?\s*)?(\d{2,6}(?:[.\-]\d+)?)',
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
                # Captura celulares com ou sem DDD, com ou sem parênteses
                # Exemplos: (54)99199-1000, 54 99199-1000, 99199-1000, (11) 91234-5678
                r'(?<!\d)\(?(\d{2})\)?[\s\-]?9\d{4}[\s\-]?\d{4}(?!\d)',
                re.IGNORECASE
            ),
            
            # NOVO: Celular sem formatação (10-11 dígitos grudados: 6199998888 ou 61999998888)
            'CELULAR_SEM_FORMATACAO': (
                r'(?<!\d)(\d{2}9?\d{7,8})(?!\d)',
                re.IGNORECASE
            ),
            
            'TELEFONE_CURTO': (
                # Captura telefone sem DDD - só usar se não houver match maior
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
            
            # NOVO: Telefone com DDD com zero (061 99999 8888)
            'TELEFONE_DDD_ZERO': (
                r'(?<!\d)(0\d{2})[\s]+(9?\d{4,5})[\s\-]?(\d{4})(?!\d)',
                re.IGNORECASE
            ),
            
            # NOVO: Telefone com hífen no DDD (ex: 21-1205-1999, 61-99999-8888)
            'TELEFONE_DDD_HIFEN': (
                r'(?<!\d)(\d{2})-(\d{4,5})-(\d{4})(?!\d)',
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
                r'(?:casa|apto?|apartamento|lote|lt|bloco|quadra|área|area)[\s\.]*'
                r'(?:n[ºo°]?[\s\.]*)?[\d]+[a-z]?)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # NOVO: Endereço genérico com "Moro na/em" + localização
            'ENDERECO_MORO_EM': (
                r'(?:moro\s+(?:na|no|em)|resido\s+(?:na|no|em))\s+'
                r'([A-ZÀ-Ú][a-záéíóúàèìòùâêîôûãõ\s]+(?:,\s*)?(?:Lt|Lote|Casa|Bloco|Quadra|Área|Area|Conjunto|Conj)?\.?\s*\d+[A-Za-z]?)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # NOVO: Endereço com contexto pessoal explícito
            # Detecta: "me encontrar na", "entrega em minha casa", "venha ao meu endereço", etc.
            'ENDERECO_CONTEXTO_PESSOAL': (
                r'(?:'
                r'(?:me\s+)?encontrar\s+(?:na|no|em)|'
                r'venha?\s+(?:na|no|em|ao)|'
                r'vou\s+estar\s+(?:na|no|em)|'
                r'fico\s+(?:na|no|em)|'
                r'estou\s+(?:na|no|em)|'
                r'entrega\s+(?:na|no|em)|'
                r'buscar\s+(?:na|no|em)|'
                r'pegar\s+(?:na|no|em)'
                r')\s+'
                r'([A-ZÀ-Ú][a-záéíóúàèìòùâêîôûãõ\s]*(?:SQ[NS]|SH[IL]N|SRES|QN[MN]|CL[NS]W|SCLR?[NS]|SCRLN|Asa\s+(?:Sul|Norte)|Rua|Av\.?|Avenida|Alameda|Travessa)[^\n,]{0,60})',
                re.IGNORECASE | re.UNICODE
            ),
            
            # NOVO: Endereço com label "endereço:" seguido de localização
            'ENDERECO_LABEL': (
                r'(?:endere[cç]o\s*:)\s*'
                r'([^,\n]+(?:,\s*(?:Rua|Av|R\.|Lote|Lt|Casa|Bloco|Quadra|N[ºo°]?|CEP)[^,\n]*)+)',
                re.IGNORECASE | re.UNICODE
            ),
            
            'ENDERECO_BRASILIA': (
                r'(?:moro|resido|minha casa|meu endere[cç]o|minha resid[eê]ncia|resid[eê]ncia:?)[^\n]{0,30}?'
                r'(?:Q[INRSEMSAB]\s*\d+|SQS\s*\d+|SQN\s*\d+|SRES\s*\d+|SHIS\s*QI\s*\d+|'
                r'SHIN\s*QI\s*\d+|QNM\s*\d+|QNN\s*\d+|Conjunto\s+[A-Z]\s+Casa\s+\d+)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # SHIN/SHIS/SHLP/SHLN - áreas residenciais de alto padrão em Brasília
            'ENDERECO_SHIN_SHIS': (
                r'\b(SHIN|SHIS|SHLP|SHLN)\s*QI\s*\d+\s*(?:Conjunto|Conj\.?)?\s*\d*',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Setores habitacionais e administrativos do DF (SHDF, SAS, SCS, SDS, etc.)
            # Ex: "shdf 602 - 607", "SAS QUADRA 15 BLC A"
            'ENDERECO_SETOR_DF': (
                r'\b(SHDF|SHCE|SHCG|SHIS|SHIN|SHN|SHS|SAS|SCS|SDS|SBS|SCN|SEN|SGO|SIA|SIG)'
                r'\s*(?:QUADRA|QD\.?|Q\.?)?\s*\d+(?:\s*[\-\/]\s*\d+)?'
                r'(?:\s*(?:BLC|BLOCO|BL\.?|CONJ|CONJUNTO)?\s*[A-Z0-9]+)?',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Endereço comercial do DF com contexto de moradia (inquilina/imóvel localizado)
            # Ex: "Sou inquilina do imóvel localizado na CRN 104 Bloco I loja 15"
            'ENDERECO_DF_RESIDENCIAL': (
                r'(?:inquilin[oa]|im[oó]vel\s+localizado|moro|resido)[^\n]{0,50}?'
                r'((?:CRN|CLN|CLS|SCLN|SCRN|SCRS|SCLS)\s*\d+\s*(?:Bloco|Bl\.?)\s*[A-Z]\s*'
                r'(?:loja|sala|apt\.?|apartamento)?\s*\d+)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # CEP com ou sem formatação, com espaços variados
            # Formatos aceitos: 12345-678, 12345 - 678, 12.345 - 678, 12.345-678, 12345678
            # NOVO: 29. 192 - 170 (com ponto e espaços)
            'CEP': (
                r'\b(?:CEP\s*:?\s*)?(\d{2}\.?\s*\d{3}\s*[\-\s]+\s*\d{3}|\d{5}[\-\s]+\d{3}|\d{8})\b',
                re.IGNORECASE
            ),
            
            # === PADRÕES GDF ===
            
            # PROCESSO_SEI - Padrões abrangentes baseados em casos reais:
            # - 00015-01009853/2026-01 (5-8/4-2)
            # - 56478.000012/2026-05 (5.6/4-2 com ponto)
            # - 589642/2018-58 (6/4-2 sem hífen inicial)
            # - 0032185265/2024 (10/4 sem hífen)
            'PROCESSO_SEI': (
                r'(?:'
                r'\d{4,5}[-\.]\d{5,10}/\d{4}(?:-\d{2})?|'     # Com hífen/ponto
                r'\d{5,13}/\d{4}(?:-\d{2})?|'                  # Sem hífen
                r'\d{4}-\d{5,10}/\d{4}(?:-\d{2})?'             # 4 dígitos iniciais
                r')',
                re.IGNORECASE
            ),
            
            'PROTOCOLO_LAI': (
                r'\bLAI-?\d{5,8}/?\d{0,4}\b',
                re.IGNORECASE
            ),
            
            'PROTOCOLO_OUV': (
                r'\bOUV-\d{5,8}/\d{4}\b',
                re.IGNORECASE
            ),
            
            # Protocolo genérico com ponto (000254.2012-56)
            'PROTOCOLO_GENERICO': (
                r'PROTOCOLO[:\s]+([\d]{5,6}[\.]\d{4}[-]\d{2})',
                re.IGNORECASE
            ),
            
            # Protocolo DFP (Junta Comercial DF)
            'PROTOCOLO_DFP': (
                r'\bDFP\d{10,12}\b',
                re.IGNORECASE
            ),
            
            # NIRE - Número de Identificação do Registro de Empresa
            'NIRE': (
                r'(?:nire|n\.i\.r\.e\.)[\s:]*(\d{10,11}[-]?\d?)',
                re.IGNORECASE
            ),
            
            # MATRICULA_IMOVEL - Matrícula de imóvel em cartório (654.789 8ºRI)
            # EXIGE sufixo RI para não conflitar com matrícula de servidor
            'MATRICULA_IMOVEL': (
                r'(?:matr[ií]cula)(?:\s+(?:n[ºo°]?|do\s+im[óo]vel))?[\s:]*n?[ºo°]?\s*(\d{1,3}[\.]\d{3})\s+\d{1,2}[ºo°]?\s*RI',
                re.IGNORECASE
            ),
            
            # CDA - Certidão de Dívida Ativa (aceita singular e plural)
            'CDA': (
                r'(?:CDA|Certid[oõaã][eo]?s?\s+de\s+D[ií]vida\s+Ativa)[\s:]*n?[ºo°]?\s*(\d{8,13})',
                re.IGNORECASE
            ),
            # CDA adicional - número após "e" no contexto de dívida ativa
            'CDA_ADICIONAL': (
                r'(?:D[ií]vida\s+Ativa[^\n]{0,60})\s+e\s+(\d{8,13})',
                re.IGNORECASE
            ),
            
            # Auto de Infração GDF - inclui Auto de Infração Demolitória (H-1564-685324-OEU)
            'AUTO_INFRACAO': (
                r'(?:Auto\s+[Dd]e\s+Infra[cç][aã]o(?:\s+Demolit[óo]ria)?|Autua[cç][aã]o)[\s:]*n?[ºo°]?\s*([A-Z]?[-]?\d{3,5}[-]\d{5,10}[-]?[A-Z]{0,5}|[A-Z]?\d{5,10}[-]?[A-Z]*)',
                re.IGNORECASE
            ),
            
            # MATRICULA_SERVIDOR: EXIGE contexto para evitar conflito com inscrição imobiliária
            # Aceita contextos como "matrícula do servidor:", "matrícula funcional:", "matrícula:"
            'MATRICULA_SERVIDOR': (
                r'(?:matr[ií]cula|mat\.?)(?:\s+(?:do\s+)?(?:servidor|funcional))?[\s:]*n?[ºo°]?\s*(\d{2,3}[\.-]\d{3}[\.-]?\d?[A-Z]?|\d{5,8}[A-Z]?)',
                re.IGNORECASE
            ),
            
            # Ocorrência policial - 14-18 dígitos começando com 2 (formato ano: 20xx, 21xx, 22xx, etc)
            'OCORRENCIA_POLICIAL': (
                r'\b(2[0-9]\d{12,16})\b',
                re.IGNORECASE
            ),
            
            # INSCRICAO_IMOVEL: 15 dígitos isolados OU label + 6-9 dígitos
            'INSCRICAO_IMOVEL_15': (
                r'\b(\d{15})\b',
                re.IGNORECASE
            ),
            'INSCRICAO_IMOVEL_LABEL': (
                r'inscri[cç][ãa]o(?:\s*im[oó]vel|\s*IPTU)?[\s\-:]*n?[ºo°]?\s*(\d{6,15})',
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
                r'(?:'
                r'(?:nasc|nascimento|nascido|data de nascimento|d\.?n\.?)[\s:]*(?:em\s+)?(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})'
                r'|'
                r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*\)?\s*\.?\s*(?:nascimento|nasc|nascido)'
                r')',
                re.IGNORECASE
            ),
            
            # Nome após título acadêmico/profissional (Profª, Drª, Dr., Msc., etc.)
            # O nome deve começar com letra maiúscula logo após o título
            'NOME_TITULO': (
                r'(?:Prof[ªaº]?\.?|Dr[ªaº]?\.?|Msc\.?|Me\.?|Dout[oa]r[ªaº]?\.?)[,\s]+([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+(?:(?:de|da|do|dos|das|e)\s+)?[A-ZÀ-Ÿ][a-zà-ÿ]+)+)',
                re.UNICODE
            ),
            
            # Nome em assinatura (linha com underscores seguida de nome próprio)
            # O nome deve ter formato "Nome Sobrenome" com letras maiúsculas
            'NOME_ASSINATURA': (
                r'_{10,}\s*([A-ZÀ-Ÿ][a-zà-ÿ]+\s+(?:(?:de|da|do|dos|das|e)\s+)?[A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+(?:(?:de|da|do|dos|das|e)\s+)?[A-ZÀ-Ÿ][a-zà-ÿ]+){0,3})',
                re.UNICODE
            ),
            
            # Nome após cargo público (funcionário público, servidor público)
            'NOME_CARGO': (
                r'(?:servidor[a]?|funcionári[oa])\s+(?:públic[oa])?\s*([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+(?:(?:de|da|do|dos|das|e)\s+)?[A-ZÀ-Ÿ][a-zà-ÿ]+)+)',
                re.UNICODE
            ),
            
            # Nome em contexto de condomínio/edifício/residencial
            'NOME_CONDOMINIO': (
                r'(?:Condom[ií]nio|Edif[ií]cio|Residencial)(?:\s+Municipal)?\s+([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+(?:(?:de|da|do|dos|das|e)\s+)?[A-ZÀ-Ÿ][a-zà-ÿ]+)+)',
                re.UNICODE
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
                r'(?:ag[êe]ncia|ag\.?)\s*(\d{3,5})[\s,]*(?:conta(?:\s*corrente)?|c/?c|c\.c\.?)[\s:]*(\d{4,12}[\-]?[\dXx]?)|'
                r'(?:conta(?:\s*corrente)?|c/?c|c\.c\.?)[\s:]*(\d{4,12}[\-]?[\dXx]?)[\s,]*(?:ag[êe]ncia|ag\.?)[\s:]*(\d{3,5})|'
                r'(?:dep[óo]sito|transferir)[^\n]{0,30}(?:conta)[\s:]*(\d{4,12}[\-]?[\dXx]?)[^\n]{0,20}(?:ag\.?|ag[êe]ncia)[\s:]*(\d{3,5})'
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
                r'(?:diagn[oó]stico|tratamento)\s+(?:de\s+|realizado\s+(?:de\s+)?)?(?:HIV|AIDS|cancer|câncer|diabetes|epilepsia)'
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
                # Detecta menores de idade com contexto claro
                # Padrão 1: "paciente/criança/filho Maria, 8 anos"
                # Padrão 2: "Maria, 8 anos, estudante/criança"
                # Inclui: paciente, menino, menina, criança, filho, filha, aluno, aluna, estudante, menor, bebê, neto, sobrinho
                r'(?:'
                r'(?:paciente|menin[oa]|crian[çc]a|filh[oa]|alun[oa]|estudante|menor|beb[êe]|net[oa]|sobrinh[oa])\s+([A-Z][a-záéíóúàâêôãõç]+(?:\s+[A-Z][a-záéíóúàâêôãõç]+)*)[\s,]+(?:de\s+)?(\d{1,2})\s*anos?|'
                r'([A-Z][a-záéíóúàâêôãõç]+)[\s,]+(\d{1,2})\s*anos[\s,]+(?:estudante|alun[oa]|crian[çc]a|menor|paciente)'
                r')',
                re.IGNORECASE | re.UNICODE
            ),
            
            # NOVO: Conta bancária com contexto explícito "Conta bancária/corrente/poupança"
            # Detecta: "Conta bancaria 12345-6 Ag 0001"
            # Não detecta: "conta de luz", "levando em conta"
            'CONTA_BANCARIA_CONTEXTUAL': (
                r'[Cc]onta\s*(?:bancária|bancaria|corrente|poupan[çc]a)\s*[:\s]*(\d[\d\.\-/]+)(?:\s*[-,]?\s*[Aa]g(?:ência|encia|\.?)?\s*[:\s]*(\d[\d\.\-/]+))?',
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
        """Inicializa o Presidio Analyzer para entidades complementares.
        
        Presidio é usado APENAS para detectar entidades que nosso sistema
        não cobre bem: IP_ADDRESS, IBAN_CODE, CREDIT_CARD, URL.
        
        NÃO registramos nossos patterns aqui pois já temos:
        - Regex próprio (53 patterns pt-BR)
        - NER BERT (monilouise/ner_news_portuguese)
        - NER NuNER (pt-BR)
        - NER spaCy (pt_core_news_lg)
        """
        try:
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            
            # Configura Presidio com modelo pt-BR (já instalado no Dockerfile)
            # Reutiliza o pt_core_news_lg que já temos
            configuration = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}]
            }
            
            provider = NlpEngineProvider(nlp_configuration=configuration)
            nlp_engine = provider.create_engine()
            
            self.presidio_analyzer = AnalyzerEngine(
                nlp_engine=nlp_engine,
                supported_languages=["pt"]
            )
            
            # NÃO registra nossos patterns - evita duplicação
            # Presidio serve apenas como complemento para tipos específicos
            
            logger.info("✅ Presidio Analyzer inicializado (pt-BR, modo complementar)")
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
        
        # Apenas palavras que realmente indicam CPF fictício/exemplo
        # Removido: PROCESSO, PROTOCOLO, SEI (aparecem em contextos legítimos de identificação)
        palavras_negativas = {
            "INVALIDO", "INVÁLIDO", "FALSO", "FICTICIO", "FICTÍCIO",
            "EXEMPLO", "TESTE", "FAKE", "GENERICO", "GENÉRICO",
            "000.000.000-00", "111.111.111-11", "XXX.XXX.XXX-XX",
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
        """Valida CPF: exige 11 dígitos e DV correto."""
        if self.validador and hasattr(self.validador, 'validar_cpf'):
            return self.validador.validar_cpf(cpf)
        numeros = re.sub(r'[^\d]', '', cpf)
        if len(numeros) != 11:
            return False
        if len(set(numeros)) == 1:
            return False
        # Validação de DV básica (fallback)
        soma = sum(int(numeros[i]) * (10 - i) for i in range(9))
        d1 = (soma * 10) % 11
        d1 = 0 if d1 >= 10 else d1
        if int(numeros[9]) != d1:
            return False
        soma = sum(int(numeros[i]) * (11 - i) for i in range(10))
        d2 = (soma * 10) % 11
        d2 = 0 if d2 >= 10 else d2
        return int(numeros[10]) == d2
    
    def _validar_cnpj(self, cnpj: str) -> bool:
        """Valida CNPJ com dígito verificador completo (algoritmo oficial)."""
        if self.validador and hasattr(self.validador, 'validar_cnpj'):
            return self.validador.validar_cnpj(cnpj)
        
        numeros = re.sub(r'[^\d]', '', cnpj)
        if len(numeros) != 14:
            return False
        # Rejeita sequências repetidas (00.000.000/0000-00, 11.111.111/1111-11, etc)
        if len(set(numeros)) == 1:
            return False
        
        # Validação do primeiro dígito verificador
        pesos_d1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(numeros[i]) * pesos_d1[i] for i in range(12))
        resto = soma % 11
        d1 = 0 if resto < 2 else 11 - resto
        if int(numeros[12]) != d1:
            return False
        
        # Validação do segundo dígito verificador
        pesos_d2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(numeros[i]) * pesos_d2[i] for i in range(13))
        resto = soma % 11
        d2 = 0 if resto < 2 else 11 - resto
        return int(numeros[13]) == d2
    
    def _detectar_regex(self, texto: str) -> List[Dict]:
        """Detecção por regex com validação de dígito verificador."""
        findings = []
        for tipo, pattern in self.patterns_compilados.items():
            for match in pattern.finditer(texto):
                # Para tipos bancários, reconstruir valor a partir de todos os grupos capturados
                if tipo in ['DADOS_BANCARIOS', 'CONTA_BANCARIA']:
                    grupos = [g for g in match.groups() if g]
                    if grupos:
                        # Monta string legível (ex: Conta 12345-6 Ag 1234)
                        if tipo == 'DADOS_BANCARIOS':
                            if len(grupos) == 4:
                                valor = f"Conta {grupos[2]} Ag {grupos[3]}"
                            elif len(grupos) == 2:
                                valor = f"Agência {grupos[0]} Conta {grupos[1]}"
                            elif len(grupos) == 3:
                                valor = f"Depósito/Transferência Ag {grupos[0]} CC {grupos[2]}"
                            else:
                                valor = ' '.join(grupos)
                        else:
                            valor = ' '.join(grupos)
                    else:
                        valor = match.group()
                    inicio, fim = match.start(), match.end()
                else:
                    # Para telefones, usar match completo ao invés do grupo capturado
                    # Isso evita pegar só o DDD ao invés do número completo
                    if tipo in ['CELULAR', 'TELEFONE_FIXO', 'TELEFONE_DDI', 'TELEFONE_DDD_ESPACO', 
                                'TELEFONE_LOCAL', 'TELEFONE_INTERNACIONAL', 'TELEFONE_CURTO',
                                'TELEFONE_DDD_HIFEN', 'CELULAR_SEM_FORMATACAO', 'TELEFONE_DDD_ZERO']:
                        valor = match.group()
                    # Para ENDERECO_SETOR_DF, usar match completo (grupo 1 é só a sigla)
                    elif tipo == 'ENDERECO_SETOR_DF':
                        valor = match.group()
                    # Para DATA_NASCIMENTO, pegar o grupo que não é None
                    elif tipo == 'DATA_NASCIMENTO':
                        valor = match.group(1) or match.group(2) or match.group()
                    # Para REGISTRO_PROFISSIONAL (OAB/CRM/etc), montar valor completo
                    elif tipo == 'REGISTRO_PROFISSIONAL':
                        grupos = match.groups()  # (tipo_registro, uf, numero)
                        tipo_reg = grupos[0].upper() if grupos[0] else ''
                        uf = grupos[1].upper() if grupos[1] else ''
                        numero = grupos[2] if grupos[2] else ''
                        if uf and numero:
                            valor = f"{tipo_reg}/{uf} {numero}"
                        elif numero:
                            valor = f"{tipo_reg} {numero}"
                        else:
                            valor = match.group()
                    else:
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

                # --- HEURÍSTICA CPF ---
                if tipo == 'CPF':
                    contexto = texto[max(0, inicio-60):fim+60].lower()
                    contexto_positivo = any(
                        kw in contexto for kw in [
                            "meu cpf", "minha cpf", "conforme cadastro", "precisa ser verificado", 
                            "cpf do titular", "cpf contribuinte", "cadastrado com cpf", "cpf formato real", 
                            "cpf com dígito", "cpf com dv", "cpf:", "contribuinte cpf", "titular do cpf",
                            "contribuinte", "titular", "o cpf", "seu cpf", "informou seu cpf",
                            "nome:", "e-mail:", "email:", "telefone:", "fone:", "celular:", "endereço:",
                            "cpf da mãe", "cpf do pai", "cpf mãe", "cpf pai", "filiação"
                        ]
                    )
                    contexto_negativo = self._contexto_negativo_cpf(texto, valor)
                    
                    # PATCH: Se o contexto imediatamente antes é "processo", não é CPF - é número de processo
                    contexto_antes = texto[max(0, inicio-20):inicio].lower()
                    if re.search(r'\bprocesso\s*$', contexto_antes):
                        logger.debug(f"[CPF] Ignorado por contexto 'processo': {valor}")
                        continue
                    
                    # Nunca marca exemplos/fictícios como PII
                    if contexto_negativo:
                        continue
                    # LGPD: Detectar CPF pelo FORMATO mesmo se matematicamente inválido
                    # CPFs com formato XX.XXX.XXX-XX são PII independente dos dígitos verificadores
                    cpf_valido = self._validar_cpf(valor)
                    cpf_limpo = re.sub(r'\D', '', valor)
                    formato_correto = len(cpf_limpo) == 11 and cpf_limpo != cpf_limpo[0] * 11
                    
                    # Aceita se: formato correto OU contexto positivo
                    if not formato_correto and not contexto_positivo:
                        continue
                    
                    # Calcula confiança baseada em validação + contexto
                    confianca = self._calcular_confianca("CPF", texto, inicio, fim)
                    if not cpf_valido:
                        confianca = max(0.6, confianca * 0.8)  # Reduz mas mantém detectável
                    
                    findings.append({
                        "tipo": "CPF", "valor": valor, "confianca": confianca,
                        "peso": 5 if cpf_valido else 3, "inicio": inicio, "fim": fim
                    })

                # --- HEURÍSTICA PROCESSO SEI ---
                elif tipo in ['PROCESSO_SEI', 'PROTOCOLO_LAI', 'PROTOCOLO_OUV', 'PROTOCOLO_EXTRA', 'PROTOCOLO_GENERICO']:
                    from text_unidecode import unidecode
                    contexto = texto[max(0, inicio-120):fim+120]
                    texto_norm = unidecode(texto).lower()
                    contexto_norm = unidecode(contexto).lower()
                    
                    # NOVO: Ignorar se é referência legal (Decreto, Lei, Portaria, Resolução)
                    ctx_antes = texto[max(0, inicio-30):inicio].lower()
                    referencias_legais = ['decreto', 'lei ', 'lei:', 'portaria', 'resolução', 'resolucao', 
                                         'instrução normativa', 'instrucao normativa', 'edital']
                    if any(ref in ctx_antes for ref in referencias_legais):
                        continue  # Não é processo SEI, é número de referência legal
                    
                    # NOVO: Ignorar se é processo de órgão FEDERAL (não é GDF, é referência administrativa)
                    orgaos_federais = ['cgu', 'tcu', 'stf', 'stj', 'pgr', 'mpu', 'advocacia geral', 
                                       'ministerio', 'ministério', 'receita federal', 'inss', 'ibama',
                                       'anatel', 'anvisa', 'ana ', ' ana,', 'caixa federal']
                    ctx_depois = texto[fim:min(len(texto), fim+50)].lower()
                    # Verifica se menciona órgão federal antes ou depois do número
                    if any(org in ctx_antes for org in orgaos_federais) or any(org in ctx_depois for org in orgaos_federais):
                        continue  # É processo de órgão federal, não GDF
                    
                    # NOVO: Ignorar se é referência genérica ("Referência:", "ref:", "conforme", etc.)
                    indicadores_referencia = ['referência:', 'referencia:', 'ref:', 'conforme ', 
                                              'conforme o ', 'considerando o processo', 'proc.']
                    if any(ref in ctx_antes.lower() for ref in indicadores_referencia):
                        continue  # É apenas referência administrativa, não PII
                    
                    # Protocolos LAI/OUV explícitos: sempre PII, exceto se contexto negativo
                    if tipo in ['PROTOCOLO_LAI', 'PROTOCOLO_OUV']:
                        label_explicito = any(lbl in contexto_norm for lbl in ['protocolo lai', 'protocolo ouv', 'lai-', 'ouv-'])
                        frases_negativas = [
                            "exemplo", "referencia", "referência", "só referência", "só exemplo", "não é protocolo", "nao é protocolo", "não protocolo", "nao protocolo", "não é válido", "nao e valido"
                        ]
                        contexto_negativo = any(kw in contexto_norm for kw in frases_negativas) or any(kw in texto_norm for kw in frases_negativas)
                        if label_explicito and not contexto_negativo:
                            findings.append({
                                "tipo": tipo, "valor": valor,
                                "confianca": self._calcular_confianca(tipo, texto, inicio, fim),
                                "peso": 3, "inicio": inicio, "fim": fim
                            })
                            continue
                    
                    # LGPD: Processos SEI são SEMPRE PIIs quando mencionados em contextos LAI
                    # Qualquer processo SEI em uma solicitação de acesso é dado pessoal
                    # pois vincula o cidadão a um procedimento administrativo
                    
                    # Frases que indicam que NÃO é PII (exemplos genéricos)
                    frases_negativas_reais = [
                        "nao e um processo", "não é um processo", "exemplo de processo", 
                        "exemplo de protocolo", "número similar", "número ficticio", 
                        "não é válido", "nao e valido", "formatação de processo"
                    ]
                    contexto_negativo = any(kw in contexto_norm for kw in frases_negativas_reais)
                    
                    if contexto_negativo:
                        continue
                    
                    # Processo SEI com label explícito: sempre PII
                    labels_processo = ['processo sei', 'processo nº', 'processo no', 'processo n°', 
                                       'processo administrativo', 'autos do processo', 'sei nº', 'sei n°',
                                       'acesso ao processo', 'processo de nº']
                    tem_label = any(lbl in contexto_norm for lbl in labels_processo)
                    
                    if tem_label:
                        findings.append({
                            "tipo": tipo, "valor": valor,
                            "confianca": self._calcular_confianca(tipo, texto, inicio, fim),
                            "peso": 3, "inicio": inicio, "fim": fim
                        })
                        continue
                    
                    # Frases que indicam contexto de posse/interesse
                    frases_posse = [
                        "meu processo", "meu número", "minha processo", "do requerente", "do cidadao", 
                        "do solicitante", "do interessado", "do titular", "do usuario", "do paciente", 
                        "do denunciante", "do autor", "do beneficiario", "do responsavel", 
                        "referente ao processo", "processo do", "processo da", "solicito acesso",
                        "solicito cópia", "gostaria de acesso", "acesso aos autos", "acesso externo",
                        "informações sobre o processo", "consultar o andamento"
                    ]
                    contexto_posse = any(kw in contexto_norm for kw in frases_posse) or any(kw in texto_norm for kw in frases_posse)
                    
                    # Se tem contexto de posse/interesse, marca como PII
                    if contexto_posse:
                        findings.append({
                            "tipo": tipo, "valor": valor,
                            "confianca": self._calcular_confianca(tipo, texto, inicio, fim),
                            "peso": 3, "inicio": inicio, "fim": fim
                        })
                    # IMPORTANTE: SEM contexto de posse, processos são apenas referências administrativas
                    # Não são PII por si só - apenas quando vinculados a pessoa específica
                    # Exemplo: "SEI 00040-00098765/2025-00" sem contexto = NÃO é PII
                    # Exemplo: "Meu processo SEI 00040-00098765/2025-00" = É PII
                    else:
                        # Não adiciona ao findings - processo sem contexto de posse não é PII
                        continue

                elif tipo in ['PROTOCOLO_LAI', 'PROTOCOLO_OUV', 'PROTOCOLO_GENERICO']:
                    contexto = texto[max(0, inicio-100):fim+100].lower()
                    contexto_negativo = any(
                        kw in contexto for kw in [
                            "exemplo", "referência", "referencia", "só referência", "só exemplo", "não é protocolo", "nao é protocolo"
                        ]
                    )
                    if contexto_negativo:
                        continue
                    # PROTOCOLO_GENERICO vai como PROTOCOLO_LAI
                    tipo_final = 'PROTOCOLO_LAI' if tipo == 'PROTOCOLO_GENERICO' else tipo
                    findings.append({
                        "tipo": tipo_final, "valor": valor,
                        "confianca": self._calcular_confianca(tipo, texto, inicio, fim),
                        "peso": 3, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'OCORRENCIA_POLICIAL':
                    contexto = texto[max(0, inicio-100):fim+100].lower()
                    contexto_negativo = any(
                        kw in contexto for kw in [
                            "exemplo", "referência", "referencia", "só referência", "só exemplo", "não é ocorrência", "nao é ocorrência"
                        ]
                    )
                    if contexto_negativo:
                        continue
                    findings.append({
                        "tipo": "OCORRENCIA_POLICIAL", "valor": valor,
                        "confianca": self._calcular_confianca("OCORRENCIA_POLICIAL", texto, inicio, fim),
                        "peso": 3, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'CNPJ':
                    # LGPD: Detectar CNPJ pelo FORMATO mesmo se matematicamente inválido
                    cnpj_valido = self._validar_cnpj(valor)
                    cnpj_limpo = re.sub(r'\D', '', valor)
                    formato_correto = len(cnpj_limpo) == 14 and cnpj_limpo != cnpj_limpo[0] * 14
                    
                    if not formato_correto:
                        continue
                    
                    # IMPORTANTE: Verificar se faz parte de PROCESSO_SEI
                    # Formato típico de processo: XXXXX-XXXXXXXX/YYYY-XX
                    # Se há prefixo de processo antes do "CNPJ", é processo, não CNPJ
                    contexto_antes = texto[max(0, inicio-10):inicio]
                    eh_parte_processo = bool(re.search(r'\d{4,5}[-\s]$', contexto_antes))
                    if eh_parte_processo:
                        continue  # Pula - é parte de um processo SEI
                        
                    contexto = texto[max(0, inicio-50):fim+50].upper()
                    
                    # Verificar contexto negativo (processos)
                    contexto_negativo_processo = any(p in contexto for p in [
                        "PROCESSO SEI", "PROCESSO Nº", "PROCESSO N°", "PROCESSO NUMERO", 
                        "AUTOS DO PROCESSO", "PROCESSO ADMINISTRATIVO", "SEI Nº", "SEI N°"
                    ])
                    if contexto_negativo_processo:
                        # Verificar se há indicação explícita de CNPJ
                        contexto_positivo_cnpj = any(p in contexto for p in [
                            "CNPJ", "EMPRESA", "RAZÃO SOCIAL", "MEI", "PESSOA JURÍDICA"
                        ])
                        if not contexto_positivo_cnpj:
                            continue  # É processo, não CNPJ
                    
                    # Calcula confiança baseada em validação
                    confianca = self._calcular_confianca("CNPJ", texto, inicio, fim)
                    if not cnpj_valido:
                        confianca = max(0.6, confianca * 0.8)  # Reduz mas mantém detectável
                    
                    if any(p in contexto for p in ["MEU CNPJ", "MINHA EMPRESA", "SOU MEI"]):
                        findings.append({
                            "tipo": "CNPJ_PESSOAL", "valor": valor,
                            "confianca": confianca,
                            "peso": 4, "inicio": inicio, "fim": fim
                        })
                    else:
                        findings.append({
                            "tipo": "CNPJ", "valor": valor,
                            "confianca": confianca,
                            "peso": 3, "inicio": inicio, "fim": fim
                        })

                elif tipo == 'NIRE':
                    # NIRE - Número de Identificação do Registro de Empresa
                    findings.append({
                        "tipo": "NIRE", "valor": valor,
                        "confianca": self._calcular_confianca("NIRE", texto, inicio, fim),
                        "peso": 3, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'MATRICULA_IMOVEL':
                    # Matrícula de imóvel em cartório
                    findings.append({
                        "tipo": "MATRICULA_IMOVEL", "valor": valor,
                        "confianca": self._calcular_confianca("MATRICULA_IMOVEL", texto, inicio, fim),
                        "peso": 3, "inicio": inicio, "fim": fim
                    })

                elif tipo in ['CDA', 'CDA_ADICIONAL']:
                    # CDA - Certidão de Dívida Ativa
                    findings.append({
                        "tipo": "CDA", "valor": valor,
                        "confianca": self._calcular_confianca("CDA", texto, inicio, fim),
                        "peso": 3, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'AUTO_INFRACAO':
                    # Auto de Infração GDF
                    findings.append({
                        "tipo": "AUTO_INFRACAO", "valor": valor,
                        "confianca": self._calcular_confianca("AUTO_INFRACAO", texto, inicio, fim),
                        "peso": 3, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'PROTOCOLO_DFP':
                    # Protocolo DFP (Junta Comercial)
                    findings.append({
                        "tipo": "PROTOCOLO_DFP", "valor": valor,
                        "confianca": self._calcular_confianca("PROTOCOLO_DFP", texto, inicio, fim),
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

                elif tipo in ['CELULAR', 'TELEFONE_FIXO', 'TELEFONE_DDI', 'TELEFONE_DDD_ESPACO', 
                              'TELEFONE_LOCAL', 'TELEFONE_INTERNACIONAL', 'TELEFONE_CURTO',
                              'TELEFONE_DDD_HIFEN', 'CELULAR_SEM_FORMATACAO', 'TELEFONE_DDD_ZERO']:
                    
                    # IMPORTANTE: Verificar se é número de processo ou protocolo (não telefone)
                    # Números como "0032185265/2024", "000025483" podem ser processos/protocolos
                    contexto_amplo = texto[max(0, inicio-30):min(len(texto), fim+30)].upper()
                    eh_processo_protocolo = any(p in contexto_amplo for p in [
                        "PROCESSO", "PROTOCOLO", "SEI", "AUTUAÇÃO", "AUTUACAO", "NIRE", 
                        "Nº DE PROCESSO", "N° DE PROCESSO", "Nº DO PROCESSO"
                    ])
                    if eh_processo_protocolo and not any(p in contexto_amplo for p in ["TEL", "FONE", "CELULAR", "CONTATO"]):
                        continue  # É processo/protocolo, não telefone
                    
                    # NOVO: Contextos que indicam que NÃO é telefone (código, referência, etc.)
                    contexto_nao_telefone = texto[max(0, inicio-40):min(len(texto), fim+40)].lower()
                    termos_nao_telefone = [
                        'código', 'codigo', 'referência', 'referencia', 'ref:', 'ref.',
                        'número do pedido', 'numero do pedido', 'nº pedido', 'n° pedido',
                        'ordem de serviço', 'ordem de servico', 'o.s.:', 'o.s. n',
                        'ticket', 'chamado', 'solicitação nº', 'solicitacao n',
                        'versão', 'versao', 'modelo', 'série', 'serie',
                        'lote nº', 'lote n°', 'item nº', 'item n°', 'artigo', 'parágrafo', 'paragrafo',
                    ]
                    if any(t in contexto_nao_telefone for t in termos_nao_telefone):
                        # Verifica se realmente tem contexto de telefone que sobrescreve
                        if not any(p in contexto_nao_telefone for p in ['tel', 'fone', 'celular', 'contato', 'ligar', 'whats']):
                            continue  # É código/referência, não telefone
                    
                    # IMPORTANTE: Número sem formatação típica (sem hífen, parênteses) pode ser processo
                    # Se começa com muitos zeros, provavelmente é número de protocolo
                    valor_limpo = re.sub(r'\D', '', valor)
                    if valor_limpo.startswith('000') or valor_limpo.startswith('0000'):
                        # Provavelmente é número de protocolo ou autuação
                        continue
                        
                    ctx_antes = texto[max(0, inicio-80):inicio].lower()
                    ctx_depois = texto[fim:min(len(texto), fim+80)].lower()

                    termos_institucionais = [
                        'institucional', 'fixo', 'ramal', 'central', 'sac', 'atendimento', 'ouvidoria', 'departamento', 'setor', 'secretaria', 'empresa', 'comercial', 'pabx', '0800', '4003', '3312', '3105', '3325', '3961', '3214', '3411', '3344', '3048', '3349', '3346', '3462', '3190', '3901', '3326', '3348', 'disque', 'contato institucional', 'serviço', 'servico', 'suporte', 'helpdesk', 'callcenter', 'ramal interno', 'ramal:', 'ramal '
                    ]
                    
                    # NOVO: Verificar se o telefone começa com prefixo institucional (fixo GDF)
                    # Telefones fixos do DF começam com 61 3xxx, se o número começa com 3xxx, verificar prefixo
                    valor_limpo = re.sub(r'[^\d]', '', valor)  # Remove tudo exceto dígitos
                    if len(valor_limpo) >= 8:
                        # Se tem 10-11 dígitos, pegar os 4 dígitos após o DDD
                        prefixo = valor_limpo[2:6] if len(valor_limpo) >= 10 else valor_limpo[:4]
                        prefixos_institucionais = {'3105', '3312', '3325', '3961', '3214', '3411', '3344', '3048', '3349', '3346', '3462', '3190', '3901', '3326', '3348'}
                        if prefixo in prefixos_institucionais:
                            continue  # Telefone institucional do GDF
                    # Filtro: se label anterior ao número contém termo institucional, ignora
                    from text_unidecode import unidecode
                    label_pre = unidecode(texto[max(0, inicio-40):inicio]).lower()
                    label_full = unidecode(texto[max(0, inicio-60):inicio]).lower()
                    ctx_antes_norm = unidecode(ctx_antes)
                    ctx_depois_norm = unidecode(ctx_depois)
                    # Filtro ultra: ignora se qualquer contexto anterior ou label contém explicitamente 'telefone institucional' ou 'fixo institucional'
                    if (
                        'telefone institucional' in label_pre
                        or 'telefone institucional' in label_full
                        or 'fixo institucional' in label_pre
                        or 'fixo institucional' in label_full
                        or 'ramal institucional' in label_pre
                        or 'ramal institucional' in label_full
                        or 'telefone institucional' in ctx_antes_norm
                        or 'fixo institucional' in ctx_antes_norm
                        or 'telefone institucional' in ctx_depois_norm
                        or 'fixo institucional' in ctx_depois_norm
                        or 'institucional' in label_pre
                        or 'institucional' in label_full
                        or any(term in label_pre for term in termos_institucionais)
                        or any(term in ctx_antes_norm or term in ctx_depois_norm for term in termos_institucionais)
                    ):
                        import logging
                        logging.warning(f"[PII-DEBUG] Ignorando telefone institucional: {valor} | contexto: {label_pre} | {label_full} | {ctx_antes_norm} | {ctx_depois_norm}")
                        continue

                    # Boost: se contexto pessoal explícito, aumenta peso/confiança
                    termos_pessoais = ['meu', 'minha', 'celular', 'telefone', 'contato', 'whatsapp', 'pessoal', 'falar com', 'ligar para', 'recado', 'urgente', 'residencial', 'para retorno', 'para contato']
                    boost = 0.0
                    if any(tp in ctx_antes or tp in ctx_depois for tp in termos_pessoais):
                        boost = 0.10

                    findings.append({
                        "tipo": "TELEFONE", "valor": valor,
                        "confianca": min(1.0, self._calcular_confianca("TELEFONE", texto, inicio, fim) + boost),
                        "peso": 4 if boost > 0 else 3, "inicio": inicio, "fim": fim
                    })

                elif tipo in ['RG', 'RG_ORGAO']:
                    findings.append({
                        "tipo": "RG", "valor": valor,
                        "confianca": self._calcular_confianca("RG", texto, inicio, fim),
                        "peso": 5, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'CNH':
                    contexto = texto[max(0, inicio-80):fim+80].lower()
                    # Contexto negativo: código de barras, boleto, ocorrência, CDA, NIS, conta
                    contexto_negativo = re.search(
                        r'c[oó]digo\s+de\s+barras|boleto|linha\s+digit[aá]vel|'
                        r'ocorr[eê]ncia|pmdf|pcdf|cbmdf|boletim|'
                        r'cda|d[ií]vida\s+ativa|certid[ãa]o|'
                        r'nis|pis|pasep|benefici[aá]rio|'
                        r'conta|ag[eê]ncia|dep[oó]sito|transfer[eê]ncia|'
                        r'processo\s+n|protocolo|sei\s*n|'
                        r'inscri[çc][aã]o|im[oó]vel|cart[aã]o|nota\s+fiscal',
                        contexto
                    )
                    if contexto_negativo:
                        continue  # Ignora CNH em contexto de código de barras, ocorrência, CDA, NIS, etc
                    
                    # Aceita CNH se tiver contexto positivo ou se o texto tem "CNH" como label
                    labels_cnh = [
                        "minha cnh", "cnh do titular", "cnh cadastrada", "habilitação", "habilitacao",
                        "carteira de motorista", "cnh:", "cnh ", "minha carteira", "carteira de habilitação",
                        "carteira de habilitacao", "numero da cnh", "n da cnh"
                    ]
                    contexto_positivo = any(kw in contexto for kw in labels_cnh)
                    
                    # Só aceita CNH se houver contexto positivo explícito de habilitação/CNH
                    if contexto_positivo and len(valor) >= 9:
                        findings.append({
                            "tipo": "CNH", "valor": valor,
                            "confianca": self._calcular_confianca("CNH", texto, inicio, fim),
                            "peso": 5, "inicio": inicio, "fim": fim
                        })


                elif tipo in ['ENDERECO_RESIDENCIAL', 'ENDERECO_BRASILIA', 'ENDERECO_SHIN_SHIS', 'ENDERECO_DF_RESIDENCIAL', 'ENDERECO_MORO_EM', 'ENDERECO_LABEL', 'ENDERECO_SETOR_DF', 'ENDERECO_CONTEXTO_PESSOAL']:
                    from text_unidecode import unidecode
                    import logging
                    contexto = unidecode(texto[max(0, inicio-120):fim+120]).lower()
                    valor_norm = unidecode(valor).lower() if valor else ""
                    
                    # Gatilhos que indicam RESIDENCIAL - mesmo que o endereço pareça comercial
                    gatilhos_residenciais = [
                        "inquilina", "inquilino", "imóvel localizado", "imovel localizado", 
                        "moro", "resido", "minha casa", "meu endere", "minha resid",
                        "mora na", "mora no", "moradora", "morador", "endereco:",
                        "residencia", "residencial", "me encontrar", "entrega", "buscar"
                    ]
                    tem_contexto_residencial = any(g in contexto for g in gatilhos_residenciais)
                    
                    # PATCH: ENDERECO_MORO_EM, ENDERECO_LABEL e ENDERECO_CONTEXTO_PESSOAL sempre aceitos
                    if tipo in ['ENDERECO_MORO_EM', 'ENDERECO_LABEL', 'ENDERECO_CONTEXTO_PESSOAL']:
                        findings.append({
                            "tipo": "ENDERECO_RESIDENCIAL", "valor": valor,
                            "confianca": self._calcular_confianca("ENDERECO_RESIDENCIAL", texto, inicio, fim),
                            "peso": 4, "inicio": inicio, "fim": fim
                        })
                        continue
                    
                    # PATCH: Ignora siglas de quadras comerciais do DF sem contexto residencial
                    siglas_comerciais_df = ['crn', 'cln', 'cls', 'scln', 'scrn', 'scrs', 'scls', 'sbs', 'scs', 'sds', 'shs', 'sep']
                    if any(valor_norm.strip() == sigla or valor_norm.strip().startswith(sigla + ' ') for sigla in siglas_comerciais_df):
                        # Quadra comercial: só aceita se tiver contexto residencial explícito
                        if not tem_contexto_residencial:
                            logger.debug(f"[DEDUP] Endereço comercial ignorado: {valor}")
                            continue
                    
                    # Se tem contexto residencial explícito, aceita direto
                    if tem_contexto_residencial:
                        findings.append({
                            "tipo": "ENDERECO_RESIDENCIAL", "valor": valor,
                            "confianca": self._calcular_confianca("ENDERECO_RESIDENCIAL", texto, inicio, fim),
                            "peso": 4, "inicio": inicio, "fim": fim
                        })
                        continue
                    
                    # Se padrão SHIN/SHIS/SHLP/SHLN/SHDF + Bloco/Apto = residencial
                    # Ou ENDERECO_SETOR_DF com setor habitacional (SH*)
                    # MAS: se contexto é de serviço público (fiscalização, denúncia), NÃO é PII
                    contexto_servico_publico = any(g in contexto for g in [
                        'fiscaliza', 'denuncia', 'denúncia', 'reclama', 'solicita', 
                        'melhoria', 'conserto', 'buraco', 'calcada', 'calçada',
                        'ilumina', 'limpeza', 'coleta', 'lixo', 'esgoto', 'agua',
                        'asfalto', 'pavimento', 'sinalizacao', 'sinalização'
                    ])
                    
                    padroes_residenciais_brasilia = ["shin", "shis", "shlp", "shln", "sqn", "sqs", "shdf", "shce", "shcg", "shn", "shs"]
                    if any(p in valor_norm for p in padroes_residenciais_brasilia):
                        # Se é contexto de serviço público, não é PII - é só localização do problema
                        if contexto_servico_publico:
                            logger.debug(f"[DEDUP] Endereço em contexto de serviço público ignorado: {valor}")
                            continue
                        
                        # PATCH: Se não há contexto residencial explícito E não há outros PIIs,
                        # endereço habitacional genérico (só quadra/bloco) não identifica pessoa
                        # Precisa de: "moro na", "minha casa", "endereço:", etc.
                        if not tem_contexto_residencial:
                            # Verifica se tem indicadores de moradia específica (apt, casa, etc)
                            indicadores_moradia = ['apt', 'apartamento', 'casa', 'residência', 'residencia', 
                                                   'moro', 'resido', 'minha', 'meu']
                            tem_indicador_moradia = any(i in contexto for i in indicadores_moradia)
                            if not tem_indicador_moradia:
                                logger.debug(f"[DEDUP] Endereço habitacional genérico ignorado (sem contexto): {valor}")
                                continue
                        
                        # Setor habitacional com contexto - aceita como endereço residencial
                        findings.append({
                            "tipo": "ENDERECO_RESIDENCIAL", "valor": valor,
                            "confianca": self._calcular_confianca("ENDERECO_RESIDENCIAL", texto, inicio, fim),
                            "peso": 4, "inicio": inicio, "fim": fim
                        })
                        continue
                    
                    # Setores administrativos (SAS, SCS, SDS, etc) - só aceita com contexto residencial explícito
                    setores_administrativos = ["sas", "scs", "sds", "sbs", "scn", "sen", "sgo", "sia", "sig"]
                    if any(p in valor_norm for p in setores_administrativos):
                        # PRIMEIRO: Verificar se é contexto institucional (Secretaria, Hospital, etc)
                        gatilhos_institucionais = [
                            "secretaria", "hospital", "escola", "orgao", "empresa", "administracao", 
                            "departamento", "diretoria", "coordenacao", "tribunal", "camara", "senado", 
                            "autarquia", "fundacao", "instituto", "agencia", "conselho", "comissao", 
                            "gdf", "seedf", "sesdf", "sedf", "sejus", "pcdf", "pmdf", "cbmdf", 
                            "detran", "caesb", "ceb", "novacap", "terracap", "brb", "metro", 
                            "ubs", "upa", "posto", "servico", "servicos", "bloco institucional", 
                            "administração regional", "administracao regional", "orgao publico",
                            "endereco da", "endereço da", "endereco do", "endereço do"
                        ]
                        if any(g in contexto for g in gatilhos_institucionais):
                            logger.debug(f"[DEDUP] Endereço institucional ignorado: {valor}")
                            continue
                        
                        # Setor administrativo: só aceita se tiver contexto residencial
                        if not tem_contexto_residencial:
                            # Ignora setores administrativos sem contexto residencial
                            continue
                        findings.append({
                            "tipo": "ENDERECO_RESIDENCIAL", "valor": valor,
                            "confianca": self._calcular_confianca("ENDERECO_RESIDENCIAL", texto, inicio, fim),
                            "peso": 4, "inicio": inicio, "fim": fim
                        })
                        continue
                    
                    # Gatilhos institucionais - se presente, ignora (fallback para outros tipos)
                    gatilhos_institucionais = [
                        "secretaria", "hospital", "escola", "orgao", "empresa", "administracao", "departamento", "diretoria", "coordenacao", "tribunal", "camara", "senado", "autarquia", "fundacao", "instituto", "agencia", "conselho", "comissao", "gdf", "seedf", "sesdf", "sedf", "sejus", "pcdf", "pmdf", "cbmdf", "detran", "caesb", "ceb", "novacap", "terracap", "brb", "metro", "ubs", "upa", "posto", "servico", "servicos", "setor", "bloco institucional", "administração regional", "administracao regional", "orgao publico"
                    ]
                    if any(g in contexto for g in gatilhos_institucionais):
                        continue
                    
                    # Caso geral: só marca se tiver padrão residencial explícito no valor
                    contexto_residencial = re.search(r'moro|resido|minha\s+casa|meu\s+endere|minha\s+resid|residencia\s*:', contexto)
                    if contexto_residencial:
                        findings.append({
                            "tipo": "ENDERECO_RESIDENCIAL", "valor": valor,
                            "confianca": self._calcular_confianca("ENDERECO_RESIDENCIAL", texto, inicio, fim),
                            "peso": 4, "inicio": inicio, "fim": fim
                        })

                elif tipo in ['CONTA_BANCARIA', 'DADOS_BANCARIOS', 'CARTAO_CREDITO', 'CARTAO_FINAL']:
                    contexto = texto[max(0, inicio-80):fim+80].lower()
                    valor_norm = valor.lower() if valor else ""
                    
                    # PATCH: Aceita dados bancários com diversos contextos
                    contexto_pessoal = re.search(
                        r'minha\s+conta|meu\s+banco|depositar|transferir|'
                        r'pix|minha\s+ag[êe]ncia|receber\s+em|'
                        r'pagamento|meu\s+cart[ãa]o|cart[ãa]o\s+final|'
                        r'dep[óo]sito|ag[êe]ncia|ag\s*\d|cc\s*\d|'
                        r'conta\s*corrente|conta\s*:',
                        contexto
                    )
                    
                    # Ignora números isolados que parecem ser outros identificadores
                    # Números de processo, ocorrência, protocolo frequentemente parecem dados bancários
                    contexto_negativo = re.search(
                        r'processo|protocolo|ocorr[êe]ncia|sei\s*n|nota\s+fiscal|'
                        r'empenho|documento|n[ºo°]\s*\d',
                        contexto
                    )
                    if contexto_negativo and not contexto_pessoal:
                        continue
                    
                    gatilhos_institucionais = [
                        "agência institucional", "agencia institucional", "conta institucional", "conta corporativa", "conta empresa", "conta comercial", "conta governo"
                    ]
                    # Se contexto institucional, nunca marca como PII
                    if any(g in contexto for g in gatilhos_institucionais):
                        continue
                    
                    # Marca como PII se tiver contexto bancário ou pessoal
                    if contexto_pessoal:
                        findings.append({
                            "tipo": "DADOS_BANCARIOS", "valor": valor,
                            "confianca": self._calcular_confianca("CONTA_BANCARIA", texto, inicio, fim),
                            "peso": 4, "inicio": inicio, "fim": fim
                        })

                elif tipo == 'DADO_BIOMETRICO':
                    contexto = texto[max(0, inicio-60):fim+60].lower()
                    gatilhos = ["impressão digital", "impressao digital", "foto 3x4", "reconhecimento facial", "biometria", "biométrico", "biometrico"]
                    if any(g in contexto for g in gatilhos) or valor:
                        findings.append({
                            "tipo": "DADO_BIOMETRICO", "valor": valor,
                            "confianca": self._calcular_confianca("DADO_BIOMETRICO", texto, inicio, fim),
                            "peso": 5, "inicio": inicio, "fim": fim
                        })

                # PATCH ULTRA: qualquer referência a menor, estudante, aluno, idade, etc., é PII, exceto se contexto genérico/institucional
                elif tipo == 'MENOR_IDENTIFICADO':
                    contexto = texto[max(0, inicio-60):fim+60].lower()
                    contextos_genericos = [
                        'solicitação genérica', 'solicito informações', 'benefício geral', 'aposentadoria', 'requerimento genérico', 'dados epidemiológicos', 'dados epidemiologicos', 'dados estatísticos', 'dados estatisticos', 'estatística geral', 'secretaria de educação', 'secretaria de educacao', 'informação institucional', 'dados públicos', 'dados publicos'
                    ]
                    # Só ignora se contexto genérico/institucional
                    if any(cg in contexto for cg in contextos_genericos):
                        continue
                    # Tenta reconstruir valor a partir dos grupos e validar idade < 18
                    idade = None
                    if match.groups():
                        grupos = [g for g in match.groups() if g]
                        # Extrai idade dos grupos (números de 1-2 dígitos)
                        for g in grupos:
                            if g and g.isdigit() and len(g) <= 2:
                                idade = int(g)
                                break
                        if grupos:
                            valor = ' '.join(grupos)
                    # Só considera se idade < 18 (é menor de idade)
                    if idade is not None and idade >= 18:
                        continue
                    findings.append({
                        "tipo": "MENOR_IDENTIFICADO", "valor": valor or match.group(),
                        "confianca": self._calcular_confianca("MENOR_IDENTIFICADO", texto, inicio, fim),
                        "peso": 5, "inicio": inicio, "fim": fim
                    })

                elif tipo in ['TELEFONE', 'TELEFONE_DDI', 'TELEFONE_FIXO', 'TELEFONE_LOCAL', 'TELEFONE_CURTO', 'CELULAR']:
                    contexto = texto[max(0, inicio-60):fim+60].lower()
                    if any(g in contexto for g in ["meu tel", "meu telefone", "celular", "telefone", "contato"]):
                        findings.append({
                            "tipo": "TELEFONE", "valor": valor,
                            "confianca": self._calcular_confianca("TELEFONE", texto, inicio, fim),
                            "peso": 4, "inicio": inicio, "fim": fim
                        })

                elif tipo == 'REGISTRO_PROFISSIONAL':
                    contexto = texto[max(0, inicio-60):fim+60].lower()
                    if any(g in contexto for g in ["oab", "crm", "crea", "cro", "crp", "crf", "coren", "crc"]):
                        findings.append({
                            "tipo": "OAB", "valor": valor,
                            "confianca": 0.85,
                            "peso": 4, "inicio": inicio, "fim": fim
                        })

                # PATCH ULTRA: qualquer referência a prontuário, tratamento, diagnóstico, CID, paciente, etc., é PII, exceto se contexto genérico/institucional
                elif tipo == 'DADO_SAUDE':
                    contexto = texto[max(0, inicio-100):fim+50].upper()
                    contextos_genericos = [
                        'ISENÇÃO', 'IMPOSTO DE RENDA', 'APOSENTADO', 'SOLICITAÇÃO', 'SOLICITO', 'PEDIDO', 'BENEFÍCIO', 'BENEFICIO', 'AUXÍLIO', 'AUXILIO', 'APOSENTADORIA', 'REQUERIMENTO', 'GENÉRICO', 'GENERICA', 'GENÉRICA', 'GENERICAMENTE', 'PARA', 'SOBRE', 'REFERENTE', 'REFERÊNCIA', 'REFERENCIA', 'INFORMAÇÃO', 'INFORMACAO', 'INFORMAÇÕES', 'INFORMACOES', 'DADOS EPIDEMIOLÓGICOS', 'DADOS EPIDEMIOLOGICOS', 'DADOS ESTATÍSTICOS', 'DADOS ESTATISTICOS', 'ESTATÍSTICA', 'ESTATISTICA', 'ESTATÍSTICAS', 'ESTATISTICAS', 'PÚBLICO', 'PUBLICO', 'SES-DF', 'SECRETARIA', 'SECRETARIA DE SAÚDE', 'SECRETARIA DE SAUDE', 'GDF', 'PÚBLICA', 'PUBLICA', 'PÚBLICO', 'PUBLICO', 'HOSPITAL', 'CLÍNICA', 'CLINICA', 'UNIDADE', 'UBS', 'UPA', 'POSTO', 'SERVIÇO', 'SERVICO', 'SERVIÇOS', 'SERVICOS', 'GENÉRICO', 'GENERICA', 'GENÉRICA', 'GENERICAMENTE'
                    ]
                    # Só ignora se contexto genérico/institucional
                    if any(cg in contexto for cg in contextos_genericos):
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

                # NOVO: Conta bancária com contexto explícito (não confundir com "conta de luz")
                elif tipo == 'CONTA_BANCARIA_CONTEXTUAL':
                    # Extrai conta e agência dos grupos
                    grupos = [g for g in match.groups() if g]
                    conta = grupos[0] if grupos else valor
                    agencia = grupos[1] if len(grupos) > 1 else None
                    # Valida que conta tem ao menos 4 dígitos
                    digitos_conta = ''.join(c for c in conta if c.isdigit())
                    if len(digitos_conta) >= 4:
                        valor_completo = f"Conta {conta}"
                        if agencia:
                            valor_completo += f" Ag {agencia}"
                        findings.append({
                            "tipo": "CONTA_BANCARIA", "valor": valor_completo,
                            "confianca": 0.92,
                            "peso": 5, "inicio": inicio, "fim": fim
                        })

                elif tipo in ['NOME_TITULO', 'NOME_ASSINATURA', 'NOME_CARGO', 'NOME_CONDOMINIO']:
                    # Nomes extraídos por contexto (título, assinatura, cargo, condomínio)
                    # Limpar valor - remover caracteres extras
                    valor_limpo = valor.strip()
                    # Verificar se é um nome válido (pelo menos 2 palavras, não muito longo)
                    palavras = valor_limpo.split()
                    if len(palavras) >= 2 and len(palavras) <= 5 and len(valor_limpo) <= 45:
                        # Verificar que todas as palavras (exceto preposições) começam com maiúscula
                        preposicoes = {'de', 'da', 'do', 'dos', 'das', 'e'}
                        palavras_validas = all(
                            p.lower() in preposicoes or (p[0].isupper() and len(p) > 1)
                            for p in palavras
                        )
                        if palavras_validas:
                            findings.append({
                                "tipo": "NOME", "valor": valor_limpo,
                                "confianca": 0.85,
                                "peso": 4, "inicio": inicio, "fim": fim
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

                elif tipo == 'PASSAPORTE':
                    contexto = texto[max(0, inicio-60):fim+60].lower()
                    # Nunca marca exemplos/fictícios como PII
                    if any(kw in contexto for kw in ["exemplo", "ficticio", "fictício", "teste", "000000", "aa000000"]):
                        continue
                    findings.append({
                        "tipo": tipo, "valor": valor,
                        "confianca": self._calcular_confianca(tipo, texto, inicio, fim),
                        "peso": 5, "inicio": inicio, "fim": fim
                    })
                elif tipo in ['PIS', 'CNS', 'TITULO_ELEITOR', 'CTPS', 'CERTIDAO', 'REGISTRO_ACADEMICO']:
                    # Para CTPS com múltiplos grupos, reconstruir valor
                    if valor is None and match.groups():
                        grupos = [g for g in match.groups() if g]
                        if grupos:
                            valor = '-'.join(grupos)  # Ex: 65421-00123-DF
                    if not valor:
                        valor = match.group()  # Fallback para match completo
                    findings.append({
                        "tipo": tipo, "valor": valor,
                        "confianca": self._calcular_confianca(tipo, texto, inicio, fim),
                        "peso": 5, "inicio": inicio, "fim": fim
                    })

                elif tipo == 'MATRICULA_SERVIDOR':
                    # PATCH: Excluir matrícula que está dentro de processo SEI
                    processo_sei_pattern = re.compile(r'\b\d{4,5}-\d{5,8}/\d{4}(?:-\d{2})?\b', re.IGNORECASE)
                    dentro_sei = False
                    for sei_match in processo_sei_pattern.finditer(texto):
                        if sei_match.start() <= inicio and fim <= sei_match.end():
                            dentro_sei = True
                            break
                        # Também verifica se o valor está contido no SEI
                        if valor in sei_match.group():
                            dentro_sei = True
                            break
                    if dentro_sei:
                        continue  # Ignora matrícula dentro de SEI
                    
                    # PATCH: Excluir se contexto indica inscrição imobiliária, IPTU ou Registro de Imóveis
                    contexto = texto[max(0, inicio-100):fim+100].lower()
                    contexto_imovel = re.search(
                        r'inscri[cç][ãa]o\s*(imobili[aá]ria|im[oó]vel|iptu)|'
                        r'iptu|matr[ií]cula\s*(do\s+)?im[oó]vel|'
                        r'registr[oa]\s*(de\s+)?im[oó]v|'
                        r'\d+[ºo°]\s*ri\b|\d+[ºo°]\s*registro|'
                        r'inscri[cç][aã]o\s*imobil|cart[oó]rio',
                        contexto
                    )
                    if contexto_imovel:
                        continue  # É inscrição imobiliária/matrícula de imóvel, não matrícula de servidor
                    
                    # Aceita se tiver contexto de matrícula (servidor, aluno, funcionário)
                    contexto_matricula = re.search(
                        r'servidor|funcional|servi[cç]o\s+p[uú]blico|gdf|seedf|sedf|'
                        r'se[jc]us|tcdf|pmdf|pcdf|cbmdf|gest[aã]o\s+de\s+pessoas|'
                        r'funcion[aá]rio|mat[r\.]|matr[ií]cula|aluno|estudante|boletim|escolar',
                        contexto
                    )
                    if contexto_matricula:
                        findings.append({
                            "tipo": tipo, "valor": valor,
                            "confianca": self._calcular_confianca(tipo, texto, inicio, fim),
                            "peso": 3, "inicio": inicio, "fim": fim
                        })

                elif tipo in ['PROCESSO_SEI', 'PROTOCOLO_LAI', 'PROTOCOLO_OUV']:
                    # IMPORTANTE: Nunca adicionar processos sem verificação de contexto
                    # A heurística principal de PROCESSO_SEI está em _detectar_regex
                    # Esta seção é um fallback que NÃO deve adicionar PIIs sem contexto
                    # Processos sem contexto de posse/interesse são apenas referências administrativas
                    continue  # Ignora - a lógica correta está no bloco principal

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

                elif tipo == 'CEP':
                    # CEP é dado de localização - pode identificar a residência de uma pessoa
                    
                    # EXCLUSÃO 1: CEP dentro de número de processo SEI (ex: 00015-01009853/2023-11)
                    processo_sei_pattern = re.compile(r'\b\d{4,5}-\d{5,8}/\d{4}(?:-\d{2})?\b', re.IGNORECASE)
                    dentro_sei = False
                    for sei_match in processo_sei_pattern.finditer(texto):
                        if sei_match.start() <= inicio and fim <= sei_match.end():
                            dentro_sei = True
                            break
                        # Também verifica se o valor está contido no SEI
                        if valor in sei_match.group():
                            dentro_sei = True
                            break
                    if dentro_sei:
                        continue  # Ignora CEP dentro de processo SEI
                    
                    # EXCLUSÃO 2: CEPs genéricos/institucionais (não identificam pessoa específica)
                    # 70000-000 a 70999-999 = Brasília centro/Esplanada (locais públicos)
                    valor_limpo = valor.replace('.', '').replace('-', '').replace(' ', '')
                    if len(valor_limpo) == 8:
                        prefixo_cep = valor_limpo[:5]
                        # CEPs de áreas públicas/comerciais genéricas
                        if prefixo_cep in ['70000', '70001', '70002', '70003', '70004', '70005', '70040', '70041', '70042', '70043', '70044', '70050', '70051']:
                            continue  # Esplanada dos Ministérios, Praça dos Três Poderes, etc.
                    
                    # Contexto de endereço aumenta a relevância
                    contexto = texto[max(0, inicio-80):fim+50].lower()
                    
                    # EXCLUSÃO 3: Contexto de consulta urbanística sobre TERCEIROS (não identifica pessoa)
                    # Importante: "meu endereço", "imóvel de interesse", "moro" = identificador pessoal
                    contexto_urbanismo_terceiros = any(kw in contexto for kw in [
                        'ocupação do solo', 'ocupacao do solo', 
                        'circulação de pessoas', 'circulacao de pessoas',
                        'espaço público', 'espaco publico',
                        'estabelecimento comercial', 'complexo'
                    ])
                    # Mas se tem contexto pessoal, não ignorar
                    contexto_pessoal = any(kw in contexto for kw in [
                        'meu endere', 'minha casa', 'moro', 'resido', 'interesse', 
                        'im[oó]vel de interesse', 'inscrição imobil', 'inscricao imobil',
                        'matrícula', 'matricula'
                    ])
                    if contexto_urbanismo_terceiros and not contexto_pessoal:
                        continue  # Contexto de urbanismo sobre terceiros, não identifica pessoa
                    
                    if re.search(r'endere[çc]o|resid|moro|casa|apt|apartamento|rua|av[en]|quadra|bloco|lote|lt|conjunto|cj|setor|im[oó]vel|localizado|cep\s*:', contexto):
                        findings.append({
                            "tipo": "CEP", "valor": valor,
                            "confianca": 0.85, "peso": 3, "inicio": inicio, "fim": fim
                        })
                    else:
                        # CEP isolado sem contexto de endereço pessoal - ignorar
                        # CEPs genéricos/comerciais não identificam pessoa
                        continue
        
        # === HEURÍSTICAS ADICIONAIS ===
        texto_lower = texto.lower()
        
        # Heurística: Tratamento de câncer (específico)
        # Mas NÃO se for contexto de solicitação genérica (isenção imposto de renda para aposentado)
        if re.search(r'tratamento\s+(?:realizado\s+)?(?:de\s+)?c[aâ]ncer', texto_lower):
            # Contexto genérico: combinação de isenção + imposto de renda + aposentado
            contexto_generico = re.search(r'isen[çc][ãa]o\s+(?:de\s+)?imposto\s+de\s+renda.*aposentado|aposentado.*isen[çc][ãa]o\s+(?:de\s+)?imposto', texto_lower)
            if not contexto_generico:
                if not any(f.get('tipo') == 'DADO_SAUDE' for f in findings):
                    findings.append({
                        "tipo": "DADO_SAUDE", "valor": "Tratamento de câncer",
                        "confianca": 0.95, "peso": 5, "inicio": 0, "fim": len(texto)
                    })
        
        # Heurística: Menor de idade identificado
        # Busca padrão "Nome, X anos, estudante/aluno"
        menor_match = re.search(
            r'(\b[A-Za-zÀ-ÿ]+)[\s,]+(\d{1,2})\s*anos',
            texto
        )
        if menor_match:
            nome = menor_match.group(1)
            # Verifica se o nome começa com maiúscula
            if nome and nome[0].isupper():
                try:
                    idade = int(menor_match.group(2))
                    if idade < 18:
                        # Verifica se há contexto de menor/estudante próximo
                        contexto = texto[max(0, menor_match.start()-20):min(len(texto), menor_match.end()+40)].lower()
                        if re.search(r'estudante|aluno|aluna|menor|crian[çc]a|escola|ec\s*\d', contexto):
                            if not any(f.get('tipo') == 'MENOR_IDENTIFICADO' for f in findings):
                                valor_menor = f"{nome}, {idade} anos"
                                findings.append({
                                    "tipo": "MENOR_IDENTIFICADO", "valor": valor_menor,
                                    "confianca": 0.95, "peso": 5, "inicio": menor_match.start(), "fim": menor_match.end()
                                })
                except ValueError:
                    pass
        
        # Heurística: Nome + menção de CPF/documento (sem número)
        # Ex: "Maria Souza, servidora, informou seu CPF"
        nome_cpf_match = re.search(
            r'([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)+)[^.]{0,50}(?:seu\s+cpf|seu\s+documento|informou\s+(?:seu\s+)?cpf)',
            texto, re.IGNORECASE
        )
        if nome_cpf_match:
            nome = nome_cpf_match.group(1)
            # Verifica se o nome começa com maiúscula e tem mais de uma palavra
            if nome[0].isupper() and ' ' in nome:
                if not self._deve_ignorar_entidade(nome):
                    findings.append({
                        "tipo": "NOME", "valor": nome,
                        "confianca": 0.90, "peso": 4, "inicio": nome_cpf_match.start(1), "fim": nome_cpf_match.end(1)
                    })
        
        # Heurística: Cidadão identificado como Nome
        cidadao_match = re.search(
            r'cidad[ãa]o[^.]{0,30}identificado[^.]{0,20}(?:como|por)\s+([A-ZÀ-Ú][a-záéíóúàâêôãõç]+)',
            texto
        )
        if cidadao_match:
            nome = cidadao_match.group(1)
            if not self._deve_ignorar_entidade(nome):
                findings.append({
                    "tipo": "NOME", "valor": nome,
                    "confianca": 0.85, "peso": 4, "inicio": cidadao_match.start(1), "fim": cidadao_match.end(1)
                })
        
        # Heurística: Assinatura no final do texto
        # Detecta nomes após "Grata/Grato/Atenciosamente/Obrigado/Obrigada"
        # Pode estar com ou sem vírgula: "Grata Conceição" ou "Grata, Conceição"
        assinatura_patterns = [
            # Com vírgula ou sem - após saudação de despedida
            r'(?:grat[ao]|atenciosamente|obrigad[ao]|cordialmente|respeitosamente)[,\s]+([A-ZÀ-Ú][a-záéíóúàâêôãõç]+(?:\s+(?:da|de|do|dos|das|e)?\s*[A-ZÀ-Ú][a-záéíóúàâêôãõç]+)+)',
        ]
        
        for pattern in assinatura_patterns:
            assinatura_match = re.search(pattern, texto, re.IGNORECASE)
            if assinatura_match:
                nome = assinatura_match.group(1).strip()
                # Verificar se parece nome de pessoa (não entidade)
                palavras = nome.split()
                # Filtrar preposições
                palavras_reais = [p for p in palavras if p.lower() not in ['da', 'de', 'do', 'dos', 'das', 'e']]
                if len(palavras_reais) >= 2:
                    # Verificar se não é entidade conhecida
                    nome_lower = nome.lower()
                    entidades_ignorar = ['distrito federal', 'secretaria', 'governo', 'ministério', 'tribunal', 
                                         'defensoria', 'procuradoria', 'polícia', 'companhia', 'universidade',
                                         'equipe', 'atendimento', 'setor', 'departamento', 'coordenação',
                                         'gerência', 'diretoria', 'assessoria', 'ouvidoria', 'central']
                    if not any(ent in nome_lower for ent in entidades_ignorar):
                        if not self._deve_ignorar_entidade(nome):
                            # Verificar se já não foi detectado
                            ja_detectado = any(f.get('tipo') == 'NOME' and f.get('valor', '').lower() == nome.lower() for f in findings)
                            if not ja_detectado:
                                findings.append({
                                    "tipo": "NOME", "valor": nome,
                                    "confianca": 0.90, "peso": 4, 
                                    "inicio": assinatura_match.start(1), "fim": assinatura_match.end(1)
                                })
                                break  # Só uma assinatura por texto
        
        return findings
    
    def _extrair_nomes_gatilho(self, texto: str) -> List[Dict]:
        """Extrai nomes após gatilhos de contato (sempre PII)."""
        findings = []
        texto_upper = self._normalizar(texto)
        
        # Palavras que indicam fim do nome (não são partes de nomes)
        PALAVRAS_FIM_NOME = {
            "GOSTARIA", "QUERO", "PRECISO", "SOLICITO", "VENHO", "PEÇO",
            "ESTOU", "TENHO", "FAÇO", "MORO", "TRABALHO", "SOU"
        }
        
        for gatilho in self.gatilhos_contato:
            if gatilho not in texto_upper:
                continue
            
            idx = texto_upper.find(gatilho) + len(gatilho)
            resto = texto[idx:idx+60].strip()
            
            if "ME CHAMO" in gatilho:
                # Captura nome simples ou composto após "me chamo"
                match = re.search(r'([A-Z][a-záéíóúàèìòùâêîôûãõç]+(?:\s+[A-Z][a-záéíóúàèìòùâêîôûãõç]+)*)', resto)
                if match:
                    nome = match.group(1).strip()
                    
                    # CORREÇÃO: Truncar nome quando encontra palavra que não é nome
                    # Ex: "Braga Gostaria" → "Braga"
                    palavras = nome.split()
                    nome_truncado = []
                    for p in palavras:
                        if p.upper() in PALAVRAS_FIM_NOME:
                            break
                        nome_truncado.append(p)
                    nome = ' '.join(nome_truncado).strip()
                    
                    if not nome or len(nome) <= 3:
                        continue
                    if self._deve_ignorar_entidade(nome):
                        continue
                    
                    inicio = idx + match.start()
                    fim = inicio + len(nome)
                    # Maior confiança para nomes após "Me chamo" (auto-identificação)
                    confianca = min(1.0, self._calcular_confianca("NOME", texto, inicio, fim) * 1.1)
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
    
    def _detectar_presidio(self, texto: str) -> List[Dict]:
        """Detecta PII complementar usando Presidio (apenas tipos que não cobrimos bem).
        
        Presidio é usado APENAS para:
        - IP_ADDRESS: Endereços IP (nosso regex é básico)
        - IBAN_CODE: Códigos bancários internacionais
        - CREDIT_CARD: Cartões de crédito internacionais
        - URL: URLs (complementar ao nosso)
        
        NÃO usamos Presidio para PERSON, PHONE, EMAIL, LOCATION pois já temos:
        - BERT NER (melhor para pt-BR)
        - NuNER (melhor para pt-BR)  
        - spaCy NER (pt_core_news_lg)
        - Regex customizado (53 patterns)
        """
        findings = []
        if not self.presidio_analyzer:
            return findings
        
        try:
            # Apenas entidades que COMPLEMENTAM nosso sistema
            entidades_complementares = [
                'IP_ADDRESS',      # Nosso regex é básico
                'IBAN_CODE',       # Não temos pattern
                'CREDIT_CARD',     # Presidio tem validação de Luhn
            ]
            
            # Mapeamento para nossos tipos
            entity_map = {
                'IP_ADDRESS': 'IP',
                'IBAN_CODE': 'CONTA_BANCARIA_INTERNACIONAL',
                'CREDIT_CARD': 'CARTAO_CREDITO',
            }
            
            # Analisa em português (consistente com o resto do sistema)
            results = self.presidio_analyzer.analyze(
                text=texto,
                language="pt",
                entities=entidades_complementares,
                score_threshold=0.5
            )
            
            for result in results:
                tipo = entity_map.get(result.entity_type, result.entity_type)
                valor = texto[result.start:result.end]
                
                # Ignora se já detectamos pelo nosso regex
                if self._deve_ignorar_entidade(valor):
                    continue
                
                score = result.score
                peso = 4 if score >= 0.8 else 3
                
                findings.append({
                    'tipo': tipo,
                    'valor': valor,
                    'confianca': score,
                    'peso': peso,
                    'inicio': result.start,
                    'fim': result.end,
                    'source': 'presidio'
                })
            
            if findings:
                logger.debug(f"[Presidio] Detectou {len(findings)} entidades complementares")
                
        except Exception as e:
            logger.debug(f"[Presidio] Erro na análise: {e}")
        
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
        # 3. NER (BERT + NuNER + spaCy)
        ner_findings = self._detectar_ner(text)
        all_findings.extend(ner_findings)
        # 4. Presidio Analyzer (pt-BR)
        presidio_findings = self._detectar_presidio(text)
        all_findings.extend(presidio_findings)

        # === VOTAÇÃO (permissiva) ===
        self._pendentes_llm = []  # Reset
        all_findings = self._aplicar_votacao(all_findings)

        # === LLM PARA RECUPERAR PENDENTES (evitar FN) ===
        # Ativação Inteligente: LLM em ambiguidades, MAS respeita variável de ambiente
        # Se PII_USE_LLM_ARBITRATION=false explicitamente, NÃO usa LLM (útil para CI/testes)
        # Se não definida ou true, ativa automaticamente em ambiguidades
        has_ambiguity = len(self._pendentes_llm) > 0
        has_hf_token = bool(os.getenv("HF_TOKEN"))
        
        # Verifica se foi explicitamente desabilitado via env
        llm_env = os.getenv("PII_USE_LLM_ARBITRATION", "").lower()
        llm_explicitly_disabled = llm_env == "false"
        
        # Só usa LLM se: (ativado OU forçado OU ambiguidade) E tem token E não foi explicitamente desabilitado
        should_use_llm = (self.use_llm_arbitration or force_llm or has_ambiguity) and has_hf_token and not llm_explicitly_disabled
        
        if should_use_llm and self._pendentes_llm:
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

        # === DEDUPLICAÇÃO AVANÇADA ===
        final_list = self._deduplicate_findings(all_findings)

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
            # Última chance: LLM analisa texto completo (apenas se permitido e tem token)
            if (self.use_llm_arbitration or force_llm) and len(text) > 50 and has_hf_token and not llm_explicitly_disabled:
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
        
        # === EXPLICABILIDADE (XAI) ===
        pii_relevantes = self._adicionar_explicacoes(pii_relevantes, text)
        
        findings_output = [{
            "tipo": f.get("tipo"),
            "valor": f.get("valor"),
            "confianca": f.get("confianca"),
            "explicacao": f.get("explicacao"),  # XAI: motivos da detecção
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
    use_llm_arbitration: bool = True
) -> PIIDetector:
    """
    Factory function para criar detector configurado.
    
    Args:
        usar_gpu: Se deve usar GPU para modelos
        use_probabilistic_confidence: Se deve usar sistema de confiança probabilística
        use_llm_arbitration: Se deve usar Llama-3.2-3B para arbitrar casos ambíguos (ATIVADO por padrão)
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