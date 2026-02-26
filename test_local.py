#!/usr/bin/env python
"""
Local WhatsApp Bot Testing Script
Simulates WhatsApp messages and tests full bot flow including MFA
"""

import json
import os
import sys
from pathlib import Path

import requests

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class WhatsAppBotTester:
    """Test WhatsApp bot locally."""

    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.webhook_url = f"{base_url}/webhook"
        self.test_phone = "+923001234567"

    def test_health(self):
        """Test health endpoint."""
        print("\n🏥 Testing Health Endpoint...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Health check passed: {response.json()}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False

    def test_webhook_verification(self):
        """Test webhook verification token."""
        print("\n🔐 Testing Webhook Verification...")
        verify_token = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "test-token")

        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": verify_token,
            "hub.challenge": "challenge_123",
        }

        try:
            response = requests.get(self.webhook_url, params=params, timeout=5)
            if response.status_code == 200 and response.text == "challenge_123":
                print(f"✅ Webhook verification passed")
                return True
            else:
                print(f"❌ Webhook verification failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Webhook verification error: {str(e)}")
            return False

    def test_text_message(self):
        """Test receiving text message."""
        print("\n💬 Testing Text Message...")

        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": self.test_phone.replace("+", ""),
                                        "type": "text",
                                        "text": {"body": "Hello bot"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            print(f"✅ Text message sent: {response.status_code}")
            return response.status_code in [200, 202]
        except Exception as e:
            print(f"❌ Text message error: {str(e)}")
            return False

    def test_mfa_setup(self):
        """Test MFA setup flow."""
        print("\n🔐 Testing MFA Setup Flow...")

        # This would test the MFA setup endpoint if available
        # For now, we're just simulating the message
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": self.test_phone.replace("+", ""),
                                        "type": "text",
                                        "text": {"body": "setup mfa"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            print(f"✅ MFA setup message processed: {response.status_code}")
            return response.status_code in [200, 202]
        except Exception as e:
            print(f"❌ MFA setup error: {str(e)}")
            return False

    def test_stock_command(self):
        """Test stock command."""
        print("\n📦 Testing Stock Command...")

        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": self.test_phone.replace("+", ""),
                                        "type": "text",
                                        "text": {"body": "stock"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            print(f"✅ Stock command processed: {response.status_code}")
            return response.status_code in [200, 202]
        except Exception as e:
            print(f"❌ Stock command error: {str(e)}")
            return False

    def test_order_command(self):
        """Test order command."""
        print("\n📋 Testing Order Command...")

        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": self.test_phone.replace("+", ""),
                                        "type": "text",
                                        "text": {"body": "order"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            print(f"✅ Order command processed: {response.status_code}")
            return response.status_code in [200, 202]
        except Exception as e:
            print(f"❌ Order command error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all tests."""
        print("\n" + "=" * 60)
        print("🤖 WhatsApp Inventory Bot - Local Testing")
        print("=" * 60)

        results = {
            "Health Check": self.test_health(),
            "Webhook Verification": self.test_webhook_verification(),
            "Text Message": self.test_text_message(),
            "MFA Setup": self.test_mfa_setup(),
            "Stock Command": self.test_stock_command(),
            "Order Command": self.test_order_command(),
        }

        print("\n" + "=" * 60)
        print("📊 Test Results:")
        print("=" * 60)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")

        print("=" * 60)
        print(f"Overall: {passed}/{total} tests passed")
        print("=" * 60 + "\n")

        return passed == total


def main():
    """Run tests."""
    # Check if bot is running
    tester = WhatsAppBotTester()

    # Try to connect
    try:
        response = requests.get(f"{tester.base_url}/health", timeout=2)
    except:
        print("\n❌ Bot server is not running!")
        print("Start the bot with: python run.py")
        print("Or use: python -m pytest tests/test_auth.py -v")
        sys.exit(1)

    # Run tests
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
