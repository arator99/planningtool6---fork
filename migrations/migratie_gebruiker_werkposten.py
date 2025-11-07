#!/usr/bin/env python3
"""
Database Migratie: Gebruiker Werkposten Koppeling
Versie: 0.6.13 -> 0.6.14

Voegt gebruiker_werkposten tabel toe voor many-to-many relatie tussen
gebruikers en werkposten. Dit zorgt voor slimme auto-generatie van planning
waarbij de juiste shift code wordt gebruikt op basis van gebruiker's werkpost.

VEILIG: Idempotent - kan meerdere keren worden uitgevoerd
"""

import sqlite3
import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("DATABASE MIGRATIE: Gebruiker Werkposten Koppeling")
    print("Versie: 0.6.13 -> 0.6.14")
    print("=" * 60)
    print()

    # Database pad
    db_path = Path("data/planning.db")

    if not db_path.exists():
        print(f"ERROR: Database niet gevonden op {db_path}")
        sys.exit(1)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check of tabel al bestaat
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='gebruiker_werkposten'
        """)

        if cursor.fetchone():
            print("INFO: gebruiker_werkposten tabel bestaat al")
            print("      Migratie al uitgevoerd - SKIP")
            conn.close()
            return

        print("STAP 1: Aanmaken gebruiker_werkposten tabel...")

        cursor.execute("""
            CREATE TABLE gebruiker_werkposten (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gebruiker_id INTEGER NOT NULL,
                werkpost_id INTEGER NOT NULL,
                prioriteit INTEGER DEFAULT 1,
                aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(gebruiker_id, werkpost_id),
                FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id) ON DELETE CASCADE,
                FOREIGN KEY (werkpost_id) REFERENCES werkposten(id) ON DELETE CASCADE
            )
        """)
        print("   OK - Tabel aangemaakt")

        print()
        print("STAP 2: Index aanmaken voor performance...")

        cursor.execute("""
            CREATE INDEX idx_gebruiker_werkposten_gebruiker
            ON gebruiker_werkposten(gebruiker_id, prioriteit)
        """)
        print("   OK - Index aangemaakt")

        print()
        print("STAP 3: Seed data - Auto-koppel gebruikers aan eerste actieve werkpost...")

        # Haal eerste actieve werkpost op
        cursor.execute("""
            SELECT id, naam FROM werkposten
            WHERE is_actief = 1
            ORDER BY aangemaakt_op
            LIMIT 1
        """)
        eerste_werkpost = cursor.fetchone()

        if eerste_werkpost:
            werkpost_id, werkpost_naam = eerste_werkpost

            # Koppel alle actieve gebruikers (behalve admin, inclusief reserves) aan deze werkpost
            cursor.execute("""
                INSERT INTO gebruiker_werkposten (gebruiker_id, werkpost_id, prioriteit)
                SELECT id, ?, 1
                FROM gebruikers
                WHERE is_actief = 1
                  AND gebruikersnaam != 'admin'
            """, (werkpost_id,))

            aantal = cursor.rowcount
            print(f"   OK - {aantal} gebruikers gekoppeld aan '{werkpost_naam}'")
            print("        (Dit kan later worden aangepast in Werkpost Koppeling beheer)")
        else:
            print("   INFO - Geen actieve werkposten gevonden, geen seed data toegevoegd")

        # Commit changes
        conn.commit()

        print()
        print("=" * 60)
        print("MIGRATIE SUCCESVOL AFGEROND")
        print("=" * 60)
        print()
        print("VOLGENDE STAPPEN:")
        print("1. Start de applicatie")
        print("2. Ga naar Beheer -> Werkpost Koppeling")
        print("3. Configureer welke werkposten elke gebruiker kent")
        print("4. Auto-generatie gebruikt nu automatisch de juiste shift codes!")
        print()

    except sqlite3.Error as e:
        print(f"ERROR: Database fout - {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
