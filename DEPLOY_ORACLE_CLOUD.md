# Deploy no Oracle Cloud (Always Free)

## 1. Criar conta Oracle Cloud Free Tier

1. Acesse [Oracle Cloud Free Tier](https://www.oracle.com/br/cloud/free/)
2. Clique em "Comece gratuitamente"
3. Preencha seus dados
   - Use um email válido
   - Cartão de crédito é necessário para verificação, mas NÃO será cobrado
   - Escolha uma região próxima (ex: São Paulo)

## 2. Criar VM (Compute Instance)

1. No Console Oracle Cloud, vá para "Compute" -> "Instances"
2. Clique em "Create Instance"
3. Configure a VM:
   - Nome: vida-financeira-bot
   - Image: Canonical Ubuntu (mais recente)
   - Shape: 
     - Clique em "Change Shape"
     - Selecione "AMD"
     - Escolha "VM.Standard.E2.1.Micro" (Always Free)
     - Esta VM vem com:
       - 1 OCPU
       - 1 GB RAM
       - Suficiente para rodar o bot
   - Network: Create new VCN (Virtual Cloud Network)
   - Add SSH key: Generate key pair
     - IMPORTANTE: Baixe e salve a chave privada
   
   OBS: Não selecione nenhum Availability Domain ou Fault Domain específico,
   deixe o Oracle Cloud escolher automaticamente para evitar erros de capacidade.

## 3. Configurar Segurança

1. No menu, vá para "Networking" -> "Virtual Cloud Networks"
2. Clique na sua VCN
3. Em "Security Lists", clique na lista padrão
4. Adicione Ingress Rule:
   - Source: 0.0.0.0/0
   - Port: 80, 443 (HTTP/HTTPS)

## 4. Acessar a VM

```powershell
# No Windows PowerShell

# 1. Encontre o IP público:
#    - No Console Oracle Cloud, vá em "Compute" -> "Instances"
#    - Clique no nome da sua instância
#    - Procure por "Public IP" na seção "Primary VNIC Information"

# 2. Configure a chave SSH:
mkdir -p $env:USERPROFILE\.ssh
New-Item -Path "$env:USERPROFILE\.ssh\oracle_key" -Type File
# Abra o arquivo no Bloco de Notas e cole sua chave privada
notepad "$env:USERPROFILE\.ssh\oracle_key"
# Configure as permissões corretas
icacls "$env:USERPROFILE\.ssh\oracle_key" /inheritance:r /grant:r "${env:USERNAME}:(R,W)"

# 3. Conecte-se à VM:
ssh -i "$env:USERPROFILE\.ssh\oracle_key" ubuntu@{ip}
```

## 5. Instalar Dependências

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python e ferramentas
sudo apt install python3-pip python3-venv git -y

# Criar diretório do projeto
mkdir vida-financeira
cd vida-financeira

# Clonar repositório
git clone https://github.com/falk-dev/vida-financeira.git .

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## 6. Configurar Serviço Systemd

```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/vidafinanceira.service
```

Conteúdo do arquivo:
```ini
[Unit]
Description=Vida Financeira Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/vida-financeira
Environment="TELEGRAM_BOT_TOKEN=seu_token_aqui"
ExecStart=/home/ubuntu/vida-financeira/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 7. Iniciar o Serviço

```bash
# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar inicialização automática
sudo systemctl enable vidafinanceira

# Iniciar o serviço
sudo systemctl start vidafinanceira

# Verificar status
sudo systemctl status vidafinanceira
```

## 8. Monitoramento e Logs

```bash
# Ver logs em tempo real
sudo journalctl -u vidafinanceira -f

# Ver últimos 100 logs
sudo journalctl -u vidafinanceira -n 100
```

## 9. Backup Automático

Crie um script de backup:
```bash
# Criar diretório de backups
mkdir -p ~/backups

# Criar script de backup
nano ~/backup_bot.sh
```

Conteúdo do script:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp /home/ubuntu/vida-financeira/financeiro.db ~/backups/financeiro_$DATE.db
find ~/backups -name "financeiro_*.db" -mtime +7 -delete
```

Configure execução automática:
```bash
# Dar permissão de execução
chmod +x ~/backup_bot.sh

# Adicionar ao crontab (backup diário às 3:00)
(crontab -l 2>/dev/null; echo "0 3 * * * /home/ubuntu/backup_bot.sh") | crontab -
```

## Dicas Importantes

1. **Monitoramento**: 
   - Use `sudo systemctl status vidafinanceira` para verificar o status
   - Use `journalctl` para ver os logs

2. **Segurança**:
   - Mantenha o sistema atualizado: `sudo apt update && sudo apt upgrade`
   - Use senhas fortes
   - Mantenha o token do bot seguro

3. **Backup**:
   - Faça backup regular do banco de dados
   - Mantenha cópias em local seguro
   - Configure notificações de backup

4. **Manutenção**:
   - Verifique o uso de disco: `df -h`
   - Monitore uso de memória: `free -h`
   - Limpe logs antigos periodicamente

## Resolução de Problemas

1. **Bot não inicia**:
   ```bash
   # Verificar logs
   sudo journalctl -u vidafinanceira -n 50
   
   # Reiniciar serviço
   sudo systemctl restart vidafinanceira
   ```

2. **Erro de permissão**:
   ```bash
   # Corrigir permissões
   sudo chown -R ubuntu:ubuntu /home/ubuntu/vida-financeira
   ```

3. **Serviço trava**:
   ```bash
   # Reiniciar serviço
   sudo systemctl restart vidafinanceira
   ```

4. **Erros de memória**:
   ```bash
   # Limpar cache do sistema
   sudo sync; echo 3 | sudo tee /proc/sys/vm/drop_caches
   
   # Reiniciar serviço
   sudo systemctl restart vidafinanceira
   ```

5. **VM lenta**:
   ```bash
   # Verificar processos consumindo recursos
   top
   
   # Verificar uso de swap
   free -h
   ```
