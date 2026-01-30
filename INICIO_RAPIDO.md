# 🚀 Guia Rápido de Início

## Instalação em 3 Passos

### 1️⃣ Preparar o Ambiente

```bash
# Navegue até a pasta do projeto
cd pncp_monitor

# Torne os scripts executáveis
chmod +x install.sh
chmod +x testar_sistema.py
chmod +x coletar_automatico.py
chmod +x configurar_coleta_auto.py
```

### 2️⃣ Instalar Dependências

```bash
# Execute o instalador
./install.sh

# OU manualmente:
pip3 install -r requirements.txt
```

### 3️⃣ Testar o Sistema

```bash
# Execute o teste
python3 testar_sistema.py
```

Se todos os testes passarem, prossiga!

## 🎯 Primeiro Uso

### Iniciar o Servidor

```bash
python3 app.py
```

Você verá algo como:
```
* Running on http://0.0.0.0:5000
```

### Acessar a Interface

1. Abra o navegador
2. Acesse: `http://localhost:5000`
3. Clique em **"🔄 Coletar Novas Licitações"**
4. Aguarde a coleta (2-5 minutos)
5. Explore as licitações encontradas!

## 📱 Acessar de Outro Dispositivo

### No Raspberry Pi/Servidor, descubra o IP:
```bash
hostname -I
# Exemplo de saída: 192.168.1.100
```

### Em outro computador/celular:
```
http://192.168.1.100:5000
```

## 🤖 Configurar Coleta Automática

Para coletar licitações automaticamente todo dia:

```bash
python3 configurar_coleta_auto.py
```

Responda 's' quando perguntado.

## 🔧 Rodar como Serviço (Opcional)

Para o sistema iniciar sozinho quando o Raspberry Pi ligar:

```bash
# 1. Editar usuário e pasta no arquivo de serviço
nano pncp-monitor.service
# Altere 'User=pi' e 'WorkingDirectory=/home/pi/pncp_monitor'

# 2. Instalar o serviço
sudo cp pncp-monitor.service /etc/systemd/system/
sudo systemctl enable pncp-monitor
sudo systemctl start pncp-monitor

# 3. Verificar status
sudo systemctl status pncp-monitor
```

## ❓ Problemas Comuns

### Porta 5000 já em uso
```bash
# Edite app.py e mude a porta:
# app.run(host='0.0.0.0', port=5001, debug=True)
```

### Erro de dependências
```bash
pip3 install --upgrade flask flask-cors requests
```

### Não consegue acessar pela rede
```bash
# Verifique o firewall
sudo ufw allow 5000
```

## 📊 Próximos Passos

1. ✅ Explore a interface web
2. ✅ Adicione observações em licitações interessantes
3. ✅ Configure a coleta automática
4. ✅ Faça backup regular do arquivo `licitacoes.db`

## 🆘 Precisa de Ajuda?

Consulte o `README.md` completo para documentação detalhada.

---

**Boa sorte com as licitações! 🎯**
