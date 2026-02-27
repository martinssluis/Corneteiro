from flask import Blueprint, jsonify, request
from app.services.clubes_service import get_clubes, get_clube

clubes_bp = Blueprint("clubes", __name__)

@clubes_bp.route("/", methods=["GET"])
def listar_clubes():
    clubes = get_clubes()
    return jsonify(clubes)

@clubes_bp.route("/<int:clube_id>", methods=["GET"])
def buscar_clube(clube_id):
    clube = get_clube(clube_id)
    if not clube:
        return jsonify({"erro": "Clube não encontrado"}), 404
    return jsonify(clube)

@clubes_bp.route("/buscar", methods=["GET"])
def buscar_por_slug():
    slug = request.args.get("slug", type=str)
    if not slug:
        return jsonify({"erro": "Informe o parâmetro 'slug'"}), 400

    slug_norm = slug.strip().lower()
    clubes = get_clubes()

    for _, clube in clubes.items():
        if (clube.get("slug") or "").strip().lower() == slug_norm:
            return jsonify(clube)

    return jsonify({"erro": "Clube não encontrado"}), 404