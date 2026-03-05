from flask import Flask
from .config import Config
import requests
from .utils.erros import resposta_erro

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)


    from .routes.mercado_routers import mercado_bp
    from .routes.atletas_routers import atleta_bp
    from .routes.pontuados_routes import pontuados_bp
    from .routes.clubes_routes import clubes_bp
    from .routes.recomendacoes_routes import recomendacoes_bp

    app.register_blueprint(mercado_bp, url_prefix="/mercado")
    app.register_blueprint(atleta_bp, url_prefix="/atletas")
    app.register_blueprint(pontuados_bp, url_prefix="/pontuados")
    app.register_blueprint(clubes_bp, url_prefix="/clubes")
    app.register_blueprint(recomendacoes_bp, url_prefix="/recomendacoes")

    @app.errorhandler(requests.exceptions.RequestException)
    def handle_requests_exception(e):
        return resposta_erro("Falha ao consultar API do Cartola", status=502, detalhe=str(e))

    @app.errorhandler(404)
    def handle_404(e):
        return resposta_erro("Recurso não encontrado", status=404)

    @app.errorhandler(500)
    def handle_500(e):
        return resposta_erro("Erro interno do servidor", status=500, detalhe=str(e))

    return app