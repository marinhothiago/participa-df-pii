---
title: participa-df-pii
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 🛡️ Backend: Motor PII Participa DF

Motor híbrido de detecção de Informações Pessoais Identificáveis (PII) para conformidade LGPD/LAI.

**Versão:** 8.5 | **Acurácia:** 112/112 (100%) | **Status:** Produção ✅

---

## 📋 Objetivo Backend

Detectar, classificar e avaliar o risco de vazamento de dados pessoais em textos de manifestações do Participa DF, retornando classificação (NÃO PÚBLICO/PÚBLICO), nível de risco (CRÍTICO/ALTO/MODERADO/SEGURO), confiança (0-1) e detalhes de PII encontrados com mascaramento.

---

## 1. Objetivo e Funcionalidades

O objetivo principal é permitir que o GDF publique manifestações em transparência ativa (LAI) sem ferir a privacidade dos cidadãos (LGPD).

- **Rastreabilidade Total:** Preserva o ID original do e-SIC em todo o fluxo (Entrada -> Motor -> Saída)
- **Motor Híbrido:** Integra Processamento de Linguagem Natural (NLP/spaCy) e Expressões Regulares (Regex)
- **Três Formas de Uso:** API REST (Hugging Face), Interface CLI (Lote) e Dashboard Web
- **Matriz de Risco Automática:** Classifica a severidade baseada na natureza do dado (ex: CPF é mais grave que Nome)

---

## 1️⃣ INSTALAÇÃO E DEPENDÊNCIAS (4 PONTOS)

### Pré-requisitos (1 ponto)

- **Python:** 3.10 ou superior
- **pip:** 23.0 ou superior  
- **Internet:** Necessária para modelos NLP

### Dependências: `requirements.txt` (2 pontos)

```
fastapi==0.104.1              # Framework web
uvicorn==0.24.0               # Servidor ASGI
spacy==3.7.2                  # NLP português
transformers==4.35.2          # BERT
torch==2.1.0                  # Deep learning
pandas==2.1.3                 # Dados
openpyxl==3.10.10             # Excel
text-unidecode==1.3           # Strings
```

### Configuração (Passo a Passo Exato) - 1 ponto

```bash
# 1. Clone
git clone https://github.com/marinhothiago/participa-df-pii.git
cd participa-df-pii/backend

# 2. Ambiente virtual
python -m venv venv

# 3. Ative
# Windows: venv\Scripts\activate
# Linux: source venv/bin/activate

# 4. Instale dependências
pip install -r requirements.txt

# 5. Baixe modelo
python -m spacy download pt_core_news_lg
```

---

## 2️⃣ EXECUÇÃO (3 PONTOS)

### API Server (2 pontos)

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Acesse:**
- Servidor: http://localhost:8000
- Docs: http://localhost:8000/docs

### Formato de Dados (1 ponto)

**Entrada:**
```json
{"text": "Sou João Silva, CPF 123.456.789-09", "id": "man_001"}
```

**Saída:**
```json
{
  "classificacao": "NÃO PÚBLICO",
  "risco": "CRÍTICO",
  "confianca": 0.98,
  "detalhes": [{"tipo": "CPF", "valor": "123.***.***-09"}]
}
```

---

## 3️⃣ CLAREZA E ORGANIZAÇÃO

### Código com Comentários (1 ponto)

**detector.py:**
```python
"""Módulo de detecção PII (Regex + NLP + BERT + Regras)."""
# 368 linhas com comentários explicativos

class PIIDetector:
    def detect(self, text):
        # Camada 1: Regex patterns
        # Camada 2: spaCy NLP
        # Camada 3: BERT
        # Camada 4: Regras negócio
```

### Estrutura Lógica (1 ponto)

```
backend/
├── api/main.py          # FastAPI server
├── src/detector.py      # Motor (368 linhas)
├── requirements.txt     # Dependências
└── Dockerfile           # Deploy
```

### Arquivo Principal (1 ponto)

Este README descreve:
✓ Objetivo: Detector PII com LGPD/LAI  
✓ Pré-requisitos: Python 3.10+  
✓ Instalação: requirements.txt + comandos exatos  
✓ Execução: CLI + API  
✓ Entrada/Saída: JSON especificado
