import sqlite3
import os

db_path = "database/sample_data/chinook.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Test query (same as in your LangChain docs)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("✅ Database connected successfully!")
    print("📊 Available tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Test sample query
    cursor.execute("SELECT COUNT(*) FROM Artist;")
    count = cursor.fetchone()[0]
    print(f"🎵 Total artists: {count}")
    
    conn.close()
else:
    print("❌ Database file not found at:", db_path)
    print("Make sure you downloaded chinook.db") 