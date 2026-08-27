import os
import logging

logger = logging.getLogger("familia-connect-ocr")

# ==========================================
# OCR — OCR.space
# ==========================================

OCR_SPACE_API_KEY = os.environ.get("OCR_SPACE_API_KEY", "helloworld")
OCR_SPACE_URL = "https://api.ocr.space/parse/image"

OCR_ENGINE = 3
OCR_LANGUAGE = "por"

if OCR_SPACE_API_KEY == "helloworld":
    logger.warning(
        "OCR_SPACE_API_KEY não configurada — usando a chave pública "
        "'helloworld', compartilhada e sujeita a rate limit/erros. "
        "Configure sua própria chave (https://ocr.space/ocrapi) via "
        "variável de ambiente OCR_SPACE_API_KEY."
    )