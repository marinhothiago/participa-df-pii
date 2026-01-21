# 🎨 Frontend: Dashboard Participa DF

[![React](https://img.shields.io/badge/React-18.3.1-61DAFB?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8.3-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4.19-646CFF?logo=vite)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4.17-06B6D4?logo=tailwindcss)](https://tailwindcss.com/)
[![Shadcn/UI](https://img.shields.io/badge/Shadcn%2FUI-latest-000000)](https://ui.shadcn.com/)

> **Interface React para análise de privacidade** em manifestações do Participa DF, seguindo o padrão visual DSGOV (Gov.br).

| 🌐 **Links de Produção** | URL |
|--------------------------|-----|
| Frontend (Dashboard) | https://marinhothiago.github.io/desafio-participa-df/ |
| Backend (API) | https://marinhothiago-desafio-participa-df.hf.space/ |

---

## 📋 Índice

1. [Funcionalidades](#-funcionalidades)
2. [Instalação](#1️⃣-instalação)
3. [Execução](#2️⃣-execução)
4. [Arquitetura](#3️⃣-arquitetura)
5. [Páginas e Componentes](#4️⃣-páginas-e-componentes)
6. [Integração com Backend](#5️⃣-integração-com-backend)
7. [Design System DSGOV](#6️⃣-design-system-dsgov)
8. [Estrutura de Arquivos](#7️⃣-estrutura-de-arquivos)
9. [Deploy](#8️⃣-deploy)

---

## 🚀 Funcionalidades

### Interface Principal

| Feature | Descrição |
|---------|-----------|
| ✅ **Análise Individual** | Testar textos e visualizar PIIs detectados em tempo real |
| ✅ **Processamento em Lote** | Upload de arquivos CSV/XLSX com relatório automático |
| ✅ **Dashboard de Métricas** | KPIs e histórico de análises realizadas |
| ✅ **Exportação de Dados** | Download de resultados em JSON |
| ✅ **Explicabilidade (XAI)** | Tooltips com justificativa detalhada de cada detecção |
| ✅ **5 Níveis de Risco** | CRÍTICO, ALTO, MODERADO, BAIXO, SEGURO com cores |
| ✅ **Responsivo** | Menu hambúrguer em dispositivos móveis |
| ✅ **Design DSGOV** | Interface seguindo padrão federal brasileiro (Gov.br) |

### Novidades v9.6.0

- 🔍 **Tooltips XAI**: Ícone ℹ️ mostra motivos, fontes e validações de cada PII
- 📊 **Benchmarks Atualizados**: Exibe F1-Score 100%, precisão e recall no Dashboard
- 🏛️ **Links CGDF**: Rodapé com links para Controladoria e LinkedIn do autor
- 🔗 **Link da API**: Status da conexão agora mostra link para a documentação Swagger

---

## 1️⃣ Instalação

### Pré-requisitos

| Software | Versão | Verificar |
|----------|--------|-----------|
| Node.js | 18.0+ | `node --version` |
| npm | 9.0+ | `npm --version` |

**Alternativa:** [Bun](https://bun.sh/) 1.0+ (mais rápido que npm)

### Instalação Passo a Passo

```bash
# 1. Entre na pasta frontend
cd desafio-participa-df/frontend

# 2. Instale todas as dependências
npm install

# Ou com Bun (mais rápido):
# bun install
```

**Tempo estimado:** 1-2 minutos

---

## 2️⃣ Execução

### Servidor de Desenvolvimento

```bash
cd frontend
npm run dev
```

**Saída esperada:**
```
  VITE v5.4.19  ready in 500 ms

  ➜  Local:   http://localhost:8080/
  ➜  Network: use --host to expose
```

**Acesse:** http://localhost:8080

### Build de Produção

```bash
# Gera arquivos otimizados em /dist
npm run build

# Prévia do build
npm run preview
```

### Docker

```bash
# Na pasta frontend/
docker build -t participa-df-frontend .
docker run -p 3000:80 participa-df-frontend
```

**Acesse:** http://localhost:3000

### Linting

```bash
npm run lint
```

---

## 3️⃣ Arquitetura

### Visão Geral

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                   │
│                   http://localhost:8080                      │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Pages (Páginas):                                       │ │
│  │  • Dashboard.tsx    → Visão geral com KPIs            │ │
│  │  • Classification.tsx → Análise individual + lote     │ │
│  │  • Documentation.tsx  → Guia de uso integrado         │ │
│  │  • NotFound.tsx       → Página 404                    │ │
│  └────────────────────────────────────────────────────────┘ │
│          │                                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Components (14 reutilizáveis):                         │ │
│  │  • Header.tsx         → Logo DSGOV + Menu             │ │
│  │  • KPICard.tsx        → Cards de métricas             │ │
│  │  • ConfidenceBar.tsx  → Barra visual 0-100%          │ │
│  │  • FileDropzone.tsx   → Upload drag & drop            │ │
│  │  • RiskThermometer.tsx→ Termômetro de risco          │ │
│  │  • ApiStatus.tsx      → Indicador de conexão         │ │
│  │  • FooterWithCounters.tsx → Rodapé com contadores    │ │
│  │  • ui/*               → Shadcn UI components          │ │
│  └────────────────────────────────────────────────────────┘ │
│          │                                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ State Management (Context API):                        │ │
│  │  • AnalysisContext.tsx → Histórico de análises        │ │
│  │  • Métricas globais (KPIs)                            │ │
│  │  • useAnalysis() hook                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│          │                                                   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                  POST /analyze
                  GET /health
                  GET /stats
                         │
                         ▼
              Backend (FastAPI v9.6.0)
              Port 7860 (local)
              ou HuggingFace Spaces
```

### Tecnologias Utilizadas

| Tecnologia | Versão | Função |
|------------|--------|--------|
| React | 18.3.1 | Biblioteca UI |
| TypeScript | 5.8.3 | Tipagem estática |
| Vite | 5.4.19 | Build tool ultra-rápido |
| TailwindCSS | 3.4.17 | Estilização (Design DSGOV) |
| Shadcn/UI | latest | Componentes acessíveis |
| React Query | 5.83.0 | Cache e estado de requisições |
| Recharts | 2.15.4 | Gráficos e visualizações |
| XLSX | 0.18.5 | Parser de arquivos Excel |
| Lucide React | 0.462.0 | Ícones |
| Zod | 3.25.76 | Validação de schemas |

---

## 4️⃣ Páginas e Componentes

### Dashboard (`/`)

Página inicial com visão geral:

- **KPI Cards**: Total de análises, textos públicos, textos restritos
- **Benchmarks**: F1-Score 100%, Precisão 100%, Recall 100%
- **Conformidade LGPD**: Texto explicativo sobre a solução
- **Histórico**: Últimas 10 análises com XAI tooltips
- **Status da API**: Indicador de conexão com link para docs

### Classification (`/classificacao`)

Página de análise de textos:

#### Análise Individual
1. Digite ou cole o texto no campo
2. Clique em "Analisar"
3. Veja o resultado com:
   - Classificação (PÚBLICO/NÃO PÚBLICO)
   - Nível de risco (cores visuais)
   - Score de confiança (0-100%)
   - Lista de PIIs detectados com **tooltips XAI**

#### Processamento em Lote
1. Arraste um arquivo CSV/XLSX para a área de upload
2. O arquivo deve ter coluna `Texto Mascarado` ou `text`
3. Clique em "Processar Lote"
4. Acompanhe o progresso
5. Exporte os resultados em JSON

### Documentation (`/documentacao`)

Guia de uso integrado:
- Como usar o sistema
- Tipos de PII detectados
- Níveis de risco explicados
- FAQ

### Componentes Principais

| Componente | Função |
|------------|--------|
| `Header.tsx` | Cabeçalho DSGOV com navegação e menu mobile |
| `KPICard.tsx` | Card de métrica individual |
| `ConfidenceBar.tsx` | Barra visual de confiança (0-100%) |
| `FileDropzone.tsx` | Upload drag & drop (CSV/XLSX) |
| `RiskThermometer.tsx` | Termômetro visual de risco |
| `ApiStatus.tsx` | Indicador de conexão com backend |
| `FooterWithCounters.tsx` | Rodapé com contadores globais e links |
| `TrainingStatus.tsx` | Status do modelo de IA |
| `ExportButton.tsx` | Botão de exportação JSON |
| `IdentifierBadge.tsx` | Badge de tipo de PII |

---

## 5️⃣ Integração com Backend

### Detecção Automática

O frontend detecta automaticamente se o backend está rodando localmente:

```typescript
// src/lib/api.ts
const PRODUCTION_API_URL = 'https://marinhothiago-desafio-participa-df.hf.space';
const LOCAL_API_URL = 'http://localhost:7860';

// Tenta detectar backend local em 2 segundos
// Se não encontrar, usa HuggingFace Spaces
```

### Formato de Resposta (API v2)

O frontend consome exclusivamente o novo formato estruturado:

```typescript
interface AnalyzeResponse {
  id?: string;
  has_pii: boolean;
  classificacao: "PÚBLICO" | "NÃO PÚBLICO";
  risco: "SEGURO" | "BAIXO" | "MODERADO" | "ALTO" | "CRÍTICO";
  confianca: number; // 0.0 a 1.0
  entities: Array<{
    tipo: string;
    valor: string;
    confianca: number;
    fonte?: string;
    explicacao?: {
      motivos: string[];
      fontes: string[];
      validacoes: string[];
      contexto: string[];
      confianca_percent: string;
      peso: number;
    };
  }>;
  risk_level: string;
  confidence_all_found: number;
  total_entities: number;
  sources_used: string[];
}
```

### Tratamento de Erros

```typescript
export type ApiErrorType = 'TIMEOUT' | 'OFFLINE' | 'WAKING_UP' | 'CORS' | 'UNKNOWN';

// Mensagens amigáveis
switch (error.type) {
  case 'WAKING_UP':
    return 'O motor de IA está acordando, aguarde...';
  case 'TIMEOUT':
    return 'API demorou muito. Tente novamente.';
  case 'OFFLINE':
    return 'Sem conexão com a API.';
}
```

### Contadores Globais

O frontend sincroniza contadores com o backend:

```typescript
// GET /stats - Retorna contadores
// POST /stats/visit - Registra visita (1x por sessão)
```

---

## 6️⃣ Design System DSGOV

O projeto segue o **Design System do Governo Federal (DSGOV)**:

### Cores

```typescript
// tailwind.config.ts
colors: {
  'gov-blue': {
    DEFAULT: '#1351B4',
    light: '#2670E8',
    dark: '#0C326F'
  },
  'gov-green': {
    DEFAULT: '#168821',
    light: '#00A91C'
  },
  'gov-yellow': {
    DEFAULT: '#FFCD07'
  },
  'gov-red': {
    DEFAULT: '#E52207'
  }
}
```

### Cores de Risco

| Nível | Cor | Hex |
|-------|-----|-----|
| 🟢 SEGURO | Verde | `#22c55e` |
| 🔵 BAIXO | Azul | `#3b82f6` |
| 🟡 MODERADO | Amarelo | `#eab308` |
| 🟠 ALTO | Laranja | `#f97316` |
| 🔴 CRÍTICO | Vermelho | `#ef4444` |

### Tipografia

- **Fonte:** Rawline (Gov.br) com fallback para system fonts
- **Tamanhos:** Scale consistente (xs, sm, base, lg, xl, 2xl)

### Acessibilidade

Todos os componentes UI usam **Radix UI** para garantir:
- ✅ Navegação por teclado
- ✅ Suporte a screen readers
- ✅ ARIA labels corretos
- ✅ Contraste adequado (WCAG AA)

---

## 7️⃣ Estrutura de Arquivos

```
frontend/
├── README.md                    ← ESTE ARQUIVO
├── package.json                 ← Dependências npm
├── package-lock.json            ← Lock de versões
│
├── vite.config.ts               ← Configuração do build (Vite 5.x)
├── tsconfig.json                ← Configuração TypeScript
├── tailwind.config.ts           ← Design System DSGOV (cores, fontes)
├── postcss.config.js            ← PostCSS para TailwindCSS
├── eslint.config.js             ← Regras de linting
├── components.json              ← Configuração Shadcn UI
│
├── index.html                   ← Entry point HTML
├── Dockerfile                   ← Container com nginx
├── nginx.conf                   ← Configuração nginx para SPA
│
├── public/
│   ├── robots.txt               ← SEO
│   └── 404.html                 ← Fallback para SPA routing
│
└── src/
    ├── main.tsx                 ← Entry point React
    ├── App.tsx                  ← Router + Layout principal
    ├── App.css                  ← Estilos globais do App
    ├── index.css                ← Reset + variáveis CSS + DSGOV
    ├── vite-env.d.ts            ← Tipos Vite
    │
    ├── pages/                   ← Páginas da aplicação
    │   ├── Index.tsx            ← Redireciona para Dashboard
    │   ├── Dashboard.tsx        ← Página inicial com KPIs
    │   ├── Classification.tsx   ← Análise de textos (700+ linhas)
    │   ├── Documentation.tsx    ← Guia de uso
    │   └── NotFound.tsx         ← Página 404
    │
    ├── components/              ← Componentes reutilizáveis
    │   ├── ui/                  ← Shadcn UI (30+ componentes)
    │   │   ├── button.tsx
    │   │   ├── card.tsx
    │   │   ├── dialog.tsx
    │   │   ├── table.tsx
    │   │   ├── tooltip.tsx
    │   │   └── ...
    │   │
    │   ├── Header.tsx           ← Cabeçalho DSGOV
    │   ├── KPICard.tsx          ← Card de métrica
    │   ├── ConfidenceBar.tsx    ← Barra de confiança
    │   ├── FileDropzone.tsx     ← Upload drag & drop
    │   ├── RiskThermometer.tsx  ← Termômetro de risco
    │   ├── ApiStatus.tsx        ← Indicador de conexão
    │   ├── ApiWakingUpMessage.tsx ← Mensagem de cold start
    │   ├── FooterWithCounters.tsx ← Rodapé com contadores
    │   ├── TrainingStatus.tsx   ← Status do modelo
    │   ├── ExportButton.tsx     ← Exportação JSON
    │   ├── IdentifierBadge.tsx  ← Badge de PII
    │   ├── DistributionChart.tsx← Gráfico de distribuição
    │   ├── PIITypesChart.tsx    ← Gráfico de tipos de PII
    │   └── RiskDistributionChart.tsx ← Gráfico de risco
    │
    ├── lib/                     ← Utilitários e serviços
    │   ├── api.ts               ← Cliente HTTP para backend (400+ linhas)
    │   │                          - Detecção automática de backend local
    │   │                          - Retry com exponential backoff
    │   │                          - Tratamento de erros
    │   │                          - Interfaces TypeScript
    │   │
    │   ├── fileParser.ts        ← Parser de CSV/XLSX
    │   ├── validateBatchFile.ts ← Validação de arquivos
    │   └── utils.ts             ← cn() e funções auxiliares
    │
    ├── contexts/                ← Estado global
    │   └── AnalysisContext.tsx  ← Histórico e métricas
    │
    └── hooks/                   ← Custom hooks
        ├── use-mobile.tsx       ← Detecta dispositivo mobile
        └── use-toast.ts         ← Notificações toast
```

---

## 8️⃣ Deploy

### GitHub Pages (Produção)

O deploy é automático via GitHub Actions ao fazer push na branch `main`:

```bash
cd frontend
npm run build
git push origin main
```

### Docker

```dockerfile
# Stage 1: Build com Node.js
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve com nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### nginx.conf para SPA

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # Fallback para React Router
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache de assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 🧪 Testes Manuais

### Teste Individual
1. Acesse http://localhost:8080
2. Na página Classification, digite: `Meu CPF é 123.456.789-09`
3. Clique "Analisar"
4. **Esperado:** Classificação "NÃO PÚBLICO", Risco "CRÍTICO", Tooltip XAI

### Teste de Lote
1. Crie um arquivo `teste.csv`:
```csv
ID,Texto Mascarado
1,"Solicito informações."
2,"Meu CPF é 529.982.247-25"
```
2. Arraste para a área de upload
3. Clique "Processar Lote"
4. **Esperado:** Item 1 PÚBLICO, Item 2 NÃO PÚBLICO

### Teste de Conexão
1. Inicie o backend local (`uvicorn api.main:app --port 7860`)
2. Recarregue o frontend
3. **Esperado:** Console mostra "✅ Backend local detectado!"

---

## 📄 Licença

Desenvolvido para o **Hackathon Participa DF 2026** em conformidade com:
- **LGPD** - Lei Geral de Proteção de Dados (Lei nº 13.709/2018)
- **LAI** - Lei de Acesso à Informação (Lei nº 12.527/2011)

---

## 🔗 Relacionado

- **Backend (Motor de IA):** [../backend/README.md](../backend/README.md)
- **Projeto Completo:** [../README.md](../README.md)
