import face_recognition
import numpy as np
import os
from os.path import join, isfile
import pyodbc

# Diretório base (sem o nome)
DIR_FACES_BASE = r"C:\Users\Admin\ATP\Faces"

MODO_FACE = "hog"  # rápido | "cnn" é mais pesado
CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=apto;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
    "Encrypt=yes;"
)

RA_BASE = 111760000
SENHA_PADRAO = "senha123"

def get_connection():
    return pyodbc.connect(CONN_STR)

def gerar_ra_automatico(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ALUNOS")
    count = cursor.fetchone()[0] + 1
    ra_num = RA_BASE + count
    ra_str = f"{ra_num:012d}sp"
    return ra_str

def salvar_embedding(id_aluno, embedding, conn):
    cursor = conn.cursor()
    embedding_bytes = embedding.tobytes()
    cursor.execute("""
        INSERT INTO EXTRACAO_FACIAL (ID_ALUNO, EMBEDDING)
        VALUES (?, ?)
    """, (id_aluno, embedding_bytes))
    conn.commit()
    print(f"[OK] Embedding salvo para aluno ID {id_aluno}")

def get_id_aluno(nome_aluno, conn):
    if not nome_aluno or nome_aluno.strip() == "":
        raise ValueError("O nome do aluno não pode ser vazio")

    nome_aluno = nome_aluno.strip()
    cursor = conn.cursor()

    cursor.execute("SELECT ID_ALUNO FROM ALUNOS WHERE UPPER(NOME) = UPPER(?)", (nome_aluno,))
    row = cursor.fetchone()

    if row:
        return row[0]
    else:
        ra_automatico = gerar_ra_automatico(conn)
        cursor.execute(
            "INSERT INTO ALUNOS (NOME, RA, SENHA) OUTPUT INSERTED.ID_ALUNO VALUES (?, ?, ?)",
            (nome_aluno, ra_automatico, SENHA_PADRAO)
        )
        id_aluno = cursor.fetchone()[0]
        conn.commit()
        print(f"[OK] Novo aluno inserido: {nome_aluno} | RA: {ra_automatico}")
        return id_aluno

def processar_pessoa(diretorio_pessoa, nome_aluno):
    print(f"\n[PROCESSANDO ALUNO] {nome_aluno}")

    with get_connection() as conn:
        try:
            id_aluno = get_id_aluno(nome_aluno, conn)
        except ValueError as e:
            print(f"[ERRO] {e}")
            return

        for filename in os.listdir(diretorio_pessoa):
            path = join(diretorio_pessoa, filename)
            if not isfile(path) or not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue

            print(f"  [IMAGEM] {filename}")
            imagem = face_recognition.load_image_file(path)
            boxes = face_recognition.face_locations(imagem, model=MODO_FACE)
            embeddings = face_recognition.face_encodings(imagem, boxes)

            if embeddings:
                vetor = np.array(embeddings[0], dtype=np.float64)
                salvar_embedding(id_aluno, vetor, conn)
            else:
                print(f"  [ERRO] Nenhum rosto encontrado em: {filename}")

def carregar_embeddings():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ID_ALUNO, EMBEDDING FROM EXTRACAO_FACIAL")
        resultados = cursor.fetchall()

    embeddings = [(id_aluno, np.frombuffer(embedding_bytes, dtype=np.float64))
                  for id_aluno, embedding_bytes in resultados]
    return embeddings

if __name__ == "__main__":
    nome_pessoa = input("Digite o nome da pessoa: ").strip()
    dir_pessoa = join(DIR_FACES_BASE, nome_pessoa)

    if not os.path.isdir(dir_pessoa):
        print(f"[ERRO] Pasta de faces não encontrada: {dir_pessoa}")
    else:
        print(f"\n[INICIANDO] Extração de embeddings de {nome_pessoa}...")
        processar_pessoa(dir_pessoa, nome_pessoa)
        print(f"\n[CONCLUÍDO] Embeddings de {nome_pessoa} salvos no banco.")

        # Teste opcional
        emb = carregar_embeddings()
        print(f"\n[TESTE] Carregados {len(emb)} embeddings do banco.")
        if emb:
            print(f"Exemplo: ID_ALUNO={emb[0][0]}")
            print(emb[0][1])
