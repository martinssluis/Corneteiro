from flask import Blueprint, jsonify, request
from app.utils.formatadores import anexar_clube_e_posicao
from app.services.cartola_service import (
    get_mercado_status,
    get_atleta_by_id,
    buscar_atletas_por_nome
)

atleta_bp = Blueprint("atletas", __name__)

@atleta_bp.route("/status", methods=["GET"])
def market_status():
    return jsonify(get_mercado_status())

@atleta_bp.route("/<int:atleta_id>", methods=["GET"])
def get_atleta(atleta_id):
    atleta = get_atleta_by_id(atleta_id)
    if not atleta:
        return jsonify({"erro": "Atleta não encontrado"}), 404

    # Unitário: sempre retorna clube e posição
    atleta = anexar_clube_e_posicao(atleta)

    return jsonify(atleta)

@atleta_bp.route("/buscar", methods=["GET"])
def buscar_por_nome():
    nome = request.args.get("nome", type=str)
    exato = request.args.get("exato", default=False, type=lambda v: str(v).lower() == "true")

    if not nome:
        return jsonify({"erro": "Informe o parâmetro 'nome'"}), 400

    resultados = buscar_atletas_por_nome(nome, exato=exato)

    if not resultados:
        return jsonify({"erro": "Nenhum atleta encontrado"}), 404

    # Lista: NÃO enriquecer por padrão (performance)
    return jsonify({
        "termo_busca": nome,
        "quantidade": len(resultados),
        "atletas": resultados
    })