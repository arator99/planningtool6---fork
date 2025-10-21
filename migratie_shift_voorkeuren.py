"""
Database migratie script voor shift voorkeuren systeem
v0.6.10 -> v0.6.11

Voegt shift_voorkeuren kolom toe aan gebruikers tabel
Format: JSON string met prioriteit mapping
Voorbeeld: {"1": "vroeg", "2": "typetabel", "3": "laat", "4": "nacht"}
"""

import sqlite3
from pathlib import Path


def migreer_shift_voorkeuren():
    """Voeg shift_voorkeuren kolom toe aan gebruikers tabel"""

    db_path = Path("data/planning.db")
    if not db_path.exists():
        print("Database niet gevonden. Run eerst main.py om database aan te maken.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check of kolom al bestaat
        cursor.execute("PRAGMA table_info(gebruikers)")
        kolommen = [row[1] for row in cursor.fetchall()]

        if 'shift_voorkeuren' in kolommen:
            print("Shift voorkeuren kolom bestaat al. Migratie al uitgevoerd.")
            conn.close()
            return

        print("Start migratie: shift_voorkeuren kolom toevoegen...")

        # Voeg kolom toe
        cursor.execute("""
            ALTER TABLE gebruikers
            ADD COLUMN shift_voorkeuren TEXT
        """)

        conn.commit()
        print("Migratie succesvol! Shift voorkeuren kolom toegevoegd.")

        # Toon voorbeeld gebruik
        print("\nVoorbeeld JSON format:")
        print('  {"1": "vroeg", "2": "typetabel", "3": "laat"}')
        print("\nOpties:")
        print("  - vroeg: Voorkeur voor vroege diensten")
        print("  - laat: Voorkeur voor late diensten")
        print("  - nacht: Voorkeur voor nachtdiensten")
        print("  - typetabel: Volg de typetabel (standaard)")
        print("\nGebruikers kunnen 1-4 voorkeuren instellen in volgorde van prioriteit.")
        print("Leeg = automatisch typetabel of vrije invulling volgen.")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database fout tijdens migratie: {e}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("PLANNING TOOL - Database Migratie")
    print("Shift Voorkeuren Systeem (v0.6.10 -> v0.6.11)")
    print("=" * 60)
    print()

    migreer_shift_voorkeuren()

    print()
    print("=" * 60)
    print("Migratie proces voltooid!")
    print("=" * 60)
