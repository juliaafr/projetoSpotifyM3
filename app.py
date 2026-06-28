from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="VALIMUSIC"
    )

@app.route("/")
def index():
    return render_template("index.html")

# =====================================================================
# CRUD DE MÚSICAS
# =====================================================================

# READ — lista todas as músicas
# SQL equivalente: SELECT m.*, a.nome as nome_album FROM MUSICA m LEFT JOIN ALBUM a ON m.id_album = a.id_album
@app.route("/musicas")
def musicas():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.*, a.nome as nome_album 
        FROM MUSICA m 
        LEFT JOIN ALBUM a ON m.id_album = a.id_album
    """)
    musicas = cursor.fetchall()
    db.close()
    return render_template("musicas.html", musicas=musicas)

# CREATE — formulário para adicionar música
# SQL equivalente: INSERT INTO MUSICA (nome, cantor, ano_lancamento, tipo, id_album) VALUES (...)
@app.route("/musicas/nova", methods=["GET", "POST"])
def nova_musica():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM ALBUM")
    albums = cursor.fetchall()

    if request.method == "POST":
        nome = request.form["nome"]
        cantor = request.form["cantor"]
        ano = request.form["ano_lancamento"]
        tipo = request.form["tipo"]
        id_album = request.form["id_album"]
        cursor.execute("""
            INSERT INTO MUSICA (nome, cantor, ano_lancamento, tipo, id_album) 
            VALUES (%s, %s, %s, %s, %s)
        """, (nome, cantor, ano, tipo, id_album))
        db.commit()
        db.close()
        return redirect(url_for("musicas"))

    db.close()
    return render_template("musica_form.html", musica=None, albums=albums)

# UPDATE — formulário para editar música
# SQL equivalente: UPDATE MUSICA SET nome=%s, cantor=%s, ... WHERE id_musica=%s
@app.route("/musicas/editar/<int:id>", methods=["GET", "POST"])
def editar_musica(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM ALBUM")
    albums = cursor.fetchall()

    if request.method == "POST":
        nome = request.form["nome"]
        cantor = request.form["cantor"]
        ano = request.form["ano_lancamento"]
        tipo = request.form["tipo"]
        id_album = request.form["id_album"]
        cursor.execute("""
            UPDATE MUSICA SET nome=%s, cantor=%s, ano_lancamento=%s, tipo=%s, id_album=%s
            WHERE id_musica=%s
        """, (nome, cantor, ano, tipo, id_album, id))
        db.commit()
        db.close()
        return redirect(url_for("musicas"))

    cursor.execute("SELECT * FROM MUSICA WHERE id_musica = %s", (id,))
    musica = cursor.fetchone()
    db.close()
    return render_template("musica_form.html", musica=musica, albums=albums)

# DELETE — remove uma música
# SQL equivalente: DELETE FROM MUSICA WHERE id_musica=%s
@app.route("/musicas/deletar/<int:id>")
def deletar_musica(id):
    db = get_db()
    cursor = db.cursor()
    # Primeiro remove da tabela de ligação para não violar a chave estrangeira
    # SQL: DELETE FROM PLAYLISTEMUSICA WHERE id_musica = %s
    cursor.execute("DELETE FROM PLAYLISTEMUSICA WHERE id_musica = %s", (id,))
    # Depois remove a música
    # SQL: DELETE FROM MUSICA WHERE id_musica = %s
    cursor.execute("DELETE FROM MUSICA WHERE id_musica = %s", (id,))
    db.commit()
    db.close()
    return redirect(url_for("musicas"))

# =====================================================================
# CRUD DE ÁLBUNS
# =====================================================================

# READ — lista todos os álbuns
# SQL equivalente: SELECT * FROM ALBUM
@app.route("/albums")
def albums():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM ALBUM")
    albums = cursor.fetchall()
    db.close()
    return render_template("albums.html", albums=albums)

# CREATE — formulário para adicionar álbum
# SQL equivalente: INSERT INTO ALBUM (nome, cantor, ano_lancamento) VALUES (...)
@app.route("/albums/novo", methods=["GET", "POST"])
def novo_album():
    if request.method == "POST":
        nome = request.form["nome"]
        cantor = request.form["cantor"]
        ano = request.form["ano_lancamento"]
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO ALBUM (nome, cantor, ano_lancamento) 
            VALUES (%s, %s, %s)
        """, (nome, cantor, ano))
        db.commit()
        db.close()
        return redirect(url_for("albums"))
    return render_template("album_form.html", album=None)

# UPDATE — formulário para editar álbum
# SQL equivalente: UPDATE ALBUM SET nome=%s, cantor=%s, ano_lancamento=%s WHERE id_album=%s
@app.route("/albums/editar/<int:id>", methods=["GET", "POST"])
def editar_album(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == "POST":
        nome = request.form["nome"]
        cantor = request.form["cantor"]
        ano = request.form["ano_lancamento"]
        cursor.execute("""
            UPDATE ALBUM SET nome=%s, cantor=%s, ano_lancamento=%s
            WHERE id_album=%s
        """, (nome, cantor, ano, id))
        db.commit()
        db.close()
        return redirect(url_for("albums"))
    cursor.execute("SELECT * FROM ALBUM WHERE id_album = %s", (id,))
    album = cursor.fetchone()
    db.close()
    return render_template("album_form.html", album=album)

# DELETE — remove um álbum
# SQL equivalente: DELETE FROM ALBUM WHERE id_album=%s
@app.route("/albums/deletar/<int:id>")
def deletar_album(id):
    db = get_db()
    cursor = db.cursor()
    # Remove álbum dos favoritos primeiro
    cursor.execute("DELETE FROM ALBUMFAVORITO WHERE id_album = %s", (id,))
    # Remove as músicas do álbum das playlists
    cursor.execute("""
        DELETE FROM PLAYLISTEMUSICA WHERE id_musica IN 
        (SELECT id_musica FROM MUSICA WHERE id_album = %s)
    """, (id,))
    # Remove as músicas do álbum
    cursor.execute("DELETE FROM MUSICA WHERE id_album = %s", (id,))
    # Remove o álbum
    cursor.execute("DELETE FROM ALBUM WHERE id_album = %s", (id,))
    db.commit()
    db.close()
    return redirect(url_for("albums"))

# =====================================================================
# CRUD DE PLAYLISTS
# =====================================================================

# READ — lista todas as playlists
# SQL equivalente: SELECT p.*, u.nome as nome_usuario FROM PLAYLIST p JOIN USUARIO u ON p.id_usuario = u.id_usuario
@app.route("/playlists")
def playlists():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, u.nome as nome_usuario 
        FROM PLAYLIST p 
        JOIN USUARIO u ON p.id_usuario = u.id_usuario
    """)
    playlists = cursor.fetchall()
    db.close()
    return render_template("playlists.html", playlists=playlists)

# CREATE — formulário para adicionar playlist
# SQL equivalente: INSERT INTO PLAYLIST (nome, id_usuario) VALUES (...)
@app.route("/playlists/nova", methods=["GET", "POST"])
def nova_playlist():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM USUARIO")
    usuarios = cursor.fetchall()
    if request.method == "POST":
        nome = request.form["nome"]
        id_usuario = request.form["id_usuario"]
        cursor.execute("""
            INSERT INTO PLAYLIST (nome, id_usuario) 
            VALUES (%s, %s)
        """, (nome, id_usuario))
        db.commit()
        db.close()
        return redirect(url_for("playlists"))
    db.close()
    return render_template("playlist_form.html", playlist=None, usuarios=usuarios)

# UPDATE — formulário para editar playlist
# SQL equivalente: UPDATE PLAYLIST SET nome=%s, id_usuario=%s WHERE id_playlist=%s
@app.route("/playlists/editar/<int:id>", methods=["GET", "POST"])
def editar_playlist(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM USUARIO")
    usuarios = cursor.fetchall()
    if request.method == "POST":
        nome = request.form["nome"]
        id_usuario = request.form["id_usuario"]
        cursor.execute("""
            UPDATE PLAYLIST SET nome=%s, id_usuario=%s
            WHERE id_playlist=%s
        """, (nome, id_usuario, id))
        db.commit()
        db.close()
        return redirect(url_for("playlists"))
    cursor.execute("SELECT * FROM PLAYLIST WHERE id_playlist = %s", (id,))
    playlist = cursor.fetchone()
    db.close()
    return render_template("playlist_form.html", playlist=playlist, usuarios=usuarios)

# DELETE — remove uma playlist
# SQL equivalente: DELETE FROM PLAYLIST WHERE id_playlist=%s
@app.route("/playlists/deletar/<int:id>")
def deletar_playlist(id):
    db = get_db()
    cursor = db.cursor()
    # Remove músicas da playlist primeiro
    cursor.execute("DELETE FROM PLAYLISTEMUSICA WHERE id_playlist = %s", (id,))
    # Remove a playlist
    cursor.execute("DELETE FROM PLAYLIST WHERE id_playlist = %s", (id,))
    db.commit()
    db.close()
    return redirect(url_for("playlists"))

if __name__ == "__main__":
    app.run(debug=True)