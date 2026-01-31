coleta_status = {
    "rodando": False,
    "uf_atual": None,
    "pagina": 0,
    "total_processadas": 0,
    "relevantes": 0,
    "mensagem": ""
}

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import sqlite3
import json
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PNCP_BASE_URL = "https://pncp.gov.br/api/consulta/v1"

PALAVRAS_CHAVE = [
    'impressora 3d', 'impressora tridimensional', 'impressao 3d',
    'impressao tridimensional', 'printer 3d', 'prototipagem rapida',
    'fdm', 'fff', 'resina', 'sla', 'dlp', 'lcd',
    'filamento', 'pla', 'abs', 'petg', 'tpu', 'nylon',
    'resina fotopolimerica', 'scanner 3d',
    'modelagem 3d', 'manufatura aditiva', 'fabricacao aditiva'
]

# ------------------ BANCO ------------------

class DatabaseManager:
    def __init__(self, db_path='licitacoes.db'):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute("""
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
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS historico_coletas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_encontradas INTEGER,
            total_relevantes INTEGER,
            status TEXT
        )
        """)

        conn.commit()
        conn.close()

    def salvar_licitacao(self, l):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
            INSERT OR IGNORE INTO licitacoes
            (numero_controlpncp, ano, sequencial, orgao_cnpj, orgao_nome, orgao_poder, orgao_esfera,
             unidade_nome, modalidade, objeto_compra, valor_total, situacao, data_publicacao,
             data_abertura_propostas, data_encerramento_propostas, link_sistema_origem,
             relevancia_score, palavras_encontradas, itens_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                l['numero_controlpncp'], l['ano'], l['sequencial'], l['orgao_cnpj'], l['orgao_nome'],
                l['orgao_poder'], l['orgao_esfera'], l['unidade_nome'], l['modalidade'],
                l['objeto_compra'], l['valor_total'], l['situacao'], l['data_publicacao'],
                l['data_abertura_propostas'], l['data_encerramento_propostas'], l['link_sistema_origem'],
                l['relevancia_score'], l['palavras_encontradas'], json.dumps(l['itens'])
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False
        finally:
            conn.close()

    def buscar_licitacoes(self, filtros=None):
        conn = self.get_connection()
        cur = conn.cursor()
        query = "SELECT * FROM licitacoes WHERE 1=1"
        params = []

        if filtros:
            if filtros.get("situacao"):
                query += " AND situacao=?"
                params.append(filtros["situacao"])
            if filtros.get("busca"):
                query += " AND (objeto_compra LIKE ? OR orgao_nome LIKE ?)"
                b = f"%{filtros['busca']}%"
                params.extend([b, b])

        query += " ORDER BY data_publicacao DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def registrar_coleta(self, total, relevantes, status):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO historico_coletas (total_encontradas, total_relevantes, status) VALUES (?, ?, ?)",
            (total, relevantes, status)
        )
        conn.commit()
        conn.close()

    def marcar_visualizado(self, id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE licitacoes SET visualizado=1 WHERE id=?", (id,))
        conn.commit()
        conn.close()

    def adicionar_observacao(self, id, obs):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE licitacoes SET observacoes=? WHERE id=?", (obs, id))
        conn.commit()
        conn.close()

# ------------------ COLETOR ------------------

class PNCPCollector:
    def __init__(self):
        self.session = requests.Session()

    def calcular_relevancia(self, texto):
        if not texto:
            return 0, []
        t = texto.lower()
        score = 0
        achadas = []
        for p in PALAVRAS_CHAVE:
            if p in t:
                achadas.append(p)
                score += 5
        return score, achadas

    def buscar_ultimas(self, dias=30, pagina=1, uf="SP"):
        data_fim = datetime.now()
        data_ini = data_fim - timedelta(days=dias)

        url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
        params = {
            "dataInicial": data_ini.strftime("%Y%m%d"),
            "dataFinal": data_fim.strftime("%Y%m%d"),
            "pagina": pagina,
            "uf": uf
        }

        r = self.session.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def processar(self, raw):
        objeto = raw.get("objetoCompra", "")
        score, palavras = self.calcular_relevancia(objeto)

        data_enc = raw.get("dataEncerramentoProposta")
        situacao = "aberta"
        if data_enc:
            try:
                if datetime.fromisoformat(data_enc[:10]) < datetime.now():
                    situacao = "encerrada"
            except:
                pass

        return {
            "numero_controlpncp": f"{raw.get('anoCompra')}-{raw.get('sequencialCompra')}",
            "ano": raw.get("anoCompra"),
            "sequencial": raw.get("sequencialCompra"),
            "orgao_cnpj": raw.get("orgaoEntidade", {}).get("cnpj"),
            "orgao_nome": raw.get("orgaoEntidade", {}).get("razaoSocial"),
            "orgao_poder": raw.get("orgaoEntidade", {}).get("poder"),
            "orgao_esfera": raw.get("orgaoEntidade", {}).get("esfera"),
            "unidade_nome": raw.get("unidadeOrgao", {}).get("nomeUnidade"),
            "modalidade": raw.get("modalidadeNome"),
            "objeto_compra": objeto,
            "valor_total": raw.get("valorTotalEstimado", 0),
            "situacao": situacao,
            "data_publicacao": (raw.get("dataPublicacaoPncp") or "")[:10],
            "data_abertura_propostas": raw.get("dataAberturaProposta"),
            "data_encerramento_propostas": data_enc,
            "link_sistema_origem": raw.get("linkSistemaOrigem"),
            "relevancia_score": score,
            "palavras_encontradas": ", ".join(palavras),
            "itens": raw.get("itens", [])
        }

    
# ------------------ APP ------------------

db = DatabaseManager()
collector = PNCPCollector()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/coletar", methods=["POST"])
def coletar():
    try:
        body = request.json or {}
        dias = body.get("dias", 365)  # padrão: 1 ano

        UFS = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
               "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]

        total = 0
        relevantes = 0

        for uf in UFS:
            logger.info(f"Coletando UF {uf}...")
            pagina = 1

            while True:
                data = collector.buscar_ultimas(dias=dias, pagina=pagina, uf=uf)

                compras = data.get("data") or data.get("items") or []
                if not compras:
                    break

                for c in compras:
                    total += 1
                    lic = collector.processar(c)

                    if lic["relevancia_score"] > 0:
                        if db.salvar_licitacao(lic):
                            relevantes += 1

                logger.info(f"UF {uf} página {pagina} processada ({len(compras)} registros)")
                pagina += 1

                if pagina > 20:  # limite de segurança por UF
                    break

        db.registrar_coleta(total, relevantes, "sucesso")

        return jsonify({
            "success": True,
            "total_encontradas": total,
            "total_relevantes": relevantes,
            "mensagem": f"Coleta concluída! {relevantes} licitações relevantes encontradas."
        })

    except Exception as e:
        logger.error(e)
        db.registrar_coleta(0, 0, str(e))
        return jsonify({"success": False, "erro": str(e)}), 500

@app.route("/api/licitacoes")
def listar():
    filtros = {
        "situacao": request.args.get("situacao"),
        "busca": request.args.get("busca"),
    }
    filtros = {k: v for k, v in filtros.items() if v}
    lic = db.buscar_licitacoes(filtros)
    return jsonify({"success": True, "total": len(lic), "licitacoes": lic})

@app.route("/api/licitacoes/<int:id>")
def obter(id):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM licitacoes WHERE id=?", (id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"success": False, "erro": "Não encontrada"}), 404

    db.marcar_visualizado(id)
    return jsonify({"success": True, "licitacao": dict(row)})

@app.route("/api/licitacoes/<int:id>/observacao", methods=["POST"])
def obs(id):
    obs = (request.json or {}).get("observacao", "")
    db.adicionar_observacao(id, obs)
    return jsonify({"success": True})

@app.route("/api/estatisticas")
def stats():
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as t FROM licitacoes")
    total = cur.fetchone()["t"]

    cur.execute("SELECT situacao, COUNT(*) as q FROM licitacoes GROUP BY situacao")
    por = {r["situacao"]: r["q"] for r in cur.fetchall()}

    cur.execute("SELECT COUNT(*) as t FROM licitacoes WHERE visualizado=0")
    novas = cur.fetchone()["t"]

    conn.close()

    return jsonify({
        "success": True,
        "estatisticas": {
            "total_licitacoes": total,
            "por_situacao": por,
            "nao_visualizadas": novas
        }
    })

if __name__ == "__main__":
    print("Rodando em http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
