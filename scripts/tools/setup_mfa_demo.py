#!/usr/bin/env python3
"""
Simple MFA Demo Account Setup
Creates demo accounts with MFA enabled for presentation
"""

import hashlib
import json
import secrets
import sqlite3
import sys
from pathlib import Path

import pyotp

# Import security function
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.core.security import hash_password


def hash_recovery_code(code):
    """Hash recovery code for storage."""
    return hashlib.sha256(code.upper().encode()).hexdigest()


def generate_recovery_codes(count=8):
    """Generate recovery codes (backup codes)."""
    codes = []
    for _ in range(count):
        code = "".join(
            secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)
        )
        codes.append(f"{code[:4]}-{code[4:]}")
    return codes


def create_demo_account(db_path, username, password):
    """Create a demo account with MFA enabled."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        print(f"  ⚠️  {username} already exists (skipping)")
        conn.close()
        return None

    try:
        # Generate MFA components
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=username, issuer_name="AI Project Assistant")
        recovery_codes = generate_recovery_codes()
        hashed_codes = [hash_recovery_code(code) for code in recovery_codes]

        # Hash password
        password_hash = hash_password(password)

        # Create account
        cursor.execute(
            """
            INSERT INTO users (username, password_hash, mfa_enabled, mfa_secret, mfa_backup_codes)
            VALUES (?, ?, ?, ?, ?)
        """,
            (username, password_hash, 1, secret, json.dumps(hashed_codes)),
        )

        conn.commit()
        user_id = cursor.lastrowid

        print(f"  ✓ {username}: MFA enabled (ID: {user_id})")

        return {
            "user_id": user_id,
            "username": username,
            "secret": secret,
            "provisioning_uri": uri,
            "recovery_codes": recovery_codes,
        }
    except Exception as e:
        print(f"  ✗ {username}: {str(e)}")
        conn.rollback()
        return None
    finally:
        conn.close()


def main():
    print("\n" + "=" * 80)
    print("MFA DEMO ACCOUNT SETUP")
    print("=" * 80 + "\n")

    db_path = "chatbot_data/chatbot.db"

    print("Creating demo accounts with MFA enabled...\n")

    accounts = []
    for username, password in [
        ("demo_user", "demo123"),
        ("demo_admin", "admin123"),
        ("demo_partner", "partner123"),
    ]:
        data = create_demo_account(db_path, username, password)
        if data:
            accounts.append(data)

    if not accounts:
        print("\n❌ No accounts created! Check database.")
        return False

    # Create summary file
    summary_path = Path("demo_mfa_setup")
    summary_path.mkdir(exist_ok=True)

    summary = {"created_at": str(Path(__file__).resolve()), "accounts": []}

    print("\n" + "=" * 80)
    print("DEMO ACCOUNTS SUMMARY")
    print("=" * 80 + "\n")

    for account in accounts:
        print(f"📱 Account: {account['username']}")
        print(f"   Secret:        {account['secret']}")
        print(f"   Setup URI:     {account['provisioning_uri'][:50]}...")
        print(f"   Backup Codes:  {account['recovery_codes'][:2]}")
        print()

        summary["accounts"].append(
            {
                "username": account["username"],
                "secret": account["secret"],
                "recovery_codes": account["recovery_codes"],
            }
        )

    # Save summary
    summary_file = summary_path / "demo_accounts.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Summary saved to: {summary_file}")

    print("\n" + "=" * 80)
    print("✅ DEMO SETUP COMPLETE!")
    print("=" * 80)
    print("\n📋 NEXT STEPS:")
    print(
        "   1. Launch app: python MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)"
    )
    print("   2. Login with: demo_user / demo123")
    print("   3. Click '🔐 Security' button")
    print("   4. Click 'Generate QR Setup' to see QR code")
    print("   5. Scan QR with Microsoft Authenticator or Oracle Authenticator")
    print("   6. Enter 6-digit code to enable MFA")
    print("\n")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
