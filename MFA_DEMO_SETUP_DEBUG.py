#!/usr/bin/env python3
"""
MFA Demo Setup - Debug Version
"""

import sys
from pathlib import Path

print("Starting MFA Demo Setup Debug...", flush=True)

try:
    print("Step 1: Importing modules...", flush=True)
    import sqlite3
    print("  ✓ sqlite3", flush=True)
    import json
    print("  ✓ json", flush=True)
    import pyotp
    print("  ✓ pyotp", flush=True)
    import qrcode
    print("  ✓ qrcode", flush=True)
    from datetime import datetime
    print("  ✓ datetime", flush=True)
    import hashlib
    print("  ✓ hashlib", flush=True)
    import secrets
    print("  ✓ secrets", flush=True)
    
    print("\nStep 2: Importing security functions...", flush=True)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from src.core.security import hash_password
    print("  ✓ hash_password imported", flush=True)
    
    print("\nStep 3: Checking database...", flush=True)
    db_path = 'chatbot_data/chatbot.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"  ✓ Database connected, tables: {tables}", flush=True)
    conn.close()
    
    print("\nStep 4: Creating demo account class...", flush=True)
    
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
        
        def create_demo_account(self, username, password):
            """Create demo account."""
            print(f"  Creating account: {username}", flush=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                print(f"    - Already exists, skipping", flush=True)
                conn.close()
                return True, {}
            
            # Generate MFA secret
            secret = pyotp.random_base32()
            totp = pyotp.TOTP(secret)
            uri = totp.provisioning_uri(name=username, issuer_name="AI Project Assistant")
            recovery_codes = self._generate_recovery_codes()
            hashed_codes = [self._hash_recovery_code(code) for code in recovery_codes]
            
            # Hash password
            password_hash = hash_password(password)
            print(f"    - Password hashed", flush=True)
            
            # Insert user
            try:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, mfa_enabled, mfa_secret, mfa_backup_codes)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, password_hash, 1, secret, json.dumps(hashed_codes)))
                
                conn.commit()
                user_id = cursor.lastrowid
                conn.close()
                
                print(f"    ✓ Account created (ID: {user_id})", flush=True)
                
                return True, {
                    "user_id": user_id,
                    "username": username,
                    "secret": secret,
                    "provisioning_uri": uri,
                    "recovery_codes": recovery_codes
                }
            except Exception as e:
                conn.close()
                print(f"    ✗ Error: {str(e)}", flush=True)
                raise
    
    print("  ✓ Class created", flush=True)
    
    print("\nStep 5: Creating demo accounts...", flush=True)
    setup = MFADemoSetup()
    
    accounts = []
    for username, password in [("demo_user", "demo123"), ("demo_admin", "admin123"), ("demo_partner", "partner123")]:
        ok, data = setup.create_demo_account(username, password)
        if ok and data:
            accounts.append((username, data))
    
    print(f"\n✓ Setup complete! Created {len(accounts)} accounts\n", flush=True)
    
    for username, data in accounts:
        print(f"Account: {username}")
        print(f"  Secret: {data['secret']}")
        print(f"  Codes: {', '.join(data['recovery_codes'][:2])}...")
    
except Exception as e:
    import traceback
    print(f"\n✗ ERROR: {str(e)}", flush=True)
    traceback.print_exc()
    sys.exit(1)
