from flask import Flask
from .config import Config

def create_app():
    app = Flask (__name__)
    app.config.from_object(Config)
    
    # registrar blueprints
    from .routes.mercado_routers import mercado_bp
    from .routes.atletas_routers import atleta_bp
    
    app.register_blueprint(mercado_bp, url_prefix="/mercado")
    app.register_blueprint(atleta_bp, url_prefix="/atletas")
    
    return app