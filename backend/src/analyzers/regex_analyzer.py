"""
Analisador de PII baseado em expressões regulares para documentos brasileiros.
"""

import re
from typing import List, Dict, Any


from src.patterns.gdf_patterns import PATTERNS

class RegexAnalyzer:
    """Detecta entidades PII usando regexes específicas e contexto."""
    def __init__(self):
        # Associa cada padrão a um tipo
        self.patterns = [
            ('CNH', PATTERNS['cnh']),
            ('CPF', PATTERNS['cpf']),
            ('TELEFONE', PATTERNS['telefone']),
            ('MATRICULA_SERVIDOR', PATTERNS['matricula_gdf']),
            ('PROCESSO_SEI', PATTERNS['processo_sei']),
            ('DADOS_BANCARIOS', PATTERNS['agencia_conta']),
            ('CODIGO_BARRAS', PATTERNS['codigo_barras']),
        ]

    def _extrair_digitos(self, val: str) -> str:
        """Extrai apenas dígitos de uma string."""
        return re.sub(r'\D', '', val)

    def _match_dentro_processo_sei(self, text: str, match_start: int, match_end: int) -> bool:
        """Verifica se o match está dentro de um padrão de processo SEI."""
        for sei_match in re.finditer(PATTERNS['processo_sei'], text):
            if sei_match.start() <= match_start and match_end <= sei_match.end():
                return True
        return False

    def analyze(self, text: str) -> List[Dict[str, Any]]:
        """Retorna lista de entidades PII detectadas via regex, com lógica de contexto para evitar FP/FN."""
        results = []
        text_lower = text.lower()
        
        for tipo, pat in self.patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                val = match.group(1) if match.lastindex else match.group()
                digitos = self._extrair_digitos(val)
                
                # ==== CNH ====
                if tipo == 'CNH':
                    contexto = text_lower[max(0, match.start()-80):match.end()+80]
                    pre = text_lower[max(0, match.start()-50):match.start()]
                    pos = text_lower[match.end():min(len(text_lower), match.end()+50)]
                    
                    # Labels de contexto CNH (ampliado)
                    labels_cnh = r'cnh|carteira de motorista|habilita[cç][aã]o|documento de identifica|minha cnh|meu documento|minha carteira|identidade civil|identidade|meu rg|minha identidade|portador da|portador do|registro n[uú]mero|documento n[uú]mero|n[uú]mero do documento'
                    
                    # Contexto negativo: código de barras, boleto, linha digitável, SEI
                    contexto_negativo = re.search(r'c[oó]digo de barras|boleto|linha digit[aá]vel|processo sei|sei[-/]', contexto)
                    if contexto_negativo:
                        continue
                    
                    # CNH de 10 ou 12 dígitos: exige contexto positivo
                    if len(digitos) == 10 or len(digitos) == 12:
                        if not (re.search(labels_cnh, pre) or re.search(labels_cnh, pos) or re.search(labels_cnh, contexto)):
                            continue
                    # CNH de 11 dígitos: aceita sempre, mas evita FP em código de barras
                    elif len(digitos) == 11:
                        if re.search(r'c[oó]digo de barras|boleto|linha digit[aá]vel', contexto):
                            continue
                
                # ==== CÓDIGO DE BARRAS ====
                if tipo == 'CODIGO_BARRAS':
                    # Evita FP de código de barras quando há contexto de CNH
                    if re.search(r'cnh|carteira de motorista|habilita[cç][aã]o', text_lower):
                        continue
                
                # ==== MATRÍCULA SERVIDOR ====
                if tipo == 'MATRICULA_SERVIDOR':
                    # Evita FP: matrícula dentro de processo SEI
                    if self._match_dentro_processo_sei(text, match.start(), match.end()):
                        continue
                    # Se o texto contém processo SEI e a matrícula é parte dele, ignora
                    if re.search(PATTERNS['processo_sei'], text):
                        # Verifica se a matrícula coincide com parte do SEI
                        for sei_match in re.finditer(PATTERNS['processo_sei'], text):
                            sei_val = sei_match.group()
                            if val in sei_val:
                                continue
                
                # ==== PROCESSO SEI ====
                if tipo == 'PROCESSO_SEI':
                    # Processo SEI é válido, não precisa filtrar matrícula
                    pass
                
                # ==== CPF ====
                if tipo == 'CPF':
                    contexto = text_lower[max(0, match.start()-80):match.end()+80]
                    # Contexto positivo ampliado para CPF
                    labels_cpf = r'cpf|contribuinte|titular|cadastro|precisa ser verificado|formato real|com d[ií]gito|com dv|n[uú]mero do cpf|cpf do titular|cpf contribuinte|cadastrado com cpf|cpf:|meu cpf|documento|identifica[cç][aã]o'
                    
                    # CPF com menos de 11 dígitos: exige contexto positivo
                    if len(digitos) < 11:
                        if not re.search(labels_cpf, contexto):
                            continue
                    # CPF com 10 dígitos: pode ser dígito faltando, aceita com contexto
                    if len(digitos) == 10 and re.search(labels_cpf, contexto):
                        pass  # Aceita
                    # CPF com 9 dígitos: só aceita com contexto muito forte
                    if len(digitos) == 9:
                        if not re.search(r'cpf:|meu cpf|cpf do', contexto):
                            continue
                
                # ==== TELEFONE ====
                if tipo == 'TELEFONE':
                    # Telefone sem formatação: exige contexto
                    contexto = text_lower[max(0, match.start()-60):match.end()+60]
                    labels_tel = r'telefone|celular|tel[.:]|fone|contato|ligar|whatsapp|n[uú]mero de contato|meu n[uú]mero'
                    
                    # Se não tem hífen/espaço e não tem contexto, ignora
                    if not re.search(r'[-\s]', val):
                        if not re.search(labels_tel, contexto):
                            continue
                
                # ==== DADOS BANCÁRIOS ====
                if tipo == 'DADOS_BANCARIOS':
                    # Aceita mais formatos: depósito, transferência, PIX, banco
                    contexto = text_lower[max(0, match.start()-80):match.end()+80]
                    labels_banco = r'ag[eê]ncia|conta|banco|dep[oó]sito|transfer[eê]ncia|pix|pagamento|recebimento|c/c|cc|ag\.'
                    if not re.search(labels_banco, contexto):
                        continue
                
                results.append({
                    'entity': 'PII',
                    'tipo': tipo,
                    'start': match.start(),
                    'end': match.end(),
                    'valor': val
                })

        # ==== HEURÍSTICA: DADO SENSÍVEL SAÚDE ====
        palavras_saude_fortes = [
            'tratamento de c[aâ]ncer', 'diagn[oó]stico de c[aâ]ncer',
            'laudo m[eé]dico', 'prontu[aá]rio', 'interna[cç][aã]o',
            'alta m[eé]dica', 'consulta m[eé]dica', 'exame de sangue',
            'receita m[eé]dica', 'atestado m[eé]dico', 'cid-?\d+',
            'paciente portador', 'hist[oó]rico m[eé]dico', 'tratamento oncol[oó]gico'
        ]
        palavras_saude_contexto = [
            'diagn[oó]stico', 'tratamento', 'c[aâ]ncer', 'doen[cç]a',
            'paciente', 'exame', 'cirurgia', 'medica[cç][aã]o', 'rem[eé]dio'
        ]
        
        # Forte: detecta direto
        for p in palavras_saude_fortes:
            if re.search(p, text_lower):
                results.append({
                    'entity': 'PII',
                    'tipo': 'DADO_SAUDE',
                    'start': 0,
                    'end': len(text),
                    'valor': 'Dado sensível saúde (contexto)'
                })
                break
        else:
            # Contexto: precisa de 2+ palavras relacionadas
            matches_saude = sum(1 for p in palavras_saude_contexto if re.search(p, text_lower))
            if matches_saude >= 2:
                results.append({
                    'entity': 'PII',
                    'tipo': 'DADO_SAUDE',
                    'start': 0,
                    'end': len(text),
                    'valor': 'Dado sensível saúde (contexto)'
                })

        # ==== HEURÍSTICA: MENOR DE IDADE IDENTIFICADO ====
        # Idade explícita < 18 + contexto de menor/estudante/escola
        idade_match = re.search(r'\b(\d{1,2})\s*anos?\b', text_lower)
        if idade_match:
            idade = int(idade_match.group(1))
            if idade < 18:
                # Contexto de menor
                contexto_menor = r'estudante|aluno|aluna|escola|col[eé]gio|menor|crian[cç]a|adolescente|filho|filha|respons[aá]vel|guarda|tutor'
                if re.search(contexto_menor, text_lower):
                    results.append({
                        'entity': 'PII',
                        'tipo': 'MENOR_IDENTIFICADO',
                        'start': 0,
                        'end': len(text),
                        'valor': 'Menor de idade identificado (contexto)'
                    })
        
        # Contexto de menor sem idade explícita
        if not idade_match:
            menor_direto = r'menor de idade|crian[cç]a identificad|adolescente identificad|aluno\s+\w+\s+\w+|estudante\s+\w+\s+\w+'
            if re.search(menor_direto, text_lower):
                results.append({
                    'entity': 'PII',
                    'tipo': 'MENOR_IDENTIFICADO',
                    'start': 0,
                    'end': len(text),
                    'valor': 'Menor de idade identificado (contexto)'
                })
        
        return results
