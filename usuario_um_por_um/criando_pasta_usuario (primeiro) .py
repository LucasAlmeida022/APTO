import os

# Diretório base
BASE_DIR = r"C:\Users\Admin\ATP"

# Entrada do nome da pessoa
nome_pessoa = input("Digite o nome da pessoa: ").strip()

# Caminhos completos
dir_fotos = os.path.join(BASE_DIR, "Fotos", nome_pessoa)
dir_faces = os.path.join(BASE_DIR, "Faces", nome_pessoa)

# Criação das pastas, se não existirem
os.makedirs(dir_fotos, exist_ok=True)
os.makedirs(dir_faces, exist_ok=True)

print(f"Pasta criada para fotos: {dir_fotos}")
print(f"Pasta criada para faces: {dir_faces}")
print("✅ Estrutura criada com sucesso!")
