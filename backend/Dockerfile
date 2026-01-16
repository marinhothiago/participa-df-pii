# ===========================================
# Participa DF - Backend Dockerfile
# Versão 9.2 - Ensemble 5 Fontes NER + Confiança Probabilística
# ===========================================

# 1. Base Python 3.10 (compatível com spaCy 3.8 e torch 2.1)
FROM python:3.10-slim

# 2. Variáveis de ambiente para otimização
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 3. Instala dependências do sistema (mínimas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# 4. Copia apenas requirements primeiro (cache de camadas Docker)
COPY requirements.txt .

# 5. Instalação de dependências em ordem otimizada
# 5.1 PyTorch CPU (antes do resto para cache)
RUN pip install --no-cache-dir \
    torch==2.1.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# 5.2 Dependências do requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5.3 Modelo spaCy para português (grande)
RUN pip install --no-cache-dir \
    https://github.com/explosion/spacy-models/releases/download/pt_core_news_lg-3.8.0/pt_core_news_lg-3.8.0-py3-none-any.whl

# 6. Pré-download dos modelos NER
# 6.1 BERT Davlan multilíngue (PER, ORG, LOC, DATE)
RUN python -c "\
from transformers import pipeline; \
print('📥 Baixando modelo BERT Davlan NER multilíngue...'); \
pipeline('ner', model='Davlan/bert-base-multilingual-cased-ner-hrl', aggregation_strategy='simple'); \
print('✅ BERT Davlan pronto!')"

# 6.2 NuNER pt-BR especializado em português brasileiro
RUN python -c "\
from transformers import pipeline; \
print('📥 Baixando modelo NuNER pt-BR...'); \
pipeline('ner', model='monilouise/ner_news_portuguese', aggregation_strategy='simple'); \
print('✅ NuNER pt-BR pronto!')"

# 7. Copia código da aplicação
COPY . .

# 8. Cria diretórios de dados com permissões
RUN mkdir -p /app/data/input /app/data/output && chmod -R 777 /app/data

# 9. Porta da aplicação (HuggingFace Spaces usa 7860)
EXPOSE 7860

# 10. Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# 11. Comando de inicialização
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
