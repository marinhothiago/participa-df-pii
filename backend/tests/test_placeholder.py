"""
Testes básicos de sanidade do PIIDetector.
Verifica se o detector inicializa corretamente e detecta casos triviais.

O detector é carregado via fixture global em conftest.py (scope=session).
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest

# NOTA: Fixture 'detector' vem do conftest.py (scope=session)
# Não precisa definir aqui - pytest encontra automaticamente


class TestDetectorSanity:
    """Testes de sanidade básica do detector."""
    
    def test_detector_inicializa(self, detector):
        """Verifica se o detector inicializa sem erros."""
        assert detector is not None
        assert hasattr(detector, 'detect')
    
    def test_detector_retorna_tupla_4_elementos(self, detector):
        """Verifica se detect() retorna tupla com 4 elementos."""
        resultado = detector.detect("Texto qualquer")
        assert isinstance(resultado, tuple)
        assert len(resultado) == 4
    
    def test_texto_vazio_e_seguro(self, detector):
        """Texto vazio não deve conter PII."""
        contem_pii, achados, risco, confianca = detector.detect("")
        assert contem_pii is False
        assert achados == []
    
    def test_texto_simples_sem_pii(self, detector):
        """Texto simples sem dados pessoais."""
        contem_pii, achados, risco, confianca = detector.detect("Bom dia, como posso ajudar?")
        assert contem_pii is False
    
    def test_cpf_valido_detectado(self, detector):
        """CPF válido deve ser detectado."""
        contem_pii, achados, risco, confianca = detector.detect("Meu CPF é 529.982.247-25")
        assert contem_pii is True
        tipos = [a.get('tipo', a.get('entity_type', '')) for a in achados]
        assert any('CPF' in t.upper() for t in tipos)
    
    def test_email_pessoal_detectado(self, detector):
        """Email pessoal deve ser detectado."""
        contem_pii, achados, risco, confianca = detector.detect("Email: joao@gmail.com")
        assert contem_pii is True
    
    def test_telefone_celular_detectado(self, detector):
        """Telefone celular deve ser detectado."""
        contem_pii, achados, risco, confianca = detector.detect("Meu celular: (61) 99999-8888")
        assert contem_pii is True
    
    def test_nome_completo_detectado(self, detector):
        """Nome completo deve ser detectado."""
        contem_pii, achados, risco, confianca = detector.detect("O requerente João Carlos Silva compareceu")
        assert contem_pii is True
    
    def test_email_institucional_nao_e_pii(self, detector):
        """Email institucional gov.br não deve ser PII."""
        contem_pii, achados, risco, confianca = detector.detect("Contato: ouvidoria@saude.df.gov.br")
        assert contem_pii is False
    
    def test_telefone_institucional_nao_e_pii(self, detector):
        """Telefone 0800 não deve ser PII."""
        contem_pii, achados, risco, confianca = detector.detect("Ligue: 0800 644 9100")
        assert contem_pii is False
    
    def test_cnpj_nao_e_pii_pessoal(self, detector):
        """CNPJ de empresa não deve ser considerado PII pessoal."""
        contem_pii, achados, risco, confianca = detector.detect("CNPJ: 12.345.678/0001-99")
        assert contem_pii is False
    
    def test_processo_sei_nao_e_pii(self, detector):
        """Número de processo SEI não deve ser PII."""
        contem_pii, achados, risco, confianca = detector.detect("Processo SEI 00015-01009853/2023-11")
        assert contem_pii is False


class TestNiveisRisco:
    """Testes dos níveis de risco retornados."""
    
    def test_risco_retornado_e_string(self, detector):
        """Nível de risco deve ser uma string."""
        _, _, risco, _ = detector.detect("Qualquer texto")
        assert isinstance(risco, str)
    
    def test_confianca_entre_0_e_1(self, detector):
        """Confiança deve estar entre 0 e 1."""
        _, _, _, confianca = detector.detect("CPF: 529.982.247-25")
        assert 0 <= confianca <= 1


class TestEdgeCases:
    """Testes de casos extremos."""
    
    def test_texto_muito_longo(self, detector):
        """Detector deve lidar com texto muito longo."""
        texto_longo = "Texto normal sem PII. " * 1000
        resultado = detector.detect(texto_longo)
        assert resultado is not None
        assert len(resultado) == 4
    
    def test_caracteres_especiais(self, detector):
        """Detector deve lidar com caracteres especiais."""
        texto = "Símbolos: @#$%^&*()[]{}|\\<>?/"
        resultado = detector.detect(texto)
        assert resultado is not None
    
    def test_unicode_acentos(self, detector):
        """Detector deve lidar com acentos e unicode."""
        texto = "José João açúcar café São Paulo"
        resultado = detector.detect(texto)
        assert resultado is not None
    
    def test_numeros_isolados_nao_sao_pii(self, detector):
        """Números isolados não devem ser PII."""
        contem_pii, _, _, _ = detector.detect("O valor é 12345")
        assert contem_pii is False
