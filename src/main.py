"""Flask application factory and setup."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify
from flask_cors import CORS

from src.auth import auth_bp
from src.core.cache import init_redis
from src.core.config import Config, get_config
from src.core.database import init_database


def create_app(config: Config | None = None) -> Flask:
    """Create and configure Flask application."""
    if config is None:
        config = get_config()

    app = Flask(__name__)
    _apply_config(app, config)

    cors_origins = os.environ.get("CORS_ORIGINS", "*")
    origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    CORS(app, origins=origins if origins else ["*"])

    setup_logging(app)

    init_database(config)
    redis_client = init_redis(config)
    app.extensions["redis_client"] = redis_client

    register_error_handlers(app)
    register_blueprints(app)
    register_health_route(app)

    app.logger.info("Flask application initialized successfully")
    return app


def _apply_config(app: Flask, config: Config) -> None:
    for key in dir(config):
        if key.isupper():
            app.config[key] = getattr(config, key)


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp)
    app.logger.info("Blueprints registered")


def register_health_route(app: Flask) -> None:
    @app.route("/health", methods=["GET"])
    def health_check():
        redis_status = (
            "connected" if app.extensions.get("redis_client") is not None else "offline"
        )
        return (
            jsonify(
                {
                    "status": "ok",
                    "bot": "ready",
                    "environment": app.config.get("FLASK_ENV", "production"),
                    "redis": redis_status,
                }
            ),
            200,
        )


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Not Found", "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(_error):
        app.logger.exception("Unhandled internal server error")
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                }
            ),
            500,
        )

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        app.logger.exception("Unhandled exception: %s", error)
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
    level_name = app.config.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, level_name, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    )
    root_logger.addHandler(stream_handler)

    log_file = app.config.get("LOG_FILE", "")
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(log_file, maxBytes=10_485_760, backupCount=5)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
        )
        root_logger.addHandler(file_handler)

    app.logger.setLevel(log_level)


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
