import requests
import sys

print("=" * 60)
print("  TROUBLESHOOTING - NO RESPONSE FROM BOT")
print("=" * 60)

# Check 1: Is bot running?
print("\n[1] Checking if bot is running...")
try:
    r = requests.get("http://localhost:5000/health", timeout=3)
    if r.status_code == 200:
        print("    [OK] Bot is running!")
        print(f"    Response: {r.json()}")
    else:
        print(f"    [FAIL] Bot returned status {r.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"    [FAIL] Bot is NOT running!")
    print(f"    Error: {e}")
    print("\n    FIX: Start bot with:")
    print("    cd AI-CHATBOT")
    print("    python run.py")
    sys.exit(1)

# Check 2: Test webhook locally
print("\n[2] Testing webhook locally...")
try:
    r = requests.post(
        "http://localhost:5000/webhook",
        data={'Body': 'hi', 'From': 'whatsapp:+923001234567'},
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=5
    )
    
    print(f"    Status: {r.status_code}")
    print(f"    Content-Type: {r.headers.get('Content-Type')}")
    
    if r.status_code == 200:
        if 'text/xml' in r.headers.get('Content-Type', ''):
            print("    [OK] Webhook returns TwiML!")
            print(f"    Response length: {len(r.text)} chars")
        else:
            print("    [FAIL] Wrong Content-Type!")
            print(f"    Response: {r.text[:200]}")
    else:
        print(f"    [FAIL] Webhook error!")
        print(f"    Response: {r.text[:200]}")
        
except Exception as e:
    print(f"    [FAIL] Webhook test failed!")
    print(f"    Error: {e}")

# Check 3: Ngrok status
print("\n[3] Checking ngrok...")
try:
    r = requests.get("http://localhost:4040/api/tunnels", timeout=3)
    tunnels = r.json()
    if tunnels.get('tunnels'):
        public_url = tunnels['tunnels'][0]['public_url']
        print(f"    [OK] Ngrok is running!")
        print(f"    Public URL: {public_url}")
        print(f"\n    USE THIS IN TWILIO:")
        print(f"    {public_url}/webhook")
    else:
        print("    [FAIL] No tunnels found!")
except Exception as e:
    print(f"    [FAIL] Ngrok is NOT running!")
    print(f"    Error: {e}")
    print("\n    FIX: Start ngrok with:")
    print("    ngrok http 5000")

print("\n" + "=" * 60)
print("  COMMON ISSUES & FIXES")
print("=" * 60)
print("\nISSUE 1: Bot not running")
print("  FIX: cd AI-CHATBOT && python run.py")
print("\nISSUE 2: Ngrok not running")
print("  FIX: ngrok http 5000")
print("\nISSUE 3: Wrong webhook URL in Twilio")
print("  FIX: Use the ngrok URL shown above")
print("\nISSUE 4: MFA blocking messages")
print("  FIX: Edit AI-CHATBOT/whatsapp/message_handler.py")
print("       Comment out lines 16-17")
print("\nISSUE 5: Twilio webhook errors")
print("  FIX: Check Twilio console logs")
print("       https://console.twilio.com")
