#!/usr/bin/env python
"""Quick verification - checks critical items only."""

import sys
from pathlib import Path

print("=" * 60)
print("  QUICK VERIFICATION - Critical Items Only")
print("=" * 60)

errors = []
warnings = []

# Check critical files
critical_files = [
    "AI-CHATBOT/run.py",
    "AI-CHATBOT/whatsapp/message_handler.py",
    "AI-CHATBOT/whatsapp/handlers.py",
    "AI-CHATBOT/whatsapp/menu.py",
    ".env",
]

print("\n[1/5] Checking critical files...")
for f in critical_files:
    if not Path(f).exists():
        errors.append(f"Missing: {f}")
    else:
        print(f"  [OK] {f}")

# Check webhook has TwiML
print("\n[2/5] Checking webhook format...")
try:
    run_py = Path("AI-CHATBOT/run.py").read_text(encoding='utf-8')
    if 'Content-Type": "text/xml"' in run_py:
        print("  [OK] Returns Content-Type: text/xml")
    else:
        errors.append("Webhook missing Content-Type: text/xml")
    
    if "MessagingResponse" in run_py:
        print("  [OK] Uses MessagingResponse")
    else:
        errors.append("Webhook missing MessagingResponse")
except Exception as e:
    errors.append(f"Cannot read run.py: {e}")

# Check handlers exist
print("\n[3/5] Checking handlers...")
try:
    handlers = Path("AI-CHATBOT/whatsapp/handlers.py").read_text(encoding='utf-8')
    required = ["handle_price_lookup", "handle_reorder", "handle_receipt", "handle_supplier_buy"]
    for h in required:
        if f"def {h}" in handlers:
            print(f"  [OK] {h}")
        else:
            errors.append(f"Missing handler: {h}")
except Exception as e:
    errors.append(f"Cannot read handlers.py: {e}")

# Check .env
print("\n[4/5] Checking environment...")
try:
    env_content = Path(".env").read_text()
    if "TWILIO_ACCOUNT_SID" in env_content:
        print("  [OK] TWILIO_ACCOUNT_SID configured")
    else:
        warnings.append("TWILIO_ACCOUNT_SID not in .env")
    
    if "TWILIO_AUTH_TOKEN" in env_content:
        print("  [OK] TWILIO_AUTH_TOKEN configured")
    else:
        warnings.append("TWILIO_AUTH_TOKEN not in .env")
except Exception as e:
    errors.append(f"Cannot read .env: {e}")

# Check .gitignore
print("\n[5/5] Checking security...")
try:
    gitignore = Path(".gitignore").read_text()
    if ".env" in gitignore:
        print("  [OK] .env in .gitignore")
    else:
        errors.append(".env not in .gitignore - SECURITY RISK!")
except Exception as e:
    warnings.append(f"Cannot read .gitignore: {e}")

# Summary
print("\n" + "=" * 60)
print("  SUMMARY")
print("=" * 60)

if errors:
    print(f"\n[FAIL] {len(errors)} critical error(s):")
    for e in errors:
        print(f"  - {e}")

if warnings:
    print(f"\n[WARN] {len(warnings)} warning(s):")
    for w in warnings:
        print(f"  - {w}")

if not errors and not warnings:
    print("\n[PASS] All critical checks passed!")
    print("\nNext steps:")
    print("1. cd AI-CHATBOT")
    print("2. python run.py")
    print("3. In another terminal: ngrok http 5000")
    print("4. Configure Twilio webhook with ngrok URL")
    print("5. Test by sending 'hi' to bot")
    sys.exit(0)
elif not errors:
    print("\n[PASS] Critical checks passed (warnings can be ignored for demo)")
    sys.exit(0)
else:
    print("\n[FAIL] Fix errors above before demo!")
    sys.exit(1)
