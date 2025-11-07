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

    cursor.execute("SELECT version_number FROM db_metadata ORDER BY version_number DESC LIMIT 1")
    db_version = cursor.fetchone()
    print(f"Database versie: {db_version[0] if db_version else 'GEEN VERSIE'}")

    cursor.execute("PRAGMA table_info(planning)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Planning heeft 'notitie' kolom: {'notitie' in columns}")

    conn.close()

print("Test einde")