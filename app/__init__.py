import os
from types import SimpleNamespace

from flask import Flask, jsonify
from flask_cors import CORS

from config import config_by_name
from constants import ConfigMessages
from app.database import init_db
from app.errors import register_error_handlers
from app.services.ai_service import AIService


def create_app(config_name=None, test_config=None):
    app = Flask(__name__)

    environment = (
        config_name
        if config_name is not None
        else os.environ.get("APP_ENV", "development")
    )

    if environment not in config_by_name:
        raise ValueError(ConfigMessages.INVALID_ENVIRONMENT)

    app.config.from_object(config_by_name[environment])
    app.config["MAX_CONTENT_LENGTH"] = 256 * 1024

    if test_config is not None:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(ConfigMessages.MISSING_SECRET_KEY)

    app.json.ensure_ascii = False

    # Servise yalnızca ihtiyaç duyduğu ayarları veriyoruz.
    ai_settings = SimpleNamespace(
        AI_PROVIDER=app.config["AI_PROVIDER"],
        GROQ_API_KEY=app.config["GROQ_API_KEY"],
        GROQ_MODEL=app.config["GROQ_MODEL"],
        BUSINESS_CONTEXT=app.config["BUSINESS_CONTEXT"],
    )

    # Bu servis nesnesi yalnızca bu uygulamaya ait.
    app.extensions["ai_service"] = AIService(
        settings=ai_settings
    )

    register_error_handlers(app)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["CORS_ORIGINS"],
            }
        },
    )

    with app.app_context():
        init_db(app)

    from app.routes import api_bp, pages_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.get("/health")
    def health():
        return jsonify({
            "basari": True,
            "durum": "aktif",
        }), 200

    return app