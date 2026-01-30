#!/bin/bash

echo "=========================================="
echo "Monitor de Licitações PNCP"
echo "Instalação com Ambiente Virtual"
echo "=========================================="
echo ""

# Verificar Python3
echo "1. Verificando Python3..."
if ! command -v python3 &> /dev/null; then
    echo "Instalando Python3..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-full
else
    echo "Python3 já instalado: $(python3 --version)"
fi

# Instalar python3-venv
echo "2. Instalando python3-venv..."
sudo apt-get install -y python3-venv python3-full

# Criar ambiente virtual
echo "3. Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Ambiente virtual criado"
else
    echo "✓ Ambiente virtual já existe"
fi

# Ativar ambiente virtual e instalar dependências
echo "4. Instalando dependências Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Criar banco de dados
echo "5. Inicializando banco de dados..."
python -c "from app import DatabaseManager; DatabaseManager()"

echo ""
echo "=========================================="
echo "Instalação Concluída!"
echo "=========================================="
echo ""
echo "Para iniciar o servidor:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "Ou use o script de início:"
echo "  ./iniciar.sh"
echo ""