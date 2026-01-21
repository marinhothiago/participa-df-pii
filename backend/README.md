---
title: Participa DF - Detector Inteligente de Dados Pessoais
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
app_file: api/main.py
pinned: false
---

# 🛡️ Backend: Motor PII Participa DF v9.6.0

[![Python](https://img.shields.io/badge/Python-3.10+-yellow?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![spaCy](https://img.shields.io/badge/spaCy-3.8.0-09A3D5?logo=spacy)](https://spacy.io/)
[![Presidio](https://img.shields.io/badge/Presidio-2.2+-purple?logo=microsoft)](https://microsoft.github.io/presidio/)
[![F1--Score](https://img.shields.io/badge/F1--Score-1.0000-success)](./tests/test_benchmark.py)
[![Testes](https://img.shields.io/badge/Testes-438%20passando-brightgreen)](./tests/)

> **Motor híbrido de detecção de Informações Pessoais Identificáveis (PII)** para conformidade LGPD/LAI em manifestações do Participa DF.
> 
> 🏆 **v9.6.0 - F1-Score = 1.0000** (100% precisão, 100% recall) em auditoria LGPD completa (153 PIIs mapeados).

| 🌐 **Links de Produção** | URL |
|--------------------------|-----|
| API Base | https://marinhothiago-desafio-participa-df.hf.space/ |
| Documentação Swagger | https://marinhothiago-desafio-participa-df.hf.space/docs |
| Health Check | https://marinhothiago-desafio-participa-df.hf.space/health |

---

## 📋 Índice

1. [Funcionalidades](#-funcionalidades-v960)
2. [Instalação](#1️⃣-instalação)
3. [Execução](#2️⃣-execução)
4. [API - Endpoints](#3️⃣-api---endpoints)
5. [Arquitetura do Motor](#4️⃣-arquitetura-do-motor)
6. [Sistema de Confiança](#5️⃣-sistema-de-confiança)
7. [Explicabilidade (XAI)](#6️⃣-explicabilidade-xai)
8. [Árbitro LLM](#7️⃣-árbitro-llm)
9. [Testes e Benchmark](#8️⃣-testes-e-benchmark)
10. [Estrutura de Arquivos](#9️⃣-estrutura-de-arquivos)
11. [Deploy](#-deploy)
12. [Troubleshooting](#️-troubleshooting)

---

## 🚀 Funcionalidades v9.6.0

### Novidades da Versão Atual

| Feature | Descrição |
|---------|-----------|
| 🤖 **Árbitro LLM** | Llama-3.2-3B-Instruct ativado automaticamente em casos ambíguos |
| 🔍 **Explicabilidade (XAI)** | Cada detecção inclui justificativa detalhada (motivos, fontes, validações) |
| 🏛️ **Presidio Customizado** | 10 PatternRecognizers para padrões GDF (PROCESSO_SEI, MATRICULA_GDF, etc.) |
| ✅ **Validação DV Completa** | CPF, CNPJ, PIS, CNS com algoritmo oficial (mod 11) |
| 📍 **Contexto Avançado** | Distingue endereço em fiscalização vs residência pessoal |
| 📊 **Auditoria LGPD** | 153 PIIs mapeados, 303 casos de teste, F1=100% |

### Detectores Integrados (Ensemble de 5 Fontes)

| Detector | Função | Tecnologia |
|----------|--------|------------|
| **Regex + DV** | Documentos (CPF, CNPJ, RG, CNH, PIS, etc.) | Expressões regulares + validação matemática |
| **BERT NER** | Nomes e entidades | Davlan/bert-base-multilingual-cased-ner-hrl |
| **NuNER** | Nomes em português | NuNER pt-BR especializado |
| **spaCy** | Complementar para nomes | pt_core_news_lg |
| **Presidio** | Framework unificado | Microsoft Presidio Analyzer |
| **Gatilhos** | "falar com", "ligar para" | Regras linguísticas |
| **Gazetteer GDF** | Filtro de FP institucionais | Lista de órgãos, escolas, hospitais |

---

## 1️⃣ Instalação

### Pré-requisitos

| Software | Versão | Verificar |
|----------|--------|-----------|
| Python | 3.10+ | `python --version` |
| pip | 23.0+ | `pip --version` |
| Git | 2.0+ | `git --version` |

**Requisitos de Sistema:** RAM 4GB+ (recomendado 8GB), Disco ~3GB para modelos NLP

### Instalação Passo a Passo

```bash
# 1. Entre na pasta backend
cd desafio-participa-df/backend

# 2. Crie ambiente virtual
python -m venv venv

# 3. Ative o ambiente
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instale PyTorch CPU (antes das outras dependências)
pip install torch==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu

# 5. Instale todas as dependências
pip install -r requirements.txt

# 6. Baixe o modelo spaCy (OBRIGATÓRIO)
python -m spacy download pt_core_news_lg

# 7. (Opcional) Configure o token Hugging Face para o árbitro LLM
echo "HF_TOKEN=seu_token_aqui" > .env
```

### Verificar Instalação

```bash
python -c "import spacy; nlp = spacy.load('pt_core_news_lg'); print('✅ spaCy OK')"
python -c "from transformers import pipeline; print('✅ Transformers OK')"
python -c "from presidio_analyzer import AnalyzerEngine; print('✅ Presidio OK')"
```

---

## 2️⃣ Execução

### Servidor API (FastAPI)

```bash
cd backend
# Ativar venv (se necessário)
# Windows: venv\Scripts\activate
# Linux: source venv/bin/activate

# Iniciar servidor
uvicorn api.main:app --host 0.0.0.0 --port 7860 --reload
```

**Saída esperada:**
```
INFO:     🏆 [v9.6.0] ENSEMBLE 5 FONTES + CONFIANÇA PROBABILÍSTICA + LLM ÁRBITRO
INFO:     ✅ spaCy pt_core_news_lg carregado
INFO:     ✅ BERT Davlan NER multilíngue carregado
INFO:     Uvicorn running on http://0.0.0.0:7860
```

**Endpoints disponíveis:**
- API: http://localhost:7860
- Swagger: http://localhost:7860/docs
- Health: http://localhost:7860/health

### CLI (Processamento em Lote)

```bash
python scripts/main_cli.py --input data/input/manifestacoes.xlsx --output data/output/resultado
```

**Saídas geradas:** `resultado.json`, `resultado.csv`, `resultado.xlsx` (com cores por risco)

### Docker

```bash
docker build -t participa-df-backend .
docker run -p 7860:7860 participa-df-backend
```

---

## 3️⃣ API - Endpoints

### Visão Geral

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/analyze` | POST | Analisa texto para detecção de PII |
| `/health` | GET | Status da API |
| `/stats` | GET | Estatísticas globais de uso |
| `/stats/visit` | POST | Registra visita ao site |
| `/feedback` | POST | Submete feedback humano |
| `/feedback/stats` | GET | Estatísticas de feedback |
| `/docs` | GET | Documentação Swagger |

### POST /analyze

**Entrada:**
```json
{
  "text": "Meu CPF é 123.456.789-09 e preciso de ajuda.",
  "id": "manifestacao_001"
}
```

**Saída (formato v2 com XAI):**
```json
{
  "id": "manifestacao_001",
  "has_pii": true,
  "classificacao": "NÃO PÚBLICO",
  "risco": "CRÍTICO",
  "confianca": 0.98,
  "entities": [
    {
      "tipo": "CPF",
      "valor": "123.456.789-09",
      "confianca": 1.0,
      "fonte": "regex",
      "explicacao": {
        "motivos": ["✓ Formato XXX.XXX.XXX-XX identificado"],
        "fontes": ["Regex (padrão)"],
        "validacoes": ["✓ Dígito verificador válido (mod 11)"],
        "contexto": ["✓ Contexto pessoal: 'cpf' encontrado"],
        "confianca_percent": "100.0%",
        "peso": 5
      }
    }
  ],
  "risk_level": "CRÍTICO",
  "confidence_all_found": 0.98,
  "total_entities": 1,
  "sources_used": ["regex", "bert_ner"]
}
```

### Parâmetros Opcionais

| Parâmetro | Valores | Descrição |
|-----------|---------|-----------|
| `merge_preset` | recall, precision, f1, custom | Estratégia de merge de spans sobrepostos |
| `use_llm` | true, false | Forçar uso do árbitro LLM |

**Exemplo com curl:**
```bash
curl -X POST "http://localhost:7860/analyze?merge_preset=recall" \
  -H "Content-Type: application/json" \
  -d '{"text": "Meu CPF é 123.456.789-09"}'
```

---

## 4️⃣ Arquitetura do Motor

### Pipeline de Detecção (Ensemble OR)

```
Texto de Entrada
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  CAMADA 1: REGEX + VALIDAÇÃO DV                              │
│  CPF, CNPJ, RG, CNH, PIS, CNS, Email, Telefone, etc.        │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  CAMADA 2: NER (BERT + NuNER + spaCy)                       │
│  Nomes pessoais com threshold de confiança                   │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  CAMADA 3: PRESIDIO (Recognizers Customizados GDF)          │
│  PROCESSO_SEI, MATRICULA_GDF, OAB, TELEFONE_BR, etc.        │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  CAMADA 4: REGRAS DE NEGÓCIO                                │
│  Gatilhos de contato, Imunidade funcional, Gazetteer GDF    │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  CAMADA 5: ÁRBITRO LLM (se ambíguo)                         │
│  Llama-3.2-3B-Instruct via Hugging Face                     │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  ENSEMBLE + DEDUPLICAÇÃO + EXPLICAÇÃO (XAI)                 │
│  Combina achados, remove duplicatas, gera justificativas    │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
   Resultado Final (has_pii, entities, risk_level, explicacao)
```

### Tipos de PII Detectados (30+)

| Categoria | Tipos | Peso LGPD |
|-----------|-------|-----------|
| **Documentos** | CPF, CNPJ, RG, CNH, PIS, CNS, Passaporte, Título Eleitor, CTPS | 5 (Crítico) |
| **Contato** | Email pessoal, Telefone, Celular, WhatsApp | 4 (Alto) |
| **Localização** | Endereço, CEP, Coordenadas GPS | 4 (Alto) |
| **Financeiro** | Conta bancária, PIX, Cartão de crédito | 4 (Alto) |
| **Identificação** | Nome completo, Data nascimento | 3-4 |
| **Veículos** | Placa (Mercosul e antiga) | 3 (Moderado) |
| **Governo GDF** | Processo SEI, Matrícula servidor, Inscrição imóvel | 3 (Moderado) |
| **Saúde** | CID, Dados biométricos | 5 (Crítico) |
| **Digital** | IP Address, User-Agent | 2 (Baixo) |

### Imunidade Funcional (LAI)

Servidores públicos em exercício de função **NÃO são PII**:
- ✅ "A Dra. Maria da Secretaria de Saúde informou que..."
- ✅ "O servidor José Santos do DETRAN atendeu a demanda"

**Gatilhos que ANULAM imunidade:**
- ❌ "Preciso falar com o João Silva sobre isso"
- ❌ "Ligar para a Dra. Maria no celular"

---

## 5️⃣ Sistema de Confiança

### Cálculo de Confiança Composta

```
confiança_final = min(1.0, confiança_base × fator_contexto)
```

### Confiança Base por Método

| Método | Tipos | Base | Justificativa |
|--------|-------|------|---------------|
| Regex + DV | CPF, PIS, CNS, CNH | 0.98 | Validação matemática (mod 11) |
| Regex + Luhn | Cartão Crédito | 0.95 | Algoritmo Luhn válido |
| Regex estrutural | Email, Telefone, Placa | 0.85-0.95 | Padrão claro |
| BERT NER | Nomes | score do modelo | 0.75-0.99 |
| spaCy NER | Nomes | 0.70 | Complementar |
| Gatilho | Nomes após "falar com" | 0.85 | Padrão linguístico |

### Fatores de Contexto (Boost/Penalidade)

| Fator | Ajuste | Exemplo |
|-------|--------|---------|
| Possessivo ("meu", "minha") | +15% | "**Meu** CPF é..." |
| Label explícito | +10% | "**CPF:** 529..." |
| Gatilho de contato | +10% | "**falar com** João" |
| Contexto de teste | -25% | "**exemplo**: 000..." |
| Declarado fictício | -30% | "CPF **fictício**" |
| Negação | -20% | "**não é** meu CPF" |

### Calibração Isotônica

O sistema utiliza `IsotonicCalibrator` (sklearn) para mapear scores de modelos NER para probabilidades reais, treinado com dados de feedback humano.

---

## 6️⃣ Explicabilidade (XAI)

Cada entidade detectada inclui campo `explicacao` com justificativa completa:

```json
{
  "explicacao": {
    "motivos": [
      "✓ Formato XXX.XXX.XXX-XX identificado",
      "✓ Documento com validação de integridade"
    ],
    "fontes": ["Regex (padrão)", "Validador DV"],
    "validacoes": ["✓ Dígito verificador válido (mod 11)"],
    "contexto": ["✓ Contexto pessoal: 'meu cpf' encontrado"],
    "confianca_percent": "100.0%",
    "peso": 5
  }
}
```

### Campos da Explicação

| Campo | Descrição |
|-------|-----------|
| `motivos` | Razões pelas quais foi detectado |
| `fontes` | Motores que detectaram (Regex, BERT, spaCy, Presidio, etc.) |
| `validacoes` | Checagens adicionais (DV válido, formato correto) |
| `contexto` | Palavras-chave encontradas no texto próximo |
| `confianca_percent` | Confiança em formato percentual |
| `peso` | Criticidade LGPD (1-5) |

### Benefícios para Hackathon

- 📊 **Auditoria:** Avaliadores podem entender exatamente por que cada PII foi detectado
- 🎯 **Transparência:** Decisões explicáveis aumentam confiança no sistema
- 🔧 **Debug:** Facilita identificar falsos positivos/negativos

---

## 7️⃣ Árbitro LLM

### Quando é Acionado

O Llama-3.2-3B-Instruct é chamado automaticamente em:

1. **Itens com baixa confiança** - PII detectado mas confiança abaixo do threshold
2. **Zero PIIs encontrados** - Análise final do texto como "última chance"

### Fluxo de Decisão

```
Ensemble Executa → Votação + Threshold
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         PIIs OK              Baixa confiança
                              ou Zero PIIs
                                    │
                                    ▼
                           LLAMA-3.2 ÁRBITRO
                           (Análise LGPD/LAI)
                                    │
                              ┌─────┴─────┐
                              ▼           ▼
                            PII        NÃO PII
```

### Configuração

```bash
# .env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx    # OBRIGATÓRIO para LLM
HF_MODEL=meta-llama/Llama-3.2-3B-Instruct  # Opcional (padrão)
PII_USE_LLM_ARBITRATION=False        # Auto em ambiguidades (padrão)
```

### Fail-Safe

Se o LLM não responder (timeout, erro de API):
- Itens pendentes são **INCLUÍDOS** no resultado (evita falso negativo)
- Warning é emitido para monitoramento
- Sistema continua funcionando sem interrupção

---

## 8️⃣ Testes e Benchmark

### Executar Testes

```bash
cd backend

# Todos os testes
pytest --disable-warnings -q

# Benchmark LGPD (303 casos)
pytest tests/test_benchmark.py -v

# Testes de confiança
pytest tests/test_confianca.py -v

# Testes de XAI
pytest tests/test_explicabilidade.py -v
```

### Métricas do Benchmark LGPD

| Métrica | Valor | Descrição |
|---------|-------|-----------|
| **Precisão** | 100% | Sem falsos positivos |
| **Recall** | 100% | Sem falsos negativos |
| **F1-Score** | 1.0000 | Média harmônica perfeita |
| **Verdadeiros Positivos** | 164 | PIIs detectados corretamente |
| **Verdadeiros Negativos** | 139 | Textos públicos classificados corretamente |
| **Total de Casos** | 303 | Benchmark completo |

### Grupos de Teste

| Grupo | Quantidade | Esperado |
|-------|------------|----------|
| Administrativo | 50+ | PÚBLICO |
| PII Clássico (CPF, Email, Tel) | 80+ | NÃO PÚBLICO |
| Nomes com contexto | 40+ | Variado |
| Edge Cases Brasília/GDF | 50+ | Variado |
| Imunidade funcional | 30+ | PÚBLICO |
| Gatilhos de contato | 25+ | NÃO PÚBLICO |
| Documentos com validação DV | 25+ | NÃO PÚBLICO |

---

## 9️⃣ Estrutura de Arquivos

```
backend/
├── README.md                 ← ESTE ARQUIVO
├── requirements.txt          ← Dependências Python
├── Dockerfile                ← Container para HuggingFace Spaces
├── docker-compose.yml        ← Orquestração local
│
├── api/
│   ├── __init__.py
│   ├── main.py               ← FastAPI: /analyze, /health, /stats, /feedback
│   ├── celery_config.py      ← Configuração Celery + Redis
│   └── tasks.py              ← Tasks assíncronas para lotes
│
├── src/
│   ├── __init__.py
│   ├── detector.py           ← Motor híbrido PII v9.6.0 (2200+ linhas)
│   │                           - PIIDetector: ensemble de detectores
│   │                           - ValidadorDocumentos: validação DV
│   │                           - 30+ tipos de PII, XAI integrado
│   │
│   ├── allow_list.py         ← Lista de termos seguros (375+ termos)
│   │
│   ├── analyzers/            ← Analisadores específicos
│   │   ├── ner_analyzer.py   ← BERT + NuNER + spaCy
│   │   └── presidio_analyzer.py ← Recognizers customizados GDF
│   │
│   ├── confidence/           ← Sistema de confiança probabilística
│   │   ├── types.py          ← PIIEntity, DocumentConfidence
│   │   ├── config.py         ← FN/FP rates, pesos LGPD, thresholds
│   │   ├── validators.py     ← Validação DV (CPF, CNPJ, PIS, CNS)
│   │   ├── calibration.py    ← IsotonicCalibrator
│   │   ├── combiners.py      ← ProbabilityCombiner, merge de spans
│   │   └── calculator.py     ← PIIConfidenceCalculator
│   │
│   ├── gazetteer/            ← Gazetteer institucional GDF
│   │   └── gazetteer_gdf.json ← Órgãos, escolas, hospitais do DF
│   │
│   └── patterns/             ← Padrões regex específicos GDF
│       └── gdf_patterns.py   ← PROCESSO_SEI, MATRICULA_GDF, etc.
│
├── scripts/
│   ├── main_cli.py           ← CLI para processamento em lote
│   ├── optimize_ensemble.py  ← Grid search de pesos
│   └── feedback_to_dataset.py ← Converte feedbacks em dataset
│
├── tests/                    ← Testes automatizados (pytest)
│   ├── conftest.py           ← Fixtures compartilhadas
│   ├── test_benchmark.py     ← Benchmark LGPD: 303 casos, F1=1.0000
│   ├── test_amostra.py       ← Testes com amostra e-SIC
│   ├── test_confianca.py     ← Testes do sistema de confiança
│   ├── test_edge_cases.py    ← Casos extremos
│   ├── test_explicabilidade.py ← Testes de XAI
│   ├── test_integracao.py    ← Testes de integração
│   └── test_regex_gdf_*.py   ← Testes de padrões GDF
│
├── data/
│   ├── input/                ← Arquivos para processar em lote
│   ├── output/               ← Relatórios gerados
│   ├── feedback.json         ← Feedbacks humanos acumulados
│   └── stats.json            ← Estatísticas de uso
│
└── models/
    └── bert_ner_onnx/        ← Modelo BERT exportado para ONNX (opcional)
```

---

## 🐳 Deploy

### HuggingFace Spaces (Produção)

```bash
# Da raiz do projeto
./deploy-hf.sh
```

### Docker Local

```bash
docker build -t participa-df-backend .
docker run -p 7860:7860 -e HF_TOKEN=seu_token participa-df-backend
```

### Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `HF_TOKEN` | Para LLM | Token Hugging Face |
| `HF_MODEL` | Não | Modelo LLM (padrão: Llama-3.2-3B) |
| `PII_USE_LLM_ARBITRATION` | Não | Forçar LLM em todas análises |

---

## 🛠️ Troubleshooting

### Erros Comuns

| Erro | Solução |
|------|---------|
| `spacy: Model not found` | Execute `python -m spacy download pt_core_news_lg` |
| `ImportError: optimum.onnxruntime` | Execute `pip install optimum[onnx] onnxruntime` |
| `Presidio Recognizers not found` | Verifique se `_compilar_patterns` foi chamado no construtor |
| `HF_TOKEN invalid` | Crie token em https://huggingface.co/settings/tokens |
| `Timeout na API` | Backend em cold start, aguarde 30-60 segundos |

### Logs de Debug

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Links Úteis

- [Presidio Docs](https://microsoft.github.io/presidio/analyzer/)
- [Optimum ONNX Export](https://huggingface.co/docs/optimum/exporters/onnx/usage_guides/export_a_model)
- [Llama Hugging Face](https://huggingface.co/meta-llama)

---

## 🔄 Feedback Loop (Aprendizado Contínuo)

O sistema implementa coleta de feedbacks humanos para melhoria contínua:

### Endpoints de Feedback

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/feedback` | POST | Submete validação humana |
| `/feedback/stats` | GET | Estatísticas acumuladas |
| `/feedback/generate-dataset` | POST | Gera dataset para treinamento |

### Fluxo de Melhoria

```
1. COLETA: Frontend coleta validação (CORRETO/INCORRETO/PARCIAL)
2. ARMAZENAMENTO: Salvo em backend/data/feedback.json
3. GERAÇÃO: Converte feedbacks em dataset JSONL/CSV
4. RECALIBRAÇÃO: IsotonicCalibrator treina com dados históricos
5. MELHORIA: Próximas detecções mais precisas
```

---

## 📄 Licença

Desenvolvido para o **Hackathon Participa DF 2026** em conformidade com:
- **LGPD** - Lei Geral de Proteção de Dados (Lei nº 13.709/2018)
- **LAI** - Lei de Acesso à Informação (Lei nº 12.527/2011)

---

## 🔗 Relacionado

- **Frontend (Interface):** [../frontend/README.md](../frontend/README.md)
- **Projeto Completo:** [../README.md](../README.md)
