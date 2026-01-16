# ===========================================
# Participa DF - Frontend Dockerfile
# Build: React + Vite → nginx
# ===========================================

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Instala dependências
COPY package*.json ./
COPY bun.lockb* ./
RUN npm ci || npm install

# Copia código e faz build
COPY . .
# Define base path para servir em /desafio-participa-df/
ENV VITE_BASE_PATH=/desafio-participa-df/
RUN npm run build

# Stage 2: Serve com nginx
FROM nginx:alpine

# Remove config default
RUN rm -rf /usr/share/nginx/html/*

# Copia build para subpasta /desafio-participa-df/
COPY --from=builder /app/dist /usr/share/nginx/html/desafio-participa-df

# Configuração nginx para SPA (React Router)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
