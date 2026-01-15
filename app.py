#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry point para HuggingFace Spaces
Inicia o servidor FastAPI do backend PII Detector
"""

import subprocess
import sys
import os

# Configurar variáveis de ambiente para GPU/CPU
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Iniciar o servidor FastAPI
def main():
    """Inicia o servidor na porta 7860 (padrão HuggingFace)"""
    
    # Navegar para o backend
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    
    # Comando para iniciar uvicorn
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'api.main:app',
        '--host', '0.0.0.0',
        '--port', '7860',
        '--reload'
    ]
    
    try:
        # Executar o servidor
        subprocess.run(cmd, cwd=backend_dir, check=True)
    except KeyboardInterrupt:
        print("\n\n✅ Servidor interrompido")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
