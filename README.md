# Bot de Vida Financeira
# Sistema inteligente para controle financeiro pessoal no Telegram

## 🚀 Como usar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Criar bot no Telegram
1. Acesse [@BotFather](https://t.me/BotFather) no Telegram
2. Digite `/newbot`
3. Escolha um nome para seu bot (ex: "Meu Bot Financeiro")
4. Escolha um username (deve terminar com 'bot', ex: "meu_bot_financeiro_bot")
5. Copie o token fornecido

### 3. Configurar token
Defina o token como variável de ambiente:
```bash
# Windows (PowerShell)
$env:TELEGRAM_BOT_TOKEN="SEU_TOKEN_AQUI"

# Linux/Mac
export TELEGRAM_BOT_TOKEN="SEU_TOKEN_AQUI"
```

### 4. Executar o bot
```bash
python bot.py
```

## 📋 Funcionalidades Implementadas

### ✅ Sistema Completo
- ✅ Parsing inteligente de comandos
- ✅ Banco de dados SQLite
- ✅ Sistema de lançamentos (receitas/despesas)
- ✅ Sistema de metas com parsing inteligente
- ✅ Gráficos de gastos por categoria
- ✅ Relatórios mensais detalhados
- ✅ Exportação de dados em CSV
- ✅ Sistema de limites de gastos
- ✅ Reset de dados com confirmação
- ✅ Interface amigável com emojis

## 🎯 Comandos Disponíveis

### 📊 Lançamentos Inteligentes
```
/add alimentação despesa 25,50 almoço no araujo pix
/add salário receita 5000 trabalho freelance nubank
/add transporte despesa 15 uber para casa cartão
```

### 💰 Saldo e Relatórios
```
/saldo - Ver saldo atual
/relatorio - Relatório mensal completo
/grafico - Gráfico de gastos por categoria
```

### 🎯 Metas Inteligentes
```
/meta Viagem de Casamento 20000 30-03-26
/meta Notebook Gamer 3000 15-12-24
/metas - Listar todas as metas
```

### 🎯 Limites de Gastos
```
/limite alimentação 500
/limite transporte 200
/limites - Ver limites ultrapassados
```

### 📤 Exportação
```
/exportar - Exportar dados em CSV
```

### ⚙️ Configurações
```
/reset - Resetar todos os dados (com confirmação)
```

## 🧠 Parsing Inteligente

O bot reconhece automaticamente:
- **Valores:** 25,50 ou 25.50
- **Categorias:** alimentação, transporte, saúde, lazer, etc.
- **Tipos:** receita ou despesa baseado em palavras-chave
- **Responsáveis:** quem enviou a mensagem (nome do usuário)
- **Métodos de Pagamento:** pix, cartão, dinheiro, nubank, itau, etc.
- **Datas:** 30-03-26, 30/03/2026, 30 março 2026
- **Descrições:** texto livre para detalhes

## 💑 **Perfeito para Casais**

- **Dados compartilhados** - Saldo único para o casal
- **Responsabilidade clara** - Sabem quem fez cada lançamento
- **Transparência total** - Ambos veem todos os dados
- **Controle conjunto** - Metas e limites compartilhados

## 🏗️ Arquitetura

- **Backend:** Python + python-telegram-bot
- **Banco:** SQLite (gratuito e simples)
- **Gráficos:** Gráficos em texto com barras visuais
- **Exportação:** CSV nativo do Python
- **Parsing:** Regex + processamento de texto inteligente

## 💡 Exemplos de Uso

**Lançamentos:**
```
/add alimentação despesa 25,50 almoço no araujo pix
/add salário receita 5000 trabalho freelance nubank
/add transporte despesa 15 uber para casa cartão
```

**Metas:**
```
/meta Viagem de Casamento 20000 30-03-26
/meta Notebook Gamer 3000 15-12-24
```

**Limites:**
```
/limite alimentação 500
/limite transporte 200
```

## 🎉 Funcionalidades Especiais

- **Parsing Inteligente:** Entende comandos em linguagem natural
- **Categorização Automática:** Reconhece categorias por palavras-chave
- **Gráficos Visuais:** Gráficos de pizza para gastos por categoria
- **Relatórios Detalhados:** Análise completa mensal
- **Exportação CSV:** Dados para Excel/Google Sheets
- **Limites Inteligentes:** Alertas quando limites são ultrapassados
- **Interface Amigável:** Emojis e formatação clara
- **Confirmação de Reset:** Proteção contra exclusão acidental
