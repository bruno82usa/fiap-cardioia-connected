#!/usr/bin/env python3
"""
================================================================================
CardioIA — API REST de Monitoramento Cardíaco
================================================================================
Servidor Flask que expõe uma API REST para receber, armazenar e consultar
leituras de sinais vitais enviadas por dispositivos ESP32.

Funcionalidades:
  - Recebimento de leituras via POST /api/dados
  - Consulta dos últimos registros via GET /api/dados
  - Estatísticas agregadas via GET /api/dados/stats
  - Alertas automáticos quando BPM > 120 ou temperatura > 38°C
  - Consulta de alertas via GET /api/alertas

Autor: CardioIA Team
Versão: 1.0.0
================================================================================
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

# ---------------------------------------------------------------------------
# Flask e utilitários HTTP
# ---------------------------------------------------------------------------
from flask import Flask, request, jsonify, g

# ---------------------------------------------------------------------------
# Configuração da aplicação Flask
# ---------------------------------------------------------------------------
app = Flask(__name__)

# Caminho do banco de dados SQLite (configurável via variável de ambiente)
DATABASE = os.environ.get("CARDIOIA_DB_PATH", "cardioia.db")

# Limiares de alerta — podem ser sobrescritos por variáveis de ambiente
BPM_ALERTA = int(os.environ.get("CARDIOIA_BPM_ALERTA", "120"))
TEMP_ALERTA = float(os.environ.get("CARDIOIA_TEMP_ALERTA", "38.0"))

# ---------------------------------------------------------------------------
# Gerenciamento do banco de dados SQLite
# ---------------------------------------------------------------------------

def get_db():
    """
    Retorna uma conexão SQLite para a thread atual.
    A conexão é armazenada no objeto 'g' do Flask e reutilizada
    durante o ciclo de vida da requisição.
    """
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
        g.db.execute("PRAGMA journal_mode=WAL")  # Melhor concorrência
    return g.db


def close_db(e=None):
    """
    Fecha a conexão com o banco ao final da requisição.
    Chamada automaticamente pelo Flask via teardown_appcontext.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """
    Inicializa as tabelas do banco de dados caso ainda não existam.

    Tabelas criadas:
      - leituras: armazena cada leitura recebida do ESP32
      - alertas:  registra alertas gerados automaticamente
    """
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()

    # Tabela principal de leituras — cada linha é uma medição do ESP32
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            temperatura REAL    NOT NULL,   -- Temperatura corporal em °C
            umidade     REAL    NOT NULL,   -- Umidade relativa do ar em %
            bpm         INTEGER NOT NULL,   -- Batimentos cardíacos por minuto
            timestamp   TEXT    NOT NULL,   -- Timestamp ISO 8601 do ESP32
            status      TEXT    DEFAULT 'ok', -- Status da leitura: ok, alerta, erro
            recebido_em TEXT    DEFAULT (datetime('now')) -- Momento do recebimento
        )
    """)

    # Tabela de alertas — registra eventos que ultrapassaram os limiares
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            leitura_id  INTEGER NOT NULL,     -- FK para leituras.id
            tipo        TEXT    NOT NULL,      -- Tipo: 'bpm_alto' ou 'temp_alta'
            valor       REAL    NOT NULL,      -- Valor que disparou o alerta
            mensagem    TEXT    NOT NULL,      -- Descrição legível do alerta
            timestamp   TEXT    NOT NULL,      -- Timestamp da leitura original
            criado_em   TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (leitura_id) REFERENCES leituras(id)
        )
    """)

    # Índices para acelerar consultas comuns
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_leituras_timestamp
        ON leituras(timestamp DESC)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_alertas_criado
        ON alertas(criado_em DESC)
    """)

    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Lógica de verificação de alertas
# ---------------------------------------------------------------------------

def verificar_alertas(leitura_id, temperatura, bpm, timestamp):
    """
    Verifica se uma leitura ultrapassa os limiares de alerta.
    Se ultrapassar, registra o alerta na tabela 'alertas'.

    Parâmetros:
      - leitura_id:  ID da leitura no banco
      - temperatura: Valor de temperatura em °C
      - bpm:         Batimentos por minuto
      - timestamp:   Timestamp original da leitura

    Retorna:
      - Lista de alertas gerados (pode ser vazia)
    """
    alertas_gerados = []
    db = get_db()

    # Verifica BPM elevado — indicativo de taquicardia ou estresse cardíaco
    if bpm > BPM_ALERTA:
        mensagem = (
            f"⚠️ ALERTA CardioIA: Batimento cardíaco elevado detectado — "
            f"{bpm} BPM às {timestamp}. "
            f"Limiar de segurança: {BPM_ALERTA} BPM."
        )
        db.execute(
            "INSERT INTO alertas (leitura_id, tipo, valor, mensagem, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            (leitura_id, "bpm_alto", bpm, mensagem, timestamp),
        )
        alertas_gerados.append({"tipo": "bpm_alto", "valor": bpm, "mensagem": mensagem})

    # Verifica temperatura elevada — indicativo de febre ou infecção
    if temperatura > TEMP_ALERTA:
        mensagem = (
            f"🌡️ ALERTA CardioIA: Temperatura corporal elevada detectada — "
            f"{temperatura}°C às {timestamp}. "
            f"Limiar de segurança: {TEMP_ALERTA}°C."
        )
        db.execute(
            "INSERT INTO alertas (leitura_id, tipo, valor, mensagem, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            (leitura_id, "temp_alta", temperatura, mensagem, timestamp),
        )
        alertas_gerados.append(
            {"tipo": "temp_alta", "valor": temperatura, "mensagem": mensagem}
        )

    db.commit()
    return alertas_gerados


# ---------------------------------------------------------------------------
# Validação dos dados de entrada
# ---------------------------------------------------------------------------

def validar_dados(dados):
    """
    Valida o payload JSON recebido na rota POST /api/dados.

    Campos obrigatórios:
      - temperatura (float):  entre 30.0 e 45.0 (°C)
      - umidade     (float):  entre 0.0 e 100.0 (%)
      - bpm         (int):    entre 20 e 300 (batimentos/min)
      - timestamp   (str):    formato ISO 8601 (ex.: '2024-06-15T14:30:00')

    Retorna:
      - (None, None) se válido
      - (mensagem_erro, status_code) se inválido
    """
    # Verifica presença dos campos obrigatórios
    campos_obrigatorios = ["temperatura", "umidade", "bpm", "timestamp"]
    for campo in campos_obrigatorios:
        if campo not in dados:
            return f"Campo obrigatório ausente: '{campo}'", 400

    # Valida temperatura (faixa fisiológica plausível)
    try:
        temperatura = float(dados["temperatura"])
        if temperatura < 30.0 or temperatura > 45.0:
            return "Temperatura fora da faixa válida (30.0–45.0 °C)", 422
    except (TypeError, ValueError):
        return "Temperatura deve ser um número", 422

    # Valida umidade (porcentagem)
    try:
        umidade = float(dados["umidade"])
        if umidade < 0.0 or umidade > 100.0:
            return "Umidade fora da faixa válida (0.0–100.0 %)", 422
    except (TypeError, ValueError):
        return "Umidade deve ser um número", 422

    # Valida BPM (faixa fisiológica plausível)
    try:
        bpm = int(dados["bpm"])
        if bpm < 20 or bpm > 300:
            return "BPM fora da faixa válida (20–300)", 422
    except (TypeError, ValueError):
        return "BPM deve ser um número inteiro", 422

    # Valida formato do timestamp (ISO 8601 simplificado)
    timestamp = dados.get("timestamp", "")
    try:
        datetime.fromisoformat(timestamp)
    except (ValueError, TypeError):
        return "Timestamp inválido. Use formato ISO 8601 (ex.: 2024-06-15T14:30:00)", 422

    # Valida status (opcional)
    status = dados.get("status", "ok")
    if status not in ("ok", "alerta", "erro"):
        return "Status deve ser: ok, alerta ou erro", 422

    return None, None


# ---------------------------------------------------------------------------
# Rotas da API REST
# ---------------------------------------------------------------------------

@app.route("/api/dados", methods=["POST"])
def receber_dados():
    """
    POST /api/dados
    ----------------
    Recebe uma leitura de sinais vitais do ESP32 e armazena no banco.

    Payload esperado (JSON):
      {
        "temperatura": 36.5,
        "umidade": 45.2,
        "bpm": 72,
        "timestamp": "2024-06-15T14:30:00",
        "status": "ok"
      }

    Resposta de sucesso (201):
      {
        "id": 42,
        "mensagem": "Leitura registrada com sucesso",
        "alertas": []
      }

    Resposta com alertas (201):
      {
        "id": 42,
        "mensagem": "Leitura registrada com sucesso",
        "alertas": [
          {"tipo": "bpm_alto", "valor": 135, "mensagem": "..."}
        ]
      }
    """
    # Obtém o JSON do corpo da requisição
    dados = request.get_json(silent=True)
    if dados is None:
        return jsonify({"erro": "Payload JSON inválido ou ausente"}), 400

    # Valida os dados recebidos
    erro, codigo = validar_dados(dados)
    if erro:
        return jsonify({"erro": erro}), codigo

    # Insere a leitura no banco de dados
    db = get_db()
    cursor = db.execute(
        "INSERT INTO leituras (temperatura, umidade, bpm, timestamp, status) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            float(dados["temperatura"]),
            float(dados["umidade"]),
            int(dados["bpm"]),
            dados["timestamp"],
            dados.get("status", "ok"),
        ),
    )
    leitura_id = cursor.lastrowid
    db.commit()

    # Verifica se a leitura dispara alertas
    alertas = verificar_alertas(
        leitura_id,
        float(dados["temperatura"]),
        int(dados["bpm"]),
        dados["timestamp"],
    )

    # Monta a resposta
    resposta = {
        "id": leitura_id,
        "mensagem": "Leitura registrada com sucesso",
        "alertas": alertas,
    }

    # Se houve alertas, inclui no log do servidor
    if alertas:
        for a in alertas:
            app.logger.warning(f"ALERTA: {a['mensagem']}")

    return jsonify(resposta), 201


@app.route("/api/dados", methods=["GET"])
def listar_dados():
    """
    GET /api/dados
    --------------
    Lista os últimos 100 registros de leituras, ordenados do mais recente
    para o mais antigo.

    Parâmetros de query opcionais:
      - limite (int): número máximo de registros (padrão: 100, máx: 500)

    Resposta (200):
      {
        "total": 100,
        "dados": [
          {
            "id": 42,
            "temperatura": 36.5,
            "umidade": 45.2,
            "bpm": 72,
            "timestamp": "2024-06-15T14:30:00",
            "status": "ok",
            "recebido_em": "2024-06-15T14:30:05"
          },
          ...
        ]
      }
    """
    # Limita a quantidade de registros retornados
    limite = request.args.get("limite", 100, type=int)
    limite = min(limite, 500)  # Máximo de 500 registros por requisição

    db = get_db()
    cursor = db.execute(
        "SELECT * FROM leituras ORDER BY recebido_em DESC LIMIT ?", (limite,)
    )
    linhas = cursor.fetchall()

    # Converte cada Row do SQLite para dicionário
    dados = []
    for linha in linhas:
        dados.append(
            {
                "id": linha["id"],
                "temperatura": linha["temperatura"],
                "umidade": linha["umidade"],
                "bpm": linha["bpm"],
                "timestamp": linha["timestamp"],
                "status": linha["status"],
                "recebido_em": linha["recebido_em"],
            }
        )

    return jsonify({"total": len(dados), "dados": dados}), 200


@app.route("/api/dados/stats", methods=["GET"])
def estatisticas():
    """
    GET /api/dados/stats
    --------------------
    Retorna estatísticas agregadas das leituras armazenadas:
    média, valor máximo e valor mínimo de temperatura e BPM.

    Parâmetros de query opcionais:
      - horas (int): janela de tempo em horas (padrão: 24, 0 = todos)

    Resposta (200):
      {
        "periodo_horas": 24,
        "total_registros": 1440,
        "temperatura": {
          "media": 36.4,
          "max": 37.2,
          "min": 35.8
        },
        "bpm": {
          "media": 74.5,
          "max": 142,
          "min": 58
        }
      }
    """
    horas = request.args.get("horas", 24, type=int)

    db = get_db()

    # Se horas > 0, filtra por janela de tempo; senão, consulta tudo
    if horas > 0:
        # Calcula o timestamp de corte (agora - N horas)
        corte = (datetime.utcnow() - timedelta(hours=horas)).isoformat()
        cursor = db.execute(
            "SELECT temperatura, bpm FROM leituras WHERE recebido_em >= ?", (corte,)
        )
    else:
        cursor = db.execute("SELECT temperatura, bpm FROM leituras")

    linhas = cursor.fetchall()

    if not linhas:
        return jsonify({"erro": "Nenhum dado disponível para o período"}), 404

    # Extrai listas de temperatura e BPM para cálculo
    temperaturas = [r["temperatura"] for r in linhas]
    bpms = [r["bpm"] for r in linhas]
    n = len(linhas)

    # Calcula as estatísticas
    stats = {
        "periodo_horas": horas if horas > 0 else "todos",
        "total_registros": n,
        "temperatura": {
            "media": round(sum(temperaturas) / n, 2),
            "max": round(max(temperaturas), 2),
            "min": round(min(temperaturas), 2),
        },
        "bpm": {
            "media": round(sum(bpms) / n, 2),
            "max": max(bpms),
            "min": min(bpms),
        },
    }

    return jsonify(stats), 200


@app.route("/api/alertas", methods=["GET"])
def listar_alertas():
    """
    GET /api/alertas
    ----------------
    Lista os últimos alertas gerados pelo sistema.

    Parâmetros de query opcionais:
      - limite (int): número máximo de alertas (padrão: 50, máx: 200)
      - tipo   (str): filtra por tipo ('bpm_alto' ou 'temp_alta')

    Resposta (200):
      {
        "total": 5,
        "alertas": [
          {
            "id": 3,
            "tipo": "bpm_alto",
            "valor": 135,
            "mensagem": "⚠️ ALERTA CardioIA: ...",
            "timestamp": "2024-06-15T14:30:00",
            "criado_em": "2024-06-15T14:30:05"
          },
          ...
        ]
      }
    """
    limite = request.args.get("limite", 50, type=int)
    limite = min(limite, 200)
    tipo = request.args.get("tipo", None)

    db = get_db()

    # Constrói a query dinamicamente conforme os filtros
    if tipo and tipo in ("bpm_alto", "temp_alta"):
        cursor = db.execute(
            "SELECT * FROM alertas WHERE tipo = ? ORDER BY criado_em DESC LIMIT ?",
            (tipo, limite),
        )
    else:
        cursor = db.execute(
            "SELECT * FROM alertas ORDER BY criado_em DESC LIMIT ?", (limite,)
        )

    linhas = cursor.fetchall()

    alertas = []
    for linha in linhas:
        alertas.append(
            {
                "id": linha["id"],
                "leitura_id": linha["leitura_id"],
                "tipo": linha["tipo"],
                "valor": linha["valor"],
                "mensagem": linha["mensagem"],
                "timestamp": linha["timestamp"],
                "criado_em": linha["criado_em"],
            }
        )

    return jsonify({"total": len(alertas), "alertas": alertas}), 200


@app.route("/api/health", methods=["GET"])
def health_check():
    """
    GET /api/health
    ---------------
    Endpoint de health check para monitoramento da API.
    """
    return jsonify({"status": "ok", "servico": "CardioIA API", "versao": "1.0.0"}), 200


# ---------------------------------------------------------------------------
# Tratamento de erros
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def nao_encontrado(e):
    """Retorna JSON padronizado para rotas inexistentes."""
    return jsonify({"erro": "Rota não encontrada"}), 404


@app.errorhandler(405)
def metodo_nao_permitido(e):
    """Retorna JSON padronizado para métodos HTTP não suportados."""
    return jsonify({"erro": "Método HTTP não permitido para esta rota"}), 405


@app.errorhandler(500)
def erro_interno(e):
    """Retorna JSON padronizado para erros internos do servidor."""
    return jsonify({"erro": "Erro interno do servidor"}), 500


# ---------------------------------------------------------------------------
# Inicialização e execução
# ---------------------------------------------------------------------------

# Registra os hooks de ciclo de vida do banco
app.teardown_appcontext(close_db)

# Inicializa o banco de dados na primeira execução
with app.app_context():
    init_db()

# ---------------------------------------------------------------------------
# Ponto de entrada principal
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Inicia o servidor Flask na porta 5000.

    Para desenvolvimento:
      python api_server.py

    Para produção, use um servidor WSGI como gunicorn:
      gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
    """
    porta = int(os.environ.get("CARDIOIA_PORT", "5000"))
    debug = os.environ.get("CARDIOIA_DEBUG", "false").lower() == "true"

    print(f"🫀 CardioIA API iniciando na porta {porta}...")
    print(f"   Endpoints disponíveis:")
    print(f"   - POST /api/dados       → Receber leituras")
    print(f"   - GET  /api/dados       → Listar registros")
    print(f"   - GET  /api/dados/stats → Estatísticas")
    print(f"   - GET  /api/alertas     → Listar alertas")
    print(f"   - GET  /api/health      → Health check")
    print(f"   Limiar BPM: {BPM_ALERTA} | Limiar Temp: {TEMP_ALERTA}°C")

    app.run(host="0.0.0.0", port=porta, debug=debug)
