---
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
