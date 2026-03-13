#!/usr/bin/env python
"""Local webhook testing script."""

import requests
import time

BASE_URL = "http://127.0.0.1:5000"
TEST_PHONE = "whatsapp:+923108311917"

def test_health():
    """Test health endpoint."""
    print("🏥 Testing health endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            print(f"✅ Health check passed: {r.json()}")
            return True
        else:
            print(f"❌ Health check failed: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_webhook(message, description):
    """Test webhook with a message."""
    print(f"\n📨 Testing: {description}")
    print(f"   Message: '{message}'")
    
    try:
        r = requests.post(
            f"{BASE_URL}/webhook",
            data={
                'Body': message,
                'From': TEST_PHONE
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        if r.status_code == 200:
            # Check if response is TwiML
            if 'Response' in r.text or 'Message' in r.text:
                print(f"✅ Status: {r.status_code}")
                print(f"✅ Content-Type: {r.headers.get('Content-Type')}")
                print(f"📤 Response preview: {r.text[:150]}...")
                return True
            else:
                print(f"❌ Not TwiML format!")
                print(f"   Response: {r.text[:200]}")
                return False
        else:
            print(f"❌ Status: {r.status_code}")
            print(f"   Response: {r.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 WhatsApp Bot - Local Testing")
    print("=" * 60)
    
    # Wait for bot to be ready
    print("\n⏳ Waiting for bot to start...")
    for i in range(10):
        if test_health():
            break
        time.sleep(1)
    else:
        print("\n❌ Bot not responding. Make sure it's running:")
        print("   python AI-CHATBOT/run.py")
        return
    
    print("\n" + "=" * 60)
    print("🧪 Running Webhook Tests")
    print("=" * 60)
    
    # Test cases
    tests = [
        ("hi", "Main menu trigger"),
        ("1", "Check stock"),
        ("2", "Place order prompt"),
        ("order Product A 50", "Create order"),
        ("3", "Price finder"),
        ("product a", "Price lookup"),
        ("4", "View transactions"),
        ("5", "My account"),
        ("6", "Help"),
        ("receipt ORD-001", "Get receipt"),
        ("reorder Product B", "Reorder product"),
        ("buy from supplier 1 Product A 100", "Supplier order"),
        ("unknown command", "Unknown command handling"),
        ("menu", "Back to menu"),
    ]
    
    passed = 0
    failed = 0
    
    for message, description in tests:
        if test_webhook(message, description):
            passed += 1
        else:
            failed += 1
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED - BOT READY FOR DEMO!")
        print("=" * 60)
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
