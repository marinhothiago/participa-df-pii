# 🛡️ Participa DF - Detector Inteligente de Dados Pessoais

[![Status](https://img.shields.io/badge/Status-Produção-brightgreen)](https://marinhothiago.github.io/desafio-participa-df/)
[![Versão](https://img.shields.io/badge/Versão-9.2-blue)](./backend/README.md)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow?logo=python)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev/)
[![F1--Score](https://img.shields.io/badge/F1--Score-1.0000-success)](./backend/benchmark.py)
[![Licença](https://img.shields.io/badge/Licença-LGPD%2FLAI-green)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

> **Motor híbrido de detecção de Informações Pessoais Identificáveis (PII)** para conformidade com LGPD e LAI em manifestações do Participa DF.
> 
> � **v9.2**: Sistema otimizado com **F1-Score = 1.0000** (100% precisão e sensibilidade) em benchmark de 303 casos LGPD.

| 🌐 **Links de Produção** | URL |
|--------------------------|-----|
| Frontend (Dashboard) | https://marinhothiago.github.io/desafio-participa-df/ |
| Backend (API) | https://marinhothiago-desafio-participa-df.hf.space/ |
| Documentação da API | https://marinhothiago-desafio-participa-df.hf.space/docs |
| Health Check | https://marinhothiago-desafio-participa-df.hf.space/health |

---

## 📋 Objetivo da Solução

O **Participa DF - PII Detector** é um sistema completo para **detectar, classificar e avaliar o risco de vazamento de dados pessoais** em textos de manifestações públicas do Governo do Distrito Federal.

### Problema Resolvido

O GDF precisa publicar manifestações de cidadãos em transparência ativa (LAI) sem violar a privacidade garantida pela LGPD. Este sistema automatiza a detecção de:

- **CPF, RG, CNH, Passaporte, PIS, CNS** (documentos de identificação)
- **Email, Telefone, Celular** (dados de contato)
- **Endereços residenciais, CEP** (localização)
- **Nomes pessoais** (com análise de contexto)
- **Dados bancários, PIX, Cartão de Crédito** (informações financeiras)
- **Placas de veículos, Processos judiciais** (outros identificadores)

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
│  │ Motor Híbrido de Detecção PII (v9.2 - 2100+ linhas)    │ │
│  │                                                         │ │
│  │ 1. REGEX + Validação DV (CPF, CNPJ, PIS, CNS, CNH)    │ │
│  │ 2. BERT NER Multilíngue (detector primário de nomes)   │ │
│  │ 3. spaCy pt_core_news_lg (NER complementar)            │ │
│  │ 4. Regras de Negócio (imunidade funcional, contexto)   │ │
│  │ 5. Confiança Probabilística (isotônico + log-odds)     │ │
│  │                                                         │ │
│  │ Estratégia: Ensemble OR (alta recall para LGPD)        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura do Projeto e Função de Cada Arquivo

```
desafio-participa-df/
│
├── README.md                     ← ESTE ARQUIVO: Visão geral do projeto
├── docker-compose.yml            ← Orquestração: backend + frontend
├── app.py                        ← Entry point para HuggingFace Spaces
├── deploy-hf.sh                  ← Script de deploy para HuggingFace
│
├── backend/                      ← 🐍 MOTOR DE IA (Python + FastAPI)
│   ├── README.md                 ← Documentação técnica do backend
│   ├── requirements.txt          ← Dependências Python (pip install)
│   ├── Dockerfile                ← Container para deploy
│   │
│   ├── api/
│   │   └── main.py               ← FastAPI: endpoints /analyze e /health
│   │
│   ├── src/
│   │   ├── detector.py           ← Motor híbrido PII v9.2 (2100+ linhas)
│   │   ├── allow_list.py         ← Lista de termos seguros (GDF, órgãos)
│   │   └── confidence/           ← Módulo de confiança probabilística
│   │       ├── types.py          ← Dataclasses: PIIEntity, DocumentConfidence
│   │       ├── config.py         ← FN/FP rates, pesos LGPD, thresholds
│   │       ├── validators.py     ← Validação DV (CPF, CNPJ, PIS, CNS)
│   │       ├── calibration.py    ← Calibrador isotônico (sklearn)
│   │       ├── combiners.py      ← Combinação log-odds (Naive Bayes)
│   │       └── calculator.py     ← Orquestrador de confiança
│   │
│   ├── main_cli.py               ← CLI: processamento em lote via terminal
│   ├── benchmark.py              ← 🏆 Benchmark LGPD: 303 casos, F1=1.0
│   ├── test_confidence.py        ← Testes do sistema de confiança
│   │
│   └── data/
│       ├── input/                ← Arquivos CSV/XLSX para processar
│       └── output/               ← Relatórios gerados (JSON, CSV, XLSX)
│
└── frontend/                     ← ⚛️ INTERFACE WEB (React + TypeScript)
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
    │   ├── components/           ← Componentes reutilizáveis (20+)
    │   │   ├── ui/               ← Shadcn UI (buttons, cards, etc)
    │   │   ├── Header.tsx        ← Cabeçalho DSGOV
    │   │   ├── KPICard.tsx       ← Cards de métricas
    │   │   ├── ResultsTable.tsx  ← Tabela de resultados
    │   │   ├── FileDropzone.tsx  ← Upload drag & drop
    │   │   ├── ConfidenceBar.tsx ← Barra visual de confiança
    │   │   ├── RiskThermometer.tsx ← Termômetro de risco
    │   │   └── ...
    │   │
    │   ├── lib/
    │   │   ├── api.ts            ← Cliente HTTP para backend
    │   │   ├── fileParser.ts     ← Parser de CSV/XLSX
    │   │   └── utils.ts          ← Funções utilitárias
    │   │
    │   ├── contexts/
    │   │   └── AnalysisContext.tsx ← Estado global (histórico)
    │   │
    │   └── hooks/
    │       └── use-toast.ts      ← Notificações
    │
    └── public/
        ├── robots.txt            ← SEO
        └── 404.html              ← Fallback SPA
```

---

## 1️⃣ INSTRUÇÕES DE INSTALAÇÃO E DEPENDÊNCIAS

### 1.1 Pré-requisitos

| Software | Versão Mínima | Verificar Instalação | Como Instalar |
|----------|---------------|---------------------|---------------|
| **Python** | 3.10+ | `python --version` | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18.0+ | `node --version` | [nodejs.org](https://nodejs.org/) |
| **npm** | 9.0+ | `npm --version` | Incluído com Node.js |
| **Git** | 2.0+ | `git --version` | [git-scm.com](https://git-scm.com/) |
| **Docker** (opcional) | 20.0+ | `docker --version` | [docker.com](https://www.docker.com/) |

### 1.2 Arquivos de Gerenciamento de Pacotes

O projeto utiliza **dois** sistemas de dependências:

#### Backend: `backend/requirements.txt`

```txt
# Framework Web
fastapi==0.110.0
uvicorn==0.27.1
python-multipart==0.0.9

# NLP Core
spacy==3.8.0
transformers==4.41.2
sentencepiece==0.1.99
accelerate>=0.21.0

# Processamento de Dados
pandas==2.2.1
openpyxl==3.1.2
text-unidecode==1.3

# PyTorch CPU (instalado separadamente)
# torch==2.1.0+cpu
```

#### Frontend: `frontend/package.json`

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.30.1",
    "typescript": "^5.8.3",
    "vite": "^5.4.19",
    "tailwindcss": "^3.4.17",
    "@tanstack/react-query": "^5.83.0",
    "recharts": "^2.15.4",
    "lucide-react": "^0.462.0",
    "xlsx": "^0.18.5",
    "zod": "^3.25.76"
  }
}
```

### 1.3 Instalação Completa (Passo a Passo)

#### Opção A: Instalação Manual (Desenvolvimento)

```bash
# 1. Clone o repositório
git clone https://github.com/marinhothiago/desafio-participa-df.git
cd desafio-participa-df

# ========== BACKEND ==========
cd backend

# 2. Crie ambiente virtual Python
python -m venv venv

# 3. Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instale PyTorch CPU (antes das outras dependências)
pip install torch==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu

# 5. Instale todas as dependências do backend
pip install -r requirements.txt

# 6. Baixe o modelo spaCy para português (obrigatório)
python -m spacy download pt_core_news_lg

# ========== FRONTEND ==========
cd ../frontend

# 7. Instale dependências do frontend
npm install
```

#### Opção B: Docker Compose (Produção - Recomendado)

```bash
# Clone o repositório
git clone https://github.com/marinhothiago/desafio-participa-df.git
cd desafio-participa-df

# Suba todos os serviços (backend + frontend)
docker-compose up -d

# Verifique se está rodando
docker-compose ps
```

---

## 2️⃣ INSTRUÇÕES DE EXECUÇÃO

### 2.1 Execução Local (Desenvolvimento)

Abra **dois terminais** side-by-side:

#### Terminal 1: Backend (Motor de IA)

```bash
cd backend

# Ative o ambiente virtual (se não estiver ativo)
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Inicie o servidor FastAPI
uvicorn api.main:app --host 0.0.0.0 --port 7860 --reload
```

**Endpoints disponíveis:**
- API: http://localhost:7860
- Documentação Swagger: http://localhost:7860/docs
- Health Check: http://localhost:7860/health

#### Terminal 2: Frontend (Interface)

```bash
cd frontend

# Inicie o servidor de desenvolvimento
npm run dev
```

**Acesse:** http://localhost:8080

#### CLI: Processamento em Lote

```bash
cd backend

# Ative o ambiente virtual
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Processe um arquivo CSV ou XLSX
python main_cli.py --input data/input/manifestacoes.xlsx --output data/output/resultado
```

**Saídas geradas (mesma estrutura de colunas nos 3 formatos):**
| Arquivo | Formato | Uso |
|---------|---------|-----|
| `resultado.json` | JSON | Integração com sistemas |
| `resultado.csv` | CSV | Importação em ferramentas |
| `resultado.xlsx` | Excel | Análise visual com cores |

**Colunas:** ID → Texto Mascarado → Classificação → Confiança → Nível de Risco → Identificadores

### 2.2 Execução com Docker

```bash
# Suba os serviços
docker-compose up -d

# Acompanhe os logs
docker-compose logs -f

# Pare os serviços
docker-compose down
```

**Portas:**
- Backend: http://localhost:7860
- Frontend: http://localhost:3000

### 2.3 Formato de Dados

#### Entrada (POST /analyze)

```json
{
  "text": "Meu CPF é 123.456.789-09 e preciso de ajuda.",
  "id": "manifestacao_001"
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `text` | string | ✅ Sim | Texto a ser analisado |
| `id` | string | ❌ Não | ID para rastreabilidade (preservado na saída) |

#### Saída

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

| Campo | Tipo | Valores Possíveis | Descrição |
|-------|------|-------------------|-----------|
| `id` | string | qualquer | ID da requisição (preservado) |
| `classificacao` | string | "PÚBLICO", "NÃO PÚBLICO" | Se pode ou não publicar |
| `risco` | string | SEGURO, BAIXO, MODERADO, ALTO, CRÍTICO | Nível de severidade |
| `confianca` | float | 0.0 a 1.0 | Score de certeza do modelo |
| `detalhes` | array | lista de objetos | PIIs encontrados com tipo e valor |

#### Formato de Arquivo em Lote (CSV/XLSX)

O arquivo deve conter uma coluna chamada `Texto Mascarado` (ou `text`) e opcionalmente `ID`:

```csv
ID,Texto Mascarado
man_001,"Solicito informações sobre minha situação cadastral."
man_002,"Meu CPF é 123.456.789-09 e preciso de ajuda urgente."
man_003,"Email para contato: joao.silva@gmail.com"
```

---

## 3️⃣ CLAREZA E ORGANIZAÇÃO

### 3.1 Código Fonte Comentado

O código-fonte possui comentários detalhados em trechos complexos. Exemplos:

#### Motor Principal (`backend/src/detector.py` - 1016 linhas)

```python
class PIIDetector:
    """Detector híbrido de PII com ensemble de alta recall.
    
    Estratégia: Ensemble OR - qualquer detector positivo classifica como PII.
    Isso maximiza recall (não deixar escapar nenhum PII) às custas de alguns
    falsos positivos, que é a estratégia correta para LAI/LGPD.
    """

    def detect(self, text: str) -> Tuple[bool, List[Dict], str, float]:
        """Detecta PII no texto usando ensemble de alta recall.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Tuple contendo:
            - is_pii (bool): True se contém PII
            - findings (List[Dict]): Lista de PIIs encontrados
            - nivel_risco (str): CRITICO, ALTO, MODERADO, BAIXO ou SEGURO
            - confianca (float): Score de confiança 0-1
        """
        # 1. Regex com validação de DV (mais preciso para documentos)
        regex_findings = self._detectar_regex(text)
        
        # 2. Nomes após gatilhos de contato (sempre PII)
        gatilho_findings = self._extrair_nomes_gatilho(text)
        
        # 3. NER com BERT (primário) + spaCy (complementar)
        ner_findings = self._detectar_ner(text)
        
        # Ensemble OR: combina todos os achados com deduplicação
        # ...
```

#### Arquitetura NER Dual (BERT + spaCy)

O sistema utiliza **dois modelos NER em paralelo** para maximizar recall:

| Modelo | Função | Threshold | Justificativa |
|--------|--------|-----------|---------------|
| **BERT NER** (Davlan/bert-base-multilingual-cased-ner-hrl) | Detector **primário** | score > 0.75 | Multilíngue, mais preciso, usa confiança própria do modelo |
| **spaCy** (pt_core_news_lg) | Detector **complementar** | confiança fixa 0.80 | Nativo PT-BR, captura nomes que o BERT pode perder |

```python
def _detectar_ner(self, texto: str) -> List[PIIFinding]:
    findings = []
    
    # BERT NER (primário) - roda primeiro
    if self.nlp_bert:
        entidades = self.nlp_bert(texto)
        for ent in entidades:
            if ent['entity_group'] == 'PER' and ent['score'] > 0.75:
                findings.append(PIIFinding(tipo="NOME", valor=ent['word'], ...))
    
    # spaCy NER (complementar) - adiciona nomes NÃO detectados pelo BERT
    if self.nlp_spacy:
        doc = self.nlp_spacy(texto)
        for ent in doc.ents:
            if ent.label_ == 'PER':
                # Evita duplicatas: só adiciona se BERT não encontrou
                if not any(f.valor.lower() == ent.text.lower() for f in findings):
                    findings.append(PIIFinding(tipo="NOME", valor=ent.text, ...))
    
    return findings
```

**Por que dois modelos?** A estratégia Ensemble OR garante que se o BERT perder um nome (ex: grafia incomum), o spaCy pode capturá-lo, e vice-versa. Isso maximiza recall, essencial para conformidade LGPD/LAI.

#### Sistema de Confiança Probabilística (v9.2)

O sistema calcula confiança usando **Calibração Isotônica** + **Log-Odds (Naive Bayes)**:

```
P(PII|evidências) = calibração_isotônica(score_raw) → combinação_log_odds(fontes)
```

**Pipeline de Confiança:**

```
┌─────────────────────────────────────────────────────────────┐
│  1. COLETA: Detecções de múltiplas fontes                   │
│     • BERT NER → score 0.92, tipo="NOME"                   │
│     • spaCy → score 0.85, tipo="NOME"                      │
│     • Regex → match, tipo="CPF"                            │
│     • DV Validation → válido (0.9999)                      │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. CALIBRAÇÃO: Isotônica (sklearn) ou conservadora         │
│     • BERT 0.92 → calibrado 0.87 (ajuste por FN/FP rate)   │
│     • spaCy 0.85 → calibrado 0.75                          │
│     • Regex → probabilidade baseada em FP rate             │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. COMBINAÇÃO: Log-Odds (Naive Bayes)                      │
│     log_odds = Σ log(P/(1-P)) por fonte                    │
│     → Múltiplas fontes concordando = confiança maior       │
│     → CPF (regex) + DV válido = confiança ~0.9999          │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. MÉTRICAS DE DOCUMENTO                                   │
│     • confidence_min_entity: menor confiança individual    │
│     • confidence_all_found: P(encontramos todos os PIIs)   │
│     • confidence_no_pii: P(texto não contém PII)           │
└─────────────────────────────────────────────────────────────┘
```

**Taxas FN/FP Calibradas por Fonte:**

| Fonte | FN Rate | FP Rate | Justificativa |
|-------|---------|---------|---------------|
| BERT NER | 0.008 | 0.02 | Modelo multilíngue robusto |
| spaCy | 0.015 | 0.03 | Modelo nativo PT complementar |
| Regex | 0.003 | 0.0002 | Padrões determinísticos precisos |
| DV Validation | 0.0001 | 0.00001 | Validação matemática (quase perfeita) |

**Exemplos de Confiança Combinada:**

| Cenário | Fontes | Confiança Final |
|---------|--------|-----------------|
| CPF válido (regex + DV) | regex + dv_validation | 0.9999 |
| Nome detectado (BERT + spaCy) | bert_ner + spacy | 0.94 |
| Telefone (apenas regex) | regex | 0.85 |
| CPF inválido (falhou DV) | - | Descartado |

**Confiança Base por Método (fallback):**

| Categoria | Tipos | Base | Justificativa |
|-----------|-------|------|---------------|
| Regex + DV | CPF, PIS, CNS, CNH, Título | 0.98 | Validação matemática (Módulo 11) |
| Regex + Luhn | Cartão Crédito | 0.95 | Algoritmo Luhn válido |
| Regex Estrutural | Email, Telefone, Placa | 0.85-0.95 | Padrão claro, sem validação |
| BERT NER | Nomes | score modelo | Retorna confiança própria (0.75-0.99) |
| spaCy NER | Nomes | 0.70 | Modelo menor, complementar |
| Gatilho | Nomes após "falar com" | 0.85 | Padrão linguístico forte |

**Fatores de Contexto (Boost/Penalidade):**

| Fator | Ajuste | Exemplo |
|-------|--------|---------|
| Possessivo ("meu", "minha") | +15% | "Meu CPF é..." → boost |
| Label explícito ("CPF:") | +10% | "CPF: 529..." → boost |
| Gatilho de contato | +10% | "falar com João" → boost |
| Contexto de teste | -25% | "exemplo: 000..." → penalidade |
| Declarado fictício | -30% | "CPF fictício..." → ignora |
| Negação antes | -20% | "não é meu CPF" → penalidade |

**Exemplos Práticos:**

| Texto | Base | Fator | Final |
|-------|------|-------|-------|
| "Meu CPF: 529.982.247-25" | 0.98 | 1.25 | **1.00** |
| "CPF 529.982.247-25" | 0.98 | 1.00 | **0.98** |
| "exemplo CPF: 529..." | 0.98 | 0.75 | **ignorado** |
| "falar com João Silva" | 0.85 | 1.10 | **0.94** |

#### API (`backend/api/main.py`)

```python
@app.post("/analyze")
async def analyze(data: Dict[str, Optional[str]]) -> Dict:
    """Analisa texto para detecção de PII com contexto Brasília/GDF.
    
    Realiza detecção híbrida usando:
    - Regex: Padrões estruturados (CPF, Email, Telefone, RG, CNH)
    - NLP: Reconhecimento de entidades com spaCy + BERT
    - Regras de Negócio: Contexto de Brasília, imunidade funcional (LAI)
    
    Classificações de Risco:
        - CRÍTICO (5): CPF, RG, CNH (identificação direta)
        - ALTO (4): Email privado, Telefone, Nome, Endereço
        - MODERADO (3): Entidade nomeada genérica
        - SEGURO (0): Sem PII detectado
    """
```

### 3.2 Estrutura Lógica do Projeto

| Pasta | Responsabilidade |
|-------|------------------|
| `backend/api/` | Endpoints HTTP (FastAPI) |
| `backend/src/` | Lógica de negócio (detector PII) |
| `backend/data/` | Entrada/saída de arquivos |
| `frontend/src/pages/` | Páginas da aplicação |
| `frontend/src/components/` | Componentes reutilizáveis |
| `frontend/src/lib/` | Utilitários e cliente API |
| `frontend/src/contexts/` | Estado global (React Context) |

### 3.3 Tecnologias Utilizadas

#### Backend (Motor de IA)

| Tecnologia | Versão | Função |
|------------|--------|--------|
| Python | 3.10+ | Linguagem principal |
| FastAPI | 0.110.0 | Framework web assíncrono |
| spaCy | 3.8.0 | NLP para português (pt_core_news_lg) |
| Transformers | 4.41.2 | BERT NER multilíngue (Davlan/bert-base-multilingual-cased-ner-hrl) |
| PyTorch | 2.1.0 | Deep learning (CPU) |
| Pandas | 2.2.1 | Processamento de dados tabulares |

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

## 🧪 Testes

```bash
cd backend

# Ative o ambiente virtual
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Execute o benchmark LGPD (303 casos)
python benchmark.py
```

O arquivo `benchmark.py` contém **303 casos de teste LGPD** com **F1-Score = 1.0000** cobrindo:
- ✅ Situações seguras (não PII) - textos administrativos
- ✅ PII clássico (CPF, Email, Telefone, RG, CNH)
- ✅ Edge cases e contexto específico de Brasília/GDF
- ✅ Imunidade funcional de servidores públicos (LAI)
- ✅ Gatilhos de contato que anulam imunidade
- ✅ Documentos com validação de dígito verificador (CPF, CNPJ, PIS, CNS)

---

## 📊 Níveis de Risco

| Nível | Peso | Tipos de PII | Ação Recomendada |
|-------|------|--------------|------------------|
| 🔴 **CRÍTICO** | 5 | CPF, RG, CNH, Passaporte, PIS, CNS | ❌ Não publicar |
| 🟠 **ALTO** | 4 | Email, Telefone, Endereço, Nome completo | ❌ Não publicar |
| 🟡 **MODERADO** | 3 | Nome por IA, Placa veículo | ⚠️ Revisar manualmente |
| 🔵 **BAIXO** | 2 | Nome parcial, Data nascimento | ⚠️ Revisar contexto |
| 🟢 **SEGURO** | 0 | Nenhum PII detectado | ✅ Pode publicar |

---

## 🚀 Deploy

### Backend → HuggingFace Spaces

O backend é deployado automaticamente em HuggingFace Spaces via Docker.

```bash
# Deploy manual
./deploy-hf.sh
```

### Frontend → GitHub Pages

```bash
cd frontend

# Build de produção
npm run build

# Deploy (via GitHub Actions automático)
git push origin main
```

---

## 📚 Documentação Detalhada

- **Backend (Motor de IA):** [backend/README.md](backend/README.md)
- **Frontend (Interface):** [frontend/README.md](frontend/README.md)

---

## 👥 Equipe

Desenvolvido para o **Hackathon Participa DF 2025** em conformidade com:
- **LGPD** - Lei Geral de Proteção de Dados (Lei nº 13.709/2018)
- **LAI** - Lei de Acesso à Informação (Lei nº 12.527/2011)

---

## 📄 Licença

Este projeto está em conformidade com as diretrizes de transparência pública do Governo do Distrito Federal.
