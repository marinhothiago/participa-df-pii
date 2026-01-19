"""
Validadores de Dígito Verificador para documentos brasileiros.

Implementa validação matemática para:
- CPF (Módulo 11)
- CNPJ (Módulo 11 com pesos)
- PIS/NIT (Módulo 11 com pesos)
- CNS - Cartão Nacional de Saúde
- Título de Eleitor
- Cartão de Crédito (Algoritmo de Luhn)
"""

import re
from typing import Optional, Tuple


class DVValidator:
    def cpf_tem_formato_valido(self, valor: str) -> bool:
        """Verifica se o CPF tem formato válido (11 dígitos, não repetido)."""
        cpf = self.limpar_numero(valor)
        if len(cpf) != 11:
            return False
        if cpf == cpf[0] * 11:
            return False
        return True

    def cpf_dv_correto(self, valor: str) -> bool:
        """Verifica se o dígito verificador do CPF está correto."""
        return self.validar_cpf(valor)
    """Validador de Dígito Verificador para documentos brasileiros."""
    
    @staticmethod
    def limpar_numero(valor: str) -> str:
        """Remove formatação, mantendo apenas dígitos."""
        return re.sub(r'\D', '', valor)
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Valida CPF com algoritmo Módulo 11.
        
        Args:
            cpf: CPF com ou sem formatação (000.000.000-00 ou 00000000000)
            
        Returns:
            True se CPF é válido, False caso contrário
        """
        cpf = DVValidator.limpar_numero(cpf)
        
        # Deve ter 11 dígitos
        if len(cpf) != 11:
            return False
        
        # Rejeita sequências repetidas (111.111.111-11, etc)
        if cpf == cpf[0] * 11:
            return False
        
        # Calcula primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        d1 = (soma * 10) % 11
        d1 = 0 if d1 >= 10 else d1
        
        if int(cpf[9]) != d1:
            return False
        
        # Calcula segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        d2 = (soma * 10) % 11
        d2 = 0 if d2 >= 10 else d2
        
        return int(cpf[10]) == d2
    
    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:
        """Valida CNPJ com algoritmo Módulo 11.
        
        Args:
            cnpj: CNPJ com ou sem formatação
            
        Returns:
            True se CNPJ é válido, False caso contrário
        """
        cnpj = DVValidator.limpar_numero(cnpj)
        
        if len(cnpj) != 14:
            return False
        
        if cnpj == cnpj[0] * 14:
            return False
        
        # Pesos para primeiro DV
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
        d1 = 11 - (soma % 11)
        d1 = 0 if d1 >= 10 else d1
        
        if int(cnpj[12]) != d1:
            return False
        
        # Pesos para segundo DV
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
        d2 = 11 - (soma % 11)
        d2 = 0 if d2 >= 10 else d2
        
        return int(cnpj[13]) == d2
    
    @staticmethod
    def validar_pis(pis: str) -> bool:
        """Valida PIS/NIT/PASEP com Módulo 11.
        
        Args:
            pis: PIS com ou sem formatação
            
        Returns:
            True se PIS é válido, False caso contrário
        """
        pis = DVValidator.limpar_numero(pis)
        
        if len(pis) != 11:
            return False
        
        if pis == pis[0] * 11:
            return False
        
        pesos = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(pis[i]) * pesos[i] for i in range(10))
        resto = soma % 11
        dv = 0 if resto < 2 else 11 - resto
        
        return int(pis[10]) == dv
    
    @staticmethod
    def validar_cns(cns: str) -> bool:
        """Valida Cartão Nacional de Saúde (CNS).
        
        O CNS tem regras específicas baseadas no primeiro dígito:
        - Começa com 1 ou 2: provisório (algoritmo específico)
        - Começa com 7, 8 ou 9: definitivo (Módulo 11)
        
        Args:
            cns: CNS com ou sem formatação
            
        Returns:
            True se CNS é válido, False caso contrário
        """
        cns = DVValidator.limpar_numero(cns)
        
        if len(cns) != 15:
            return False
        
        # CNS provisório (começa com 1 ou 2)
        if cns[0] in ['1', '2']:
            soma = sum(int(cns[i]) * (15 - i) for i in range(15))
            return soma % 11 == 0
        
        # CNS definitivo (começa com 7, 8 ou 9)
        if cns[0] in ['7', '8', '9']:
            soma = sum(int(cns[i]) * (15 - i) for i in range(15))
            return soma % 11 == 0
        
        return False
    
    @staticmethod
    def validar_titulo_eleitor(titulo: str) -> bool:
        """Valida Título de Eleitor.
        
        O título tem 12 dígitos:
        - 8 primeiros: número sequencial
        - 2 seguintes: código do estado (01-28)
        - 2 últimos: dígitos verificadores
        
        Args:
            titulo: Título de eleitor com ou sem formatação
            
        Returns:
            True se título é válido, False caso contrário
        """
        titulo = DVValidator.limpar_numero(titulo)
        
        if len(titulo) != 12:
            return False
        
        # Código do estado (posições 8 e 9)
        estado = int(titulo[8:10])
        if estado < 1 or estado > 28:
            return False
        
        # Primeiro DV
        soma = sum(int(titulo[i]) * (i + 2) for i in range(8))
        d1 = soma % 11
        if d1 == 0 and estado in [1, 2]:  # SP e MG
            d1 = 1
        elif d1 == 0:
            d1 = 0
        elif d1 == 1:
            d1 = 0
        else:
            d1 = 11 - d1
        
        if int(titulo[10]) != d1:
            return False
        
        # Segundo DV
        soma = int(titulo[8]) * 7 + int(titulo[9]) * 8 + d1 * 9
        d2 = soma % 11
        if d2 == 0:
            d2 = 0
        elif d2 == 1:
            d2 = 0
        else:
            d2 = 11 - d2
        
        return int(titulo[11]) == d2
    
    @staticmethod
    def validar_cartao_credito(numero: str) -> bool:
        """Valida número de cartão de crédito com algoritmo de Luhn.
        
        Args:
            numero: Número do cartão com ou sem formatação
            
        Returns:
            True se número é válido pelo algoritmo de Luhn
        """
        numero = DVValidator.limpar_numero(numero)
        
        if len(numero) < 13 or len(numero) > 19:
            return False
        
        soma = 0
        dobrar = False
        
        # Percorre da direita para esquerda
        for i in range(len(numero) - 1, -1, -1):
            digito = int(numero[i])
            
            if dobrar:
                digito *= 2
                if digito > 9:
                    digito -= 9
            
            soma += digito
            dobrar = not dobrar
        
        return soma % 10 == 0
    
    def validar(self, valor: str, tipo_pii: str) -> Optional[bool]:
        """Valida um valor baseado no tipo de PII.
        
        Args:
            valor: Valor a ser validado
            tipo_pii: Tipo de PII (CPF, CNPJ, PIS, etc)
            
        Returns:
            True se válido, False se inválido, None se tipo não suporta DV
        """
        tipo_upper = tipo_pii.upper()
        
        validadores = {
            "CPF": self.validar_cpf,
            "CNPJ": self.validar_cnpj,
            "CNPJ_PESSOAL": self.validar_cnpj,
            "PIS": self.validar_pis,
            "CNS": self.validar_cns,
            "TITULO_ELEITOR": self.validar_titulo_eleitor,
            "CARTAO_CREDITO": self.validar_cartao_credito,
        }
        
        validador = validadores.get(tipo_upper)
        if validador is None:
            return None  # Tipo não suporta validação DV
        
        try:
            return validador(valor)
        except Exception:
            return False
    
    def get_dv_confidence(self, tipo_pii: str, valor: str) -> Tuple[float, Optional[bool]]:
        """Retorna score de confiança baseado na validação DV.
        
        Args:
            tipo_pii: Tipo de PII
            valor: Valor a ser validado
            
        Returns:
            Tupla (confidence, is_valid):
            - (0.9999, True) se DV válido
            - (0.0001, False) se DV inválido
            - (0.5, None) se tipo não suporta validação
        """
        resultado = self.validar(valor, tipo_pii)
        
        if resultado is None:
            return 0.5, None  # Não suporta DV - neutro
        elif resultado:
            return 0.9999, True  # DV válido - muito alta confiança
        else:
            return 0.0001, False  # DV inválido - muito baixa confiança
