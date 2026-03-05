from flask import Blueprint, jsonify, request
from app.services.recomendacoes_service import recomendacao_custo_beneficio
from app.utils.erros import resposta_erro

recomendacoes_bp = Blueprint("recomendacoes", __name__)


@recomendacoes_bp.route("/custo-beneficio", methods=["GET"])
def custo_beneficio():
    """
    Endpoint de recomendação v0 baseado em custo-benefício.

    Parâmetros:
    - posicao_id (opcional): filtra recomendações por posição
    - limite (opcional): quantidade máxima de recomendações (1 a 50)
    
    Exemplo:
    /recomendacoes/custo-beneficio
    /recomendacoes/custo-beneficio?posicao_id=5
    /recomendacoes/custo-beneficio?posicao_id=5&limite=10
    """

    posicao_id = request.args.get("posicao_id", type=int)
    limite = request.args.get("limite", default=10, type=int)

    # validação do limite
    if limite <= 0 or limite > 50:
        return resposta_erro(
            "Parâmetro 'limite' inválido. Use um valor entre 1 e 50.",
            status=400
        )

    try:
        resultado = recomendacao_custo_beneficio(
            posicao_id=posicao_id,
            limite=limite
        )
        return jsonify(resultado)

    except Exception as e:
        # fallback para evitar quebra inesperada
        return resposta_erro(
            "Erro ao gerar recomendações",
            status=500,
            detalhe=str(e)
        )