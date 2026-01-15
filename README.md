---
title: Participa DF - PII Detector
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
pinned: false
---

# 🛡️ Projeto Participa DF: Detector Inteligente de Dados Pessoais para Transparência Ativa

[![Status do Deploy](https://img.shields.io/badge/Status-Online%20v8.5-brightgreen)](https://marinhothiago.github.io/desafio-participa-df/)
[![Licença](https://img.shields.io/badge/Licença-LGPD%20%2F%20LAI%20Compliant-blue)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
[![Acurácia](https://img.shields.io/badge/Acurácia-112%2F112%20%28100%25%29-brightgreen)](./backend/README.md)
![Arquitetura](https://img.shields.io/badge/Arquitetura-Monorepo-orange)

## 📋 Objetivo da Solução

Detector híbrido de Informações Pessoais Identificáveis (PII) que classifica e avalia o risco de vazamento de dados pessoais em textos de manifestações públicas, garantindo:
- **Transparência Ativa (LAI):** Publicação responsável de pedidos de acesso à informação
- **Conformidade LGPD:** Proteção rigorosa da privacidade do cidadão
- **Rastreabilidade:** Preservação do ID original do e-SIC para auditoria

### 🎯 Resultado Esperado

O Governo do Distrito Federal pode publicizar manifestações de cidadãos sem expor dados sensíveis (CPF, RG, Telefone, Email, Endereço Residencial, etc.), automaticamente e em tempo real.

---

## 📁 Estrutura do Monorepo e Função de Cada Arquivo

O projeto é organizado em **componentes independentes mas integrados**:

```
projeto-participa-df/                   ← Raiz (você está aqui)
├── README.md                           ← ESTE ARQUIVO (Overview completo)
│
├── backend/                            ← Motor de IA (Python + FastAPI)
│   ├── README.md                       ← Guia técnico backend detalhado
│   ├── requirements.txt                ← Dependências Python (pip)
│   ├── Dockerfile                      ← Deploy em container (HuggingFace)
│   ├── api/
│   │   └── main.py                     ← FastAPI server: POST /analyze, GET /health
│   ├── src/
│   │   ├── detector.py                 ← Motor híbrido de PII (368 linhas, comentado)
│   │   └── allow_list.py               ← Dicionário de exceções (termos GDF)
│   ├── data/
│   │   ├── input/                      ← Arquivos Excel/CSV para processar em lote
│   │   └── output/                     ← Resultados em JSON/CSV
│   ├── main_cli.py                     ← CLI: processar lotes via terminal
│   ├── test_metrics.py                 ← Suite de 112 testes automatizados
│   └── test_debug.py                   ← Debug interativo
│
├── frontend/                           ← Interface React (Node.js + Vite)
│   ├── README.md                       ← Guia técnico frontend detalhado
│   ├── package.json                    ← Dependências JavaScript (npm)
│   ├── vite.config.ts                  ← Configuração de build
│   ├── index.html                      ← Arquivo HTML principal
│   ├── src/
│   │   ├── main.tsx                    ← Arquivo principal (entry point)
│   │   ├── App.tsx                     ← Componente raiz com roteamento
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx           ← Página inicial com KPIs
│   │   │   ├── Classification.tsx      ← Análise individual + processamento lote
│   │   │   ├── Documentation.tsx       ← Guia de uso no próprio app
│   │   │   └── NotFound.tsx            ← Página 404
│   │   ├── components/                 ← Componentes reutilizáveis
│   │   │   ├── ui/                     ← Shadcn UI components (buttons, cards, etc)
│   │   │   ├── Header.tsx              ← Cabeçalho com logo DSGOV
│   │   │   ├── KPICard.tsx             ← Cards de métricas
│   │   │   ├── ConfidenceBar.tsx       ← Barra visual de confiança (0-100%)
│   │   │   ├── ResultsTable.tsx        ← Tabela de resultados com paginação
│   │   │   └── ... (15+ componentes)   ← Outros componentes especializados
│   │   ├── lib/
│   │   │   ├── api.ts                  ← Cliente HTTP integrado com backend
│   │   │   ├── fileParser.ts           ← Parser de CSV/XLSX para batch
│   │   │   └── utils.ts                ← Utilitários (masks, formatação, etc)
│   │   ├── contexts/
│   │   │   └── AnalysisContext.tsx     ← State management (histórico de análises)
│   │   └── hooks/
│   │       └── use-toast.ts            ← Notificações do sistema
│   ├── public/
│   │   ├── favicon.svg                 ← Ícone 🟢🟡🔵 (cores da bandeira)
│   │   ├── robots.txt                  ← SEO para mecanismos de busca
│   │   └── data/                       ← Dados de exemplo
│   └── tailwind.config.ts              ← Design system DSGOV (cores, fontes)
│
├── .gitignore                          ← Arquivos ignorados do git
├── STATUS_FINAL_v8.6.md                ← Documentação final e canônica
├── GUIA_VALIDACAO_v8.6.md              ← Como testar e validar
├── GUIA_HUGGINGFACE.md                 ← Deploy em nuvem (HuggingFace Spaces)
└── GEMINI.md                           ← Contexto de IA (prompt)
```

---

## 🏗️ Arquitetura Técnica do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND (React + Vite)                    │
│              GitHub Pages (Static Hosting)                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Dashboard com KPIs em tempo real                      │ │\n│  │ • Análise individual: texto → detalhes de PII          │ │\n│  │ • Processamento em lote: CSV/XLSX → Relatório         │ │\n│  │ • Design System DSGOV (Padrão Federal Brasileiro)      │ │\n│  └────────────────────────────────────────────────────────┘ │\n└────────────────┬──────────────────────────────────────────────┘\n                 │\n                 │ HTTP POST /analyze\n                 │ { text: string }\n                 │\n                 ↓\n┌─────────────────────────────────────────────────────────────┐\n│                 BACKEND (FastAPI + Docker)                 │\n│           Hugging Face Spaces (Cloud Hosting)              │\n│  ┌────────────────────────────────────────────────────────┐ │\n│  │ Motor Híbrido de Detecção PII (detector.py)            │ │\n│  │ 368 linhas com comentários explicativos                 │ │\n│  │                                                         │ │\n│  │ 1. REGEX PATTERNS (Estruturado)                        │ │\n│  │    → CPF: 123.456.789-09                               │ │\n│  │    → RG, CNH, Passaporte, Email, Telefone             │ │\n│  │                                                         │ │\n│  │ 2. NLP SPACY (Português pt_core_news_lg)               │ │\n│  │    → Reconhecimento de entidades nomeadas (NER)        │ │\n│  │    → Endereços, Órgãos, Pessoas                        │ │\n│  │                                                         │ │\n│  │ 3. BERT (Transformers)                                 │ │\n│  │    → Classificação de nomes pessoais                   │ │\n│  │    → Alta precisão com contexto                        │ │\n│  │                                                         │ │\n│  │ 4. REGRAS DE NEGÓCIO (Brasília + LGPD)                │ │\n│  │    → Imunidade funcional de servidores públicos        │ │\n│  │    → Contexto administrativo vs residencial            │ │\n│  │    → Deduplicação de achados                           │ │\n│  │                                                         │ │\n│  │ OUTPUT: {                                              │ │\n│  │   \"classificacao\": \"NÃO PÚBLICO\" | \"PÚBLICO\",         │ │\n│  │   \"risco\": \"CRÍTICO\" | \"ALTO\" | \"MODERADO\" | \"SEGURO\",│ │\n│  │   \"confianca\": 0.0-1.0 (normalizado),                 │ │\n│  │   \"detalhes\": [                                        │ │\n│  │     { \"tipo\": \"CPF\", \"valor\": \"123.***.***-09\" }      │ │\n│  │   ]                                                     │ │\n│  │ }                                                       │ │\n│  └────────────────────────────────────────────────────────┘ │\n└─────────────────────────────────────────────────────────────┘\n```


---

## 1️⃣ INSTRUÇÕES DE INSTALAÇÃO E DEPENDÊNCIAS (4 PONTOS)

### 1.1 Pré-requisitos (1 ponto)

Antes de começar, instale os seguintes softwares:

| Componente | Versão Mínima | Como Instalar |
|-----------|---------------|---------------|
| **Python** | 3.10+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18.0+ | [nodejs.org](https://nodejs.org/) |
| **npm** (incluído) | 9.0+ | Automático com Node.js |
| **Git** | Qualquer | [git-scm.com](https://git-scm.com/) |

**Verificar instalação:**
```bash
python --version        # Esperado: Python 3.10+
node --version          # Esperado: v18.0+
npm --version           # Esperado: 9.0+
```

### 1.2 Gerenciamento de Pacotes (2 pontos)

O projeto utiliza **dois** sistemas de dependências:

#### Backend: `backend/requirements.txt`
```
fastapi==0.104.1
uvicorn==0.24.0
spacy==3.7.2
transformers==4.35.2
torch==2.1.0
pandas==2.1.3
openpyxl==3.10.10
text-unidecode==1.3
```

#### Frontend: `frontend/package.json`
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "vite": "^5.4.19",
    "typescript": "^5.3.3",
    "tailwindcss": "^3.3.6",
    "recharts": "^2.10.3"
  }
}
```

### 1.3 Configuração do Ambiente (Passo a Passo Exato) - 1 ponto

#### PASSO 1: Clone o Repositório
```bash
git clone https://github.com/marinhothiago/participa-df-pii.git
cd participa-df-pii
```

#### PASSO 2: Configure o Backend (Python)
```bash
cd backend

# Crie ambiente virtual
python -m venv venv

# Ative o ambiente
# ▼ Windows
venv\Scripts\activate
# ▼ Linux/Mac
source venv/bin/activate

# Instale TODAS as dependências
pip install -r requirements.txt

# Baixe o modelo de linguagem
python -m spacy download pt_core_news_lg

# Retorne à raiz
cd ..
```

#### PASSO 3: Configure o Frontend (Node.js)
```bash
cd frontend

# Instale dependências
npm install

# Retorne à raiz
cd ..
```

✅ **Instalação concluída!**

---

## 2️⃣ INSTRUÇÕES DE EXECUÇÃO (3 PONTOS)

### 2.1 Comandos Exatos para Executar (2 pontos)

Abra **DOIS terminais** side-by-side:

#### Terminal 1: Backend (Motor de IA)
```bash
cd backend

# Ative ambiente
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Inicie servidor
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Você verá:
# ℹ️ Uvicorn running on http://0.0.0.0:8000
# ℹ️ Press CTRL+C to quit
```

#### Terminal 2: Frontend (Interface)
```bash
cd frontend

# Inicie desenvolvimento
npm run dev

# Você verá:
# ➜  Local:   http://localhost:8080/desafio-participa-df/
```

#### Acesse a Aplicação
Abra: **http://localhost:8080/desafio-participa-df/**

---

### 2.2 Formato de Dados Esperado (Entrada e Saída) - 1 ponto

#### Entrada (Input)

**A) Texto Individual:**
```json
POST /analyze
Content-Type: application/json

{
  "text": "Meu CPF é 123.456.789-09 e telefone (11) 99999-9999",
  "id": "manifestacao_001"
}
```

**B) Arquivo CSV/XLSX (Lote):**
```
ID                | Texto
MAN-2024-001      | Cidadão solicita informações sobre...
MAN-2024-002      | Reclamação regarding service...
```

#### Saída (Output)

```json
{
  "id": "manifestacao_001",
  "classificacao": "NÃO PÚBLICO",
  "risco": "CRÍTICO",
  "confianca": 0.98,
  "detalhes": [
    {
      "tipo": "CPF",
      "valor": "123.***.***-09",
      "confianca": 1.0
    },
    {
      "tipo": "TELEFONE",
      "valor": "(11) 9****-9999",
      "confianca": 0.95
    }
  ]
}
```

**Campos:**
- `classificacao`: "NÃO PÚBLICO" (contém PII) | "PÚBLICO" (seguro)
- `risco`: "CRÍTICO" > "ALTO" > "MODERADO" > "SEGURO"
- `confianca`: 0.0-1.0 (certeza do modelo)

---

## 3️⃣ CLAREZA E ORGANIZAÇÃO (3 PONTOS)

### 3.1 README Principal (Este Arquivo) - 1 ponto

✅ Descreve objetivo da solução  
✅ Mostra estrutura completa de arquivos  
✅ Explica função de cada componente  
✅ Instruções de instalação, configuração, execução  

### 3.2 Código-Fonte com Comentários - 1 ponto

**Backend:** [src/detector.py](./backend/src/detector.py) - 368 linhas com:
```python
"""Módulo de detecção de PII com híbrido (Regex + NLP + BERT + Regras)."""
# Comentários explicando lógica de:
# - Normalização de confiança
# - Regras de imunidade funcional
# - Deduplicação inteligente
```

**API:** [api/main.py](./backend/api/main.py) - Comentários detalhados:
```python
@app.post("/analyze")
async def analyze(data):
    """Análise completa com contexto Brasília/GDF."""
    # Explicação de cada etapa do processamento
```

**Frontend:** [src/lib/api.ts](./frontend/src/lib/api.ts) - Tipos bem documentados:
```typescript
// Interfaces explicadas com comentários
// Mapeamento de resposta da API
// Tratamento de erros específicos
```

### 3.3 Estrutura de Arquivos Lógica - 1 ponto

✅ **Separação clara:**
- `/backend` - Lógica IA apenas
- `/frontend` - Interface apenas
- `/data` - Entrada/saída isolada

✅ **Modularização:**
- `detector.py` = uma responsabilidade
- `allow_list.py` = exceções fácil de atualizar
- Componentes React com props claras

✅ **Configuração centralizada:**
- `requirements.txt` / `package.json`
- `Dockerfile` / `vite.config.ts`

---

## 🧪 Guias de Teste - 3 Cenários de Execução

### 📌 Resumo Executivo

| Cenário | Tempo Setup | Dependências | Melhor Para | Comando |
|---------|-----------|--------------|-----------|---------|
| **LOCAL (Nativo)** | 5-10 min | Python 3.10, Node.js 18+, pip, npm | Desenvolvimento rápido | `npm run dev` + `uvicorn api.main:app --reload` |
| **DOCKER (Local)** | 2-3 min | Docker + docker-compose | Ambiente isolado, sem deps | `docker-compose up` |
| **ONLINE (Cloud)** | 0 min | Browser + internet | Demo sem instalação | Acesso direto ao link |

---

### 🔴 Cenário 1: EXECUÇÃO NATIVA (Local - npm + uvicorn)

**Ideal para:** Desenvolvimento, debugging, avaliação rápida sem Docker

#### Pré-requisitos:
```bash
✓ Python 3.10+  (verificar: python --version)
✓ Node.js 18+   (verificar: node --version)
✓ pip           (geralmente vem com Python)
✓ npm           (geralmente vem com Node.js)
```

#### Passos:

**1️⃣ Clonar o repositório:**
```bash
git clone https://github.com/marinhothiago/participa-df-pii.git
cd participa-df-pii
```

**2️⃣ Iniciar Backend (Terminal 1):**
```bash
cd backend
pip install -r requirements.txt          # Instalar dependências (primeira vez: 3-5 min)
python -m uvicorn api.main:app --reload   # Servidor em http://localhost:8000
```
✅ Esperado: `Uvicorn running on http://127.0.0.1:8000`

**3️⃣ Iniciar Frontend (Terminal 2):**
```bash
cd frontend
npm install                               # Instalar dependências (primeira vez: 2-3 min)
npm run dev                              # Dev server em http://localhost:8080
```
✅ Esperado: `Local: http://127.0.0.1:8080/desafio-participa-df/`

**4️⃣ Testar:**
- Abrir browser em `http://localhost:8080/desafio-participa-df/`
- Submeter um texto com dados pessoais (ex: "Meu CPF é 123.456.789-09")
- ✅ Esperado: Resposta local (<2 segundos) - backend local auto-detectado

**Troubleshooting:**
| Problema | Solução |
|----------|---------|
| `ModuleNotFoundError: No module named 'spacy'` | `pip install -r requirements.txt` novamente |
| `Port 8000 already in use` | Mude porta: `uvicorn api.main:app --reload --port 8001` |
| `Port 8080 already in use` | Npm usa porta alternativa automaticamente |
| Frontend conecta em HuggingFace em vez de localhost | Aguarde 2s para autodetecção, recarregue a página |

**Tempo Total:** ~15 minutos (primeira vez), ~1 minuto (próximas vezes)

---

### 🐳 Cenário 2: EXECUÇÃO COM DOCKER (Recomendado para Avaliação)

**Ideal para:** Isolamento total, sem dependências globais, reprodutibilidade garantida

#### Pré-requisitos:
```bash
✓ Docker      (verificar: docker --version)
✓ Docker Compose (verificar: docker-compose --version)
✓ Internet    (para baixar imagem ~800MB na primeira vez)
```

#### Passos:

**1️⃣ Clonar o repositório:**
```bash
git clone https://github.com/marinhothiago/participa-df-pii.git
cd participa-df-pii
```

**2️⃣ Iniciar com Docker Compose:**
```bash
docker-compose up
```

✅ Esperado (primeira vez):
```
Building backend-app
[...] Sending build context to Docker daemon
[...] Installing requirements
[...] Downloading spaCy model pt_core_news_lg
[...] Container backend-app Running

Backend API on http://127.0.0.1:7860
```

**3️⃣ Testar:**
- Abrir browser em `http://localhost:7860/docs` (Swagger API)
- Ou acessar interface: `http://localhost:7860/` (se configurado)
- Submeter teste via Swagger

**Vantagens:**
- ✅ Sem instalação de Python/Node localmente
- ✅ Modelos de IA (spaCy, BERT) já pre-instalados na imagem
- ✅ Ambiente exatamente igual ao HuggingFace Spaces
- ✅ Isolamento perfeito (não afeta outro software)

**Troubleshooting:**
| Problema | Solução |
|----------|---------|
| `docker: command not found` | Instalar Docker Desktop: https://docker.com/download |
| `ERROR: pull access denied` | Verificar conexão internet, tentar novamente |
| `Port 7860 already in use` | Mude no docker-compose.yml: `"8001:8000"` |
| Imagem muito grande | Normal (~2.5GB descompactado), primeiro build é mais lento |

**Tempo Total:** ~5 minutos (primeira vez, download incluído), <30 segundos (próximas vezes)

---

### 🌐 Cenário 3: EXECUÇÃO ONLINE (Demo - Zero Setup)

**Ideal para:** Demo rápida, sem instalação, compartilhar link

#### Pré-requisitos:
```bash
✓ Browser moderno (Chrome, Firefox, Safari, Edge)
✓ Conexão internet
```

#### Passos:

**1️⃣ Acessar URL:**
- Frontend: https://marinhothiago.github.io/desafio-participa-df/
- Backend: https://marinhothiago-participa-df-pii.hf.space/

**2️⃣ Usar imediatamente:**
- Colar texto na interface
- Clicar "Analisar"
- Aguardar resposta (primeira requisição pode demorar 10-20s se backend estiver "dormindo")

**Características:**
- ✅ Zero instalação
- ✅ Funciona em qualquer máquina com browser
- ✅ Dados não são salvos no servidor
- ⚠️ Primeira requisição pode demorar (cold start do HuggingFace Spaces)

**Tempo Total:** <30 segundos

---

### 📊 Comparativo Detalhado

```
CENÁRIO 1: NATIVO
├─ Setup: 15 min (primeira) + 1 min (próximas)
├─ Performance: Ultra-rápido (modelo carregado em memória)
├─ Debugging: Excelente (logs em tempo real, hot reload)
└─ Custo: 0 (sua máquina)

CENÁRIO 2: DOCKER ⭐ RECOMENDADO
├─ Setup: 5 min (primeira, com download) + <30s (próximas)
├─ Performance: Rápido (container isolado)
├─ Isolamento: Perfeito (não afeta SO)
├─ Reprodutibilidade: Garantida (mesma imagem para todos)
└─ Custo: Espaço disco (~2.5GB)

CENÁRIO 3: ONLINE
├─ Setup: 0 min (apenas acesso link)
├─ Performance: Variável (depende de latência + cold start HF)
├─ Isolamento: N/A (servidor remoto)
└─ Custo: 0 (hospedagem gratuita HuggingFace Spaces)
```

---

### ✅ Validação de Sucesso

Após escolher um cenário, você saberá que funcionou quando:

**✅ Backend rodando:**
```bash
GET http://localhost:8000/health  (ou :7860 em Docker)
Resposta esperada: {"status": "ok"}
```

**✅ Frontend conectado:**
- Console do browser sem erros (F12 → Console)
- Botão "Analisar" ativo (não desabilitado)
- Indicador de status verde (ApiStatus component)

**✅ Análise funcionando:**
1. Cole texto: `"CPF: 123.456.789-09"`
2. Clique "Analisar"
3. Esperado em <2s: 
   - Campo marcado como PII
   - Risco: "CRÍTICO"
   - Confiança: >0.95

---

## 🛠️ Tecnologias

- **Backend:** FastAPI, spaCy (NLP PT), Transformers (BERT), Python 3.10+
- **Frontend:** React 18, Vite, Tailwind CSS, Shadcn/UI, Recharts
- **Deploy:** Docker (HuggingFace), GitHub Pages

- **Processamento Efêmero:** Nenhum dado pessoal é armazenado no banco de dados após a análise
- **Anonimização em Lote:** Capacidade de processar grandes volumes de arquivos CSV/XLSX preservando o ID original para auditoria

---

## 👨‍💻 Desenvolvedor

Thiago Marinho - Desenvolvido para o Desafio Participa-DF (Hackathon CGDF)
