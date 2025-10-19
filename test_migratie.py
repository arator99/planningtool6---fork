# test_migratie.py
from pathlib import Path
import sqlite3

print("Test start")

db_path = Path("data/planning.db")
print(f"Database path: {db_path}")
print(f"Bestaat: {db_path.exists()}")

if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM werkposten")
    print(f"Werkposten: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM shift_codes")
    print(f"Shift codes: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM speciale_codes")
    print(f"Speciale codes: {cursor.fetchone()[0]}")

    conn.close()

print("Test einde")