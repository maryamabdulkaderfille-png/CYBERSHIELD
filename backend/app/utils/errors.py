from flask import jsonify
from marshmallow import ValidationError


class APIError(Exception):
    def __init__(self, message: str, status_code: int = 400, payload: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}

    def to_dict(self) -> dict:
        return {"error": self.message, **self.payload}


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(err: APIError):
        return jsonify(err.to_dict()), err.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    @app.errorhandler(404)
    def handle_not_found(err):
        return jsonify({"error": "Resource not found."}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(err):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(413)
    def handle_payload_too_large(err):
        return jsonify({"error": "Request body is too large."}), 413

    @app.errorhandler(429)
    def handle_rate_limited(err):
        return jsonify({"error": "Too many requests. Please try again later."}), 429

    @app.errorhandler(500)
    def handle_server_error(err):
        app.logger.exception("Unhandled server error: %s", err)
        return jsonify({"error": "Internal server error."}), 500
