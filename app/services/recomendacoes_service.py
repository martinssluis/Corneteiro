from app.services.cartola_service import get_atletas_mercado
from app.services.cartola_parciais_service import get_pontuados, get_pontuados_por_rodada
from app.services.pontuacao_service import calcular_pontuacao_por_scout


def recomendacao_custo_beneficio(posicao_id: int | None = None, limite: int = 10) -> dict:
    """
    Recomendação v0:
    indice_custo_beneficio = media_num / preco_num
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


def recomendacao_destaques_rodada(
    rodada: int | None = None,
    posicao_id: int | None = None,
    limite: int = 10,
    ordenar_por: str = "pontuacao_cartola"
) -> dict:
    """
    Recomendação baseada nos destaques da rodada.

    ordenar_por:
    - pontuacao_cartola
    - pontuacao_calculada
    """
    if rodada is None:
        data = get_pontuados()
        rodada_referencia = "atual"
    else:
        data = get_pontuados_por_rodada(rodada)
        rodada_referencia = rodada

    atletas_dict = data.get("atletas", {})
    atletas_lista = []

    for atleta_id_str, atleta in atletas_dict.items():
        atleta_id = int(atleta_id_str)

        item = {
            "atleta_id": atleta_id,
            "apelido": atleta.get("apelido"),
            "foto": atleta.get("foto"),
            "clube_id": atleta.get("clube_id"),
            "posicao_id": atleta.get("posicao_id"),
            "entrou_em_campo": atleta.get("entrou_em_campo"),
            "pontuacao_cartola": atleta.get("pontuacao"),
            "scout": atleta.get("scout", {})
        }

        if ordenar_por == "pontuacao_calculada":
            item["pontuacao_calculada"] = calcular_pontuacao_por_scout(item["scout"])

        atletas_lista.append(item)

    if posicao_id is not None:
        atletas_lista = [a for a in atletas_lista if a.get("posicao_id") == posicao_id]

    if ordenar_por == "pontuacao_calculada":
        atletas_lista.sort(
            key=lambda x: x.get("pontuacao_calculada", 0),
            reverse=True
        )
    else:
        atletas_lista.sort(
            key=lambda x: x.get("pontuacao_cartola", 0) or 0,
            reverse=True
        )

    limite = max(1, min(int(limite), 50))
    atletas_lista = atletas_lista[:limite]

    return {
        "criterio": "destaques_rodada",
        "rodada": rodada_referencia,
        "posicao_id": posicao_id,
        "ordenar_por": ordenar_por,
        "limite": limite,
        "quantidade": len(atletas_lista),
        "recomendacoes": atletas_lista
    }