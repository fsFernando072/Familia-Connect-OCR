import os
import tempfile
import cv2
from fastapi import FastAPI, UploadFile, File
from app.core.alinhamento import alinhar_formulario
from app.core.leitura import ler_campo
from app.core.regex import normalizar_cpf, normalizar_rg, normalizar_telefone, calcular_data_nascimento

app = FastAPI()

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
        "trabalhando": bool(dados.get("profissao")),
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