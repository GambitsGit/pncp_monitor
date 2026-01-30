# 🖨️ Monitor de Licitações PNCP - Impressoras 3D

Sistema completo de monitoramento de licitações públicas focado em **Impressoras 3D (FDM e Resina)** e seus insumos através da API do Portal Nacional de Contratações Públicas (PNCP).

## 📋 Características

- ✅ **Coleta automática** de licitações do PNCP
- 🔍 **Filtro inteligente** por palavras-chave relacionadas a impressão 3D
- 📊 **Dashboard interativo** com estatísticas em tempo real
- 💾 **Banco de dados SQLite** - leve e eficiente
- 🎯 **Sistema de relevância** - classifica licitações por importância
- 📝 **Anotações personalizadas** em cada licitação
- 🔄 **Coleta agendada** - atualização diária automática
- 🌐 **Interface web responsiva** - acesse de qualquer dispositivo
- 🍓 **Otimizado para Raspberry Pi** - baixo consumo de recursos

## 🎯 Palavras-chave Monitoradas

O sistema busca licitações que mencionem:

### Impressoras 3D
- impressora 3d, impressora tridimensional
- prototipagem rápida, fabricação aditiva
- FDM, FFF, SLA, DLP, LCD

### Insumos
- Filamentos: PLA, ABS, PETG, TPU, Nylon
- Resinas: fotopolimérica, UV, dental
- Scanner 3D, mesa aquecida, extrusora

### Software
- Modelagem 3D, CAD 3D, slicing, fatiamento

## 🚀 Instalação

### Requisitos
- Python 3.7+
- 64GB de espaço (o banco cresce conforme coleta dados)
- Conexão com internet

### Instalação Rápida

```bash
# 1. Clone ou extraia o projeto
cd pncp_monitor

# 2. Execute o script de instalação
chmod +x install.sh
./install.sh

# 3. Inicie o servidor
python3 app.py
```

### Instalação Manual

```bash
# Instalar dependências
pip3 install -r requirements.txt

# Iniciar servidor
python3 app.py
```

## 🌐 Acesso

Após iniciar o servidor, acesse:

- **Local:** http://localhost:5000
- **Rede local:** http://[IP-DO-SEU-COMPUTADOR]:5000

### Descobrir IP no Raspberry Pi
```bash
hostname -I
```

## 📱 Como Usar

### 1. Primeira Coleta
1. Acesse a interface web
2. Clique em "**🔄 Coletar Novas Licitações**"
3. Aguarde a coleta (pode levar alguns minutos)
4. Visualize os resultados

### 2. Filtros Disponíveis
- **Situação:** Abertas, Futuras, Encerradas
- **Busca:** Por órgão ou objeto
- **Período:** Data inicial e final

### 3. Detalhes da Licitação
- Clique em qualquer licitação para ver:
  - Informações completas do órgão
  - Datas importantes
  - Link para o sistema de origem
  - Campo para adicionar suas observações

### 4. Sistema de Relevância
Cada licitação recebe uma pontuação baseada em:
- ⭐⭐⭐⭐⭐ (25+): Altamente relevante
- ⭐⭐⭐⭐ (20-24): Muito relevante
- ⭐⭐⭐ (15-19): Relevante
- ⭐⭐ (10-14): Moderadamente relevante
- ⭐ (5-9): Pouco relevante

## 🤖 Coleta Automática

### Configurar coleta diária às 8h:

```bash
# Opção 1: Script automático
python3 configurar_coleta_auto.py

# Opção 2: Manual com crontab
crontab -e

# Adicione a linha:
0 8 * * * cd /home/pi/pncp_monitor && /usr/bin/python3 coletar_automatico.py >> /home/pi/pncp_monitor/coleta_auto.log 2>&1
```

### Testar coleta manual:
```bash
python3 coletar_automatico.py
```

## 🔧 Executar como Serviço (Raspberry Pi)

Para o sistema iniciar automaticamente com o Raspberry Pi:

```bash
# 1. Editar o arquivo de serviço se necessário
nano pncp-monitor.service
# Ajustar User= e WorkingDirectory= conforme seu usuário

# 2. Copiar para systemd
sudo cp pncp-monitor.service /etc/systemd/system/

# 3. Habilitar e iniciar
sudo systemctl enable pncp-monitor
sudo systemctl start pncp-monitor

# 4. Verificar status
sudo systemctl status pncp-monitor

# 5. Ver logs
sudo journalctl -u pncp-monitor -f
```

### Comandos úteis:
```bash
# Parar o serviço
sudo systemctl stop pncp-monitor

# Reiniciar o serviço
sudo systemctl restart pncp-monitor

# Desabilitar inicialização automática
sudo systemctl disable pncp-monitor
```

## 📊 Estrutura do Banco de Dados

### Tabela: licitacoes
- Informações completas da licitação
- Score de relevância
- Palavras-chave encontradas
- Status de visualização
- Campo para observações personalizadas

### Tabela: historico_coletas
- Registro de todas as coletas realizadas
- Quantidade de licitações encontradas
- Status de cada coleta

## 🔍 API REST

O sistema disponibiliza endpoints REST para integração:

### GET /api/licitacoes
Lista todas as licitações com filtros opcionais
```
?situacao=aberta
&data_inicio=2024-01-01
&data_fim=2024-12-31
&busca=termo
```

### GET /api/licitacoes/:id
Detalhes de uma licitação específica

### POST /api/coletar
Inicia coleta de licitações
```json
{
  "dias": 30
}
```

### POST /api/licitacoes/:id/observacao
Adiciona observação a uma licitação
```json
{
  "observacao": "Texto da observação"
}
```

### GET /api/estatisticas
Retorna estatísticas gerais do sistema

## 📁 Estrutura de Arquivos

```
pncp_monitor/
├── app.py                      # Aplicação principal Flask
├── requirements.txt            # Dependências Python
├── install.sh                  # Script de instalação
├── coletar_automatico.py      # Script de coleta automática
├── configurar_coleta_auto.py  # Configurador de cron
├── pncp-monitor.service       # Arquivo de serviço systemd
├── licitacoes.db              # Banco de dados (criado automaticamente)
├── templates/
│   └── index.html             # Interface web
└── README.md                  # Esta documentação
```

## 🎨 Personalização

### Adicionar palavras-chave

Edite o arquivo `app.py`, seção `PALAVRAS_CHAVE`:

```python
PALAVRAS_CHAVE = [
    # Suas palavras-chave aqui
    'nova palavra',
    'outro termo',
]
```

### Ajustar período de coleta

Por padrão, o sistema coleta licitações dos últimos 30 dias. Para alterar:

```python
# No arquivo app.py, rota /api/coletar
dias_retroativos = data.get('dias', 30)  # Altere o número aqui
```

### Alterar porta do servidor

```python
# No final do app.py
app.run(host='0.0.0.0', port=5000, debug=True)  # Altere a porta aqui
```

## 🐛 Solução de Problemas

### Erro: "Não foi possível conectar ao servidor"
- Verifique se o servidor está rodando: `ps aux | grep python`
- Reinicie: `python3 app.py`

### Coleta não encontra nada
- Verifique sua conexão com a internet
- A API do PNCP pode estar temporariamente indisponível
- Tente novamente em alguns minutos

### Banco de dados corrompido
```bash
# Backup do banco atual
cp licitacoes.db licitacoes.db.backup

# Criar novo banco
python3 -c "from app import DatabaseManager; DatabaseManager()"
```

### Espaço insuficiente no Raspberry Pi
```bash
# Verificar espaço
df -h

# Limpar logs antigos
> coleta_auto.log
> pncp_monitor.log
```

## 📈 Dicas de Uso

1. **Primeira semana:** Deixe o sistema coletar dados por uma semana para criar um histórico
2. **Revise regularmente:** Configure alertas ou verifique licitações novas semanalmente
3. **Anote observações:** Use o campo de observações para registrar seu interesse
4. **Backup:** Faça backup regular do arquivo `licitacoes.db`

## 🔐 Segurança

- O sistema não requer autenticação (é local)
- Se expor na internet, configure firewall ou autenticação
- Para uso em rede local, restrinja acesso por IP

## 🤝 Contribuindo

Sugestões de melhoria:
- Notificações por email/Telegram
- Exportação para Excel/PDF
- Gráficos de tendências
- Integração com sistemas de gestão

## 📝 Licença

Este projeto é fornecido "como está" para uso pessoal e comercial.

## 🆘 Suporte

Para problemas com:
- **API PNCP:** https://www.gov.br/pncp/pt-br
- **Python/Flask:** Documentação oficial
- **Raspberry Pi:** Fóruns da comunidade Raspberry Pi

## 🎯 Roadmap

- [ ] Notificações push
- [ ] App mobile
- [ ] Integração com calendário
- [ ] Exportação de relatórios
- [ ] Machine learning para recomendações
- [ ] Dashboard com gráficos avançados

---

**Desenvolvido para importadoras de impressoras 3D** 🖨️

Versão: 1.0.0 | Janeiro 2026
