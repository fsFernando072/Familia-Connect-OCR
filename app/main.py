import os
import logging
import tempfile
import cv2
import httpx
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.core.alinhamento import alinhar_formulario
from app.core.leitura import ler_texto_completo
from app.core.extracao import montar_campos
from app.core.preprocessamento import preparar_imagem_completa
from app.core.regex import normalizar_cpf, normalizar_rg, normalizar_telefone, calcular_data_nascimento

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("familia-connect-ocr")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# CAMPOS DO RESPONSÁVEL
# ==========================================

CAMPOS = {
    "nome": (50, 207, 840, 40),
    "rg": (90, 242, 460, 40),
    "cpf": (610, 242, 510, 40),
    "endereco": (180, 277, 740, 40),
    "numero": (960, 277, 150, 40),
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

    # ==========================================
    # MONTA O DICIONÁRIO DE COORDENADAS DE TODOS OS CAMPOS
    # ==========================================

    campos_coords = dict(CAMPOS)
    for idx, roi_nome, roi_idade in DEPENDENTES:
        campos_coords[f"dep_{idx}_nome"] = roi_nome
        campos_coords[f"dep_{idx}_idade"] = roi_idade

    # ==========================================
    # 1 ÚNICA CHAMADA AO OCR.SPACE PARA O FORMULÁRIO INTEIRO
    # ==========================================

    img_preprocessada = preparar_imagem_completa(img)

    try:
        async with httpx.AsyncClient() as client:
            palavras = await ler_texto_completo(client, img_preprocessada)
    except RuntimeError as exc:
        logger.error("Falha ao processar OCR do formulário: %s", exc)
        return {"erro": f"Falha ao processar OCR: {exc}"}

    dados = montar_campos(palavras, campos_coords)

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
        "isResponsavel": True
    }

    # =========================
    # DEPENDENTES
    # =========================

    dependentes = []

    for idx, _, _ in DEPENDENTES:
        nome = dados.get(f"dep_{idx}_nome", "")
        idade = dados.get(f"dep_{idx}_idade", "")

        if nome:
            dependentes.append({
                "nome": nome,
                "dataNascimento": calcular_data_nascimento(idade),
                "grauParentesco": "Filho/Filha",
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
                "numero": dados.get("numero"),
                "complemento": dados.get("vila"),
                "cidade": "São Paulo"
            },
            "responsavel": responsavel,
            "dependentes": dependentes
        }
    ]

    return response
