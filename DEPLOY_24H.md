# Deploy 24/7 - Bot de Vida Financeira

## 🚀 Opções de Deploy Gratuito

### 1. **Railway (Recomendado)**
- ✅ Gratuito para projetos pessoais
- ✅ Deploy automático
- ✅ Bot fica online 24/7

**Passos:**
1. Acesse [railway.app](https://railway.app)
2. Conecte sua conta GitHub
3. Crie novo projeto
4. Conecte este repositório
5. Adicione variável: `TELEGRAM_BOT_TOKEN`
6. Deploy automático!

### 2. **Render**
- ✅ Plano gratuito disponível
- ✅ Deploy via GitHub

**Passos:**
1. Acesse [render.com](https://render.com)
2. Conecte GitHub
3. Crie novo Web Service
4. Conecte este repositório
5. Adicione variável: `TELEGRAM_BOT_TOKEN`

### 3. **Heroku**
- ⚠️ Plano gratuito limitado
- ✅ Fácil de usar

**Passos:**
1. Instale Heroku CLI
2. `heroku create seu-bot-financeiro`
3. `heroku config:set TELEGRAM_BOT_TOKEN=seu_token`
4. `git push heroku main`

### 4. **VPS Gratuito**

#### Oracle Cloud (Sempre Gratuito)
- ✅ VPS gratuito para sempre
- ✅ 1GB RAM, 1 CPU

#### Google Cloud Platform
- ✅ $300 créditos gratuitos
- ✅ VPS gratuito por 1 ano

## 🐳 Deploy com Docker

### Local (para testar)
```bash
# Construir imagem
docker build -t bot-financeiro .

# Executar container
docker run -e TELEGRAM_BOT_TOKEN="seu_token" bot-financeiro
```

### Docker Compose
```bash
# Configurar token
export TELEGRAM_BOT_TOKEN="seu_token"

# Executar
docker-compose up -d
```

## 📱 Configuração do Token

### No Railway/Render/Heroku:
1. Vá em Settings/Environment Variables
2. Adicione: `TELEGRAM_BOT_TOKEN`
3. Valor: seu token do @BotFather

### No VPS:
```bash
export TELEGRAM_BOT_TOKEN="seu_token"
```

## 🎯 Recomendação

**Para começar:** Use **Railway** - é o mais simples e gratuito!

**Para produção:** Use **Oracle Cloud** - VPS gratuito para sempre.

## ✅ Checklist Deploy

- [ ] Token do bot configurado
- [ ] Repositório no GitHub
- [ ] Deploy configurado
- [ ] Bot respondendo no Telegram
- [ ] Teste com `/start`

## 🆘 Problemas Comuns

**Bot não responde:**
- Verifique se o token está correto
- Verifique se o deploy foi bem-sucedido
- Veja os logs do serviço

**Erro de dependências:**
- Use a versão simplificada (sem matplotlib/pandas)
- Verifique se o Dockerfile está correto
