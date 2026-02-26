import sqlite3
from pathlib import Path

db_path = Path("chatbot_data") / "chatbot.db"
if not db_path.exists():
    print(f"Database not found: {db_path}")
    raise SystemExit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

tables = ["tasks", "notes", "conversations", "files", "settings", "users"]

for t in tables:
    print("\n" + "=" * 60)
    print(f"Table: {t}")
    try:
        cur.execute(f"PRAGMA table_info({t})")
        cols = cur.fetchall()
        if not cols:
            print("  (no such table)")
            continue
        for c in cols:
            # c: (cid, name, type, notnull, dflt_value, pk)
            print(f"  - {c[1]} ({c[2]})")
    except Exception as e:
        print(f"  Error reading table {t}: {e}")

conn.close()
print("\nDone")
