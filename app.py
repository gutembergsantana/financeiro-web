from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "financeiro.db"


def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET"])
def index():
    conn = conectar()

    # filtro por período
    data_inicio = request.args.get("inicio")
    data_fim = request.args.get("fim")

    query = """
        SELECT m.id, m.descricao, m.valor, m.tipo,
               c.nome as categoria, m.data_operacao
        FROM movimentacoes m
        JOIN categorias c ON c.id = m.categoria_id
    """

    params = []

    if data_inicio and data_fim:
        query += " WHERE m.data_operacao BETWEEN ? AND ? "
        params.extend([data_inicio, data_fim])

    query += " ORDER BY m.id DESC"

    movimentacoes = conn.execute(query, params).fetchall()

    categorias = conn.execute("""
        SELECT id, nome FROM categorias
    """).fetchall()

    # resumo financeiro
    resumo_query = """
        SELECT
            COALESCE(SUM(CASE WHEN tipo='Provento' THEN valor END), 0),
            COALESCE(SUM(CASE WHEN tipo='Despesa' THEN valor END), 0)
        FROM movimentacoes
    """

    if data_inicio and data_fim:
        resumo_query += " WHERE data_operacao BETWEEN ? AND ? "
        resumo = conn.execute(resumo_query, params).fetchone()
    else:
        resumo = conn.execute(resumo_query).fetchone()

    proventos = resumo[0]
    despesas = resumo[1]
    saldo = proventos - despesas

    # gráfico por categoria (pizza)
    dados_categoria = conn.execute("""
        SELECT c.nome, SUM(m.valor)
        FROM movimentacoes m
        JOIN categorias c ON c.id = m.categoria_id
        WHERE m.tipo='Despesa'
        GROUP BY c.nome
    """).fetchall()

    labels_cat = [row[0] for row in dados_categoria]
    valores_cat = [row[1] for row in dados_categoria]

    # gráfico provento vs despesa (barras)
    dados_tipo = conn.execute("""
        SELECT tipo, SUM(valor)
        FROM movimentacoes
        GROUP BY tipo
    """).fetchall()

    labels_tipo = [row[0] for row in dados_tipo]
    valores_tipo = [row[1] for row in dados_tipo]

    # gráfico evolução mensal (linha)
    dados_mensais = conn.execute("""
        SELECT 
            strftime('%Y-%m', data_operacao) as mes,
            SUM(CASE WHEN tipo='Provento' THEN valor ELSE 0 END),
            SUM(CASE WHEN tipo='Despesa' THEN valor ELSE 0 END)
        FROM movimentacoes
        GROUP BY mes
        ORDER BY mes
    """).fetchall()

    labels_mes = [row[0] for row in dados_mensais]
    proventos_mes = [row[1] for row in dados_mensais]
    despesas_mes = [row[2] for row in dados_mensais]

    conn.close()


    return render_template(
        "index.html",
        movimentacoes=movimentacoes,
        categorias=categorias,
        proventos=proventos,
        despesas=despesas,
        saldo=saldo,
        data_inicio=data_inicio,
        data_fim=data_fim,
        labels_cat=labels_cat,
        valores_cat=valores_cat,
        labels_tipo=labels_tipo,
        valores_tipo=valores_tipo,
        labels_mes=labels_mes,
        proventos_mes=proventos_mes,
        despesas_mes=despesas_mes
    )


@app.route("/add", methods=["POST"])
def add():
    descricao = request.form["descricao"]
    valor = float(request.form["valor"])
    tipo = request.form["tipo"]
    categoria_id = int(request.form["categoria"])
    data_operacao = request.form["data_operacao"]

    conn = conectar()
    conn.execute("""
        INSERT INTO movimentacoes (
            data_operacao, tipo, categoria_id, descricao,
            credor_pagador, forma_transacao, valor
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data_operacao,
        tipo,
        categoria_id,
        descricao,
        "Manual",
        "Dinheiro",
        valor
    ))
    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/categorias")
def categorias():
    conn = conectar()
    dados = conn.execute("SELECT * FROM categorias").fetchall()
    conn.close()
    return render_template("categorias.html", dados=dados)


@app.route("/add_categoria", methods=["POST"])
def add_categoria():
    nome = request.form["nome"]

    conn = conectar()
    conn.execute("INSERT INTO categorias (nome) VALUES (?)", (nome,))
    conn.commit()
    conn.close()

    return redirect("/categorias")


@app.route("/cartoes")
def cartoes():
    conn = conectar()
    dados = conn.execute("SELECT * FROM cartoes").fetchall()
    conn.close()
    return render_template("cartoes.html", dados=dados)


@app.route("/add_cartao", methods=["POST"])
def add_cartao():
    nome = request.form["nome"]
    bandeira = request.form["bandeira"]

    conn = conectar()
    conn.execute("""
        INSERT INTO cartoes (nome_operadora, bandeira, dia_vencimento, limite)
        VALUES (?, ?, 10, 0)
    """, (nome, bandeira))
    conn.commit()
    conn.close()

    return redirect("/cartoes")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)