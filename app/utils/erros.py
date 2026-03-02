from flask import jsonify

def resposta_erro(mensagem: str, status: int = 400, detalhe: str | None = None):
    payload = {"erro": mensagem}
    if detalhe:
        payload["detalhe"] = detalhe
    return jsonify(payload), status