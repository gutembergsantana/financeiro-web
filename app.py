from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave_super_segura_123"

# 🔐 CONFIG LOGIN
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# 👤 USUÁRIO SIMPLES
class User(UserMixin):
    def __init__(self, id):
        self.id = id

users = {
    "admin": {"password": "123"}
}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# 📌 CONEXÃO BANCO
def conectar():
    conn = sqlite3.connect("financeiro.db")
    conn.row_factory = sqlite3.Row
    return conn

# 🔐 LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username]["password"] == password:
            user = User(username)
            login_user(user)
            return redirect("/")

        return "Usuário ou senha inválidos"

    return render_template("login.html")

# 🔓 LOGOUT
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# 🏠 HOME (PROTEGIDA)
@app.route("/", methods=["GET"])
@login_required
def index():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM movimentacoes ORDER BY id DESC")
    movimentacoes = cursor.fetchall()

    # 📊 PROVENTOS E DESPESAS
    cursor.execute("""
        SELECT tipo, SUM(valor) FROM movimentacoes GROUP BY tipo
    """)
    dados = cursor.fetchall()

    proventos = 0
    despesas = 0

    for tipo, total in dados:
        if tipo == "Provento":
            proventos = total
        elif tipo == "Despesa":
            despesas = total
    # 📊 DESPESAS POR CATEGORIA
    cursor.execute("""
    SELECT categoria_id, SUM(valor)
    FROM movimentacoes
    WHERE tipo = 'Despesa'
    GROUP BY categoria_id
    """)

    dados_categoria = cursor.fetchall()

    labels_categoria = []
    valores_categoria = []

    for linha in dados_categoria:
        labels_categoria.append(str(linha[0]))  # nome simples por enquanto
        valores_categoria.append(linha[1])
    
    conn.close()

    return render_template(
    "index.html",
    movimentacoes=movimentacoes,
    proventos=proventos,
    despesas=despesas,
    labels_categoria=labels_categoria,
    valores_categoria=valores_categoria
)
# ➕ ADICIONAR MOVIMENTAÇÃO
@app.route("/add", methods=["POST"])
@login_required
def add():
    descricao = request.form["descricao"]
    valor = float(request.form["valor"])
    tipo = request.form["tipo"]
    data_operacao = request.form["data_operacao"]

    conn = conectar()
    conn.execute("""
        INSERT INTO movimentacoes (data_operacao, tipo, descricao, valor)
        VALUES (?, ?, ?, ?)
    """, (data_operacao, tipo, descricao, valor))

    conn.commit()
    conn.close()

    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)