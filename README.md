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

# Run MFA demo + WhatsApp bot (presentation-ready)
python MFA_DEMO_SETUP.py            # seed demo accounts + QR codes
python MFA_VERIFY_SETUP.py          # sanity check TOTP
make run-whatsapp-bot               # start WhatsApp webhook (env vars required)
make tunnel                         # expose webhook via ngrok
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

## WhatsApp Bot (Docker)

```bash
docker compose -f docker-compose.whatsapp.yml up --build
```

Environment required in `.env`: `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`.

Health check: `curl http://localhost:5000/healthz` (also wired into docker-compose healthcheck).

Cost estimate (Pakistan): `python scripts/pricing_calculator.py --marketing 500 --utility 3000 --authentication 100`

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

## WhatsApp API (Meta Cloud - Sandbox Ready)

Create outbound WhatsApp message payload:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/whatsapp/send \
  -H "Content-Type: application/json" \
  -d "{\"to_phone\":\"923001234567\",\"message\":\"Assalam o Alaikum! Aap ka order confirm ho gaya hai.\"}"
```

Webhook endpoints:
- Verify endpoint: `GET /api/v1/whatsapp/webhook`
- Event endpoint: `POST /api/v1/whatsapp/webhook`

`POST /api/v1/whatsapp/send` sends real messages in live mode and includes retry logic.

Set these env vars in `.env` for live mode:
- `WHATSAPP_ENABLED=true`
- `WHATSAPP_SANDBOX_MODE=false`
- `WHATSAPP_ACCESS_TOKEN=...`
- `WHATSAPP_PHONE_NUMBER_ID=...`
- `WHATSAPP_VERIFY_TOKEN=...`
- `WHATSAPP_APP_SECRET=...`
- `WHATSAPP_TIMEOUT_SECONDS=15`
- `WHATSAPP_MAX_RETRIES=2`
- `WHATSAPP_RETRY_BACKOFF_SECONDS=1.0`

## Requirements

- Python 3.8+
- See `requirements-simple.txt` for API + local ML starter dependencies

For stable local ML behavior on Windows, prefer Python 3.11 or 3.12.  
Python 3.13 environments can hit native NumPy/SciPy crashes depending on wheel build.

Client pricing proposal template (Pakistan, beginner-friendly):  
`docs/CLIENT_PROPOSAL_TEMPLATE_PK_BEGINNER.md`

Detailed pricing/cost model for partner discussion:  
`docs/PRICING_COST_MODEL_PK.md`

## License

MIT License - see `LICENSE`
