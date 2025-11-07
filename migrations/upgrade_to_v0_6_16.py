"""
Database Versie Update: v0.6.14 -> v0.6.16
Update alleen de db_metadata versie (schema is al correct)

Wijzigingen:
- v0.6.14 -> v0.6.15: Concept/Gepubliceerd planning status (GUI only, geen DB wijziging)
- v0.6.15 -> v0.6.16: Planning notitie kolom (al toegepast)
"""

import sqlite3
import sys
from pathlib import Path

def upgrade():
    """Update database versie van 0.6.14 naar 0.6.16"""

    db_path = Path("data/planning.db")

    if not db_path.exists():
        print("[ERROR] Database niet gevonden: data/planning.db")
        sys.exit(1)

    print("\n=== Database Versie Update: v0.6.14 -> v0.6.16 ===\n")

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

        if current_version[0] == "0.6.16":
            print("[OK] Database is al op versie 0.6.16 - geen update nodig")
            conn.close()
            return

        # Check of notitie kolom bestaat
        cursor.execute("PRAGMA table_info(planning)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'notitie' not in columns:
            print("[ERROR] Notitie kolom niet gevonden - run eerst migratie_planning_notities.py")
            sys.exit(1)

        print("[OK] Schema is correct (notitie kolom aanwezig)")

        # Update versie naar 0.6.16
        print("[...] Updaten database versie naar 0.6.16...")

        cursor.execute("""
            INSERT INTO db_metadata (version_number, migration_description)
            VALUES (?, ?)
        """, (
            "0.6.16",
            "Versie update: v0.6.14 -> v0.6.16 (notitie kolom + concept/gepubliceerd status)"
        ))

        conn.commit()
        print("[OK] Database versie updated naar 0.6.16")

        # Verificatie
        cursor.execute("SELECT version_number FROM db_metadata ORDER BY version_number DESC LIMIT 1")
        new_version = cursor.fetchone()

        if new_version and new_version[0] == "0.6.16":
            print("[OK] Verificatie geslaagd")
            print("\n[SUCCESS] Database upgrade voltooid!")
            print("\nDatabase is nu compatible met Planning Tool v0.6.16\n")
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