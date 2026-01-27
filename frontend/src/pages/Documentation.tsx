import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Calculator,
  Check,
  CheckCircle2,
  Code,
  Copy,
  Cpu,
  Database,
  ExternalLink,
  Eye,
  FileInput, FileOutput,
  FileText,
  FolderTree,
  Github,
  Globe,
  Hash,
  KeyRound,
  Layers,
  Layout,
  Lock,
  Package, Play,
  RefreshCw,
  Server,
  Shield,
  ShieldCheck, Sparkles,
  Target,
  Terminal,
  Zap
} from 'lucide-react';
import { useState } from 'react';

interface DocLinkProps {
  href: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}

function DocLink({ href, icon, title, description }: DocLinkProps) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="gov-card hover:border-primary/50 transition-all duration-200 group block"
    >
      <div className="flex items-start gap-4">
        <div className="p-3 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
          {icon}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
              {title}
            </h3>
            <ExternalLink className="w-4 h-4 text-muted-foreground" />
          </div>
          <p className="text-sm text-muted-foreground mt-1">{description}</p>
        </div>
      </div>
    </a>
  );
}

function CodeBlock({ children, title }: { children: string; title?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg overflow-hidden border border-border relative group">
      {title && (
        <div className="bg-muted px-4 py-2 border-b border-border flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground">{title}</span>
          <button
            onClick={handleCopy}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            {copied ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>
      )}
      <pre className="p-4 bg-muted/50 overflow-x-auto">
        <code className="text-sm font-mono text-foreground">{children}</code>
      </pre>
      {!title && (
        <button
          onClick={handleCopy}
          className="absolute top-2 right-2 text-muted-foreground hover:text-foreground transition-colors opacity-0 group-hover:opacity-100"
        >
          {copied ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
        </button>
      )}
    </div>
  );
}

function SoftwareBadge({ name, version, color = "primary" }: { name: string; version: string; color?: string }) {
  const colorClasses = {
    primary: "bg-primary/10 text-primary border-primary/30",
    success: "bg-success/10 text-success border-success/30",
    warning: "bg-warning/10 text-warning border-warning/30",
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${colorClasses[color as keyof typeof colorClasses] || colorClasses.primary}`}>
      {name}
      <span className="font-bold">{version}</span>
    </span>
  );
}

export function Documentation() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="gov-card bg-gradient-to-r from-primary/5 to-primary/10 border-primary/20">
        <div className="flex items-start gap-4">
          <div className="p-4 rounded-xl bg-primary/10">
            <Shield className="w-8 h-8 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-foreground">Documentação Técnica</h2>
            <p className="text-muted-foreground mt-1">
              Motor Híbrido de Proteção de Dados Pessoais (PII) v9.6.0 — F1-Score: 1.0000 | 452 Testes | 156 PIIs
            </p>
          </div>
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-2 md:grid-cols-4 lg:grid-cols-8 h-auto gap-1">
          <TabsTrigger value="overview" className="flex items-center gap-2 text-xs">
            <Eye className="w-4 h-4" />
            <span className="hidden sm:inline">Visão Geral</span>
          </TabsTrigger>
          <TabsTrigger value="architecture" className="flex items-center gap-2 text-xs">
            <Layers className="w-4 h-4" />
            <span className="hidden sm:inline">Arquitetura</span>
          </TabsTrigger>
          <TabsTrigger value="installation" className="flex items-center gap-2 text-xs">
            <Package className="w-4 h-4" />
            <span className="hidden sm:inline">Instalação</span>
          </TabsTrigger>
          <TabsTrigger value="execution" className="flex items-center gap-2 text-xs">
            <Play className="w-4 h-4" />
            <span className="hidden sm:inline">Execução</span>
          </TabsTrigger>
          <TabsTrigger value="dataformat" className="flex items-center gap-2 text-xs">
            <Database className="w-4 h-4" />
            <span className="hidden sm:inline">Formatos</span>
          </TabsTrigger>
          <TabsTrigger value="methodology" className="flex items-center gap-2 text-xs">
            <Activity className="w-4 h-4" />
            <span className="hidden sm:inline">Metodologia</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center gap-2 text-xs">
            <Lock className="w-4 h-4" />
            <span className="hidden sm:inline">Segurança</span>
          </TabsTrigger>
          <TabsTrigger value="api" className="flex items-center gap-2 text-xs">
            <Server className="w-4 h-4" />
            <span className="hidden sm:inline">API</span>
          </TabsTrigger>
        </TabsList>

        {/* ============================================ */}
        {/* Tab 1: VISÃO GERAL */}
        {/* ============================================ */}
        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="gov-card">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Eye className="w-5 h-5 text-primary" />
              1. Visão Geral
            </h3>

            {/* Objetivo Principal */}
            <div className="p-5 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border-2 border-primary/30 rounded-xl mb-6">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-primary/20">
                  <Target className="w-7 h-7 text-primary" />
                </div>
                <div>
                  <h4 className="font-bold text-foreground text-lg">Objetivo</h4>
                  <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                    Sistema de IA para <strong className="text-foreground">detectar, classificar e avaliar o risco de vazamento de dados pessoais</strong> em
                    textos de pedidos de acesso a informação recebidos pelo GDF, garantindo conformidade com a
                    <strong className="text-primary"> Lei Geral de Proteção de Dados (LGPD)</strong> sem prejudicar a
                    <strong className="text-success"> Transparência Ativa (LAI)</strong>.
                  </p>
                </div>
              </div>
            </div>

            {/* Diferencial */}
            <div className="p-5 bg-gradient-to-br from-warning/10 via-warning/5 to-transparent border-2 border-warning/30 rounded-xl mb-6">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-warning/20">
                  <Sparkles className="w-7 h-7 text-warning" />
                </div>
                <div>
                  <h4 className="font-bold text-foreground text-lg flex items-center gap-2">
                    Diferencial Competitivo
                    <Sparkles className="w-5 h-5 text-warning" />
                  </h4>
                  <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                    <strong className="text-foreground">Pipeline Ensemble de 9 Etapas:</strong> Combinação de
                    <strong className="text-primary"> BERT NER + NuNER + spaCy + Presidio</strong> com
                    <strong className="text-warning"> Regex + Validação DV (Módulo 11)</strong> e
                    <strong className="text-success"> Árbitro LLM (Llama-3.2-3B)</strong> para alcançar F1-Score = 1.0000.
                  </p>
                  <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                    <strong className="text-foreground">30+ Tipos de PII:</strong> CPF, RG, CNH, Email, Telefone, Nome, Endereço,
                    Dados Bancários, PIX, Placas, Processos CNJ, IP, GPS, e mais.
                  </p>
                </div>
              </div>
            </div>

            {/* Cards de Funcionalidades */}
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="p-4 border border-border rounded-lg hover:border-primary/50 transition-colors">
                <div className="flex items-center gap-3 text-primary mb-2">
                  <Shield className="w-5 h-5" />
                  <h4 className="font-semibold text-foreground">Conformidade LGPD</h4>
                </div>
                <p className="text-sm text-muted-foreground">Identificação e proteção automática de dados pessoais sensíveis em pedidos LAI.</p>
              </div>
              <div className="p-4 border border-border rounded-lg hover:border-primary/50 transition-colors">
                <div className="flex items-center gap-3 text-success mb-2">
                  <Globe className="w-5 h-5" />
                  <h4 className="font-semibold text-foreground">Transparência LAI</h4>
                </div>
                <p className="text-sm text-muted-foreground">Preservação de dados geográficos e institucionais para análise estatística governamental.</p>
              </div>
              <div className="p-4 border border-border rounded-lg hover:border-primary/50 transition-colors">
                <div className="flex items-center gap-3 text-warning mb-2">
                  <Hash className="w-5 h-5" />
                  <h4 className="font-semibold text-foreground">Rastreabilidade</h4>
                </div>
                <p className="text-sm text-muted-foreground">ID original preservado em todo o pipeline para auditoria e integração sistêmica.</p>
              </div>
              <div className="p-4 border border-border rounded-lg hover:border-primary/50 transition-colors">
                <div className="flex items-center gap-3 text-primary mb-2">
                  <Calculator className="w-5 h-5" />
                  <h4 className="font-semibold text-foreground">Validação Matemática</h4>
                </div>
                <p className="text-sm text-muted-foreground">Algoritmos de dígito verificador (Módulo 11) para CPF e CNPJ com 100% de precisão.</p>
              </div>
              <div className="p-4 border border-border rounded-lg hover:border-primary/50 transition-colors">
                <div className="flex items-center gap-3 text-warning mb-2">
                  <RefreshCw className="w-5 h-5" />
                  <h4 className="font-semibold text-foreground">Aprendizado Automático</h4>
                </div>
                <p className="text-sm text-muted-foreground">Recalibração contínua via feedback humano com IsotonicRegression para melhoria constante.</p>
              </div>
              <div className="p-4 border border-border rounded-lg hover:border-primary/50 transition-colors">
                <div className="flex items-center gap-3 text-success mb-2">
                  <Github className="w-5 h-5" />
                  <h4 className="font-semibold text-foreground">Código Versionado</h4>
                </div>
                <p className="text-sm text-muted-foreground">Repositório Git público com histórico completo, CI/CD e documentação técnica no GitHub.</p>
              </div>
            </div>

            {/* Documentação Markdown */}
            <div className="mt-6">
              <h4 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                <FileInput className="w-4 h-4 text-primary" />
                Documentação Completa (Markdown)
              </h4>
              <div className="grid sm:grid-cols-3 gap-4">
                <a
                  href="https://github.com/marinhothiago/desafio-participa-df/blob/main/README.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-4 border border-border rounded-lg hover:border-primary/50 transition-colors group"
                >
                  <div className="flex items-center gap-2 text-primary mb-2">
                    <Github className="w-5 h-5" />
                    <span className="font-semibold text-foreground group-hover:text-primary">README.md (Raiz)</span>
                    <ExternalLink className="w-3 h-3 text-muted-foreground" />
                  </div>
                  <p className="text-xs text-muted-foreground">Documentação geral do projeto, instalação e arquitetura.</p>
                </a>
                <a
                  href="https://github.com/marinhothiago/desafio-participa-df/blob/main/backend/README.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-4 border border-border rounded-lg hover:border-success/50 transition-colors group"
                >
                  <div className="flex items-center gap-2 text-success mb-2">
                    <Server className="w-5 h-5" />
                    <span className="font-semibold text-foreground group-hover:text-success">README.md (Backend)</span>
                    <ExternalLink className="w-3 h-3 text-muted-foreground" />
                  </div>
                  <p className="text-xs text-muted-foreground">API FastAPI, motor de detecção e endpoints.</p>
                </a>
                <a
                  href="https://github.com/marinhothiago/desafio-participa-df/blob/main/frontend/README.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-4 border border-border rounded-lg hover:border-warning/50 transition-colors group"
                >
                  <div className="flex items-center gap-2 text-warning mb-2">
                    <Layout className="w-5 h-5" />
                    <span className="font-semibold text-foreground group-hover:text-warning">README.md (Frontend)</span>
                    <ExternalLink className="w-3 h-3 text-muted-foreground" />
                  </div>
                  <p className="text-xs text-muted-foreground">Interface React, componentes e DSGOV.</p>
                </a>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ============================================ */}
        {/* Tab 2: ARQUITETURA */}
        {/* ============================================ */}
        <TabsContent value="architecture" className="space-y-6 mt-6">
          <div className="gov-card">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Layers className="w-5 h-5 text-primary" />
              2. Arquitetura do Sistema
            </h3>

            {/* Estrutura Lógica */}
            <div className="p-5 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border-2 border-primary/30 rounded-xl mb-6">
              <h4 className="font-bold text-foreground mb-4 flex items-center gap-2">
                <FolderTree className="w-5 h-5 text-primary" />
                Motor Híbrido de Detecção PII (v9.6.0)
              </h4>
              <p className="text-sm text-muted-foreground mb-4">
                <strong className="text-foreground">Pipeline Ensemble de 9 Etapas</strong> que combina
                <strong className="text-primary"> BERT NER + NuNER + spaCy + Presidio</strong> com
                <strong className="text-warning"> Regex + Validação DV (Módulo 11)</strong> e árbitro
                <strong className="text-success"> LLM (Llama-3.2-3B)</strong> para decisões ambíguas.
              </p>

              {/* Pipeline Visual */}
              <div className="grid md:grid-cols-4 gap-3 p-4 bg-muted/30 rounded-lg mb-4">
                <div className="text-center p-3 bg-background rounded-lg border border-primary/30">
                  <Code className="w-5 h-5 text-primary mx-auto mb-1" />
                  <p className="font-medium text-foreground text-sm">1-5: Detecção</p>
                  <p className="text-[10px] text-muted-foreground">Regex + BERT + NuNER + spaCy + Gazetteer</p>
                </div>
                <div className="text-center p-3 bg-background rounded-lg border border-warning/30">
                  <Calculator className="w-5 h-5 text-warning mx-auto mb-1" />
                  <p className="font-medium text-foreground text-sm">6-8: Validação</p>
                  <p className="text-[10px] text-muted-foreground">Regras + Confiança + Thresholds</p>
                </div>
                <div className="text-center p-3 bg-background rounded-lg border border-success/30">
                  <Cpu className="w-5 h-5 text-success mx-auto mb-1" />
                  <p className="font-medium text-foreground text-sm">9: Árbitro LLM</p>
                  <p className="text-[10px] text-muted-foreground">Llama-3.2-3B (HF)</p>
                </div>
                <div className="text-center p-3 bg-background rounded-lg border border-blue-500/30">
                  <RefreshCw className="w-5 h-5 text-blue-500 mx-auto mb-1" />
                  <p className="font-medium text-foreground text-sm">10: Feedback Loop</p>
                  <p className="text-[10px] text-muted-foreground">Recalibração Isotônica</p>
                </div>
              </div>

              {/* Fluxo Visual Frontend-Backend */}
              <div className="flex flex-col md:flex-row items-center justify-center gap-3 p-4 bg-muted/30 rounded-lg">
                <div className="text-center p-3 bg-background rounded-lg border border-blue-500/30">
                  <Layout className="w-5 h-5 text-blue-500 mx-auto mb-1" />
                  <p className="font-medium text-foreground text-sm">Frontend</p>
                  <p className="text-[10px] text-muted-foreground">React + Vite + DSGOV</p>
                </div>
                <div className="hidden md:block text-muted-foreground text-2xl">→</div>
                <div className="text-center p-3 bg-background rounded-lg border border-primary/30">
                  <Zap className="w-5 h-5 text-primary mx-auto mb-1" />
                  <p className="font-medium text-foreground text-sm">POST /analyze</p>
                  <p className="text-[10px] text-muted-foreground">HTTPS/REST</p>
                </div>
                <div className="hidden md:block text-muted-foreground text-2xl">→</div>
                <div className="text-center p-3 bg-background rounded-lg border border-success/30">
                  <Server className="w-5 h-5 text-success mx-auto mb-1" />
                  <p className="font-medium text-foreground text-sm">Backend</p>
                  <p className="text-[10px] text-muted-foreground">FastAPI + Motor v9.6.0</p>
                </div>
                <div className="hidden md:block text-muted-foreground text-2xl">→</div>
                <div className="text-center p-3 bg-background rounded-lg border border-warning/30">
                  <Cpu className="w-5 h-5 text-warning mx-auto mb-1" />
                  <p className="font-medium text-foreground text-sm">Hugging Face</p>
                  <p className="text-[10px] text-muted-foreground">Spaces + LLM API</p>
                </div>
              </div>
            </div>

            {/* Arquivos Principais */}
            <h4 className="font-semibold text-foreground mb-4 flex items-center gap-2">
              <Code className="w-4 h-4 text-primary" />
              Função dos Arquivos Principais
            </h4>

            <div className="overflow-x-auto mb-6">
              <table className="w-full text-sm border border-border rounded-lg overflow-hidden">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left py-3 px-4 font-semibold text-foreground border-b border-border">Arquivo</th>
                    <th className="text-left py-3 px-4 font-semibold text-foreground border-b border-border">Função</th>
                    <th className="text-left py-3 px-4 font-semibold text-foreground border-b border-border">Descrição</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-border">
                    <td className="py-3 px-4">
                      <code className="bg-primary/10 text-primary px-2 py-1 rounded text-xs font-bold">detector.py</code>
                    </td>
                    <td className="py-3 px-4 font-medium text-foreground">Core do Motor</td>
                    <td className="py-3 px-4 text-muted-foreground">Núcleo do motor de detecção de PII. Implementa a lógica híbrida de NLP + Regex + Validação Matemática.</td>
                  </tr>
                  <tr className="border-b border-border">
                    <td className="py-3 px-4">
                      <code className="bg-warning/10 text-warning px-2 py-1 rounded text-xs font-bold">main_cli.py</code>
                    </td>
                    <td className="py-3 px-4 font-medium text-foreground">Interface CLI</td>
                    <td className="py-3 px-4 text-muted-foreground">Interface de linha de comando para processamento massivo (Lote) de arquivos Excel/CSV.</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4">
                      <code className="bg-success/10 text-success px-2 py-1 rounded text-xs font-bold">main.py</code>
                    </td>
                    <td className="py-3 px-4 font-medium text-foreground">Gateway API</td>
                    <td className="py-3 px-4 text-muted-foreground">Ponto de entrada da API FastAPI. Expõe os endpoints REST para consumo pelo Frontend.</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Estrutura de Diretórios Backend */}
            <h4 className="font-semibold text-foreground mb-3 flex items-center gap-2">
              <FolderTree className="w-4 h-4 text-success" />
              Estrutura de Diretórios do Backend
            </h4>
            <CodeBlock title="backend/">{`backend/
├── api/
│   ├── main.py              # Gateway da API (FastAPI)
│   ├── celery_config.py     # Configuração Celery (async)
│   └── tasks.py             # Tasks assíncronas
│
├── src/
│   ├── detector.py          # Core do Motor de Detecção
│   ├── allow_list.py        # Lista de termos públicos
│   ├── analyzers/           # Presidio + Regex analyzers
│   ├── confidence/          # Sistema de confiança probabilística
│   ├── gazetteer/           # Dados geográficos GDF
│   └── patterns/            # Padrões regex GDF
│
├── scripts/
│   ├── main_cli.py          # Interface CLI (Lote)
│   └── auditoria_*.py       # Scripts de auditoria
│
├── tests/                   # 452 testes automatizados
├── models/                  # BERT NER ONNX otimizado
├── data/                    # Dados de entrada/saída
├── Dockerfile               # Container Docker
├── requirements.txt         # Dependências Python
└── README.md                # Documentação`}</CodeBlock>

            {/* Estrutura de Diretórios Frontend */}
            <h4 className="font-semibold text-foreground mb-3 mt-6 flex items-center gap-2">
              <FolderTree className="w-4 h-4 text-blue-500" />
              Estrutura de Diretórios do Frontend
            </h4>
            <CodeBlock title="frontend-desafio-participa-df/">{`frontend-desafio-participa-df/
├── public/
│   └── data/                # Arquivos de amostra (XLSX)
│
├── src/
│   ├── components/          # Componentes React reutilizáveis
│   │   ├── ui/              # Componentes shadcn/ui
│   │   ├── Header.tsx       # Cabeçalho com navegação
│   │   ├── KPICard.tsx      # Cards de métricas
│   │   ├── FileDropzone.tsx # Upload drag-and-drop
│   │   └── ExportButton.tsx # Exportação CSV/XLSX/JSON
│   │
│   ├── pages/               # Páginas da aplicação
│   │   ├── Index.tsx        # Layout principal
│   │   ├── Dashboard.tsx    # KPIs e gráficos
│   │   ├── Classification.tsx # Análise de arquivos
│   │   └── Documentation.tsx  # Documentação técnica
│   │
│   ├── contexts/            # Contextos React (estado global)
│   │   └── AnalysisContext.tsx
│   │
│   ├── lib/                 # Utilitários
│   │   ├── api.ts           # Cliente HTTP para backend
│   │   └── fileParser.ts    # Parser de CSV/XLSX
│   │
│   ├── App.tsx              # Rotas da aplicação
│   └── index.css            # Estilos globais (Tailwind + DSGOV)
│
├── package.json             # Dependências npm
├── tailwind.config.ts       # Configuração Tailwind
└── vite.config.ts           # Configuração Vite`}</CodeBlock>

            {/* Documentação Markdown */}
            <h4 className="font-semibold text-foreground mb-3 mt-6 flex items-center gap-2">
              <FileText className="w-4 h-4 text-warning" />
              Documentação Markdown (README.md)
            </h4>
            <div className="grid md:grid-cols-3 gap-4">
              <a
                href="https://github.com/marinhothiago/desafio-participa-df/blob/main/README.md"
                target="_blank"
                rel="noopener noreferrer"
                className="p-4 bg-muted/50 rounded-lg border border-border hover:border-primary/50 transition-colors group"
              >
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-5 h-5 text-primary" />
                  <span className="font-semibold text-foreground group-hover:text-primary transition-colors">README.md (Raiz)</span>
                  <ExternalLink className="w-3 h-3 text-muted-foreground ml-auto" />
                </div>
                <p className="text-xs text-muted-foreground">
                  Documentação geral do projeto: visão geral, instalação, execução e metodologia completa.
                </p>
              </a>
              <a
                href="https://github.com/marinhothiago/desafio-participa-df/blob/main/backend/README.md"
                target="_blank"
                rel="noopener noreferrer"
                className="p-4 bg-muted/50 rounded-lg border border-border hover:border-success/50 transition-colors group"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Server className="w-5 h-5 text-success" />
                  <span className="font-semibold text-foreground group-hover:text-success transition-colors">backend/README.md</span>
                  <ExternalLink className="w-3 h-3 text-muted-foreground ml-auto" />
                </div>
                <p className="text-xs text-muted-foreground">
                  Motor Híbrido v9.6.0: arquitetura do detector, API endpoints, CLI e configuração.
                </p>
              </a>
              <a
                href="https://github.com/marinhothiago/desafio-participa-df/blob/main/frontend/README.md"
                target="_blank"
                rel="noopener noreferrer"
                className="p-4 bg-muted/50 rounded-lg border border-border hover:border-blue-500/50 transition-colors group"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Layout className="w-5 h-5 text-blue-500" />
                  <span className="font-semibold text-foreground group-hover:text-blue-500 transition-colors">frontend/README.md</span>
                  <ExternalLink className="w-3 h-3 text-muted-foreground ml-auto" />
                </div>
                <p className="text-xs text-muted-foreground">
                  Interface React: componentes, páginas, integração com backend e padrão DSGOV.
                </p>
              </a>
            </div>
          </div>
        </TabsContent>

        {/* ============================================ */}
        {/* Tab 3: INSTALAÇÃO */}
        {/* ============================================ */}
        <TabsContent value="installation" className="space-y-6 mt-6">
          <div className="gov-card">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Package className="w-5 h-5 text-primary" />
              3. Guia de Instalação
            </h3>

            {/* Opção 1: Docker */}
            <div className="mb-8">
              <div className="p-5 bg-gradient-to-br from-success/10 via-success/5 to-transparent border-2 border-success/30 rounded-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-success/20">
                    <Server className="w-6 h-6 text-success" />
                  </div>
                  <div>
                    <h4 className="font-bold text-foreground text-lg">Opção 1: Via Docker (Recomendado)</h4>
                    <p className="text-sm text-muted-foreground">Um comando para rodar o sistema completo</p>
                  </div>
                  <span className="ml-auto px-3 py-1 bg-success/20 text-success rounded-full text-xs font-semibold">
                    ⚡ Avaliadores
                  </span>
                </div>

                {/* Pré-requisitos Docker */}
                <div className="mb-4">
                  <h5 className="font-semibold text-foreground mb-2 text-sm">Pré-requisitos:</h5>
                  <div className="flex flex-wrap gap-2">
                    <SoftwareBadge name="Docker" version="24.0+" color="primary" />
                    <SoftwareBadge name="Docker Compose" version="2.20+" color="success" />
                    <SoftwareBadge name="Git" version="2.40+" color="warning" />
                  </div>
                </div>

                {/* Passos Docker */}
                <div className="space-y-3">
                  <div className="p-3 bg-background/50 rounded-lg border-l-4 border-primary">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="w-5 h-5 bg-primary text-white rounded-full flex items-center justify-center text-xs font-bold">1</span>
                      <span className="font-medium text-foreground text-sm">Clonar o repositório</span>
                    </div>
                    <CodeBlock>{`git clone https://github.com/marinhothiago/desafio-participa-df.git
cd desafio-participa-df`}</CodeBlock>
                  </div>

                  <div className="p-3 bg-background/50 rounded-lg border-l-4 border-success">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="w-5 h-5 bg-success text-white rounded-full flex items-center justify-center text-xs font-bold">2</span>
                      <span className="font-medium text-foreground text-sm">Subir os containers (Backend + Frontend)</span>
                    </div>
                    <CodeBlock>{`docker compose up --build`}</CodeBlock>
                    <p className="text-xs text-muted-foreground mt-2">
                      ⏱️ Aguarde o download das imagens (~2-5 min na primeira vez)
                    </p>
                  </div>

                  <div className="p-3 bg-background/50 rounded-lg border-l-4 border-warning">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="w-5 h-5 bg-warning text-white rounded-full flex items-center justify-center text-xs font-bold">✓</span>
                      <span className="font-medium text-foreground text-sm">Verificar se está funcionando</span>
                    </div>
                    <div className="grid md:grid-cols-3 gap-2 mt-2">
                      <div className="text-center p-2 bg-muted/50 rounded-lg">
                        <p className="font-medium text-foreground text-xs">Frontend</p>
                        <code className="text-xs text-primary">http://localhost:80</code>
                      </div>
                      <div className="text-center p-2 bg-muted/50 rounded-lg">
                        <p className="font-medium text-foreground text-xs">Backend API</p>
                        <code className="text-xs text-success">http://localhost:7860</code>
                      </div>
                      <div className="text-center p-2 bg-muted/50 rounded-lg">
                        <p className="font-medium text-foreground text-xs">Swagger Docs</p>
                        <code className="text-xs text-warning">http://localhost:7860/docs</code>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Opção 2: Desenvolvimento Local */}
            <div className="mb-6">
              <div className="p-5 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border-2 border-primary/30 rounded-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-primary/20">
                    <Terminal className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-bold text-foreground text-lg">Opção 2: Desenvolvimento Local (Sem Docker)</h4>
                    <p className="text-sm text-muted-foreground">Para contribuir ou modificar o código</p>
                  </div>
                  <span className="ml-auto px-3 py-1 bg-primary/20 text-primary rounded-full text-xs font-semibold">
                    🛠️ Desenvolvedores
                  </span>
                </div>

                {/* Pré-requisitos Local */}
                <div className="mb-4">
                  <h5 className="font-semibold text-foreground mb-2 text-sm">Pré-requisitos:</h5>
                  <div className="flex flex-wrap gap-2">
                    <SoftwareBadge name="Python" version="3.10+" color="success" />
                    <SoftwareBadge name="Node.js" version="20+" color="primary" />
                    <SoftwareBadge name="Git" version="2.40+" color="warning" />
                  </div>
                </div>

                {/* Backend Setup */}
                <div className="mb-4">
                  <h5 className="font-semibold text-foreground mb-3 text-sm flex items-center gap-2">
                    <Server className="w-4 h-4 text-success" />
                    Backend (Python + FastAPI)
                  </h5>
                  <div className="space-y-3">
                    <div className="p-3 bg-background/50 rounded-lg border-l-4 border-success">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-5 h-5 bg-success text-white rounded-full flex items-center justify-center text-xs font-bold">1</span>
                        <span className="font-medium text-foreground text-sm">Clonar e entrar no diretório</span>
                      </div>
                      <CodeBlock>{`git clone https://github.com/marinhothiago/desafio-participa-df.git
cd desafio-participa-df/backend`}</CodeBlock>
                    </div>

                    <div className="p-3 bg-background/50 rounded-lg border-l-4 border-success">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-5 h-5 bg-success text-white rounded-full flex items-center justify-center text-xs font-bold">2</span>
                        <span className="font-medium text-foreground text-sm">Criar ambiente virtual Python</span>
                      </div>
                      <CodeBlock>{`# Windows
python -m venv .venv
.venv\\Scripts\\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate`}</CodeBlock>
                    </div>

                    <div className="p-3 bg-background/50 rounded-lg border-l-4 border-success">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-5 h-5 bg-success text-white rounded-full flex items-center justify-center text-xs font-bold">3</span>
                        <span className="font-medium text-foreground text-sm">Instalar dependências</span>
                      </div>
                      <CodeBlock>{`pip install -r requirements.txt

# Baixar modelo spaCy pt-BR
python -m spacy download pt_core_news_lg`}</CodeBlock>
                    </div>

                    <div className="p-3 bg-background/50 rounded-lg border-l-4 border-success">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-5 h-5 bg-success text-white rounded-full flex items-center justify-center text-xs font-bold">4</span>
                        <span className="font-medium text-foreground text-sm">Iniciar servidor backend</span>
                      </div>
                      <CodeBlock>{`python -m uvicorn api.main:app --host 0.0.0.0 --port 7860 --reload`}</CodeBlock>
                      <p className="text-xs text-muted-foreground mt-2">
                        ✅ Backend rodando em <code className="bg-muted px-1 rounded">http://localhost:7860</code>
                      </p>
                    </div>
                  </div>
                </div>

                {/* Frontend Setup */}
                <div>
                  <h5 className="font-semibold text-foreground mb-3 text-sm flex items-center gap-2">
                    <Layout className="w-4 h-4 text-primary" />
                    Frontend (React + Vite)
                  </h5>
                  <div className="space-y-3">
                    <div className="p-3 bg-background/50 rounded-lg border-l-4 border-primary">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-5 h-5 bg-primary text-white rounded-full flex items-center justify-center text-xs font-bold">1</span>
                        <span className="font-medium text-foreground text-sm">Entrar no diretório frontend</span>
                      </div>
                      <CodeBlock>{`cd ../frontend  # ou cd desafio-participa-df/frontend`}</CodeBlock>
                    </div>

                    <div className="p-3 bg-background/50 rounded-lg border-l-4 border-primary">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-5 h-5 bg-primary text-white rounded-full flex items-center justify-center text-xs font-bold">2</span>
                        <span className="font-medium text-foreground text-sm">Instalar dependências Node.js</span>
                      </div>
                      <CodeBlock>{`npm install`}</CodeBlock>
                    </div>

                    <div className="p-3 bg-background/50 rounded-lg border-l-4 border-primary">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-5 h-5 bg-primary text-white rounded-full flex items-center justify-center text-xs font-bold">3</span>
                        <span className="font-medium text-foreground text-sm">Iniciar servidor de desenvolvimento</span>
                      </div>
                      <CodeBlock>{`npm run dev`}</CodeBlock>
                      <p className="text-xs text-muted-foreground mt-2">
                        ✅ Frontend rodando em <code className="bg-muted px-1 rounded">http://localhost:5173</code>
                      </p>
                    </div>
                  </div>
                </div>

                {/* Dica de desenvolvimento */}
                <div className="mt-4 p-3 bg-warning/10 border border-warning/30 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-warning mt-0.5 flex-shrink-0" />
                    <div className="text-xs text-muted-foreground">
                      <strong className="text-foreground">Dica:</strong> Abra dois terminais - um para o backend e outro para o frontend.
                      O frontend detecta automaticamente o backend local em <code className="bg-muted px-1 rounded">localhost:7860</code>.
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Executar Testes */}
            <div className="p-4 bg-muted/30 rounded-lg border border-border">
              <h4 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-success" />
                Executar Testes (452 casos)
              </h4>
              <div className="grid md:grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Via Docker:</p>
                  <CodeBlock>{`docker compose exec backend pytest -q`}</CodeBlock>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Local (dentro de /backend):</p>
                  <CodeBlock>{`pytest --disable-warnings -q`}</CodeBlock>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>
        {/* ============================================ */}
        {/* Tab 4: EXECUÇÃO (Critério 8.1.5.3.2) */}
        {/* ============================================ */}
        <TabsContent value="execution" className="space-y-6 mt-6">
          <div className="gov-card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                <Play className="w-5 h-5 text-primary" />
                4. Instruções de Execução
              </h3>
              <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-medium">
                Critério 8.1.5.3.2
              </span>
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
              {/* Modo Docker */}
              <div className="p-5 bg-gradient-to-br from-success/10 via-success/5 to-transparent border-2 border-success/30 rounded-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-success/20">
                    <Server className="w-6 h-6 text-success" />
                  </div>
                  <div>
                    <h4 className="font-bold text-foreground">Via Docker (Recomendado)</h4>
                    <p className="text-xs text-muted-foreground">Um comando para tudo funcionar</p>
                  </div>
                </div>

                <CodeBlock title="Subir todo o sistema">{`docker compose up --build`}</CodeBlock>

                <div className="mt-4 space-y-2">
                  <h5 className="font-semibold text-foreground text-sm">URLs:</h5>
                  <ul className="space-y-1 text-xs text-muted-foreground">
                    <li className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-primary rounded-full"></span>
                      Frontend: <code className="bg-muted px-1.5 py-0.5 rounded">http://localhost:80</code>
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-success rounded-full"></span>
                      Backend: <code className="bg-muted px-1.5 py-0.5 rounded">http://localhost:7860</code>
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-warning rounded-full"></span>
                      Swagger: <code className="bg-muted px-1.5 py-0.5 rounded">http://localhost:7860/docs</code>
                    </li>
                  </ul>
                </div>
              </div>

              {/* Modo CLI */}
              <div className="p-5 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border-2 border-primary/30 rounded-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-primary/20">
                    <Terminal className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-bold text-foreground">Modo CLI (Lote)</h4>
                    <p className="text-xs text-muted-foreground">Processamento massivo de arquivos</p>
                  </div>
                </div>

                <CodeBlock title="Comando de Execução">{`cd backend && python scripts/main_cli.py --input amostra.xlsx --output resultado`}</CodeBlock>

                <div className="mt-4 space-y-2">
                  <h5 className="font-semibold text-foreground text-sm">Argumentos:</h5>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <tbody>
                        <tr className="border-b border-border/50">
                          <td className="py-2 pr-3">
                            <code className="bg-primary/10 text-primary px-2 py-0.5 rounded">--input</code>
                          </td>
                          <td className="py-2 text-muted-foreground">Arquivo fonte (Excel/CSV) contendo colunas "ID" e "Texto"</td>
                        </tr>
                        <tr>
                          <td className="py-2 pr-3">
                            <code className="bg-primary/10 text-primary px-2 py-0.5 rounded">--output</code>
                          </td>
                          <td className="py-2 text-muted-foreground">Nome base do arquivo gerado (sem extensão)</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>

            {/* Desenvolvimento Local */}
            <div className="mt-6 p-5 bg-gradient-to-br from-warning/10 via-warning/5 to-transparent border-2 border-warning/30 rounded-xl">
              <h4 className="font-bold text-foreground mb-4 flex items-center gap-2">
                <Code className="w-5 h-5 text-warning" />
                Desenvolvimento Local (sem Docker)
              </h4>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <h5 className="font-semibold text-foreground text-sm mb-2">Backend</h5>
                  <CodeBlock>{`cd backend
python -m venv venv
.\\venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
python -m uvicorn api.main:app --port 7860 --reload`}</CodeBlock>
                </div>
                <div>
                  <h5 className="font-semibold text-foreground text-sm mb-2">Frontend</h5>
                  <CodeBlock>{`cd frontend
npm install
npm run dev
# Acesse http://localhost:8080`}</CodeBlock>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ============================================ */}
        {/* Tab 5: FORMATOS */}
        {/* ============================================ */}
        <TabsContent value="dataformat" className="space-y-6 mt-6">
          <div className="gov-card">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Database className="w-5 h-5 text-primary" />
              5. Formatos de Dados
            </h3>

            {/* Entrada */}
            <div className="p-5 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border-2 border-primary/30 rounded-xl mb-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-primary/20">
                  <FileInput className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h4 className="font-bold text-foreground">Entrada</h4>
                  <p className="text-xs text-muted-foreground">Arquivo fonte para processamento</p>
                </div>
              </div>

              <p className="text-sm text-muted-foreground mb-4">
                Arquivo <strong className="text-foreground">Excel (.xlsx)</strong> ou <strong className="text-foreground">CSV</strong> com as seguintes colunas obrigatórias:
              </p>

              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm border border-border rounded overflow-hidden">
                  <thead className="bg-muted">
                    <tr>
                      <th className="py-2 px-3 text-left font-semibold text-foreground">Coluna</th>
                      <th className="py-2 px-3 text-left font-semibold text-foreground">Descrição</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-t border-border">
                      <td className="py-2 px-3"><code className="bg-primary/10 text-primary px-1.5 py-0.5 rounded text-xs">ID</code></td>
                      <td className="py-2 px-3 text-muted-foreground text-xs">Identificador único da manifestação</td>
                    </tr>
                    <tr className="border-t border-border">
                      <td className="py-2 px-3"><code className="bg-primary/10 text-primary px-1.5 py-0.5 rounded text-xs">Texto Mascarado</code></td>
                      <td className="py-2 px-3 text-muted-foreground text-xs">Conteúdo do pedido/manifestação</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <CodeBlock title="Exemplo CSV">{`ID,Texto Mascarado
12345,"Solicito informações sobre o servidor José Silva, CPF 123.456.789-00"
12346,"Qual o orçamento da Secretaria de Educação em 2024?"`}</CodeBlock>
            </div>

            {/* Saídas - Grid 3 colunas */}
            <h4 className="font-semibold text-foreground mb-4 flex items-center gap-2">
              <FileOutput className="w-4 h-4 text-success" />
              Formatos de Saída
            </h4>

            <div className="grid lg:grid-cols-3 gap-4 mb-6">
              {/* Saída API */}
              <div className="p-4 bg-gradient-to-br from-success/10 via-success/5 to-transparent border-2 border-success/30 rounded-xl">
                <div className="flex items-center gap-2 mb-3">
                  <Server className="w-5 h-5 text-success" />
                  <h5 className="font-bold text-foreground">API (JSON)</h5>
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  Response estruturado com classificação, risco e achados detalhados.
                </p>
                <CodeBlock title="POST /analyze">{`{
  "contem_pii": true,
  "nivel_risco": "CRÍTICO",
  "peso_risco": 5,
  "tipos_pii": ["CPF", "NOME"],
  "texto_anonimizado": "...",
  "findings": [{...}],
  "confianca": {...}
}`}</CodeBlock>
              </div>

              {/* Saída CLI */}
              <div className="p-4 bg-gradient-to-br from-warning/10 via-warning/5 to-transparent border-2 border-warning/30 rounded-xl">
                <div className="flex items-center gap-2 mb-3">
                  <Terminal className="w-5 h-5 text-warning" />
                  <h5 className="font-bold text-foreground">CLI (Lote)</h5>
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  Processamento em massa com múltiplos formatos de exportação.
                </p>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="px-2 py-0.5 bg-success/20 text-success rounded font-medium">XLSX</span>
                    <span className="text-muted-foreground">Colorido por nível de risco</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="px-2 py-0.5 bg-primary/20 text-primary rounded font-medium">CSV</span>
                    <span className="text-muted-foreground">Compatível com planilhas</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="px-2 py-0.5 bg-warning/20 text-warning rounded font-medium">JSON</span>
                    <span className="text-muted-foreground">Integração com sistemas</span>
                  </div>
                </div>
              </div>

              {/* Saída Frontend */}
              <div className="p-4 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border-2 border-primary/30 rounded-xl">
                <div className="flex items-center gap-2 mb-3">
                  <Layout className="w-5 h-5 text-primary" />
                  <h5 className="font-bold text-foreground">Frontend</h5>
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  Interface completa com recursos interativos.
                </p>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs">
                    <CheckCircle2 className="w-3 h-3 text-success" />
                    <span className="text-muted-foreground">Relatório dinâmico em tempo real</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <CheckCircle2 className="w-3 h-3 text-success" />
                    <span className="text-muted-foreground">Dashboard com métricas</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <CheckCircle2 className="w-3 h-3 text-success" />
                    <span className="text-muted-foreground">Aprendizado por feedback</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <CheckCircle2 className="w-3 h-3 text-success" />
                    <span className="text-muted-foreground">Exportação XLSX, CSV, JSON</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <CheckCircle2 className="w-3 h-3 text-success" />
                    <span className="text-muted-foreground">Documentação integrada</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Exemplo XLSX Colorido */}
            <div className="p-4 bg-muted/50 rounded-lg border border-border">
              <h5 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-warning" />
                Exemplo: Saída XLSX Colorida (CLI)
              </h5>
              <div className="overflow-x-auto">
                <table className="w-full text-xs border border-border rounded">
                  <thead className="bg-muted">
                    <tr>
                      <th className="py-2 px-3 text-left">ID</th>
                      <th className="py-2 px-3 text-left">Classificação</th>
                      <th className="py-2 px-3 text-left">Confiança</th>
                      <th className="py-2 px-3 text-left">Nível de Risco</th>
                      <th className="py-2 px-3 text-left">Identificadores</th>
                    </tr>
                  </thead>
                  <tbody>
                    {/* CRÍTICO - Vermelho Escuro */}
                    <tr>
                      <td className="py-2 px-3">12345</td>
                      <td className="py-2 px-3 bg-red-200 dark:bg-red-900/50 text-red-800 dark:text-red-200">[X] NÃO PÚBLICO</td>
                      <td className="py-2 px-3">99.2%</td>
                      <td className="py-2 px-3 bg-red-300 dark:bg-red-800/60 text-red-900 dark:text-red-100 font-bold">CRÍTICO</td>
                      <td className="py-2 px-3">CPF, NOME</td>
                    </tr>
                    {/* ALTO - Vermelho Claro */}
                    <tr>
                      <td className="py-2 px-3">12346</td>
                      <td className="py-2 px-3 bg-red-200 dark:bg-red-900/50 text-red-800 dark:text-red-200">[X] NÃO PÚBLICO</td>
                      <td className="py-2 px-3">87.5%</td>
                      <td className="py-2 px-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 font-bold">ALTO</td>
                      <td className="py-2 px-3">EMAIL, TELEFONE</td>
                    </tr>
                    {/* MODERADO - Amarelo */}
                    <tr>
                      <td className="py-2 px-3">12347</td>
                      <td className="py-2 px-3 bg-red-200 dark:bg-red-900/50 text-red-800 dark:text-red-200">[X] NÃO PÚBLICO</td>
                      <td className="py-2 px-3">65.0%</td>
                      <td className="py-2 px-3 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 font-bold">MODERADO</td>
                      <td className="py-2 px-3">MATRICULA_GDF</td>
                    </tr>
                    {/* BAIXO - Azul Claro */}
                    <tr>
                      <td className="py-2 px-3">12348</td>
                      <td className="py-2 px-3 bg-red-200 dark:bg-red-900/50 text-red-800 dark:text-red-200">[X] NÃO PÚBLICO</td>
                      <td className="py-2 px-3">45.0%</td>
                      <td className="py-2 px-3 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-bold">BAIXO</td>
                      <td className="py-2 px-3">PROCESSO_GDF</td>
                    </tr>
                    {/* SEGURO - Verde */}
                    <tr>
                      <td className="py-2 px-3">12349</td>
                      <td className="py-2 px-3 bg-green-200 dark:bg-green-900/50 text-green-800 dark:text-green-200">[OK] PÚBLICO</td>
                      <td className="py-2 px-3">100.0%</td>
                      <td className="py-2 px-3 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 font-bold">SEGURO</td>
                      <td className="py-2 px-3">-</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                📊 Células coloridas: <strong>Classificação</strong> (🟢 verde = PÚBLICO, 🔴 vermelho = NÃO PÚBLICO) |
                <strong> Nível de Risco</strong> (🔴 CRÍTICO, 🟠 ALTO, 🟡 MODERADO, 🔵 BAIXO, 🟢 SEGURO)
              </p>
            </div>
          </div>
        </TabsContent>

        {/* ============================================ */}
        {/* Tab 6: METODOLOGIA */}
        {/* ============================================ */}
        <TabsContent value="methodology" className="space-y-6 mt-6">
          <div className="gov-card">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary" />
              6. Metodologia do Motor Híbrido
            </h3>

            {/* Explicação do Motor */}
            <div className="p-5 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border-2 border-primary/30 rounded-xl mb-6">
              <h4 className="font-bold text-foreground mb-4 flex items-center gap-2">
                <Cpu className="w-5 h-5 text-primary" />
                Pipeline Ensemble de 9 Etapas
              </h4>
              <p className="text-sm text-muted-foreground mb-4">
                O Motor Híbrido v9.6.0 combina múltiplas camadas de análise para alcançar F1-Score = 1.0000:
              </p>

              <div className="grid md:grid-cols-3 gap-4">
                <div className="p-4 bg-background/50 rounded-lg border border-primary/20">
                  <div className="flex items-center gap-2 text-primary mb-2">
                    <Code className="w-5 h-5" />
                    <span className="font-semibold">1-2: Regex + DV</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Expressões regulares com <strong className="text-foreground">validação de dígito verificador (Módulo 11)</strong>
                    para CPF, CNPJ, CNH, etc.
                  </p>
                </div>
                <div className="p-4 bg-background/50 rounded-lg border border-warning/20">
                  <div className="flex items-center gap-2 text-warning mb-2">
                    <Cpu className="w-5 h-5" />
                    <span className="font-semibold">3-5: NER (BERT + NuNER + spaCy)</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Modelos de <strong className="text-foreground">Named Entity Recognition</strong>
                    para nomes, organizações e contexto semântico.
                  </p>
                </div>
                <div className="p-4 bg-background/50 rounded-lg border border-success/20">
                  <div className="flex items-center gap-2 text-success mb-2">
                    <Calculator className="w-5 h-5" />
                    <span className="font-semibold">6-9: Fusão + LLM</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    <strong className="text-foreground">Presidio + Gazetteer GDF</strong> com árbitro
                    <strong className="text-success"> Llama-3.2-3B</strong> para decisões ambíguas.
                  </p>
                </div>
              </div>
            </div>

            {/* Destaque: Aprendizado Automático */}
            <div className="p-5 bg-gradient-to-br from-blue-500/10 via-blue-500/5 to-transparent border-2 border-blue-500/30 rounded-xl mb-6">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-blue-500/20">
                  <RefreshCw className="w-7 h-7 text-blue-500" />
                </div>
                <div>
                  <h4 className="font-bold text-foreground text-lg flex items-center gap-2">
                    Aprendizado Automático (Feedback Loop)
                    <span className="px-2 py-0.5 bg-blue-500/20 text-blue-500 rounded text-xs font-medium">HUMAN-IN-THE-LOOP</span>
                  </h4>
                  <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                    Sistema de <strong className="text-foreground">recalibração contínua</strong> baseado em feedback humano.
                    Cada correção do usuário (CORRETO/INCORRETO/PARCIAL) é armazenada e, a cada
                    <strong className="text-blue-500"> 10+ feedbacks</strong>, o sistema treina calibradores
                    <strong className="text-foreground"> IsotonicRegression</strong> por tipo de entidade, melhorando a precisão dos scores de confiança.
                  </p>
                  <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                    <div className="p-2 bg-background/50 rounded text-center">
                      <span className="font-semibold text-foreground">POST /feedback</span>
                      <p className="text-muted-foreground">Envia correções</p>
                    </div>
                    <div className="p-2 bg-background/50 rounded text-center">
                      <span className="font-semibold text-foreground">Recalibração</span>
                      <p className="text-muted-foreground">A cada feedback</p>
                    </div>
                    <div className="p-2 bg-background/50 rounded text-center">
                      <span className="font-semibold text-foreground">GET /feedback/stats</span>
                      <p className="text-muted-foreground">Métricas de acurácia</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Destaque: Validação Matemática */}
            <div className="p-5 bg-gradient-to-br from-success/10 via-success/5 to-transparent border-2 border-success/30 rounded-xl mb-6">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-success/20">
                  <Calculator className="w-7 h-7 text-success" />
                </div>
                <div>
                  <h4 className="font-bold text-foreground text-lg flex items-center gap-2">
                    Validação Matemática de Documentos
                    <span className="px-2 py-0.5 bg-success/20 text-success rounded text-xs font-medium">DESTAQUE</span>
                  </h4>
                  <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                    Implementação de algoritmos de <strong className="text-foreground">dígito verificador (Módulo 11)</strong> para
                    validação matemática de CPF e CNPJ. Isso garante que apenas documentos <strong className="text-success">matematicamente válidos</strong> sejam
                    classificados como dados pessoais, eliminando falsos positivos causados por sequências numéricas aleatórias.
                  </p>
                </div>
              </div>
            </div>

            {/* Métricas de Performance */}
            <h4 className="font-semibold text-foreground mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              Métricas de Performance do Motor Híbrido
            </h4>

            <div className="overflow-x-auto mb-6">
              <table className="w-full text-sm border border-border rounded-lg overflow-hidden">
                <thead className="bg-muted">
                  <tr>
                    <th className="py-3 px-4 text-left font-semibold text-foreground">Métrica</th>
                    <th className="py-3 px-4 text-center font-semibold text-foreground">Valor</th>
                    <th className="py-3 px-4 text-left font-semibold text-foreground">Descrição</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4 font-medium text-foreground">F1-Score</td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-3 py-1 bg-success/10 text-success rounded-full text-lg font-bold">1.0000</span>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground text-xs">Perfeito equilíbrio entre Precisão (100%) e Recall (100%) no benchmark LGPD.</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4 font-medium text-foreground">Precisão</td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-3 py-1 bg-success/10 text-success rounded-full text-lg font-bold">100%</span>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground text-xs">VP=164, FP=0 — Zero falsos positivos no benchmark de 303 casos.</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4 font-medium text-foreground">Sensibilidade</td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-3 py-1 bg-success/10 text-success rounded-full text-lg font-bold">100%</span>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground text-xs">VP=164, FN=0 — Todos os PIIs detectados, zero falsos negativos.</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4 font-medium text-foreground">Casos de Benchmark</td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-lg font-bold">303</span>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground text-xs">164 com PII (VP) + 139 sem PII (VN) — Dataset balanceado.</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4 font-medium text-foreground">Testes Automatizados</td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-lg font-bold">452</span>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground text-xs">Cobertura de 30+ tipos de PII com validação matemática e edge cases.</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4 font-medium text-foreground">Tipos de PII</td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-3 py-1 bg-warning/10 text-warning rounded-full text-lg font-bold">30+</span>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground text-xs">CPF, RG, CNH, Email, Telefone, Nome, Endereço, Dados Bancários, etc.</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Fórmulas */}
            <div className="grid md:grid-cols-3 gap-4">
              <div className="p-4 border border-border rounded-lg">
                <h5 className="font-semibold text-foreground mb-2">Precisão</h5>
                <code className="block p-2 bg-muted rounded text-xs font-mono text-center">
                  Precisão = VP / (VP + FP)
                </code>
                <p className="text-xs text-muted-foreground mt-2 text-center">
                  VP = Verdadeiros Positivos | FP = Falsos Positivos
                </p>
              </div>
              <div className="p-4 border border-border rounded-lg">
                <h5 className="font-semibold text-foreground mb-2">Sensibilidade</h5>
                <code className="block p-2 bg-muted rounded text-xs font-mono text-center">
                  Sensibilidade = VP / (VP + FN)
                </code>
                <p className="text-xs text-muted-foreground mt-2 text-center">
                  VP = Verdadeiros Positivos | FN = Falsos Negativos
                </p>
              </div>
              <div className="p-4 border border-border rounded-lg">
                <h5 className="font-semibold text-foreground mb-2">F1-Score</h5>
                <code className="block p-2 bg-muted rounded text-xs font-mono text-center">
                  F1 = 2 × (P × R) / (P + R)
                </code>
                <p className="text-xs text-muted-foreground mt-2 text-center">
                  P = Precisão | R = Recall
                </p>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ============================================ */}
        {/* Tab 7: SEGURANÇA */}
        {/* ============================================ */}
        <TabsContent value="security" className="space-y-6 mt-6">
          <div className="gov-card">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Lock className="w-5 h-5 text-primary" />
              7. Segurança e Privacidade
            </h3>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Privacy by Design */}
              <div className="p-5 bg-gradient-to-br from-success/10 via-success/5 to-transparent border-2 border-success/30 rounded-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-xl bg-success/20">
                    <ShieldCheck className="w-6 h-6 text-success" />
                  </div>
                  <h4 className="font-bold text-foreground">Privacy by Design</h4>
                </div>

                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-success mt-0.5 shrink-0" />
                    <span>
                      <strong className="text-foreground">Processamento em Memória Volátil (RAM):</strong> Os dados enviados
                      são processados exclusivamente em memória RAM e destruídos imediatamente após o retorno da resposta.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-success mt-0.5 shrink-0" />
                    <span>
                      <strong className="text-foreground">Sem Persistência de Dados Sensíveis:</strong> Nenhum texto de
                      manifestação é gravado em banco de dados, arquivos de log ou qualquer meio persistente.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-success mt-0.5 shrink-0" />
                    <span>
                      <strong className="text-foreground">Sem Logs de Conteúdo:</strong> Os logs do sistema registram apenas
                      metadados operacionais (timestamps, status), nunca o conteúdo das manifestações.
                    </span>
                  </li>
                </ul>
              </div>

              {/* Comunicação Criptografada */}
              <div className="p-5 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border-2 border-primary/30 rounded-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-xl bg-primary/20">
                    <KeyRound className="w-6 h-6 text-primary" />
                  </div>
                  <h4 className="font-bold text-foreground">Comunicação Criptografada</h4>
                </div>

                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <Lock className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                    <span>
                      <strong className="text-foreground">Criptografia TLS 1.3:</strong> Toda comunicação entre o Frontend
                      e o Backend utiliza o protocolo de criptografia mais recente e seguro.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Lock className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                    <span>
                      <strong className="text-foreground">HTTPS Obrigatório:</strong> Todas as requisições são automaticamente
                      redirecionadas para conexão segura HTTPS.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Lock className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                    <span>
                      <strong className="text-foreground">Certificado SSL Válido:</strong> Emitido e gerenciado automaticamente
                      pela infraestrutura Hugging Face Spaces.
                    </span>
                  </li>
                </ul>
              </div>
            </div>

            {/* Padrão DSGOV */}
            <div className="p-5 bg-gradient-to-br from-warning/10 via-warning/5 to-transparent border-2 border-warning/30 rounded-xl mt-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 rounded-xl bg-warning/20">
                  <Layout className="w-6 h-6 text-warning" />
                </div>
                <h4 className="font-bold text-foreground">Design System Gov.br (DSGOV)</h4>
              </div>
              <ul className="space-y-3 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-warning mt-0.5 shrink-0" />
                  <span>
                    <strong className="text-foreground">Identidade Visual Gov.br:</strong> Cores institucionais (#1351B4, #0C326F),
                    tipografia e componentes seguindo o padrão do governo federal.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-warning mt-0.5 shrink-0" />
                  <span>
                    <strong className="text-foreground">Acessibilidade WCAG 2.1:</strong> Contraste adequado, navegação por teclado,
                    suporte a leitores de tela e modo escuro.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-warning mt-0.5 shrink-0" />
                  <span>
                    <strong className="text-foreground">Responsividade:</strong> Interface adaptável para desktop, tablet e mobile
                    seguindo breakpoints do DSGOV.
                  </span>
                </li>
              </ul>
            </div>

            {/* Conformidade */}
            <div className="mt-6 p-4 bg-muted/50 rounded-lg border border-border">
              <h4 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-success" /> Conformidade Legal e Técnica
              </h4>
              <div className="grid sm:grid-cols-4 gap-4 text-sm">
                <div className="flex items-center gap-2 p-3 bg-background rounded-lg">
                  <CheckCircle2 className="w-4 h-4 text-success shrink-0" />
                  <span className="text-muted-foreground"><strong className="text-foreground">LGPD</strong> — Lei 13.709/2018</span>
                </div>
                <div className="flex items-center gap-2 p-3 bg-background rounded-lg">
                  <CheckCircle2 className="w-4 h-4 text-success shrink-0" />
                  <span className="text-muted-foreground"><strong className="text-foreground">LAI</strong> — Lei 12.527/2011</span>
                </div>
                <div className="flex items-center gap-2 p-3 bg-background rounded-lg">
                  <CheckCircle2 className="w-4 h-4 text-success shrink-0" />
                  <span className="text-muted-foreground"><strong className="text-foreground">OWASP</strong> — Top 10</span>
                </div>
                <div className="flex items-center gap-2 p-3 bg-background rounded-lg">
                  <CheckCircle2 className="w-4 h-4 text-warning shrink-0" />
                  <span className="text-muted-foreground"><strong className="text-foreground">DSGOV</strong> — Gov.br</span>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ============================================ */}
        {/* Tab 8: API */}
        {/* ============================================ */}
        <TabsContent value="api" className="space-y-6 mt-6">
          <div className="gov-card">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Server className="w-5 h-5 text-primary" />
              8. Referência da API
            </h3>

            {/* Endpoint Principal */}
            <div className="p-5 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border-2 border-primary/30 rounded-xl mb-6">
              <div className="flex items-center gap-3 mb-4">
                <span className="px-3 py-1 bg-primary text-white rounded text-sm font-bold">POST</span>
                <code className="font-mono text-foreground font-semibold text-lg">/analyze</code>
              </div>

              <p className="text-sm text-muted-foreground mb-4">
                Endpoint principal para análise de texto individual. Retorna classificação, nível de risco,
                confiança e lista de identificadores encontrados.
              </p>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <h5 className="font-semibold text-foreground mb-2 text-sm flex items-center gap-2">
                    <FileInput className="w-4 h-4 text-primary" /> Request Payload
                  </h5>
                  <CodeBlock title="POST /analyze">{`{
  "text": "Meu CPF é 529.982.247-25 e 
           meu email é joao@email.com"
}`}</CodeBlock>
                </div>
                <div>
                  <h5 className="font-semibold text-foreground mb-2 text-sm flex items-center gap-2">
                    <FileOutput className="w-4 h-4 text-success" /> Response
                  </h5>
                  <CodeBlock title="200 OK">{`{
  "contem_pii": true,
  "nivel_risco": "CRÍTICO",
  "peso_risco": 5,
  "tipos_pii": ["CPF", "EMAIL"],
  "quantidade_pii": 2,
  "texto_anonimizado": "Meu CPF é [CPF_1] e...",
  "findings": [{...}],
  "confianca": {"min_entity": 0.95}
}`}</CodeBlock>
                </div>
              </div>
            </div>

            {/* Endpoints de Feedback e Aprendizado */}
            <h4 className="font-semibold text-foreground mb-3 flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-blue-500" /> Endpoints de Aprendizado Automático
            </h4>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="p-4 border border-blue-500/30 rounded-lg bg-blue-500/5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-success text-white rounded text-xs font-bold">POST</span>
                  <code className="font-mono text-foreground text-sm">/feedback</code>
                </div>
                <p className="text-xs text-muted-foreground">Envia validação humana (CORRETO/INCORRETO/PARCIAL). Dispara recalibração automática.</p>
              </div>
              <div className="p-4 border border-blue-500/30 rounded-lg bg-blue-500/5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-primary text-white rounded text-xs font-bold">GET</span>
                  <code className="font-mono text-foreground text-sm">/feedback/stats</code>
                </div>
                <p className="text-xs text-muted-foreground">Estatísticas de acurácia por tipo de entidade e taxa de falso positivo.</p>
              </div>
              <div className="p-4 border border-blue-500/30 rounded-lg bg-blue-500/5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-primary text-white rounded text-xs font-bold">GET</span>
                  <code className="font-mono text-foreground text-sm">/feedback/export</code>
                </div>
                <p className="text-xs text-muted-foreground">Exporta todos os feedbacks para dataset de treinamento.</p>
              </div>
              <div className="p-4 border border-blue-500/30 rounded-lg bg-blue-500/5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-success text-white rounded text-xs font-bold">POST</span>
                  <code className="font-mono text-foreground text-sm">/feedback/generate-dataset</code>
                </div>
                <p className="text-xs text-muted-foreground">Gera dataset JSONL/CSV a partir dos feedbacks coletados.</p>
              </div>
            </div>

            {/* Campos do Payload */}
            <h4 className="font-semibold text-foreground mb-3 flex items-center gap-2">
              <Database className="w-4 h-4 text-primary" /> Estrutura do Payload
            </h4>

            <div className="overflow-x-auto mb-6">
              <table className="w-full text-sm border border-border rounded-lg overflow-hidden">
                <thead className="bg-muted">
                  <tr>
                    <th className="py-3 px-4 text-left font-semibold text-foreground">Campo</th>
                    <th className="py-3 px-4 text-left font-semibold text-foreground">Tipo</th>
                    <th className="py-3 px-4 text-left font-semibold text-foreground">Descrição</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4"><code className="bg-primary/10 text-primary px-2 py-0.5 rounded text-xs">id</code></td>
                    <td className="py-3 px-4 text-muted-foreground">string</td>
                    <td className="py-3 px-4 text-muted-foreground">Identificador único da manifestação (preservado na resposta)</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4"><code className="bg-primary/10 text-primary px-2 py-0.5 rounded text-xs">text</code></td>
                    <td className="py-3 px-4 text-muted-foreground">string</td>
                    <td className="py-3 px-4 text-muted-foreground">Texto da manifestação a ser analisado</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Campos da Response */}
            <h4 className="font-semibold text-foreground mb-3 flex items-center gap-2">
              <FileOutput className="w-4 h-4 text-success" /> Estrutura da Response
            </h4>

            <div className="overflow-x-auto mb-6">
              <table className="w-full text-sm border border-border rounded-lg overflow-hidden">
                <thead className="bg-muted">
                  <tr>
                    <th className="py-3 px-4 text-left font-semibold text-foreground">Campo</th>
                    <th className="py-3 px-4 text-left font-semibold text-foreground">Tipo</th>
                    <th className="py-3 px-4 text-left font-semibold text-foreground">Descrição</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4"><code className="bg-success/10 text-success px-2 py-0.5 rounded text-xs">contem_pii</code></td>
                    <td className="py-3 px-4 text-muted-foreground">boolean</td>
                    <td className="py-3 px-4 text-muted-foreground">Indica se há PII no texto analisado</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4"><code className="bg-success/10 text-success px-2 py-0.5 rounded text-xs">nivel_risco</code></td>
                    <td className="py-3 px-4 text-muted-foreground">string</td>
                    <td className="py-3 px-4 text-muted-foreground">"SEGURO", "BAIXO", "MODERADO", "ALTO" ou "CRÍTICO"</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4"><code className="bg-success/10 text-success px-2 py-0.5 rounded text-xs">peso_risco</code></td>
                    <td className="py-3 px-4 text-muted-foreground">number</td>
                    <td className="py-3 px-4 text-muted-foreground">0 (seguro), 1-2 (baixo), 3 (moderado), 4 (alto), 5 (crítico)</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4"><code className="bg-success/10 text-success px-2 py-0.5 rounded text-xs">tipos_pii</code></td>
                    <td className="py-3 px-4 text-muted-foreground">array</td>
                    <td className="py-3 px-4 text-muted-foreground">Lista de tipos de PII detectados (CPF, EMAIL, etc.)</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4"><code className="bg-success/10 text-success px-2 py-0.5 rounded text-xs">texto_anonimizado</code></td>
                    <td className="py-3 px-4 text-muted-foreground">string</td>
                    <td className="py-3 px-4 text-muted-foreground">Texto com PIIs substituídos por placeholders</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4"><code className="bg-success/10 text-success px-2 py-0.5 rounded text-xs">findings</code></td>
                    <td className="py-3 px-4 text-muted-foreground">array</td>
                    <td className="py-3 px-4 text-muted-foreground">Detalhes de cada PII: tipo, valor, início, fim, confidence</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4"><code className="bg-success/10 text-success px-2 py-0.5 rounded text-xs">confianca</code></td>
                    <td className="py-3 px-4 text-muted-foreground">object</td>
                    <td className="py-3 px-4 text-muted-foreground">Scores: min_entity, all_found, no_pii (0-1)</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Níveis de Risco */}
            <h4 className="font-semibold text-foreground mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-warning" /> Níveis de Risco
            </h4>

            <div className="overflow-x-auto">
              <table className="w-full text-sm border border-border rounded-lg overflow-hidden">
                <thead className="bg-muted">
                  <tr>
                    <th className="py-3 px-4 text-left font-semibold text-foreground">Nível</th>
                    <th className="py-3 px-4 text-left font-semibold text-foreground">Peso</th>
                    <th className="py-3 px-4 text-left font-semibold text-foreground">Tipos de PII</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t border-border bg-red-50 dark:bg-red-950/20">
                    <td className="py-3 px-4"><span className="text-red-600 font-bold">🔴 CRÍTICO</span></td>
                    <td className="py-3 px-4 font-bold">5</td>
                    <td className="py-3 px-4 text-muted-foreground">CPF, RG, CNH, Passaporte, PIS, CNS, Dados Sensíveis LGPD</td>
                  </tr>
                  <tr className="border-t border-border bg-orange-50 dark:bg-orange-950/20">
                    <td className="py-3 px-4"><span className="text-orange-600 font-bold">🟠 ALTO</span></td>
                    <td className="py-3 px-4 font-bold">4</td>
                    <td className="py-3 px-4 text-muted-foreground">Email, Telefone, Endereço, Nome Pessoal</td>
                  </tr>
                  <tr className="border-t border-border bg-yellow-50 dark:bg-yellow-950/20">
                    <td className="py-3 px-4"><span className="text-yellow-600 font-bold">🟡 MODERADO</span></td>
                    <td className="py-3 px-4 font-bold">3</td>
                    <td className="py-3 px-4 text-muted-foreground">Placa, Data de Nascimento, Processo CNJ</td>
                  </tr>
                  <tr className="border-t border-border bg-blue-50 dark:bg-blue-950/20">
                    <td className="py-3 px-4"><span className="text-blue-600 font-bold">🔵 BAIXO</span></td>
                    <td className="py-3 px-4 font-bold">1-2</td>
                    <td className="py-3 px-4 text-muted-foreground">IP, GPS, User-Agent, Identificadores Indiretos</td>
                  </tr>
                  <tr className="border-t border-border bg-green-50 dark:bg-green-950/20">
                    <td className="py-3 px-4"><span className="text-green-600 font-bold">🟢 SEGURO</span></td>
                    <td className="py-3 px-4 font-bold">0</td>
                    <td className="py-3 px-4 text-muted-foreground">Nenhum PII detectado</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </TabsContent>
      </Tabs >

      {/* GitHub Links */}
      <div className="gov-card">
        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <Github className="w-5 h-5 text-primary" />
          Repositórios e Recursos
        </h3>
        <div className="grid md:grid-cols-2 gap-4">
          <DocLink
            href="https://github.com/marinhothiago/desafio-participa-df"
            icon={<Shield className="w-5 h-5" />}
            title="Repositório Principal"
            description="Monorepo completo: Backend (FastAPI) + Frontend (React) com Docker."
          />
          <DocLink
            href="https://huggingface.co/spaces/marinhothiago/desafio-participa-df"
            icon={<Layout className="w-5 h-5" />}
            title="Hugging Face Spaces"
            description="Backend hospedado com Swagger UI para testes da API."
          />
        </div>
      </div>
    </div >
  );
}
