"""
Database Migratie: Planning Notities Kolom
Voegt notitie kolom toe aan planning tabel voor herinneringen/opmerkingen

Versie: v0.6.15 -> v0.6.16
Datum: 23 Oktober 2025
"""

import sqlite3
import sys
from pathlib import Path

def migrate():
    """Voeg notitie kolom toe aan planning tabel"""

    db_path = Path("data/planning.db")

    if not db_path.exists():
        print("[ERROR] Database niet gevonden: data/planning.db")
        print("Voer dit script uit vanuit de root directory van het project.")
        sys.exit(1)

    print("\n=== Planning Notities Migratie ===\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check of notitie kolom al bestaat
        cursor.execute("PRAGMA table_info(planning)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'notitie' in columns:
            print("[OK] Notitie kolom bestaat al - migratie niet nodig")
            conn.close()
            return

        print("[INFO] Notitie kolom niet gevonden - starten migratie...")

        # Voeg notitie kolom toe
        print("[...] Toevoegen notitie kolom aan planning tabel...")
        cursor.execute("""
            ALTER TABLE planning
            ADD COLUMN notitie TEXT
        """)

        conn.commit()
        print("[OK] Notitie kolom toegevoegd")

        # Verificatie
        cursor.execute("PRAGMA table_info(planning)")
        columns_after = [row[1] for row in cursor.fetchall()]

        if 'notitie' in columns_after:
            print("[OK] Verificatie geslaagd - notitie kolom is aanwezig")
        else:
            print("[ERROR] Verificatie gefaald - notitie kolom niet gevonden")
            conn.rollback()
            sys.exit(1)

        print("\n[SUCCESS] Migratie voltooid!")
        print("\nDe planning tabel heeft nu een notitie kolom voor herinneringen.")
        print("Gebruik: Rechtermuisklik op cel -> Notitie toevoegen\n")

    except sqlite3.Error as e:
        print(f"[ERROR] Database fout: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
