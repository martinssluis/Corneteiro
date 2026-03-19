from pathlib import Path

from flask import Blueprint, Response, jsonify


docs_bp = Blueprint("docs", __name__)

OPENAPI_FILE = Path(__file__).resolve().parents[2] / "docs" / "openapi.yaml"


@docs_bp.route("", methods=["GET"])
@docs_bp.route("/", methods=["GET"])
def docs_index():
    return jsonify(
        {
            "documentacao": "API Corneteiro",
            "arquivos": {
                "openapi": "/docs/openapi.yaml",
                "guia_endpoints": "/docs/api-endpoints",
            },
        }
    )


@docs_bp.route("/openapi.yaml", methods=["GET"])
def openapi_spec():
    return Response(OPENAPI_FILE.read_text(encoding="utf-8"), mimetype="application/yaml")


@docs_bp.route("/api-endpoints", methods=["GET"])
def api_endpoints_guide():
    guide_file = Path(__file__).resolve().parents[2] / "docs" / "api-endpoints.md"
    return Response(guide_file.read_text(encoding="utf-8"), mimetype="text/markdown")
