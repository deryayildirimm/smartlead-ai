from flask import current_app, jsonify, request
from werkzeug.exceptions import HTTPException

from constants import ErrorMessages, LogMessages
from app.exceptions import (
    AIServiceError,
    DatabaseError,
    ValidationError,
)


def error_response(message, status_code):
    """Ortak JSON hata yanıtını oluşturur."""

    return jsonify({
        "basari": False,
        "hata": message,
    }), status_code


def register_error_handlers(app):
    """Hata yakalayıcılarını Flask uygulamasına kaydeder."""

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return error_response(str(error), 400)

    @app.errorhandler(AIServiceError)
    def handle_ai_error(error):
        return error_response(str(error), 503)

    @app.errorhandler(DatabaseError)
    def handle_database_error(error):
        return error_response(str(error), 503)

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        is_api_request = (
            request.path == "/api"
            or request.path.startswith("/api/")
        )

        # Sayfa isteklerinde standart HTML hata yanıtını koru.
        if not is_api_request:
            return error

        # HTTP durum kodunu ve gerekli başlıkları koru.
        response = error.get_response()

        response.data = current_app.json.dumps({
            "basari": False,
            "hata": ErrorMessages.HTTP_ERRORS.get(
                error.code,
                ErrorMessages.REQUEST_FAILED,
            ),
        })

        response.content_type = "application/json"
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # Teknik ayrıntılar yalnızca sunucu loguna yazılır.
        current_app.logger.exception(
            LogMessages.UNEXPECTED
        )

        return error_response(
            ErrorMessages.UNEXPECTED,
            500,
        )