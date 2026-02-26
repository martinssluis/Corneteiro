from flask import Blueprint, jsonify
from app.services.cartola_service import get_mercado_status

mercado_bp = Blueprint("mercado", __name__)

@mercado_bp.route("/status", methods=["GET"])
def status_mercado():
    return jsonify(get_mercado_status())