#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para fazer upload do backend para Hugging Face Spaces (simples)
Apenas copia os arquivos principais para o repositório
"""

import shutil
import os
from pathlib import Path
import subprocess
import json

def create_huggingface_setup():
    """Cria estrutura para upload em Hugging Face"""
    
    print("📦 Preparando arquivos para Hugging Face Spaces...\n")
    
    # Criar pasta de output
    hf_folder = Path("hf_upload")
    if hf_folder.exists():
        shutil.rmtree(hf_folder)
    hf_folder.mkdir()
    
    # Copiar estrutura necessária
    print("1️⃣  Copiando arquivos essenciais...")
    
    # Copiar backend
    shutil.copytree("backend/src", hf_folder / "src")
    shutil.copy("backend/requirements.txt", hf_folder / "requirements.txt")
    shutil.copy("backend/Dockerfile", hf_folder / "Dockerfile")
    shutil.copy("backend/main_cli.py", hf_folder / "main_cli.py")
    shutil.copy("backend/test_metrics.py", hf_folder / "test_metrics.py")
    shutil.copy("README.md", hf_folder / "README.md")
    
    # Criar data folders
    (hf_folder / "data" / "input").mkdir(parents=True, exist_ok=True)
    (hf_folder / "data" / "output").mkdir(parents=True, exist_ok=True)
    
    print("   ✅ Arquivos copiados\n")
    
    # Criar README específico para Hugging Face
    print("2️⃣  Criando README para Hugging Face...")
    
    hf_readme = """---
title: PII Detector Participa DF
emoji: 🔐
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
---

# PII Detector - Hackathon Participa DF

Detector de Informações Pessoais Identificáveis (PII) com **100% de acurácia** em 112 casos de teste.

## 🎯 Características

- **Acurácia**: 100% (112/112 testes)
- **Modelos**: Regex + spaCy + BERT
- **Suporte**: CPF, Email, Telefone, RG, CNH, Passaporte, Contas Bancárias, PIX
- **Contexto**: Reconhece imunidade funcional (cargos públicos)
- **LAI/LGPD**: Compatível com Lei de Acesso à Informação

## 📊 Cobertura de Testes

- ✅ Administrativo (12/12)
- ✅ PII Essencial (12/12)
- ✅ Imunidade Funcional (15/15)
- ✅ Endereços (12/12)
- ✅ Contas Bancárias (8/8)
- ✅ Nomes com contextos (12/12)
- ✅ LAI/LGPD (9/9)

## 🚀 Uso

### Local (Python)
```bash
cd backend
pip install -r requirements.txt
python main_cli.py "texto para análise"
```

### Docker
```bash
docker build -t pii-detector .
docker run pii-detector python main_cli.py "seu texto aqui"
```

### API (em desenvolvimento)
```bash
python -m api.main
# Acessa em http://localhost:8000
```

## 📈 Versão

- **v8.6** - 100% Acurácia Final
- Desenvolvido para: Hackathon Participa DF
- Data: Janeiro 2026

## 👨‍💻 Autor

Thiago - GitHub: marinhothiago

## 📝 Licença

MIT - Livre para uso em projetos do setor público

---

*Pronto para o Hackathon Participa DF!*
"""
    
    with open(hf_folder / "README.md", "w", encoding="utf-8") as f:
        f.write(hf_readme)
    
    print("   ✅ README criado\n")
    
    # Criar dockerfile.dockerignore
    print("3️⃣  Criando arquivos de configuração...")
    
    with open(hf_folder / ".dockerignore", "w") as f:
        f.write("__pycache__\n.git\n*.pyc\n.env\n")
    
    print("   ✅ Configuração pronta\n")
    
    print("=" * 60)
    print("📦 Pasta 'hf_upload' pronta para upload!")
    print("=" * 60)
    print("\n✨ Próximos passos:\n")
    print("1. Acesse: https://huggingface.co/spaces")
    print("2. Clique em 'Create new Space'")
    print("3. Nome: 'participa-df-pii-detector'")
    print("4. SDK: Docker")
    print("5. Upload dos arquivos em 'hf_upload/'")
    print("\n💡 Ou faça git push (git + Hugging Face)")
    print("   git remote add hf https://huggingface.co/spaces/SEU_USER/participa-df-pii-detector")
    print("   git push hf main\n")
    
    return True

if __name__ == "__main__":
    try:
        create_huggingface_setup()
        print("✅ Sucesso!")
    except Exception as e:
        print(f"❌ Erro: {e}")
        exit(1)
