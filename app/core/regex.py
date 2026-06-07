import re
from datetime import date

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
# UTILIDADES
# ==========================================

def calcular_data_nascimento(idade_str):
    try:
        idade = int("".join(filter(str.isdigit, idade_str)))
        ano = date.today().year - idade
        return f"01/01/{ano}"
    except:
        return None