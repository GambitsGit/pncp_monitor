#!/usr/bin/env python3
"""
Script de teste do Sistema de Monitoramento PNCP
Verifica se todas as dependências e componentes estão funcionando
"""

import sys
import os

def verificar_modulo(nome):
    """Verifica se um módulo Python está instalado"""
    try:
        __import__(nome)
        print(f"✓ {nome}")
        return True
    except ImportError:
        print(f"✗ {nome} - NÃO INSTALADO")
        return False

def verificar_arquivo(caminho):
    """Verifica se um arquivo existe"""
    if os.path.exists(caminho):
        print(f"✓ {caminho}")
        return True
    else:
        print(f"✗ {caminho} - NÃO ENCONTRADO")
        return False

def testar_banco():
    """Testa a criação do banco de dados"""
    try:
        from app import DatabaseManager
        db = DatabaseManager('teste_licitacoes.db')
        print("✓ Banco de dados criado com sucesso")
        
        # Limpar arquivo de teste
        if os.path.exists('teste_licitacoes.db'):
            os.remove('teste_licitacoes.db')
        
        return True
    except Exception as e:
        print(f"✗ Erro ao criar banco: {e}")
        return False

def testar_api_pncp():
    """Testa conexão com a API do PNCP"""
    try:
        import requests
        url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao/aberta"
        
        print("  Testando conexão com API PNCP...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            total = len(data.get('data', []))
            print(f"✓ API PNCP acessível ({total} licitações abertas encontradas)")
            return True
        else:
            print(f"✗ API PNCP retornou código {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Erro de conexão com API PNCP - verifique sua internet")
        return False
    except Exception as e:
        print(f"✗ Erro ao testar API: {e}")
        return False

def main():
    """Executa todos os testes"""
    
    print("=" * 60)
    print("TESTE DO SISTEMA DE MONITORAMENTO PNCP")
    print("=" * 60)
    print()
    
    # Verificar Python
    print(f"Python: {sys.version}")
    print()
    
    # Verificar módulos
    print("1. Verificando dependências Python...")
    modulos_ok = True
    modulos_ok &= verificar_modulo('flask')
    modulos_ok &= verificar_modulo('flask_cors')
    modulos_ok &= verificar_modulo('requests')
    modulos_ok &= verificar_modulo('sqlite3')
    print()
    
    if not modulos_ok:
        print("⚠️  Instale as dependências com: pip3 install -r requirements.txt")
        print()
    
    # Verificar arquivos
    print("2. Verificando arquivos do projeto...")
    arquivos_ok = True
    arquivos_ok &= verificar_arquivo('app.py')
    arquivos_ok &= verificar_arquivo('requirements.txt')
    arquivos_ok &= verificar_arquivo('templates/index.html')
    print()
    
    if not arquivos_ok:
        print("⚠️  Alguns arquivos estão faltando")
        print()
    
    # Testar banco de dados
    print("3. Testando banco de dados...")
    banco_ok = testar_banco()
    print()
    
    # Testar API PNCP
    print("4. Testando conexão com API PNCP...")
    api_ok = testar_api_pncp()
    print()
    
    # Resultado final
    print("=" * 60)
    if modulos_ok and arquivos_ok and banco_ok and api_ok:
        print("✓ TODOS OS TESTES PASSARAM!")
        print()
        print("Seu sistema está pronto para uso!")
        print()
        print("Para iniciar o servidor:")
        print("  python3 app.py")
        print()
        print("Depois acesse: http://localhost:5000")
        return 0
    else:
        print("✗ ALGUNS TESTES FALHARAM")
        print()
        print("Corrija os problemas indicados acima antes de prosseguir.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
