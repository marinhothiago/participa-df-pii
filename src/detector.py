"""Módulo de detecção de Informações Pessoais Identificáveis (PII).

Este módulo implementa um detector híbrido que combina:
1. Regex: Padrões estruturados (CPF, Email, Telefone, RG, CNH)
2. NLP (spaCy): Reconhecimento de entidades nomeadas
3. BERT: Detecção de nomes pessoais com alta precisão
4. Regras de negócio: Contexto Brasília/GDF, imunidade funcional, LAI/LGPD

Abordagem de contexto:
- Agentes públicos em exercício de função: IMUNE (ex: "Dra. Maria na Secretaria")
- Gatilhos de contato anulam imunidade: PII (ex: "Falar com o Dr. João")
- Endereços administrativos: SEGURO (ex: "SQS 302")
- Endereços residenciais: PII (ex: "Rua A Casa 45")
"""

import re
from typing import List, Dict, Tuple, Optional
import spacy
from transformers import pipeline
from text_unidecode import unidecode


class PIIDetector:
    """Detector híbrido de PII para máxima precisão e contexto de Brasília.
    
    Attributes:
        nlp_spacy (spacy.Language): Modelo spaCy pt_core_news_lg para NLP português
        nlp_bert (pipeline): Pipeline BERT para reconhecimento de nomes
        blocklist_total (set): Palavras que nunca são PII (ex: "SOLICITO", "ENCAMINHO")
        termos_seguros (set): Termos institucionais/públicos (órgãos GDF, regiões de Brasília)
        indicadores_servidor (set): Termos que indicam agente público em função
        cargos_autoridade (set): Cargos que conferem imunidade (Dra, Dr, Sr, Sra)
        gatilhos_contato (set): Gatilhos que anulam imunidade (falar com, contato com)
        patterns (dict): Regex patterns para estruturas de PII
    """

    def __init__(self) -> None:
        """Inicializa o detector com modelos NLP e configurações de contexto."""
        print("🏆 [v8.5] VERSÃO 100% FINAL - HACKATHON PARTICIPA DF")
        
        # Carrega modelo spaCy com tratamento de erro
        try:
            self.nlp_spacy = spacy.load("pt_core_news_lg")
        except Exception as e:
            print(f"⚠️ spaCy modelo não carregado: {e}")
            self.nlp_spacy = None

        # Carrega modelo BERT com tratamento de erro
        try:
            self.nlp_bert = pipeline(
                "ner",
                model="neuralmind/bert-large-portuguese-cased",
                aggregation_strategy="simple"
            )
        except Exception as e:
            print(f"⚠️ BERT modelo não carregado: {e}")
            self.nlp_bert = None

        self.blocklist_total = {
            "AGRADECO", "ATENCIOSAMENTE", "CIDADA", "CIDADAO", "BOM DIA", "BOA TARDE", "BOA NOITE",
            "SOLICITO", "INFORMO", "ENCAMINHO", "DESPACHO", "PROCESSO", "AUTOS", "DRA", "DR", "SR", "SRA",
            "SECRETARIA", "DEPARTAMENTO", "DIRETORIA", "GERENCIA", "COORDENACAO", "SUPERINTENDENCIA",
            "LIGACOES", "TELEFONICAS", "MUDAS", "ILUMINACAO", "PUBLICA", "OUVIDORIA", "RECLAMACAO", "DENUNCIA"
        }

        self.termos_seguros = {
            "GDF", "PMDF", "SEEDF", "SESDF", "SSP", "DETRAN", "BRB", "NOVACAP", "CGDF",
            "PCDF", "CBMDF", "CLDF", "TCDF", "DODF", "SEI", "TERRACAP", "CAESB", "NEOENERGIA",
            "BRASILIA", "PLANO PILOTO", "GAMA", "TAGUATINGA", "BRAZLANDIA", "SOBRADINHO",
            "PLANALTINA", "PARANOA", "NUCLEO BANDEIRANTE", "CEILANDIA", "GUARA", "CRUZEIRO",
            "SAMAMBAIA", "SANTA MARIA", "SAO SEBASTIAO", "RECANTO DAS EMAS", "LAGO SUL",
            "LAGO NORTE", "CANDANGOLANDIA", "RIACHO FUNDO", "SUDOESTE", "OCTOGONAL",
            "VARJAO", "PARK WAY", "SCIA", "ESTRUTURAL", "JARDIM BOTANICO", "ITAPOA",
            "SIA", "VICENTE PIRES", "FERCAL", "SOL NASCENTE", "POR DO SOL", "ARNIQUEIRA",
            "ASA SUL", "ASA NORTE", "EIXO MONUMENTAL", "W3", "L2", "SQS", "SQN", "SRES", "SHIS"
        }

        self.indicadores_servidor = {
            "SERVIDOR", "SERVIDORA", "ANALISTA", "TECNICO", "TÉCNICO", "AUDITOR", "FISCAL", 
            "PERITO", "DELEGADO", "ADMINISTRADOR", "COORDENADOR", "DIRETOR", "SECRETARIO", 
            "SECRETÁRIO", "SECRETARIA", "AGENTE", "MEDICO", "MÉDICO"
        }

        self.cargos_autoridade = {"DRA", "DR", "SR", "SRA", "PROF", "DOUTOR", "DOUTORA"}
        
        self.gatilhos_contato = {
            "FALAR COM", "TRATAR COM", "LIGAR PARA", "CONTATO COM", "TELEFONE DO", 
            "CELULAR DO", "WHATSAPP DO", "EMAIL DO", "FALAR COM O", "FALAR COM A", "CONTATO DO"
        }

        self.patterns = {
            'CPF': r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'TELEFONE': r'(?<!\d)(?:\(?\d{2}\)?\s?)?9\d{4,5}[\-\s]?\d{4}(?!\d)',
            'RG_CNH': r'(?i)\b(?:RG|IDENTIDADE|CNH)\b.{0,10}?\b[\d\.X-]{5,15}',
            # V8.5: Aceita formato Brasília (SQS 402 Bloco C) OU tradicional (Casa 45)
            'ENDERECO_RESIDENCIAL': r'(?i)(?:moro|resido|minha casa|meu endere[cç]o|endere[cç]o\s*:).{0,60}(?:\b(?:CASA|APTO|APT|APARTAMENTO|LOTE)\s*(?:N[ºO]?\s*)?\d+|\b(?:SQS|SQN|SRES|SHIS)\s*\d+\s*(?:BLOCO|BL)\s*[A-Z0-9]+)'
        }

    def _normalizar(self, texto):
        return unidecode(texto).upper().strip() if texto else ""

    def _eh_lixo(self, texto_entidade):
        if not texto_entidade or len(texto_entidade) < 3: return True
        t_norm = self._normalizar(texto_entidade)
        
        if t_norm in self.blocklist_total: return True
        if any(ts in t_norm for ts in self.termos_seguros): return True
        if re.match(r'^[\d/\.\-\s]+$', texto_entidade): return True
        
        palavras_bloqueadas = {"LIGACOES", "TELEFONICAS", "RECLAMACAO", "DENUNCIA", "PROTOCOLO", "PROCESSO"}
        if any(p in t_norm for p in palavras_bloqueadas): return True
        
        return False

    def _cpf_em_contexto_negativo(self, texto, cpf_valor):
        idx = texto.find(cpf_valor)
        if idx == -1: return False
        contexto = texto[max(0, idx-30):min(len(texto), idx+len(cpf_valor)+30)].upper()
        palavras_negativas = ["INVALIDO", "INVÁLIDO", "FALSO", "FICTICIO", "FICTÍCIO"]
        return any(p in contexto for p in palavras_negativas)

    def _cpf_invalido_obvio(self, cpf_raw):
        numeros = [d for d in cpf_raw if d.isdigit()]
        if len(set(numeros)) == 1:
            if numeros[0] == '0':
                return False
            return True
        return False

    def _extrair_nome_apos_gatilho(self, texto):
        nomes_encontrados = []
        texto_upper = self._normalizar(texto)
        
        for gatilho in self.gatilhos_contato:
            if gatilho in texto_upper:
                idx = texto_upper.find(gatilho) + len(gatilho)
                resto = texto[idx:idx+50].strip()
                
                match = re.search(r'\b(?:o|a)?\s*(?:\w+\s+)?([A-Z][a-záéíóúàèìòùâêîôûãõ]+)\b', resto)
                if match:
                    nome = match.group(1)
                    nome_upper = nome.upper()
                    
                    if nome_upper in self.cargos_autoridade:
                        continue
                    if nome_upper in self.indicadores_servidor:
                        continue
                    if len(nome) > 3:
                        nomes_encontrados.append({"tipo": "NOME_CONTEXTO", "valor": nome, "conf": 0.85})
        
        return nomes_encontrados

    def _deve_ignorar_nome(self, texto_original, start_index):
        if start_index < 3: return False
        pre_text = unidecode(texto_original[max(0, start_index-60):start_index].upper())

        for cargo in self.cargos_autoridade:
            if re.search(rf"\b{cargo}\.?\s*$", pre_text):
                return True

        for gatilho in self.gatilhos_contato:
            if gatilho in pre_text:
                return False 

        if any(ind in pre_text for ind in self.indicadores_servidor):
            return True
        
        return False

    def detect(self, text):
        if not text: return False, [], "SEGURO", 0.0
        findings = []

        for label, regex in self.patterns.items():
            for match in re.finditer(regex, text, re.IGNORECASE):
                val = match.group()
                
                if label == 'CPF':
                    if self._cpf_em_contexto_negativo(text, val):
                        continue
                    if self._cpf_invalido_obvio(val):
                        continue
                    findings.append({"tipo": "CPF", "valor": val, "conf": 1.0})
                
                elif label == 'EMAIL':
                    if not any(x in val.lower() for x in ['gov.br', 'df.gov.br']):
                        findings.append({"tipo": "EMAIL", "valor": val, "conf": 1.0})
                
                elif label == 'TELEFONE':
                    findings.append({"tipo": "TELEFONE", "valor": val, "conf": 0.9})
                
                elif label in ['RG_CNH', 'ENDERECO_RESIDENCIAL']:
                    findings.append({"tipo": label, "valor": val, "conf": 1.0})

        nomes_gatilho = self._extrair_nome_apos_gatilho(text)
        findings.extend(nomes_gatilho)

        threshold = 0.75

        for nome_nlp, nlp in [("BERT", self.nlp_bert), ("SPACY", self.nlp_spacy)]:
            if not nlp: continue
            try:
                if nome_nlp == "BERT":
                    ents = nlp(text)
                    for ent in ents:
                        word = ent['word'].strip()
                        if ent['entity_group'] == 'PER' and ent['score'] > threshold:
                            if len(word) > 2 and " " in word and not self._eh_lixo(word):
                                if self._deve_ignorar_nome(text, ent['start']):
                                    continue
                                findings.append({"tipo": "NOME_PESSOAL", "valor": word, "conf": float(ent['score'])})
                else:
                    doc = nlp(text)
                    for ent in doc.ents:
                        if ent.label_ == 'PER' and " " in ent.text and not self._eh_lixo(ent.text):
                            if self._deve_ignorar_nome(text, ent.start_char):
                                continue
                            if not any(f['valor'] == ent.text for f in findings):
                                findings.append({"tipo": "IA_PER", "valor": ent.text, "conf": 0.80})
            except: pass

        pesos = {
            "CPF": 5, "RG_CNH": 5, "EMAIL": 4, "TELEFONE": 4, 
            "ENDERECO_RESIDENCIAL": 4, "NOME_PESSOAL": 4, "IA_PER": 3, "NOME_CONTEXTO": 4
        }
        
        final_dict = {}
        for f in findings:
            v_key = f['valor'].strip().lower()
            peso_atual = pesos.get(f['tipo'], 0)
            if v_key not in final_dict or peso_atual > pesos.get(final_dict[v_key]['tipo'], 0):
                final_dict[v_key] = f

        final_list = list(final_dict.values())
        pii_relevantes = [f for f in final_list if pesos.get(f['tipo'], 0) >= 3]
        max_score = max([pesos.get(f['tipo'], 0) for f in pii_relevantes]) if pii_relevantes else 0
        
        is_pii = max_score >= 3
        risco_map = {5: "CRÍTICO", 4: "ALTO", 3: "MODERADO", 0: "SEGURO"}
        
        return is_pii, pii_relevantes, risco_map.get(max_score, "BAIXO"), float(max_score)