#!/usr/bin/env python3
import sqlite3
import os

db_path = 'chatbot_data/chatbot.db'
print(f'✓ DB exists: {os.path.exists(db_path)}')
if os.path.exists(db_path):
    print(f'✓ DB size: {os.path.getsize(db_path)} bytes')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f'✓ Tables: {tables}')
    
    # Check users table
    if 'users' in tables:
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f'✓ User columns: {columns}')
        
        # Check for MFA columns
        mfa_cols = [c for c in columns if 'mfa' in c]
        print(f'✓ MFA columns: {mfa_cols}')
    
    conn.close()
    print("\n✓ Database is accessible and ready!")
else:
    print(f'✗ Database not found at {db_path}')
