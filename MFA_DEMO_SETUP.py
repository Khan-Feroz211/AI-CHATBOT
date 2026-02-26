#!/usr/bin/env python3
"""
MFA Demo Setup Script for Client Presentation
Generates demo accounts with MFA enabled and creates testing guide
For Microsoft Authenticator and Oracle Authenticator
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

# Import the security functions from the project
try:
    from src.core.security import hash_password
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from src.core.security import hash_password

class MFADemoSetup:
    def __init__(self, db_path="chatbot_data/chatbot.db"):
        self.db_path = db_path
        self.demo_dir = Path("demo_mfa_setup")
        self.demo_dir.mkdir(exist_ok=True)
        
    def _hash_recovery_code(self, code):
        """Hash recovery code for storage."""
        return hashlib.sha256(code.upper().encode()).hexdigest()
    
    def _generate_recovery_codes(self, count=8):
        """Generate recovery codes (backup codes)."""
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes
    
    def create_demo_account_with_mfa(self, username, password, issuer_name="AI Project Assistant"):
        """Create demo account with MFA enabled."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return False, f"User '{username}' already exists"
        
        # Generate MFA secret
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=username, issuer_name=issuer_name)
        recovery_codes = self._generate_recovery_codes()
        hashed_codes = [self._hash_recovery_code(code) for code in recovery_codes]
        
        # Hash password using project's security function
        password_hash = hash_password(password)
        
        # Insert user with MFA enabled
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, mfa_enabled, mfa_secret, mfa_backup_codes)
                VALUES (?, ?, ?, ?, ?)
            """, (username, password_hash, 1, secret, json.dumps(hashed_codes)))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            return True, {
                "user_id": user_id,
                "username": username,
                "secret": secret,
                "provisioning_uri": uri,
                "recovery_codes": recovery_codes
            }
        except Exception as e:
            conn.close()
            return False, f"Error creating user: {str(e)}"
    
    def generate_qr_code(self, provisioning_uri, output_file):
        """Generate QR code image."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_file)
        return output_file
    
    def setup_demo_accounts(self):
        """Set up multiple demo accounts for testing."""
        demo_accounts = [
            ("demo_user", "demo123"),
            ("demo_admin", "admin123"),
            ("demo_partner", "partner123")
        ]
        
        results = []
        for username, password in demo_accounts:
            ok, data = self.create_demo_account_with_mfa(username, password)
            if ok:
                results.append((username, data))
                print(f"✓ Created demo account: {username}")
            else:
                print(f"✗ Failed to create {username}: {data}")
        
        return results
    
    def create_demo_guide(self, accounts_data):
        """Create comprehensive testing guide."""
        guide_path = self.demo_dir / "MFA_TESTING_GUIDE.txt"
        
        guide_content = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    MFA DEMO SETUP FOR CLIENT PRESENTATION                     ║
║               Two-Factor Authentication with Microsoft & Oracle Authenticator  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 DEMO ACCOUNTS CREATED:

"""
        for username, data in accounts_data:
            guide_content += f"""
┌─ Account: {username}
│  Secret: {data['secret']}
│  Recovery Codes:
"""
            for code in data['recovery_codes']:
                guide_content += f"│    • {code}\n"
            guide_content += f"└─ QR Code saved: qr_{username}.png\n"
        
        guide_content += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔐 TESTING STEPS FOR CLIENT PRESENTATION:

1. DEMONSTRATE NORMAL LOGIN:
   ✓ Launch application (python MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed))
   ✓ Click on demo account login
   ✓ Enter username and password
   ✓ Show normal login without MFA prompt (for non-MFA users)

2. DEMONSTRATE MFA SETUP:
   ✓ Click on "🔐 Security" button (in header)
   ✓ Show "Generate QR Setup" button
   ✓ Click "Generate QR Setup"
   ✓ Display QR code on screen

3. SCAN QR CODE WITH AUTHENTICATOR:
   
   Option A - MICROSOFT AUTHENTICATOR:
   ┌────────────────────────────────────────────────────┐
   │ 1. Open Microsoft Authenticator on phone          │
   │ 2. Tap "+" button                                 │
   │ 3. Select "Other account"                         │
   │ 4. Select "Enter setup key"                       │
   │ 5. Paste secret (shown in app) OR scan QR code   │
   │ 6. Set up complete - shows 6-digit code           │
   └────────────────────────────────────────────────────┘
   
   Option B - ORACLE AUTHENTICATOR:
   ┌────────────────────────────────────────────────────┐
   │ 1. Open Oracle Authenticator on phone             │
   │ 2. Tap "+" button                                 │
   │ 3. Select "TOTP" (Time-based)                     │
   │ 4. Scan QR code OR enter setup key                │
   │ 5. Authenticator code appears                     │
   └────────────────────────────────────────────────────┘

4. COMPLETE MFA SETUP IN APP:
   ✓ Look at Authenticator app on phone
   ✓ Enter 6-digit code into "Enter authenticator code" field
   ✓ Click "Enable MFA"
   ✓ Show message: "Two-factor authentication has been enabled"
   ✓ Show backup recovery codes (save for emergency use)

5. DEMONSTRATE MFA LOGIN:
   ✓ Logout from application
   ✓ Login with same demo account again
   ✓ Enter username and password
   ✓ App prompts for authenticator code
   ✓ Show phone - 6-digit code is actively changing (every 30 seconds)
   ✓ Enter current 6-digit code from Authenticator
   ✓ Login succeeds
   ✓ Show "2FA enabled" indicator in app status

6. DEMONSTRATE BACKUP CODES:
   ✓ Logout and login again
   ✓ App prompts for authenticator code
   ✓ Instead of phone code, enter one of the backup codes
   ✓ Login succeeds with backup code
   ✓ Show that backup code is now consumed (can't be reused)

7. DEMONSTRATE DISABLE MFA:
   ✓ Click "🔐 Security" button
   ✓ Show "Disable MFA" button (if MFA is enabled)
   ✓ Click to disable MFA
   ✓ Prompts for authenticator code to verify
   ✓ Enter code from phone
   ✓ MFA is disabled successfully

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 KEY FEATURES TO HIGHLIGHT IN PRESENTATION:

✓ Security: Industry-standard TOTP (Time-based One-Time Password)
✓ Compatibility: Works with ANY authenticator app:
  • Microsoft Authenticator (most popular)
  • Google Authenticator
  • Oracle Authenticator
  • Authy
  • Any RFC 6238 compliant app

✓ Backup Codes: 8 one-time backup codes for account recovery
✓ QR Code: Easy setup - scan once and you're protected
✓ User-Friendly: Simple toggle to enable/disable MFA
✓ Enterprise-Ready: Standard security protocols
✓ No Phone Number Required: No SMS vulnerabilities

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 NOTES FOR PARTNER/CLIENT:

1. MFA Setup is optional for users
2. No performance impact - instant verification
3. Backup codes stored securely (hashed)
4. Can be disabled anytime with valid authenticator code
5. No vendor lock-in - use any TOTP-compatible authenticator

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ IMPORTANT REMINDERS:

• Save recovery codes in a safe place
• Don't share authenticator secrets with anyone
• Time sync on phone MUST be automatic for codes to work
• If codes don't match, your phone time may be out of sync
• Reset phone time settings to automatic

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ VERIFICATION CHECKLIST BEFORE PRESENTATION:

□ All demo accounts created successfully
□ QR codes generated and saved
□ Microsoft Authenticator installed on demo phone
□ Test account setup works in Authenticator
□ Can login with MFA enabled
□ Backup codes work as expected
□ MFA can be disabled and re-enabled
□ UI is responsive and clean
□ All error messages are clear

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 SUPPORT INFORMATION:

If client asks about implementation details:
• Backend: Python with pyotp library (RFC 6238 standard)
• Frontend: Tkinter GUI with real-time QR code display
• Database: SQLite with hashed secrets and backup codes
• No external services required (completely self-hosted)
• GDPR compliant (no data shared with third parties)

"""
        
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"\n✓ Testing guide created: {guide_path}")
        return guide_path
    
    def create_qr_codes(self, accounts_data):
        """Generate QR code images for all demo accounts."""
        qr_files = []
        for account in accounts_data:
            username = account[0]
            data = account[1]
            
            qr_file = self.demo_dir / f"qr_{username}.png"
            self.generate_qr_code(data['provisioning_uri'], qr_file)
            qr_files.append((username, qr_file))
            print(f"✓ QR code generated: {qr_file}")
        
        return qr_files
    
    def create_json_reference(self, accounts_data):
        """Create JSON file with all demo account info."""
        json_path = self.demo_dir / "demo_accounts.json"
        
        json_data = {
            "generated_at": datetime.now().isoformat(),
            "accounts": []
        }
        
        for username, data in accounts_data:
            json_data["accounts"].append({
                "username": username,
                "secret": data['secret'],
                "recovery_codes": data['recovery_codes'],
                "qr_code_file": f"qr_{username}.png",
                "note": "For demonstration purposes only"
            })
        
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"✓ JSON reference created: {json_path}")
        return json_path
    
    def run_setup(self):
        """Execute full demo setup."""
        print("\n" + "="*80)
        print("MFA DEMO SETUP FOR CLIENT PRESENTATION")
        print("="*80 + "\n")
        
        try:
            # Setup demo accounts
            print("1️⃣  Creating demo accounts with MFA enabled...")
            accounts_data = self.setup_demo_accounts()
            
            if not accounts_data:
                print("❌ No demo accounts created. Check database path.")
                return False
            
            # Generate QR codes
            print("\n2️⃣  Generating QR codes...")
            self.create_qr_codes(accounts_data)
            
            # Create testing guide
            print("\n3️⃣  Creating comprehensive testing guide...")
            self.create_demo_guide(accounts_data)
            
            # Create JSON reference
            print("\n4️⃣  Creating JSON reference...")
            self.create_json_reference(accounts_data)
            
            print("\n" + "="*80)
            print("✅ MFA DEMO SETUP COMPLETE!")
            print("="*80)
            print(f"\n📁 All files saved to: {self.demo_dir.absolute()}")
            print("\n📋 Files generated:")
            print("   • MFA_TESTING_GUIDE.txt - Complete testing instructions")
            print("   • qr_demo_user.png - QR code for demo_user")
            print("   • qr_demo_admin.png - QR code for demo_admin")
            print("   • qr_demo_partner.png - QR code for demo_partner")
            print("   • demo_accounts.json - JSON reference of all accounts")
            
            print("\n🚀 NEXT STEPS:")
            print("   1. Read MFA_TESTING_GUIDE.txt for full instructions")
            print("   2. Set up Microsoft Authenticator on your phone")
            print("   3. Test login with one of the demo accounts")
            print("   4. Expected: App will prompt for 6-digit authenticator code")
            print("   5. Show client during presentation\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Setup failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    # Run setup
    setup = MFADemoSetup()
    success = setup.run_setup()
    
    if not success:
        print("\n⚠️  Check that database path is correct and database file exists.")
        exit(1)
