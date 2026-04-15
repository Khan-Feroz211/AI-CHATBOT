# 🇵🇰 BazaarBot — Pakistan ki Apni Business Assistant

## Kya Hai? / What is it?

**BazaarBot** ek AI-powered WhatsApp business assistant hai jo Pakistani chote
dukandar, retailers, aur service providers ke liye specifically design kiya gaya
hai. Yeh aapko WhatsApp pe hi poora business manage karne ki suvidha deta hai —
bina kisi complex software ke.

> **Target users:** Jazz/Zong franchise dealers, kirana store owners, wholesale
> merchants, service providers, restaurant/dhaba owners, mobile shop dealers

---

## Features / Kya Kar Sakta Hai?

| Feature | WhatsApp Command | Description |
|---------|-----------------|-------------|
| 📦 Stock Manager | `1` / `stock` | Check inventory, add/update products |
| 🛍️ Order Management | `2` / `order` | Take customer orders on WhatsApp |
| 🏪 Market Finder | `3` / `market karachi` | Find wholesale markets by city |
| 💰 Payments | `4` / `payment` | Share EasyPaisa/JazzCash details |
| 📅 Appointments | `5` / `appointment` | Book/manage customer visits |
| 💳 Order History | `6` / `history` | View past sales |
| ❓ Help | `7` / `help` | Full command list |

### WhatsApp Quick Commands
```
add product Atta 100 kg 70      → Add/update product
sell Atta 5                     → Record a sale (-5 from stock)
update Atta 200                 → Set stock to exact quantity
order Atta 5                    → Customer places an order
market lahore                   → Find Lahore wholesale markets
appoint 2026-05-01 10:00 Delivery → Book an appointment
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language  | Python 3.12 |
| Web/API   | Flask 3, Flask-Limiter |
| Bot channel | Twilio WhatsApp API |
| NLP/AI    | TF-IDF + Cosine RAG (scikit-learn) — no external API required |
| Database  | SQLite (WAL mode, multi-tenant) |
| Hosting   | Railway / Render / Docker |
| Notifications | SMTP email (Gmail/Zoho) |

---

## Quick Start / Jaldi Shuru Karein

### 1. Requirements install karein
```bash
pip install -r requirements.txt
```

### 2. Environment variables set karein
```bash
cp .env.example .env
# .env file mein apna password aur credentials bharein
```

### 3. Pehla tenant setup karein
```bash
python run.py --setup-tenant
```

### 4. Server start karein
```bash
python run.py
# Dashboard: http://localhost:5000/dashboard  (password: .env mein set karein)
# WhatsApp Webhook: http://localhost:5000/webhook
```

### 5. Twilio WhatsApp configure karein
- Twilio Console mein WhatsApp Sandbox activate karein
- Webhook URL: `https://your-domain.com/webhook`

---

## Pricing Plans / Qeemat

| Plan | Price | Msgs/Month | Features |
|------|-------|-----------|---------|
| **Starter** | Free | 100 | WhatsApp bot, stock manager |
| **Business** | Rs.1,500/month | Unlimited | + EasyPaisa/JazzCash, dashboard, email |
| **Pro** | Rs.3,500/month | Unlimited | + Multi-branch, REST API, priority support |

---

## Deployment / Deploy Karna

### Railway (Recommended)
Set these environment variables on Railway:
`SECRET_KEY, ADMIN_PASSWORD, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN`

### Docker
```bash
docker build -t bazaarbot .
docker run -p 5000:5000 --env-file .env bazaarbot
```

---

## REST API

```http
POST /api/message
Content-Type: application/json

{"phone": "+923001234567", "message": "stock", "tenant": "my-shop"}
```

```json
{"response": "📦 Aapka Stock...", "intent": "stock_check"}
```

---

## Architecture

```
run.py                          ← Single entrypoint
bazaarbot/
  config.py                     ← Environment config
  database.py                   ← SQLite (multi-tenant)
  nlp/
    rag_engine.py               ← TF-IDF intent classifier + RAG
    knowledge_base/             ← Pakistan markets, payments, FAQ (Markdown)
  bot/
    intent_router.py            ← Main dispatcher (session-aware)
    handlers.py                 ← Business logic handlers
    menu.py                     ← WhatsApp menu strings
  channels/
    whatsapp.py                 ← Twilio outbound
    email_channel.py            ← SMTP notifications
  web/
    app.py                      ← Flask routes, webhook, REST API
    templates/                  ← Jinja2 dashboard templates
    static/                     ← CSS + JS
tests/
  test_bot.py                   ← 46 tests
```

---

## License
MIT
