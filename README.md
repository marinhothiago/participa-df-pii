# 🛡️ Participa DF - Detector Inteligente de Dados Pessoais

> **Motor de IA para Detecção de Informações Pessoais em Textos Públicos**  
> Hackathon Participa DF 2026 CGDF | F1-Score: 1.0000 | 452 Testes | 156 PIIs detectados

[![Status](https://img.shields.io/badge/Status-Produção-brightgreen)](https://marinhothiago.github.io/desafio-participa-df/)
[![Versão](https://img.shields.io/badge/Versão-9.6.0-blue)](./backend/README.md)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow?logo=python)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?logo=node.js)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)](https://www.docker.com/)
[![Licença](https://img.shields.io/badge/Licença-LGPD%2FLAI-green)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![F1--Score](https://img.shields.io/badge/F1--Score-1.0000-success)](./backend/benchmark.py)
[![CI](https://github.com/marinhothiago/desafio-participa-df/actions/workflows/ci.yml/badge.svg)](https://github.com/marinhothiago/desafio-participa-df/actions/workflows/ci.yml)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Code Style: Prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg)](https://prettier.io/)
[![GitHub last commit](https://img.shields.io/github/last-commit/marinhothiago/desafio-participa-df)](https://github.com/marinhothiago/desafio-participa-df/commits/main)
[![Frontend](https://img.shields.io/badge/Demo-GitHub%20Pages-blue)](https://marinhothiago.github.io/desafio-participa-df/)
[![API](https://img.shields.io/badge/API-HuggingFace-yellow)](https://marinhothiago-desafio-participa-df.hf.space/docs)

---

## 🔗 Links do Projeto Publicado

| Recurso | URL |
|---------|-----|
| **Frontend (Demo)** | https://marinhothiago.github.io/desafio-participa-df/ |
| **Backend (API)** | https://marinhothiago-desafio-participa-df.hf.space/ |
| **Documentação API** | https://marinhothiago-desafio-participa-df.hf.space/docs |
| **Repositório** | https://github.com/marinhothiago/desafio-participa-df |

---

## 📋 Sumário Rápido (Critérios do Edital)

| Critério | Seção |
|----------|-------|
| 1a) Pré-requisitos com versões | [1. Pré-requisitos](#1-pré-requisitos) |
| 1b) Arquivo de dependências | [2. Dependências](#2-dependências) |
| 1c) Comandos de instalação | [3. Instalação](#3-instalação-via-docker-recomendado) |
| 2a) Comandos de execução | [4. Execução](#4-execução) |
| 2b) Formato entrada/saída | [5. Formato de Entrada/Saída](#5-formato-de-entradasaída) |
| 3a) Objetivo e arquivos | [6. Descrição da Solução](#6-descrição-da-solução) |
| 3b) Comentários no código | [7. Comentários no Código](#7-comentários-no-código) |
| 3c) Estrutura lógica | [8. Estrutura de Arquivos](#8-estrutura-de-arquivos) |

---

## 1. Pré-requisitos

| Ferramenta | Versão Mínima | Verificar Instalação |
|------------|---------------|----------------------|
| **Docker** | 24.0+ | `docker --version` |
| **Docker Compose** | 2.20+ | `docker compose version` |
| Git | 2.40+ | `git --version` |

> **⚡ Para avaliadores:** Apenas Docker é necessário para rodar o projeto completo.

<details>
<summary>📌 Pré-requisitos para desenvolvimento local (opcional)</summary>

| Ferramenta | Versão | Verificar |
|------------|--------|-----------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

</details>

---

## 2. Dependências

Os arquivos de gerenciamento de pacotes estão em:

| Componente | Arquivo | Descrição |
|------------|---------|-----------|
| **Backend** | [backend/requirements.txt](backend/requirements.txt) | Dependências Python (FastAPI, spaCy, Transformers, etc.) |
| **Frontend** | [frontend/package.json](frontend/package.json) | Dependências Node.js (React, TypeScript, Vite, etc.) |
| **Docker** | [docker-compose.yml](docker-compose.yml) | Orquestração dos containers |

---

## 3. Instalação via Docker (Recomendado)

### Passo a passo

```bash
# 1. Clonar o repositório
git clone https://github.com/marinhothiago/desafio-participa-df.git
cd desafio-participa-df

# 2. Subir os containers (backend + frontend)
docker compose up --build
```

Aguarde o download das imagens (~2-5 minutos na primeira vez).

### Verificar se está funcionando

| Serviço | URL | Status |
|---------|-----|--------|
| **Frontend** | http://localhost:80 | Interface web |
| **Backend API** | http://localhost:7860 | API REST |
| **Documentação** | http://localhost:7860/docs | Swagger UI |

---

## 4. Execução

### 4.1 Via Docker (Recomendado)

```bash
# Iniciar todos os serviços
docker compose up

# Parar os serviços
docker compose down
```

### 4.2 Testar a API

```bash
# Exemplo: detectar PII em texto
curl -X POST "http://localhost:7860/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "Meu CPF é 529.982.247-25 e meu email é joao@email.com"}'
```

### 4.3 Usar a Interface Web

1. Acesse http://localhost (porta 80) ou http://localhost:8080 (dev local)
2. Cole um texto ou faça upload de arquivo (CSV/XLSX)
3. Clique em "Analisar"
4. Visualize os PIIs detectados e exporte os resultados

### 4.4 Processar Arquivo em Lote (CLI)

```bash
# Entrar no container do backend
docker compose exec backend bash

# Processar arquivo XLSX
python scripts/main_cli.py \
  --input data/input/AMOSTRA_e-SIC.xlsx \
  --output data/output/resultado
```

<details>
<summary>📌 Execução local sem Docker (desenvolvimento)</summary>

### Backend (via Conda - Recomendado)

O projeto requer Python 3.10+ e ferramentas de compilação C++. Recomendamos o **Conda** para evitar conflitos (especialmente no Ubuntu 24.04+ e macOS).

```bash
# 1. Clonar e entrar no diretório
git clone https://github.com/marinhothiago/desafio-participa-df.git
cd desafio-participa-df/backend

# 2. Criar ambiente com Python 3.10 + ferramentas de build
conda create -n participa_env python=3.10 cmake pkg-config -c conda-forge -y

# 3. Ativar o ambiente
conda activate participa_env

# 4. Instalar dependências
pip install -r requirements.txt
python -m spacy download pt_core_news_lg

# 5. Iniciar servidor
python -m uvicorn api.main:app --host 0.0.0.0 --port 7860 --reload
```

> 💡 Se for a primeira vez usando Conda, rode `conda init` e reinicie o terminal.

<details>
<summary>Alternativa: venv (apenas Windows)</summary>

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download pt_core_news_lg
python -m uvicorn api.main:app --host 0.0.0.0 --port 7860 --reload
```

</details>

### Frontend

```bash
cd frontend
npm install
npm run dev
```

</details>

---

## 5. Formato de Entrada/Saída

### Entrada (POST /analyze)

```json
{
  "text": "Texto para análise de PII"
}
```

### Saída

```json
{
  "contem_pii": true,
  "nivel_risco": "CRÍTICO",
  "peso_risco": 5,
  "tipos_pii": ["CPF", "EMAIL"],
  "quantidade_pii": 2,
  "texto_anonimizado": "Meu CPF é [CPF_1] e meu email é [EMAIL_1]",
  "findings": [
    {
      "tipo": "CPF",
      "valor": "529.982.247-25",
      "inicio": 11,
      "fim": 25,
      "confidence": 0.9999,
      "contexto": "Meu CPF é ..."
    }
  ],
  "confianca": {
    "min_entity": 0.95,
    "all_found": 0.98,
    "no_pii": 0.001
  }
}
```

### Níveis de Risco

| Nível | Peso | Tipos de PII |
|-------|------|--------------|
| 🔴 CRÍTICO | 5 | CPF, RG, CNH, Passaporte, PIS, CNS, Dados Sensíveis LGPD |
| 🟠 ALTO | 4 | Email, Telefone, Endereço, Nome Pessoal |
| 🟡 MODERADO | 3 | Placa, Data de Nascimento, Processo CNJ |
| 🔵 BAIXO | 1-2 | IP, GPS, User-Agent, Identificadores Indiretos |
| 🟢 SEGURO | 0 | Nenhum PII detectado |

---

## 6. Descrição da Solução

## 📋 Objetivo da Solução

O **Participa DF - PII Detector** é um sistema completo para **detectar, classificar e avaliar o risco de vazamento de dados pessoais** em textos de pedidos de acesso a informação recebidos pelo GDF.

### Problema Resolvido

O GDF precisa analisar manifestações de cidadãos em transparência ativa (LAI) sem violar a privacidade garantida pela LGPD. Este sistema automatiza a detecção de:

- **CPF, RG, CNH, Passaporte, PIS, CNS, Título Eleitor, CTPS** (documentos de identificação)
- **Email, Telefone, Celular, Telefones Internacionais** (dados de contato)
- **Endereços residenciais, CEP, Endereços Brasília (SQS, SQN, etc)** (localização)
- **Nomes pessoais** (com análise de contexto via BERT + spaCy + NuNER)
- **Dados bancários, PIX, Cartão de Crédito, Conta Bancária** (informações financeiras)
- **Placas de veículos, Processos CNJ, Matrículas** (outros identificadores)
- **Dados de Saúde (CID), Dados Biométricos, Menores Identificados** (dados sensíveis LGPD)
- **IP Address, Coordenadas GPS, User-Agent** (identificação indireta - risco baixo)

### Resultado

Classificação automática como **"PÚBLICO"** (pode publicar) ou **"NÃO PÚBLICO"** (contém PII), com nível de risco (CRÍTICO, ALTO, MODERADO, BAIXO, SEGURO) e score de confiança normalizado (0-1).

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND (React + Vite)                    │
│              GitHub Pages / Docker (nginx)                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Dashboard com métricas em tempo real                 │ │
│  │ • Análise individual de textos                         │ │
│  │ • Processamento em lote (CSV/XLSX)                     │ │
│  │ • Design System DSGOV (Gov.br)                         │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP POST /analyze
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                 BACKEND (FastAPI + Python)                  │
│           HuggingFace Spaces / Docker                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Motor Híbrido de Detecção PII (v9.6.0)                 │ │
│  │                                                      │ │
│  │ ┌─────────────────────────────┐   ┌─────────────────┐ │ │
│  │ │ Pipeline Híbrido Original   │   │ Presidio (MSFT) │ │ │
│  │ │ 1. REGEX + Validação DV     │   │ • AnalyzerEngine│ │ │
│  │ │ 2. BERT Davlan NER          │   │ • Recognizers   │ │ │
│  │ │ 3. BERT monilouise pt-BR    │   │   Customizados  │ │ │
│  │ │ 4. spaCy pt_core_news_lg    │   │   GDF (10+)     │ │ │
│  │ │ 5. Gazetteer GDF            │   └─────────────────┘ │ │
│  │ │ 6. Regras de Negócio        │           │           │ │
│  │ │ 7. Confiança Probabilística │           │           │ │
│  │ │ 8. Thresholds Dinâmicos     │           │           │ │
│  │ │ 9. Deduplicação Avançada    │           │           │ │
│  │ └─────────────┬───────────────┘           │           │ │
│  │               │                           │           │ │
│  │         ┌─────▼─────────────┐             │           │ │
│  │         │   Ensemble/Fusão  │◄────────────┘           │ │
│  │         └─────────┬─────────┘                         │ │
│  │                   │                                   │ │
│  │         ┌─────────▼─────────┐                         │ │
│  │         │ Árbitro LLM       │                         │ │
│  │         │ Llama-3.2-3B (HF) │  ← ✅ ATIVADO PADRÃO    │ │
│  │         │ • Reidentificação │                         │ │
│  │         │ • Decisão ambígua │                         │ │
│  │         └────────────────────┘                        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```
---
## 🔄 Aprendizado Contínuo (Human-in-the-Loop)

O sistema implementa um ciclo de melhoria contínua:

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│ Usuário revisa  │────▶│ POST /feedback   │────▶│ feedback.json      │
│ detecção no UI  │     │ CORRETO/INCORRETO│     │ (persiste dados)   │
└─────────────────┘     └──────────────────┘     └─────────┬──────────┘
                                                           │
┌─────────────────┐     ┌──────────────────┐     ┌─────────▼──────────┐
│ Próximas        │◀────│ Calibradores     │◀────│ Recalibração       │
│ detecções       │     │ isotônicos       │     │ automática         │
│ mais precisas   │     │ ajustados        │     │ (por fonte)        │
└─────────────────┘     └──────────────────┘     └────────────────────┘
```

**Endpoints:** `POST /feedback`, `GET /feedback/stats`, `POST /feedback/generate-dataset`

Consulte [backend/README.md](backend/README.md#-feedback-loop-como-o-motor-aprende-com-feedbacks-humanos) para documentação completa.

---

### Tecnologias Utilizadas

#### Backend (Motor de IA)

| Tecnologia | Versão | Função |
|------------|--------|--------|
| **Python** | 3.10+ | Linguagem principal |
| **FastAPI** | 0.110.0 | Framework web assíncrono |
| **spaCy** | 3.8.0 | NLP para português (`pt_core_news_lg`) |
| **Transformers** | 4.41.2 | BERT NER Davlan + monilouise pt-BR |
| **PyTorch** | 2.1.0 | Deep learning (CPU) |
| **Presidio Analyzer** | 2.2.360+ | Framework Microsoft para detecção de PII |
| **Llama 3.2** | 3B-Instruct | Árbitro LLM via HuggingFace Inference API |
| **huggingface_hub** | latest | InferenceClient para chamadas LLM |
| **scikit-learn** | 1.3.0+ | Calibração isotônica de confiança |
| **Pandas** | 2.2.1 | Processamento de dados tabulares |
| **Celery** | 5.3.0+ | Processamento assíncrono de lotes |
| **Redis** | - | Broker para filas Celery |

#### Modelos de IA

| Modelo | Tipo | Função |
|--------|------|--------|
| `Davlan/bert-base-multilingual-cased-ner-hrl` | BERT NER | Detecção de nomes (multilíngue) |
| `monilouise/ner_news_portuguese` | BERT NER | Detecção de nomes (pt-BR especializado) |
| `pt_core_news_lg` | spaCy | NER português (fallback) |
| `meta-llama/Llama-3.2-3B-Instruct` | LLM | Árbitro para casos ambíguos |

#### Frontend (Interface)

| Tecnologia | Versão | Função |
|------------|--------|--------|
| React | 18.3.1 | Biblioteca UI |
| TypeScript | 5.8.3 | Tipagem estática |
| Vite | 5.4.19 | Build tool ultra-rápido |
| TailwindCSS | 3.4.17 | Estilização (Design DSGOV) |
| Shadcn/UI | latest | Componentes acessíveis |
| Recharts | 2.15.4 | Gráficos e visualizações |
| React Query | 5.83.0 | Cache e estado de requisições |
| XLSX | 0.18.5 | Parser de arquivos Excel |

---

## 7. Comentários no Código

O código está documentado com comentários explicativos em trechos complexos. Exemplos:

### Detector Principal (backend/src/detector.py)

```python
def detect(self, text: str) -> List[PIIFinding]:
    """Detecção de PII usando estratégia Ensemble OR.
    
    Pipeline:
    1. Regex: Detecta padrões estruturados (CPF, Email, Telefone)
    2. NER: spaCy + BERT detectam nomes e entidades
    3. Merge: Combina resultados eliminando duplicatas
    4. LLM: Árbitro resolve conflitos e valida contexto
    
    Estratégia OR: Se QUALQUER detector encontra PII, considera encontrado.
    Isso maximiza recall, essencial para conformidade LGPD.
    """
```

### Sistema de Confiança (backend/src/confidence/calculator.py)

```python
def calculate_confidence(self, findings: List[PIIFinding]) -> float:
    """Calcula confiança usando Calibração Isotônica + Log-Odds.
    
    Combina scores de múltiplas fontes usando Naive Bayes:
    - BERT NER: score do modelo (0.75-0.99)
    - Regex: 0.98 se DV válido, 0.85 se estrutural
    - Contexto: boost/penalidade por padrões linguísticos
    """
```

### API Principal (backend/api/main.py)

```python
@app.post("/analyze")
async def analyze(data: Dict[str, Optional[str]]) -> Dict:
    """Endpoint principal de análise de PII.
    
    Classificações de Risco LGPD:
    - CRÍTICO (5): CPF, RG, CNH (identificação direta)
    - ALTO (4): Email, Telefone, Nome, Endereço
    - MODERADO (3): Placa, Data nascimento, Processo
    - SEGURO (0): Sem PII detectado
    """
```

---

## 8. Estrutura de Arquivos

```
desafio-participa-df/
│
├── README.md                     ← ESTE ARQUIVO: Visão geral do projeto
├── docker-compose.yml            ← Orquestração: backend + frontend
├── deploy-hf.sh                  ← Script de deploy para HuggingFace
│
├── backend/                      ← MOTOR DE IA (Python + FastAPI)
│   ├── app.py                    ← Entry point para HuggingFace Spaces
│   ├── README.md                 ← Documentação técnica do backend
│   ├── requirements.txt          ← Dependências Python (pip install)
│   ├── Dockerfile                ← Container para deploy
│   │
│   ├── api/
│   │   ├── main.py               ← FastAPI: endpoints /analyze e /health
│   │   ├── celery_config.py      ← Configuração Celery + Redis
│   │   └── tasks.py              ← Tasks assíncronas para lotes
│   │
│   ├── src/
│   │   ├── detector.py           ← Motor híbrido PII v9.6 (3300+ linhas, 30+ tipos, thresholds dinâmicos, pós-processamento, gazetteer)
│   │   ├── allow_list.py         ← Lista de termos seguros (blocklist, cargos, contextos, 375+ termos)
│   │   └── confidence/           ← Módulo de confiança probabilística (isotônico, log-odds, thresholds dinâmicos)
│   │       ├── types.py          ← Dataclasses: PIIEntity, DocumentConfidence
│   │       ├── config.py         ← FN/FP rates, pesos LGPD, thresholds
│   │       ├── validators.py     ← Validação DV (CPF, CNPJ, PIS, CNS)
│   │       ├── calibration.py    ← Calibrador isotônico (sklearn)
│   │       ├── combiners.py      ← Combinação log-odds (Naive Bayes)
│   │       └── calculator.py     ← Orquestrador de confiança
│   │
│   ├── scripts/
│   │   ├── main_cli.py           ← CLI: processamento em lote via terminal
│   │   ├── optimize_ensemble.py  ← Grid search de pesos do ensemble
│   │   ├── clean_backend.ps1     ← Limpeza de cache do backend
│   │   └── clean_frontend.ps1    ← Limpeza de cache do frontend
│   │
│   ├── tests/                    ← Testes automatizados (pytest, 410+ casos)
│   │   ├── test_benchmark.py     ← Benchmark LGPD: 452+ casos, F1=1.0000 + 5 casos LLM
│   │   ├── test_amostra.py       ← Testes com amostra e-SIC
│   │   ├── test_confianca.py     ← Testes do sistema de confiança
│   │   ├── test_edge_cases.py    ← Casos extremos e edge cases
│   │   ├── test_regex_gdf.py     ← Testes de padrões regex GDF
│   │   └── ...                   ← Outros testes especializados
│   │
│   └── data/
│       ├── input/                ← Arquivos CSV/XLSX para processar
│       └── output/               ← Relatórios gerados (JSON, CSV, XLSX, resultados benchmark)
│
└── frontend/                     ← INTERFACE WEB (React + TypeScript)
    ├── README.md                 ← Documentação técnica do frontend
    ├── package.json              ← Dependências Node.js (npm install)
    ├── Dockerfile                ← Container com nginx
    ├── vite.config.ts            ← Configuração de build (Vite)
    ├── tailwind.config.ts        ← Design System DSGOV
    │
    ├── src/
    │   ├── main.tsx              ← Entry point React
    │   ├── App.tsx               ← Roteamento e layout
    │   │
    │   ├── pages/
    │   │   ├── Dashboard.tsx     ← Página inicial com KPIs
    │   │   ├── Classification.tsx← Análise individual + lote
    │   │   ├── Documentation.tsx ← Guia de uso integrado
    │   │   └── NotFound.tsx      ← Página 404
    │   │
    │   ├── components/           ← Componentes reutilizáveis (15+)
    │   │   ├── ui/               ← Shadcn UI (16 componentes otimizados)
    │   │   ├── Header.tsx        ← Cabeçalho DSGOV
    │   │   ├── KPICard.tsx       ← Cards de métricas
    │   │   ├── ResultsTable.tsx  ← Tabela de resultados
    │   │   ├── FileDropzone.tsx  ← Upload drag & drop
    │   │   ├── ConfidenceBar.tsx ← Barra visual de confiança
    │   │   ├── RiskThermometer.tsx ← Termômetro de risco
    │   │   └── ...
    │   │
    │   ├── lib/
    │   │   ├── api.ts            ← Cliente HTTP para backend (detecção automática do backend local, retry, tratamento de erros, integração com contadores globais)
    │   │   ├── fileParser.ts     ← Parser de CSV/XLSX
    │   │   └── utils.ts          ← Funções utilitárias
    │   │
    │   ├── contexts/
    │   │   └── AnalysisContext.tsx ← Estado global (histórico, métricas, funções de update)
    │   │
    │   └── hooks/
    │       └── use-toast.ts      ← Notificações
    │
    └── public/
      ├── robots.txt            ← SEO
      └── 404.html              ← Fallback SPA
```

---

## 🧪 Executar Testes

```bash
# Via Docker
docker compose exec backend pytest --maxfail=1 -q

# Local
cd backend
pytest --maxfail=1 -q
```

**Resultado esperado:** `452 passed`

---

## 📚 Documentação Detalhada

Para informações técnicas aprofundadas, consulte:

- **Backend (Motor de IA):** [backend/README.md](backend/README.md)
- **Frontend (Interface):** [frontend/README.md](frontend/README.md)

---

## 👥 Equipe

**Thiago Marinho**  
[LinkedIn](https://www.linkedin.com/feed/) | [GitHub](https://github.com/marinhothiago/)

---

## 📄 Licença

MIT - Uso livre para fins públicos, educacionais e governamentais.

---

<div align="center">

**Hackathon Participa DF 2026 CGDF**  
Projeto em conformidade com LGPD e LAI

</div>
