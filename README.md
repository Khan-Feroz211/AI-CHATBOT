# WhatsApp Business Bot - Quick Start

Production-ready WhatsApp bot with Twilio integration, MFA authentication, and business features.

## Features

✅ **TwiML Response Format** - Proper XML responses for Twilio
✅ **MFA Authentication** - TOTP-based security with QR codes
✅ **Business Functions** - Stock, Orders, Pricing, Transactions
✅ **PKR Currency** - Pakistan Rupee formatting
✅ **Error Handling** - Comprehensive error recovery
✅ **Health Checks** - Monitoring endpoints

## Quick Start

### 1. Install Dependencies

```bash
cd AI-CHATBOT
pip install -r requirements.txt
```

### 2. Configure Twilio

Edit `.env` in parent directory:
```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 3. Run Bot Locally

```bash
python run.py
```

Bot starts on: `http://localhost:5000`

### 4. Test Locally

```bash
python test_local.py
```

### 5. Start Demo with Ngrok

```bash
python start_demo.py
```

This will:
- Start the bot
- Launch ngrok tunnel
- Display webhook URL for Twilio

### 6. Configure Twilio Sandbox

1. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Paste webhook URL in "WHEN A MESSAGE COMES IN"
3. Click Save
4. Send `join <code>` to Twilio WhatsApp number
5. Send `hi` to start!

## Bot Commands

| Command | Description |
|---------|-------------|
| `hi`, `hello`, `menu` | Show main menu |
| `1`, `stock` | Check inventory |
| `2`, `order` | Place order |
| `order Product A 50` | Create order |
| `3`, `price` | Find best prices |
| `product a` | Price lookup |
| `4`, `transactions` | View history |
| `5`, `account` | My account |
| `6`, `help` | Help menu |
| `reorder Product B` | Restock product |
| `receipt ORD-001` | Get receipt |
| `buy from supplier 1 Product A 100` | Supplier order |

## File Structure

```
AI-CHATBOT/
├── run.py                    # Main Flask app
├── start_demo.py             # Demo launcher with ngrok
├── test_local.py             # Local testing script
├── requirements.txt          # Dependencies
├── auth/
│   ├── __init__.py
│   └── mfa_whatsapp.py      # MFA authentication
└── whatsapp/
    ├── __init__.py
    ├── message_handler.py    # Message router
    ├── handlers.py           # Business logic
    └── menu.py               # Menu templates
```

## Endpoints

- `POST /webhook` - Twilio webhook (TwiML response)
- `GET /webhook` - Webhook verification
- `GET /health` - Health check

## Testing

### Manual Test
```bash
curl -X POST http://localhost:5000/webhook \
  -d "Body=hi&From=whatsapp:+923001234567"
```

### Automated Tests
```bash
python test_local.py
```

## Troubleshooting

### Bot not responding?
- Check bot is running: `curl http://localhost:5000/health`
- Check Twilio webhook URL is correct
- Check console for errors

### Twilio sending template instead of bot reply?
- Verify webhook returns TwiML format
- Check Content-Type is `text/xml`
- Verify webhook URL in Twilio console

### MFA not working?
- QR codes saved in current directory
- Use Microsoft Authenticator or Oracle Authenticator
- Check 6-digit code is current

## Production Deployment

### Docker
```bash
docker build -t whatsapp-bot .
docker run -p 5000:5000 --env-file ../.env whatsapp-bot
```

### Heroku
```bash
heroku create your-bot-name
git push heroku main
heroku config:set TWILIO_ACCOUNT_SID=xxx
heroku config:set TWILIO_AUTH_TOKEN=xxx
```

### Railway
```bash
railway init
railway up
```

## Security Notes

- Never commit `.env` file
- Change `SECRET_KEY` in production
- Enable `VALIDATE_TWILIO=true` in production
- Use environment variables for secrets
- Rate limit webhook in production

## Support

For issues or questions:
- Check console logs
- Review Twilio webhook logs
- Test with `test_local.py`
- Check health endpoint

## License

MIT License
