#!/usr/bin/env python3
"""
WhatsApp MFA Webhook Integration
Handles MFA setup and verification through WhatsApp Bot
"""

import hashlib
import json
import os
import sqlite3
from pathlib import Path

import pyotp
import requests
from dotenv import load_dotenv
from flask import Flask, request

# Load environment variables
load_dotenv()

app = Flask(__name__)

# WhatsApp API Configuration
WHATSAPP_API_URL = "https://graph.instagram.com/v18.0"
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_ID")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
DB_PATH = "chatbot_data/chatbot.db"

# Store pending MFA setups (in production, use database)
pending_mfa_setups = {}


class WhatsAppMFABot:
    """Handle MFA setup via WhatsApp."""

    def __init__(self, phone_id, access_token):
        self.phone_id = phone_id
        self.access_token = access_token

    def send_text_message(self, recipient_id, message):
        """Send text message via WhatsApp."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"body": message},
        }

        try:
            response = requests.post(
                f"{WHATSAPP_API_URL}/{self.phone_id}/messages",
                headers=headers,
                json=payload,
                timeout=10,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending text: {e}")
            return False

    def send_image_message(self, recipient_id, image_path, caption=None):
        """Send image (QR code) via WhatsApp."""
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            # Upload media
            with open(image_path, "rb") as f:
                files = {
                    "file": (Path(image_path).name, f, "image/png"),
                    "messaging_product": (None, "whatsapp"),
                }

                upload_response = requests.post(
                    f"{WHATSAPP_API_URL}/{self.phone_id}/media",
                    headers=headers,
                    files=files,
                    timeout=10,
                )

            if upload_response.status_code != 200:
                print(f"Upload failed: {upload_response.text}")
                return False

            media_id = upload_response.json().get("id")

            # Send media message
            headers["Content-Type"] = "application/json"

            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_id,
                "type": "image",
                "image": {"id": media_id},
            }

            if caption:
                payload["image"]["caption"] = caption

            response = requests.post(
                f"{WHATSAPP_API_URL}/{self.phone_id}/messages",
                headers=headers,
                json=payload,
                timeout=10,
            )

            return response.status_code == 200
        except Exception as e:
            print(f"Error sending image: {e}")
            return False

    def setup_mfa_for_user(self, user_phone, username):
        """Initiate MFA setup process."""
        try:
            # Get MFA setup from database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Generate new secret if not exists
            secret = pyotp.random_base32()
            totp = pyotp.TOTP(secret)
            uri = totp.provisioning_uri(
                name=username, issuer_name="AI Project Assistant"
            )

            # Store pending setup
            pending_mfa_setups[user_phone] = {
                "username": username,
                "secret": secret,
                "uri": uri,
            }

            conn.close()

            # Step 1: Send QR code image
            qr_file = f"qr_codes/mfa_{username}_qr.png"
            if os.path.exists(qr_file):
                self.send_image_message(
                    user_phone,
                    qr_file,
                    caption="Scan this QR code with your authenticator app (Microsoft, Google, etc.)",
                )

            # Step 2: Send manual setup instructions
            manual_setup = f"""📱 Can't scan the QR code? Here's the manual way:

1. Open your authenticator app
2. Tap + to add account
3. Select "Enter setup key" or "Manual entry"
4. Enter this key: {secret}
5. Authenticator will show a 6-digit code

OR: Send me 'Code XXXXXX' with your 6-digit code to continue"""

            self.send_text_message(user_phone, manual_setup)

            return True
        except Exception as e:
            print(f"Error setting up MFA: {e}")
            return False

    def verify_mfa_code(self, user_phone, provided_code):
        """Verify MFA code."""
        try:
            if user_phone not in pending_mfa_setups:
                self.send_text_message(
                    user_phone, "No MFA setup in progress. Send 'setup mfa' to begin."
                )
                return False

            setup_data = pending_mfa_setups[user_phone]
            secret = setup_data["secret"]
            username = setup_data["username"]

            # Verify code
            totp = pyotp.TOTP(secret)
            if not totp.verify(str(provided_code).strip(), valid_window=1):
                self.send_text_message(
                    user_phone,
                    "Invalid code. Wait for the next 6-digit code (changes every 30 seconds) and try again.",
                )
                return False

            # Code verified - generate backup codes
            backup_codes = self._generate_backup_codes()

            # Save to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            try:
                hashed_codes = [
                    hashlib.sha256(c.encode()).hexdigest() for c in backup_codes
                ]
                cursor.execute(
                    """
                    UPDATE users 
                    SET mfa_enabled = 1, mfa_secret = ?, mfa_backup_codes = ?
                    WHERE username = ?
                """,
                    (secret, json.dumps(hashed_codes), username),
                )

                conn.commit()

                # Send success message with backup codes
                codes_list = "\n".join(
                    [f"   {i+1}. {code}" for i, code in enumerate(backup_codes)]
                )

                success_msg = f"""✅ MFA Successfully Enabled!

Your backup codes (save these in a safe place):
{codes_list}

Use these if:
• You lose your phone
• You can't access your authenticator
• You need emergency access

IMPORTANT: Each code can only be used ONCE.

Next time you login, you'll need:
1. Username + Password
2. 6-digit code from your authenticator

Stay secure! 🔒"""

                self.send_text_message(user_phone, success_msg)

                # Clean up
                del pending_mfa_setups[user_phone]

                return True

            except Exception as e:
                print(f"Database error: {e}")
                conn.rollback()
                self.send_text_message(
                    user_phone, "Error saving setup. Please try again."
                )
                return False
            finally:
                conn.close()

        except Exception as e:
            print(f"Error verifying code: {e}")
            return False

    @staticmethod
    def _generate_backup_codes(count=8):
        """Generate backup codes."""
        import secrets

        codes = []
        for _ in range(count):
            code = "".join(
                secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)
            )
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes


# Initialize bot
bot = WhatsAppMFABot(PHONE_NUMBER_ID, ACCESS_TOKEN)


# Routes
@app.route("/whatsapp/webhook", methods=["GET"])
def webhook_verify():
    """Verify webhook with WhatsApp."""
    verify_token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    mode = request.args.get("hub.mode")

    if mode == "subscribe" and verify_token == VERIFY_TOKEN:
        print("Webhook verified")
        return challenge

    return "Invalid token", 403


@app.route("/whatsapp/webhook", methods=["POST"])
def webhook_receive():
    """Receive messages from WhatsApp."""
    try:
        data = request.json

        # Check if there are messages
        if "entry" not in data:
            return {"status": "ok"}, 200

        for entry in data["entry"]:
            for change in entry["changes"]:
                if "messages" not in change["value"]:
                    continue

                for message in change["value"]["messages"]:
                    user_phone = message["from"]

                    # Handle different message types
                    if message["type"] == "text":
                        text = message["text"]["body"].strip()
                        handle_text_message(user_phone, text)
                    elif message["type"] == "button":
                        # Handle button clicks
                        pass

        return {"status": "ok"}, 200

    except Exception as e:
        print(f"Error in webhook: {e}")
        return {"status": "error"}, 500


def handle_text_message(user_phone, text):
    """Handle incoming text messages."""
    text_lower = text.lower()

    # Help
    if text_lower in ["help", "h"]:
        help_msg = """Available commands:
        
setup mfa       - Enable two-factor authentication
disable mfa     - Disable MFA
codes           - Show backup codes
status          - Check MFA status
help            - Show this menu"""
        bot.send_text_message(user_phone, help_msg)

    # Setup MFA
    elif text_lower in ["setup mfa", "setup 2fa", "enable mfa"]:
        bot.send_text_message(
            user_phone, "Starting MFA setup...\n\nWhat's your username?"
        )
        pending_mfa_setups[user_phone] = {"waiting_for_username": True}

    # Check if waiting for username
    elif user_phone in pending_mfa_setups and pending_mfa_setups[user_phone].get(
        "waiting_for_username"
    ):
        username = text.strip()
        pending_mfa_setups[user_phone]["waiting_for_username"] = False

        # Verify username exists
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            bot.send_text_message(
                user_phone, f"User '{username}' not found. Please check your username."
            )
            del pending_mfa_setups[user_phone]
        else:
            bot.setup_mfa_for_user(user_phone, username)

    # Verify code (6 digits)
    elif len(text) == 6 and text.isdigit():
        bot.verify_mfa_code(user_phone, text)

    # Status
    elif text_lower == "status":
        bot.send_text_message(user_phone, "MFA status check not implemented yet.")

    else:
        bot.send_text_message(
            user_phone,
            f"I didn't understand '{text}'. Type 'help' for available commands.",
        )


# Health check
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return {"error": "Not found"}, 404


@app.errorhandler(500)
def server_error(e):
    return {"error": "Server error"}, 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
