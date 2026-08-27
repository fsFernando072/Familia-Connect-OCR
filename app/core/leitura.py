import cv2
import requests
from app.core.ocr import OCR_SPACE_API_KEY, OCR_SPACE_URL, OCR_ENGINE, OCR_LANGUAGE
from app.core.preprocessamento import preparar_roi

# ==========================================
# OCR POR CAMPO — OCR.space
# ==========================================

TIMEOUT_SEGUNDOS = 30


def ler_campo(roi):
    roi = preparar_roi(roi)

    ok, buffer = cv2.imencode(".png", roi)
    if not ok:
        return ""

    files = {"file": ("roi.png", buffer.tobytes(), "image/png")}
    dados = {
        "apikey": OCR_SPACE_API_KEY,
        "language": OCR_LANGUAGE,
        "OCREngine": OCR_ENGINE,
        "isOverlayRequired": False,
        "scale": True,
        "detectOrientation": False,
    }

    try:
        resposta = requests.post(OCR_SPACE_URL, files=files, data=dados, timeout=TIMEOUT_SEGUNDOS)
        resposta.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Erro ao chamar OCR.space: {exc}") from exc

    resultado = resposta.json()

    if resultado.get("IsErroredOnProcessing"):
        erro = resultado.get("ErrorMessage") or ["Erro desconhecido no OCR.space"]
        if isinstance(erro, list):
            erro = "; ".join(erro)
        raise RuntimeError(f"Erro no OCR.space: {erro}")

    parsed_results = resultado.get("ParsedResults") or []
    if not parsed_results:
        return ""

    texto = parsed_results[0].get("ParsedText", "")
    return texto.replace("\r\n", " ").replace("\n", " ").strip()