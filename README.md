---
title: participa-df-pii
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 🛡️ Motor PII Desafio Participa-DF

**Inteligência Híbrida para Proteção de Dados Pessoais com Rastreabilidade e-SIC**

Este projeto é uma solução de conformidade com a LGPD desenvolvida para o **Desafio Participa-DF (Hackathon)**. O sistema identifica, classifica e avalia o risco de vazamento de dados pessoais (PII) em textos de manifestações, garantindo que o ID original da Controladoria seja preservado para fins de auditoria.

---

## 1. Objetivo e Funcionalidades

O objetivo principal é permitir que o GDF publique manifestações em transparência ativa (LAI) sem ferir a privacidade dos cidadãos (LGPD).

- **Rastreabilidade Total:** Preserva o ID original do e-SIC em todo o fluxo (Entrada -> Motor -> Saída)
- **Motor Híbrido:** Integra Processamento de Linguagem Natural (NLP/spaCy) e Expressões Regulares (Regex)
- **Três Formas de Uso:** API REST (Hugging Face), Interface CLI (Lote) e Dashboard Web (Lovable)
- **Matriz de Risco Automática:** Classifica a severidade baseada na natureza do dado (ex: CPF é mais grave que Nome)

---

## 2. Estrutura de Arquivos e Organização

A estrutura foi desenhada para garantir modularidade e facilidade de manutenção:

```
.
├── api/
│   └── main.py              # Interface da API FastAPI (Suporta ID e Texto)
├── src/
│   ├── detector.py          # O "Cérebro": Motor de detecção e classificação
│   └── allow_list.py        # Dicionário de exceções (Termos institucionais do GDF)
├── data/
│   ├── input/               # Pasta para arquivos de entrada (Excel/CSV)
│   └── output/              # Resultados processados e formatados
├── main_cli.py              # Script para processamento massivo via terminal
├── requirements.txt         # Gestão automatizada de dependências
├── Dockerfile               # Configuração para deploy (Hugging Face)
└── README.md                # Documentação técnica
```

---

## 3. Instruções de Instalação e Configuração

### 3.1. Pré-requisitos

- **Linguagem:** Python versão 3.10 ou superior
- **Gerenciador de Pacotes:** pip
- **Conexão com Internet:** Necessária para baixar o modelo de linguagem `pt_core_news_lg`

### 3.2. Configuração do Ambiente (Passo a Passo)

Siga estes comandos sequenciais no seu terminal:

```bash
# 1. Clone o repositório
git clone https://github.com/marinhothiago/participa-df-pii.git
cd participa-df-pii

# 2. Crie e ative o ambiente virtual
python -m venv venv
# No Windows: venv\Scripts\activate
# No Linux/Mac: source venv/bin/activate

# 3. Instale as dependências automaticamente
pip install -r requirements.txt

# 4. Baixe o modelo de processamento de linguagem natural (NLP)
python -m spacy download pt_core_news_lg
```

---

## 4. Instruções de Execução

### 4.1. Processamento em Lote (CLI)

Ideal para processar a amostra oficial da CGDF.

```bash
python main_cli.py --input AMOSTRA_e-SIC.xlsx --output resultado_analise
```

O sistema lerá automaticamente as colunas `ID` e `Texto Mascarado`.

### 4.2. Execução via Servidor Local (API)

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 4.3. Execução via Nuvem (Hugging Face)

A API está disponível publicamente para o Frontend Lovable em:

**Endpoint:** `https://marinhothiago-participa-df-pii.hf.space/analyze`

---

## 5. Formatos de Dados (Entrada e Saída)

### 5.1. Formato de Entrada (Input)

- **Arquivo:** `.xlsx` ou `.csv`
- **Colunas Necessárias:** `ID` (rastreabilidade) e `Texto Mascarado` (conteúdo)

### 5.2. Formato de Saída (JSON API)

```json
{
  "id": "LAI-114286/2012",
  "classificacao": "NÃO PÚBLICO",
  "risco": "CRÍTICO",
  "confianca": 0.99,
  "detalhes": [
    {
      "tipo": "CPF",
      "valor": "000.***.***-00",
      "conf": 0.99
    }
  ]
}
```

---

## 6. Metodologia e Matriz de Risco

O motor utiliza uma triagem em três camadas (Regex + NLP + Validação Matemática). A confiança para o nível SEGURO é fixada em 99% para garantir a precisão dos indicadores de performance.

| Nível | Identificadores Detectados | Ação Recomendada | Confiança |
|-------|----------------------------|------------------|-----------|
| **CRÍTICO** | CPF, Documentos Únicos | Bloqueio imediato | 95-99% |
| **ALTO** | RG, Endereço completo | Anonimização | 85-94% |
| **MODERADO** | E-mail, Telefone | Revisão Humana | 70-84% |
| **BAIXO** | Nomes pessoais isolados | Monitoramento | 60-69% |
| **SEGURO** | Nenhum dado detectado | Publicação liberada | 99% |

---

## 7. Segurança e Privacidade

- **Privacy by Design:** Processamento efêmero em memória RAM. Os textos são destruídos após a resposta da API
- **Eficiência:** O uso de `allow_list` reduz falsos positivos em nomes de órgãos públicos do Distrito Federal

---

## 8. Licença e Créditos

Desenvolvido por Thiago Marinho para o Desafio Participa-DF (CGDF).
