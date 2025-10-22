FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos
COPY requirements.txt .
COPY bot.py .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para executar o bot
CMD ["python", "bot.py"]
