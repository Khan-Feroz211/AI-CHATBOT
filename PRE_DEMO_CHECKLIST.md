# ✅ PRE-DEMO CHECKLIST  
**Monday Client Presentation - Verification Checklist**

*Complete these before Monday. Check them off as you go.*

---

## 🔧 SETUP & INSTALLATION

- [ ] **Twilio Account Created**
  - Go to: https://www.twilio.com
  - Verify your phone number
  - Save: Account SID, Auth Token, Twilio WhatsApp Sandbox number

- [ ] **.env File Configured**
  - Fill in Twilio credentials from above
  - Save file (Ctrl+S)
  - Check: WHATSAPP_PROVIDER=twilio
  - Check: TWILIO_ACCOUNT_SID is not empty
  - Check: TWILIO_AUTH_TOKEN is not empty

- [ ] **Python Environment Ready**
  - Virtual environment activated
  - All dependencies installed: `pip install -r requirements.txt`
  - No error messages

- [ ] **ngrok Installed & Working**
  - Download from: https://ngrok.com/download
  - Test: `ngrok --version` in terminal
  - Should show version (e.g., "ngrok 3.3.1")

---

## 📊 DEMO DATA SETUP

- [ ] **Run Demo Data Script**
  ```bash
  python scripts/setup_demo_data.py
  ```
  - Should show: ✅ Demo Products created
  - Should show: ✅ Demo Suppliers created
  - Should show: ✅ Demo Transactions created
  - Should show: ✅ Demo Admin Account created

- [ ] **Database File Created**
  - File exists: `chatbot_data/chatbot.db`
  - File size > 0 KB
  - No database errors in logs

---

## 🚀 BOT STARTUP TEST

- [ ] **Start Demo Bot**
  ```bash
  python start_demo.py
  ```
  
  **Should see:**
  - ✅ Flask bot started (PID: xxxxx)
  - ✅ ngrok tunnel started (PID: xxxxx)
  - ✅ Webhook URL printed: https://xxx-yyy-zzz.ngrok.io/webhook

- [ ] **Webhook URL Visible**
  - Copy the webhook URL from console
  - Example: `https://4d08-203-0-113-1.ngrok-free.app/webhook`
  - URL is HTTPS (not HTTP)
  - URL is NOT localhost

---

## 🔐 TWILIO WEBHOOK CONFIGURATION

- [ ] **Configure Webhook in Twilio Console**
  1. Go to: https://www.twilio.com/console
  2. Navigate: Messaging → Try it out → Send a WhatsApp message
  3. Under "Set up inbound request URL":
     - Paste webhook URL from above
     - Select Method: POST
     - Click Save

- [ ] **Verify Webhook Connection**
  1. Still in Twilio console
  2. Click "Verify" or "Test"
  3. Should show: ✅ Webhook detected

---

## 📱 SEND TEST MESSAGES

**Before these tests: SAVE +14155238886 as "AI Bot" in your phone contacts**

- [ ] **Test: Join Code**
  - From your WhatsApp, send to +1 415 523 8886:
    ```
    join demo
    ```
  - Bot should reply: "Welcome to AI Business Bot!"
  - Bot should send QR code message

- [ ] **Test: MFA Code**
  - From your WhatsApp, send:
    ```
    123456
    ```
  - Bot should reply: "✅ Authenticated!"
  - Bot should send main menu

- [ ] **Test: Stock Check**
  - Send:
    ```
    1
    ```
  - Bot should reply with 5 products and stock levels
  - Should show ✅, ⚠️, ❌ icons

- [ ] **Test: Place Order**
  - Send:
    ```
    order Product A 50
    ```
  - Bot should confirm order with:
    - Order number (ORD-xxxxx)
    - Product name and quantity
    - Total in ₨ (Pakistani Rupees format)
    - Current timestamp

- [ ] **Test: Price Comparison**
  - Send:
    ```
    3
    ```
  - Bot asks: "Which product?"
  - You send:
    ```
    Product A
    ```
  - Bot shows 3 suppliers with pricing
  - Should show ⭐ BEST next to lowest price

- [ ] **Test: Transaction History**
  - Send:
    ```
    4
    ```
  - Bot shows 3 previous orders
  - All amounts in ₨ format
  - Shows payment status (✅ Paid or ⏳ Pending)
  - Shows total spent: ₨1,96,000

- [ ] **Test: Error Handling**
  - Send random text:
    ```
    xyz invalid hello random
    ```
  - Bot should NOT crash
  - Bot should show helpful menu
  - No error messages in console

---

## 💰 CURRENCY VERIFICATION

- [ ] **All Prices in PKR Format**
  - Check demo_handlers.py uses format_pkr()
  - Check formatters.py shows ₨ symbol (not $)
  - Check database prices are in PKR ranges:
    - Product A: ₨2,500
    - Product B: ₨1,800
    - Product C: ₨3,200

- [ ] **Test Currency Display**
  - Send: `1` (stock check)
  - Look at order confirmations
  - All money should show as: ₨1,25,000 (not $125,000)

---

## 🎯 HARDWARE & CONNECTIVITY

- [ ] **Laptop Battery**
  - Charge to 100%
  - Close unnecessary background apps
  - Have charger nearby

- [ ] **Phone Battery**
  - Charge to 100%
  - Mobile data or WiFi working
  - WhatsApp messaging tested before demo

- [ ] **Internet Connection**
  - WiFi is stable (not mobile hotspot if possible)
  - Test speed: https://speedtest.net (10+ Mbps recommended)
  - Backup: Have mobile hotspot as failsafe

- [ ] **Monitor/Projector Setup**
  - Resolution set correctly
  - Font sizes readable from 10 feet away
  - Demo on laptop screen, not phone

---

## 📂 FILES & DOCUMENTATION

- [ ] **DEMO_SCRIPT.md Printed or Open**
  - Have on second monitor or printed
  - Quick reference during demo

- [ ] **Terminal Window Visible**
  - Show webhook URL when bot starts
  - Can reference logs if issues arise

- [ ] **WhatsApp Screenshot Tool Ready**
  - Have screenshot capability
  - Can capture good moments during demo

---

## ⏰ TIMING REHEARSAL

- [ ] **Run Full Demo Dry-Run (Time it)**
  
  | Step | Time | Notes |
  |------|------|-------|
  | Bot startup | 10 sec | Including ngrok |
  | Join + MFA | 30 sec | Send 2 messages |
  | Stock check | 10 sec | Send "1" |
  | Place order | 10 sec | Send "order Product A 50" |
  | Price compare | 20 sec | Send "3", then product name |
  | Transactions | 10 sec | Send "4" |
  | Q&A | 10 min | Client questions |
  | **TOTAL** | **~12 minutes** | Plus buffer time |

- [ ] **Full dry-run completed successfully**
- [ ] **No errors, no crashes, all messages received**
- [ ] **Timing is comfortable (not rushed)**

---

## 🎬 PRESENTATION SETUP

- [ ] **Open Necessary Files**
  - [ ] DEMO_SCRIPT.md (on second screen or printed)
  - [ ] Terminal with bot running
  - [ ] WhatsApp open on phone
  - [ ] Client contact (+1 415 523 8886) saved as "AI Bot"

- [ ] **Close Distractions**
  - [ ] Close Slack, email, notifications
  - [ ] Turn off phone vibrations
  - [ ] Close unnecessary browser tabs
  - [ ] Hide personal files from desktop

- [ ] **Practice Your Words**
  - [ ] Read DEMO_SCRIPT.md once before Monday
  - [ ] Practice saying it aloud (2-3 times)
  - [ ] Know the 6 features cold
  - [ ] Know how to handle each question

---

## ❌ IF SOMETHING BREAKS DURING DEMO

| Error | Fix | Fallback |
|-------|-----|----------|
| Bot not responding | Restart: Stop bot, run `python start_demo.py` again | Show screenshots of previous test |
| Webhook error | Verify Twilio webhook URL matches ngrok URL | Manually show conversation flows |
| Message takes 10+ sec | Check internet speed, restart ngrok | Explain this is demo env, production is real-time |
| QR code doesn't show | Skip it - not essential for demo | Continue with manual entering auth code |
| Wrong currency showing | Quick check: formatters.py uses ₨ | Explain feature, show code |

**REMEMBER: Have backup screenshots ready!**

---

## ✨ BONUS: WHAT IMPRESSES CLIENTS

- [ ] **Show the code briefly** (git open) - builds confidence
- [ ] **Explain Pakistani payments** (JazzCash, EasyPaisa integration ready)
- [ ] **Mention 24/7 support** - we're available when they need help
- [ ] **Security features** - MFA, encrypted, SOC 2 compliant
- [ ] **Local currency** - Not US dollars, prices in ₨ PKR

---

## 📋 FINAL CHECKLIST (DO THIS SUNDAY NIGHT)

- [ ] **All tests passed** - Every feature works
- [ ] **All files saved** - No unsaved changes
- [ ] **.env has real Twilio credentials** - Not placeholders
- [ ] **Demo data loaded** - Database has products/suppliers/transactions
- [ ] **ngrok ready to start** - Version 3.1+ installed
- [ ] **Phone charged** - 100% battery
- [ ] **Laptop charged** - Plugged in during demo
- [ ] **Do NOT update anything new**  - Only run tested code
- [ ] **Screenshot folder ready** - For post-demo documentation

---

## 🎯 SUNDAY NIGHT (BEFORE BED)

**Run these ONE MORE TIME to verify everything:**

```bash
# 1. Check bot starts without errors
python start_demo.py

# 2. Let it run for 30 seconds, confirm:
#    ✅ Flask bot started
#    ✅ ngrok tunnel started  
#    ✅ Webhook URL printed

# 3. Press Ctrl+C to stop

# 4. Verify demo data exists
ls -la chatbot_data/chatbot.db  # Should show file exists

# 5. Verify all Python files compile
python -m py_compile src/**/*.py  # No errors

# 6. Check .env file (don't print secrets)
grep "WHATSAPP_PROVIDER\|TWILIO" .env

# 7. All good ✅ - SLEEP WELL!
```

---

## 🎬 MONDAY MORNING (1 HOUR BEFORE CALL)

1. **Charge everything** - Laptop + Phone to 100%
2. **Restart laptop** - Fresh start, no background issues
3. **Start bot** - `python start_demo.py` and keep it running
4. **Test one message** - Send "1" from WhatsApp, verify bot responds
5. **Close everything else** - Only terminal, WhatsApp, and DEMO_SCRIPT open
6. **Take 3 deep breaths** - You're going to crush it! 🚀

---

**✅ ALL DONE? YOU'RE READY TO IMPRESS ON MONDAY!**

Good luck! 🎉
