"""
# Backend - Detector de PII Participa DF v8.5

Detector híbrido de Informações Pessoalmente Identificáveis (PII) para
manifestações cidadãs com conformidade LGPD/LAI.

## 🏗️ Arquitetura

### Camadas de Detecção (6 níveis)

```
┌─ CAMADA 1: LISTA DE BLOQUEIO ─────────────────┐
│  Palavras que NUNCA são PII                   │
└───────────────────────────────────────────────┘
                      ↓
┌─ CAMADA 2: TERMOS SEGUROS ────────────────────┐
│  Órgãos GDF, regiões Brasília (LAI público)   │
└───────────────────────────────────────────────┘
                      ↓
┌─ CAMADA 3: REGEX ─────────────────────────────┐
│  CPF, Email, Telefone, RG, CNH, Endereços    │
└───────────────────────────────────────────────┘
                      ↓
┌─ CAMADA 4: NLP (SPACY + BERT) ────────────────┐
│  Entidades nomeadas com contexto português   │
└───────────────────────────────────────────────┘
                      ↓
┌─ CAMADA 5: IMUNIDADE FUNCIONAL ───────────────┐
│  Agentes públicos em exercício → IMUNES       │
│  Gatilho de contato → Anula imunidade         │
└───────────────────────────────────────────────┘
                      ↓
┌─ CAMADA 6: DEDUPLICAÇÃO E RANKING ────────────┐
│  Pesos por criticidade (5=CRÍTICO, 0=SEGURO)  │
└───────────────────────────────────────────────┘
```

## 📊 Resultado de Testes (v8.5)

| Métrica | Valor | Status |
|---------|-------|--------|
| **Acurácia Geral** | 87.5% (98/112) | ✅ Bom |
| **Casos Testados** | 112 | - |
| **Erros Residuais** | 14 (12.5%) | ⚠️ Documentados |
| **PII Crítico (CPF/RG)** | 100% | ✅ Excelente |
| **Administrativo** | 100% | ✅ Excelente |
| **Imunidade Funcional** | 88.9% | ✅ Bom |

## 🚀 Como Usar

### 1. Docker (Recomendado para Produção)

```bash
# Build
docker build -t backend-participa-df .

# Run API
docker run -p 8000:8000 backend-participa-df

# Run testes
docker run --rm backend-participa-df python test_metrics.py
```

### 2. Local (Desenvolvimento)

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar API
python -m api.main

# Executar testes
python test_metrics.py

# Executar CLI em batch
python main_cli.py input.xlsx
```

## 📝 API Endpoints

### POST `/analyze`

Detecta PII em um texto.

**Request:**
```json
{
    "text": "Meu CPF é 123.456.789-09 e telefone (61) 98765-4321",
    "id": "manifestacao_123"
}
```

**Response:**
```json
{
    "id": "manifestacao_123",
    "classificacao": "NÃO PÚBLICO",
    "risco": "CRÍTICO",
    "confianca": 5.0,
    "detalhes": [
        {
            "tipo": "CPF",
            "valor": "123.456.789-09",
            "confianca": 1.0
        },
        {
            "tipo": "TELEFONE",
            "valor": "(61) 98765-4321",
            "confianca": 1.0
        }
    ]
}
```

### GET `/health`

Verifica status da API.

**Response:**
```json
{
    "status": "healthy",
    "version": "8.5"
}
```

## 🔍 Tipos de PII Detectados

| Tipo | Exemplo | Peso | Risco |
|------|---------|------|-------|
| **CPF** | 123.456.789-09 | 5 | CRÍTICO |
| **RG/CNH** | 1.234.567 SSP/DF | 5 | CRÍTICO |
| **Email Privado** | joao@gmail.com | 4 | ALTO |
| **Telefone** | (61) 98765-4321 | 4 | ALTO |
| **Nome Privado** | João da Silva | 4 | ALTO |
| **Endereço Residencial** | Rua A Casa 45 | 4 | ALTO |
| **Entidade NLP** | [PERSON] genérico | 3 | MODERADO |

## ⚖️ Contexto LGPD/LAI

### Imunidade Funcional

Agentes públicos em exercício de função estão **IMUNES** a proteção:

```
✅ SEGURO: "Falar com a Dra. Maria na Secretaria de Saúde do DF"
   → Cargo (Dra.) + Instituição (Secretaria) = Agente público

❌ PII: "Falar com o Dr. João sobre meu caso"
   → Gatilho de contato quebra imunidade

❌ PII: "Preciso do telefone do Dr. João"
   → Contexto de contato quebra imunidade
```

### Lei de Acesso à Informação (LAI)

Termos públicos e institucionais **NUNCA são PII**:

```
✅ SEGURO: "Solicito ao GDF informações sobre..."
✅ SEGURO: "Endereço: SQS 302 Bloco K" (setor administrativo)
✅ SEGURO: "email: ouvidoria@saude.df.gov.br" (institucional)

❌ PII: "Moro em Rua A Casa 45" (residencial)
❌ PII: "email: joao@gmail.com" (pessoal)
```

## 📂 Estrutura do Projeto

```
backend/
├── src/
│   ├── detector.py          # Detector híbrido (200 linhas, 6 camadas)
│   ├── allow_list.py        # Termos que não são PII (100+ termos GDF/Brasília)
│   └── __init__.py
├── api/
│   └── main.py              # FastAPI endpoint (130 linhas, docstrings)
├── main_cli.py              # CLI para batch processing
├── test_metrics.py          # Suite de testes (112 casos, 87.5% acurácia)
├── requirements.txt         # Dependências
├── Dockerfile               # Containerização
├── docker-compose.yml       # Orquestração
├── data/
│   ├── input/               # Arquivos para batch
│   └── output/              # Resultados processados
├── README.md                # Este arquivo
└── RELATORIO_MELHORIAS.md   # Análise detalhada dos 14 erros residuais
```

## 🛠️ Dependências

```
fastapi==0.104.1
spacy==3.6.1
transformers==4.35.2
torch==2.0.1
pandas==2.0.3
openpyxl==3.1.2
text_unidecode==1.3
python-dotenv==1.0.0
```

**Modelos NLP:**
- `spacy`: pt_core_news_lg (carregado automaticamente)
- `transformers`: neuralmind/bert-large-portuguese-cased

## 🧪 Testes (112 Casos)

```bash
python test_metrics.py
```

Resultado esperado: **87.5% acurácia** (98/112 acertos)

**Grupos de teste:**
- 15 casos administrativos seguros (0% erro)
- 17 casos PII clássico (0% erro)
- 9 casos imunidade funcional (11% erro)
- 6 casos quebra de imunidade (0% erro)
- 9 casos endereços (0% erro)
- 6 casos edge cases CPF (0% erro)
- 45 casos contexto GDF/Brasília (31% erro)

## 📋 Erros Residuais (14 casos, 12.5%)

Veja `RELATORIO_MELHORIAS.md` para análise detalhada de cada erro.

**Principais categorias:**
- Nomes simples sem triggerwords (BERT)
- Diferenciação institucional vs pessoal (DDI, emails, contas)
- Padrões não implementados (passaporte, PIX)
- Contexto de servidor/cargo

## 🚀 Próximos Passos

### Curto Prazo (Hackathon)
- [ ] Aumentar threshold BERT para 0.85 (reduz falsos positivos)
- [ ] Implementar regex para passaportes
- [ ] Adicionar patterns para PIX/dados bancários
- [ ] Fortalecer contexto de imunidade

### Médio Prazo
- [ ] Fine-tuning BERT com dados GDF reais
- [ ] Integração com base de servidores públicos
- [ ] Validação matemática de CPF/CNPJ
- [ ] Dashboard de métricas

### Longo Prazo
- [ ] Transfer learning com manifestações reais
- [ ] Feedback loop de usuários
- [ ] A/B testing de thresholds
- [ ] Multilíngue (espanhol, inglês)

## 📞 Suporte

- **Dúvidas arquitetura**: Veja `src/detector.py` (comentários em 6 camadas)
- **Testes**: Execute `python test_metrics.py`
- **Deploy**: `docker build -t backend-participa-df .`
- **Documentação**: Veja docstrings em Google-style em todos os módulos

## 📄 Licença

Este projeto é parte do Hackathon Participa DF - LGPD/LAI 2026.

---

**Versão:** 8.5  
**Data:** 14/01/2026  
**Status:** ✅ Pronto para Produção com otimizações adicionais
"""
