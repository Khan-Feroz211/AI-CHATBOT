"""BazaarBot — single entrypoint.

Usage:
    python run.py                       # start web server
    python run.py --setup-tenant        # interactive tenant setup wizard
"""
import sys
import os


def _setup_wizard():
    print("\n🛒 BazaarBot Tenant Setup Wizard")
    print("═" * 38)
    slug = input("Tenant slug (e.g. my-shop): ").strip() or "default"
    name = input("Business name: ").strip() or "My Shop"
    city = input("City (Karachi/Lahore/...): ").strip() or "Karachi"
    btype = input("Business type (retail/wholesale/restaurant...): ").strip() or "retail"
    phone = input("Owner phone (03XX-XXXXXXX): ").strip()
    email = input("Owner email: ").strip()
    from bazaarbot.database import init_db, create_tenant
    init_db()
    create_tenant(slug, name, city, btype, phone, email)
    print(f"\n✅ Tenant '{slug}' created.")
    print(f"   Dashboard: http://localhost:5000/dashboard")
    print(f"   Set DEFAULT_TENANT={slug} in .env\n")


def main():
    if "--setup-tenant" in sys.argv:
        _setup_wizard()
        return

    from bazaarbot.config import config
    port = config.PORT
    backend = os.environ.get("APP_BACKEND", "flask").lower()

    print(f"🚀 BazaarBot starting on port {port} [{backend}]")
    print(f"📍 Dashboard : http://localhost:{port}/dashboard")
    print(f"📱 Webhook   : http://localhost:{port}/webhook")
    print(f"💚 Health    : http://localhost:{port}/health")
    print(f"🔌 REST API  : http://localhost:{port}/api/message")

    if backend == "fastapi":
        import uvicorn
        from bazaarbot.web.fastapi_app import app as fastapi_app
        uvicorn.run(fastapi_app, host="0.0.0.0", port=port, reload=config.DEBUG)
    else:
        from bazaarbot.web.app import app
        app.run(host="0.0.0.0", port=port, debug=config.DEBUG)


if __name__ == "__main__":
    main()
