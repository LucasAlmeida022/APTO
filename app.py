from flask import Flask, render_template, request, jsonify, session, flash, redirect, url_for
import face_recognition
import numpy as np
import base64
import cv2
import pyodbc  

app = Flask(__name__)
app.secret_key = "uma_chave_secreta_qualquer"

# Configurações do banco de dados
CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};" #drive necessário para realizar a conexão do banco de dados
    "SERVER=localhost;"       #altetar o nome de acordo com o nome do SEU SERVER no SQLSERVER 
    "DATABASE=APTO;" #base de dados precisa aletarar para que estivemos usando no momento
    "Trusted_Connection=yes;"      # indica autenticação do Windows não precisa altearr
    "TrustServerCertificate=yes;"  # evita problemas de certificado SSL,não precisa alterar
    "Encrypt=yes;" #sempre deve estar dessa forma
)

DIST_THRESHOLD = 0.6  # distância máxima para considerar correspondência


# Carrega embeddings do banco de dados usando CNN
def carregar_embeddings():
    conn = pyodbc.connect(CONN_STR) 
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.ID_ALUNO, a.NOME, e.EMBEDDING
        FROM EXTRACAO_FACIAL e
        JOIN ALUNOS a ON a.ID_ALUNO = e.ID_ALUNO
    """)
    resultados = cursor.fetchall()
    conn.close()

    embeddings = [(row.ID_ALUNO, row.NOME, np.frombuffer(row.EMBEDDING, dtype=np.float64)) 
                  for row in resultados]
    return embeddings

# Carrega todos os embeddings na inicialização
EMBEDDINGS = carregar_embeddings()

# Rota principal
@app.route('/')
def index():
    return render_template('index.html')

@app.route("/login/aluno", methods=["GET", "POST"])
def login_aluno():
    if request.method == "POST":
        RA = request.form.get("RA")
        SENHA = request.form.get("SENHA")

        conn = pyodbc.connect(CONN_STR)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ALUNOS WHERE RA = ?", (RA,))
        aluno = cursor.fetchone()
        conn.close()

        if aluno and aluno[3].strip() == SENHA.strip():  # índice 3 = SENHA
            session["usuario"] = aluno[1]  # índice 1 = NOME
            session["ra"] = aluno[2]       # índice 2 = RA
            session["tipo"] = "aluno"
            return redirect(url_for("inicial_aluno"))
        else:
            flash("RA ou SENHA incorretos")
            return redirect(url_for("login_aluno"))
            
    return render_template("login_aluno.html")


@app.route("/login/professor", methods=["GET", "POST"])
def login_professor():
    if request.method == "POST":
        EMAIL = request.form.get("EMAIL")
        SENHA = request.form.get("SENHA")

        conn = pyodbc.connect(CONN_STR)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM PROFESSORES WHERE EMAIL = ?", (EMAIL,))
        professor = cursor.fetchone()
        conn.close()

        if professor and professor[3].strip() == SENHA.strip():  # índice 3 = SENHA
            session["usuario"] = professor[1]  # índice 1 = NOME
            session["email"] = professor[2]    # índice 2 = EMAIL
            session["tipo"] = "professor"
            return redirect(url_for("inicial_professor"))
        else:
            flash("Email ou senha incorretos")
            return redirect(url_for("login_professor"))
            
    return render_template("login_professor.html")

@app.route("/inicial_aluno")
def inicial_aluno():
    if session.get("tipo") != "aluno" or not session.get("usuario"):
        flash("Acesso negado. Faça login como aluno.")
        return redirect(url_for("login_aluno"))
    
    nome_usuario = session.get("usuario")
    return render_template("inicial_aluno.html", nome=nome_usuario)

@app.route("/chamado_aluno")
def chamado_aluno():
    if session.get("tipo") != "aluno" or not session.get("usuario"):
        flash("Acesso negado. Faça login como aluno.")
        return redirect(url_for("login_aluno"))

    nome_usuario = session.get("usuario")
    return render_template("chamado_aluno.html", nome=nome_usuario)

@app.route("/presenca_aluno")
def presenca_aluno():
    if session.get("tipo") != "aluno" or not session.get("usuario"):
        flash("Acesso negado. Faça login como aluno.")
        return redirect(url_for("login_aluno"))
    
    nome_usuario = session.get("usuario")
    return render_template("inicial_aluno.html", nome=nome_usuario)

@app.route("/inicial_professor")
def inicial_professor():
    if session.get("tipo") != "professor" or not session.get("usuario"):
        flash("Acesso negado. Faça login como professor.")
        return redirect(url_for("login_professor"))
    
    nome_usuario = session.get("usuario")
    return render_template("inicial_professor.html", nome=nome_usuario)

@app.route("/disciplina_professor")
def disciplina_professor():
    if session.get("tipo") != "professor" or not session.get("usuario"):
        flash("Acesso negado. Faça login como professor.")
        return redirect(url_for("login_aluno"))
    
    nome_usuario = session.get("usuario")
    return render_template("disciplina_professor.html", nome=nome_usuario)

@app.route("/chamado_professor", methods=["GET", "POST"])
def chamado_professor():
    # Verifica se é professor logado
    if session.get("tipo") != "professor" or not session.get("usuario"):
        flash("Acesso negado. Faça login como professor.")
        return redirect(url_for("login_aluno"))
    
    # Se for GET → só mostra a página
    if request.method == "GET":
        nome_usuario = session.get("usuario")
        return render_template("chamado_professor.html", nome=nome_usuario)
    
    # Se for POST → executa reconhecimento facial
    elif request.method == "POST":
        data = request.get_json()
        image_data = data['image'].split(',')[1]  # remove "data:image/jpeg;base64,"
        img_bytes = base64.b64decode(image_data)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Detecta rostos
        face_locations = face_recognition.face_locations(rgb_img)
        # Extrai embeddings usando CNN
        face_encodings = face_recognition.face_encodings(rgb_img, face_locations, model="cnn")

        resultados = []

        for encoding in face_encodings:
            distancias = [np.linalg.norm(encoding - e[2]) for e in EMBEDDINGS]
            if distancias:
                min_dist = min(distancias)
                index = distancias.index(min_dist)
                if min_dist < DIST_THRESHOLD:
                    id_aluno, nome, _ = EMBEDDINGS[index]
                    resultados.append({'id': id_aluno, 'nome': nome, 'distancia': float(min_dist)})

        return jsonify(resultados)

if __name__ == '__main__':
    app.run(debug=True)