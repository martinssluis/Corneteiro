from flask import Blueprint, jsonify, request
from app.services.cartola_parciais_service import get_pontuados, get_pontuados_por_rodada
from app.services.pontuacao_service import calcular_pontuacao_por_scout
from app.utils.formatadores import anexar_clube_e_posicao

pontuados_bp = Blueprint("pontuados", __name__)

def _anexar_pontuacao_calculada(data: dict):
    atletas = data.get("atletas", {})
    for _, atleta in atletas.items():
        scout = atleta.get("scout", {})
        atleta["pontuacao_calculada"] = calcular_pontuacao_por_scout(scout)
    return data

def _buscar_atleta_em_pontuados(data: dict, atleta_id: int):
    atletas = data.get("atletas", {})
    return atletas.get(str(atleta_id))


# Rodada atual (LISTA) -> sem clube/posição
@pontuados_bp.route("/", methods=["GET"])
def pontuados_rodada_atual():
    calcular = str(request.args.get("calcular", "false")).lower() == "true"
    data = get_pontuados()

    if calcular:
        data = _anexar_pontuacao_calculada(data)

    return jsonify(data)


# Rodada específica (LISTA) -> sem clube/posição
@pontuados_bp.route("/<int:rodada>", methods=["GET"])
def pontuados_por_rodada(rodada):
    calcular = str(request.args.get("calcular", "false")).lower() == "true"
    data = get_pontuados_por_rodada(rodada)

    if calcular:
        data = _anexar_pontuacao_calculada(data)

    return jsonify(data)


# Atleta na rodada atual (UNITÁRIO) -> com clube/posição
@pontuados_bp.route("/atleta/<int:atleta_id>", methods=["GET"])
def pontuados_atleta_rodada_atual(atleta_id):
    calcular = str(request.args.get("calcular", "true")).lower() == "true"
    data = get_pontuados()

    atleta = _buscar_atleta_em_pontuados(data, atleta_id)
    if not atleta:
        return jsonify({"erro": "Atleta não encontrado nos pontuados da rodada atual"}), 404

    resposta = {
        "atleta_id": atleta_id,
        "apelido": atleta.get("apelido"),
        "foto": atleta.get("foto"),
        "pontuacao_cartola": atleta.get("pontuacao"),
        "posicao_id": atleta.get("posicao_id"),
        "clube_id": atleta.get("clube_id"),
        "entrou_em_campo": atleta.get("entrou_em_campo"),
        "scout": atleta.get("scout", {})
    }

    if calcular:
        resposta["pontuacao_calculada"] = calcular_pontuacao_por_scout(resposta["scout"])

    # Unitário: sempre retorna clube e posição
    resposta = anexar_clube_e_posicao(resposta)

    return jsonify(resposta)


# Atleta em rodada específica (UNITÁRIO) -> com clube/posição
@pontuados_bp.route("/<int:rodada>/atleta/<int:atleta_id>", methods=["GET"])
def pontuados_atleta_por_rodada(rodada, atleta_id):
    calcular = str(request.args.get("calcular", "true")).lower() == "true"
    data = get_pontuados_por_rodada(rodada)

    atleta = _buscar_atleta_em_pontuados(data, atleta_id)
    if not atleta:
        return jsonify({"erro": "Atleta não encontrado nos pontuados desta rodada"}), 404

    resposta = {
        "rodada": rodada,
        "atleta_id": atleta_id,
        "apelido": atleta.get("apelido"),
        "foto": atleta.get("foto"),
        "pontuacao_cartola": atleta.get("pontuacao"),
        "posicao_id": atleta.get("posicao_id"),
        "clube_id": atleta.get("clube_id"),
        "entrou_em_campo": atleta.get("entrou_em_campo"),
        "scout": atleta.get("scout", {})
    }

    if calcular:
        resposta["pontuacao_calculada"] = calcular_pontuacao_por_scout(resposta["scout"])

    # Unitário: sempre retorna clube e posição
    resposta = anexar_clube_e_posicao(resposta)

    return jsonify(resposta)