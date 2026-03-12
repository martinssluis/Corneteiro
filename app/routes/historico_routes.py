from flask import Blueprint, jsonify, request
from app.services.historico_service import get_historico_atleta
from app.utils.erros import resposta_erro

historico_bp = Blueprint("historico", __name__)


@historico_bp.route("/atleta/<int:atleta_id>", methods=["GET"])
def historico_atleta(atleta_id):
    rodadas = request.args.get("rodadas", default=5, type=int)

    if rodadas <= 0 or rodadas > 38:
        return resposta_erro(
            "Parâmetro 'rodadas' inválido. Use um valor entre 1 e 38.",
            status=400
        )

    resultado = get_historico_atleta(atleta_id=atleta_id, rodadas=rodadas)
    return jsonify(resultado)