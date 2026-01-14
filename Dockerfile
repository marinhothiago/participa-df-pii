# 1. Base leve
FROM python:3.10-slim

# 2. Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Instala dependências do sistema e limpa cache na mesma camada (CRÍTICO PARA REDUZIR TAMANHO)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 4. Copia requirements
COPY requirements.txt .

# 5. Instalação UNIFICADA para economizar camadas e espaço
# A flag --no-cache-dir é essencial para não salvar o cache do pip (~800MB)
RUN sed -i '/torch/d' requirements.txt && \
    pip install --no-cache-dir torch==2.1.0+cpu torchvision==0.16.0+cpu --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir https://github.com/explosion/spacy-models/releases/download/pt_core_news_lg-3.8.0/pt_core_news_lg-3.8.0-py3-none-any.whl

# 6. Pré-download do BERT (NeuralMind)
# Isso garante que o modelo esteja dentro da imagem, mas sem cache extra
RUN python -c "from transformers import pipeline; pipeline('ner', model='neuralmind/bert-large-portuguese-cased')"

# 7. Copia código
COPY . .

# 8. Permissões
RUN mkdir -p /app/data/output && chmod -R 777 /app/data

EXPOSE 7860

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]