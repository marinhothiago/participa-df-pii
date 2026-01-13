import re
import spacy
from src.allow_list import ALLOW_LIST_TERMS, BLOCK_IF_CONTAINS

class PIIDetector:
    def __init__(self):
        try:
            self.nlp = spacy.load("pt_core_news_lg")
        except Exception:
            print("Erro: Instale o modelo pt_core_news_lg")
        
        self.patterns = {
            'CPF': r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{1,2}\b',
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'TELEFONE': r'\(?\d{2}\)?\s?9?\d{4}-?\d{4}',
            'RG': r'\b\d{1,2}\.\d{3}\.\d{3}-[0-9X|x]\b|\b\d{8,9}[0-9X|x]\b',
            # Regex de endereço que trava em quebras de linha ou múltiplos espaços
            'ENDERECO_ESTRUTURADO': r'(?i)\b(Rua|Av|Avenida|Setor|Lote|Conjunto|Condomínio|Trecho|Eixo)\b\s+[A-ZÁ-ú0-9][a-zÁ-ú0-9\s\.]{1,40}?\d+'
        }

    def validar_cpf_matematicamente(self, cpf):
        nums = re.sub(r'\D', '', str(cpf))
        if len(nums) != 11: return False
        if nums == nums[0] * 11: return False
        for i in range(9, 11):
            soma = sum(int(nums[num]) * ((i + 1) - num) for num in range(i))
            digito = (soma * 10 % 11) % 10
            if digito != int(nums[i]): return False
        return True

    def detect(self, text):
        if not text or not isinstance(text, str):
            return False, [], "SEGURO", 0.99

        findings = []
        doc = self.nlp(text)
        
        # Filtro de Órgãos e Instituições (Ignora entidades públicas)
        termos_publicos = ["CONSTITUIÇÃO", "FEDERAL", "MPSP", "CGDF", "PMDF", "PREFEITURA", "JUSTIÇA", "AUTOS", "PROCESSO SEI", "CONTROLADORIA", "GAMPES"]

        # --- 1. CAMADA REGEX (Busca Padrões Exatos) ---
        for label, regex in self.patterns.items():
            for match in re.finditer(regex, text):
                m = match.group().strip()
                pos = match.start()
                ctx_prev = text[max(0, pos-40) : pos].upper()
                
                # Ignora se tiver palavras de sistema (SEI, Protocolo) antes
                if any(tag in ctx_prev for tag in ["SEI", "PROTOCOL", "LAI"]):
                    continue

                conf = 0.95
                if label == 'CPF':
                    if not self.validar_cpf_matematicamente(m) and "CPF" not in ctx_prev:
                        continue
                    conf = 0.99
                
                findings.append({"tipo": label, "valor": m, "conf": conf})

        # --- 2. CAMADA NLP (Contexto e Nomes) ---
        for ent in doc.ents:
            val_raw = ent.text.strip()
            val_up = val_raw.upper()
            
            # Filtro Gramatical (Ignora verbos e advérbios)
            if ent.root.pos_ in ["VERB", "ADJ", "AUX", "PRON", "ADV"]:
                continue

            if any(t in val_up for t in termos_publicos):
                continue

            # Nomes Pessoais
            if ent.label_ == 'PER' and " " in val_raw and len(val_raw) > 8:
                if not any(f['valor'] in val_raw for f in findings):
                    findings.append({"tipo": "NOME_PESSOAL", "valor": val_raw, "conf": 0.90})
            
            # Endereços/Locais
            elif ent.label_ == 'LOC' and len(val_raw) > 5:
                # Lógica simplificada de endereço
                if not any(val_raw in f['valor'] for f in findings):
                     findings.append({"tipo": "ENDERECO_SENSIVEL", "valor": val_raw, "conf": 0.85})

        # --- 3. DEDUPLICAÇÃO ---
        findings = sorted(findings, key=lambda x: len(x['valor']), reverse=True)
        final_findings = []
        for f in findings:
            if not any(f['valor'] in entry['valor'] for entry in final_findings if f != entry):
                final_findings.append(f)

        if not final_findings:
            return False, [], "SEGURO", 0.99 # Sem risco
        
        # --- 4. CÁLCULO DE RISCO REAL (NOVA LÓGICA LGPD) ---
        # Aqui definimos o "peso" de cada dado vazado
        mapa_risco = {
            'CPF': 4,       # Crítico (Documento Único)
            'RG': 3,        # Alto
            'EMAIL': 2,     # Moderado
            'TELEFONE': 2,  # Moderado
            'ENDERECO_ESTRUTURADO': 3, # Alto (Endereço completo)
            'ENDERECO_SENSIVEL': 2,
            'NOME_PESSOAL': 1 # Baixo (Nome sozinho as vezes é público)
        }

        # Pega o maior nível de risco encontrado na lista
        max_peso = 0
        for f in final_findings:
            peso = mapa_risco.get(f['tipo'], 2) # Se não souber, assume 2
            if peso > max_peso:
                max_peso = peso

        # Traduz o número para Texto de Risco
        if max_peso >= 4:
            risco_final = "CRÍTICO"
        elif max_peso == 3:
            risco_final = "ALTO"
        elif max_peso == 2:
            risco_final = "MODERADO"
        else:
            risco_final = "BAIXO" # Risco mínimo, mas ainda há algo

         # Média de confiança da IA (apenas estatística)
        avg_conf = sum([f['conf'] for f in final_findings]) / len(final_findings)
        
        return True, final_findings, risco_final, avg_conf