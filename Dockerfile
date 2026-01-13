# Usa uma imagem leve do Python
FROM python:3.10-slim

# Define a pasta de trabalho
WORKDIR /app

# Copia os arquivos de requisitos e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código do backend
COPY . .

# Expõe a porta que o FastAPI usa
EXPOSE 7860

# Comando para rodar a API (O Hugging Face usa a porta 7860 por padrão)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]