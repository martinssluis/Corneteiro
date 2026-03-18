from flask import Blueprint, jsonify, request

from app.services.tendencia_service import get_tendencia_atleta
from app.utils.erros import resposta_erro

tendencia_bp = Blueprint("tendencia", __name__)


@tendencia_bp.route("/atleta/<int:atleta_id>", methods=["GET"])
def tendencia_atleta(atleta_id):
    rodadas = request.args.get("rodadas", default=6, type=int)

    if rodadas <= 0 or rodadas > 38:
        return resposta_erro(
            "Parâmetro 'rodadas' inválido. Use um valor entre 1 e 38.",
            status=400
        )

    resultado = get_tendencia_atleta(atleta_id=atleta_id, rodadas=rodadas)
    return jsonify(resultado)
