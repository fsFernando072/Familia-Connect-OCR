import asyncio
import logging
import cv2
import httpx
from app.core.ocr import OCR_SPACE_API_KEY, OCR_SPACE_URL, OCR_ENGINE, OCR_LANGUAGE

logger = logging.getLogger("familia-connect-ocr")


TIMEOUT_SEGUNDOS = 20.0  # imagem inteira demora um pouco mais que 1 campo
MAX_TENTATIVAS = 3
BACKOFF_BASE_SEGUNDOS = 2.0

MARCADORES_ERRO_TRANSITORIO = ("e571", "overloaded", "throttled")

_semaforo_global = asyncio.Semaphore(4)


def _e_erro_transitorio(status_code, texto_erro):
    if status_code == 503:
        return True
    texto = (texto_erro or "").lower()
    return any(marcador in texto for marcador in MARCADORES_ERRO_TRANSITORIO)


async def ler_texto_completo(client: httpx.AsyncClient, img):
    ok, buffer = cv2.imencode(".png", img)
    if not ok:
        return []

    files = {"file": ("formulario.png", buffer.tobytes(), "image/png")}
    dados = {
        "apikey": OCR_SPACE_API_KEY,
        "language": OCR_LANGUAGE,
        "OCREngine": OCR_ENGINE,
        "isOverlayRequired": True,
        "scale": True,
        "detectOrientation": False,
    }

    ultimo_erro = "erro desconhecido"

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        async with _semaforo_global:
            try:
                resposta = await client.post(OCR_SPACE_URL, files=files, data=dados, timeout=TIMEOUT_SEGUNDOS)
            except httpx.HTTPError as exc:
                ultimo_erro = f"erro de rede: {exc}"
                logger.warning("Tentativa %d/%d falhou (rede): %s", tentativa, MAX_TENTATIVAS, ultimo_erro)
                if tentativa < MAX_TENTATIVAS:
                    await asyncio.sleep(BACKOFF_BASE_SEGUNDOS * tentativa)
                    continue
                raise RuntimeError(f"Erro ao chamar OCR.space após {MAX_TENTATIVAS} tentativas: {ultimo_erro}") from exc

        if resposta.status_code != 200:
            corpo = resposta.text
            ultimo_erro = f"HTTP {resposta.status_code}: {corpo}"
            transitorio = _e_erro_transitorio(resposta.status_code, corpo)
            logger.warning("Tentativa %d/%d falhou (%s): %s", tentativa, MAX_TENTATIVAS,
                            "transitório" if transitorio else "definitivo", ultimo_erro)
            if transitorio and tentativa < MAX_TENTATIVAS:
                await asyncio.sleep(BACKOFF_BASE_SEGUNDOS * tentativa)
                continue
            raise RuntimeError(ultimo_erro)

        resultado = resposta.json()

        if "error" in resultado and "ParsedResults" not in resultado:
            erro = f"{resultado.get('error', '')} {resultado.get('details', '')}".strip()
            ultimo_erro = erro
            transitorio = _e_erro_transitorio(resposta.status_code, erro)
            logger.warning("Tentativa %d/%d falhou (%s): %s", tentativa, MAX_TENTATIVAS,
                            "transitório" if transitorio else "definitivo", erro)
            if transitorio and tentativa < MAX_TENTATIVAS:
                await asyncio.sleep(BACKOFF_BASE_SEGUNDOS * tentativa)
                continue
            raise RuntimeError(f"Erro no OCR.space: {erro}")

        if resultado.get("IsErroredOnProcessing"):
            erro = resultado.get("ErrorMessage") or ["Erro desconhecido no OCR.space"]
            if isinstance(erro, list):
                erro = "; ".join(erro)
            ultimo_erro = erro
            transitorio = _e_erro_transitorio(resposta.status_code, erro)
            logger.warning("Tentativa %d/%d falhou (%s): %s", tentativa, MAX_TENTATIVAS,
                            "transitório" if transitorio else "definitivo", erro)
            if transitorio and tentativa < MAX_TENTATIVAS:
                await asyncio.sleep(BACKOFF_BASE_SEGUNDOS * tentativa)
                continue
            raise RuntimeError(f"Erro no OCR.space: {erro}")

        parsed_results = resultado.get("ParsedResults") or []
        if not parsed_results:
            return []

        overlay = parsed_results[0].get("TextOverlay") or {}
        linhas = overlay.get("Lines") or []

        palavras = []
        for linha in linhas:
            for w in linha.get("Words", []):
                palavras.append({
                    "text": w.get("WordText", ""),
                    "left": float(w.get("Left", 0)),
                    "top": float(w.get("Top", 0)),
                    "width": float(w.get("Width", 0)),
                    "height": float(w.get("Height", 0)),
                })

        return palavras

    raise RuntimeError(f"OCR.space continuou indisponível após {MAX_TENTATIVAS} tentativas: {ultimo_erro}")
