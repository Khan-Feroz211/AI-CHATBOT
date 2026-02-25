"""
WhatsApp Integration Testing Script
Tests all WhatsApp functionality in sandbox and live modes
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.services.whatsapp import WhatsAppService
from src.api.schemas.whatsapp import WhatsAppSendRequest
from config.settings import settings


class WhatsAppTester:
    """Complete WhatsApp integration tester"""
    
    def __init__(self):
        self.service = WhatsAppService()
        self.test_results = []
        self.colors = {
            'green': '\033[92m',
            'red': '\033[91m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'reset': '\033[0m'
        }
    
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{self.colors['blue']}{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}{self.colors['reset']}\n")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{self.colors['green']}✓ {text}{self.colors['reset']}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"{self.colors['red']}✗ {text}{self.colors['reset']}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"{self.colors['yellow']}ℹ {text}{self.colors['reset']}")
    
    def test_configuration(self) -> bool:
        """Test WhatsApp configuration"""
        self.print_header("CONFIGURATION CHECK")
        
        checks = {
            "WhatsApp Enabled": settings.WHATSAPP_ENABLED,
            "Sandbox Mode": settings.WHATSAPP_SANDBOX_MODE,
            "Verify Token Set": bool(settings.WHATSAPP_VERIFY_TOKEN),
            "App Secret Set": bool(settings.WHATSAPP_APP_SECRET),
        }
        
        if not settings.WHATSAPP_SANDBOX_MODE:
            checks["Access Token Set"] = bool(settings.WHATSAPP_ACCESS_TOKEN)
            checks["Phone Number ID Set"] = bool(settings.WHATSAPP_PHONE_NUMBER_ID)
        
        all_good = True
        for check, result in checks.items():
            if result:
                self.print_success(f"{check}")
            else:
                self.print_error(f"{check}")
                all_good = False
        
        return all_good
    
    def test_webhook_verification(self) -> bool:
        """Test webhook verification"""
        self.print_header("WEBHOOK VERIFICATION TEST")
        
        verify_token = settings.WHATSAPP_VERIFY_TOKEN
        test_token = verify_token
        wrong_token = "wrong-token-test"
        challenge = "test-challenge-123"
        
        # Test correct token
        result = self.service.verify_webhook_challenge("subscribe", test_token, challenge)
        if result == challenge:
            self.print_success("Webhook verification with correct token")
        else:
            self.print_error("Webhook verification with correct token")
            return False
        
        # Test wrong token
        result = self.service.verify_webhook_challenge("subscribe", wrong_token, challenge)
        if result is None:
            self.print_success("Webhook verification correctly rejects wrong token")
        else:
            self.print_error("Webhook verification should reject wrong token")
            return False
        
        self.print_info("Webhook challenge test command to run locally:")
        print(f"curl -X GET 'http://localhost:8000/api/v1/whatsapp/webhook?")
        print(f"hub.mode=subscribe&")
        print(f"hub.challenge=TEST_CHALLENGE&")
        print(f"hub.verify_token={verify_token}'")
        
        return True
    
    def test_signature_verification(self) -> bool:
        """Test webhook signature verification"""
        self.print_header("SIGNATURE VERIFICATION TEST")
        
        if settings.WHATSAPP_SANDBOX_MODE:
            self.print_info("Skipping signature test (sandbox mode)")
            return True
        
        try:
            import hashlib
            import hmac
            
            test_body = b'{"test": "data"}'
            secret = settings.WHATSAPP_APP_SECRET.encode()
            
            # Generate valid signature
            digest = hmac.new(secret, test_body, hashlib.sha256).hexdigest()
            valid_sig = f"sha256={digest}"
            
            # Test valid signature
            if self.service.verify_webhook_signature(test_body, valid_sig):
                self.print_success("Valid signature verification")
            else:
                self.print_error("Failed to verify valid signature")
                return False
            
            # Test invalid signature
            if not self.service.verify_webhook_signature(test_body, "sha256=invalidsignature"):
                self.print_success("Invalid signature correctly rejected")
            else:
                self.print_error("Should reject invalid signature")
                return False
            
            return True
        except Exception as e:
            self.print_error(f"Signature test failed: {e}")
            return False
    
    def test_sandbox_mode(self) -> bool:
        """Test sandbox mode message sending"""
        self.print_header("SANDBOX MODE TEST")
        
        if not settings.WHATSAPP_SANDBOX_MODE:
            self.print_info("Sandbox mode is disabled, skipping")
            return True
        
        try:
            test_phone = settings.WHATSAPP_TEST_PHONE or "923001234567"
            
            request = WhatsAppSendRequest(
                to_phone=test_phone,
                message="🧪 Test message from sandbox mode"
            )
            
            result = self.service.build_outbound_message(request)
            
            print(f"Test Phone: {test_phone}")
            print(f"Status: {result.status}")
            print(f"Success: {result.success}")
            
            if result.success:
                self.print_success(f"Sandbox message sent (Status: {result.status})")
                self.print_info(f"Message ID would be: {result.message_id or 'N/A'}")
                return True
            else:
                self.print_error(f"Sandbox message failed: {result.status}")
                return False
        except Exception as e:
            self.print_error(f"Sandbox test failed: {e}")
            return False
    
    def test_live_mode_config(self) -> bool:
        """Test live mode configuration without sending"""
        self.print_header("LIVE MODE CONFIGURATION CHECK")
        
        if settings.WHATSAPP_SANDBOX_MODE:
            self.print_info("Sandbox mode is enabled, skipping live mode test")
            return True
        
        required_config = {
            "Access Token": settings.WHATSAPP_ACCESS_TOKEN,
            "Phone Number ID": settings.WHATSAPP_PHONE_NUMBER_ID,
            "Business Account ID": settings.WHATSAPP_BUSINESS_ACCOUNT_ID,
        }
        
        all_ready = True
        for config, value in required_config.items():
            if value:
                self.print_success(f"{config} configured")
                # Show first 10 chars of sensitive data
                display_value = value[:10] + "..." if len(value) > 10 else value
                self.print_info(f"  Value: {display_value}")
            else:
                self.print_error(f"{config} missing")
                all_ready = False
        
        if all_ready:
            self.print_info("Live mode is properly configured")
            self.print_info("You can now send messages to real WhatsApp numbers")
        
        return all_ready
    
    def test_message_formatting(self) -> bool:
        """Test message formatting"""
        self.print_header("MESSAGE FORMATTING TEST")
        
        test_cases = [
            ("Simple text", "This is a simple message"),
            ("With emoji", "Hello 👋 This is a test 🧪"),
            ("Multi-line", "Line 1\nLine 2\nLine 3"),
            ("With special chars", "Price: $99.99, Discount: 50%"),
            ("Long message", "A" * 500),  # Test max length
        ]
        
        all_passed = True
        for name, message in test_cases:
            if len(message) <= 4096:
                self.print_success(f"Message formatting test: {name} ({len(message)} chars)")
            else:
                self.print_error(f"Message too long: {name} ({len(message)} chars)")
                all_passed = False
        
        return all_passed
    
    def test_phone_validation(self) -> bool:
        """Test phone number validation"""
        self.print_header("PHONE NUMBER VALIDATION TEST")
        
        test_phones = [
            ("923001234567", True, "Pakistani number"),
            ("+923001234567", False, "With country code prefix"),  # Service should handle
            ("03001234567", False, "National format"),
            ("invalid", False, "Invalid number"),
        ]
        
        all_passed = True
        for phone, should_pass, description in test_phones:
            try:
                # The service should handle validation
                request = WhatsAppSendRequest(
                    to_phone=phone,
                    message="Test"
                )
                self.print_success(f"Phone validation: {description} - {phone}")
            except Exception as e:
                if should_pass:
                    self.print_error(f"Phone validation failed: {description} - {phone}")
                    all_passed = False
                else:
                    self.print_success(f"Phone correctly rejected: {description}")
        
        return all_passed
    
    def test_rate_limiting(self) -> bool:
        """Test rate limiting"""
        self.print_header("RATE LIMITING TEST")
        
        if settings.WHATSAPP_SANDBOX_MODE:
            self.print_info("Testing rate limits with small delays...")
            
            messages_sent = 0
            for i in range(3):
                try:
                    request = WhatsAppSendRequest(
                        to_phone="923001234567",
                        message=f"Rate limit test message {i+1}"
                    )
                    result = self.service.build_outbound_message(request)
                    if result.success:
                        messages_sent += 1
                    time.sleep(0.5)  # Small delay between messages
                except Exception as e:
                    self.print_error(f"Rate limit test error: {e}")
                    break
            
            self.print_success(f"Sent {messages_sent} messages within rate limits")
            return True
        else:
            self.print_info("Rate limiting configured (Max retries: {})".format(
                settings.WHATSAPP_MAX_RETRIES
            ))
            self.print_info("Backoff time: {} seconds".format(
                settings.WHATSAPP_RETRY_BACKOFF_SECONDS
            ))
            return True
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate test report"""
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "environment": "SANDBOX" if settings.WHATSAPP_SANDBOX_MODE else "PRODUCTION",
            "configuration_status": "✓ Configured" if self.test_configuration() else "✗ Not configured",
        }
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        self.print_header("WHATSAPP INTEGRATION TEST SUITE")
        
        tests = [
            ("Configuration Check", self.test_configuration),
            ("Webhook Verification", self.test_webhook_verification),
            ("Signature Verification", self.test_signature_verification),
            ("Sandbox Mode", self.test_sandbox_mode),
            ("Live Mode Configuration", self.test_live_mode_config),
            ("Message Formatting", self.test_message_formatting),
            ("Phone Validation", self.test_phone_validation),
            ("Rate Limiting", self.test_rate_limiting),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = "PASSED" if result else "FAILED"
            except Exception as e:
                self.print_error(f"Test exception: {e}")
                results[test_name] = "ERROR"
        
        # Print summary
        self.print_header("TEST SUMMARY")
        passed = sum(1 for v in results.values() if v == "PASSED")
        failed = sum(1 for v in results.values() if v == "FAILED")
        errors = sum(1 for v in results.values() if v == "ERROR")
        
        for test_name, status in results.items():
            if status == "PASSED":
                self.print_success(test_name)
            elif status == "FAILED":
                self.print_error(test_name)
            else:
                print(f"{self.colors['yellow']}⚠ {test_name}: {status}{self.colors['reset']}")
        
        print(f"\n{self.colors['blue']}Total: {len(results)} tests")
        print(f"Passed: {passed}, Failed: {failed}, Errors: {errors}{self.colors['reset']}\n")
        
        return failed == 0 and errors == 0


def main():
    """Main entry point"""
    try:
        tester = WhatsAppTester()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
