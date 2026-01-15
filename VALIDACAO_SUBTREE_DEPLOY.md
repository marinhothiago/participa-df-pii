# ✅ Validação: Deploy Seletivo HuggingFace

## 📋 Checklist de Implementação

- [x] **Git Subtree Split** - Criado com sucesso
- [x] **HF Histórico Limpo** - Force push realizado
- [x] **Script deploy-hf.sh** - Atualizado e melhorado
- [x] **GitHub Actions** - Workflow criado (.github/workflows/deploy-hf.yml)
- [x] **Documentação** - SETUP_HF_AUTOMATION.md criado
- [ ] **Token HF Configurado** - Falta por fazer (manual)
- [ ] **Teste de Deploy** - Aguardando confirmação

---

## 🧪 Como Testar

### Teste 1: Manual (Sem GitHub Actions)

**Ambiente:** Seu computador local

```bash
# 1. Clonar repo
git clone https://github.com/marinhothiago/desafio-participa-df.git
cd desafio-participa-df

# 2. Fazer mudança no backend
echo "# test" >> backend/README.md

# 3. Fazer commit
git add backend/README.md
git commit -m "test: validate deploy"

# 4. Fazer push para GitHub
git push origin main

# 5. Fazer deploy manual para HF
./deploy-hf.sh

# 6. Verificar HuggingFace
# Abrir: https://huggingface.co/spaces/marinhothiago/participa-df-pii
# Verificar "Files and versions"
```

**Esperado:**
- ✅ Script executa sem erros
- ✅ HF recebe push
- ✅ Apenas conteúdo de `/backend/` presente

### Teste 2: Automático (GitHub Actions)

**Ambiente:** GitHub

```bash
# 1. Fazer mudança no backend
git checkout -b test/hf-deploy
echo "# auto deploy test" >> backend/README.md

# 2. Fazer commit e push
git add backend/README.md
git commit -m "test: trigger auto-deploy"
git push origin test/hf-deploy

# 3. Criar Pull Request
# Abrir GitHub → New Pull Request

# 4. Merge para main (isso dispara workflow)
# GitHub Actions iniciará automaticamente

# 5. Acompanhar em Actions
# https://github.com/marinhothiago/desafio-participa-df/actions
```

**Esperado:**
- ✅ Workflow `Deploy Backend to HuggingFace Spaces` dispara
- ✅ Todos os steps completam
- ✅ HF recebe push automaticamente

---

## 🔍 Verificações no HuggingFace

Após deploy, verificar que HF tem:

### ✅ Deve Conter
```
Files and versions:
├─ api/
│  └─ main.py           ✅
├─ src/
│  ├─ detector.py       ✅
│  ├─ allow_list.py     ✅
│  └─ __init__.py       ✅
├─ data/
│  ├─ input/            ✅
│  └─ output/           ✅
├─ requirements.txt     ✅
├─ Dockerfile           ✅
├─ README.md            ✅
└─ .gitignore           ✅
```

### ❌ NÃO Deve Conter
```
❌ frontend/
❌ .github/
❌ node_modules/
❌ venv/
❌ dist/
❌ .venv/
```

**Como Verificar:**
1. Ir a: https://huggingface.co/spaces/marinhothiago/participa-df-pii
2. Clique em **"Files and versions"**
3. Percorra a estrutura de arquivos
4. Confirme que apenas `/backend/` está presente

---

## 🚀 Deploy em Produção

### Configuração Obrigatória

Para que GitHub Actions funcione, siga os passos em [SETUP_HF_AUTOMATION.md](./SETUP_HF_AUTOMATION.md):

1. Criar token em HuggingFace
2. Adicionar como secret `HF_TOKEN` em GitHub
3. Fazer teste de deploy

### Workflow Automático

Após configuração:

```
Desenvolvedor faz push em /backend/
  ↓
GitHub Actions (automaticamente):
  1. Checkout código
  2. Criar subtree split
  3. Push para HF com HF_TOKEN
  4. Limpar arquivos temporários
  ↓
HuggingFace recebe apenas /backend/
  ↓
HF auto-rebuild e restart
```

### Manual Deploy (Alternativa)

Se GitHub Actions não estiver configurado:

```bash
./deploy-hf.sh              # Deploy normal
./deploy-hf.sh --force      # Force (se conflitar)
```

---

## 📊 Estrutura Implementada

```
┌─────────────────────────────────────────────────────┐
│                    Push /backend/                   │
└────────────┬────────────────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
  Manual       GitHub Actions
  ./deploy-     Workflow
  hf.sh        (.github/workflows/deploy-hf.yml)
      │             │
      └──────┬──────┘
             │
      ┌──────▼──────────┐
      │  Git Subtree    │
      │  Split Branch   │
      └──────┬──────────┘
             │
      ┌──────▼──────────────┐
      │  Force Push to HF   │
      │  (Limpa histórico)  │
      └──────┬──────────────┘
             │
      ┌──────▼──────────────┐
      │  HuggingFace       │
      │  Apenas /backend/   │
      │  Auto-rebuild      │
      └────────────────────┘
```

---

## 🔧 Troubleshooting

### Problema: "git subtree split failed"

**Causa:** Histórico git corrompido ou branch não existe

**Solução:**
```bash
git gc                    # Garbage collect
git fsck --full           # Validar integridade
./deploy-hf.sh --force    # Tentar novamente
```

### Problema: "Push rejected - non-fast-forward"

**Causa:** Histórico de HF conflita com local

**Solução:**
```bash
./deploy-hf.sh --force    # Force push (limpa HF)
```

### Problema: "HF_TOKEN not found"

**Causa:** Secret não configurado em GitHub

**Solução:**
1. Seguir [SETUP_HF_AUTOMATION.md](./SETUP_HF_AUTOMATION.md)
2. Criar token em HuggingFace
3. Adicionar como `HF_TOKEN` em GitHub Secrets
4. Tentar deploy novamente

### Problema: "Authentication failed"

**Causa:** Token inválido ou expirado

**Solução:**
1. Revog token em https://huggingface.co/settings/tokens
2. Criar novo token
3. Atualizar `HF_TOKEN` em GitHub

---

## 📈 Monitoramento

### Logs do GitHub Actions

Abrir: https://github.com/marinhothiago/desafio-participa-df/actions

Procurar por: `Deploy Backend to HuggingFace Spaces`

Verificar:
- ✅ Job `deploy` completa
- ✅ Steps todos com ✓
- ✅ Log contém "Deploy bem-sucedido"

### Logs do HuggingFace

Abrir: https://huggingface.co/spaces/marinhothiago/participa-df-pii/logs

Procurar por:
- ✅ Rebuild iniciado
- ✅ Build succeeded
- ✅ App running

---

## 📝 Próximos Passos

1. **Setup do HF_TOKEN** (OBRIGATÓRIO)
   - Seguir [SETUP_HF_AUTOMATION.md](./SETUP_HF_AUTOMATION.md)
   - Tempo: ~5 min

2. **Teste Manual**
   - Rodar `./deploy-hf.sh`
   - Verificar HuggingFace
   - Tempo: ~5 min

3. **Teste Automático**
   - Fazer push de teste
   - Acompanhar GitHub Actions
   - Verificar HF atualizado
   - Tempo: ~2 min

4. **Documentar para Time**
   - Compartilhar DEPLOY_STRATEGY.md
   - Treinar devs no workflow
   - Tempo: ~15 min

---

## ✨ Resumo

**Deploy Seletivo HuggingFace: ✅ IMPLEMENTADO**

- ✅ Git subtree funcional
- ✅ Script robusto (deploy-hf.sh)
- ✅ GitHub Actions criado
- ✅ Documentação completa
- ⏳ Aguardando HF_TOKEN setup (manual)

**Tempo para usar:**
- Setup: 5 min (HF_TOKEN)
- Deploy manual: 1 min (./deploy-hf.sh)
- Deploy automático: 0 min (automático ao push)

---

*Implementação concluída: 2024*
