#!/home/pihole/licitacoes-3d/venv/bin/python
"""
Script para coleta automática de licitações
Executado pelo cron diariamente
"""

import requests
from datetime import datetime
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def coletar():
    """Executa coleta de licitações"""
    
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{timestamp}] Iniciando coleta automática de licitações...")
    
    try:
        # Fazer requisição para o endpoint de coleta
        response = requests.post(
            'http://localhost:5000/api/coletar',
            json={'dias': 30},
            timeout=300  # 5 minutos de timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print(f"✓ Coleta concluída com sucesso!")
                print(f"  Total encontradas: {data.get('total_encontradas', 0)}")
                print(f"  Total relevantes: {data.get('total_relevantes', 0)}")
                return True
            else:
                print(f"✗ Erro na coleta: {data.get('erro', 'Desconhecido')}")
                return False
        else:
            print(f"✗ Erro HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Erro: Não foi possível conectar ao servidor")
        print("  Certifique-se de que o servidor está rodando (python3 app.py)")
        return False
        
    except requests.exceptions.Timeout:
        print("✗ Erro: Timeout na requisição (mais de 5 minutos)")
        return False
        
    except Exception as e:
        print(f"✗ Erro inesperado: {e}")
        return False

if __name__ == '__main__':
    sucesso = coletar()
    sys.exit(0 if sucesso else 1)
