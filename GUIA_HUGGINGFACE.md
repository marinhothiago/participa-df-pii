# 📤 Guia de Upload para Hugging Face

## ✅ Pré-requisitos

1. **Conta Hugging Face**
   - https://huggingface.co/join
   - Crie sua conta gratuita

2. **Token de Acesso**
   - Acesse: https://huggingface.co/settings/tokens
   - Clique em "New token"
   - Copie o token (mantenha em segurança!)

## 🚀 Opção 1: Upload via Hugging Face Web Interface (Recomendado)

### Passo 1: Criar o Space
1. Acesse https://huggingface.co/spaces
2. Clique em **"Create new Space"**
3. Preencha:
   - **Space name**: `participa-df-pii-detector`
   - **License**: MIT
   - **SDK**: Docker (selecione!)
   - **Visibility**: Public
4. Clique em **"Create Space"**

### Passo 2: Fazer Upload dos Arquivos
1. Na página do Space, clique em **"Files and versions"**
2. Clique em **"Upload file"** (ou "Upload folder")
3. Selecione todos os arquivos da pasta `hf_upload/`:
   - `Dockerfile`
   - `README.md`
   - `requirements.txt`
   - `main_cli.py`
   - `test_metrics.py`
   - Pasta `src/`
   - Pasta `data/`

4. Clique em **"Upload"**

### Passo 3: Aguarde o Build
- Hugging Face fará build automático
- Você verá o progresso na aba "Logs"
- Quando terminar, seu Space estará ativo!

---

## 🚀 Opção 2: Upload via Git (Avançado)

### Passo 1: Adicionar remoto do Hugging Face
```bash
cd projeto-participa-df

# Substitua SEU_USER pelo seu username
git remote add hf https://huggingface.co/spaces/SEU_USER/participa-df-pii-detector
```

### Passo 2: Fazer Push
```bash
git push hf main -f
```

---

## 🚀 Opção 3: Upload via CLI (Programático)

```bash
# 1. Configure o token
$env:HF_TOKEN = "seu_token_aqui"

# 2. Execute o script de upload
python push_to_huggingface.py
```

---

## ✨ O que será deployado?

```
Space no Hugging Face:
├── Docker Container rodando
├── Backend PII Detector v8.6
├── 100% Acurácia garantida
├── Pronto para Hackathon
└── Documentação completa
```

---

## 📊 Resultado Esperado

Após upload bem-sucedido:

```
🎉 PII Detector Online!
  • URL: https://huggingface.co/spaces/SEU_USER/participa-df-pii-detector
  • Status: ✅ Running
  • Acurácia: 100% (112/112 testes)
  • Versão: v8.6
```

---

## 🔧 Troubleshooting

### Build falhou?
- Verifique o `Dockerfile` em `hf_upload/`
- Veja os logs em "Runtime logs"
- Certifique-se que `requirements.txt` está correto

### Container não inicia?
- Verifique porta: deve ser `8000` por padrão
- Veja se há erros em `main_cli.py`

### Erro de memória?
- Hugging Face free tier: ~16GB RAM
- Remova modelos não essenciais se necessário

---

## 📝 Estrutura de Arquivos

```
hf_upload/
├── Dockerfile           # Config do container
├── README.md            # Documentação
├── requirements.txt     # Dependências Python
├── main_cli.py          # CLI principal
├── test_metrics.py      # Suite de testes
├── src/
│   ├── detector.py      # Detector PII (v8.6)
│   ├── allow_list.py    # Blocklist
│   └── __init__.py
└── data/
    ├── input/           # Pasta para input
    └── output/          # Pasta para resultados
```

---

## 🎯 Próximas Etapas

1. ✅ Docker build: **COMPLETO**
2. ⏭️ Upload para Hugging Face: **VOCÊ ESTÁ AQUI**
3. ⏭️ Testar no Space
4. ⏭️ Documentar no README
5. ⏭️ Apresentar no Hackathon!

---

**Dúvidas?**
- Docs Hugging Face: https://huggingface.co/docs/hub/spaces
- Issues no GitHub: https://github.com/marinhothiago/desafio-participa-df

🚀 **Boa sorte no Hackathon Participa DF!**
