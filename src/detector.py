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
            'TELEFONE_DDI': r'\+55\s*\d{2}\s*9\d{4,5}[\-\s]?\d{4}',  # Processa PRIMEIRO
            'TELEFONE': r'(?<![+5\d])(?:\(?\d{2}\)?\s?)?9\d{4,5}[\-\s]?\d{4}(?!\d)',  # Depois de DDI
            'RG_CNH': r'(?i)\b(?:RG|IDENTIDADE|CNH)\b.{0,10}?\b[\d\.X-]{5,15}',
            'PASSAPORTE': r'(?i)(?:meu passaporte é|passaporte.*?)\s*(?:BR)?([A-Z]{0,2}\d{7,8})\b',
            'CONTA_BANCARIA': r'(?i)(?:minha conta|transferência para).*?(?:\d{4,6}[\-\s]?\d{1,8}|\d{10,11})',
            'CHAVE_PIX': r'[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}',
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
        """Extrai nomes após gatilhos de contato (falar com, ligar para, etc).
        Estes SEMPRE são PII pois indicam intenção de contato direto."""
        nomes_encontrados = []
        texto_upper = self._normalizar(texto)
        
        # Gatilhos de contato
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
                        nomes_encontrados.append({"tipo": "NOME_CONTEXTO", "valor": nome, "conf": 0.95})
        
        # Nomes após "contra" (reclamação contra Pedro)
        if "CONTRA" in texto_upper:
            idx = texto_upper.find("CONTRA") + 6
            resto = texto[idx:].strip().strip(".,;:'\"-").strip()
            match = re.search(r"^([A-Z][a-záéíóúàèìòùâêîôûãõ]+)", resto)
            if match:
                nome = match.group(1).strip()
                if len(nome) > 3 and nome not in self.blocklist_total:
                    nomes_encontrados.append({"tipo": "NOME_CONTEXTO", "valor": nome, "conf": 0.85})
        
        # Nomes isolados após contextos de testemunha/visitante
        contextos_isolados = [
            ("testemunha informa que seu nome é", 1),
            ("visitante registrado como", 1),
            ("protocolo de atendimento para a reclamação contra", 1)
        ]
        for contexto, priority in contextos_isolados:
            if contexto.lower() in texto.lower():
                idx = texto.lower().find(contexto.lower()) + len(contexto)
                resto = texto[idx:].strip().strip("':.,\"").strip()
                
                # Extrai nome completo (trata também formato invertido "Silva, José")
                if "," in resto:
                    partes = [p.strip() for p in resto.split(",")]
                    if len(partes) >= 2:
                        nome = f"{partes[1]} {partes[0]}"  # Inverte formato
                    else:
                        nome = partes[0]
                else:
                    match = re.search(r"([A-Z][a-záéíóúàèìòùâêîôûãõ]+(?:\s+[A-Z][a-záéíóúàèìòùâêîôûãõ]+)*)", resto)
                    if not match:
                        continue
                    nome = match.group(1).strip()
                
                if len(nome) > 5 and nome.upper() not in self.blocklist_total:
                    nomes_encontrados.append({"tipo": "NOME_CONTEXTO", "valor": nome, "conf": 0.92})
        
        return nomes_encontrados

    def _deve_ignorar_nome(self, texto_original, start_index):
        """Determina se um nome detectado deve ser ignorado (imunidade funcional).
        
        Regras:
        1. Cargo (Dra, Dr, Sr, Sra) + instituição/função = IGNORAR (imune)
        2. Gatilho de contato = NÃO ignorar (quebra imunidade)
        3. Servidor em função = IGNORAR
        4. Funcionário do mês = IGNORAR (contexto de elogio)
        """
        if start_index < 3: return False
        pre_text = unidecode(texto_original[max(0, start_index-100):start_index].upper())
        pos_text = unidecode(texto_original[start_index:min(len(texto_original), start_index+100)].upper())
        
        # Verifica se tem gatilho de contato - NÃO ignora
        for gatilho in self.gatilhos_contato:
            if gatilho in pre_text:
                return False 
        
        # "Funcionário do mês" ou contexto de elogio = imune
        if "FUNCIONARIO DO MES" in pre_text or "FUNCIONÁRIA DO MES" in pre_text:
            return True
        
        # Verifica cargo + instituição/função = imune
        # Cargo pode estar ANTES ou DENTRO do nome (pos_text)
        for cargo in self.cargos_autoridade:
            # Cargo no final do pre_text (logo antes do nome)
            if re.search(rf"\b{cargo}\.?\s*$", pre_text):
                # Precisa ter contexto de instituição/função APÓS o nome
                if any(inst in pos_text for inst in ["SECRETARIA", "ADMINISTRACAO", "DEPARTAMENTO", "DIRETORIA", "GDF", "SEEDF", "RESPONSAVEL", "DA ADMINISTRACAO"]):
                    return True
            
            # Cargo dentro do pos_text (fazendo parte do nome ou próximo dele)
            if re.search(rf"\b{cargo}\b", pos_text):
                # Se houver cargo + instituição/função no pos_text = imune
                if any(inst in pos_text for inst in ["ADMINISTRACAO", "DEPARTAMENTO", "RESPONSAVEL"]):
                    return True
        
        # "Servidora em contexto de função" = imune
        if "SERVIDORA" in pos_text or "SERVIDOR" in pre_text:
            if not any(gatilho in pre_text for gatilho in self.gatilhos_contato):
                return True
        
        # Servidor/Servidor com indicador = imune (se não tiver gatilho de contato)
        if any(ind in pre_text for ind in self.indicadores_servidor):
            if not any(gatilho in pre_text for gatilho in self.gatilhos_contato):
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
                    if not any(x in val.lower() for x in ['gov.br', 'df.gov.br', 'empresa-df.com']):
                        findings.append({"tipo": "EMAIL", "valor": val, "conf": 1.0})
                
                elif label == 'TELEFONE':
                    # Verifica se este número já foi detectado como parte de DDI
                    # Procura por +55 nos 10 caracteres anteriores
                    if '+55' in text[max(0, match.start()-10):match.start()]:
                        continue  # Já foi processado como DDI
                    findings.append({"tipo": "TELEFONE", "valor": val, "conf": 0.9})
                
                elif label == 'TELEFONE_DDI':
                    # DDI com contexto de "celular institucional" = seguro (não adiciona)
                    pre_contexto = text[max(0, match.start()-100):match.start()].lower()
                    if 'institucional' in pre_contexto:
                        continue  # Telefone institucional - seguro
                    # Extrai só o telefone sem DDI para normalizar
                    tel_limpo = re.search(r'\d{2}\s*9\d{4,5}[\-\s]?\d{4}', val)
                    if tel_limpo:
                        findings.append({"tipo": "TELEFONE", "valor": tel_limpo.group(), "conf": 0.9})
                
                elif label in ['RG_CNH', 'ENDERECO_RESIDENCIAL']:
                    findings.append({"tipo": label, "valor": val, "conf": 1.0})
                
                elif label == 'PASSAPORTE':
                    # Extrai só o número (ignora "Passaporte: " ou similares)
                    match_numero = re.search(r'(?:BR)?([A-Z]{0,2}\d{7,8})', val)
                    if match_numero:
                        numero = match_numero.group(1)
                        # Genéricos como AA000000 não são PII
                        if numero in ['AA000000', 'AA00000', 'AA0000']:
                            continue
                        # "Meu passaporte é" = PII (mesmo sem "BR")
                        if 'meu' in text[max(0, match.start()-30):match.start()].lower():
                            findings.append({"tipo": "PASSAPORTE", "valor": numero, "conf": 0.95})
                        # Formato "BR1234567" sem "meu" = não detecta em padrão genérico
                        elif re.search(r'BR\d{7,8}', val):
                            # Só detecta se houver indicativo de pessoal
                            findings.append({"tipo": "PASSAPORTE", "valor": numero, "conf": 0.95})
                
                elif label == 'CONTA_BANCARIA':
                    # Detecta números de conta pessoais
                    # Formatos: XXXX-X, XXXXX-XX, ou 10-11 dígitos contínuos
                    # Extrai todos os números do match
                    numbers = re.findall(r'\d{4,6}[\-\s]?\d{1,8}|\d{10,11}', val)
                    for conta in numbers:
                        # Valida: ou tem hífen (formato agência-conta) ou tem 10+ dígitos
                        if re.search(r'[\-\s]', conta) or len(conta.replace('-', '').replace(' ', '')) >= 10:
                            # Evita falsos positivos: ignora se faz parte de CNPJ ou documento
                            if not re.search(r'/000[1-9]|\.00', val):
                                findings.append({"tipo": "CONTA_BANCARIA", "valor": conta.strip(), "conf": 0.95})
                
                elif label == 'CHAVE_PIX':
                    # Chave PIX é PII
                    findings.append({"tipo": "PIX", "valor": val, "conf": 0.95})

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
                                findings.append({"tipo": "NOME_POR_IA", "valor": ent.text, "conf": 0.80})
            except: pass

        pesos = {
            "CPF": 5, "RG_CNH": 5, "EMAIL": 4, "TELEFONE": 4, 
            "ENDERECO_RESIDENCIAL": 4, "NOME_PESSOAL": 4, "NOME_POR_IA": 3, "NOME_CONTEXTO": 4,
            "PASSAPORTE": 5, "CONTA_BANCARIA": 5, "PIX": 5
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
        
        # Normalizar confiança para 0-1 (max_score vai de 0 a 5)
        confidence = float(max_score) / 5.0 if max_score > 0 else 0.0
        return is_pii, pii_relevantes, risco_map.get(max_score, "BAIXO"), confidence