from app.services.cartola_service import get_mercado_status
from app.services.cartola_parciais_service import get_pontuados_por_rodada
from app.services.pontuacao_service import calcular_pontuacao_por_scout


def get_historico_atleta(
    atleta_id: int,
    rodadas: int = 5,
    rodada_atual: int | None = None,
    pontuados_por_rodada: dict[int, dict] | None = None,
) -> dict:
    if rodada_atual is None:
        mercado = get_mercado_status()
        rodada_atual = mercado.get("rodada_atual")

    if not rodada_atual:
        return {
            "atleta_id": atleta_id,
            "rodadas_analisadas": 0,
            "historico": []
        }

    rodadas = max(1, min(int(rodadas), rodada_atual))
    historico = []

    rodada_inicial = max(1, rodada_atual - rodadas + 1)

    for rodada in range(rodada_inicial, rodada_atual + 1):
        if pontuados_por_rodada is not None and rodada in pontuados_por_rodada:
            data = pontuados_por_rodada[rodada]
        else:
            data = get_pontuados_por_rodada(rodada)

        atletas = data.get("atletas", {})

        atleta = atletas.get(str(atleta_id))
        if not atleta:
            continue

        scout = atleta.get("scout", {})

        historico.append({
            "rodada": rodada,
            "pontuacao_cartola": atleta.get("pontuacao"),
            "pontuacao_calculada": calcular_pontuacao_por_scout(scout),
            "scout": scout,
            "entrou_em_campo": atleta.get("entrou_em_campo"),
            "clube_id": atleta.get("clube_id"),
            "posicao_id": atleta.get("posicao_id")
        })

    return {
        "atleta_id": atleta_id,
        "rodadas_analisadas": len(historico),
        "historico": historico
    }
