"""
Sistema de Monitoramento de Licitações PNCP
Foco: Impressão 3D (equipamentos, insumos e serviços)
Autor: você 😄
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import requests
import sqlite3
import json
import logging
from datetime import datetime, timedelta

# =============================
# CONFIGURAÇÕES GERAIS
# =============================

PNCP_BASE_URL = "https://pncp.gov.br/api/pncp/v1"
DB_PATH = "licitacoes.db"

PALAVRAS_CHAVE = [
    "impressora 3d", "impressao 3d", "impressora tridimensional",
    "fdm", "fff", "resina", "sla", "dlp", "lcd",
    "filamento", "pla", "abs", "petg", "tpu", "nylon",
    "scanner 3d", "manufatura aditiva", "fabricacao aditiva",
    "modelagem 3d", "prototipagem", "cad 3d"
]

# =============================
# APP / LOG
# =============================

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PNCP")

# =============================
# BANCO DE DADOS
# =============================

class Database:
    def __init__(self):
        self.init_db()

    def connect(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS licitacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT UNIQUE,
                orgao TEXT,
                objeto TEXT,
                modalidade TEXT,
                valor REAL,
                situacao TEXT,
                data_publicacao TEXT,
                link TEXT,
                score INTEGER,
                palavras TEXT,
                visualizado INTEGER DEFAULT 0,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS coletas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total INTEGER,
                relevantes INTEGER,
                status TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Banco de dados pronto")

    def salvar_licitacao(self, data):
        conn = self.connect()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT OR IGNORE INTO licitacoes
                (numero, orgao, objeto, modalidade, valor, situacao,
                 data_publicacao, link, score, palavras)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["numero"],
                data["orgao"],
                data["objeto"],
                data["modalidade"],
                data["valor"],
                data["situacao"],
                data["data_publicacao"],
                data["link"],
                data["score"],
                data["palavras"]
            ))
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Erro DB: {e}")
            return False
        finally:
            conn.close()

    def listar_licitacoes(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM licitacoes ORDER BY data_publicacao DESC")
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def registrar_coleta(self, total, relevantes, status):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO coletas (total, relevantes, status)
            VALUES (?, ?, ?)
        """, (total, relevantes, status))
        conn.commit()
        conn.close()

db = Database()

# =============================
# COLETOR PNCP
# =============================

class PNCPCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "PNCP-Monitor"
        })

    def calcular_relevancia(self, texto):
        texto = texto.lower()
        score = 0
        achadas = []

        for p in PALAVRAS_CHAVE:
            if p in texto:
                achadas.append(p)
                score += 5 if "impressora" in p else 2

        return score, achadas

    def buscar_recentes(self, dias=7):
        data_fim = datetime.now().strftime("%Y-%m-%d")
        data_ini = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")

        endpoint = f"{PNCP_BASE_URL}/contratacoes/publicacao"
        params = {
            "pagina": 1,
            "tamanhoPagina": 50,
            "dataInicial": data_ini,
            "dataFinal": data_fim
        }

        try:
            r = self.session.get(endpoint, params=params, timeout=30)
            r.raise_for_status()
            return r.json().get("data", [])
        except Exception as e:
            logger.error(f"Erro PNCP: {e}")
            return []

    def normalizar(self, raw):
        objeto = raw.get("objetoCompra", "")
        score, palavras = self.calcular_relevancia(objeto)

        if score == 0:
            return None

        return {
            "numero": f'{raw.get("anoCompra")}-{raw.get("sequencialCompra")}',
            "orgao": raw.get("orgaoEntidade", {}).get("razaoSocial"),
            "objeto": objeto,
            "modalidade": raw.get("modalidadeNome"),
            "valor": raw.get("valorTotalEstimado", 0),
            "situacao": "aberta",
            "data_publicacao": raw.get("dataPublicacaoPncp", "")[:10],
            "link": raw.get("linkSistemaOrigem"),
            "score": score,
            "palavras": ", ".join(palavras)
        }

collector = PNCPCollector()

# =============================
# ROTAS
# =============================

@app.route("/")
def index():
    return "<h2>PNCP Monitor ativo 🚀</h2>"

@app.route("/api/coletar", methods=["POST"])
def coletar():
    try:
        logger.info("Coletando PNCP...")
        raws = collector.buscar_recentes()
        total = len(raws)
        relevantes = 0

        for r in raws:
            lic = collector.normalizar(r)
            if lic and db.salvar_licitacao(lic):
                relevantes += 1

        db.registrar_coleta(total, relevantes, "sucesso")

        return jsonify({
            "success": True,
            "total": total,
            "relevantes": relevantes
        })
    except Exception as e:
        db.registrar_coleta(0, 0, "erro")
        return jsonify({"success": False, "erro": str(e)}), 500

@app.route("/api/licitacoes")
def listar():
    return jsonify(db.listar_licitacoes())

# =============================
# MAIN
# =============================

if __name__ == "__main__":
    print("\nPNCP Monitor iniciado")
    print("http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
