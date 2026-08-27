import os

# ==========================================
# OCR — OCR.space
# ==========================================

OCR_SPACE_API_KEY = os.environ.get("OCR_SPACE_API_KEY", "helloworld")
OCR_SPACE_URL = "https://api.ocr.space/parse/image"

# Engine 3 = melhor acurácia, incluindo caligrafia (handwriting) e 200+ idiomas
OCR_ENGINE = 3
OCR_LANGUAGE = "por"