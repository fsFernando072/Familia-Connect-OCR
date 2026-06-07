from app.core.ocr import ocr
from app.core.preprocessamento import preparar_roi

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