#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Final Pre-Delivery Checklist - Verify everything before demo."""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def check_item(description, passed):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {description}")
    return passed

def check_files():
    """Check all required files exist."""
    print_header("PART 1: FILE STRUCTURE CHECK")
    
    required_files = [
        "AI-CHATBOT/run.py",
        "AI-CHATBOT/requirements.txt",
        "AI-CHATBOT/Dockerfile",
        "AI-CHATBOT/README.md",
        "AI-CHATBOT/auth/mfa_whatsapp.py",
        "AI-CHATBOT/whatsapp/message_handler.py",
        "AI-CHATBOT/whatsapp/handlers.py",
        "AI-CHATBOT/whatsapp/menu.py",
        "AI-CHATBOT/test_local.py",
        "AI-CHATBOT/start_demo.py",
        ".env",
        ".env.example",
        ".gitignore",
    ]
    
    all_exist = True
    for file in required_files:
        exists = Path(file).exists()
        check_item(f"File exists: {file}", exists)
        all_exist = all_exist and exists
    
    return all_exist

def check_env():
    """Check .env configuration."""
    print_header("PART 2: ENVIRONMENT CONFIGURATION")
    
    # Load .env file
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    required_vars = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_WHATSAPP_NUMBER",
        "SECRET_KEY",
        "ADMIN_PHONE_NUMBER",
    ]
    
    all_set = True
    for var in required_vars:
        value = os.environ.get(var, "")
        is_set = len(value) > 0 and "your_" not in value.lower() and "change" not in value.lower()
        check_item(f"Environment variable: {var}", is_set)
        all_set = all_set and is_set
    
    return all_set

def check_gitignore():
    """Check .gitignore has sensitive files."""
    print_header("PART 3: SECURITY CHECK")
    
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        check_item(".gitignore exists", False)
        return False
    
    content = gitignore_path.read_text()
    
    required_entries = [
        ".env",
        "*.db",
        "qr_codes/",
        "__pycache__/",
        ".venv",
    ]
    
    all_present = True
    for entry in required_entries:
        present = entry in content
        check_item(f".gitignore contains: {entry}", present)
        all_present = all_present and present
    
    return all_present

def check_webhook_format():
    """Check webhook returns TwiML format."""
    print_header("PART 4: WEBHOOK FORMAT CHECK")
    
    run_py = Path("AI-CHATBOT/run.py").read_text(encoding='utf-8')
    
    checks = [
        ('Content-Type": "text/xml"' in run_py, "Returns Content-Type: text/xml"),
        ("MessagingResponse" in run_py, "Uses MessagingResponse"),
        ("traceback" in run_py, "Has error handling"),
        ("/health" in run_py, "Has health endpoint"),
    ]
    
    all_passed = True
    for passed, desc in checks:
        check_item(desc, passed)
        all_passed = all_passed and passed
    
    return all_passed

def check_message_router():
    """Check message router has all handlers."""
    print_header("PART 5: MESSAGE ROUTER CHECK")
    
    handler_py = Path("AI-CHATBOT/whatsapp/message_handler.py").read_text(encoding='utf-8')
    
    required_handlers = [
        "handle_stock",
        "handle_order_create",
        "handle_price_lookup",
        "handle_transactions",
        "handle_reorder",
        "handle_receipt",
        "handle_supplier_buy",
        "handle_unknown",
    ]
    
    all_present = True
    for handler in required_handlers:
        present = handler in handler_py
        check_item(f"Handler: {handler}", present)
        all_present = all_present and present
    
    return all_present

def check_handlers_exist():
    """Check all handler functions exist."""
    print_header("PART 6: HANDLER FUNCTIONS CHECK")
    
    handlers_py = Path("AI-CHATBOT/whatsapp/handlers.py").read_text(encoding='utf-8')
    
    required_functions = [
        "handle_price_lookup",
        "handle_reorder",
        "handle_receipt",
        "handle_supplier_buy",
    ]
    
    all_present = True
    for func in required_functions:
        present = f"def {func}" in handlers_py
        check_item(f"Function: {func}", present)
        all_present = all_present and present
    
    return all_present

def check_bot_running():
    """Check if bot is running and responding."""
    print_header("PART 7: BOT RUNTIME CHECK")
    
    try:
        r = requests.get("http://localhost:5000/health", timeout=5)
        health_ok = r.status_code == 200
        check_item("Bot is running", health_ok)
        
        if health_ok:
            data = r.json()
            check_item(f"Health status: {data.get('status')}", data.get('status') == 'ok')
        
        return health_ok
    except Exception as e:
        check_item("Bot is running", False)
        print(f"   Error: {e}")
        print("   Start bot with: python AI-CHATBOT/run.py")
        return False

def check_webhook_responses():
    """Check webhook returns proper TwiML."""
    print_header("PART 8: WEBHOOK RESPONSE CHECK")
    
    test_messages = [
        ("hi", "Main menu"),
        ("1", "Stock check"),
        ("order Product A 50", "Order creation"),
    ]
    
    all_passed = True
    for message, desc in test_messages:
        try:
            r = requests.post(
                "http://localhost:5000/webhook",
                data={'Body': message, 'From': 'whatsapp:+923001234567'},
                timeout=5
            )
            
            is_twiml = 'Response' in r.text or 'Message' in r.text
            is_xml = r.headers.get('Content-Type', '').startswith('text/xml')
            passed = r.status_code == 200 and is_twiml and is_xml
            
            check_item(f"{desc}: TwiML response", passed)
            all_passed = all_passed and passed
            
        except Exception as e:
            check_item(f"{desc}: TwiML response", False)
            print(f"   Error: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Run all checks."""
    print("=" * 60)
    print("  FINAL PRE-DELIVERY CHECKLIST - WhatsApp Bot")
    print("=" * 60)
    
    results = []
    
    # Run all checks
    results.append(("File Structure", check_files()))
    results.append(("Environment Config", check_env()))
    results.append(("Security (.gitignore)", check_gitignore()))
    results.append(("Webhook Format", check_webhook_format()))
    results.append(("Message Router", check_message_router()))
    results.append(("Handler Functions", check_handlers_exist()))
    
    # Runtime checks (optional if bot not running)
    print("\n" + "!" * 60)
    print("RUNTIME CHECKS - Bot must be running for these tests")
    print("Start bot in another terminal: python AI-CHATBOT/run.py")
    print("!" * 60)
    
    response = input("\nPress Enter when bot is running (or type 'skip' to skip): ")
    
    if response.lower() != 'skip':
        results.append(("Bot Running", check_bot_running()))
        results.append(("Webhook Responses", check_webhook_responses()))
    
    # Summary
    print_header("FINAL SUMMARY")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")
    
    print(f"\nScore: {passed}/{total}")
    
    if passed == total:
        print("\n" + "=" * 60)
        print("   BOT READY FOR DELIVERY TOMORROW!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run: python AI-CHATBOT/start_demo.py")
        print("2. Configure Twilio webhook with ngrok URL")
        print("3. Test with real WhatsApp messages")
        print("4. Demo is ready!")
    else:
        print("\n! ISSUES FOUND - Fix the failed checks above")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nChecklist interrupted")
        sys.exit(0)
