import unicodedata
import requests
import requests
from flask import current_app

def get_mercado_status():
    base = current_app.config.get("CARTOLA_API_URL", "https://api.cartola.globo.com")
    url = f"{base}/mercado/status"

    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

def get_atleta_by_id(atleta_id: int):
    base = current_app.config.get("CARTOLA_API_URL")
    url = f"{base}/atletas/mercado"

    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    data = resp.json()

    for atleta in data.get("atletas", []):
        if atleta["atleta_id"] == atleta_id:
            return atleta

    return None

def _normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return texto

def buscar_atletas_por_nome(nome: str, exato: bool = False):
    base = current_app.config.get("CARTOLA_API_URL", "https://api.cartola.globo.com")
    url = f"{base}/atletas/mercado"

    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    data = resp.json()
    atletas = data.get("atletas", [])

    alvo = _normalizar_texto(nome)

    resultados = []
    for atleta in atletas:
        apelido = _normalizar_texto(atleta.get("apelido", ""))
        nome_completo = _normalizar_texto(atleta.get("nome", ""))
        slug = _normalizar_texto(atleta.get("slug", ""))

        if exato:
            if alvo in (apelido, nome_completo, slug):
                resultados.append(atleta)
        else:
            if alvo and (alvo in apelido or alvo in nome_completo or alvo in slug):
                resultados.append(atleta)

    return resultados