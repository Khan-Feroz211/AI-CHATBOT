"""
Database Migration Script - Fix Missing user_id Column
Run this ONCE to update your database schema
"""

import sqlite3
from pathlib import Path

def migrate_database():
    """Add user_id column to existing tables"""
    
    db_path = Path("chatbot_data") / "chatbot.db"
    
    if not db_path.exists():
        print("❌ Database not found!")
        return
    
    print("🔧 Starting database migration...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check and add user_id to tasks table
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("📋 Adding user_id column to tasks table...")
            cursor.execute('ALTER TABLE tasks ADD COLUMN user_id INTEGER')
            print("✅ Tasks table updated!")
        else:
            print("ℹ️ Tasks table already has user_id column")
        
        # Check and add user_id to notes table
        cursor.execute("PRAGMA table_info(notes)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("📝 Adding user_id column to notes table...")
            cursor.execute('ALTER TABLE notes ADD COLUMN user_id INTEGER')
            print("✅ Notes table updated!")
        else:
            print("ℹ️ Notes table already has user_id column")
        
        # Get first user ID (for existing data)
        cursor.execute("SELECT id FROM users LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            first_user_id = result[0]
            
            # Update existing tasks with first user ID
            cursor.execute("UPDATE tasks SET user_id = ? WHERE user_id IS NULL", (first_user_id,))
            affected_tasks = cursor.rowcount
            if affected_tasks > 0:
                print(f"📋 Updated {affected_tasks} existing tasks")
            
            # Update existing notes with first user ID
            cursor.execute("UPDATE notes SET user_id = ? WHERE user_id IS NULL", (first_user_id,))
            affected_notes = cursor.rowcount
            if affected_notes > 0:
                print(f"📝 Updated {affected_notes} existing notes")
        
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        print("\n🚀 You can now run the app: python enhanced_chatbot_pro.py")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION SCRIPT".center(60))
    print("=" * 60)
    print()
    
    migrate_database()
    
    print()
    print("=" * 60)
