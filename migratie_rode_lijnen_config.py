#!/usr/bin/env python3
"""
Database Migratie - Rode Lijnen Config
Voegt rode_lijnen_config tabel toe voor configureerbare HR cycli

ACHTERGROND:
- Rode lijnen worden gebruikt voor HR validatie (max werkdagen per cyclus)
- Momenteel hardcoded interval van 28 dagen vanaf 28 juli 2024
- Moet configureerbaar worden met historiek voor wijzigingen
- Validator moet juiste config gebruiken op basis van planning datum

WIJZIGINGEN:
- Nieuwe tabel rode_lijnen_config met versioning (actief_vanaf, actief_tot, is_actief)
- Start met default config (2024-07-28, 28 dagen interval)
- Services moeten config raadplegen ipv hardcoded waardes
"""

import sqlite3
from pathlib import Path


def migratie_rode_lijnen_config():
    """Voeg rode_lijnen_config tabel toe"""
    db_path = Path("data/planning.db")

    if not db_path.exists():
        print("XX Database niet gevonden op: data/planning.db")
        print("   Start eerst de applicatie om een database aan te maken.")
        return False

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Check of tabel al bestaat
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='rode_lijnen_config'
        """)

        if cursor.fetchone():
            print("OK Tabel rode_lijnen_config bestaat al")
            print("  Migratie is al uitgevoerd, niets te doen.")
            conn.close()
            return True

        print("="*60)
        print("Database Migratie - Rode Lijnen Config")
        print("="*60)
        print()

        # Stap 1: Maak rode_lijnen_config tabel
        print("[1/2] rode_lijnen_config tabel aanmaken...")
        cursor.execute("""
            CREATE TABLE rode_lijnen_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_datum DATE NOT NULL,
                interval_dagen INTEGER NOT NULL,
                actief_vanaf TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                actief_tot TIMESTAMP,
                is_actief BOOLEAN DEFAULT 1
            )
        """)
        print("      OK Tabel aangemaakt")

        # Stap 2: Seed default config
        print("\n[2/2] Default configuratie seeden...")
        cursor.execute("""
            INSERT INTO rode_lijnen_config
            (start_datum, interval_dagen, actief_vanaf, is_actief)
            VALUES ('2024-07-28', 28, CURRENT_TIMESTAMP, 1)
        """)
        print("      OK Start: 2024-07-28, Interval: 28 dagen")

        # Validatie
        print("\n[Validatie] Actieve rode lijnen config:")
        cursor.execute("""
            SELECT start_datum, interval_dagen, actief_vanaf, is_actief
            FROM rode_lijnen_config
            WHERE is_actief = 1
        """)

        config = cursor.fetchone()
        if config:
            print(f"      - Start datum: {config['start_datum']}")
            print(f"      - Interval: {config['interval_dagen']} dagen")
            print(f"      - Actief vanaf: {config['actief_vanaf'][:10]}")
        else:
            print("      ! Geen actieve config gevonden")

        # Commit
        conn.commit()

        print("\n" + "="*60)
        print(">> Migratie succesvol voltooid!")
        print("="*60)
        print("\nWAT IS ER VERANDERD:")
        print("- rode_lijnen_config tabel toegevoegd")
        print("- Default config: start 2024-07-28, interval 28 dagen")
        print("- Versioning kolommen: actief_vanaf, actief_tot, is_actief")
        print()
        print("GEBRUIK:")
        print("- Rode Lijnen Beheer UI om config te wijzigen")
        print("- Bij wijziging: oude config krijgt actief_tot + is_actief=0")
        print("- Nieuwe config wordt ingevoerd met is_actief=1")
        print("- data_ensure_service.py gebruikt config ipv hardcoded waardes")
        print()

        return True

    except sqlite3.Error as e:
        print(f"\nXX Database fout: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    print()
    success = migratie_rode_lijnen_config()
    print()

    if success:
        print("Je kunt nu de applicatie starten met de nieuwe functionaliteit.")
    else:
        print("Migratie mislukt. Controleer de foutmeldingen hierboven.")

    print()
