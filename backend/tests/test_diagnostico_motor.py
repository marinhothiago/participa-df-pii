#!/usr/bin/env python3
"""
diagnostico_motor.py
=====================
Script de diagnóstico completo para validar integração do Motor PII.
Verifica cada componente e a integração entre eles.

Uso:
    python diagnostico_motor.py
    python diagnostico_motor.py --verbose
    python diagnostico_motor.py --fix  # Tenta corrigir problemas
"""


import os
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import importlib
import json

# === AJUSTE DE PATHS PARA IMPORTS ROBUSTOS ===
# Calcula o root do projeto (backend/) a partir deste arquivo
PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_PATH = os.path.join(PROJ_ROOT, 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# Permite importar o dataset localmente, independente do CWD
DATASET_PATH = os.path.join(os.path.dirname(__file__), 'test_diagnostico_motor_dataset_lgpd.py')
if os.path.isfile(DATASET_PATH):
    import importlib.util
    spec = importlib.util.spec_from_file_location("test_diagnostico_motor_dataset_lgpd", DATASET_PATH)
    dataset_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dataset_mod)
    DATASET_LGPD = dataset_mod.DATASET_LGPD
else:
    DATASET_LGPD = []

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

class Status(Enum):
    OK = "✅ OK"
    WARN = "⚠️ AVISO"
    FAIL = "❌ FALHA"
    SKIP = "⏭️ PULADO"

@dataclass
class TestResult:
    nome: str
    status: Status
    mensagem: str
    tempo_ms: float = 0.0
    detalhes: Optional[Dict] = None
    excecao: Optional[str] = None

@dataclass
class DiagnosticoReport:
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    componentes: List[TestResult] = field(default_factory=list)
    integracoes: List[TestResult] = field(default_factory=list)
    fluxo_completo: List[TestResult] = field(default_factory=list)
    performance: List[TestResult] = field(default_factory=list)
    
    @property
    def total_ok(self) -> int:
        todos = self.componentes + self.integracoes + self.fluxo_completo + self.performance
        return sum(1 for t in todos if t.status == Status.OK)
    
    @property
    def total_fail(self) -> int:
        todos = self.componentes + self.integracoes + self.fluxo_completo + self.performance
        return sum(1 for t in todos if t.status == Status.FAIL)
    
    @property
    def total_warn(self) -> int:
        todos = self.componentes + self.integracoes + self.fluxo_completo + self.performance
        return sum(1 for t in todos if t.status == Status.WARN)

# ============================================================================
# TESTES DE COMPONENTES INDIVIDUAIS
# ============================================================================

class DiagnosticoMotor:
    def teste_fluxo_completo(self) -> Dict:
        """Executa benchmark real: roda o detector em todo o DATASET_LGPD, calcula métricas e tempo."""
        import time
        t0_total = time.time()
        print("[PROFILING] Iniciando teste_fluxo_completo", flush=True)
        try:
            t0_import = time.time()
            print("[PROFILING] Importando detector...", flush=True)
            import detector as detector_mod
            print(f"[PROFILING] detector importado em {time.time() - t0_import:.2f}s", flush=True)
            t0_inst = time.time()
            detector_instance = detector_mod.PIIDetector()
            print(f"[PROFILING] Instanciado PIIDetector em {time.time() - t0_inst:.2f}s", flush=True)
        except Exception as e:
            print(f"[PROFILING][ERRO] Falha no import/instanciação: {e}", flush=True)
            return {'status': Status.FAIL, 'mensagem': f'Erro ao importar PIIDetector: {e}'}
        if not DATASET_LGPD:
            print("[PROFILING][ERRO] DATASET_LGPD não encontrado ou vazio", flush=True)
            return {'status': Status.FAIL, 'mensagem': 'DATASET_LGPD não encontrado ou vazio'}
        detector = detector_instance
        total = len(DATASET_LGPD)
        acertos = 0
        erros = 0
        t0_bench = time.time()
        print(f"[PROFILING] Iniciando benchmark com {total} exemplos...", flush=True)
        for idx, (texto, contem_pii, descricao, categoria) in enumerate(DATASET_LGPD):
            t0_ex = time.time()
            try:
                resultado, findings, risco, confianca = detector.detect(texto)
                if resultado == contem_pii:
                    acertos += 1
                else:
                    erros += 1
            except Exception as ex:
                print(f"[PROFILING][ERRO] Exceção no exemplo {idx}: {ex}", flush=True)
                erros += 1
            if idx == 0 or (idx+1) % 2 == 0:
                print(f"[PROFILING] Exemplo {idx+1}/{total} processado em {time.time() - t0_ex:.2f}s", flush=True)
        tempo_ms = (time.time() - t0_bench) * 1000
        acc = acertos / total if total else 0
        status = Status.OK if acc > 0.95 else (Status.WARN if acc > 0.85 else Status.FAIL)
        print(f"[PROFILING] Benchmark finalizado em {tempo_ms/1000:.2f}s", flush=True)
        print(f"[PROFILING] Tempo total teste_fluxo_completo: {time.time() - t0_total:.2f}s", flush=True)
        return {
            'status': status,
            'mensagem': f'Benchmark: {acertos}/{total} acertos ({acc*100:.1f}%), tempo total {tempo_ms:.1f}ms',
            'detalhes': {
                'acertos': acertos,
                'erros': erros,
                'total': total,
                'acc': acc,
                'tempo_ms': tempo_ms
            },
            'tempo_ms': tempo_ms
        }

    def _imprimir_resumo(self):
        print("\n" + "=" * 70, flush=True)
        print("📊 RESUMO DO DIAGNÓSTICO", flush=True)
        print("=" * 70, flush=True)
        total = self.report.total_ok + self.report.total_fail + self.report.total_warn
        print(f"""
┌─────────────────────────────────────────────────────────────┐
│                    RESULTADO GERAL                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Total de testes:    {total:<4}                                 │
│                                                             │
│  ✅ OK:              {self.report.total_ok:<4}                                 │
│  ⚠️ Avisos:          {self.report.total_warn:<4}                                 │
│  ❌ Falhas:          {self.report.total_fail:<4}                                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STATUS GERAL:       {'🟢 OPERACIONAL' if self.report.total_fail == 0 else '🔴 COM PROBLEMAS':<20}            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
""", flush=True)
        if self.report.total_fail > 0:
            print("\n⚠️  AÇÕES NECESSÁRIAS:", flush=True)
            for result in (self.report.componentes + self.report.integracoes + self.report.fluxo_completo + self.report.performance):
                if result.status == Status.FAIL:
                    print(f"   ❌ {result.nome}: {result.mensagem}", flush=True)
                    if result.excecao and self.verbose:
                        print(f"      Exceção: {result.excecao[:200]}...", flush=True)
        if self.report.total_warn > 0:
            print("\n📝 AVISOS (não críticos):", flush=True)
            for result in (self.report.componentes + self.report.integracoes + self.report.fluxo_completo + self.report.performance):
                if result.status == Status.WARN:
                    print(f"   ⚠️ {result.nome}: {result.mensagem}", flush=True)
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.report = DiagnosticoReport()

    def log(self, msg: str):
        if self.verbose:
            print(f"  [DEBUG] {msg}")

    def teste_importacoes_basicas(self) -> Dict:
        modulos_obrigatorios = [
            ('re', 'Regex padrão Python'),
            ('json', 'JSON padrão Python'),
            ('typing', 'Type hints'),
            ('dataclasses', 'Dataclasses'),
            ('collections', 'Collections'),
        ]
        modulos_externos = [
            ('spacy', 'spaCy NLP'),
            ('presidio_analyzer', 'Presidio Analyzer'),
            ('transformers', 'HuggingFace Transformers'),
            ('torch', 'PyTorch'),
            ('numpy', 'NumPy'),
            ('tqdm', 'Progress bars'),
        ]
        falhas = []
        avisos = []
        for mod, desc in modulos_obrigatorios:
            try:
                importlib.import_module(mod)
                self.log(f"✓ {mod} importado")
            except ImportError as e:
                falhas.append(f"{mod} ({desc}): {e}")
        for mod, desc in modulos_externos:
            try:
                importlib.import_module(mod)
                self.log(f"✓ {mod} importado")
            except ImportError as e:
                avisos.append(f"{mod} ({desc}): {e}")
        if falhas:
            return {
                'status': Status.FAIL,
                'mensagem': f'Falha ao importar: {falhas}',
                'detalhes': {'falhas': falhas, 'avisos': avisos}
            }
        if avisos:
            return {
                'status': Status.WARN,
                'mensagem': f'Avisos ao importar: {avisos}',
                'detalhes': {'avisos': avisos}
            }
        return {
            'status': Status.OK,
            'mensagem': 'Todos os módulos importados com sucesso',
            'detalhes': None
        }

    def teste_estrutura_projeto(self) -> Dict:
        estrutura_esperada = {
            'src/': 'Diretório principal',
            'src/detector.py': 'Detector principal',
            'src/analyzers/': 'Analisadores',
            'src/analyzers/regex_analyzer.py': 'Analisador Regex',
            'src/analyzers/presidio_analyzer.py': 'Analisador Presidio',
            'src/analyzers/ner_analyzer.py': 'Analisador NER',
            'src/confidence/': 'Módulo de confiança',
            'src/confidence/calculators.py': 'Calculadores de confiança',
            'src/confidence/combiners.py': 'Combinadores de resultado',
            'src/ensemble/': 'Módulo ensemble',
            'src/ensemble/arbitro.py': 'Árbitro de decisão',
            'src/patterns/': 'Padrões regex',
            'src/patterns/gdf_patterns.py': 'Padrões específicos GDF',
            'data/': 'Diretório de dados',
            'tests/': 'Diretório de testes',
        }
        faltando = []
        encontrados = []
        # Sempre verifica a partir do root do projeto (backend/)
        for path, desc in estrutura_esperada.items():
            abs_path = os.path.join(PROJ_ROOT, path)
            if path.endswith('/'):
                existe = os.path.isdir(abs_path)
            else:
                existe = os.path.isfile(abs_path)
            if existe:
                encontrados.append(path)
                self.log(f"✓ {path}")
            else:
                faltando.append(f"{path} ({desc})")
                self.log(f"✗ {path}")
        if faltando:
            return {
                'status': Status.WARN if len(faltando) < 5 else Status.FAIL,
                'mensagem': f"{len(faltando)} arquivos/diretórios faltando",
                'detalhes': {'faltando': faltando, 'encontrados': encontrados}
            }
        return {
            'status': Status.OK,
            'mensagem': f'Estrutura completa ({len(encontrados)} itens)',
            'detalhes': {'encontrados': encontrados}
        }

    def teste_integracao_api(self) -> dict:
        """Testa a integração real com a API local (FastAPI), priorizando porta 7860 se disponível."""
        import requests
        import socket
        # Detecta ambiente Docker automaticamente
        def em_docker():
            if os.environ.get("DOCKER") == "1":
                return True
            if os.path.exists("/.dockerenv"):
                return True
            hn = socket.gethostname()
            if len(hn) >= 12 and all(c in '0123456789abcdef' for c in hn[:12].lower()):
                return True
            return False

        # Ordem de prioridade: API_PORT > 7860 > 8000
        porta_env = os.environ.get("API_PORT")
        portas = []
        if porta_env:
            try:
                portas.append(int(porta_env))
            except Exception:
                pass
        portas += [7860, 8000]
        tried = []
        for porta in portas:
            url = f"http://localhost:{porta}/health"
            t0 = time.time()
            try:
                resp = requests.get(url, timeout=5)
                tempo_ms = (time.time() - t0) * 1000
                status_valido = resp.json().get("status") in ("ok", "healthy")
                if resp.status_code == 200 and status_valido:
                    return {
                        'status': Status.OK,
                        'mensagem': f'API respondeu corretamente em {tempo_ms:.1f}ms (porta {porta})',
                        'detalhes': {'status_code': resp.status_code, 'body': resp.json(), 'porta': porta},
                        'tempo_ms': tempo_ms
                    }
                else:
                    tried.append((porta, f"Resposta inesperada: {resp.status_code} {resp.text}"))
            except requests.ConnectionError as e:
                tried.append((porta, f"ConnectionError: {e}"))
            except Exception as e:
                tried.append((porta, f"Erro: {e}"))
        return {
            'status': Status.FAIL,
            'mensagem': f'API não respondeu nas portas testadas: {tried}',
            'detalhes': {'tentativas': tried}
        }


    def testar_componente(self, nome: str, func) -> TestResult:
        start = time.time()
        try:
            resultado = func()
            tempo_ms = (time.time() - start) * 1000
            return TestResult(
                nome=nome,
                status=resultado.get('status', Status.OK),
                mensagem=resultado.get('mensagem', 'OK'),
                tempo_ms=tempo_ms,
                detalhes=resultado.get('detalhes')
            )
        except Exception as e:
            tempo_ms = (time.time() - start) * 1000
            return TestResult(
                nome=nome,
                status=Status.FAIL,
                mensagem=str(e),
                tempo_ms=tempo_ms,
                excecao=traceback.format_exc()
            )

    def executar(self) -> DiagnosticoReport:
        print("\n" + "=" * 70, flush=True)
        print("🔍 DIAGNÓSTICO COMPLETO DO MOTOR PII", flush=True)
        print("=" * 70, flush=True)
        print("\n📦 1. VERIFICANDO COMPONENTES INDIVIDUAIS...", flush=True)
        print("-" * 50, flush=True)
        testes_componentes = [
            ("Importações Básicas", self.teste_importacoes_basicas),
            ("Estrutura do Projeto", self.teste_estrutura_projeto),
        ]
        for nome, func in testes_componentes:
            result = self.testar_componente(nome, func)
            self.report.componentes.append(result)
            print(f"  {result.status.value} {nome}: {result.mensagem} ({result.tempo_ms:.1f}ms)", flush=True)

        print("\n🔗 2. VERIFICANDO INTEGRAÇÕES...", flush=True)
        print("-" * 50, flush=True)
        testes_integracoes = [
            ("Integração API", self.teste_integracao_api),
        ]
        for nome, func in testes_integracoes:
            result = self.testar_componente(nome, func)
            self.report.integracoes.append(result)
            print(f"  {result.status.value} {nome}: {result.mensagem} ({result.tempo_ms:.1f}ms)", flush=True)

        print("\n🔄 3. VERIFICANDO FLUXO COMPLETO...", flush=True)
        print("-" * 50, flush=True)
        testes_fluxo = [
            ("Fluxo Completo Benchmark", self.teste_fluxo_completo),
        ]
        for nome, func in testes_fluxo:
            result = self.testar_componente(nome, func)
            self.report.fluxo_completo.append(result)
            print(f"  {result.status.value} {nome}: {result.mensagem} ({result.tempo_ms:.1f}ms)", flush=True)

        print("\n⚡ 4. VERIFICANDO PERFORMANCE...", flush=True)
        print("-" * 50, flush=True)
        # Pode adicionar testes de performance reais aqui no futuro
        self._imprimir_resumo()
        return self.report
    

# Bloco main para execução direta
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Diagnóstico do Motor PII")
    parser.add_argument('--verbose', action='store_true', help='Exibe logs detalhados')
    args = parser.parse_args()
    diag = DiagnosticoMotor(verbose=args.verbose)
    report = diag.executar()
    # Exit code baseado no resultado
    import sys
    sys.exit(0 if report.total_fail == 0 else 1)

if __name__ == "__main__":
    main()