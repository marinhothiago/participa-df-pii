# 🎨 Frontend: Dashboard Participa DF

[![React](https://img.shields.io/badge/React-18.3.1-61DAFB?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8.3-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4.19-646CFF?logo=vite)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4.17-06B6D4?logo=tailwindcss)](https://tailwindcss.com/)

> **Interface React para análise de privacidade** em pedidos de Lei de Acesso à Informação (LAI), seguindo o padrão visual DSGOV (Gov.br).

| 🌐 **Links de Produção** | URL |
|--------------------------|-----|
| Frontend (Dashboard) | https://marinhothiago.github.io/desafio-participa-df/ |
| Backend (API) | https://marinhothiago-desafio-participa-df.hf.space/ |

---

## 📋 Objetivo do Frontend

Disponibilizar uma interface web intuitiva e acessível para:

- ✅ **Análise Individual:** Testar textos e visualizar PIIs detectados em tempo real
- ✅ **Processamento em Lote:** Upload de arquivos CSV/XLSX com relatório automático
- ✅ **Dashboard de Métricas:** KPIs e histórico de análises realizadas
- ✅ **Exportação de Dados:** Download de resultados em JSON
- ✅ **Design DSGOV:** Interface seguindo padrão federal brasileiro (Gov.br)
- ✅ **Responsivo (v9.4):** Menu hambúrguer em dispositivos móveis
- ✅ **Estatísticas Globais (v9.4):** Contadores de acessos e requisições sincronizados via backend

---

## 🏗️ Arquitetura: Client-Side React

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
│          │ Usa componentes ↓                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Components (20+ reutilizáveis):                        │ │
│  │  • Header.tsx         → Logo DSGOV + Menu             │ │
│  │  • KPICard.tsx        → Cards de métricas             │ │
│  │  • ConfidenceBar.tsx  → Barra visual 0-100%          │ │
│  │  • ResultsTable.tsx   → Tabela com paginação          │ │
│  │  • FileDropzone.tsx   → Upload drag & drop            │ │
│  │  • RiskThermometer.tsx→ Termômetro de risco          │ │
│  │  • ui/*               → Shadcn UI components          │ │
│  └────────────────────────────────────────────────────────┘ │
│          │ Usa contexto e hooks ↓                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ State Management (Context API):                        │ │
│  │  • AnalysisContext.tsx → Histórico de análises        │ │
│  │  • Métricas globais (KPIs)                            │ │
│  │  • useAnalysis() hook                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│          │ HTTP requests ↓                                   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                  POST /analyze
                  GET /health
                  GET /stats
                  POST /stats/visit
                         │
                         ▼
              Backend (FastAPI)
              Port 7860 (local)
              ou HuggingFace Spaces
```

---

## 📁 Estrutura de Arquivos e Função de Cada Componente

```
frontend/
├── README.md                    ← ESTE ARQUIVO: Documentação técnica
├── package.json                 ← Dependências npm (npm install)
├── package-lock.json            ← Lock de versões
├── bun.lockb                    ← Lock para Bun (alternativo)
│
├── vite.config.ts               ← Configuração do build (Vite 5.x)
├── tsconfig.json                ← Configuração TypeScript
├── tsconfig.app.json            ← Config TS para aplicação
├── tsconfig.node.json           ← Config TS para Node
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
│   ├── robots.txt               ← SEO para mecanismos de busca
│   ├── 404.html                 ← Fallback para SPA routing
│   └── data/                    ← Dados de exemplo
│
└── src/
    ├── main.tsx                 ← Entry point React (ReactDOM.render)
    ├── App.tsx                  ← Router + Layout principal
    ├── App.css                  ← Estilos globais do App
    ├── index.css                ← Reset + variáveis CSS + DSGOV
    ├── vite-env.d.ts            ← Tipos Vite
    │
    ├── pages/                   ← Páginas da aplicação (rotas)
    │   ├── Index.tsx            ← Redireciona para Dashboard
    │   ├── Dashboard.tsx        ← Página inicial com KPIs e métricas
    │   │                          - Cards de estatísticas
    │   │                          - Gráficos de distribuição
    │   │                          - Histórico recente
    │   │
    │   ├── Classification.tsx   ← Análise de textos (707 linhas)
    │   │                          - Textarea para texto individual
    │   │                          - FileDropzone para upload em lote
    │   │                          - Tabela de resultados com paginação
    │   │                          - Dialog de detalhes
    │   │
    │   ├── Documentation.tsx    ← Guia de uso integrado
    │   │                          - Como usar o sistema
    │   │                          - Tipos de PII detectados
    │   │                          - Níveis de risco
    │   │
    │   └── NotFound.tsx         ← Página 404
    │
    ├── components/              ← Componentes reutilizáveis
    │   │
    │   ├── ui/                  ← Shadcn UI (30+ componentes)
    │   │   ├── button.tsx       ← Botões com variantes
    │   │   ├── card.tsx         ← Cards para conteúdo
    │   │   ├── input.tsx        ← Inputs de texto
    │   │   ├── textarea.tsx     ← Áreas de texto
    │   │   ├── dialog.tsx       ← Modais
    │   │   ├── table.tsx        ← Tabelas
    │   │   ├── progress.tsx     ← Barras de progresso
    │   │   ├── badge.tsx        ← Badges/tags
    │   │   ├── toast.tsx        ← Notificações
    │   │   ├── tabs.tsx         ← Abas
    │   │   ├── tooltip.tsx      ← Tooltips
    │   │   └── ...              ← (30+ componentes acessíveis)
    │   │
    │   ├── Header.tsx           ← Cabeçalho com logo DSGOV e navegação
    │   ├── KPICard.tsx          ← Card de métrica individual
    │   ├── ConfidenceBar.tsx    ← Barra visual de confiança (0-100%)
    │   ├── ResultsTable.tsx     ← Tabela de resultados com paginação
    │   ├── ResultsLegend.tsx    ← Legenda de cores de risco
    │   ├── FileDropzone.tsx     ← Upload drag & drop (CSV/XLSX)
    │   ├── ExportButton.tsx     ← Botão de exportação JSON
    │   ├── IdentifierBadge.tsx  ← Badge de tipo de PII
    │   ├── StatusBadge.tsx      ← Badge de status (público/restrito)
    │   ├── RiskThermometer.tsx  ← Termômetro visual de risco
    │   ├── AnalysisSkeleton.tsx ← Skeleton loading durante análise
    │   ├── ApiStatus.tsx        ← Indicador de conexão com backend
    │   ├── ApiWakingUpMessage.tsx ← Mensagem de cold start
    │   ├── BenchmarkMetrics.tsx ← Métricas de benchmark
    │   ├── DistributionChart.tsx← Gráfico de distribuição
    │   ├── EntityTypesChart.tsx ← Gráfico de tipos de entidade
    │   ├── PIITypesChart.tsx    ← Gráfico de tipos de PII
    │   ├── RiskDistributionChart.tsx ← Gráfico de distribuição de risco
    │   ├── FooterWithCounters.tsx ← Rodapé com contadores
    │   ├── NavLink.tsx          ← Link de navegação ativo
    │   └── BrazilianAtomIcon.tsx← Ícone customizado
    │
    ├── lib/                     ← Utilitários e serviços
    │   ├── api.ts               ← Cliente HTTP para backend (376 linhas)
    │   │                          - Detecção automática de backend local
    │   │                          - Retry com exponential backoff
    │   │                          - Tratamento de erros (CORS, timeout)
    │   │                          - Interfaces TypeScript
    │   │
    │   ├── fileParser.ts        ← Parser de arquivos CSV/XLSX
    │   │                          - Validação de colunas
    │   │                          - Extração de texto e ID
    │   │
    │   ├── validateBatchFile.ts ← Validação de arquivos de lote
    │   │
    │   └── utils.ts             ← Funções auxiliares
    │                              - cn() para merge de classes
    │                              - Formatação de números
    │
    ├── contexts/                ← Estado global (React Context)
    │   └── AnalysisContext.tsx  ← Contexto de análises
    │                              - Histórico de resultados
    │                              - Métricas agregadas
    │                              - Funções de update
    │
    └── hooks/                   ← Custom hooks
        ├── use-mobile.tsx       ← Detecta dispositivo mobile
        └── use-toast.ts         ← Hook para notificações toast
```

---

## 1️⃣ INSTRUÇÕES DE INSTALAÇÃO E DEPENDÊNCIAS

### 1.1 Pré-requisitos

| Software | Versão Mínima | Verificar | Como Instalar |
|----------|---------------|-----------|---------------|
| **Node.js** | 18.0+ | `node --version` | [nodejs.org](https://nodejs.org/) |
| **npm** | 9.0+ | `npm --version` | Incluído com Node.js |
| **Git** | 2.0+ | `git --version` | [git-scm.com](https://git-scm.com/) |

**Alternativa:** [Bun](https://bun.sh/) 1.0+ (mais rápido que npm)

### 1.2 Arquivo de Dependências: `package.json`

```json
{
  "name": "vite_react_shadcn_ts",
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint ."
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.30.1",
    
    "@tanstack/react-query": "^5.83.0",
    "react-hook-form": "^7.61.1",
    "@hookform/resolvers": "^3.10.0",
    "zod": "^3.25.76",
    
    "recharts": "^2.15.4",
    "xlsx": "^0.18.5",
    "lucide-react": "^0.462.0",
    "date-fns": "^3.6.0",
    
    "@radix-ui/react-dialog": "^1.1.14",
    "@radix-ui/react-tabs": "^1.1.12",
    "@radix-ui/react-toast": "^1.2.14",
    "@radix-ui/react-progress": "^1.1.7",
    "@radix-ui/react-tooltip": "^1.2.7",
    
    "tailwind-merge": "^2.6.0",
    "tailwindcss-animate": "^1.0.7",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    
    "sonner": "^1.7.4",
    "vaul": "^0.9.9",
    "cmdk": "^1.1.1"
  },
  "devDependencies": {
    "vite": "^5.4.19",
    "typescript": "^5.8.3",
    "@vitejs/plugin-react-swc": "^3.11.0",
    
    "tailwindcss": "^3.4.17",
    "@tailwindcss/typography": "^0.5.16",
    "autoprefixer": "^10.4.21",
    "postcss": "^8.5.6",
    
    "eslint": "^9.32.0",
    "eslint-plugin-react-hooks": "^5.2.0",
    "eslint-plugin-react-refresh": "^0.4.20",
    "typescript-eslint": "^8.38.0",
    
    "@types/react": "^18.3.23",
    "@types/react-dom": "^18.3.7",
    "@types/node": "^22.16.5"
  }
}
```

### 1.3 Instalação Passo a Passo

```bash
# 1. Clone o repositório (se ainda não fez)
git clone https://github.com/marinhothiago/desafio-participa-df.git
cd desafio-participa-df/frontend

# 2. Instale todas as dependências
npm install

# Alternativa com Bun (mais rápido):
# bun install
```

**Tempo estimado:** 1-2 minutos

---

## 2️⃣ INSTRUÇÕES DE EXECUÇÃO

### 2.1 Servidor de Desenvolvimento

```bash
# Na pasta frontend/
npm run dev

# Alternativa com Bun:
# bun run dev
```

**Saída esperada:**
```
  VITE v5.4.19  ready in 500 ms

  ➜  Local:   http://localhost:8080/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Acesse:** http://localhost:8080

### 2.2 Build de Produção

```bash
# Gera arquivos otimizados em /dist
npm run build

# Prévia do build
npm run preview
```

**Arquivos gerados em `dist/`:**
- `index.html` - HTML principal
- `assets/*.js` - JavaScript minificado
- `assets/*.css` - CSS otimizado
- `robots.txt`, `404.html` - Arquivos estáticos

### 2.3 Execução com Docker

```bash
# Na pasta frontend/
docker build -t participa-df-frontend .

# Execute o container
docker run -p 3000:80 participa-df-frontend
```

**Ou usando docker-compose (da raiz):**
```bash
cd ..
docker-compose up frontend
```

**Acesse:** http://localhost:3000

### 2.4 Linting

```bash
# Verifica código com ESLint
npm run lint
```

---

## 📊 Funcionalidades da Interface

### Dashboard (Página Inicial)

- **KPI Cards:** Total de análises, textos públicos, textos restritos
- **Gráficos:** Distribuição de risco, tipos de PII detectados
- **Histórico:** Últimas análises realizadas

### Classification (Análise)

#### Análise Individual
1. Digite ou cole o texto no campo
2. Clique em "Analisar"
3. Veja o resultado com:
   - Classificação (PÚBLICO/NÃO PÚBLICO)
   - Nível de risco (cores visuais)
   - Score de confiança (0-100%)
   - Lista de PIIs detectados

#### Processamento em Lote
1. Arraste um arquivo CSV/XLSX para a área de upload
2. O arquivo deve ter coluna `Texto Mascarado` ou `text`
3. Clique em "Processar Lote"
4. Acompanhe o progresso
5. Exporte os resultados em JSON

### Documentation (Guia)

- Como usar o sistema
- Tipos de PII detectados
- Níveis de risco explicados
- FAQ

---

## � Exibição da Confiança

### Barra de Confiança

O componente `ConfidenceBar` exibe a confiança como uma barra visual verde:

```tsx
// src/components/ConfidenceBar.tsx
export function ConfidenceBar({ value, showLabel = true }: ConfidenceBarProps) {
  const percentage = value * 100;  // Backend envia 0-1
  
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
        <div 
          className="h-full rounded-full"
          style={{ 
            width: `${percentage}%`,
            backgroundColor: 'hsl(120, 60%, 40%)'  // Verde
          }}
        />
      </div>
      {showLabel && <span>{percentage.toFixed(0)}%</span>}
    </div>
  );
}
```

### Como a Confiança é Calculada

O backend retorna valores entre **0.0 e 1.0** usando o sistema de **Confiança Composta**:

```
confiança_final = min(1.0, confiança_base × fator_contexto)
```

| Cenário | Confiança | Exibição |
|---------|-----------|----------|
| CPF com "Meu CPF:" | 1.0 | **100%** |
| CPF sem contexto | 0.98 | **98%** |
| Nome via BERT (score 0.87) | 0.87 | **87%** |
| Nome via spaCy | 0.70 | **70%** |
| Texto PÚBLICO (sem PII) | 1.0 | **100%** (certeza de segurança) |

### Interpretação

- **90-100%**: Alta confiança - PII confirmado ou texto seguro
- **70-89%**: Confiança moderada - provavelmente PII
- **< 70%**: Confiança baixa - verificar manualmente

---

## �🔌 Integração com Backend

### Detecção Automática

O frontend detecta automaticamente se o backend está rodando localmente:

```typescript
// src/lib/api.ts
const PRODUCTION_API_URL = 'https://marinhothiago-desafio-participa-df.hf.space';
const LOCAL_API_URL = 'http://localhost:7860';
const LOCAL_DETECTION_TIMEOUT = 2000; // 2 segundos

async function detectLocalBackend(): Promise<void> {
  try {
    const response = await fetch(`${LOCAL_API_URL}/health`, {
      signal: AbortSignal.timeout(LOCAL_DETECTION_TIMEOUT)
    });
    if (response.ok) {
      API_BASE_URL = LOCAL_API_URL;
      console.log('✅ Backend local detectado!');
    }
  } catch {
    console.log('ℹ️ Usando HuggingFace Spaces');
  }
}
```

### Tratamento de Erros

```typescript
// Tipos de erro tratados
export type ApiErrorType = 'TIMEOUT' | 'OFFLINE' | 'WAKING_UP' | 'CORS' | 'UNKNOWN';

// Mensagens amigáveis
export function getErrorMessage(error: ApiError): string {
  switch (error.type) {
    case 'WAKING_UP':
      return 'O motor de IA está acordando, aguarde...';
    case 'TIMEOUT':
      return 'API demorou muito. Tente novamente.';
    case 'OFFLINE':
      return 'Sem conexão com a API.';
    // ...
  }
}
```

---

## 🎨 Design System DSGOV

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

### Tipografia

- **Fonte:** Rawline (Gov.br) com fallback para system fonts
- **Tamanhos:** Scale consistente (xs, sm, base, lg, xl, 2xl, etc)

### Componentes Acessíveis

Todos os componentes UI usam **Radix UI** para garantir:
- ✅ Navegação por teclado
- ✅ Suporte a screen readers
- ✅ ARIA labels corretos
- ✅ Contraste adequado

---

## 🐳 Dockerfile

```dockerfile
# Stage 1: Build com Node.js
FROM node:20-alpine AS builder

WORKDIR /app

# Instala dependências
COPY package*.json ./
COPY bun.lockb* ./
RUN npm ci || npm install

# Build de produção
COPY . .
RUN npm run build

# Stage 2: Serve com nginx
FROM nginx:alpine

# Remove config padrão
RUN rm -rf /usr/share/nginx/html/*

# Copia build (Vite gera em /dist)
COPY --from=builder /app/dist /usr/share/nginx/html

# Config nginx para SPA (React Router)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### nginx.conf para SPA

```nginx
server {
    listen 80;
    server_name localhost;
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

## 📚 Código Fonte Comentado

### Exemplo: Cliente API (`src/lib/api.ts`)

```typescript
/**
 * Cliente HTTP para comunicação com backend FastAPI.
 * 
 * Features:
 * - Detecção automática de backend local
 * - Retry com exponential backoff
 * - Tratamento de cold start (HuggingFace Spaces)
 * - Tipagem TypeScript completa
 */

// Interface para resposta da API
export interface AnalyzeResponse {
  classificacao: "PÚBLICO" | "NÃO PÚBLICO";
  risco: "SEGURO" | "BAIXO" | "MODERADO" | "ALTO" | "CRÍTICO";
  confianca: number; // 0.0 a 1.0 (normalizado)
  detalhes: Array<{
    tipo: string;    // Ex: "CPF"
    valor: string;   // Ex: "123.456..."
    confianca: number;
  }>;
}

class ApiClient {
  /**
   * Realiza requisição HTTP com retry e tratamento de erros.
   */
  private async request<T>(
    endpoint: string,
    options?: RequestInit,
    retryCount = 0
  ): Promise<T> {
    // ... implementação com timeout e retry
  }

  /**
   * Analisa texto único para detecção de PII.
   */
  async analyzeText(text: string): Promise<AnalysisResult> {
    const response = await this.request<AnalyzeResponse>('/analyze', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
    // Mapeia resposta para formato interno
    return {
      classificacao: response.classificacao,
      confianca: response.confianca,
      risco: response.risco,
      detalhes: response.detalhes,
    };
  }
}
```

### Exemplo: Context de Estado (`src/contexts/AnalysisContext.tsx`)

```typescript
/**
 * Contexto React para gerenciamento de estado global.
 * 
 * Armazena:
 * - Histórico de análises realizadas
 * - Métricas agregadas (total, públicos, restritos)
 * - Funções para adicionar/limpar resultados
 */

interface AnalysisContextType {
  history: AnalysisHistoryItem[];
  metrics: {
    total: number;
    public: number;
    restricted: number;
    classificationRequests: number;
  };
  addAnalysisResult: (result: AnalysisResult, text: string, source: string) => void;
  addBatchResults: (results: BatchResult[]) => void;
  clearHistory: () => void;
  incrementClassificationRequests: (count: number) => void;
}
```

---

## 🧪 Testes Manuais

### Teste Individual
1. Acesse http://localhost:8080
2. Na página Classification, digite: `Meu CPF é 123.456.789-09`
3. Clique "Analisar"
4. **Esperado:** Classificação "NÃO PÚBLICO", Risco "CRÍTICO"

### Teste de Lote
1. Crie um arquivo `teste.csv`:
```csv
ID,Texto Mascarado
1,"Solicito informações."
2,"Meu CPF é 529.982.247-25"
```
2. Arraste para a área de upload
3. Clique "Processar Lote"
4. **Esperado:** 
   - Item 1: PÚBLICO
   - Item 2: NÃO PÚBLICO

### Teste de Conexão
1. Inicie o backend local (`uvicorn api.main:app --port 7860`)
2. Recarregue o frontend
3. **Esperado:** Console mostra "✅ Backend local detectado!"

---

## 🔗 Relacionado

- **Backend (Motor de IA):** [../backend/README.md](../backend/README.md)
- **Projeto Completo:** [../README.md](../README.md)

---

## 📄 Licença

Desenvolvido para o **Hackathon Participa DF 2025** em conformidade com:
- **LGPD** - Lei Geral de Proteção de Dados (Lei nº 13.709/2018)
- **LAI** - Lei de Acesso à Informação (Lei nº 12.527/2011)
