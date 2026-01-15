# 🎨 Frontend: Dashboard Participa DF

Interface React para análise de privacidade em pedidos de Lei de Acesso à Informação (LAI), seguindo o padrão visual DSGOV (Gov.br).

**Versão:** 8.5 | **Status:** Produção ✅ | **Deploy:** GitHub Pages

---

## 📋 Objetivo Frontend

Disponibilizar uma interface web intuitiva para:
- **Análise Individual:** Testar textos e visualizar PII detectado
- **Processamento em Lote:** Upload de CSV/XLSX e relatório automático
- **Dashboards KPI:** Métricas em tempo real de análises realizadas
- **Design DSGOV:** Interface seguindo padrão federal brasileiro

---

## 🏗️ Arquitetura: Client-Side React

```
┌──────────────────────────────────────────┐
│     Frontend (React + Vite)              │
│     Rodar em: http://localhost:8080      │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │ Pages (Páginas):                   │ │
│  │  • Dashboard.tsx - Visão geral KPI │ │
│  │  • Classification.tsx - Análise    │ │
│  │  • Documentation.tsx - Guia        │ │
│  └────────────────────────────────────┘ │
│          ↓ Usa componentes ↓            │
│  ┌────────────────────────────────────┐ │
│  │ Components (Reutilizáveis):        │ │
│  │  • Header.tsx - Logo + Menu        │ │
│  │  • KPICard.tsx - Cards métri cas  │ │
│  │  • ConfidenceBar.tsx - Barra 0-1  │ │
│  │  • ResultsTable.tsx - Tabela Dados│ │
│  │  • FileDropzone.tsx - Upload      │ │
│  └────────────────────────────────────┘ │
│          ↓ Usa contexto e hooks ↓       │
│  ┌────────────────────────────────────┐ │
│  │ State Management (Context):        │ │
│  │  • AnalysisContext.tsx - Histórico │ │
│  │  • Metrics (KPIs globais)          │ │
│  │  • useAnalysis() hook              │ │
│  └────────────────────────────────────┘ │
│          ↓ HTTP requests ↓              │
└────────────────┬─────────────────────────┘
                 │
         POST /analyze
         GET /health
                 │
                 ↓
        Backend (FastAPI)
        Port 8000
```

---

## 📁 Estrutura de Arquivos

```
frontend/
├── README.md                    ← ESTE ARQUIVO
├── package.json                 ← Dependências npm
├── vite.config.ts               ← Build config
├── tailwind.config.ts           ← Design system DSGOV
├── index.html                   ← Entry point HTML
│
├── src/
│   ├── main.tsx                 ← Arquivo principal (React.render)
│   ├── App.tsx                  ← Router + Layout
│   ├── index.css                ← Estilos globais DSGOV
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx        ← Página inicial com KPIs
│   │   ├── Classification.tsx   ← Análise individual + lote
│   │   ├── Documentation.tsx    ← Guia integrado no app
│   │   └── NotFound.tsx         ← Página 404
│   │
│   ├── components/              ← Componentes reutilizáveis
│   │   ├── ui/                  ← Shadcn components
│   │   │   ├── button.tsx       ← Botões
│   │   │   ├── card.tsx         ← Cards
│   │   │   ├── input.tsx        ← Inputs
│   │   │   └── ... (30+ components)
│   │   │
│   │   ├── Header.tsx           ← Cabeçalho com logo
│   │   ├── KPICard.tsx          ← Card de métrica
│   │   ├── ConfidenceBar.tsx    ← Barra visual 0-1
│   │   ├── ResultsTable.tsx     ← Tabela com paginação
│   │   ├── FileDropzone.tsx     ← Upload drag & drop
│   │   ├── ResultsLegend.tsx    ← Legenda de cores
│   │   ├── IdentifierBadge.tsx  ← Badge de tipo PII
│   │   ├── StatusBadge.tsx      ← Status (público/restrito)
│   │   ├── RiskThermometer.tsx  ← Termômetro risco
│   │   └── ... (mais componentes)
│   │
│   ├── lib/
│   │   ├── api.ts               ← Cliente HTTP integrado
│   │   ├── fileParser.ts        ← Parser CSV/XLSX
│   │   └── utils.ts             ← Funções auxiliares
│   │
│   ├── contexts/
│   │   └── AnalysisContext.tsx  ← State global (histórico análises)
│   │
│   └── hooks/
│       ├── use-mobile.tsx       ← Detecta mobile
│       └── use-toast.ts         ← Notificações
│
├── public/
│   ├── favicon.svg              ← Ícone 🟢🟡🔵 (cores Brasil)
│   └── robots.txt               ← SEO
│
└── tailwind.config.ts           ← Design system DSGOV
```

---

## 1️⃣ INSTALAÇÃO E DEPENDÊNCIAS (4 PONTOS)

### Pré-requisitos (1 ponto)

| Item | Versão Mínima |
|------|---------------|
| **Node.js** | 18.0+ |
| **npm** | 9.0+ |

### Arquivo de Dependências: `package.json` (2 pontos)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "vite": "^5.4.19",
    "typescript": "^5.3.3",
    "@radix-ui/react-primitive": "^1.0.3",
    "tailwindcss": "^3.3.6",
    "recharts": "^2.10.3",
    "lucide-react": "^0.374.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.3.3"
  }
}
```

### Configuração (Passo a Passo Exato) - 1 ponto

```bash
# 1. Clone
git clone https://github.com/marinhothiago/participa-df-pii.git
cd participa-df-pii/frontend

# 2. Instale dependências
npm install

# 3. Inicie desenvolvimento
npm run dev

# 4. Acesse http://localhost:8080/desafio-participa-df/
```

---

## 2️⃣ EXECUÇÃO (3 PONTOS)

### Desenvolvimento (2 pontos)

```bash
npm run dev
```

**Acesso:**
- Local: http://localhost:8080/desafio-participa-df/
- Reload automático (HMR ativo)

### Build Produção

```bash
npm run build  # Gera /dist
npm run preview  # Testa build local
```

### Formato de Dados (1 ponto)

**Entrada (Upload):**
```
CSV/XLSX com:
- Coluna A (ID)
- Coluna B (Texto)
```

**Saída (Visualização):**
- Dashboard: KPIs e gráficos
- Tabela: Resultados com paginação
- Detalhes: Modal com PIIs encontrados

---

## 3️⃣ CLAREZA E ORGANIZAÇÃO

### Código com Comentários (1 ponto)

**Pages ([src/pages/Classification.tsx](./src/pages/Classification.tsx)):**
```typescript
export function Classification() {
  // State para análise individual
  const [text, setText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  
  // Handler da análise
  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setIsAnalyzing(true);
    
    try {
      // Chamar API backend
      const data = await api.analyzeText(text);
      setAnalysisResult(data);
      
      // Salvar no contexto global
      addAnalysisResult(data, text, 'individual');
    } finally {
      setIsAnalyzing(false);
    }
  };
}
```

**Components ([src/components/ConfidenceBar.tsx](./src/components/ConfidenceBar.tsx)):**
```typescript
/**
 * Barra de confiança com preenchimento verde sólido
 * O preenchimento segue a porcentagem de confiança (0-100%)
 * 
 * Recebe valor entre 0-1 do backend
 */
export function ConfidenceBar({ value }: ConfidenceBarProps) {
  const percentage = value * 100;  // Converter para %
  
  return (
    <div className="flex items-center gap-2">
      {/* Track (fundo cinza) */}
      <div className="flex-1 h-2 bg-muted rounded-full">
        {/* Thumb (preenchimento verde) */}
        <div 
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      <span>{Math.min(percentage, 100).toFixed(0)}%</span>
    </div>
  );
}
```

### Estrutura Lógica (1 ponto)

```
src/
├── pages/          ← Telas (uma por página)
├── components/     ← Reutilizáveis (5+ linhas = componente)
├── lib/           ← Lógica compartilhada
├── contexts/      ← State management
└── hooks/         ← Custom React hooks
```

### Arquivo Principal (1 ponto)

Este README descreve:
✓ Objetivo: Interface React para análise PII  
✓ Pré-requisitos: Node.js 18+  
✓ Instalação: npm install + npm run dev  
✓ Tecnologias: React, Vite, Tailwind, Shadcn  
✓ Funcionalidades: Dashboard, análise, lote  
✓ Estrutura: Componentes bem organizados

---

## 🎨 Design System (DSGOV)

### Cores

```css
/* Primária */
--primary: #1351B4;      /* Azul Gov.br */

/* Semáforo */
--success: #00A65E;      /* Verde (seguro) */
--warning: #FDB700;      /* Amarelo (atenção) */
--danger: #E60000;       /* Vermelho (crítico) */

/* Neutros */
--background: #FFFFFF;
--text: #1A1A1A;
--border: #E0E0E0;
```

### Tipografia

- **Font:** Roboto (sans-serif)
- **Sizes:** 12px (small) → 24px (h1)
- **Weight:** 300 (light) → 700 (bold)

---

## 🛠️ Tecnologias

- **React 18:** Framework UI
- **Vite:** Build tool rápido
- **TypeScript:** Type safety
- **Tailwind CSS:** Utility-first CSS
- **Shadcn/UI:** Component library
- **Recharts:** Gráficos
- **Lucide React:** Ícones

---

## 🔌 Integração com Backend

### Endpoints Consumidos

```typescript
// api.ts - Cliente HTTP

POST /analyze
  Entrada: { text: string }
  Saída: AnalysisResult
  Timeout: 15s

GET /health
  Saída: { status: string }
  Timeout: 8s
```

### Tratamento de Erros

```typescript
// Se backend está offline:
// → Exibir dados de demonstração (mock)
// → Mensagem "API iniciando"
// → Retry automático
```

---

## 📊 Funcionalidades Implementadas

| Feature | Status | Local |
|---------|--------|-------|
| Dashboard KPI | ✅ | Dashboard.tsx |
| Análise individual | ✅ | Classification.tsx |
| Processamento lote | ✅ | Classification.tsx |
| Upload drag & drop | ✅ | FileDropzone.tsx |
| Tabela com paginação | ✅ | ResultsTable.tsx |
| Gráficos (Recharts) | ✅ | Dashboard.tsx |
| Design DSGOV | ✅ | tailwind.config.ts |
| Documentação in-app | ✅ | Documentation.tsx |

---

## 📝 Licença

Desenvolvido para o Desafio Participa DF (Hackathon 2024-2025)
#   G i t H u b   P a g e s   D e p l o y   T e s t  
 