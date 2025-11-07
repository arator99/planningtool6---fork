"""
Database Versie Update: v0.6.20 -> v0.6.21
Toevoegen is_kritisch kolom aan shift_codes tabel voor selectieve bemanningscontrole

Wijzigingen:
- shift_codes tabel: nieuwe kolom is_kritisch BOOLEAN DEFAULT 0
- Alleen kritische shifts tellen mee voor bemanningscontrole overlay
"""

import sqlite3
import sys
from pathlib import Path

def upgrade():
    """Update database versie van 0.6.20 naar 0.6.21"""

    db_path = Path("data/planning.db")

    if not db_path.exists():
        print("[ERROR] Database niet gevonden: data/planning.db")
        sys.exit(1)

    print("\n=== Database Versie Update: v0.6.20 -> v0.6.21 ===\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check huidige versie
        cursor.execute("SELECT version_number FROM db_metadata ORDER BY version_number DESC LIMIT 1")
        current_version = cursor.fetchone()

        if current_version:
            print(f"[INFO] Huidige database versie: {current_version[0]}")
        else:
            print("[ERROR] Geen versie gevonden in db_metadata")
            sys.exit(1)

        if current_version[0] == "0.6.21":
            print("[OK] Database is al op versie 0.6.21 - geen update nodig")
            conn.close()
            return

        # Check of is_kritisch kolom al bestaat
        cursor.execute("PRAGMA table_info(shift_codes)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'is_kritisch' in columns:
            print("[OK] is_kritisch kolom bestaat al - alleen versie updaten")
        else:
            # Voeg is_kritisch kolom toe
            print("[...] Toevoegen is_kritisch kolom aan shift_codes tabel...")

            cursor.execute("""
                ALTER TABLE shift_codes
                ADD COLUMN is_kritisch BOOLEAN DEFAULT 0
            """)

            print("[OK] Kolom is_kritisch toegevoegd")

        # Update versie naar 0.6.21
        print("[...] Updaten database versie naar 0.6.21...")

        cursor.execute("""
            INSERT INTO db_metadata (version_number, migration_description)
            VALUES (?, ?)
        """, (
            "0.6.21",
            "Kritische shift codes: is_kritisch kolom voor selectieve bemanningscontrole"
        ))

        conn.commit()
        print("[OK] Database versie updated naar 0.6.21")

        # Verificatie
        cursor.execute("SELECT version_number FROM db_metadata ORDER BY version_number DESC LIMIT 1")
        new_version = cursor.fetchone()

        cursor.execute("PRAGMA table_info(shift_codes)")
        columns = [row[1] for row in cursor.fetchall()]

        if new_version and new_version[0] == "0.6.21" and 'is_kritisch' in columns:
            print("[OK] Verificatie geslaagd")
            print("\n[SUCCESS] Database upgrade voltooid!")
            print("\nDatabase is nu compatible met Planning Tool v0.6.21")
            print("\nWijzigingen:")
            print("- shift_codes.is_kritisch kolom toegevoegd")
            print("- Alleen kritische shifts tellen mee voor bemanningscontrole\n")
        else:
            print("[ERROR] Verificatie gefaald")
            conn.rollback()
            sys.exit(1)

    except sqlite3.Error as e:
        print(f"[ERROR] Database fout: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    upgrade()
