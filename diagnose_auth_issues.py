#!/usr/bin/env python3
"""
Diagnostic script to identify authentication and login system issues
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def check_imports():
    """Check if all required imports work"""
    print("📦 Checking imports...")
    try:
        import tkinter as tk
        print("  ✅ tkinter")
    except ImportError as e:
        print(f"  ❌ tkinter: {e}")
        return False
    
    try:
        import sqlite3
        print("  ✅ sqlite3")
    except ImportError as e:
        print(f"  ❌ sqlite3: {e}")
        return False
    
    try:
        from src.core.security import hash_password, verify_password
        print("  ✅ src.core.security")
    except ImportError as e:
        print(f"  ❌ src.core.security: {e}")
        return False
    
    try:
        from config.settings import settings
        print("  ✅ config.settings")
    except ImportError as e:
        print(f"  ❌ config.settings: {e}")
        return False
    
    print("✅ All imports successful\n")
    return True

def check_database_setup():
    """Check if database can be created"""
    print("💾 Checking database setup...")
    try:
        import sqlite3
        from pathlib import Path
        
        data_dir = Path("chatbot_data")
        data_dir.mkdir(exist_ok=True)
        db_path = data_dir / "chatbot.db"
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            DROP TABLE IF EXISTS users_test
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_date TEXT,
                last_login TEXT,
                role TEXT DEFAULT 'user',
                is_guest INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"  ✅ Database created at: {db_path}")
        print("✅ Database setup successful\n")
        return True
    except Exception as e:
        print(f"  ❌ Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_password_hashing():
    """Check if password hashing works"""
    print("🔐 Checking password hashing...")
    try:
        from src.core.security import hash_password, verify_password
        
        # Test basic hashing
        password = "test_password_123"
        hashed = hash_password(password)
        print(f"  ✅ Hashed password: {hashed[:50]}...")
        
        # Test verification
        if verify_password(password, hashed):
            print("  ✅ Password verification successful")
        else:
            print("  ❌ Password verification failed")
            return False
        
        # Test wrong password
        if verify_password("wrong_password", hashed):
            print("  ❌ Wrong password verified (security issue!)")
            return False
        else:
            print("  ✅ Wrong password correctly rejected")
        
        print("✅ Password hashing successful\n")
        return True
    except Exception as e:
        print(f"  ❌ Password hashing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_auth_system():
    """Check if UserAuthSystem works"""
    print("👤 Checking UserAuthSystem...")
    try:
        from pathlib import Path
        from enhanced_chatbot_pro import UserAuthSystem
        
        data_dir = Path("chatbot_data")
        data_dir.mkdir(exist_ok=True)
        db_path = data_dir / "test_auth.db"
        
        # Clean up test DB
        try:
            db_path.unlink()
        except:
            pass
        
        # Create auth system
        auth = UserAuthSystem(str(db_path))
        print("  ✅ UserAuthSystem created")
        
        # Test registration
        success, msg = auth.register_user("testuser", "password123", "test@example.com")
        if success:
            print(f"  ✅ User registration: {msg}")
        else:
            print(f"  ❌ User registration failed: {msg}")
            return False
        
        # Test login
        success, msg = auth.login_user("testuser", "password123")
        if success:
            print(f"  ✅ User login: {msg}")
        else:
            print(f"  ❌ User login failed: {msg}")
            return False
        
        # Test wrong password
        success, msg = auth.login_user("testuser", "wrongpassword")
        if success:
            print(f"  ❌ Wrong password accepted: {msg}")
            return False
        else:
            print(f"  ✅ Wrong password rejected: {msg}")
        
        # Test guest
        success, msg = auth.create_guest_user()
        if success:
            print(f"  ✅ Guest creation: {msg}")
        else:
            print(f"  ❌ Guest creation failed: {msg}")
            return False
        
        # Clean up
        try:
            db_path.unlink()
        except:
            pass
        
        print("✅ UserAuthSystem works correctly\n")
        return True
    except Exception as e:
        print(f"  ❌ UserAuthSystem check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostics"""
    print("=" * 70)
    print("🔍 AI PROJECT ASSISTANT PRO - DIAGNOSTIC REPORT")
    print("=" * 70)
    print()
    
    results = {
        "Imports": check_imports(),
        "Database": check_database_setup(),
        "Password Hashing": check_password_hashing(),
        "Auth System": check_auth_system(),
    }
    
    print("=" * 70)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 70)
    
    for category, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {category:.<50} {status}")
    
    print()
    
    all_pass = all(results.values())
    if all_pass:
        print("🎉 All diagnostics passed! App should run correctly.")
        print("\n✅ Ready to start the application:")
        print("   python MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)")
        sys.exit(0)
    else:
        print("⚠️  Some diagnostics failed!")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Install missing dependencies: pip install -r requirements.txt")
        print("   2. Check file permissions for chatbot_data/ directory")
        print("   3. Verify Python version (3.7+)")
        print("   4. Check for file encoding issues")
        sys.exit(1)

if __name__ == "__main__":
    main()
