"""Railpack fallback entrypoint at repository root.

Railpack can auto-start Python apps from app.py/main.py when no explicit
start command is detected.
"""

from run import app


if __name__ == "__main__":
    import os

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
