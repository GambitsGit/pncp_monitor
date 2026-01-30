#!/usr/bin/env python3
"""
Script para agendar coleta automática de licitações
"""

import subprocess
import sys

def criar_cron_job():
    """Cria um cron job para executar coleta diariamente às 8h"""
    
    cron_line = "0 8 * * * cd /home/pi/pncp_monitor && /usr/bin/python3 coletar_automatico.py >> /home/pi/pncp_monitor/coleta_auto.log 2>&1\n"
    
    print("Configurando coleta automática diária às 8h da manhã...")
    print("")
    print("Execute os seguintes comandos:")
    print("")
    print("1. Abrir crontab:")
    print("   crontab -e")
    print("")
    print("2. Adicionar a seguinte linha ao final do arquivo:")
    print(f"   {cron_line}")
    print("")
    print("3. Salvar e fechar")
    print("")
    print("Ou execute automaticamente:")
    print("   (crontab -l 2>/dev/null; echo '" + cron_line.strip() + "') | crontab -")
    print("")
    
    resposta = input("Deseja configurar automaticamente? (s/n): ")
    
    if resposta.lower() == 's':
        try:
            # Obter crontab atual
            resultado = subprocess.run(['crontab', '-l'], 
                                     capture_output=True, 
                                     text=True)
            
            crontab_atual = resultado.stdout if resultado.returncode == 0 else ""
            
            # Verificar se já existe
            if cron_line.strip() in crontab_atual:
                print("✓ Coleta automática já está configurada!")
                return
            
            # Adicionar nova linha
            novo_crontab = crontab_atual + cron_line
            
            # Aplicar novo crontab
            processo = subprocess.Popen(['crontab', '-'], 
                                      stdin=subprocess.PIPE,
                                      text=True)
            processo.communicate(input=novo_crontab)
            
            if processo.returncode == 0:
                print("✓ Coleta automática configurada com sucesso!")
                print("  As licitações serão coletadas automaticamente todos os dias às 8h")
            else:
                print("✗ Erro ao configurar crontab")
                
        except Exception as e:
            print(f"✗ Erro: {e}")
            print("Configure manualmente seguindo as instruções acima.")
    else:
        print("Configure manualmente seguindo as instruções acima.")

if __name__ == '__main__':
    criar_cron_job()
