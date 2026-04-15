# CHANGES — BazaarBot

## v1.0.0 — 2026-04-15 (Initial Release)

### New features
- **WhatsApp bot** with full menu-driven and natural language interface
- **Stock manager** — add, update, sell products; auto low-stock detection
- **Order management** — customer orders on WhatsApp, stock auto-decrements
- **Market Finder** — Pakistan wholesale market guide (Karachi, Lahore, Islamabad, Faisalabad)
- **EasyPaisa / JazzCash / Bank IBAN** payment info sharing
- **Appointment booking** — date/time based, multi-turn session, admin view
- **Transaction history** — per-customer order list
- **TF-IDF NLP engine** with Urdu romanisation — 12 intents, cosine retrieval RAG
- **Built-in knowledge base** — Pakistan markets, payment methods, FAQ (Markdown)
- **Multi-tenant SQLite database** — one deployment, multiple shops
- **Flask web dashboard** — landing page, login, dashboard, inventory, appointments, knowledge, settings
- **REST API** `/api/message` for CRM / app integration
- **Rate limiting** — Flask-Limiter on all public endpoints
- **Email notifications** — SMTP (order confirm, low stock alert, appointment confirm)
- **Tenant onboarding CLI** — `python run.py --setup-tenant`
- **Dockerfile** — single container deploy
- **Railway/Render** ready (Procfile + nixpacks.toml)
- **46 tests** — NLP, DB, webhook, REST API, chat widget, dashboard

### Architecture
- Replaced old desktop/Tkinter app with cloud-native Flask + WhatsApp stack
- Removed legacy/, desktop/, enhanced_chatbot_pro.py, 18 stale docs
- Single `run.py` entrypoint; all code in `bazaarbot/` package

### Removed
- `desktop/` — Tkinter GUI (not useful for mobile-first Pakistan market)
- `legacy/` — old demo scripts
- `auth/mfa_whatsapp.py` — replaced by simpler admin login
- Various stale docs, PS1 scripts, duplicate entry points
