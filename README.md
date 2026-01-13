# 🛡️ Projeto Participa DF: Inteligência Artificial para Transparência Ativa

[![Status do Deploy](https://img.shields.io/badge/Status-Online-brightgreen)](https://marinhothiago.github.io/desafio-participa-df/)
[![Licença](https://img.shields.io/badge/Licença-LGPD%20Compliance-blue)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

## 📝 Visão Geral do Projeto

Esta solução foi desenvolvida para o **Desafio Participa DF**, focando na proteção de dados sensíveis (PII - Personally Identifiable Information) em textos de manifestações públicas. O objetivo é garantir a **Transparência Ativa** (LAI), permitindo que o Governo do Distrito Federal publique informações úteis à sociedade enquanto protege rigorosamente a privacidade do cidadão (LGPD).

### 🌟 Diferenciais da Solução

- **Motor Híbrido:** Combina Processamento de Linguagem Natural (IA) com validações matemáticas rigorosas para CPFs e documentos
- **Arquitetura Monorepo:** Organização profissional que integra Frontend e Backend em um único ecossistema
- **Design System GOV.BR:** Interface intuitiva que segue o padrão oficial de identidade visual do Governo Federal

---

## 🏗️ Arquitetura do Sistema

O projeto está estruturado como um **Monorepo**, garantindo rastreabilidade total:

- **`/frontend`**: Interface React hospedada no **GitHub Pages**. É onde o usuário interage com os gráficos e dashboards
- **`/backend`**: Motor de IA em Python (FastAPI + Docker) hospedado no **Hugging Face Spaces**. É o "cérebro" que processa anonimizações em tempo real

---

## 🛠️ Tecnologias e Ferramentas

### Frontend (Telas)

- **React 18 + Vite:** Velocidade e modernidade na navegação
- **Tailwind CSS + Shadcn/UI:** Interface limpa seguindo o padrão **DSGOV**
- **Recharts:** Gráficos interativos para visualização de métricas de privacidade

### Backend (Inteligência)

- **FastAPI:** Servidor de alta performance para resposta imediata
- **spaCy (Modelo pt_core_news_lg):** IA avançada para reconhecimento de entidades brasileiras
- **Docker:** Garantia de que o sistema rode da mesma forma em qualquer computador

---

## ⚙️ Como Executar o Projeto (Passo a Passo)

### 1. Configuração Inicial

```bash
# Clone o repositório
git clone https://github.com/marinhothiago/participa-df-pii.git
cd participa-df-pii
```

### 2. Rodando o Motor de IA (Backend)

```bash
cd backend

# Crie um ambiente virtual
python -m venv venv

# Ative e instale as dependências
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
python -m spacy download pt_core_news_lg

# Inicie o servidor
uvicorn api.main:app --reload
```

### 3. Rodando o Site (Frontend)

```bash
cd ../frontend
npm install
npm run dev
```

---

## 📊 Matriz de Risco e Classificação

O sistema classifica cada texto automaticamente baseado na severidade dos dados detectados:

| Nível de Risco | Dados Identificados | Ação Sugerida |
|---|---|---|
| **CRÍTICO** | CPF, Documentos Únicos | Bloqueio imediato para revisão |
| **MODERADO** | E-mail, Telefone, Endereços | Anonimização automática |
| **BAIXO** | Nomes pessoais isolados | Monitoramento |
| **SEGURO** | Termos institucionais / Sem PII | Publicação liberada |

---

## 🔒 Segurança e Privacidade

Este projeto foi construído sob o princípio de **Privacy by Design**:

- **Processamento Efêmero:** Nenhum dado pessoal é armazenado no banco de dados após a análise
- **Anonimização em Lote:** Capacidade de processar grandes volumes de arquivos CSV/XLSX preservando o ID original para auditoria

---

## 👨‍💻 Desenvolvedor

Thiago Marinho - Desenvolvido para o Desafio Participa-DF (Hackathon CGDF)
