
---
title: Participa DF - Detector Inteligente de Dados Pessoais
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
pinned: false
---

## 🚀 MELHORIAS E FUNCIONALIDADES AVANÇADAS (2025-2026)

- 🏛️ **Gazetteer institucional GDF:** Filtro de falsos positivos para nomes de órgãos, escolas, hospitais e aliases do DF, editável via `src/gazetteer_gdf.json`. Garante máxima precisão em contexto Brasília/DF.
- 🧠 **Sistema de confiança probabilística:** Calibração isotônica + log-odds, thresholds dinâmicos por tipo, fatores de contexto, explicação detalhada abaixo.
- ⚡ **Pós-processamento de spans:** Normalização, merge/split, deduplicação de entidades para máxima precisão, via `pos_processar_spans.py`.
- 🏆 **Benchmark LGPD/LAI:** 318+ casos reais, F1-score 0.9763, todos FPs/FNs conhecidos e documentados.
- 🔒 **Segurança do token Hugging Face:** Uso obrigatório de `.env` (não versionado), carregamento automático em todos os entrypoints, nunca exposto em código ou log.
- 🧹 **Limpeza e organização:** `.gitignore` e `.dockerignore` revisados, scripts de limpeza, deploy seguro, documentação atualizada.
- 🐳 **Deploy profissional:** Docker Compose, Hugging Face Spaces, checklist de produção.
- 🛠️ **Otimizador de ensemble:** `optimize_ensemble.py` para grid search de pesos do ensemble, reuso de detector, e validação automática.

---
## 🆕 Estratégias de Merge de Spans (Presets)

A partir da versão 9.4.3, o endpoint `/analyze` permite escolher a estratégia de merge de spans (entidades sobrepostas) via parâmetro `merge_preset`:

- `recall`: Mantém todos os spans sobrepostos (maximiza recall, útil para auditoria).
- `precision`: Mantém apenas o span com maior score/confiança (maximiza precisão, útil para produção).
- `f1`: Mantém o span mais longo por sobreposição (equilíbrio entre recall e precisão, padrão).
- `custom`: Permite lógica customizada (exemplo: priorizar fonte específica ou lógica própria).

### Como usar na API

```http
POST /analyze?merge_preset=recall
Content-Type: application/json
{
  "text": "Meu CPF é 123.456.789-09 e meu telefone é 99999-8888"
}
```

- `merge_preset` pode ser: `recall`, `precision`, `f1`, `custom` (default: `f1`)
- O resultado em `detalhes` refletirá a estratégia escolhida.

### Exemplos de uso via curl

```bash
# Maximizar recall (todos spans):

# Maximizar precisão (apenas maior score):
curl -X POST "http://localhost:8000/analyze?merge_preset=precision" -H "Content-Type: application/json" -d '{"text": "Meu CPF é 123.456.789-09"}'

# Customizado:
```

### Observações
- O merge só é aplicado se as entidades retornadas tiverem `start` e `end` (posição no texto).
- Para uso avançado, consulte `src/confidence/combiners.py` e ajuste a função `merge_spans_custom`.
- O preset `custom` pode ser expandido para lógica própria no backend.

---
# 📚 COMO USAR AS NOVAS FUNCIONALIDADES
### Gazetteer GDF
- Edite `src/gazetteer_gdf.json` para adicionar órgãos, escolas, hospitais, programas ou aliases. O detector ignora entidades que batem com o gazetteer, reduzindo FPs em contexto institucional.

- Execute `python optimize_ensemble.py` para buscar os melhores pesos do ensemble. O script reusa o detector e valida o F1-score automaticamente.
### Segurança do Token Hugging Face
- Crie um `.env` (NÃO versionado) com `HF_TOKEN=seu_token`. O backend carrega automaticamente. Nunca exponha o token em código ou log.

- [x] `.env` nunca versionado
- [x] Modelos baixados no build do Docker
- [x] Scripts de limpeza não vão para produção
- [x] Testes e benchmark executados antes do deploy
```bash
python main_cli.py --input data/input/manifestacoes.xlsx --output data/output/resultado

# Rodar benchmark completo

python pos_processar_spans.py --input data/output/resultado.json --output data/output/resultado_pos.json
```

---
---
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 🛡️ Backend: Motor PII Participa DF

## 🔒 Segurança do Token Hugging Face (HF_TOKEN)

> **IMPORTANTE:**
> - O token Hugging Face **NUNCA** deve ser colocado no código-fonte nem em arquivos versionados (ex: .env, settings.py, etc).
> - Use sempre o arquivo `.env` (NÃO versionado) para armazenar o token localmente ou no deploy.
> - O arquivo `.env.example` serve apenas de modelo e pode ir para o GitHub, mas sem o token real.
> - O backend já lê automaticamente o `.env` e injeta o token no pipeline do transformers.
> - No deploy Hugging Face Spaces, configure o token como variável de ambiente ou suba um `.env` manualmente (NÃO envie para o repositório).

**Resumo:**
- O token é lido em tempo de execução, nunca aparece no log nem no código.
- O projeto está seguro para uso público e privado, desde que siga essas orientações.

## 🆕 Integração Gazetteer GDF (v9.5)

O motor agora integra um **gazetteer institucional do GDF** (arquivo `gazetteer_gdf.json`) para filtrar falsos positivos de nomes, órgãos, escolas, hospitais e programas públicos. Isso garante que entidades institucional não sejam marcadas como PII, elevando a precisão em contexto Brasília/DF.

**Como funciona:**
- O arquivo `src/gazetteer_gdf.json` contém listas de órgãos, siglas, aliases, escolas e hospitais do GDF.
- O detector carrega todos os nomes/siglas/aliases e ignora qualquer entidade que bata exata ou parcialmente com o gazetteer.
- Logs informam quando uma entidade é ignorada por match no gazetteer.

**Impacto no benchmark:**
- F1-Score mantido em 0.9763 (excelente, sem aumento de FP/FN)
- Nenhum novo falso positivo ou negativo foi introduzido
- Todos os FPs/FNs remanescentes são casos conhecidos de padrões GDF, não relacionados ao filtro institucional

**Como editar/expandir:**
- Edite `src/gazetteer_gdf.json` para adicionar novos órgãos, escolas, hospitais, programas ou aliases.
- O formato é autoexplicativo e suporta múltiplos aliases por entidade.

**Exemplo de entrada:**
```json
{
    "orgaos": [
        {"nome": "Secretaria de Educação do DF", "sigla": "SEEDF", "aliases": ["Educação DF", "Secretaria Educação"]},
        {"nome": "DETRAN-DF", "sigla": "DETRAN", "aliases": ["Departamento de Trânsito"]}
    ],
    "escolas": [
        {"nome": "Centro de Ensino Fundamental 01 do Guará", "sigla": "CEF 01", "aliases": ["CEF Guará"]}
    ]
}
```

**Arquivo:** `backend/src/gazetteer_gdf.json`

---

[![Python](https://img.shields.io/badge/Python-3.10+-yellow?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![spaCy](https://img.shields.io/badge/spaCy-3.8.0-09A3D5?logo=spacy)](https://spacy.io/)
[![Versão](https://img.shields.io/badge/Versão-9.4.3-blue)](./src/detector.py)
[![F1--Score](https://img.shields.io/badge/F1--Score-1.0000-success)](./benchmark.py)

> **Motor híbrido de detecção de Informações Pessoais Identificáveis (PII)** para conformidade LGPD/LAI em manifestações do Participa DF.
> 🏆 **v9.4.3 - F1-Score = 1.0000** (100% precisão, 100% sensibilidade) em benchmark de 303 casos LGPD.
>
> 🆕 **v9.4.3**: 5 níveis de risco LGPD (CRÍTICO → BAIXO), 30+ tipos de PII, IP/Coordenadas/User-Agent, contadores globais.

| 🌐 **Links de Produção** | URL |
|--------------------------|-----|
| API Base | https://marinhothiago-desafio-participa-df.hf.space/ |
| Documentação Interativa | https://marinhothiago-desafio-participa-df.hf.space/docs |
| Health Check | https://marinhothiago-desafio-participa-df.hf.space/health |

---

## 📋 Objetivo do Backend

Detectar, classificar e avaliar o risco de vazamento de dados pessoais em textos de manifestações do Participa DF, retornando:

- **Classificação:** "PÚBLICO" ou "NÃO PÚBLICO"
- **Nível de Risco:** SEGURO, BAIXO, MODERADO, ALTO, CRÍTICO (5 níveis LGPD)
- **Confiança:** Score normalizado (0.0 a 1.0)
- **Detalhes:** Lista de PIIs encontrados com tipo, valor e confiança

### Funcionalidades Principais

- ✅ **Rastreabilidade Total:** Preserva o ID original do e-SIC em todo o fluxo
- ✅ **Motor Híbrido v9.4.3:** Ensemble de Regex + BERT Davlan + NuNER + spaCy + Regras
- ✅ **30+ Tipos de PII:** Documentos, contatos, financeiros, saúde, biometria, localização
- ✅ **Confiança Probabilística:** Calibração isotônica + combinação log-odds
- ✅ **Três Formas de Uso:** API REST, Interface CLI (lote) e integração com Dashboard Web
- ✅ **Validação de Documentos:** CPF, CNPJ, PIS, CNS com dígito verificador
- ✅ **Contexto Brasília/GDF:** Imunidade funcional para servidores públicos em exercício
- ✅ **Contadores Globais:** Persistência em stats.json com thread-safety

---

## 📁 Estrutura de Arquivos e Função de Cada Componente

```
backend/
├── README.md                 ← ESTE ARQUIVO: Documentação técnica
├── requirements.txt          ← Dependências Python (pip install -r)
├── Dockerfile                ← Container para deploy em HuggingFace
├── docker-compose.yml        ← Orquestração local com frontend
│
├── api/
│   ├── __init__.py           ← Marca como módulo Python
│   └── main.py               ← FastAPI: endpoints /analyze e /health
│                               (135 linhas, comentários detalhados)
│
├── src/
│   ├── __init__.py           ← Marca como módulo Python
│   ├── detector.py           ← Motor híbrido PII v9.4.3
│   │                           (2100+ linhas com comentários explicativos)
│   │                           - Classe PIIDetector: ensemble de detectores
│   │                           - Classe ValidadorDocumentos: validação DV
│   │                           - Regex patterns para 30+ tipos de PII
│   │                           - NER: BERT Davlan + NuNER + spaCy
│   │                           - Regras de negócio (imunidade funcional)
│   │                           - Método detect_extended() com confiança prob.
│   │
│   ├── allow_list.py         ← Lista de termos seguros (375 termos)
│   │                           - Órgãos do GDF (SEEDF, SESDF, DETRAN, etc)
│   │                           - Regiões administrativas de Brasília
│   │                           - Endereços administrativos (SQS, SQN, etc)
│   │                           - Confiança base por tipo de PII
│   │
│   └── confidence/           ← NOVO: Módulo de confiança probabilística
│       ├── __init__.py       ← Exports do módulo
│       ├── types.py          ← PIIEntity, DocumentConfidence, SourceDetection
│       ├── config.py         ← FN_RATES, FP_RATES, PESOS_LGPD, thresholds
│       ├── validators.py     ← Validação DV (CPF, CNPJ, PIS, CNS, etc)
│       ├── calibration.py    ← IsotonicCalibrator, CalibratorRegistry
│       ├── combiners.py      ← ProbabilityCombiner, EntityAggregator
│       └── calculator.py     ← PIIConfidenceCalculator (orquestrador)
│
├── main_cli.py               ← CLI para processamento em lote
│                               - Entrada: CSV/XLSX com coluna "Texto Mascarado"
│                               - Saída: JSON + CSV + XLSX com cores
│
├── benchmark.py              ← 🏆 Benchmark LGPD: 303 casos de teste
│                               - F1-Score = 1.0000 (100% P/R)
│                               - Casos seguros (não PII)
│                               - PIIs clássicos (CPF, Email, Telefone)
│                               - Edge cases de Brasília/GDF
│                               - Imunidade funcional
│
├── test_confianca.py         ← Testes do sistema de confiança
│                               - Validação de dígitos verificadores
│                               - Calibração isotônica
│                               - Combinação log-odds
│
└── data/
    ├── input/                ← Arquivos para processar em lote
    └── output/               ← Relatórios gerados
        ├── resultado.json    ← Dados estruturados
        ├── resultado.csv     ← Planilha simples
        └── resultado.xlsx    ← Excel com formatação de cores
```

---

## 1️⃣ INSTRUÇÕES DE INSTALAÇÃO E DEPENDÊNCIAS

### 1.1 Pré-requisitos

| Software | Versão Mínima | Verificar | Como Instalar |
|----------|---------------|-----------|---------------|
| **Python** | 3.10+ | `python --version` | [python.org](https://www.python.org/downloads/) |
| **pip** | 23.0+ | `pip --version` | Incluído com Python |
| **Git** | 2.0+ | `git --version` | [git-scm.com](https://git-scm.com/) |

**Requisitos de Sistema:**
- **RAM:** Mínimo 4GB (recomendado 8GB para modelos NLP)
- **Disco:** ~3GB (modelos spaCy + BERT)
- **Internet:** Necessária para download inicial dos modelos

### 1.2 Arquivo de Dependências: `requirements.txt`

```txt
# ===========================================
# Participa DF - Backend Requirements
# Python 3.10 (compatível com spaCy 3.8)
# ===========================================

# === Framework Web ===
fastapi==0.110.0              # API REST assíncrona
uvicorn==0.27.1               # Servidor ASGI de alta performance
python-multipart==0.0.9       # Upload de arquivos

# === Processamento de Dados ===
pandas==2.2.1                 # Manipulação de DataFrames
openpyxl==3.1.2               # Leitura/escrita de Excel

# === NLP Core ===
spacy==3.8.0                  # NLP para português (pt_core_news_lg)
text-unidecode==1.3           # Normalização de strings

# === Transformers + PyTorch (CPU) ===
transformers==4.41.2          # BERT NER multilíngue
sentencepiece==0.1.99         # Tokenização
accelerate>=0.21.0            # Otimização de inferência

# NOTA: PyTorch instalado separadamente no Dockerfile
# pip install torch==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

### 1.3 Instalação Passo a Passo

```bash
# 1. Clone o repositório (se ainda não fez)
git clone https://github.com/marinhothiago/desafio-participa-df.git
cd desafio-participa-df/backend

# 2. Crie ambiente virtual Python
python -m venv venv

# 3. Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instale PyTorch CPU (ANTES das outras dependências)
pip install torch==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu

# 5. Instale todas as dependências
pip install -r requirements.txt

# 6. Baixe o modelo spaCy para português (OBRIGATÓRIO)
python -m spacy download pt_core_news_lg

# 7. (Opcional) Verifique a instalação
python -c "import spacy; nlp = spacy.load('pt_core_news_lg'); print('✅ spaCy OK')"
python -c "from transformers import pipeline; print('✅ Transformers OK')"
```

**Tempo estimado:** 5-10 minutos (primeira instalação)

---

## 2️⃣ INSTRUÇÕES DE EXECUÇÃO

### 2.1 Servidor API (FastAPI)

```bash
# Certifique-se de estar na pasta backend/
cd backend

# Ative o ambiente virtual (se não estiver ativo)
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Inicie o servidor
uvicorn api.main:app --host 0.0.0.0 --port 7860 --reload
```

**Saída esperada:**
```
INFO:     🏆 [v9.4.3] VERSÃO HACKATHON - ENSEMBLE 5 FONTES + CONFIANÇA PROBABILÍSTICA
INFO:     ✅ spaCy pt_core_news_lg carregado
INFO:     ✅ BERT Davlan NER multilíngue carregado (PER, ORG, LOC, DATE)
INFO:     ✅ NuNER pt-BR carregado (especializado em português)
INFO:     Uvicorn running on http://0.0.0.0:7860 (Press CTRL+C to quit)
```

**Endpoints disponíveis:**
| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/analyze` | POST | Analisa texto para detecção de PII |
| `/health` | GET | Verifica status da API |
| `/docs` | GET | Documentação Swagger interativa |
| `/redoc` | GET | Documentação ReDoc |

### 2.2 CLI (Processamento em Lote)

```bash
# Ative o ambiente virtual
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Execute o processamento
python main_cli.py --input data/input/manifestacoes.xlsx --output data/output/resultado
```

**Argumentos:**
| Argumento | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `--input` | string | ✅ | Caminho do arquivo CSV ou XLSX |
| `--output` | string | ✅ | Nome base dos arquivos de saída |

**Arquivos gerados (todos com mesma estrutura de colunas):**
| Arquivo | Formato | Uso |
|---------|---------|-----|
| `resultado.json` | JSON | Integração com sistemas, APIs |
| `resultado.csv` | CSV UTF-8 | Importação em outras ferramentas |
| `resultado.xlsx` | Excel | Análise visual com cores por risco |

**Colunas de saída (ordem padronizada):**
1. `ID` - Identificador original do registro
2. `Texto Mascarado` - Texto analisado
3. `Classificação` - ✅ PÚBLICO ou ❌ NÃO PÚBLICO
4. `Confiança` - Percentual de certeza (ex: 98.5%)
5. `Nível de Risco` - SEGURO, BAIXO, MODERADO, ALTO, CRÍTICO
6. `Identificadores` - Lista de PIIs detectados

### 2.3 Execução com Docker

```bash
# Na pasta backend/
docker build -t participa-df-backend .

# Execute o container
docker run -p 7860:7860 participa-df-backend
```

**Ou usando docker-compose (da raiz do projeto):**
```bash
cd ..  # volta para a raiz
docker-compose up backend
```

---

## 📊 Formato de Dados

### Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/analyze` | POST | Analisa texto para detecção de PII |
| `/health` | GET | Verifica status da API |
| `/stats` | GET | Retorna estatísticas globais de uso |
| `/stats/visit` | POST | Registra uma visita ao site |

### Estatísticas Globais (v9.4)

**GET /stats** - Retorna contadores globais:
```json
{
  "site_visits": 1234,
  "classification_requests": 5678,
  "last_updated": "2026-01-16T10:30:00"
}
```

**POST /stats/visit** - Registra visita (chamado 1x por sessão do frontend):
```json
{
  "site_visits": 1235,
  "classification_requests": 5678,
  "last_updated": "2026-01-16T10:31:00"
}
```

> **Nota:** O contador `classification_requests` é incrementado automaticamente a cada chamada ao `/analyze`.

### Entrada (POST /analyze)

```json
{
  "text": "Meu CPF é 123.456.789-09 e preciso de ajuda urgente.",
  "id": "manifestacao_001"
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `text` | string | ✅ Sim | Texto a ser analisado (máx 10.000 caracteres) |
| `id` | string | ❌ Não | ID para rastreabilidade (preservado na saída) |

### Saída

```json
{
  "id": "manifestacao_001",
  "classificacao": "NÃO PÚBLICO",
  "risco": "CRÍTICO",
  "confianca": 0.98,
  "detalhes": [
    {
      "tipo": "CPF",
      "valor": "123.456.789-09",
      "confianca": 1.0
    }
  ]
}
```

| Campo | Tipo | Valores | Descrição |
|-------|------|---------|-----------|
| `id` | string | qualquer | ID preservado da entrada |
| `classificacao` | string | "PÚBLICO", "NÃO PÚBLICO" | Se pode publicar |
| `risco` | string | SEGURO, BAIXO, MODERADO, ALTO, CRÍTICO | Severidade |
| `confianca` | float | 0.0 - 1.0 | Certeza do modelo (normalizado) |
| `detalhes` | array | objetos | Lista de PIIs encontrados |

### Formato de Arquivo para CLI (CSV/XLSX)

O arquivo deve conter uma coluna `Texto Mascarado` (ou `text`):

```csv
ID,Texto Mascarado
man_001,"Solicito informações sobre minha situação cadastral."
man_002,"Meu CPF é 529.982.247-25 e telefone (61) 98765-4321."
man_003,"Reclamação contra o servidor João Silva do DETRAN."
```

**Saída do CLI (mesma estrutura nos 3 formatos):**

```csv
ID,Texto Mascarado,Classificação,Confiança,Nível de Risco,Identificadores
man_001,"Solicito informações...","✅ PÚBLICO","100.0%","SEGURO","[]"
man_002,"Meu CPF é 529.982.247-25...","❌ NÃO PÚBLICO","98.0%","CRÍTICO","['CPF: 529.982.247-25', 'TELEFONE: (61) 98765-4321']"
```

```json
[
  {
    "id": "man_001",
    "texto_mascarado": "Solicito informações...",
    "classificacao": "✅ PÚBLICO",
    "confianca": "100.0%",
    "nivel_risco": "SEGURO",
    "identificadores": "[]"
  },
  {
    "id": "man_002",
    "texto_mascarado": "Meu CPF é 529.982.247-25...",
    "classificacao": "❌ NÃO PÚBLICO",
    "confianca": "98.0%",
    "nivel_risco": "CRÍTICO",
    "identificadores": "['CPF: 529.982.247-25', 'TELEFONE: (61) 98765-4321']"
  }
]
```

---

## 🧠 Arquitetura do Motor de Detecção (v9.4.3)

### Pipeline de Processamento

```
Texto de Entrada
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│                    CAMADA 1: REGEX                           │
│  • CPF (com validação de dígito verificador)                 │
│  • CNPJ, PIS, CNS, Título de Eleitor (validação DV)         │
│  • RG, CNH, Passaporte, CTPS, Certidões                     │
│  • Email pessoal (exclui .gov.br, .org.br, .edu.br)         │
│  • Telefone (fixo, celular, DDI)                             │
│  • Endereço residencial, CEP                                 │
│  • Dados bancários, PIX, Cartão de crédito                   │
│  • Placa de veículo (Mercosul e antiga)                      │
│  • Data de nascimento, IP Address                            │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│              CAMADA 2: BERT NER (primário)                   │
│  Modelo: Davlan/bert-base-multilingual-cased-ner-hrl        │
│  • Detector primário de nomes pessoais (PER)                 │
│  • Threshold de confiança: 0.75                              │
│  • Filtros: nome + sobrenome, não em blocklist               │
│  • Verifica imunidade funcional antes de marcar              │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│            CAMADA 3: spaCy (complementar)                    │
│  Modelo: pt_core_news_lg (português)                         │
│  • Captura nomes que o BERT não detectou                     │
│  • Roda em paralelo, não é fallback                          │
│  • Evita duplicatas: só adiciona se BERT não encontrou       │
│  • Mesmos filtros de qualidade                               │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│              CAMADA 4: REGRAS DE NEGÓCIO                     │
│  • Gatilhos de contato: "falar com", "ligar para"           │
│    → Nome após gatilho = SEMPRE PII                          │
│  • Imunidade funcional: "Dr. João da Secretaria"             │
│    → Servidor em contexto funcional = NÃO PII                │
│  • Contexto Brasília: SQS, SQN, Eixo = endereço público     │
│  • Blocklist: saudações, termos administrativos              │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│                  ENSEMBLE OR + DEDUPLICAÇÃO                  │
│  • Combina achados de todas as camadas                       │
│  • Remove duplicatas priorizando maior peso                  │
│  • Calcula risco máximo e confiança composta                 │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
   Resultado Final
   (classificacao, risco, confianca, detalhes)
```

### Sistema de Confiança Composta

A confiança de cada PII detectado é calculada dinamicamente:

```
confiança_final = min(1.0, confiança_base × fator_contexto)
```

#### Confiança Base por Método

| Método | Tipos | Base | Justificativa |
|--------|-------|------|---------------|
| **Regex + DV** | CPF, PIS, CNS, CNH, Título Eleitor, CTPS | 0.98 | Validação matemática |
| **Regex + Luhn** | Cartão Crédito | 0.95 | Algoritmo válido |
| **Regex estrutural** | Email, Telefone, Placa, PIX | 0.85-0.95 | Padrão claro |
| **Regex + contexto** | CEP, Data Nascimento | 0.70-0.75 | Depende de contexto |
| **BERT NER** | Nomes | score do modelo | Retorna 0.75-0.99 |
| **spaCy NER** | Nomes | 0.70 | Modelo complementar |
| **Gatilho** | Nomes após "falar com" | 0.85 | Padrão linguístico |

#### Fatores de Contexto

| Fator | Ajuste | Exemplo |
|-------|--------|---------|
| Possessivo | +15% | "**Meu** CPF é..." |
| Label explícito | +10% | "**CPF:** 529..." |
| Verbo declarativo | +5% | "CPF **é** 529..." |
| Gatilho de contato | +10% | "**falar com** João" |
| Contexto de teste | -25% | "**exemplo**: 000..." |
| Declarado fictício | -30% | "CPF **fictício**" |
| Negação | -20% | "**não é** meu CPF" |
| Institucional | -10% | "CPF **da empresa**" |

#### Exemplos de Cálculo

```python
# Exemplo 1: CPF com possessivo e label
texto = "Meu CPF: 529.982.247-25"
base = 0.98  # DV válido
fator = 1.0 + 0.15 (possessivo) + 0.10 (label) = 1.25
confianca = min(1.0, 0.98 * 1.25) = 1.0  # Capped

# Exemplo 2: CPF em contexto de exemplo
texto = "exemplo de CPF: 529.982.247-25"
base = 0.98
fator = 1.0 - 0.25 (exemplo) = 0.75
confianca = 0.98 * 0.75 = 0.74  # Baixa, pode ser filtrado

# Exemplo 3: Nome detectado por BERT com gatilho
texto = "falar com João Silva"
base = 0.87  # Score do BERT
fator = 1.0 + 0.10 (gatilho) = 1.10
confianca = min(1.0, 0.87 * 1.10) = 0.96
```

### Tipos de PII Detectados

| Categoria | Tipos | Peso | Validação |
|-----------|-------|------|-----------|
| **Documentos** | CPF, RG, CNH, Passaporte, PIS, CNS, CNPJ (MEI), Título Eleitor, CTPS, Certidões | 5 (Crítico) | Dígito Verificador |
| **Contato** | Email pessoal, Telefone, Celular | 4 (Alto) | Regex + exclusão institucional |
| **Localização** | Endereço residencial, CEP | 4 (Alto) | Contexto "moro", "resido" |
| **Financeiro** | Conta bancária, PIX, Cartão de crédito | 4 (Alto) | Padrões estruturados |
| **Identificação** | Nome completo, Nome em contexto | 3-4 | BERT NER + regras |
| **Outros** | Placa de veículo, Data nascimento, IP | 3 (Moderado) | Regex |

### Imunidade Funcional (LAI)

Servidores públicos em exercício de função **NÃO são PII**:
- ✅ "A Dra. Maria da Secretaria de Saúde informou que..."
- ✅ "O servidor José Santos do DETRAN atendeu a demanda"
- ✅ "Funcionário do mês: Pedro Oliveira"

**Gatilhos que ANULAM imunidade:**
- ❌ "Preciso falar com o João Silva sobre isso"
- ❌ "Ligar para a Dra. Maria no celular"
- ❌ "Endereço da Maria: Rua das Flores, 123"

---

## 🧪 Testes e Benchmark

```bash
# Na pasta backend/, com ambiente virtual ativo

# Execute o benchmark LGPD (303 casos, F1=1.0)
python benchmark.py

# Execute os testes de confiança
python test_confianca.py
```

**Benchmark LGPD (303 casos - F1-Score = 1.0000):**

| Grupo | Quantidade | Esperado | Descrição |
|-------|------------|----------|-----------|
| Administrativo | 50+ | PÚBLICO | Textos burocráticos sem PII |
| PII Clássico | 80+ | NÃO PÚBLICO | CPF, Email, Telefone, RG, etc |
| Nomes | 40+ | Variado | Nomes com contexto funcional vs pessoal |
| Edge Cases | 50+ | Variado | Situações ambíguas, Brasília/GDF |
| Imunidade | 30+ | PÚBLICO | Servidores em exercício |
| Gatilhos | 25+ | NÃO PÚBLICO | "falar com", "ligar para" |
| Documentos DV | 25+ | NÃO PÚBLICO | CPF, CNPJ, PIS, CNS com validação |

---

## 🐳 Dockerfile

```dockerfile
# Python 3.10 slim para menor tamanho
FROM python:3.10-slim

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala PyTorch CPU
RUN pip install --no-cache-dir torch==2.1.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baixa modelo spaCy
RUN pip install --no-cache-dir \
    https://github.com/explosion/spacy-models/releases/download/pt_core_news_lg-3.8.0/pt_core_news_lg-3.8.0-py3-none-any.whl

# Pré-download BERT NER
RUN python -c "from transformers import pipeline; \
    pipeline('ner', model='Davlan/bert-base-multilingual-cased-ner-hrl')"

# Copia código
COPY . .

# Porta HuggingFace Spaces
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Comando de inicialização
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

---

## 📚 Código Fonte Comentado

### Exemplo: Motor de Detecção (`src/detector.py`)

```python
class PIIDetector:
    """Detector híbrido de PII com ensemble de alta recall.
    
    Estratégia: Ensemble OR - qualquer detector positivo classifica como PII.
    Isso maximiza recall (não deixar escapar nenhum PII) às custas de alguns
    falsos positivos, que é a estratégia correta para LAI/LGPD.
    """

    def __init__(self, usar_gpu: bool = True) -> None:
        """Inicializa o detector com todos os modelos NLP.
        
        Args:
            usar_gpu: Se True, usa CUDA quando disponível
        """
        logger.info("🏆 [v9.2] F1-Score = 1.0000 - Benchmark LGPD")
        
        self.validador = ValidadorDocumentos()
        self._inicializar_modelos(usar_gpu)
        self._inicializar_vocabularios()
        self._compilar_patterns()

    def detect(self, text: str) -> Tuple[bool, List[Dict], str, float]:
        """Detecta PII no texto usando ensemble de alta recall.
        
        Pipeline:
        1. Regex com validação de DV (documentos)
        2. Extração de nomes após gatilhos de contato
        3. NER com BERT + spaCy (nomes e entidades)
        4. Deduplicação com prioridade por peso
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Tuple com:
            - is_pii (bool): True se contém PII
            - findings (List[Dict]): PIIs encontrados
            - nivel_risco (str): CRITICO, ALTO, MODERADO, BAIXO, SEGURO
            - confianca (float): Score 0-1 normalizado
        """
```

### Exemplo: API FastAPI (`api/main.py`)

```python
@app.post("/analyze")
async def analyze(data: Dict[str, Optional[str]]) -> Dict:
    """Analisa texto para detecção de PII com contexto Brasília/GDF.
    
    Realiza detecção híbrida usando:
    - Regex: Padrões estruturados (CPF, Email, Telefone, RG, CNH)
    - NLP: Reconhecimento de entidades com spaCy + BERT
    - Regras de Negócio: Contexto de Brasília, imunidade funcional (LAI)
    
    Args:
        data: Dict com "text" (obrigatório) e "id" (opcional)
    
    Returns:
        Dict com classificacao, risco, confianca e detalhes
    """
```

---

## 🔗 Integração com Frontend

O frontend React se conecta automaticamente ao backend:

1. **Detecção automática:** Tenta `localhost:7860` primeiro (2s timeout)
2. **Fallback produção:** Se local não disponível, usa HuggingFace Spaces
3. **Retry automático:** 1 retry com delay de 3s para cold start

```typescript
// frontend/src/lib/api.ts
const PRODUCTION_API_URL = 'https://marinhothiago-desafio-participa-df.hf.space';
const LOCAL_API_URL = 'http://localhost:7860';
```

---

## 🎯 Sistema de Confiança Probabilística (v9.4)

O backend inclui um sistema sofisticado de cálculo de confiança baseado em práticas de produção de grandes empresas (Google, Microsoft, Meta) e bancos brasileiros.

### Arquitetura do Módulo

```
backend/src/confidence/
├── __init__.py        # Exports do módulo
├── types.py           # Dataclasses (PIIEntity, DocumentConfidence)
├── config.py          # Taxas FN/FP, pesos LGPD, thresholds
├── validators.py      # Validação de dígitos verificadores
├── calibration.py     # Calibração isotônica de scores
├── combiners.py       # Combinação via Log-Odds (Naive Bayes)
└── calculator.py      # Orquestrador principal
```

### Componentes Principais

#### 1. Calibração de Scores (Isotonic Regression)

Modelos neurais como BERT são frequentemente **overconfident** - retornam scores altos mesmo quando erram. A calibração isotônica corrige isso:

```python
# Score bruto 0.95 -> Score calibrado ~0.85
# Score bruto 0.99 -> Score calibrado ~0.90
```

#### 2. Combinação via Log-Odds (Naive Bayes)

Quando múltiplas fontes detectam a mesma entidade, combinamos via log-odds:

$$
\text{logit} = \log\frac{p_{\text{prior}}}{1 - p_{\text{prior}}} + \sum_i \log\frac{p_i}{FP_i}
$$

$$
\text{confidence} = \frac{e^{\text{logit}}}{1 + e^{\text{logit}}}
$$

#### 3. Taxas de Erro por Fonte

```python
# False Negative Rates (quanto cada fonte PERDE)
FN_RATES = {
    "bert_ner": 0.008,      # BERT perde 0.8%
    "spacy": 0.015,         # spaCy perde 1.5%
    "regex": 0.003,         # Regex perde 0.3%
    "dv_validation": 0.0001 # DV quase perfeito
}

# False Positive Rates (alarmes falsos)
FP_RATES = {
    "bert_ner": 0.02,       # 2% de FP
    "spacy": 0.03,          # 3% de FP
    "regex": 0.0002,        # Muito preciso
    "dv_validation": 0.00001 # Quase impossível ser FP
}
```

#### 4. Métricas de Documento

- **`confidence_no_pii`**: P(não existe PII) quando nada detectado
- **`confidence_all_found`**: P(encontramos todo PII) quando tem detecções
- **`confidence_min_entity`**: Menor confiança entre entidades (elo mais fraco)

### Novo Endpoint Extendido

```python
# Método detect_extended() retorna estrutura completa
resultado = detector.detect_extended(texto)

# Estrutura de resposta:
{
    "has_pii": True,
    "classificacao": "NÃO PÚBLICO",
    "risco": "CRÍTICO",
    "confidence": {
        "no_pii": 0.0,
        "all_found": 0.9999,
        "min_entity": 0.9850
    },
    "sources_used": ["bert_ner", "spacy", "regex"],
    "entities": [
        {
            "tipo": "CPF",
            "valor": "529.982.247-25",
            "confianca": 0.9999,
            "confidence_level": "very_high",
            "sources": ["regex", "dv_validation"],
            "dv_valid": True
        }
    ],
    "total_entities": 1
}
```

### Validação de Dígitos Verificadores

O módulo valida automaticamente documentos brasileiros:

| Documento | Algoritmo | Confiança se Válido |
|-----------|-----------|---------------------|
| CPF | Módulo 11 | 0.9999 |
| CNPJ | Módulo 11 com pesos | 0.9999 |
| PIS/NIT | Módulo 11 com pesos | 0.9999 |
| CNS | Soma ponderada | 0.9999 |
| Título Eleitor | DVs específicos por UF | 0.9999 |
| Cartão Crédito | Luhn | 0.9999 |

### Backward Compatibility

O método `detect()` original continua funcionando:

```python
# API antiga (mantida)
is_pii, findings, risco, conf = detector.detect(texto)

# API nova (recomendada)
resultado = detector.detect_extended(texto)
```

---

## 📄 Licença

Desenvolvido para o **Hackathon Participa DF 2025** em conformidade com:
- **LGPD** - Lei Geral de Proteção de Dados (Lei nº 13.709/2018)
- **LAI** - Lei de Acesso à Informação (Lei nº 12.527/2011)

---

## 🚀 Deploy no Hugging Face Spaces: Quais arquivos vão para produção?

Para garantir builds rápidos, seguros e reprodutíveis no Hugging Face Spaces (ou Docker em produção), **apenas os arquivos essenciais devem ser enviados para o contexto de build**:


### Checklist de Deploy (Docker/Hugging Face)

**Inclua no build:**
- `src/` (código-fonte principal)
- `api/` (endpoints FastAPI)
- `requirements.txt` (dependências)
- `Dockerfile` (build)
- `data/input/AMOSTRA_e-SIC.xlsx` (amostra oficial, permitida no build)

**Ignore tudo que for apenas para desenvolvimento local:**
- `scripts/` (automatizações, limpeza, etc)
- arquivos de teste, notebooks, caches, dados sensíveis não autorizados

**Observação:**
- A amostra `AMOSTRA_e-SIC.xlsx` pode ir para produção (Docker/HF) conforme decisão do projeto/hackathon.
- O diretório `scripts/` é exclusivo para automações e limpeza local, nunca vai para produção.

**Dica:** O arquivo `.dockerignore` já está configurado para ignorar scripts/ e artefatos de dev. Se for subir manualmente para o Hugging Face, envie só os arquivos essenciais e a amostra permitida!

---
