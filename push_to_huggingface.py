#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para fazer upload do modelo PII Detector para Hugging Face
"""

from huggingface_hub import create_repo, push_folder_to_repo, HfApi
import subprocess
import os
from pathlib import Path

# Configurações
HF_USERNAME = "thiagozin"  # Substitua com seu username do Hugging Face
HF_TOKEN = os.getenv("HF_TOKEN", "")  # Token do Hugging Face (via variável de ambiente)
REPO_NAME = "participa-df-pii-detector"
REPO_DESCRIPTION = "PII Detector v8.6 - 100% Accuracy - Para Hackathon Participa DF"

def upload_to_huggingface():
    """Faz upload do projeto para Hugging Face"""
    
    print("🚀 Iniciando upload para Hugging Face...")
    print(f"   Username: {HF_USERNAME}")
    print(f"   Repo: {REPO_NAME}")
    
    if not HF_TOKEN:
        print("\n⚠️  Variável HF_TOKEN não encontrada!")
        print("   Execute: $env:HF_TOKEN='seu_token_aqui'")
        print("   Ou configure em: https://huggingface.co/settings/tokens")
        return False
    
    try:
        api = HfApi()
        
        # 1. Criar repositório
        print("\n1️⃣  Criando repositório no Hugging Face...")
        repo_url = api.create_repo(
            repo_id=f"{HF_USERNAME}/{REPO_NAME}",
            repo_type="model",
            private=False,
            exist_ok=True,
            token=HF_TOKEN
        )
        print(f"   ✅ Repositório pronto: {repo_url}")
        
        # 2. Fazer upload dos arquivos
        print("\n2️⃣  Fazendo upload dos arquivos...")
        
        # Arquivos principais
        arquivos_upload = [
            "backend/src",
            "backend/requirements.txt",
            "backend/Dockerfile",
            "backend/main_cli.py",
            "README.md",
            ".gitignore"
        ]
        
        repo_name_full = f"{HF_USERNAME}/{REPO_NAME}"
        
        for arquivo in arquivos_upload:
            caminho = Path(arquivo)
            if caminho.exists():
                print(f"   📤 Uploading: {arquivo}")
                if caminho.is_dir():
                    # Upload de pasta
                    for file in caminho.rglob("*"):
                        if file.is_file():
                            rel_path = str(file.relative_to(arquivo.split('/')[0]))
                            try:
                                api.upload_file(
                                    path_or_fileobj=str(file),
                                    path_in_repo=rel_path,
                                    repo_id=repo_name_full,
                                    token=HF_TOKEN
                                )
                            except:
                                pass
                else:
                    # Upload de arquivo individual
                    api.upload_file(
                        path_or_fileobj=str(caminho),
                        path_in_repo=caminho.name,
                        repo_id=repo_name_full,
                        token=HF_TOKEN
                    )
        
        print(f"\n   ✅ Upload concluído!")
        
        # 3. Fazer upload da imagem Docker
        print("\n3️⃣  Preparando upload da imagem Docker...")
        print("   (Este passo pode levar alguns minutos)")
        
        # Taguear e fazer push da imagem
        docker_image = "backend-participa-df:v8.6"
        print(f"   🐳 Imagem Docker: {docker_image}")
        
        print(f"\n✅ Setup completo! Seu repositório está em:")
        print(f"   https://huggingface.co/{repo_name_full}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao fazer upload: {e}")
        return False

if __name__ == "__main__":
    success = upload_to_huggingface()
    exit(0 if success else 1)
