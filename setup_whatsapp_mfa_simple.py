#!/usr/bin/env python3
"""
WhatsApp + MFA Integration - Quick Setup
Generates QR codes and WhatsApp integration files
"""

import sqlite3
import json
import pyotp
import qrcode
from datetime import datetime
from pathlib import Path
import hashlib
import secrets
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.core.security import hash_password

def hash_recovery_code(code):
    return hashlib.sha256(code.upper().encode()).hexdigest()

def generate_recovery_codes(count=8):
    codes = []
    for _ in range(count):
        code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
        codes.append(f"{code[:4]}-{code[4:]}")
    return codes

def create_demo_account_with_qr(username, password):
    """Create account and generate QR code file."""
    db_path = "chatbot_data/chatbot.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    qr_dir = Path("qr_codes")
    qr_dir.mkdir(exist_ok=True)
    
    # Check if exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        print(f"  ⚠️  {username} already exists (skipping)")
        conn.close()
        return None
    
    try:
        # Generate MFA
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=username, issuer_name="AI Project Assistant")
        recovery_codes = generate_recovery_codes()
        hashed_codes = [hash_recovery_code(code) for code in recovery_codes]
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create account
        cursor.execute("""
            INSERT INTO users (username, password_hash, mfa_enabled, mfa_secret, mfa_backup_codes)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, 1, secret, json.dumps(hashed_codes)))
        
        conn.commit()
        user_id = cursor.lastrowid
        print(f"  ✓ {username} created (MFA enabled)")
        
        conn.close()
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=15,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        qr_file = qr_dir / f"mfa_{username}_qr.png"
        img.save(qr_file)
        
        print(f"    ✓ QR code: {qr_file}")
        
        return {
            "username": username,
            "secret": secret,
            "uri": uri,
            "recovery_codes": recovery_codes,
            "qr_file": str(qr_file)
        }
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        conn.rollback()
        conn.close()
        return None

def main():
    print("\n" + "="*80)
    print("WHATSAPP + MFA INTEGRATION SETUP")
    print("="*80 + "\n")
    
    # Create demo accounts
    print("1️⃣  Creating demo accounts with actual QR code files...\n")
    accounts = []
    for username, password in [("demo_user", "demo123"), ("demo_admin", "admin123"), ("demo_partner", "partner123")]:
        data = create_demo_account_with_qr(username, password)
        if data:
            accounts.append(data)
    
    # Create WhatsApp directory
    wa_dir = Path("whatsapp_mfa")
    wa_dir.mkdir(exist_ok=True)
    
    # Create config
    print("\n2️⃣  Creating WhatsApp configuration...\n")
    config = {
        "whatsapp_api": {
            "provider": "Meta/WhatsApp Cloud API",
            "endpoints": {
                "send_message": "https://graph.instagram.com/v18.0/{phone-number-id}/messages",
                "upload_media": "https://graph.instagram.com/v18.0/{phone-number-id}/media"
            }
        },
        "mfa_workflow": {
            "step_1": "User sends: 'setup mfa'",
            "step_2": "Bot sends: QR code image",
            "step_3": "Bot also sends: Manual secret key",
            "step_4": "User scans QR or enters key manually",
            "step_5": "User sends: 6-digit code",
            "step_6": "Bot sends: Backup recovery codes"
        },
        "qr_codes_generated": {
            acc["username"]: acc["qr_file"] for acc in accounts
        }
    }
    
    config_file = wa_dir / "whatsapp_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"  ✓ Config: {config_file}\n")
    
    # Create summary
    print("="*80)
    print("✅ SETUP COMPLETE!")
    print("="*80)
    print()
    
    print("📁 Files Created:")
    print(f"   QR Codes: qr_codes/")
    print(f"   WhatsApp Config: whatsapp_mfa/")
    print()
    
    print("📊 QR Codes Generated:")
    for acc in accounts:
        print(f"   • {acc['username']}")
        print(f"     File: {acc['qr_file']}")
        print(f"     Secret: {acc['secret'][:10]}...")
        print(f"     Codes: 8 backup recovery codes")
    
    print()
    print("🎯 FOR YOUR CLIENT:")
    print("   ✓ QR codes are actual image files - can be viewed/downloaded")
    print("   ✓ If scanning fails: Manual secret key provided as fallback")
    print("   ✓ Works with Microsoft Authenticator, Google Authenticator, Oracle")
    print()
    
    print("🠦  WHATSAPP WORKFLOW:")
    print("   User: 'setup mfa'")
    print("   Bot: [Sends QR code image] + [Sends manual key]")
    print("   User: Scans QR or enters key manually")
    print("   User: '123456' (6-digit code)")
    print("   Bot: 'MFA Enabled! Your backup codes: ...'")
    print()
    
    print("📝 Next Steps:")
    print("   1. Get WhatsApp Business account from https://www.whatsapp.com/business/")
    print("   2. Get Meta API credentials from https://developers.facebook.com/")
    print("   3. Deploy Flask webhook (we'll create the code)")
    print("   4. Save credentials in environment variables")
    print("   5. Test: Send 'setup mfa' to your bot number")
    print()

if __name__ == "__main__":
    try:
        main()
        print("✅ Ready for WhatsApp integration!\n")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
