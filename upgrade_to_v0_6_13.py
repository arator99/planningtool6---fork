#!/usr/bin/env python3
"""
Database Upgrade: v0.6.12 → v0.6.13
Doel: Toevoegen db_metadata tabel voor versie tracking

Gebruik:
    python upgrade_to_v0_6_13.py

Dit script:
1. Controleert of db_metadata tabel al bestaat
2. Maakt tabel aan indien nodig
3. Initialiseert versienummer op 0.6.12 (laatste DB schema wijziging voor v0.6.13)
4. Idempotent: kan meerdere keren uitgevoerd worden zonder problemen

Auteur: Planning Tool Team
Datum: 21 Oktober 2025
"""

import sqlite3
from pathlib import Path
from config import MIN_DB_VERSION

def upgrade_database():
    """Upgrade database naar v0.6.13"""

    db_path = Path("data/planning.db")

    if not db_path.exists():
        print(f"[FOUT] Database niet gevonden op {db_path}")
        print("       De database wordt automatisch aangemaakt bij eerste start.")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check of tabel al bestaat
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='db_metadata'
        """)

        if cursor.fetchone():
            print("[OK] db_metadata tabel bestaat al")

            # Toon huidige versie
            cursor.execute("SELECT version_number, updated_at FROM db_metadata ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                print(f"     Database versie: {result[0]}")
                print(f"     Bijgewerkt op: {result[1]}")

            conn.close()
            return True

        print("[>>] Aanmaken db_metadata tabel...")

        # Maak tabel aan
        cursor.execute("""
            CREATE TABLE db_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_number TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                migration_description TEXT
            )
        """)

        # Initialiseer met v0.6.13 (huidige versie met db_metadata tabel)
        cursor.execute("""
            INSERT INTO db_metadata (version_number, migration_description)
            VALUES (?, ?)
        """, (MIN_DB_VERSION, f"Upgrade naar v{MIN_DB_VERSION} - Database versie tracking systeem toegevoegd"))

        conn.commit()
        print("[OK] db_metadata tabel aangemaakt")
        print(f"[OK] Database versie ingesteld op {MIN_DB_VERSION}")

        return True

    except sqlite3.Error as e:
        print(f"[FOUT] Database error: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("Database Upgrade naar v0.6.13")
    print("=" * 60)
    print()

    succes = upgrade_database()

    if succes:
        print()
        print("[OK] Upgrade succesvol afgerond!")
        print()
        print("De applicatie kan nu gestart worden.")
        print("Versie check zal automatisch plaatsvinden bij opstarten.")

    else:
        print()
        print("[FOUT] Upgrade mislukt")
        print()

    print("=" * 60)
