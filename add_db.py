import sqlite3

def upgrade_database():
    conn = sqlite3.connect("data/jalan-ready.db")
    cursor = conn.cursor()
    try:
        # Adds the new column and defaults all existing tickets to 1
        cursor.execute("ALTER TABLE reports ADD COLUMN report_count INTEGER DEFAULT 1;")
        conn.commit()
        print("✅ [SUCCESS] Added 'report_count' to the existing database!")
    except sqlite3.OperationalError as e:
        print(f"⚠️ [NOTICE] {e} (The column might already exist)")
    finally:
        conn.close()

if __name__ == "__main__":
    upgrade_database()