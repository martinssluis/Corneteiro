import requests
from flask import current_app

def get_pontuados():
    base = current_app.config.get("CARTOLA_API_URL")
    if not base:
        raise ValueError("CARTOLA_API_URL não configurada")

    url = f"{base}/atletas/pontuados"

    resp = requests.get(url, timeout=10)
    if resp.status_code == 204:
        return {"atletas": {}}

    resp.raise_for_status()
    return resp.json()


def get_pontuados_por_rodada(rodada: int):
    base = current_app.config.get("CARTOLA_API_URL")
    if not base:
        raise ValueError("CARTOLA_API_URL não configurada")

    url = f"{base}/atletas/pontuados/{rodada}"

    resp = requests.get(url, timeout=10)
    if resp.status_code == 204:
        return {"rodada": rodada, "atletas": {}}

    resp.raise_for_status()
    return resp.json()