# ==========================================
# MAPEAMENTO DE PALAVRAS → CAMPOS DO FORMULÁRIO
# ==========================================


def _centro(palavra):
    cx = palavra["left"] + palavra["width"] / 2
    cy = palavra["top"] + palavra["height"] / 2
    return cx, cy


def extrair_campo(palavras, x, y, w, h):
    selecionadas = []
    for palavra in palavras:
        cx, cy = _centro(palavra)
        if x <= cx <= x + w and y <= cy <= y + h:
            selecionadas.append(palavra)

    selecionadas.sort(key=lambda p: p["left"])
    return " ".join(p["text"] for p in selecionadas).strip()


def montar_campos(palavras, campos_coords):
    return {
        chave: extrair_campo(palavras, x, y, w, h)
        for chave, (x, y, w, h) in campos_coords.items()
    }
