import time
import requests
from flask import current_app

_cache_clubes = {"data": None, "expíres_at": 0}

def get_clubes(ttl_segundos: int = 3600):
    """
    Busca clubes na API do Cartola e aplica cache simples em memória.
    Rertorna um dict no formato {clube_id(int): dados_clube(dict)}
    """
    agora  = time.time()
    
    if _cache_clubes["data"] is not None and agora < _cache_clubes["expíres_at"]:
        return _cache_clubes["data"]
    
    base = current_app.config.get("CARTOLA_API_URL")
    if not base:
        raise ValueError("CARTOLA_API_URL não configurada")
    
    url = F"{base}/clubes"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    
    data = resp.json()
    
    # A API retorna chaves como string ("284"), normalizamos para int (284)
    clubes = {int(k): v for k, v in data.items()}

    _cache_clubes["data"] = clubes
    _cache_clubes["expires_at"] = agora + ttl_segundos

    return clubes

def get_clube(clube_id: int) -> dict | None:
    clubes = get_clubes()
    return clubes.get(clube_id)