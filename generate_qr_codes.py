#!/usr/bin/env python3
"""
Generate QR codes from existing accounts
"""

import sqlite3
import json
import qrcode
from pathlib import Path
import pyotp

db_path = "chatbot_data/chatbot.db"
qr_dir = Path("qr_codes")
qr_dir.mkdir(exist_ok=True)

print("\n" + "="*80)
print("GENERATING QR CODES FOR EXISTING DEMO ACCOUNTS")
print("="*80 + "\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get demo accounts with MFA enabled
cursor.execute("""
    SELECT id, username, mfa_secret 
    FROM users 
    WHERE username LIKE 'demo%' AND mfa_enabled = 1
""")

accounts = cursor.fetchall()
print(f"Found {len(accounts)} demo accounts with MFA enabled\n")

for user_id, username, secret in accounts:
    print(f"📱 Generating QR for {username}...")
    
    # Create provisioning URI
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=username, issuer_name="AI Project Assistant")
    
    # Generate QR code with high error correction (for reliable scanning)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=15,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save file
    qr_file = qr_dir / f"mfa_{username}_qr.png"
    img.save(qr_file)
    
    print(f"   ✓ QR code saved: {qr_file}")
    print(f"   ✓ File size: {qr_file.stat().st_size} bytes")
    print(f"   ✓ Secret: {secret[:10]}...")
    print(f"   ✓ Can be scanned by:")
    print(f"     - Microsoft Authenticator")
    print(f"     - Google Authenticator")
    print(f"     - Oracle Authenticator")
    print(f"     - Any TOTP app")
    print()

conn.close()

# Create a README for QR codes
readme = """# QR Codes for MFA Setup

These are high-resolution QR codes that can be scanned by any TOTP authenticator app.

## Files

- `mfa_demo_user_qr.png` - For demo_user account
- `mfa_demo_admin_qr.png` - For demo_admin account
- `mfa_demo_partner_qr.png` - For demo_partner account

## How to Use

### Option 1: Scan with Phone (Recommended)
1. Open Microsoft Authenticator, Google Authenticator, or similar
2. Tap "+" to add account
3. Select "Scan QR code"
4. Point at the QR code
5. It automatically adds the account

### Option 2: View on Screen
1. Display this image on your presentation screen
2. User scans from phone camera
3. Works even if they can't physically get to the QR code

### Option 3: Download & Share
1. Download the PNG file
2. Share via email, WhatsApp, etc.
3. User scans from their device

### Option 4: Manual Setup (If Scanning Fails)
If QR scanning doesn't work:
1. Open authenticator app
2. Tap "+" → "Enter setup key"
3. Use the base32 secret (from database)
4. Enter manually

## Specifications

- Format: PNG image
- Size: ~200x200 pixels
- Error Correction: High (can scan even if damaged)
- Encoding: QR v1
- Standard: RFC 6238 TOTP

## For WhatsApp Integration

These QR codes can be sent via WhatsApp:
1. Save the PNG file
2. Upload to WhatsApp
3. User receives it in chat
4. They can scan directly from message

## Troubleshooting

**QR won't scan?**
- Check camera focus
- Ensure adequate lighting
- Try manual setup with secret key
- Or use a different authenticator app

**Code doesn't work after scanning?**
- Ensure phone time is set to automatic
- Wait for code to refresh (every 30 seconds)
- Check issuer name matches: "AI Project Assistant"

"""

readme_file = qr_dir / "README.md"
with open(readme_file, 'w') as f:
    f.write(readme)

print("\n" + "="*80)
print("✅ QR CODE GENERATION COMPLETE!")
print("="*80)
print(f"\nAll QR codes saved to: {qr_dir}/")
print(f"Total files: {len(list(qr_dir.glob('*.png')))}")
print()
print("🎯 USAGE:")
print("   ✓ Display on screen during presentation")
print("   ✓ Send via WhatsApp (PNG attachment)")
print("   ✓ Share via email / download links")
print("   ✓ Print for events")
print()
print("🠦  WHATSAPP INTEGRATION:")
print("   User sends: 🠦 'setup mfa'")
print("   Bot sends: QR code file (PNG) + manual secret")
print("   User scans QR code")
print("   User sends: '123456' (6-digit code)")
print("   Bot sends: Success message + backup codes")
print()
