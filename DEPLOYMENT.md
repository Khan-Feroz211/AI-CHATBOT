# WhatsApp Inventory Bot - Complete Deployment & Testing Guide

## Quick Start (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements-minimal.txt

# 2. Set up environment
cp .env.example .env

# 3. Start bot locally
python run.py

# 4. In another terminal, run tests
python test_local.py
```

---

## Table of Contents

1. [Local Testing](#local-testing)
2. [Webhook Setup (Critical)](#webhook-setup)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployments](#cloud-deployments)
5. [Production Verification](#production-verification)

---

## Local Testing

### Starting the Bot

```bash
# Terminal 1: Start bot server
python run.py

# Expected output:
# 🚀 Starting WhatsApp Inventory Bot
# 📦 Initializing database...
# ✅ Database initialized
# 🌐 Starting server on 127.0.0.1:5000
# 📝 Debug mode: False
```

### Available Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/webhook` | GET | Webhook verification |
| `/webhook` | POST | Receive WhatsApp messages |

### Running Local Tests

```bash
# Terminal 2: Run test suite
python test_local.py

# Expected output:
# ==========================================
# 🤖 WhatsApp Inventory Bot - Local Testing
# ==========================================
# ✅ PASS: Health Check
# ✅ PASS: Webhook Verification
# ✅ PASS: Text Message
# ✅ PASS: MFA Setup
# ✅ PASS: Stock Command
# ✅ PASS: Order Command
# ==========================================
# Overall: 6/6 tests passed
```

### Running Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_security.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Webhook Setup (CRITICAL)

### Understanding Webhooks

A webhook is a URL your bot listens to for incoming WhatsApp messages. You need to:

1. **Create a webhook endpoint** (✅ Already done at `/webhook`)
2. **Register it with WhatsApp provider** (Twilio or Meta)
3. **Test that messages are received**

### Option A: Twilio Webhook

#### Step 1: Create Twilio Account

```
1. Go to https://www.twilio.com
2. Sign up (free tier available)
3. Create WhatsApp Sandbox
4. Get these credentials:
   - TWILIO_ACCOUNT_SID (your account ID)
   - TWILIO_AUTH_TOKEN (your auth token)
   - TWILIO_PHONE_NUMBER (sandbox number, e.g., +1234567890)
```

#### Step 2: Configure Webhook in Twilio

```
Twilio Console:
1. Go to Messaging → WhatsApp → Sandbox Settings
2. Set Webhook URL: https://your-domain.com/webhook
3. Set Webhook Method: POST
4. Save
```

#### Step 3: Test Webhook Reception

```bash
# Send test message from WhatsApp
# Your Twilio sandbox number will respond automatically

# Check logs to see the message was received
docker-compose logs -f bot
```

### Option B: Meta Cloud API Webhook

#### Step 1: Create Meta App

```
1. Go to https://developers.facebook.com
2. Create App → Business Type
3. Add WhatsApp Product
4. Get these credentials:
   - META_ACCESS_TOKEN
   - META_PHONE_NUMBER_ID
   
5. Generate a WEBHOOK_VERIFY_TOKEN (any random string):
   python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Step 2: Configure Webhook in Meta

```
Meta App Dashboard:
1. WhatsApp → Configuration
2. Set Webhook URL: https://your-domain.com/webhook
3. Set Verify Token: (your random token from step 1)
4. Subscribe to webhook fields:
   - messages
   - message_status
5. Save settings
```

#### Step 3: Meta Will Test Your Webhook

Meta sends:
```
GET /webhook?hub.mode=subscribe&hub.verify_token=<token>&hub.challenge=<random>
```

Your bot automatically responds with the challenge string to verify.

#### Step 4: Send Test Message

Once verified, send a WhatsApp to your number. Your bot will:
1. Receive the message
2. Parse it
3. Generate response
4. Send reply

Check bot logs:
```bash
# If using Docker
docker-compose logs -f bot | grep "message"
```

### Testing Webhook Locally (No HTTPS)

Use **ngrok** to create a public HTTPS tunnel to your local machine:

```bash
# 1. Download ngrok from https://ngrok.com
#    (or brew install ngrok if you have Homebrew)

# 2. Start ngrok tunnel to your local bot
ngrok http 5000

# Output:
# Session Status       online
# Account              (your account)
# Version              3.0.0
# Region               us (California)
# Latency              0ms
# Web Interface        http://127.0.0.1:4040
# Forwarding           https://abc123def456.ngrok.io -> http://127.0.0.1:5000

# 3. Use this URL in WhatsApp provider:
#    Webhook: https://abc123def456.ngrok.io/webhook

# 4. Send test message to your WhatsApp number

# 5. Check bot logs for receipt:
python run.py  # Should show incoming messages
```

### Testing Webhook with curl

```bash
# Test webhook verification (this is what Meta/Twilio does)
curl -X GET "http://localhost:5000/webhook?" \
  -d "hub.mode=subscribe" \
  -d "hub.verify_token=your-verify-token" \
  -d "hub.challenge=test_challenge"

# Test incoming message
curl -X POST "http://localhost:5000/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "923001234567",
            "type": "text",
            "text": {"body": "Hello bot"}
          }]
        }
      }]
    }]
  }'
```

---

## Docker Deployment

### Quick Start with Docker Compose

```bash
# 1. Create .env file
cp .env.example .env

# 2. Start all services (bot + database)
docker-compose up -d

# 3. Check services are running
docker-compose ps

# Expected output:
# NAME                      STATUS
# whatsapp-bot-db           Up 30 seconds (healthy)
# whatsapp-bot-api          Up 15 seconds

# 4. Test health
curl http://localhost:5000/health

# 5. View logs
docker-compose logs -f bot

# 6. Stop services
docker-compose down
```

### Building Custom Image

```bash
# Build image
docker build -t my-whatsapp-bot:latest .

# Run with environment file
docker run -p 5000:5000 \
  --env-file .env \
  my-whatsapp-bot:latest

# Run with individual env vars
docker run -p 5000:5000 \
  -e FLASK_ENV=production \
  -e DATABASE_URL=postgresql://... \
  my-whatsapp-bot:latest
```

### Docker Compose Profiles

```bash
# Start without Redis cache
docker-compose up -d

# Start with Redis cache
docker-compose --profile cache up -d

# Stop all
docker-compose down
```

---

## Cloud Deployments

### Railway (Recommended - Easiest)

Railway automatically deploys from your repository with zero configuration needed.

```bash
# 1. Create Railway account at https://railway.app

# 2. Connect your GitHub repository
#    (Railway reads Dockerfile automatically)

# 3. Railway automatically provides:
#    - Dockerfile support
#    - Environment variables UI
#    - PostgreSQL plugin
#    - Free tier available
#    - Automatic deployments on push

# 4. Set environment variables in Railway dashboard:
#    Go to Variables tab and add all .env variables

# 5. Deploy
#    It automatically deploys on each push to main

# 6. Get your public URL
#    Railway → Deployments → Domain

# 7. Update webhook in Meta/Twilio
#    Webhook: https://<your-railway-domain>/webhook
```

### Render (Free Tier Available)

```bash
# 1. Create Render account at https://render.com

# 2. Create Web Service:
#    - Connect GitHub repo
#    - Runtime: Python 3.11
#    - Build: pip install -r requirements.txt
#    - Start: gunicorn -w 4 -b 0.0.0.0:5000 src.main:create_app()

# 3. Add PostgreSQL database:
#    - Render automatically sets DATABASE_URL

# 4. Add environment variables:
#    Same as .env file

# 5. Deploy
#    Render → Manual Deploy

# 6. Get public URL and update webhook
```

### Self-Hosted VPS

Complete guide at DEPLOYMENT_VPS.md (see appendix)

---

## Production Verification

### Checklist Before Going Live

```bash
# 1. Health check
curl https://your-domain.com/health
# Response: {"status": "ok"}

# 2. Send test message
# From your WhatsApp account, message your business number

# 3. Check bot response
# You should receive: "I received your message"

# 4. Test MFA flow
# Message: "setup mfa"
# Bot should send QR code

# 5. Test stock command
# Message: "stock"
# Bot should return inventory

# 6. Test order placement
# Message: "order"
# Bot should guide through ordering

# 7. Check logs for errors
docker-compose logs bot | grep -i error

# 8. Verify database is working
docker-compose exec bot python -c \
  "from src.core.models import Client; print(Client.query.count())"

# 9. Check performance
curl -w "@curl-format.txt" -o /dev/null -s https://your-domain.com/health
# Should be < 500ms
```

### Production Monitoring

```bash
# View real-time logs
docker-compose logs -f bot

# Check resource usage
docker stats

# Monitor database
docker-compose exec db psql -U botuser -d whatsapp_bot -c \
  "SELECT COUNT(*) as message_count FROM whatsapp_messages;"

# Setup alerts (recommended services)
# - Sentry (errors)
# - DataDog (monitoring)
# - Uptime Robot (uptime checks)
```

---

## Environment Variables

### Minimal Required

```env
# Database (required in production)
DATABASE_URL=postgresql://user:pass@localhost/whatsapp_bot

# Flask
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=<32-char-random-string>

# JWT
JWT_SECRET_KEY=<32-char-random-string>

# WhatsApp Provider (choose one)
WHATSAPP_PROVIDER=twilio # or meta

# Twilio credentials
TWILIO_ACCOUNT_SID=<your-sid>
TWILIO_AUTH_TOKEN=<your-token>
TWILIO_PHONE_NUMBER=+1234567890

# Meta credentials  
META_ACCESS_TOKEN=<your-token>
META_PHONE_NUMBER_ID=<your-id>
META_WEBHOOK_VERIFY_TOKEN=<random-token>

# MFA
MFA_ENABLED=true
TOTP_ENCRYPTION_KEY=<32-character-key>

# Admin contact
ADMIN_PHONE=+923001234567
```

Generate random keys safely:

```python
import secrets

# 32-byte key
print(f"SECRET_KEY={secrets.token_urlsafe(32)}")
print(f"JWT_SECRET_KEY={secrets.token_urlsafe(32)}")

# 16-byte encrypted fields key (base64)
print(f"TOTP_ENCRYPTION_KEY={secrets.token_urlsafe(32)}")
```

---

## Troubleshooting

### "Bot not receiving messages"

```bash
# 1. Check webhook is registered
#    Meta/Twilio Dashboard → Webhook URL should match your domain

# 2. Check bot is running
curl https://your-domain.com/health
# Should return 200 OK

# 3. Check logs for errors
docker-compose logs bot | tail -50

# 4. Webhook verification failed?
#    Check VERIFY_TOKEN matches what's registered
#    Check webhook URL is exactly correct (HTTPS, no typos)

# 5. Test manually
curl -X POST https://your-domain.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"entry":[{"changes":[{"value":{"messages":[{"from":"923001234567","type":"text","text":{"body":"test"}}]}}]}]}'
```

### "Database connection error"

```bash
# Check PostgreSQL is running
docker-compose ps | grep db
# Should show "Up" and "healthy"

# Check DATABASE_URL format
# Should be: postgresql://user:password@host:5432/database

# For Docker Compose, host is: db (service name)
DATABASE_URL=postgresql://botuser:botpassword@db:5432/whatsapp_bot

# Test connection
docker-compose exec db psql -U botuser -d whatsapp_bot -c "SELECT 1"
```

### "500 Internal Server Error"

```bash
# Check bot logs
docker-compose logs bot | tail -100

# Look for Python exceptions (they'll be printed)
# Common issues:
# - Missing environment variables
# - Database not initialized
# - Invalid JWT key format
```

### "CORS errors in browser"

Already configured in `.src/main.py` with Flask-CORS. Should work for all origins in development.

---

## Security Checklist

Before production:

- [ ] All secrets in .env (not in code)
- [ ] HTTPS enabled (SSL certificate)
- [ ] Database password changed from default
- [ ] Admin phone number changed to your phone
- [ ] JWT_SECRET_KEY is cryptographically random
- [ ] TOTP_ENCRYPTION_KEY is set properly
- [ ] Incoming webhooks validated
- [ ] Rate limiting enabled
- [ ] Database backups configured
- [ ] Monitoring/alerting enabled
- [ ] Log aggregation setup
- [ ] No debug mode in production

---

## Performance Tips

### Optimize Gunicorn

```bash
# In docker-compose.yml or Dockerfile
# Formula: (2 × CPU cores) + 1

gunicorn -w 9 -b 0.0.0.0:5000 --timeout 120 src.main:create_app()
```

### Database Connection Pooling

```env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_RECYCLE=3600
```

### Enable Redis Cache

```bash
# In docker-compose.yml
docker-compose --profile cache up -d

# Set in .env
REDIS_URL=redis://redis:6379
```

---

## Next Steps

1. ✅ Run `python test_local.py` to verify local setup
2. ✅ Set up webhook with Twilio or Meta
3. ✅ Deploy following Docker or Cloud section
4. ✅ Update webhook URL in Meta/Twilio dashboard
5. ✅ Send test message and verify receipt
6. ✅ Monitor logs for errors

---

**Questions or issues?** Check DEPLOYMENT_VPS.md for self-hosted setup details.

**Last Updated:** February 2026  
**Version:** 1.0-production
