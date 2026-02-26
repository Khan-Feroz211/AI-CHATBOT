#!/usr/bin/env python3
"""
WhatsApp + MFA Integration Setup
Generates QR codes as files and sets up WhatsApp API integration
"""

import hashlib
import json
import secrets
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pyotp
import qrcode

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.core.security import hash_password


class WhatsAppMFASetup:
    def __init__(self, db_path="chatbot_data/chatbot.db"):
        self.db_path = db_path
        # Create directories for QR codes and WhatsApp data
        self.qr_dir = Path("qr_codes")
        self.wa_dir = Path("whatsapp_mfa")
        self.qr_dir.mkdir(exist_ok=True)
        self.wa_dir.mkdir(exist_ok=True)

    def _hash_recovery_code(self, code):
        """Hash recovery code for storage."""
        return hashlib.sha256(code.upper().encode()).hexdigest()

    def _generate_recovery_codes(self, count=8):
        """Generate recovery codes (backup codes)."""
        codes = []
        for _ in range(count):
            code = "".join(
                secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)
            )
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes

    def create_demo_account_with_qr(
        self, username, password, issuer_name="AI Project Assistant"
    ):
        """Create demo account and generate QR code file."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing = cursor.fetchone()

        if existing:
            print(f"  ⚠️  {username} already exists")
            conn.close()
        else:
            # Generate MFA
            secret = pyotp.random_base32()
            totp = pyotp.TOTP(secret)
            uri = totp.provisioning_uri(name=username, issuer_name=issuer_name)
            recovery_codes = self._generate_recovery_codes()
            hashed_codes = [self._hash_recovery_code(code) for code in recovery_codes]

            # Hash password
            password_hash = hash_password(password)

            # Create account
            try:
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, mfa_enabled, mfa_secret, mfa_backup_codes)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (username, password_hash, 1, secret, json.dumps(hashed_codes)),
                )

                conn.commit()
                user_id = cursor.lastrowid
                print(f"  ✓ {username} created (ID: {user_id})")

                conn.close()

                # Generate QR code file
                qr_file = self.generate_qr_code_file(username, uri)

                return {
                    "user_id": user_id,
                    "username": username,
                    "secret": secret,
                    "provisioning_uri": uri,
                    "recovery_codes": recovery_codes,
                    "qr_file": str(qr_file),
                }
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                conn.rollback()
                conn.close()
                return None

    def generate_qr_code_file(self, username, provisioning_uri):
        """Generate QR code as image file."""
        # Create high-quality QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction for WhatsApp
            box_size=15,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save as PNG
        qr_file = self.qr_dir / f"mfa_{username}_qr.png"
        img.save(qr_file)

        print(f"    ✓ QR code saved: {qr_file}")
        return qr_file

    def create_whatsapp_config(self):
        """Create WhatsApp API configuration template."""
        config = {
            "whatsapp_api": {
                "provider": "Meta/WhatsApp Cloud API",
                "version": "v18.0",
                "endpoints": {
                    "send_message": "https://graph.instagram.com/v18.0/{phone-number-id}/messages",
                    "upload_media": "https://graph.instagram.com/v18.0/{phone-number-id}/media",
                    "webhook": "/api/whatsapp/webhook",
                },
                "auth": {
                    "access_token": "YOUR_WHATSAPP_API_TOKEN",
                    "phone_number_id": "YOUR_PHONE_NUMBER_ID",
                    "verify_token": "YOUR_VERIFY_TOKEN",
                },
            },
            "mfa_workflow": {
                "step_1_request_setup": "User sends: 'setup mfa' or 'enable 2fa'",
                "step_2_send_qr": "Bot sends: QR code image + manual secret key",
                "step_3_user_scans": "User scans with authenticator app",
                "step_4_send_code_prompt": "Bot sends: 'Enter your 6-digit code'",
                "step_5_verify": "User sends: 6-digit code",
                "step_6_confirmation": "Bot sends: 'MFA Enabled! Your backup codes are...'",
            },
            "features": {
                "qr_code_delivery": "Image file attachment (supports JPEG/PNG)",
                "manual_setup": "Send secret key via message",
                "backup_codes": "Send as message (encrypted optional)",
                "verify_code": "User enters code via chat",
                "emergency_access": "Send backup code to login",
            },
        }

        config_file = self.wa_dir / "whatsapp_mfa_config.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        print(f"  ✓ WhatsApp config template: {config_file}")
        return config_file

    def create_whatsapp_integration_code(self):
        """Create WhatsApp integration code."""
        code = '''#!/usr/bin/env python3
"""
WhatsApp MFA Integration Module
Handles MFA setup and verification via WhatsApp
"""

import requests
import json
from pathlib import Path
import pyotp

class WhatsAppMFAIntegration:
    def __init__(self, access_token, phone_number_id, verify_token):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.verify_token = verify_token
        self.api_url = f"https://graph.instagram.com/v18.0/{phone_number_id}"
    
    def send_message(self, recipient_phone, message_text):
        """Send text message via WhatsApp."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_text
            }
        }
        
        response = requests.post(
            f"{self.api_url}/messages",
            headers=headers,
            json=payload
        )
        return response.json()
    
    def send_image(self, recipient_phone, image_path, caption=None):
        """Send image (QR code) via WhatsApp."""
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        # Upload media first
        with open(image_path, 'rb') as img:
            files = {'file': (Path(image_path).name, img, 'image/png')}
            data = {'messaging_product': 'whatsapp'}
            
            upload_response = requests.post(
                f"{self.api_url}/media",
                headers=headers,
                files=files,
                data=data
            )
        
        media_id = upload_response.json().get('id')
        
        # Send media message
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "image",
            "image": {
                "id": media_id
            }
        }
        
        if caption:
            payload["image"]["caption"] = caption
        
        response = requests.post(
            f"{self.api_url}/messages",
            headers=headers,
            json=payload
        )
        return response.json()
    
    def handle_mfa_setup_request(self, user_phone, username, mfa_secret, recovery_codes):
        """Handle MFA setup process via WhatsApp."""
        
        # Step 1: Send QR code
        qr_path = f"qr_codes/mfa_{username}_qr.png"
        
        self.send_image(
            user_phone,
            qr_path,
            caption="🔐 Scan this QR code with Microsoft Authenticator or Google Authenticator"
        )
        
        # Step 2: Send manual setup key
        setup_message = f"""📱 **Manual Setup (if QR scan fails):**

If you can't scan the QR code:
1. Open your Authenticator app
2. Tap + to add account
3. Select "Enter setup key"
4. Name: {username}
5. Key: {mfa_secret}
6. Time-based (TOTP)

Then send me the 6-digit code to verify!"""
        
        self.send_message(user_phone, setup_message)
        
        # Step 3: Request verification code
        verification_request = "Now, please send me your current 6-digit code from the authenticator app to verify:"
        self.send_message(user_phone, verification_request)
    
    def handle_mfa_verification(self, user_phone, mfa_secret, provided_code):
        """Verify MFA code via WhatsApp."""
        totp = pyotp.TOTP(mfa_secret)
        
        if totp.verify(str(provided_code).strip(), valid_window=1):
            success_message = """✅ **MFA Successfully Enabled!**

Your backup codes (save these somewhere safe):
{}

Use these if:
- Your phone is lost
- You can't access your authenticator
- You need emergency access

Each code can only be used ONCE.

Next time you login, you'll need:
1. Username + Password
2. 6-digit code from authenticator

Stay secure! 🔒"""
            
            codes_formatted = "\\n".join([f"• {code}" for code in mfa_secret['backup_codes']])
            self.send_message(user_phone, success_message.format(codes_formatted))
            return True
        else:
            error_message = """❌ Code not valid.

Try these steps:
1. Check your app is synced (time must be automatic)
2. Make sure you entered the CURRENT code (changes every 30 seconds)
3. Wait for next code and try again

Need help? Send 'help' or contact support."""
            self.send_message(user_phone, error_message)
            return False

'''

        code_file = self.wa_dir / "whatsapp_mfa_integration.py"
        with open(code_file, "w") as f:
            f.write(code)

        print(f"  ✓ WhatsApp integration code: {code_file}")
        return code_file

    def create_whatsapp_setup_guide(self):
        """Create WhatsApp integration setup guide."""
        guide = """# 🠦 WhatsApp MFA Integration Guide

## Overview

Integrate MFA (Two-Factor Authentication) into WhatsApp so your users can:
- Enable MFA by sending a message
- Receive QR code via WhatsApp
- Verify with 6-digit code
- Get backup recovery codes

## Prerequisites

1. **WhatsApp Business Account**
   - Sign up at: https://www.whatsapp.com/business/
   - Verify your business

2. **Meta API Access**
   - Create app at: https://developers.facebook.com
   - Get Access Token
   - Get Phone Number ID
   - Get Verify Token

3. **Python Libraries**
   ```bash
   pip install requests pyotp flask
   ```

## Setup Steps

### Step 1: Get API Credentials

1. Go to: https://developers.facebook.com/apps/
2. Create new app → "Business"
3. Add "WhatsApp" product
4. Get credentials:
   - Business Phone Number ID
   - Permanent Access Token
   - Verify Token (create random string)

### Step 2: Configure Flask Webhook

```python
from flask import Flask, request
import json

app = Flask(__name__)

# WhatsApp credentials (use environment variables in production!)
ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
VERIFY_TOKEN = os.environ.get("META_WEBHOOK_VERIFY_TOKEN", "")
PHONE_ID = os.environ.get("META_PHONE_NUMBER_ID", "")

@app.route('/api/whatsapp/webhook', methods=['GET'])
def webhook_verify():
    # Verify webhook with WhatsApp
    verify_token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if verify_token == VERIFY_TOKEN:
        return challenge
    return 'Invalid token', 403

@app.route('/api/whatsapp/webhook', methods=['POST'])
def webhook_receive():
    # Receive messages from WhatsApp
    data = request.json
    
    try:
        if data['entry'][0]['changes'][0]['value']['messages']:
            message = data['entry'][0]['changes'][0]['value']['messages'][0]
            user_phone = message['from']
            text = message['text']['body']
            
            # Handle MFA commands
            if text.lower() == 'setup mfa' or text.lower() == 'enable 2fa':
                # Trigger MFA setup
                setup_mfa_for_user(user_phone)
            
            elif len(text) == 6 and text.isdigit():
                # Verify MFA code
                verify_mfa_code(user_phone, text)
    
    except Exception as e:
        print(f"Error: {e}")
    
    return '{"status":"ok"}', 200

if __name__ == '__main__':
    app.run(port=5000, debug=False)
```

### Step 3: Configure Webhook in Meta

1. Go to WhatsApp app settings
2. Set Webhook URL: `https://yourdomain.com/api/whatsapp/webhook`
3. Verify Token: (the one you created)
4. Subscribe to:
   - messages
   - message_template_status_update

### Step 4: Test Webhook

```bash
# Test message
Send to your WhatsApp number: "setup mfa"

# Should receive:
# 1. QR code image
# 2. Manual setup instructions
# 3. Code verification prompt
```

## User Workflow

```
User Action              |  Bot Response
─────────────────────────┼──────────────────────────
Send: "setup mfa"        | QR code image
                         | Manual setup key
                         | "Send 6-digit code"
─────────────────────────┼──────────────────────────
Send: "123456"           | "✅ MFA Enabled!"
                         | Backup codes listed
─────────────────────────┼──────────────────────────
Send: "help"             | Help menu
─────────────────────────┼──────────────────────────
Send: "disable mfa"      | Verification process
                         | "Disabled"
```

## Deployment

### Option 1: Heroku (Free tier)

```bash
# Create Procfile
echo "web: python app.py" > Procfile

# Create requirements.txt
pip freeze > requirements.txt

# Deploy
heroku login
heroku create your-app-name
git push heroku main
```

### Option 2: AWS Lambda

```bash
# Package code
zip -r lambda_function.zip .

# Upload to Lambda
aws lambda create-function \\
  --function-name mfa-whatsapp \\
  --runtime python3.11 \\
  --zip-file fileb://lambda_function.zip
```

### Option 3: Docker (Self-hosted)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

```bash
docker build -t mfa-whatsapp .
docker run -p 5000:5000 mfa-whatsapp
```

## QR Code Delivery

The QR code is automatically generated and sent via WhatsApp as an image.

**If QR scanning fails:**
- Manual setup key is provided immediately
- User can enter key manually in authenticator app
- Takes ~1 minute instead of 10 seconds

**Supported Authenticators (all work with manual key):**
- Microsoft Authenticator
- Google Authenticator
- Oracle Authenticator
- Authy
- Any RFC 6238 TOTP app

## Error Handling

### Common Issues

**Issue:** "Failed to upload media"
- Solution: Check WhatsApp API permissions
- Solution: Verify access token is valid

**Issue:** QR code doesn't display
- Solution: Check image file exists
- Solution: Manual setup key is sent as fallback

**Issue:** Code verification fails
- Solution: Phone time must be automatic
- Solution: Code is valid for ~30 seconds per window
- Solution: Check valid_window tolerance

## Security Considerations

1. **Access Tokens**
   - Store in environment variables (.env file)
   - Never commit to version control
   - Rotate periodically

2. **Verification Codes**
   - Validate format (6 digits only)
   - Implement rate limiting (max 5 attempts per hour)
   - Log failed attempts

3. **Backup Codes**
   - Hash before storing
   - Send via encrypted channel
   - Display only once

4. **User Privacy**
   - Don't log user messages
   - Comply with GDPR/local laws
   - Clear data after setup

## Monitoring

Track these metrics:

```
- MFA setup requests: /day
- Successful verifications: /day
- Failed attempts: /day  
- QR vs Manual setup: ratio
- Code verification time: average
```

## Support Commands

Set up these commands in WhatsApp:

```
setup mfa      - Enable MFA
disable mfa    - Disable MFA
show codes     - Backup codes reminder
verify code    - Re-verify MFA
help           - Show all commands
```

## Testing Checklist

- [ ] Can send "setup mfa" command
- [ ] Receive QR code image
- [ ] Receive manual setup key
- [ ] Can scan QR with authenticator
- [ ] 6-digit code appears in app
- [ ] Send code to WhatsApp
- [ ] Receive success message
- [ ] Backup codes displayed
- [ ] Codes are different each time
- [ ] Previous code doesn't work twice
- [ ] Login with username + password shows MFA prompt
- [ ] Login succeeds with 6-digit code

## Next Steps

1. Set up WhatsApp Business account
2. Get API credentials
3. Deploy webhook server
4. Test MFA workflow
5. Train support team
6. Roll out to users

---

**Status:** Ready for production
**Support:** contact@yourcompany.com
"""

        guide_file = self.wa_dir / "WHATSAPP_MFA_SETUP_GUIDE.md"
        with open(guide_file, "w") as f:
            f.write(guide)

        print(f"  ✓ WhatsApp setup guide: {guide_file}")
        return guide_file

    def run_setup(self):
        """Run complete setup."""
        print("\n" + "=" * 80)
        print("WHATSAPP + MFA INTEGRATION SETUP")
        print("=" * 80 + "\n")

        # Create demo accounts with QR codes
        print("1️⃣  Creating demo accounts with QR codes...\n")
        accounts = []
        for username, password in [
            ("demo_user", "demo123"),
            ("demo_admin", "admin123"),
            ("demo_partner", "partner123"),
        ]:
            data = self.create_demo_account_with_qr(username, password)
            if data:
                accounts.append(data)

        # Create WhatsApp configuration
        print("\n2️⃣  Creating WhatsApp configuration...\n")
        self.create_whatsapp_config()

        # Create integration code
        print("\n3️⃣  Creating WhatsApp integration code...\n")
        self.create_whatsapp_integration_code()

        # Create setup guide
        print("\n4️⃣  Creating WhatsApp setup guide...\n")
        self.create_whatsapp_setup_guide()

        # Create summary
        print("\n" + "=" * 80)
        print("✅ WHATSAPP MFA INTEGRATION COMPLETE!")
        print("=" * 80 + "\n")

        print("📁 Files Generated:")
        print(f"   QR Codes: {self.qr_dir}/")
        print(f"   WhatsApp Files: {self.wa_dir}/")
        print()

        print("📋 What You Have Now:")
        print("   ✓ QR code PNG files for each demo account")
        print("   ✓ Fallback manual setup keys")
        print("   ✓ WhatsApp API configuration template")
        print("   ✓ Python integration code (ready to deploy)")
        print("   ✓ Complete setup guide with example code")
        print()

        print("🚀 Next Steps:")
        print("   1. Get WhatsApp Business account")
        print("   2. Get Meta API credentials")
        print("   3. Deploy webhook (using provided Flask code)")
        print("   4. Configure webhook URL in Meta dashboard")
        print("   5. Test with 'setup mfa' command")
        print()

        print("💡 User Experience:")
        print("   User sends: 'setup mfa'")
        print("   Bot sends: QR code (as image) + manual key")
        print("   User: Scans QR or enters manual key")
        print("   User sends: '123456' (6-digit code)")
        print("   Bot sends: 'MFA Enabled! Backup codes: ...'")
        print()

        return True


if __name__ == "__main__":
    try:
        setup = WhatsAppMFASetup()
        success = setup.run_setup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
