from flask import Blueprint, jsonify, request

from app.services.recomendacoes_service import (
    recomendacao_custo_beneficio,
    recomendacao_destaques_rodada,
    recomendacao_por_criterio,
)
from app.utils.erros import resposta_erro


recomendacoes_bp = Blueprint("recomendacoes", __name__)

CRITERIOS_SUPORTADOS = {"custo_beneficio", "destaques_rodada", "misto"}
ORDENACOES_DESTAQUES = {"pontuacao_cartola", "pontuacao_calculada"}


@recomendacoes_bp.route("", methods=["GET"])
@recomendacoes_bp.route("/", methods=["GET"])
def listar_recomendacoes():
    criterio = request.args.get("criterio", type=str)
    posicao_id = request.args.get("posicao_id", type=int)
    limite = request.args.get("limite", default=10, type=int)
    rodadas = request.args.get("rodadas", default=5, type=int)
    rodada = request.args.get("rodada", type=int)
    ordenar_por = request.args.get("ordenar_por", default="pontuacao_cartola", type=str)

    if not criterio:
        return resposta_erro(
            "Parâmetro 'criterio' é obrigatório. Use 'custo_beneficio', 'destaques_rodada' ou 'misto'.",
            status=400,
        )

    if criterio not in CRITERIOS_SUPORTADOS:
        return resposta_erro(
            "Parâmetro 'criterio' inválido. Use 'custo_beneficio', 'destaques_rodada' ou 'misto'.",
            status=400,
        )

    if limite <= 0 or limite > 50:
        return resposta_erro(
            "Parâmetro 'limite' inválido. Use um valor entre 1 e 50.",
            status=400,
        )

    if rodadas <= 0 or rodadas > 38:
        return resposta_erro(
            "Parâmetro 'rodadas' inválido. Use um valor entre 1 e 38.",
            status=400,
        )

    if ordenar_por not in ORDENACOES_DESTAQUES:
        return resposta_erro(
            "Parâmetro 'ordenar_por' inválido. Use 'pontuacao_cartola' ou 'pontuacao_calculada'.",
            status=400,
        )

    resultado = recomendacao_por_criterio(
        criterio=criterio,
        posicao_id=posicao_id,
        limite=limite,
        rodadas=rodadas,
        rodada=rodada,
        ordenar_por=ordenar_por,
    )
    return jsonify(resultado)


@recomendacoes_bp.route("/custo-beneficio", methods=["GET"])
def custo_beneficio():
    posicao_id = request.args.get("posicao_id", type=int)
    limite = request.args.get("limite", default=10, type=int)

    if limite <= 0 or limite > 50:
        return resposta_erro(
            "Parâmetro 'limite' inválido. Use um valor entre 1 e 50.",
            status=400
        )

    resultado = recomendacao_custo_beneficio(
        posicao_id=posicao_id,
        limite=limite
    )
    return jsonify(resultado)


@recomendacoes_bp.route("/destaques-rodada", methods=["GET"])
def destaques_rodada():
    rodada = request.args.get("rodada", type=int)
    posicao_id = request.args.get("posicao_id", type=int)
    limite = request.args.get("limite", default=10, type=int)
    ordenar_por = request.args.get("ordenar_por", default="pontuacao_cartola", type=str)

    if limite <= 0 or limite > 50:
        return resposta_erro(
            "Parâmetro 'limite' inválido. Use um valor entre 1 e 50.",
            status=400
        )

    if ordenar_por not in ORDENACOES_DESTAQUES:
        return resposta_erro(
            "Parâmetro 'ordenar_por' inválido. Use 'pontuacao_cartola' ou 'pontuacao_calculada'.",
            status=400
        )

    resultado = recomendacao_destaques_rodada(
        rodada=rodada,
        posicao_id=posicao_id,
        limite=limite,
        ordenar_por=ordenar_por
    )
    return jsonify(resultado)