# 🚀 DEMO DAY DEPLOYMENT GUIDE

## Pre-Demo Checklist (Run This First!)

```bash
python FINAL_CHECKLIST.py
```

This will verify:
- ✅ All files present
- ✅ Environment configured
- ✅ Security settings
- ✅ Webhook format correct
- ✅ All handlers working
- ✅ Bot responding properly

## Quick Start (5 Minutes)

### Step 1: Start the Bot

```bash
cd AI-CHATBOT
python run.py
```

Bot will start on `http://localhost:5000`

### Step 2: Start Ngrok Tunnel

**Option A: Automatic (Recommended)**
```bash
python start_demo.py
```

**Option B: Manual**
```bash
ngrok http 5000
```

Copy the `https://xxxx.ngrok-free.app` URL

### Step 3: Configure Twilio

1. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Find "Sandbox Configuration"
3. In "WHEN A MESSAGE COMES IN" field, paste:
   ```
   https://your-ngrok-url.ngrok-free.app/webhook
   ```
4. Click **Save**

### Step 4: Test Connection

1. Send to Twilio WhatsApp number: `join <your-sandbox-code>`
2. Wait for confirmation
3. Send: `hi`
4. You should see the main menu! 🎉

## Demo Script

### 1. Show Main Menu
```
Send: hi
```
Expected: Main menu with 6 options

### 2. Check Stock
```
Send: 1
```
Expected: Stock list with PKR prices

### 3. Place Order
```
Send: order Product A 50
```
Expected: Order confirmation with total in PKR

### 4. Find Best Price
```
Send: 3
Then: product a
```
Expected: Supplier comparison with prices

### 5. View Transactions
```
Send: 4
```
Expected: Transaction history

### 6. Get Receipt
```
Send: receipt ORD-001
```
Expected: Detailed receipt

### 7. Supplier Order
```
Send: buy from supplier 1 Product A 100
```
Expected: Supplier order confirmation

## Troubleshooting

### Bot Not Responding?

**Check 1: Bot Running?**
```bash
curl http://localhost:5000/health
```
Should return: `{"status": "ok", "bot": "ready"}`

**Check 2: Ngrok Working?**
Visit: http://localhost:4040
Should show ngrok dashboard

**Check 3: Twilio Webhook?**
- Go to Twilio Console
- Check webhook URL is correct
- Check for error logs

**Check 4: Console Logs?**
Look for errors in terminal where bot is running

### Twilio Sending Template Instead of Bot Reply?

This means webhook is not returning TwiML properly.

**Fix:**
1. Stop bot (Ctrl+C)
2. Run: `python FINAL_CHECKLIST.py`
3. Verify "Webhook Format" passes
4. Restart bot

### MFA Issues?

**Bypass MFA for Demo:**
Edit `AI-CHATBOT/whatsapp/message_handler.py`:
```python
# Comment out MFA check temporarily
# if not is_user_authenticated(from_number):
#     return handle_mfa_flow(from_number, message)
```

**Or Complete MFA:**
1. QR code saved as `qr_<phone>.png`
2. Scan with Microsoft Authenticator
3. Send 6-digit code

## Monitoring During Demo

### Terminal 1: Bot Logs
```bash
cd AI-CHATBOT
python run.py
```
Watch for incoming messages and responses

### Terminal 2: Ngrok Dashboard
Visit: http://localhost:4040

Shows all webhook requests in real-time

### Terminal 3: Test Commands
```bash
python AI-CHATBOT/test_local.py
```
Quick verification if something breaks

## Emergency Recovery

### Bot Crashed?
```bash
cd AI-CHATBOT
python run.py
```

### Ngrok Disconnected?
```bash
ngrok http 5000
```
Update Twilio webhook with new URL

### Database Corrupted?
```bash
rm chatbot_data/chatbot.db
# Restart bot - will recreate
```

## Post-Demo

### Stop Services
```bash
# Stop bot: Ctrl+C in bot terminal
# Stop ngrok: Ctrl+C in ngrok terminal
```

### Review Logs
Check console output for any errors

### Backup
```bash
# Save successful configuration
cp .env .env.backup
```

## Production Deployment (After Demo)

### Docker
```bash
cd AI-CHATBOT
docker build -t whatsapp-bot .
docker run -p 5000:5000 --env-file ../.env whatsapp-bot
```

### Railway
```bash
railway init
railway up
# Set environment variables in Railway dashboard
```

### Heroku
```bash
heroku create your-bot-name
git push heroku main
heroku config:set TWILIO_ACCOUNT_SID=xxx
heroku config:set TWILIO_AUTH_TOKEN=xxx
```

## Support Contacts

- Twilio Support: https://support.twilio.com
- Ngrok Docs: https://ngrok.com/docs
- Bot Issues: Check console logs first

## Final Checklist Before Demo

- [ ] Bot running on localhost:5000
- [ ] Ngrok tunnel active
- [ ] Twilio webhook configured
- [ ] Test message sent successfully
- [ ] All 6 menu options tested
- [ ] Order creation works
- [ ] Prices showing in PKR
- [ ] No errors in console
- [ ] Backup terminal ready
- [ ] Phone charged and ready 📱

---

**Good luck with your demo! 🚀**

If everything is green in `FINAL_CHECKLIST.py`, you're ready to go!
