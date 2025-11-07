"""
Database upgrade script: v0.6.23 -> v0.6.24
Week & Weekend Definitie in HR Regels

Wijzigingen:
- Nieuwe HR regels: week_definitie en weekend_definitie (eenheid: periode)
- Week default: Maandag 00:00 - Zondag 23:59
- Weekend default: Vrijdag 22:00 - Maandag 06:00
- Geïntegreerd in bestaand HR Regels Beheer scherm

Database versie wordt ge-update naar 0.6.24
"""

import sqlite3
from pathlib import Path
from datetime import datetime


def check_already_upgraded(cursor):
    """Check of upgrade al is uitgevoerd"""
    # Check of week_definitie HR regel bestaat
    cursor.execute("""
        SELECT COUNT(*) FROM hr_regels
        WHERE naam = 'week_definitie' AND is_actief = 1
    """)

    if cursor.fetchone()[0] > 0:
        print("  OK week_definitie HR regel bestaat al")
        return True

    return False


def add_periode_hr_regels(cursor):
    """Voeg week_definitie en weekend_definitie HR regels toe"""
    print("\n[1/2] Toevoegen periode HR regels...")

    # Check of regels al bestaan
    cursor.execute("""
        SELECT COUNT(*) FROM hr_regels
        WHERE naam IN ('week_definitie', 'weekend_definitie')
    """)

    if cursor.fetchone()[0] > 0:
        print("  OK Periode regels al aanwezig, skip")
        return

    # Voeg week_definitie toe
    cursor.execute("""
        INSERT INTO hr_regels (naam, waarde, eenheid, beschrijving, is_actief)
        VALUES (?, ?, ?, ?, 1)
    """, (
        'week_definitie',
        'ma-00:00|zo-23:59',
        'periode',
        'Definitie wanneer werkweek start en eindigt (voor 50-uur regel)'
    ))

    # Voeg weekend_definitie toe
    cursor.execute("""
        INSERT INTO hr_regels (naam, waarde, eenheid, beschrijving, is_actief)
        VALUES (?, ?, ?, ?, 1)
    """, (
        'weekend_definitie',
        'vr-22:00|ma-06:00',
        'periode',
        'Definitie wanneer weekend start en eindigt'
    ))

    print("  OK Week & weekend definitie regels toegevoegd")
    print("     - week_definitie: Maandag 00:00 - Zondag 23:59")
    print("     - weekend_definitie: Vrijdag 22:00 - Maandag 06:00")


def update_db_version(cursor):
    """Update database versie naar 0.6.24"""
    print("\n[2/2] Updaten database versie...")

    cursor.execute("""
        INSERT INTO db_metadata (version_number, migration_description)
        VALUES (?, ?)
    """, ("0.6.24", "Week & weekend definitie als HR regels (eenheid: periode)"))

    print("  OK Database versie ge-update naar 0.6.24")


def main():
    """Voer upgrade uit"""
    db_path = Path("data/planning.db")

    if not db_path.exists():
        print("ERROR: Database niet gevonden op:", db_path)
        print("   Zorg dat het script wordt uitgevoerd vanuit de project root.")
        return

    print("\n" + "="*60)
    print("Database Upgrade: v0.6.23 -> v0.6.24")
    print("Week Definitie Systeem")
    print("="*60)

    # Backup maken
    backup_path = db_path.parent / f"planning.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    print(f"\nBackup maken naar: {backup_path.name}")

    import shutil
    shutil.copy2(db_path, backup_path)
    print("  OK Backup compleet")

    # Database connectie
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Check of al upgraded
        if check_already_upgraded(cursor):
            print("\nWaarschuwing: Database is al ge-upgrade naar v0.6.24")
            print("  Geen actie nodig.")
            conn.close()
            return

        # Voer upgrade stappen uit
        add_periode_hr_regels(cursor)
        update_db_version(cursor)

        # Commit
        conn.commit()

        print("\n" + "="*60)
        print("SUCCESS: Upgrade succesvol afgerond!")
        print("="*60)
        print("\nWijzigingen:")
        print("  - Nieuwe HR regels: week_definitie en weekend_definitie")
        print("  - Week default: Maandag 00:00 - Zondag 23:59")
        print("  - Weekend default: Vrijdag 22:00 - Maandag 06:00")
        print("  - Database versie: 0.6.24")
        print("\nVolgende stappen:")
        print("  1. Start de applicatie")
        print("  2. Ga naar Instellingen > HR Regels")
        print("  3. Wijzig week/weekend definitie indien gewenst")
        print(f"\nBackup bewaard als: {backup_path.name}")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: Fout tijdens upgrade: {e}")
        print(f"   Database is NIET gewijzigd (rollback uitgevoerd)")
        print(f"   Backup beschikbaar: {backup_path.name}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
