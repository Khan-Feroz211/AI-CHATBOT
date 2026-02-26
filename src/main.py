"""Flask application factory and setup."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify
from flask_cors import CORS

from src.auth import auth_bp
from src.core.config import Config, get_config
from src.core.database import init_database


def create_app(config: Config = None) -> Flask:
    """Create and configure Flask application.

    Args:
        config: Configuration object. If None, uses environment to select config.

    Returns:
        Configured Flask application instance.
    """
    if config is None:
        config = get_config()

    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    CORS(app, origins=["*"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    init_database(config)
    setup_logging(app)
    register_error_handlers(app)
    register_blueprints(app)

    @app.route("/health", methods=["GET"])
    def health_check():
        """Return service health payload for deployment probes."""
        return jsonify({"status": "ok", "bot": "ready", "version": "1.0.0"}), 200

    with app.app_context():
        app.logger.info("Flask application initialized successfully")

    return app


def register_blueprints(app: Flask) -> None:
    """Register all active domain blueprints."""
    app.register_blueprint(auth_bp)
    app.logger.info("Blueprints registered")


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for common exceptions."""

    @app.errorhandler(400)
    def bad_request(error):
        """Handle HTTP 400 errors."""
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": str(error.description)
                    if hasattr(error, "description")
                    else "Invalid request",
                }
            ),
            400,
        )

    @app.errorhandler(401)
    def unauthorized(_error):
        """Handle HTTP 401 errors."""
        return (
            jsonify({"error": "Unauthorized", "message": "Authentication required"}),
            401,
        )

    @app.errorhandler(403)
    def forbidden(_error):
        """Handle HTTP 403 errors."""
        return jsonify({"error": "Forbidden", "message": "Access denied"}), 403

    @app.errorhandler(404)
    def not_found(_error):
        """Handle HTTP 404 errors."""
        return jsonify({"error": "Not Found", "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(_error):
        """Handle HTTP 500 errors."""
        app.logger.exception("Unhandled exception")
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                }
            ),
            500,
        )


def setup_logging(app: Flask) -> None:
    """Configure application logging."""
    if not app.debug and not app.testing:
        log_file = os.environ.get("LOG_FILE", "data/logs/app.log")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=10)
        file_handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    if app.debug or app.testing:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        )
        console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
        app.logger.addHandler(console_handler)

    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
    app.logger.info(
        "Logging configured for %s mode", "DEBUG" if app.debug else "PRODUCTION"
    )


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
