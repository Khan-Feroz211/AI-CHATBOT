# 🤖 AI Business Chatbot (WhatsApp)

A WhatsApp Business AI chatbot powered by Flask + Twilio + TOTP MFA.

## Quick Start
1. Fill .env with Twilio credentials
2. Run: python scripts/setup_demo_data.py
3. Run: python start_demo.py
4. Copy webhook URL → paste in Twilio Sandbox Settings
5. Send "join bite-drink" to +1 415 523 8886
6. Send "hi" → bot replies with menu ✅

## Features
- 🔐 TOTP MFA Authentication (Microsoft/Oracle Authenticator)
- 📦 Stock Management
- 🛒 Order Placement
- 💰 Price Finder
- 💳 Transaction History
- 👤 Account Management

## Project Structure
```
AI-CHATBOT/
├── run.py                     # Flask app + webhook
├── start_demo.py              # Demo runner
├── whatsapp/
│   ├── message_handler.py     # Message router
│   ├── menu.py                # Main menu
│   └── handlers.py            # Feature handlers
├── auth/
│   └── mfa_whatsapp.py        # TOTP MFA flow
├── tests/
│   └── test_bot.py            # Pytest tests
└── scripts/
    └── setup_demo_data.py     # Demo data setup
```

## Environment Variables (.env)
```
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

## Installation
```bash
pip install flask twilio pyotp qrcode[pil] pytest
python start_demo.py
```

## Webhook Setup
- Use ngrok: `ngrok http 5000`
- Set webhook URL in Twilio Sandbox: `https://<your-ngrok>.ngrok.io/webhook`
