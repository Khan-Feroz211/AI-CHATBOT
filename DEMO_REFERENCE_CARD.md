# 🎯 DEMO DAY QUICK REFERENCE CARD

## START BOT (Choose One)

### Option 1: Automatic (Recommended)
```bash
cd AI-CHATBOT
python start_demo.py
```

### Option 2: Manual
```bash
# Terminal 1
cd AI-CHATBOT
python run.py

# Terminal 2
ngrok http 5000
```

## CONFIGURE TWILIO
1. Copy ngrok URL: `https://xxxx.ngrok-free.app`
2. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
3. Paste: `https://xxxx.ngrok-free.app/webhook`
4. Save

## DEMO COMMANDS (Copy-Paste Ready)

```
hi
1
order Product A 50
3
product a
4
receipt ORD-001
buy from supplier 1 Product A 100
reorder Product C
menu
```

## EMERGENCY COMMANDS

### Check Bot Health
```bash
curl http://localhost:5000/health
```

### Restart Bot
```bash
cd AI-CHATBOT
python run.py
```

### Restart Ngrok
```bash
ngrok http 5000
```

### Quick Verification
```bash
python QUICK_CHECK.py
```

## TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Bot not responding | `curl http://localhost:5000/health` |
| Ngrok disconnected | Restart ngrok, update Twilio webhook |
| Wrong responses | Check console for errors |
| MFA blocking | Comment out lines 16-17 in message_handler.py |

## MONITORING URLS

- Bot: http://localhost:5000
- Health: http://localhost:5000/health
- Ngrok: http://localhost:4040
- Twilio: https://console.twilio.com

## EXPECTED RESPONSES

| Command | Response Includes |
|---------|-------------------|
| hi | Main menu with 6 options |
| 1 | Stock list, PKR prices |
| order Product A 50 | Order #, ₨125,000 total |
| 3 | Price finder menu |
| product a | 3 suppliers, best price |
| 4 | Transaction history |
| receipt ORD-001 | Detailed receipt |

---
**Print this card and keep it handy during demo! 📋**
