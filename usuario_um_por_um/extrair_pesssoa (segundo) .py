from PIL import Image
from numpy import asarray
import cv2
import os
from os.path import join, exists
import mediapipe as mp

# Diretórios principais (sem o nome da pessoa)
DIR_FOTOS_BASE = r"C:\Users\Admin\ATP\Fotos"
DIR_FACES_BASE = r"C:\Users\Admin\ATP\Faces"

detector = mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)

def extrair_face(arquivo, size=(180, 180)):
    img = Image.open(arquivo).convert('RGB')
    vetor = asarray(img)
    img_bgr = cv2.cvtColor(vetor, cv2.COLOR_RGB2BGR)
    resultado = detector.process(img_bgr)

    if not resultado.detections:
        print(f"[AVISO] Nenhuma face detectada em: {arquivo}")
        return None

    bbox = resultado.detections[0].location_data.relative_bounding_box
    h, w, _ = vetor.shape
    x1 = int(bbox.xmin * w)
    y1 = int(bbox.ymin * h)
    x2 = int((bbox.xmin + bbox.width) * w)
    y2 = int((bbox.ymin + bbox.height) * h)
    x1, y1 = max(x1, 0), max(y1, 0)
    x2, y2 = min(x2, w), min(y2, h)

    face = vetor[y1:y2, x1:x2]
    image = Image.fromarray(face).resize(size)
    return image

def flip_image(image):
    return image.transpose(Image.FLIP_LEFT_RIGHT)

def processar_diretorio(diretorio_src, diretorio_target):
    if not exists(diretorio_target):
        os.makedirs(diretorio_target)

    for filename in os.listdir(diretorio_src):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        path = join(diretorio_src, filename)
        path_tg = join(diretorio_target, filename)
        path_tg_flip = join(diretorio_target, "flip-" + filename)

        face = extrair_face(path)
        if face is not None:
            face.save(path_tg)
            flip = flip_image(face)
            flip.save(path_tg_flip)
            print(f"[OK] Face salva: {path_tg}")
        else:
            print(f"[X] Nenhum rosto detectado em: {filename}")

if __name__ == "__main__":
    nome_pessoa = input("Digite o nome da pessoa: ").strip()
    dir_fotos = join(DIR_FOTOS_BASE, nome_pessoa)
    dir_faces = join(DIR_FACES_BASE, nome_pessoa)

    if not os.path.isdir(dir_fotos):
        print(f"[ERRO] Pasta de fotos não encontrada: {dir_fotos}")
    else:
        print(f"\n[INICIANDO] Extração de faces de {nome_pessoa}...")
        processar_diretorio(dir_fotos, dir_faces)
        print(f"\n[CONCLUÍDO] Faces salvas em: {dir_faces}")
