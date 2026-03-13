"""Railpack fallback entrypoint for AI-CHATBOT subfolder deployments."""

from run import app


if __name__ == "__main__":
    import os

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
