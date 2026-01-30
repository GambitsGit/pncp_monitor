"""
Sistema de Monitoramento de Licitações PNCP - VERSÃO CORRIGIDA
Focado em Impressoras 3D (FDM, Resina) e Insumos
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import sqlite3
import json
import re
from typing import List, Dict
import logging

app = Flask(__name__)
CORS(app)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações da API PNCP - ENDPOINTS ATUALIZADOS
PNCP_BASE_URL = "https://pncp.gov.br/api/pncp/v1"

# Palavras-chave para filtrar licitações relevantes
PALAVRAS_CHAVE = [
    # Impressoras 3D
    'impressora 3d', 'impressora tridimensional', 'impressao 3d', 
    'impressao tridimensional', 'printer 3d', 'prototipagem rapida',
    
    # Tipos de impressão
    'fdm', 'fff', 'resina', 'sla', 'dlp', 'lcd',
    
    # Insumos
    'filamento', 'pla', 'abs', 'petg', 'tpu', 'nylon',
    'resina fotopolimerica', 'resina uv', 'resina dental',
    
    # Equipamentos relacionados
    'scanner 3d', 'escaneamento tridimensional', 
    'mesa aquecida', 'extrusora', 'bico extrusor',
    
    # Software e serviços
    'modelagem 3d', 'cad 3d', 'slicing', 'fatiamento',
    'fabricacao aditiva', 'manufatura aditiva'
]

class DatabaseManager:
    """Gerenciador do banco de dados SQLite"""
    
    def __init__(self, db_path='licitacoes.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de licitações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS licitacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_controlpncp TEXT UNIQUE,
                ano INTEGER,
                sequencial INTEGER,
                orgao_cnpj TEXT,
                orgao_nome TEXT,
                orgao_poder TEXT,
                orgao_esfera TEXT,
                unidade_nome TEXT,
                modalidade TEXT,
                objeto_compra TEXT,
                valor_total REAL,
                situacao TEXT,
                data_publicacao TEXT,
                data_abertura_propostas TEXT,
                data_encerramento_propostas TEXT,
                link_sistema_origem TEXT,
                relevancia_score REAL,
                palavras_encontradas TEXT,
                itens_json TEXT,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                visualizado INTEGER DEFAULT 0,
                observacoes TEXT
            )
        ''')
        
        # Tabela de histórico de coletas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_coletas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_encontradas INTEGER,
                total_relevantes INTEGER,
                status TEXT
            )
        ''')
        
        # Índices para otimização
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_data_publicacao 
            ON licitacoes(data_publicacao)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_situacao 
            ON licitacoes(situacao)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Banco de dados inicializado com sucesso")
    
    def salvar_licitacao(self, licitacao: Dict) -> bool:
        """Salva ou atualiza uma licitação no banco"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO licitacoes 
                (numero_controlpncp, ano, sequencial, orgao_cnpj, orgao_nome, 
                 orgao_poder, orgao_esfera, unidade_nome, modalidade, objeto_compra,
                 valor_total, situacao, data_publicacao, data_abertura_propostas,
                 data_encerramento_propostas, link_sistema_origem, relevancia_score,
                 palavras_encontradas, itens_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                licitacao.get('numero_controlpncp'),
                licitacao.get('ano'),
                licitacao.get('sequencial'),
                licitacao.get('orgao_cnpj'),
                licitacao.get('orgao_nome'),
                licitacao.get('orgao_poder'),
                licitacao.get('orgao_esfera'),
                licitacao.get('unidade_nome'),
                licitacao.get('modalidade'),
                licitacao.get('objeto_compra'),
                licitacao.get('valor_total'),
                licitacao.get('situacao'),
                licitacao.get('data_publicacao'),
                licitacao.get('data_abertura_propostas'),
                licitacao.get('data_encerramento_propostas'),
                licitacao.get('link_sistema_origem'),
                licitacao.get('relevancia_score'),
                licitacao.get('palavras_encontradas'),
                json.dumps(licitacao.get('itens', []))
            ))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar licitação: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def buscar_licitacoes(self, filtros: Dict = None) -> List[Dict]:
        """Busca licitações com filtros opcionais"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM licitacoes WHERE 1=1"
        params = []
        
        if filtros:
            if filtros.get('situacao'):
                query += " AND situacao = ?"
                params.append(filtros['situacao'])
            
            if filtros.get('data_inicio'):
                query += " AND data_publicacao >= ?"
                params.append(filtros['data_inicio'])
            
            if filtros.get('data_fim'):
                query += " AND data_publicacao <= ?"
                params.append(filtros['data_fim'])
            
            if filtros.get('busca'):
                query += " AND (objeto_compra LIKE ? OR orgao_nome LIKE ?)"
                busca = f"%{filtros['busca']}%"
                params.extend([busca, busca])
        
        query += " ORDER BY data_publicacao DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def registrar_coleta(self, total_encontradas: int, total_relevantes: int, status: str):
        """Registra uma coleta no histórico"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO historico_coletas (total_encontradas, total_relevantes, status)
            VALUES (?, ?, ?)
        ''', (total_encontradas, total_relevantes, status))
        
        conn.commit()
        conn.close()
    
    def marcar_visualizado(self, licitacao_id: int):
        """Marca uma licitação como visualizada"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE licitacoes SET visualizado = 1 WHERE id = ?
        ''', (licitacao_id,))
        
        conn.commit()
        conn.close()
    
    def adicionar_observacao(self, licitacao_id: int, observacao: str):
        """Adiciona observação a uma licitação"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE licitacoes SET observacoes = ? WHERE id = ?
        ''', (observacao, licitacao_id))
        
        conn.commit()
        conn.close()


class PNCPCollector:
    """Coletor de dados da API do PNCP - VERSÃO CORRIGIDA"""
    
    def __init__(self):
        self.base_url = PNCP_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (compatible; PNCP-Monitor/1.0)'
        })
    
    def calcular_relevancia(self, texto: str) -> tuple:
        """Calcula score de relevância baseado nas palavras-chave"""
        if not texto:
            return 0, []
        
        texto_lower = texto.lower()
        palavras_encontradas = []
        score = 0
        
        for palavra in PALAVRAS_CHAVE:
            if palavra.lower() in texto_lower:
                palavras_encontradas.append(palavra)
                # Palavras mais específicas têm maior peso
                if palavra in ['impressora 3d', 'fdm', 'resina']:
                    score += 10
                elif palavra in ['filamento', 'pla', 'abs']:
                    score += 5
                else:
                    score += 2
        
        return score, palavras_encontradas
    
    def eh_relevante(self, licitacao: Dict) -> bool:
        """Verifica se a licitação é relevante para o negócio"""
        objeto = licitacao.get('objetoCompra', '')
        score, _ = self.calcular_relevancia(objeto)
        return score > 0
    
    def buscar_licitacoes_por_orgao(self, cnpj: str, ano: int = None) -> List[Dict]:
        """Busca licitações de um órgão específico - MÉTODO ALTERNATIVO"""
        if ano is None:
            ano = datetime.now().year
        
        endpoint = f"{self.base_url}/orgaos/{cnpj}/compras/{ano}"
        
        try:
            response = self.session.get(endpoint, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data if isinstance(data, list) else [data]
            return []
        except Exception as e:
            logger.error(f"Erro ao buscar licitações do órgão {cnpj}: {e}")
            return []
    
    def criar_licitacoes_exemplo(self) -> List[Dict]:
        """Cria licitações de exemplo para teste inicial"""
        logger.info("Criando licitações de exemplo para teste...")
        
        exemplos = [
            {
                'anoCompra': 2024,
                'sequencialCompra': 1,
                'objetoCompra': 'Aquisição de impressora 3D FDM com área mínima de 300x300x400mm, filamentos PLA e ABS',
                'orgaoEntidade': {
                    'cnpj': '12345678000190',
                    'razaoSocial': 'Universidade Federal de Exemplo',
                    'poder': 'E',
                    'esfera': 'F'
                },
                'unidadeOrgao': {
                    'nomeUnidade': 'Campus Exemplo - Lab de Prototipagem'
                },
                'modalidadeNome': 'Pregão Eletrônico',
                'valorTotalEstimado': 45000.00,
                'dataPublicacaoPncp': datetime.now().isoformat(),
                'dataAberturaProposta': (datetime.now() + timedelta(days=15)).isoformat(),
                'dataEncerramentoProposta': (datetime.now() + timedelta(days=15, hours=4)).isoformat(),
                'linkSistemaOrigem': 'https://pncp.gov.br'
            },
            {
                'anoCompra': 2024,
                'sequencialCompra': 2,
                'objetoCompra': 'Contratação de serviços de impressão 3D em resina fotopolimérica para produção de protótipos',
                'orgaoEntidade': {
                    'cnpj': '98765432000111',
                    'razaoSocial': 'Prefeitura Municipal de Teste',
                    'poder': 'E',
                    'esfera': 'M'
                },
                'unidadeOrgao': {
                    'nomeUnidade': 'Secretaria de Inovação'
                },
                'modalidadeNome': 'Concorrência',
                'valorTotalEstimado': 120000.00,
                'dataPublicacaoPncp': datetime.now().isoformat(),
                'dataAberturaProposta': (datetime.now() + timedelta(days=30)).isoformat(),
                'dataEncerramentoProposta': (datetime.now() + timedelta(days=30, hours=3)).isoformat(),
                'linkSistemaOrigem': 'https://pncp.gov.br'
            },
            {
                'anoCompra': 2023,
                'sequencialCompra': 3,
                'objetoCompra': 'Aquisição de scanner 3D e filamentos PETG, TPU e Nylon para laboratório de manufatura aditiva',
                'orgaoEntidade': {
                    'cnpj': '11122233000144',
                    'razaoSocial': 'Instituto Federal de Tecnologia',
                    'poder': 'E',
                    'esfera': 'F'
                },
                'unidadeOrgao': {
                    'nomeUnidade': 'Departamento de Engenharia'
                },
                'modalidadeNome': 'Pregão Eletrônico',
                'valorTotalEstimado': 75000.00,
                'dataPublicacaoPncp': (datetime.now() - timedelta(days=60)).isoformat(),
                'dataAberturaProposta': (datetime.now() - timedelta(days=45)).isoformat(),
                'dataEncerramentoProposta': (datetime.now() - timedelta(days=45)).isoformat(),
                'linkSistemaOrigem': 'https://pncp.gov.br'
            }
        ]
        
        return exemplos
    
    def processar_licitacao(self, licitacao_raw: Dict) -> Dict:
        """Processa e normaliza dados de uma licitação"""
        objeto = licitacao_raw.get('objetoCompra', '')
        score, palavras = self.calcular_relevancia(objeto)
        
        # Determina situação
        situacao = 'desconhecida'
        data_abertura = licitacao_raw.get('dataAberturaProposta')
        data_encerramento = licitacao_raw.get('dataEncerramentoProposta')
        
        hoje = datetime.now()
        
        if data_abertura:
            try:
                data_abertura_dt = datetime.fromisoformat(data_abertura.replace('Z', '+00:00'))
                if data_abertura_dt > hoje:
                    situacao = 'futura'
                elif data_encerramento:
                    data_encerramento_dt = datetime.fromisoformat(data_encerramento.replace('Z', '+00:00'))
                    if data_encerramento_dt > hoje:
                        situacao = 'aberta'
                    else:
                        situacao = 'encerrada'
                else:
                    situacao = 'aberta'
            except:
                situacao = 'aberta'
        
        data_pub = licitacao_raw.get('dataPublicacaoPncp', '')
        if data_pub:
            data_pub = data_pub[:10] if len(data_pub) >= 10 else data_pub
        
        return {
            'numero_controlpncp': f"{licitacao_raw.get('anoCompra')}-{licitacao_raw.get('sequencialCompra')}",
            'ano': licitacao_raw.get('anoCompra'),
            'sequencial': licitacao_raw.get('sequencialCompra'),
            'orgao_cnpj': licitacao_raw.get('orgaoEntidade', {}).get('cnpj'),
            'orgao_nome': licitacao_raw.get('orgaoEntidade', {}).get('razaoSocial'),
            'orgao_poder': licitacao_raw.get('orgaoEntidade', {}).get('poder'),
            'orgao_esfera': licitacao_raw.get('orgaoEntidade', {}).get('esfera'),
            'unidade_nome': licitacao_raw.get('unidadeOrgao', {}).get('nomeUnidade'),
            'modalidade': licitacao_raw.get('modalidadeNome'),
            'objeto_compra': objeto,
            'valor_total': licitacao_raw.get('valorTotalEstimado', 0),
            'situacao': situacao,
            'data_publicacao': data_pub,
            'data_abertura_propostas': data_abertura,
            'data_encerramento_propostas': data_encerramento,
            'link_sistema_origem': licitacao_raw.get('linkSistemaOrigem'),
            'relevancia_score': score,
            'palavras_encontradas': ', '.join(palavras),
            'itens': licitacao_raw.get('itens', [])
        }


# Inicializar gerenciadores
db = DatabaseManager()
collector = PNCPCollector()


# Rotas da API
@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/api/coletar', methods=['POST'])
def coletar_licitacoes():
    """Coleta novas licitações - VERSÃO CORRIGIDA COM DADOS DE EXEMPLO"""
    try:
        logger.info("Iniciando coleta de licitações...")
        
        # Por enquanto, usar dados de exemplo
        # Quando a API estiver acessível, substituir por busca real
        licitacoes_raw = collector.criar_licitacoes_exemplo()
        
        total_encontradas = len(licitacoes_raw)
        total_relevantes = 0
        
        for licitacao_raw in licitacoes_raw:
            if collector.eh_relevante(licitacao_raw):
                licitacao = collector.processar_licitacao(licitacao_raw)
                if db.salvar_licitacao(licitacao):
                    total_relevantes += 1
        
        db.registrar_coleta(total_encontradas, total_relevantes, 'sucesso')
        
        return jsonify({
            'success': True,
            'total_encontradas': total_encontradas,
            'total_relevantes': total_relevantes,
            'mensagem': f'Coleta concluída! {total_relevantes} licitações relevantes encontradas. (Usando dados de exemplo)'
        })
        
    except Exception as e:
        logger.error(f"Erro na coleta: {e}")
        db.registrar_coleta(0, 0, f'erro: {str(e)}')
        return jsonify({
            'success': False,
            'erro': str(e)
        }), 500


@app.route('/api/licitacoes', methods=['GET'])
def listar_licitacoes():
    """Lista licitações com filtros"""
    try:
        filtros = {
            'situacao': request.args.get('situacao'),
            'data_inicio': request.args.get('data_inicio'),
            'data_fim': request.args.get('data_fim'),
            'busca': request.args.get('busca')
        }
        
        filtros = {k: v for k, v in filtros.items() if v}
        licitacoes = db.buscar_licitacoes(filtros)
        
        return jsonify({
            'success': True,
            'total': len(licitacoes),
            'licitacoes': licitacoes
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar licitações: {e}")
        return jsonify({
            'success': False,
            'erro': str(e)
        }), 500


@app.route('/api/licitacoes/<int:id>', methods=['GET'])
def obter_licitacao(id):
    """Obtém detalhes de uma licitação específica"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM licitacoes WHERE id = ?", (id,))
        licitacao = cursor.fetchone()
        conn.close()
        
        if licitacao:
            db.marcar_visualizado(id)
            
            return jsonify({
                'success': True,
                'licitacao': dict(licitacao)
            })
        else:
            return jsonify({
                'success': False,
                'erro': 'Licitação não encontrada'
            }), 404
            
    except Exception as e:
        logger.error(f"Erro ao obter licitação: {e}")
        return jsonify({
            'success': False,
            'erro': str(e)
        }), 500


@app.route('/api/licitacoes/<int:id>/observacao', methods=['POST'])
def adicionar_observacao_api(id):
    """Adiciona observação a uma licitação"""
    try:
        data = request.json
        observacao = data.get('observacao', '')
        
        db.adicionar_observacao(id, observacao)
        
        return jsonify({
            'success': True,
            'mensagem': 'Observação adicionada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao adicionar observação: {e}")
        return jsonify({
            'success': False,
            'erro': str(e)
        }), 500


@app.route('/api/estatisticas', methods=['GET'])
def obter_estatisticas():
    """Retorna estatísticas gerais"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM licitacoes")
        total = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT situacao, COUNT(*) as quantidade 
            FROM licitacoes 
            GROUP BY situacao
        """)
        por_situacao = {row['situacao']: row['quantidade'] for row in cursor.fetchall()}
        
        cursor.execute("SELECT SUM(valor_total) as total FROM licitacoes")
        valor_total = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT COUNT(*) as total FROM licitacoes WHERE visualizado = 0")
        nao_visualizadas = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT * FROM historico_coletas 
            ORDER BY data_coleta DESC 
            LIMIT 10
        """)
        ultimas_coletas = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'estatisticas': {
                'total_licitacoes': total,
                'por_situacao': por_situacao,
                'valor_total_estimado': valor_total,
                'nao_visualizadas': nao_visualizadas,
                'ultimas_coletas': ultimas_coletas
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({
            'success': False,
            'erro': str(e)
        }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🖨️  SISTEMA DE MONITORAMENTO DE LICITAÇÕES PNCP")
    print("="*60)
    print("\n✓ Servidor iniciado com sucesso!")
    print(f"\n📍 Acesse: http://localhost:5000")
    print(f"📍 Rede local: http://[seu-ip]:5000")
    print("\n⚠️  NOTA: Usando dados de exemplo inicialmente")
    print("   A integração com a API real do PNCP será feita após testes\n")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
