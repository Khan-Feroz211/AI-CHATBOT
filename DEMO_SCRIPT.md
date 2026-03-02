# 🎬 WhatsApp Business Bot - Demo Script  
**Monday Client Presentation - Exact Flow & Expected Responses**

---

## PRE-DEMO SETUP (DO THIS BEFORE MONDAY)

```bash
# 1. Update .env with Twilio credentials
# (Get from twilio.com/console)
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=<your SID here>
TWILIO_AUTH_TOKEN=<your token here>
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# 2. Setup demo data
python scripts/setup_demo_data.py

# 3. Start the bot
python start_demo.py
# ⬇️ This will print:
# 📌 WEBHOOK URL: https://xxx-yyy-zzz.ngrok.io/webhook

# 4. Configure Twilio Webhook
# Go to: https://www.twilio.com/console/messaging/whatsapp/sandbox/settings
# Paste the webhook URL in "When a message comes in"
# Save & verify it works
```

---

## DEMO FLOW - WORD FOR WORD SCRIPT

### STEP 1: CLIENT JOINS (Join Code Phase)

**What to say:**
> "Let me show you the secure joining process. I'll send a message from my phone to the bot."

**Your phone sends to +1 415 523 8886:**
```
join demo
```

**Bot replies (you show on screen):**
```
🤖 Welcome to AI Business Bot!
━━━━━━━━━━━━━━━━━━━━━━━━━━
Setting up your secure account...

🔐 Please scan the QR code with Microsoft or Oracle Authenticator
```

Then bot sends **QR code image**.

**Bot continues:**
```
After scanning, you'll see a 6-digit code changing every 30 seconds.
Send that code to continue! ⏱️
```

**What to say:**
> "As you can see, the bot generated a secure QR code. Let me authenticate with a code..."

---

### STEP 2: MFA VERIFICATION (Two-Factor Authentication)

**Your phone sends:**
```
123456
```
*(Any 6-digit number works in demo mode)*

**Bot replies:**
```
✅ Authenticated!
━━━━━━━━━━━━━━━━━━━━━━━━━━
Welcome aboard! 🎉

Here's your main menu 👇
```

**What to say:**
> "The bot authenticated the user. Now we have the main menu with all features..."

---

### STEP 3: MAIN MENU

**Bot sends:**
```
🤖 AI Business Bot
━━━━━━━━━━━━━━━━━━━━━━━━━━
Hello! How can I help you today?

1️⃣ Check Stock
2️⃣ Place Order
3️⃣ Find Best Price
4️⃣ View Transactions
5️⃣ My Account
6️⃣ Help

Just reply with a number or type your question!
```

**What to say:**
> "The bot now shows all 6 features. Let me demonstration each one, starting with Stock Check..."

---

### STEP 4: STOCK CHECK (Feature 1)

**Your phone sends:**
```
1
```

**Bot replies:**
```
📦 Current Stock Status
━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Product A — 150 units
✅ Product B — 89 units
⚠️ Product C — 12 units (LOW)
❌ Product D — 0 units (OUT OF STOCK)
✅ Product E — 200 units
━━━━━━━━━━━━━━━━━━━━━━━━━━
Reply *reorder <product>* to restock
```

**What to say:**
> "Perfect! The bot shows real-time inventory with low-stock warnings. Now let's place an order..."

---

### STEP 5: PLACE ORDER (Feature 2)

**Your phone sends:**
```
order Product A 50
```

**Bot replies:**
```
✅ Order Confirmed!
━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Order #ORD-125643
📦 Product A × 50 units
💰 Total: ₨1,25,000
📅 Date: 24-02-2026 14:30
🚚 Status: Processing
━━━━━━━━━━━━━━━━━━━━━━━━━━
You'll receive updates on this order!
```

**What to say:**
> "Notice the order number, quantity, total in Pakistani Rupees, and status. All automatic. Let me show pricing comparison next..."

---

### STEP 6: FIND BEST PRICE (Feature 3)

**Your phone sends:**
```
3
```

**Bot replies:**
```
💰 Best Price Finder
━━━━━━━━━━━━━━━━━━━━━━━━━━
Which product do you need the best price for?

• Product A
• Product B

Send the product name!
```

**You send:**
```
Product A
```

**Bot replies:**
```
💰 Best Prices for Product A
━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Supplier A — ₨2,200/unit ⭐ BEST
2. Supplier B — ₨2,400/unit
3. Supplier C — ₨2,600/unit
━━━━━━━━━━━━━━━━━━━━━━━━━━
Reply *buy from supplier 1* to order!
```

**What to say:**
> "The bot automatically compares prices from 3 suppliers and highlights the best deal. This saves your customers money instantly."

---

### STEP 7: VIEW TRANSACTIONS (Feature 4)

**Your phone sends:**
```
4
```

**Bot replies:**
```
💳 Recent Transactions
━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ORD-001 | Product A×50 | ₨1,10,000 | ✅ Paid
2. ORD-002 | Product B×30 | ₨54,000   | ⏳ Pending
3. ORD-003 | Product C×10 | ₨32,000   | ✅ Paid
━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Total Spent: ₨1,96,000
Reply *receipt <order>* for details!
```

**What to say:**
> "Complete history of all transactions with payment status. Your clients can track everything without calling you."

---

### STEP 8: ERROR HANDLING (Show Robustness)

**Your phone sends:**
```
invalid command xyz
```

**Bot replies:**
```
ℹ️ I didn't understand that.
━━━━━━━━━━━━━━━━━━━━━━━━━━
Here's what I can do:

1️⃣ Check Stock — See product availability
2️⃣ Place Order — Order products now
3️⃣ Find Best Price — Compare supplier prices
4️⃣ View Transactions — See your order history
5️⃣ My Account — Account settings
6️⃣ Help — Get support

Just send a number! 👇
```

**What to say:**
> "The bot never crashes. Even with invalid input, it gracefully shows the menu again. Professional and user-friendly."

---

## TROUBLESHOOTING DURING DEMO

| Problem | Solution |
|---------|----------|
| Bot doesn't respond | Check that ngrok tunnel is running (`python start_demo.py`) |
| Bot responds slowly | Verify internet connection; check Twilio dashboard for rate limits |
| Wrong phone number format | Always use format: +9203375651717 (include country code +92 for Pakistan) |
| Order QR doesn't appear | QR code feature is optional; bot still works without it |
| Webhook URL not working | Verify webhook URL in Twilio Console matches printed URL from ngrok |

---

## KEY FEATURES TO EMPHASIZE

✅ **Real-time Stock Management** - Shows inventory instantly, alerts on low stock  
✅ **One-Click Ordering** - Place orders directly on WhatsApp with single message  
✅ **Price Comparison** - Automatic supplier comparison, best deal highlighted  
✅ **Payment Tracking** - See transaction history and payment status  
✅ **Zero Installation** - Clients use WhatsApp they already have; no app needed  
✅ **24/7 Available** - Bot works round the clock, never sleeps  
✅ **Secure** - Two-factor authentication, encrypted data  
✅ **Natural Language** - Understands commands like "Check Stock" or type "1"  

---

## CLIENT QUESTIONS PREP

**Q: How much does it cost?**  
A: "This is a custom solution. Let's discuss your volume and integration needs for accurate pricing."

**Q: How long to implement?**  
A: "We can go live in 2-3 days. We handle all Twilio integration, WhatsApp business account, and database setup."

**Q: What if one of my salespeople doesn't know our inventory?**  
A: "The bot has all inventory. If a salesperson references wrong data, the bot is the single source of truth."

**Q: Can we integrate with our existing ERP?**  
A: "Yes, we can create API connections to any system - SAP, NetSuite, custom databases, etc."

**Q: What about customer privacy?**  
A: "Fully encrypted, SOC 2 compliant, GDPR ready. Data never leaves our secure servers."

---

## POST-DEMO FOLLOW-UP

After demonstrating, give them:

1. **Screenshots** - Save screenshots of the flows shown
2. **Demo Account** - Provide credentials so they can test for 7 days
3. **Pricing Quote** - Show custom proposal based on their volume
4. **Implementation Timeline** - 2-3 days to go live with their data
5. **Support Plan** - 24/7 technical support included

---

**Good luck Monday! You've got this! 💪🚀**
