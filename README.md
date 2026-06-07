# 🔍 Família Connect — OCR

> Microsserviço de leitura automática de formulários físicos de cadastro de famílias, utilizando PaddleOCR + OpenCV e exposto via FastAPI.

---

## 📋 Sobre o Projeto

Este serviço recebe a foto de um formulário preenchido à mão e retorna um JSON estruturado com os dados do responsável e dos dependentes da família. O pipeline realiza alinhamento da imagem por homografia (ORB), recorte preciso de cada campo, pré-processamento de contraste (CLAHE) e leitura via OCR com normalização de CPF, RG e telefone por regex.

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Versão | Descrição |
|---|---|---|
| Python | 3.10+ | Linguagem principal |
| FastAPI | 0.110.0 | Framework da API REST |
| Uvicorn | 0.29.0 | Servidor ASGI |
| PaddleOCR | 2.7.0.3 | Motor de OCR |
| PaddlePaddle | 2.6.2 | Backend do PaddleOCR |
| OpenCV (headless) | 4.9.0.80 | Visão computacional (alinhamento e pré-processamento) |
| NumPy | 1.26.4 | Operações matriciais |
| Docker | — | Containerização |

---

## 📁 Estrutura do Projeto

```
ocr-cesta-basica/
│
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ocr.py
│   │   ├── alinhamento.py
│   │   ├── preprocessamento.py
│   │   ├── leitura.py
│   │   └── regex.py
│   ├── templates/
│   │   └── template-vazio.png
│   └── __init__.py
│
├── Dockerfile
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🔄 Pipeline de Processamento

```
Imagem recebida (POST)
        │
        ▼
alinhar_formulario(img)      ← ORB detecta keypoints, BFMatcher casa com o template,
        │                       findHomography + warpPerspective corrige a perspectiva
        ▼
  Para cada campo em CAMPOS:
        │
        ├── roi = img[y:y+h, x:x+w]
        │
        ├── preparar_roi(roi)     ← converte para cinza, resize 1.3x, aplica CLAHE
        │
        └── ler_campo(roi)        ← chama ocr.ocr(), filtra confiança ≥ 0.45, junta textos
                │
                ▼
        normalizar_cpf / normalizar_rg / normalizar_telefone
                │
                ▼
        calcular_data_nascimento(idade_str)
                │
                ▼
        JSON estruturado (familiaEndereco + responsavel + dependentes[])
```

---

## 📐 Campos Lidos do Formulário

### Responsável

| Campo | Coordenadas (x, y, w, h) |
|---|---|
| nome | (50, 207, 840, 40) |
| rg | (90, 242, 460, 40) |
| cpf | (610, 242, 510, 40) |
| endereco | (180, 277, 740, 40) |
| vila | (100, 310, 440, 40) |
| bairro | (640, 310, 470, 40) |
| telefone | (120, 345, 480, 40) |
| profissao | (185, 378, 500, 40) |
| idade | (985, 200, 160, 40) |

### Dependentes (6 linhas)

Cada dependente tem dois campos lidos: **nome** e **idade**, com coordenadas mapeadas linha a linha (linhas 482 a 652, espaçadas em 34px).

---

## 📤 Exemplo de Resposta

```json
[
  {
    "familiaEndereco": {
      "cep": "00000-000",
      "bairro": "Vila Madalena",
      "logradouro": "Rua Aspicuelta",
      "complemento": "Casa 2",
      "cidade": "São Paulo"
    },
    "responsavel": {
      "nome": "Maria Souza",
      "rg": "12.345.678-9",
      "cpf": "123.456.789-00",
      "dataNascimento": "01/01/1985",
      "telefone": "(11) 91234-5678",
      "profissao": "Auxiliar administrativo",
      "trabalhando": true,
      "responsavel": true
    },
    "dependentes": [
      {
        "nome": "Lucas Souza",
        "dataNascimento": "01/01/2015",
        "grauParentesco": "Filho",
        "responsavel": false
      }
    ]
  }
]
```

---

## ⚙️ Pré-requisitos

- [Python 3.10+](https://www.python.org/)
- [Docker](https://www.docker.com/) *(recomendado para evitar conflitos de dependências do PaddlePaddle)*

---

## 🚀 Como Iniciar

### Opção A — Docker (recomendado)

```bash
# Build da imagem
docker build -t familia-connect-ocr .

# Subir o container
docker run -p 8080:8080 familia-connect-ocr
```

### Opção B — Ambiente local

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar o servidor
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

> A API estará disponível em: **http://localhost:8080**

---

## 📖 Documentação Interativa

Com o serviço rodando, acesse o Swagger:

```
http://localhost:8080/docs
```

---

## 📬 Endpoint

### `POST /ocr/cesta-basica`

Recebe a foto do formulário e retorna os dados extraídos em JSON.

**Request:** `multipart/form-data`

| Campo | Tipo | Descrição |
|---|---|---|
| `file` | `UploadFile` | Imagem do formulário (JPG, PNG) |

**Exemplo com curl:**

```bash
curl -X POST http://localhost:8080/ocr/cesta-basica \
  -F "file=@foto_formulario.jpg"
```

---

## 📄 Licença

Este projeto está sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.