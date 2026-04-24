from flask import Blueprint, jsonify, request
from app.utils.formatadores import anexar_clube_e_posicao
from app.services.cartola_service import (
    get_mercado_status,
    get_atleta_by_id,
    buscar_atletas_por_nome,
    get_atletas_mercado,
)

atleta_bp = Blueprint("atletas", __name__)

@atleta_bp.route("/status", methods=["GET"])
def market_status():
    return jsonify(get_mercado_status())

@atleta_bp.route("/<int:atleta_id>", methods=["GET"])
def get_atleta(atleta_id):
    atleta = get_atleta_by_id(atleta_id)
    if not atleta:
        return jsonify({"erro": "Atleta nao encontrado"}), 404

    # Unitario: sempre retorna clube e posicao
    atleta = anexar_clube_e_posicao(atleta)

    return jsonify(atleta)

@atleta_bp.route("/buscar", methods=["GET"])
def buscar_por_nome():
    nome = request.args.get("nome", type=str)
    exato = request.args.get("exato", default=False, type=lambda v: str(v).lower() == "true")

    if not nome:
        return jsonify({"erro": "Informe o parametro 'nome'"}), 400

    resultados = buscar_atletas_por_nome(nome, exato=exato)

    if not resultados:
        return jsonify({"erro": "Nenhum atleta encontrado"}), 404

    # Lista: NAO enriquecer por padrao (performance)
    return jsonify({
        "termo_busca": nome,
        "quantidade": len(resultados),
        "atletas": resultados
    })


@atleta_bp.route("/clube/<int:clube_id>", methods=["GET"])
def listar_atletas_do_clube(clube_id):
    """Lista atletas de um clube especifico a partir do mercado atual."""
    data = get_atletas_mercado()
    atletas = data.get("atletas", []) if isinstance(data, dict) else []

    filtrados = [a for a in atletas if a.get("clube_id") == clube_id]

    if not filtrados:
        return jsonify({
            "clube_id": clube_id,
            "quantidade": 0,
            "atletas": [],
        }), 200

    enriquecidos = [anexar_clube_e_posicao(dict(a)) for a in filtrados]

    # Ordena por preco desc para destacar os mais caros primeiro
    enriquecidos.sort(
        key=lambda a: (a.get("preco_num") or 0),
        reverse=True,
    )

    return jsonify({
        "clube_id": clube_id,
        "quantidade": len(enriquecidos),
        "atletas": enriquecidos,
    })
