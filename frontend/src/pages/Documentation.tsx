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
  FolderTree,
  Github,
  Globe,
  Hash,
  KeyRound,
  Layers,
  Layout,
  Lock,
  Package, Play,
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
              <div className="grid md:grid-cols-3 gap-3 p-4 bg-muted/30 rounded-lg mb-4">
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
            <CodeBlock title="backend-desafio-participa-df/">{`backend-desafio-participa-df/
├── api/
│   └── main.py              # Gateway da API (FastAPI)
│
├── src/
│   ├── detector.py          # Core do Motor de Detecção (NLP + Regex + Módulo 11)
│   └── allow_list.py        # Lista de termos públicos permitidos
│
├── main_cli.py              # Interface CLI para processamento em Lote
├── requirements.txt         # Dependências Python
└── README.md                # Documentação do projeto`}</CodeBlock>

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
          </div>
        </TabsContent>

        {/* ============================================ */}
        {/* Tab 3: INSTALAÇÃO (Critério 8.1.5.3.1) */}
        {/* ============================================ */}
        <TabsContent value="installation" className="space-y-6 mt-6">
          <div className="gov-card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                <Package className="w-5 h-5 text-primary" />
                3. Guia de Instalação
              </h3>
              <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-medium">
                Critério 8.1.5.3.1
              </span>
            </div>

            {/* Pré-requisitos */}
            <div className="mb-6">
              <h4 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-success" />
                Pré-requisitos
              </h4>
              <div className="flex flex-wrap gap-3 mb-4">
                <SoftwareBadge name="Docker" version="24.0+" color="primary" />
                <SoftwareBadge name="Docker Compose" version="2.20+" color="success" />
                <SoftwareBadge name="Git" version="2.40+" color="warning" />
              </div>
              <p className="text-sm text-muted-foreground">
                <strong className="text-foreground">⚡ Para avaliadores:</strong> Apenas Docker é necessário para rodar o projeto completo.
              </p>
            </div>

            {/* Comandos Sequenciais */}
            <div className="space-y-4">
              <h4 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-primary" />
                Instalação via Docker (Recomendado)
              </h4>

              <div className="space-y-4">
                {/* Passo 1 */}
                <div className="p-4 bg-muted/50 rounded-lg border-l-4 border-primary">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-xs font-bold">1</span>
                    <span className="font-semibold text-foreground">Clonar o Repositório</span>
                  </div>
                  <CodeBlock>{`git clone https://github.com/marinhothiago/desafio-participa-df.git
cd desafio-participa-df`}</CodeBlock>
                </div>

                {/* Passo 2 */}
                <div className="p-4 bg-muted/50 rounded-lg border-l-4 border-success">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-6 h-6 bg-success text-white rounded-full flex items-center justify-center text-xs font-bold">2</span>
                    <span className="font-semibold text-foreground">Subir os Containers (Backend + Frontend)</span>
                  </div>
                  <CodeBlock>{`docker compose up --build`}</CodeBlock>
                  <p className="text-xs text-muted-foreground mt-2">
                    Aguarde o download das imagens (~2-5 minutos na primeira vez).
                  </p>
                </div>

                {/* URLs */}
                <div className="p-4 bg-muted/50 rounded-lg border-l-4 border-warning">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-6 h-6 bg-warning text-white rounded-full flex items-center justify-center text-xs font-bold">✓</span>
                    <span className="font-semibold text-foreground">Verificar se está funcionando</span>
                  </div>
                  <div className="grid md:grid-cols-3 gap-3 mt-3">
                    <div className="text-center p-3 bg-background rounded-lg">
                      <p className="font-medium text-foreground text-sm">Frontend</p>
                      <code className="text-xs text-primary">http://localhost:80</code>
                    </div>
                    <div className="text-center p-3 bg-background rounded-lg">
                      <p className="font-medium text-foreground text-sm">Backend API</p>
                      <code className="text-xs text-success">http://localhost:7860</code>
                    </div>
                    <div className="text-center p-3 bg-background rounded-lg">
                      <p className="font-medium text-foreground text-sm">Swagger Docs</p>
                      <code className="text-xs text-warning">http://localhost:7860/docs</code>
                    </div>
                  </div>
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

            <div className="grid lg:grid-cols-2 gap-6">
              {/* Entrada */}
              <div className="p-5 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border-2 border-primary/30 rounded-xl">
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

              {/* Saída */}
              <div className="p-5 bg-gradient-to-br from-success/10 via-success/5 to-transparent border-2 border-success/30 rounded-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-success/20">
                    <FileOutput className="w-6 h-6 text-success" />
                  </div>
                  <div>
                    <h4 className="font-bold text-foreground">Saída</h4>
                    <p className="text-xs text-muted-foreground">JSON estruturado com análise</p>
                  </div>
                </div>

                <p className="text-sm text-muted-foreground mb-4">
                  Objeto JSON contendo classificação, risco, confiança e detalhes dos achados:
                </p>

                <CodeBlock title="Response JSON">{`{
  "classificacao": "NAO_PUBLICO",
  "risco": "CRITICO",
  "confianca": 0.98,
  "detalhes": [
    {
      "tipo": "CPF",
      "valor": "123.456.789-00"
    },
    {
      "tipo": "NOME_PESSOAL",
      "valor": "José Silva"
    }
  ]
}`}</CodeBlock>
              </div>
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
                    <td className="py-3 px-4 text-muted-foreground text-xs">Perfeito equilíbrio entre Precisão e Recall no benchmark LGPD.</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4 font-medium text-foreground">Testes Automatizados</td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-lg font-bold">452</span>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground text-xs">Cobertura de 156 tipos de PII com validação matemática e edge cases.</td>
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

            {/* Conformidade */}
            <div className="mt-6 p-4 bg-muted/50 rounded-lg border border-border">
              <h4 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-success" /> Conformidade Legal
              </h4>
              <div className="grid sm:grid-cols-3 gap-4 text-sm">
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
                  <span className="text-muted-foreground"><strong className="text-foreground">OWASP</strong> — Boas práticas</span>
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

            {/* Outros Endpoints */}
            <div className="grid md:grid-cols-2 gap-4 mb-6">
              <div className="p-4 border border-border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-success text-white rounded text-xs font-bold">POST</span>
                  <code className="font-mono text-foreground text-sm">/feedback</code>
                </div>
                <p className="text-xs text-muted-foreground">Envia correção do usuário (CORRETO/INCORRETO) para aprendizado contínuo.</p>
              </div>
              <div className="p-4 border border-border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-primary text-white rounded text-xs font-bold">GET</span>
                  <code className="font-mono text-foreground text-sm">/feedback/stats</code>
                </div>
                <p className="text-xs text-muted-foreground">Retorna estatísticas de feedbacks e taxa de acurácia percebida.</p>
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
                    <td className="py-3 px-4 text-muted-foreground">"SEGURO", "MODERADO", "ALTO" ou "CRÍTICO"</td>
                  </tr>
                  <tr className="border-t border-border">
                    <td className="py-3 px-4"><code className="bg-success/10 text-success px-2 py-0.5 rounded text-xs">peso_risco</code></td>
                    <td className="py-3 px-4 text-muted-foreground">number</td>
                    <td className="py-3 px-4 text-muted-foreground">0 (seguro), 3 (moderado), 4 (alto), 5 (crítico)</td>
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
                    <td className="py-3 px-4 text-muted-foreground">CPF, RG, CNH, Passaporte, PIS, CNS</td>
                  </tr>
                  <tr className="border-t border-border bg-orange-50 dark:bg-orange-950/20">
                    <td className="py-3 px-4"><span className="text-orange-600 font-bold">🟠 ALTO</span></td>
                    <td className="py-3 px-4 font-bold">4</td>
                    <td className="py-3 px-4 text-muted-foreground">Email, Telefone, Endereço, Nome</td>
                  </tr>
                  <tr className="border-t border-border bg-yellow-50 dark:bg-yellow-950/20">
                    <td className="py-3 px-4"><span className="text-yellow-600 font-bold">🟡 MODERADO</span></td>
                    <td className="py-3 px-4 font-bold">3</td>
                    <td className="py-3 px-4 text-muted-foreground">Placa, Data de Nascimento, Processo</td>
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
            href="https://huggingface.co/spaces/thiagomarinho/participa-df"
            icon={<Layout className="w-5 h-5" />}
            title="Hugging Face Spaces"
            description="Backend hospedado com Swagger UI para testes da API."
          />
        </div>
      </div>
    </div >
  );
}
