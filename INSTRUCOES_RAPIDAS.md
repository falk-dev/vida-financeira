# 🚀 Instruções Rápidas - Bot de Vida Financeira

## ⚡ Instalação Super Rápida

### 1. Instalar dependência única
```bash
pip install python-telegram-bot==20.7
```

### 2. Criar bot no Telegram
1. Acesse [@BotFather](https://t.me/BotFather)
2. Digite `/newbot`
3. Escolha nome: "Meu Bot Financeiro"
4. Escolha username: "meu_bot_financeiro_bot"
5. **COPIE O TOKEN**

### 3. Configurar token (Windows PowerShell)
```bash
$env:TELEGRAM_BOT_TOKEN="SEU_TOKEN_AQUI"
```

### 4. Executar
```bash
python bot.py
```

## 🎯 Comandos Principais

### Lançamentos Inteligentes
```
/add alimentação despesa 25,50 almoço no araujo
/add salário receita 5000 trabalho freelance
/add transporte despesa 15 uber para casa
```

### Metas Inteligentes
```
/meta Viagem de Casamento 20000 30-03-26
/meta Notebook Gamer 3000 15-12-24
```

### Relatórios e Gráficos
```
/saldo - Saldo atual
/relatorio - Relatório mensal
/grafico - Gráfico em texto
/exportar - Exportar CSV
```

### Limites
```
/limite alimentação 500
/limites - Ver limites ultrapassados
```

## 🧠 Parsing Inteligente

O bot entende automaticamente:
- **Valores:** 25,50 ou 25.50
- **Categorias:** alimentação, transporte, saúde, lazer
- **Tipos:** receita/despesa por palavras-chave
- **Datas:** 30-03-26, 30/03/2026

## ✅ Funcionalidades

- ✅ Parsing inteligente de comandos
- ✅ Banco SQLite local
- ✅ Sistema de lançamentos
- ✅ Sistema de metas
- ✅ Gráficos em texto
- ✅ Relatórios mensais
- ✅ Exportação CSV
- ✅ Limites de gastos
- ✅ Reset com confirmação

## 🎉 Pronto para usar!

O bot está 100% funcional e não precisa de dependências complexas!
