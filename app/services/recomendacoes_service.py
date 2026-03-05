from app.services.cartola_service import get_atletas_mercado

def recomendacao_custo_beneficio(posicao_id: int | None = None, limite: int = 10) -> dict:
    """
    Recomendação v0:
    indice_custo_beneficio = media_num / preco_num

    Retorno leve (lista/ranking). Sem enriquecer clube/posição aqui por performance.
    (Se precisar detalhes, o front chama /atletas/<atleta_id>).
    """
    data = get_atletas_mercado()
    atletas = data.get("atletas", [])

    if not atletas:
        return {
            "criterio": "custo_beneficio",
            "posicao_id": posicao_id,
            "limite": limite,
            "quantidade": 0,
            "recomendacoes": []
        }

    if posicao_id is not None:
        atletas = [a for a in atletas if a.get("posicao_id") == posicao_id]

    recomendacoes = []
    for a in atletas:
        preco = a.get("preco_num")
        media = a.get("media_num")

        if preco is None or media is None:
            continue

        try:
            preco = float(preco)
            media = float(media)
        except (TypeError, ValueError):
            continue

        if preco <= 0:
            continue

        indice = media / preco

        recomendacoes.append({
            "atleta_id": a.get("atleta_id"),
            "apelido": a.get("apelido"),
            "clube_id": a.get("clube_id"),
            "posicao_id": a.get("posicao_id"),
            "preco_num": preco,
            "media_num": media,
            "indice_custo_beneficio": round(indice, 4),
        })

    recomendacoes.sort(key=lambda x: x["indice_custo_beneficio"], reverse=True)

    limite = max(1, min(int(limite), 50))
    recomendacoes = recomendacoes[:limite]

    return {
        "criterio": "custo_beneficio",
        "posicao_id": posicao_id,
        "limite": limite,
        "quantidade": len(recomendacoes),
        "recomendacoes": recomendacoes
    }