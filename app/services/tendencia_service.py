from app.services.historico_service import get_historico_atleta


LIMIAR_TENDENCIA = 0.5


def _arredondar(valor: float) -> float:
    return round(valor, 2)


def _calcular_media(valores: list[float]) -> float:
    if not valores:
        return 0.0
    return sum(valores) / len(valores)


def _classificar_tendencia(variacao: float) -> str:
    if variacao > LIMIAR_TENDENCIA:
        return "alta"
    if variacao < -LIMIAR_TENDENCIA:
        return "queda"
    return "estavel"


def get_tendencia_atleta(atleta_id: int, rodadas: int = 6) -> dict:
    historico_atleta = get_historico_atleta(atleta_id=atleta_id, rodadas=rodadas)
    historico = historico_atleta.get("historico", [])

    partidas_validas = [
        partida["pontuacao_calculada"]
        for partida in historico
        if partida.get("entrou_em_campo") is True
        and partida.get("pontuacao_calculada") is not None
    ]

    total_partidas_validas = len(partidas_validas)
    resposta_base = {
        "atleta_id": atleta_id,
        "rodadas_consideradas": rodadas,
        "partidas_validas": total_partidas_validas,
        "ultimas_pontuacoes": partidas_validas,
    }

    if total_partidas_validas < 2:
        return {
            **resposta_base,
            "media_bloco_antigo": None,
            "media_bloco_recente": None,
            "variacao": None,
            "tendencia": "insuficiente",
        }

    tamanho_bloco_antigo = total_partidas_validas // 2
    bloco_antigo = partidas_validas[:tamanho_bloco_antigo]
    bloco_recente = partidas_validas[tamanho_bloco_antigo:]

    media_bloco_antigo = _calcular_media(bloco_antigo)
    media_bloco_recente = _calcular_media(bloco_recente)
    variacao = media_bloco_recente - media_bloco_antigo

    return {
        **resposta_base,
        "media_bloco_antigo": _arredondar(media_bloco_antigo),
        "media_bloco_recente": _arredondar(media_bloco_recente),
        "variacao": _arredondar(variacao),
        "tendencia": _classificar_tendencia(variacao),
    }
