# 💑 Bot de Vida Financeira para Casais

## 🎯 Funcionamento para Casais

O bot foi projetado especialmente para casais que querem **compartilhar as finanças** mas saber quem fez cada lançamento!

### 👥 **Dados Compartilhados**
- **Saldo único** para o casal
- **Relatórios compartilhados**
- **Metas em conjunto**
- **Histórico unificado**

### 👤 **Responsável por Lançamento**
- **Quem enviar a mensagem = Responsável pelo gasto**
- Exemplo: Se João envia `/add alimentação despesa 25,50 almoço pix`
- Resultado: "👤 Responsável: João"

### 📱 **Exemplos de Uso**

**João envia:**
```
/add alimentação despesa 25,50 almoço no araujo pix
```

**Bot responde:**
```
💸 Lançamento adicionado!

📊 Categoria: alimentação
🏷️ Tipo: despesa
💵 Valor: R$ 25,50
👤 Responsável: João
💳 Método: pix
📝 Descrição: almoço no araujo

✅ Saldo atualizado!
```

**Maria envia:**
```
/add salário receita 5000 trabalho freelance nubank
```

**Bot responde:**
```
💰 Lançamento adicionado!

📊 Categoria: outros
🏷️ Tipo: receita
💵 Valor: R$ 5000,00
👤 Responsável: Maria
💳 Método: conta
📝 Descrição: trabalho freelance nubank

✅ Saldo atualizado!
```

**Qualquer um envia `/saldo`:**
```
💰 Saldo do Casal

💵 Valor: R$ 4.974,50
📊 Status: Positivo

💡 Use /add para adicionar lançamentos
```

## 🎯 **Vantagens para Casais**

### ✅ **Transparência Total**
- Ambos veem todos os lançamentos
- Saldo compartilhado
- Relatórios unificados

### ✅ **Controle Individual**
- Sabem quem fez cada gasto
- Responsabilidade clara
- Histórico detalhado

### ✅ **Facilidade**
- Não precisa especificar quem fez o gasto
- Parsing inteligente funciona igual
- Comandos simples e rápidos

## 🚀 **Comandos para Casais**

### **Lançamentos:**
```
/add alimentação despesa 25,50 almoço no araujo pix
/add transporte despesa 15 uber para casa cartão
/add salário receita 5000 trabalho freelance nubank
```

### **Consultas Compartilhadas:**
```
/saldo - Saldo do casal
/relatorio - Relatório mensal do casal
/metas - Metas do casal
/grafico - Gráficos de gastos do casal
```

### **Configurações:**
```
/limite alimentação 500 - Limite do casal
/exportar - Exportar dados do casal
/reset - Resetar dados do casal (com confirmação)
```

## 💡 **Dicas para Casais**

### 🎯 **Organização**
- Metas em conjunto
- Limites compartilhados
- Relatórios unificados

### 📊 **Análise**
- Gráficos do casal
- Exportação de dados compartilhados
- Histórico completo

### 🔒 **Transparência**
- Dados compartilhados
- Responsabilidade clara
- Controle conjunto

## 🎉 **Exemplo Prático**

**Grupo: "Finanças do Casal"**

**João:** `/add alimentação despesa 25,50 almoço pix`
**Bot:** "💸 Lançamento adicionado! 👤 Responsável: João"

**Maria:** `/add transporte despesa 15 uber cartão`
**Bot:** "💸 Lançamento adicionado! 👤 Responsável: Maria"

**João:** `/saldo`
**Bot:** "💰 Saldo do Casal: R$ 1.250,00"

**Maria:** `/relatorio`
**Bot:** "📊 Relatório Mensal do Casal..."

**Dados compartilhados, responsabilidade individual!** 💑
