import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File
from paddleocr import PaddleOCR
import tempfile
import os
from datetime import date
import re

app = FastAPI()

# ==========================================
# OCR
# ==========================================

ocr = PaddleOCR(
    lang="pt",
    use_angle_cls=True,
    det_db_box_thresh=0.3,
    det_db_unclip_ratio=1.6,
    rec_algorithm="CRNN",
    use_space_char=True,
    show_log=False
)

# ==========================================
# TEMPLATE (CARREGADO UMA VEZ)
# ==========================================

TEMPLATE_PATH = "template-vazio.png"
template = cv2.imread(TEMPLATE_PATH)

if template is None:
    raise RuntimeError("Template não encontrado no container")

# ==========================================
# CAMPOS DO RESPONSÁVEL
# ==========================================

CAMPOS = {
    "nome": (50, 207, 840, 40),
    "rg": (90, 242, 460, 40),
    "cpf": (610, 242, 510, 40),
    "endereco": (180, 277, 740, 40),
    "vila": (100, 310, 440, 40),
    "bairro": (640, 310, 470, 40),
    "telefone": (120, 345, 480, 40),
    "profissao": (185, 378, 500, 40),
    "idade": (985, 200, 160, 40),
}

# ==========================================
# DEPENDENTES (NOME, IDADE)
# ==========================================

DEPENDENTES = [
    ("01", (190, 482, 700, 40), (985, 482, 160, 40)),
    ("02", (190, 516, 700, 40), (985, 516, 160, 40)),
    ("03", (190, 550, 700, 40), (985, 550, 160, 40)),
    ("04", (190, 584, 700, 40), (985, 584, 160, 40)),
    ("05", (190, 618, 700, 40), (985, 618, 160, 40)),
    ("06", (190, 652, 700, 40), (985, 652, 160, 40)),
]

# ==========================================
# ALINHAMENTO ORB
# ==========================================

def alinhar_formulario(img):
    g1 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create(4000)
    kp1, d1 = orb.detectAndCompute(g1, None)
    kp2, d2 = orb.detectAndCompute(g2, None)

    if d1 is None or d2 is None:
        return img

    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = sorted(bf.match(d1, d2), key=lambda x: x.distance)[:200]

    pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])

    H, _ = cv2.findHomography(pts1, pts2, cv2.RANSAC)

    if H is None:
        return img

    h, w = template.shape[:2]
    return cv2.warpPerspective(img, H, (w, h))

# ==========================================
# PREPROCESSAMENTO LEVE
# ==========================================

def preparar_roi(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(
        gray, None,
        fx=1.3, fy=1.3,
        interpolation=cv2.INTER_CUBIC
    )

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

# ==========================================
# OCR POR CAMPO
# ==========================================

def ler_campo(roi):
    roi = preparar_roi(roi)
    resultado = ocr.ocr(roi, cls=False)

    if not resultado or not resultado[0]:
        return ""

    textos = []
    for linha in resultado[0]:
        texto, conf = linha[1]
        if conf >= 0.45:
            textos.append(texto.strip())

    return " ".join(textos)

# ==========================================
# UTILIDADES
# ==========================================

def calcular_data_nascimento(idade_str):
    try:
        idade = int("".join(filter(str.isdigit, idade_str)))
        ano = date.today().year - idade
        return f"01/01/{ano}"
    except:
        return None
    
# ==========================================
# NORMALIZAÇÃO COM REGEX
# ==========================================

def somente_digitos(texto: str) -> str:
    if not texto:
        return ""
    return re.sub(r"\D", "", texto)


def normalizar_cpf(cpf: str) -> str:
    digitos = somente_digitos(cpf)
    digitos = digitos.zfill(11)

    return f"{digitos[0:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:11]}"


def normalizar_rg(rg: str) -> str:
    digitos = somente_digitos(rg)
    digitos = digitos.zfill(9)

    return f"{digitos[0:2]}.{digitos[2:5]}.{digitos[5:8]}-{digitos[8]}"


def normalizar_telefone(telefone: str) -> str:
    digitos = somente_digitos(telefone)

    if len(digitos) <= 10:
        digitos = digitos.zfill(10)
        return f"({digitos[0:2]}) {digitos[2:6]}-{digitos[6:10]}"
    else:
        digitos = digitos.zfill(11)
        return f"({digitos[0:2]}) {digitos[2:7]}-{digitos[7:11]}"

# ==========================================
# ENDPOINT
# ==========================================

@app.post("/ocr/cesta-basica")
async def ocr_cesta(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    img = cv2.imread(tmp_path)
    os.unlink(tmp_path)

    if img is None:
        return {"erro": "Imagem inválida"}

    img = alinhar_formulario(img)

    dados = {}

    for campo, (x, y, w, h) in CAMPOS.items():
        roi = img[y:y+h, x:x+w]
        dados[campo] = ler_campo(roi)

    # =========================
    # RESPONSÁVEL
    # =========================

    responsavel = {
        "nome": dados.get("nome"),
        "rg": normalizar_rg(dados.get("rg")),
        "cpf": normalizar_cpf(dados.get("cpf")),
        "dataNascimento": calcular_data_nascimento(dados.get("idade", "")),
        "telefone": normalizar_telefone(dados.get("telefone")),
        "profissao": dados.get("profissao"),
        "trabalhando": False,
        "responsavel": True
    }

    # =========================
    # DEPENDENTES
    # =========================

    dependentes = []

    for _, roi_nome, roi_idade in DEPENDENTES:
        nome = ler_campo(img[roi_nome[1]:roi_nome[1]+roi_nome[3],
                              roi_nome[0]:roi_nome[0]+roi_nome[2]])
        idade = ler_campo(img[roi_idade[1]:roi_idade[1]+roi_idade[3],
                               roi_idade[0]:roi_idade[0]+roi_idade[2]])

        if nome:
            dependentes.append({
                "nome": nome,
                "dataNascimento": calcular_data_nascimento(idade),
                "grauParentesco": "Filho",
                "responsavel": False
            })

    # =========================
    # JSON FINAL
    # =========================

    response = [
        {
            "familiaEndereco": {
                "cep": "00000-000",
                "bairro": dados.get("bairro"),
                "logradouro": dados.get("endereco"),
                "complemento": dados.get("vila"),
                "cidade": "São Paulo"
            },
            "responsavel": responsavel,
            "dependentes": dependentes
        }
    ]

    return response