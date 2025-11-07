#!/usr/bin/env python3
"""
Database Migratie - HR Regels Versioning
Voegt actief_tot en is_actief kolommen toe voor historiek bijhouden

ACHTERGROND:
- HR regels kunnen wijzigen over tijd (bijv. 12u rust → 10u rust vanaf 1 mei)
- Planning van voor de wijziging moet gevalideerd worden met oude regels
- Planning van na de wijziging moet gevalideerd worden met nieuwe regels
- Datum-specifieke historiek nodig voor correcte validatie

WIJZIGINGEN:
- actief_tot kolom (TIMESTAMP, nullable) - wanneer regel vervangen wordt
- is_actief kolom (BOOLEAN) - huidige actieve regel per naam
"""

import sqlite3
from pathlib import Path


def migratie_hr_regels_versioning():
    """Voeg versioning kolommen toe aan hr_regels tabel"""
    db_path = Path("data/planning.db")

    if not db_path.exists():
        print("❌ Database niet gevonden op: data/planning.db")
        print("   Start eerst de applicatie om een database aan te maken.")
        return False

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Check of kolommen al bestaan
        cursor.execute("PRAGMA table_info(hr_regels)")
        columns = [row[1] for row in cursor.fetchall()]

        # Check of UNIQUE constraint nog bestaat
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='hr_regels'")
        table_sql_result = cursor.fetchone()
        table_sql = table_sql_result[0] if table_sql_result else ""
        has_unique = 'naam TEXT UNIQUE' in table_sql or 'UNIQUE(naam)' in table_sql

        if 'actief_tot' in columns and 'is_actief' in columns and not has_unique:
            print("OK Kolommen actief_tot en is_actief bestaan al")
            print("  Migratie is al uitgevoerd, niets te doen.")
            conn.close()
            return True

        print("="*60)
        print("Database Migratie - HR Regels Versioning")
        print("="*60)
        print()

        # Stap 1: Voeg actief_tot kolom toe
        if 'actief_tot' not in columns:
            print("[1/3] actief_tot kolom toevoegen...")
            cursor.execute("""
                ALTER TABLE hr_regels
                ADD COLUMN actief_tot TIMESTAMP
            """)
            print("      OK Kolom 'actief_tot' toegevoegd")
        else:
            print("[1/3] actief_tot kolom bestaat al")

        # Stap 2: Voeg is_actief kolom toe
        if 'is_actief' not in columns:
            print("\n[2/3] is_actief kolom toevoegen...")
            cursor.execute("""
                ALTER TABLE hr_regels
                ADD COLUMN is_actief BOOLEAN DEFAULT 1
            """)
            print("      OK Kolom 'is_actief' toegevoegd")
        else:
            print("\n[2/3] is_actief kolom bestaat al")

        # Stap 3: Verwijder UNIQUE constraint op naam kolom (rebuild tabel)
        print("\n[3/4] UNIQUE constraint verwijderen van naam kolom...")

        # Check of naam nog UNIQUE is
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='hr_regels'")
        table_sql = cursor.fetchone()[0]

        if 'naam TEXT UNIQUE' in table_sql or 'UNIQUE(naam)' in table_sql:
            print("      Rebuilding tabel zonder UNIQUE constraint...")

            # Maak backup
            cursor.execute("ALTER TABLE hr_regels RENAME TO hr_regels_old")

            # Maak nieuwe tabel zonder UNIQUE
            cursor.execute("""
                CREATE TABLE hr_regels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    naam TEXT NOT NULL,
                    waarde REAL NOT NULL,
                    eenheid TEXT NOT NULL,
                    beschrijving TEXT,
                    actief_vanaf TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actief_tot TIMESTAMP,
                    is_actief BOOLEAN DEFAULT 1
                )
            """)

            # Kopieer data
            cursor.execute("""
                INSERT INTO hr_regels (id, naam, waarde, eenheid, beschrijving, actief_vanaf, actief_tot, is_actief)
                SELECT id, naam, waarde, eenheid, beschrijving, actief_vanaf, actief_tot, is_actief
                FROM hr_regels_old
            """)

            # Verwijder backup
            cursor.execute("DROP TABLE hr_regels_old")

            print("      OK UNIQUE constraint verwijderd")
        else:
            print("      Geen UNIQUE constraint gevonden, skip")

        # Stap 4: Zet bestaande regels op is_actief=1
        print("\n[4/4] Bestaande regels markeren als actief...")
        cursor.execute("""
            UPDATE hr_regels
            SET is_actief = 1
            WHERE is_actief IS NULL
        """)

        updated = cursor.rowcount
        print(f"      OK {updated} regel(s) gemarkeerd als actief")

        # Validatie
        print("\n[Validatie] Huidige actieve regels:")
        cursor.execute("""
            SELECT naam, waarde, eenheid, actief_vanaf, actief_tot, is_actief
            FROM hr_regels
            WHERE is_actief = 1
            ORDER BY naam
        """)

        regels = cursor.fetchall()
        if regels:
            for regel in regels:
                actief_van = regel['actief_vanaf'][:10] if regel['actief_vanaf'] else 'N/A'
                actief_tot = regel['actief_tot'][:10] if regel['actief_tot'] else 'heden'
                print(f"      - {regel['naam']:25} = {regel['waarde']} {regel['eenheid']:6} "
                      f"({actief_van} -> {actief_tot})")
        else:
            print("      ! Geen actieve regels gevonden")

        # Commit
        conn.commit()

        print("\n" + "="*60)
        print(">> Migratie succesvol voltooid!")
        print("="*60)
        print("\nWAT IS ER VERANDERD:")
        print("- hr_regels.actief_tot kolom toegevoegd (voor einddatum regel)")
        print("- hr_regels.is_actief kolom toegevoegd (voor huidige actieve regel)")
        print("- Alle bestaande regels zijn gemarkeerd als actief")
        print()
        print("GEBRUIK:")
        print("- Bij wijzigen regel: oude regel krijgt actief_tot + is_actief=0")
        print("- Nieuwe regel wordt ingevoerd met is_actief=1")
        print("- Validatie gebruikt regel op basis van planning datum")
        print()

        return True

    except sqlite3.Error as e:
        print(f"\n❌ Database fout: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    print()
    success = migratie_hr_regels_versioning()
    print()

    if success:
        print("Je kunt nu de applicatie starten met de nieuwe functionaliteit.")
    else:
        print("Migratie mislukt. Controleer de foutmeldingen hierboven.")

    print()
