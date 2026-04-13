from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
with app.app_context():
    criar_banco()
app.secret_key = os.environ.get("SECRET_KEY", "dev")  # altere para algo seguro em produção

UPLOAD_IMAGENS = 'uploads/imagens'
UPLOAD_ARQUIVOS = 'uploads/uploads'
os.makedirs(UPLOAD_IMAGENS, exist_ok=True)
os.makedirs(UPLOAD_ARQUIVOS, exist_ok=True)

app.config['UPLOAD_IMAGENS'] = UPLOAD_IMAGENS
app.config['UPLOAD_ARQUIVOS'] = UPLOAD_ARQUIVOS

def conectar():
    return sqlite3.connect("banco.db")

def criar_banco():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conhecimento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT,
        descricao TEXT,
        categoria TEXT,
        tags TEXT,
        imagem TEXT,
        sistema TEXT,
        arquivo TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        senha TEXT
    )
    """)
    conn.commit()
    conn.close()

def usuario_logado():
    return session.get("usuario")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        user = cursor.fetchone()
        conn.close()
        if user:
            session["usuario"] = usuario
            return redirect(url_for("index"))
        else:
            return render_template("login.html", erro="Usuário ou senha incorretos")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

def login_requerido(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not usuario_logado():
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

# -----------------------
# ROTAS CONHECIMENTO
# -----------------------

@app.route("/")
@login_requerido
def index():
    busca = request.args.get("busca", "")
    sistema_filtro = request.args.get("sistema", "")
    conn = conectar()
    cursor = conn.cursor()
    query = "SELECT * FROM conhecimento WHERE (titulo LIKE ? OR descricao LIKE ? OR tags LIKE ?)"
    params = [f"%{busca}%", f"%{busca}%", f"%{busca}%"]
    if sistema_filtro:
        query += " AND sistema = ?"
        params.append(sistema_filtro)
    cursor.execute(query, params)
    dados = cursor.fetchall()
    conn.close()
    return render_template("index.html", dados=dados, busca=busca, sistema_filtro=sistema_filtro)

@app.route("/adicionar", methods=["GET", "POST"])
@login_requerido
def adicionar():
    if request.method == "POST":
        titulo = request.form["titulo"]
        descricao = request.form["descricao"]
        categoria = request.form["categoria"]
        tags = request.form["tags"]
        sistema = request.form["sistema"]
        imagem = request.files.get("imagem")
        arquivo = request.files.get("arquivo")
        nome_imagem = ""
        nome_arquivo = ""
        if imagem and imagem.filename != "":
            nome_imagem = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_IMAGENS'], nome_imagem))
        if arquivo and arquivo.filename != "":
            nome_arquivo = secure_filename(arquivo.filename)
            arquivo.save(os.path.join(app.config['UPLOAD_ARQUIVOS'], nome_arquivo))
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conhecimento (titulo, descricao, categoria, tags, imagem, sistema, arquivo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (titulo, descricao, categoria, tags, nome_imagem, sistema, nome_arquivo))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))
    return render_template("adicionar.html")

@app.route("/detalhe/<int:id>")
@login_requerido
def detalhe(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conhecimento WHERE id = ?", (id,))
    dado = cursor.fetchone()
    conn.close()
    return render_template("detalhe.html", dado=dado)

@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_requerido
def editar(id):
    conn = conectar()
    cursor = conn.cursor()
    if request.method == "POST":
        titulo = request.form["titulo"]
        descricao = request.form["descricao"]
        categoria = request.form["categoria"]
        tags = request.form["tags"]
        sistema = request.form["sistema"]
        imagem = request.files.get("imagem")
        arquivo = request.files.get("arquivo")
        nome_imagem = ""
        nome_arquivo = ""
        if imagem and imagem.filename != "":
            nome_imagem = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_IMAGENS'], nome_imagem))
        if arquivo and arquivo.filename != "":
            nome_arquivo = secure_filename(arquivo.filename)
            arquivo.save(os.path.join(app.config['UPLOAD_ARQUIVOS'], nome_arquivo))
        # manter arquivos antigos caso não envie novos
        cursor.execute("SELECT imagem, arquivo FROM conhecimento WHERE id = ?", (id,))
        antigo = cursor.fetchone()
        if not nome_imagem:
            nome_imagem = antigo[0]
        if not nome_arquivo:
            nome_arquivo = antigo[1]
        cursor.execute("""
            UPDATE conhecimento SET titulo=?, descricao=?, categoria=?, tags=?, imagem=?, sistema=?, arquivo=?
            WHERE id=?
        """, (titulo, descricao, categoria, tags, nome_imagem, sistema, nome_arquivo, id))
        conn.commit()
        conn.close()
        return redirect(url_for("detalhe", id=id))
    cursor.execute("SELECT * FROM conhecimento WHERE id=?", (id,))
    dado = cursor.fetchone()
    conn.close()
    return render_template("editar.html", dado=dado)

@app.route("/excluir/<int:id>")
@login_requerido
def excluir(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conhecimento WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# -----------------------
# ROTAS USUÁRIOS
# -----------------------

@app.route("/usuarios")
@login_requerido
def listar_usuarios():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, usuario FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return render_template("usuarios.html", usuarios=usuarios)

@app.route("/usuarios/adicionar", methods=["GET", "POST"])
@login_requerido
def adicionar_usuario():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", (usuario, senha))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Usuário já existe"
        finally:
            conn.close()
        return redirect(url_for("listar_usuarios"))
    return render_template("usuarios_adicionar.html")

# -----------------------
# INICIALIZAÇÃO
# -----------------------

if __name__ == "__main__":
    criar_banco()
    # cria usuário admin padrão, se não existir
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE usuario='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "admin"))
        conn.commit()
    conn.close()
    app.run(debug=True)