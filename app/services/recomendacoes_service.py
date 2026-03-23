from app.services.cartola_parciais_service import get_pontuados, get_pontuados_por_rodada
from app.services.cartola_service import get_atletas_mercado, get_mercado_status, get_partidas_por_rodada
from app.services.clubes_service import get_clubes
from app.services.historico_service import get_historico_atleta
from app.services.pontuacao_service import calcular_pontuacao_por_scout
from app.utils.posicoes import get_posicao


PESO_FASE_RECENTE = 0.5
PESO_CONSISTENCIA = 0.3
PESO_CUSTO_BENEFICIO = 0.2

PESO_SCORE_INDIVIDUAL = 0.6
PESO_FORCA_CONFRONTO = 0.4


def _clamp(valor: float, minimo: float, maximo: float) -> float:
    return max(minimo, min(valor, maximo))


def _arredondar(valor: float) -> float:
    return round(valor, 2)


def _safe_float(valor) -> float | None:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _safe_int(valor) -> int | None:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _normalizar_0_10(valor: float, minimo: float, maximo: float) -> float:
    if maximo == minimo:
        return 10.0

    nota = 10 * (valor - minimo) / (maximo - minimo)
    return _arredondar(_clamp(nota, 0.0, 10.0))


def _normalizar_opcional_0_10(valor: float | None, minimo: float, maximo: float) -> float:
    if valor is None:
        return 0.0
    return _normalizar_0_10(valor, minimo, maximo)


def _calcular_media(valores: list[float]) -> float:
    if not valores:
        return 0.0
    return sum(valores) / len(valores)


def _calcular_oscilacao(valores: list[float]) -> float:
    if len(valores) < 2:
        return 0.0

    media = _calcular_media(valores)
    desvios = [abs(valor - media) for valor in valores]
    return _calcular_media(desvios)


def _calcular_penalizacao_amostra(partidas_validas: int, rodadas_referencia: int) -> float:
    if rodadas_referencia <= 0:
        return 0.5

    fator_amostra = _clamp(partidas_validas / rodadas_referencia, 0.0, 1.0)
    return _arredondar(0.5 * (1 - fator_amostra))


def _extrair_pontuacoes_validas(historico: list[dict]) -> list[float]:
    pontuacoes = []

    for partida in historico:
        if partida.get("entrou_em_campo") is not True:
            continue

        pontuacao = partida.get("pontuacao_calculada")
        if pontuacao is None:
            continue

        pontuacoes.append(float(pontuacao))

    return pontuacoes


def _precarregar_cache_historico_misto(rodadas: int) -> tuple[int | None, int, dict[int, dict]]:
    mercado = get_mercado_status()
    rodada_atual = mercado.get("rodada_atual")

    if not rodada_atual:
        return None, rodadas, {}

    rodadas_consideradas = max(1, min(int(rodadas), rodada_atual))
    rodada_inicial = max(1, rodada_atual - rodadas_consideradas + 1)

    pontuados_por_rodada = {}
    for rodada in range(rodada_inicial, rodada_atual + 1):
        pontuados_por_rodada[rodada] = get_pontuados_por_rodada(rodada)

    return rodada_atual, rodadas_consideradas, pontuados_por_rodada


def _carregar_clubes_seguro() -> dict:
    try:
        return get_clubes()
    except Exception:
        return {}


def _enriquecer_identidade(item: dict, clubes: dict) -> dict:
    clube_id = _safe_int(item.get("clube_id"))
    posicao_id = _safe_int(item.get("posicao_id"))

    clube = clubes.get(clube_id, {}) if clube_id is not None else {}
    posicao = get_posicao(posicao_id) if posicao_id is not None else None

    return {
        **item,
        "clube_nome": clube.get("nome"),
        "clube_sigla": clube.get("abreviacao"),
        "posicao_nome": posicao.get("nome") if posicao else None,
    }


def _montar_candidato_misto(
    atleta: dict,
    rodadas: int,
    rodada_atual: int | None = None,
    pontuados_por_rodada: dict[int, dict] | None = None,
) -> dict | None:
    preco = atleta.get("preco_num")
    media = atleta.get("media_num")

    try:
        preco = float(preco)
        media = float(media)
    except (TypeError, ValueError):
        return None

    if preco <= 0:
        return None

    historico_atleta = get_historico_atleta(
        atleta_id=atleta.get("atleta_id"),
        rodadas=rodadas,
        rodada_atual=rodada_atual,
        pontuados_por_rodada=pontuados_por_rodada,
    )
    historico = historico_atleta.get("historico", [])
    pontuacoes_validas = _extrair_pontuacoes_validas(historico)

    if not pontuacoes_validas:
        return None

    media_recente = _calcular_media(pontuacoes_validas)
    oscilacao = _calcular_oscilacao(pontuacoes_validas)
    indice_custo_beneficio = media / preco

    return {
        "atleta_id": atleta.get("atleta_id"),
        "apelido": atleta.get("apelido"),
        "clube_id": atleta.get("clube_id"),
        "posicao_id": atleta.get("posicao_id"),
        "preco_num": preco,
        "media_num": media,
        "partidas_validas": len(pontuacoes_validas),
        "ultimas_pontuacoes": [_arredondar(valor) for valor in pontuacoes_validas],
        "media_recente": media_recente,
        "oscilacao_recente": oscilacao,
        "indice_custo_beneficio": indice_custo_beneficio,
    }


def _aplicar_scores_mistos(candidatos: list[dict], rodadas: int, clubes: dict) -> list[dict]:
    if not candidatos:
        return []

    medias_recentes = [item["media_recente"] for item in candidatos]
    oscilacoes = [item["oscilacao_recente"] for item in candidatos]
    custos_beneficios = [item["indice_custo_beneficio"] for item in candidatos]

    media_min = min(medias_recentes)
    media_max = max(medias_recentes)
    oscilacao_min = min(oscilacoes)
    oscilacao_max = max(oscilacoes)
    cb_min = min(custos_beneficios)
    cb_max = max(custos_beneficios)

    recomendacoes = []
    for candidato in candidatos:
        score_fase_recente = _normalizar_0_10(
            candidato["media_recente"],
            media_min,
            media_max,
        )
        score_consistencia = _normalizar_0_10(
            oscilacao_max - candidato["oscilacao_recente"],
            oscilacao_max - oscilacao_max,
            oscilacao_max - oscilacao_min,
        )
        score_custo_beneficio = _normalizar_0_10(
            candidato["indice_custo_beneficio"],
            cb_min,
            cb_max,
        )

        score_base = (
            PESO_FASE_RECENTE * score_fase_recente
            + PESO_CONSISTENCIA * score_consistencia
            + PESO_CUSTO_BENEFICIO * score_custo_beneficio
        )
        penalizacao_amostra = _calcular_penalizacao_amostra(
            candidato["partidas_validas"],
            rodadas,
        )
        score_recomendacao = score_base * (1 - penalizacao_amostra)

        recomendacao = {
            "atleta_id": candidato["atleta_id"],
            "apelido": candidato["apelido"],
            "clube_id": candidato["clube_id"],
            "posicao_id": candidato["posicao_id"],
            "preco_num": _arredondar(candidato["preco_num"]),
            "media_num": _arredondar(candidato["media_num"]),
            "partidas_validas": candidato["partidas_validas"],
            "ultimas_pontuacoes": candidato["ultimas_pontuacoes"],
            "score_fase_recente": score_fase_recente,
            "score_consistencia": score_consistencia,
            "score_custo_beneficio": score_custo_beneficio,
            "penalizacao_amostra": penalizacao_amostra,
            "score_recomendacao": _arredondar(score_recomendacao),
        }
        recomendacoes.append(_enriquecer_identidade(recomendacao, clubes))

    recomendacoes.sort(key=lambda item: item["score_recomendacao"], reverse=True)
    return recomendacoes


def _obter_adversario_id(partidas, clube_id: int) -> int | None:
    if not partidas:
        return None

    partidas_iter = partidas.values() if isinstance(partidas, dict) else partidas

    for partida in partidas_iter:
        casa_id = _safe_int(partida.get("clube_casa_id"))
        visitante_id = _safe_int(partida.get("clube_visitante_id"))

        if casa_id == clube_id:
            return visitante_id
        if visitante_id == clube_id:
            return casa_id

    return None


def _calcular_media_cedida_posicao(
    adversario_id: int,
    posicao_id: int,
    rodada_atual: int | None,
    rodadas: int,
    pontuados_por_rodada: dict[int, dict],
) -> float | None:
    if not rodada_atual or rodadas <= 0:
        return None

    rodada_inicial = max(1, rodada_atual - rodadas + 1)
    pontuacoes = []

    for rodada in range(rodada_inicial, rodada_atual + 1):
        data = pontuados_por_rodada.get(rodada, {})
        atletas = data.get("atletas", {})

        for atleta in atletas.values():
            if _safe_int(atleta.get("clube_id")) != adversario_id:
                continue
            if _safe_int(atleta.get("posicao_id")) != posicao_id:
                continue
            if atleta.get("entrou_em_campo") is not True:
                continue

            pontuacao = _safe_float(atleta.get("pontuacao"))
            if pontuacao is None:
                continue

            pontuacoes.append(pontuacao)

    if not pontuacoes:
        return None

    return _calcular_media(pontuacoes)


def _obter_partidas_rodada(mercado_data: dict, rodada_atual: int | None = None) -> dict:
    partidas = mercado_data.get("partidas")
    if partidas:
        return partidas

    try:
        status = get_mercado_status()
        partidas_status = status.get("partidas", {})
        if partidas_status:
            return partidas_status
        if rodada_atual is None:
            rodada_atual = _safe_int(status.get("rodada_atual"))
    except Exception:
        pass

    if rodada_atual is None:
        return {}

    try:
        partidas_rodada = get_partidas_por_rodada(rodada_atual)
    except Exception:
        return {}

    if isinstance(partidas_rodada, dict):
        if "partidas" in partidas_rodada:
            return partidas_rodada.get("partidas", {}) or {}
        return partidas_rodada

    return partidas_rodada or {}


def recomendacao_por_criterio(
    criterio: str,
    posicao_id: int | None = None,
    limite: int = 10,
    rodadas: int = 5,
    rodada: int | None = None,
    ordenar_por: str = "pontuacao_cartola",
    janela_curta: int = 5,
    janela_longa: int = 10,
    peso_curta: float = 0.7,
    peso_longa: float = 0.3,
) -> dict:
    criterio_normalizado = (criterio or "").strip().lower()

    if criterio_normalizado == "custo_beneficio":
        return recomendacao_custo_beneficio(posicao_id=posicao_id, limite=limite)

    if criterio_normalizado == "destaques_rodada":
        return recomendacao_destaques_rodada(
            rodada=rodada,
            posicao_id=posicao_id,
            limite=limite,
            ordenar_por=ordenar_por,
        )

    if criterio_normalizado == "misto":
        return recomendacao_mista(posicao_id=posicao_id, limite=limite, rodadas=rodadas)

    if criterio_normalizado == "confronto_hibrido":
        return recomendacao_confronto_hibrido(
            posicao_id=posicao_id,
            limite=limite,
            janela_curta=janela_curta,
            janela_longa=janela_longa,
            peso_curta=peso_curta,
            peso_longa=peso_longa,
        )

    raise ValueError("criterio_invalido")


def recomendacao_custo_beneficio(posicao_id: int | None = None, limite: int = 10) -> dict:
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

    clubes = _carregar_clubes_seguro()
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

        item = {
            "atleta_id": a.get("atleta_id"),
            "apelido": a.get("apelido"),
            "clube_id": a.get("clube_id"),
            "posicao_id": a.get("posicao_id"),
            "preco_num": preco,
            "media_num": media,
            "indice_custo_beneficio": round(indice, 4),
        }
        recomendacoes.append(_enriquecer_identidade(item, clubes))

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
    if rodada is None:
        data = get_pontuados()
        rodada_referencia = "atual"
    else:
        data = get_pontuados_por_rodada(rodada)
        rodada_referencia = rodada

    atletas_dict = data.get("atletas", {})
    atletas_lista = []
    clubes = _carregar_clubes_seguro()

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

        atletas_lista.append(_enriquecer_identidade(item, clubes))

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


def recomendacao_mista(posicao_id: int | None = None, limite: int = 10, rodadas: int = 5) -> dict:
    data = get_atletas_mercado()
    atletas = data.get("atletas", [])

    if posicao_id is not None:
        atletas = [atleta for atleta in atletas if atleta.get("posicao_id") == posicao_id]

    rodada_atual, rodadas_consideradas, pontuados_por_rodada = _precarregar_cache_historico_misto(rodadas)

    candidatos = []
    for atleta in atletas:
        candidato = _montar_candidato_misto(
            atleta,
            rodadas_consideradas,
            rodada_atual=rodada_atual,
            pontuados_por_rodada=pontuados_por_rodada,
        )
        if candidato is None:
            continue
        candidatos.append(candidato)

    clubes = _carregar_clubes_seguro()
    recomendacoes = _aplicar_scores_mistos(candidatos, rodadas_consideradas, clubes)

    limite = max(1, min(int(limite), 50))
    recomendacoes = recomendacoes[:limite]

    return {
        "criterio": "misto",
        "perfil": "equilibrado",
        "rodadas": rodadas_consideradas,
        "posicao_id": posicao_id,
        "limite": limite,
        "quantidade": len(recomendacoes),
        "recomendacoes": recomendacoes,
    }


def recomendacao_confronto_hibrido(
    posicao_id: int | None = None,
    limite: int = 10,
    janela_curta: int = 5,
    janela_longa: int = 10,
    peso_curta: float = 0.7,
    peso_longa: float = 0.3,
) -> dict:
    data = get_atletas_mercado()
    atletas = data.get("atletas", [])

    if posicao_id is not None:
        atletas = [atleta for atleta in atletas if atleta.get("posicao_id") == posicao_id]

    rodada_atual, rodadas_longa_consideradas, pontuados_por_rodada = _precarregar_cache_historico_misto(janela_longa)
    partidas = _obter_partidas_rodada(data, rodada_atual=rodada_atual)
    rodadas_curta_consideradas = min(janela_curta, rodada_atual or janela_curta)

    candidatos = []
    for atleta in atletas:
        atleta_id = atleta.get("atleta_id")
        atleta_clube_id = _safe_int(atleta.get("clube_id"))
        atleta_posicao_id = _safe_int(atleta.get("posicao_id"))
        preco_num = _safe_float(atleta.get("preco_num"))
        media_num = _safe_float(atleta.get("media_num"))

        if not atleta_id or atleta_clube_id is None or atleta_posicao_id is None:
            continue
        if preco_num is None or preco_num <= 0 or media_num is None:
            continue

        adversario_id = _obter_adversario_id(partidas, atleta_clube_id)
        media_cedida_curta = None
        media_cedida_longa = None
        if adversario_id is not None:
            media_cedida_curta = _calcular_media_cedida_posicao(
                adversario_id=adversario_id,
                posicao_id=atleta_posicao_id,
                rodada_atual=rodada_atual,
                rodadas=rodadas_curta_consideradas,
                pontuados_por_rodada=pontuados_por_rodada,
            )
            media_cedida_longa = _calcular_media_cedida_posicao(
                adversario_id=adversario_id,
                posicao_id=atleta_posicao_id,
                rodada_atual=rodada_atual,
                rodadas=rodadas_longa_consideradas,
                pontuados_por_rodada=pontuados_por_rodada,
            )

        candidatos.append(
            {
                "atleta_id": atleta_id,
                "apelido": atleta.get("apelido"),
                "clube_id": atleta_clube_id,
                "posicao_id": atleta_posicao_id,
                "preco_num": preco_num,
                "media_num": media_num,
                "adversario_id": adversario_id,
                "media_cedida_curta": media_cedida_curta,
                "media_cedida_longa": media_cedida_longa,
            }
        )

    if not candidatos:
        return {
            "criterio": "confronto_hibrido",
            "janela_curta": rodadas_curta_consideradas,
            "janela_longa": rodadas_longa_consideradas,
            "peso_curta": _arredondar(peso_curta),
            "peso_longa": _arredondar(peso_longa),
            "posicao_id": posicao_id,
            "limite": max(1, min(int(limite), 50)),
            "quantidade": 0,
            "recomendacoes": [],
        }

    clubes = _carregar_clubes_seguro()

    individuais = [item["media_num"] for item in candidatos]
    curto_validos = [item["media_cedida_curta"] for item in candidatos if item["media_cedida_curta"] is not None]
    longo_validos = [item["media_cedida_longa"] for item in candidatos if item["media_cedida_longa"] is not None]

    ind_min, ind_max = min(individuais), max(individuais)
    curto_min, curto_max = (min(curto_validos), max(curto_validos)) if curto_validos else (0.0, 0.0)
    longo_min, longo_max = (min(longo_validos), max(longo_validos)) if longo_validos else (0.0, 0.0)

    recomendacoes = []
    for candidato in candidatos:
        score_individual = _normalizar_0_10(candidato["media_num"], ind_min, ind_max)
        score_confronto_curto = _normalizar_opcional_0_10(candidato["media_cedida_curta"], curto_min, curto_max)
        score_confronto_longo = _normalizar_opcional_0_10(candidato["media_cedida_longa"], longo_min, longo_max)

        forca_confronto = (peso_curta * score_confronto_curto) + (peso_longa * score_confronto_longo)
        score_recomendacao = (PESO_SCORE_INDIVIDUAL * score_individual) + (PESO_FORCA_CONFRONTO * forca_confronto)

        base_item = {
            "atleta_id": candidato["atleta_id"],
            "apelido": candidato["apelido"],
            "clube_id": candidato["clube_id"],
            "posicao_id": candidato["posicao_id"],
            "preco_num": _arredondar(candidato["preco_num"]),
            "media_num": _arredondar(candidato["media_num"]),
            "adversario_id": candidato["adversario_id"],
            "historico_time_curto": {
                "rodadas": rodadas_curta_consideradas,
                "media_cedida_posicao": _arredondar(candidato["media_cedida_curta"]) if candidato["media_cedida_curta"] is not None else None,
            },
            "historico_time_longo": {
                "rodadas": rodadas_longa_consideradas,
                "media_cedida_posicao": _arredondar(candidato["media_cedida_longa"]) if candidato["media_cedida_longa"] is not None else None,
            },
            "score_individual": score_individual,
            "score_confronto_curto": score_confronto_curto,
            "score_confronto_longo": score_confronto_longo,
            "forca_confronto": _arredondar(forca_confronto),
            "score_recomendacao": _arredondar(score_recomendacao),
        }

        clube_adversario = clubes.get(candidato["adversario_id"], {}) if candidato["adversario_id"] is not None else {}
        item = {
            **_enriquecer_identidade(base_item, clubes),
            "adversario_nome": clube_adversario.get("nome"),
            "adversario_sigla": clube_adversario.get("abreviacao"),
        }
        recomendacoes.append(item)

    recomendacoes.sort(key=lambda item: item["score_recomendacao"], reverse=True)

    limite = max(1, min(int(limite), 50))
    recomendacoes = recomendacoes[:limite]

    return {
        "criterio": "confronto_hibrido",
        "janela_curta": rodadas_curta_consideradas,
        "janela_longa": rodadas_longa_consideradas,
        "peso_curta": _arredondar(peso_curta),
        "peso_longa": _arredondar(peso_longa),
        "posicao_id": posicao_id,
        "limite": limite,
        "quantidade": len(recomendacoes),
        "recomendacoes": recomendacoes,
    }
