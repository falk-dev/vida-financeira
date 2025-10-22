# Deploy no Oracle Cloud Free Tier

1. Criar conta no Oracle Cloud (https://www.oracle.com/cloud/free/)
   - Use um email válido
   - Adicione um cartão de crédito (não será cobrado)
   - Escolha uma região próxima (ex: São Paulo)

2. Criar VM:
   - Vá em Compute -> Instances -> Create Instance
   - Escolha "Always Free eligible" 
   - Use Oracle Linux 8
   - Configure SSH key

3. Conectar na VM:
   ```bash
   ssh -i sua_chave.pem opc@IP_DA_VM
   ```

4. Instalar dependências:
   ```bash
   sudo dnf update -y
   sudo dnf install python39 python39-pip git -y
   ```

5. Clonar repositório:
   ```bash
   git clone https://github.com/SEU_USUARIO/vida-financeira.git
   cd vida-financeira
   ```

6. Configurar ambiente:
   ```bash
   python3.9 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

7. Configurar serviço systemd:
   ```bash
   sudo nano /etc/systemd/system/vidafinanceira.service
   ```

   Conteúdo:
   ```ini
   [Unit]
   Description=Vida Financeira Bot
   After=network.target

   [Service]
   Type=simple
   User=opc
   WorkingDirectory=/home/opc/vida-financeira
   Environment=PATH=/home/opc/vida-financeira/venv/bin
   ExecStart=/home/opc/vida-financeira/venv/bin/python bot.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

8. Iniciar serviço:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable vidafinanceira
   sudo systemctl start vidafinanceira
   ```

9. Verificar logs:
   ```bash
   sudo journalctl -u vidafinanceira -f
   ```