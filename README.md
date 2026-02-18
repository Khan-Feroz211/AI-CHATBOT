# AI Project Assistant Pro (Pakistan Seller Edition)

A powerful AI-powered task management and productivity tool.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Khan-Feroz211/AI-CHATBOT.git
cd AI-CHATBOT

# Install dependencies (recommended)
pip install -r requirements-simple.txt

# Run database migration (first time only)
python migrate_database.py

# Start the desktop app
python enhanced_chatbot_pro.py

# Or run the web version (Pakistan seller profile UI)
cd web
python -m http.server 8000
# Visit: http://localhost:8000
```

## Windows PowerShell (Path With Spaces)

If your folder path has spaces (for example `C:\Users\Feroz Khan\...`), quote it:

```powershell
Set-Location "C:\Users\Feroz Khan\project-assistant-bot"
python -m http.server 8000 --directory web
```

Visit: `http://127.0.0.1:8000`

## Docker Deploy

```bash
# Build and run API + Web
docker compose up -d --build
```

Services:
- API: `http://127.0.0.1:8000`
- Web UI: `http://127.0.0.1:8080`

Set a strong secret before production deploy:

```bash
# Linux/macOS
export SECRET_KEY="replace-with-strong-random-value"
docker compose up -d --build
```

```powershell
# Windows PowerShell
$env:SECRET_KEY="replace-with-strong-random-value"
docker compose up -d --build
```

## Features

- Task management with priorities
- Smart note-taking with tags
- AI chat assistant (OpenAI/Anthropic-ready)
- Guest mode (no registration needed)
- Analytics dashboard
- Export to PDF/Markdown
- Secure user authentication
- Pakistan-market workflow support (Urdu voice, PKR pricing, WhatsApp-style templates)
- Payment workflows: JazzCash, EasyPaisa, bank transfer, COD (sandbox-ready API)

## Payment API

Create payment request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/payments/create \
  -H "Content-Type: application/json" \
  -d "{\"order_id\":\"ORD-1001\",\"amount_pkr\":3500,\"payment_provider\":\"jazzcash\"}"
```

Configure providers in `.env` (see `.env.example`).

Sandbox mode (default) lets you demo payment links locally without live merchant credentials.
For live mode, set `PAYMENT_SANDBOX_MODE=false` and provide JazzCash/EasyPaisa merchant keys.

## Requirements

- Python 3.8+
- See `requirements-simple.txt` for API + local ML starter dependencies

## License

MIT License - see `LICENSE`
