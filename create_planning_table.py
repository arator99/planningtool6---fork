# create_planning_table.py
"""
Maak planning tabel aan (tijdelijk, tot Planning Editor gemaakt is)
"""
import sqlite3
from pathlib import Path

db_path = Path("data/planning.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Maak planning tabel
cursor.execute("""
    CREATE TABLE IF NOT EXISTS planning (
        id INTEGER PRIMARY KEY,
        gebruiker_id INTEGER NOT NULL,
        datum TEXT NOT NULL,
        shift_code TEXT,
        status TEXT DEFAULT 'concept',
        aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id),
        UNIQUE(gebruiker_id, datum)
    )
""")

conn.commit()
conn.close()

print("✓ Planning tabel aangemaakt (leeg)")