#!/usr/bin/env python
"""Application entry point for local runs and Gunicorn."""

from __future__ import annotations

import logging
import os
import signal
import sys
from threading import Event

from src.main import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 5000))
HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
DEBUG = os.environ.get("FLASK_ENV", "production") == "development"
shutdown_event = Event()


def _register_signal_handlers() -> None:
    """Register SIGINT/SIGTERM handlers for graceful shutdown."""

    def _handle_signal(signum, _frame):
        logger.info("Received signal %s, shutting down gracefully.", signum)
        shutdown_event.set()
        raise KeyboardInterrupt

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _handle_signal)


app = create_app()


def main() -> None:
    """Run Flask app for local development and direct execution."""
    _register_signal_handlers()
    logger.info("Starting app on %s:%s (debug=%s)", HOST, PORT, DEBUG)

    try:
        app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=DEBUG, threaded=True)
    except KeyboardInterrupt:
        logger.info("Application stopped gracefully.")
    except Exception:
        logger.exception("Failed to start application.")
        sys.exit(1)


if __name__ == "__main__":
    main()
