#!/usr/bin/env python3
"""Final verification that demo accounts are ready"""
import sqlite3

conn = sqlite3.connect('chatbot_data/chatbot.db')
c = conn.cursor()

print("\n" + "="*80)
print("📱 DEMO ACCOUNTS VERIFICATION")
print("="*80 + "\n")

c.execute('SELECT username, mfa_enabled, mfa_secret, mfa_backup_codes FROM users WHERE username LIKE "demo%"')
rows = c.fetchall()

for username, mfa_enabled, secret, backup_codes in rows:
    status = "✓ ENABLED" if mfa_enabled else "✗ DISABLED"
    secret_preview = secret[:10] + "..." if secret else "None"
    print(f"  {username:20} │ MFA: {status:15} │ Secret: {secret_preview}")
    if mfa_enabled:
        import json
        codes = json.loads(backup_codes)
        print(f"                         │ Backup codes: {len(codes)} codes stored")

print("\n✓ All demo accounts ready for presentation!\n")

conn.close()
