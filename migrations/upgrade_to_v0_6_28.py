"""
Database upgrade script: v0.6.27 -> v0.6.28
Split volledige_naam in voornaam + achternaam

Wijzigingen:
- Nieuwe kolommen: voornaam, achternaam (TEXT)
- Parse volledige_naam en split in voor/achternaam
- Behouden: volledige_naam (backward compatibility + display)
- Sortering: ORDER BY is_reserve, achternaam, voornaam

Fixes:
- ISSUE-002: Planning Editor kolom sortering op achternaam

Database versie wordt ge-update naar 0.6.28
"""

import sqlite3
from pathlib import Path
from datetime import datetime


def check_already_upgraded(cursor):
    """Check of upgrade al is uitgevoerd"""
    # Check of voornaam kolom bestaat
    cursor.execute("PRAGMA table_info(gebruikers)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'voornaam' not in columns or 'achternaam' not in columns:
        return False

    # Kolommen bestaan, check of data ook is ingevuld
    cursor.execute("SELECT COUNT(*) FROM gebruikers WHERE voornaam IS NULL OR achternaam IS NULL")
    null_count = cursor.fetchone()[0]

    if null_count > 0:
        print(f"  Waarschuwing: Kolommen bestaan maar {null_count} rijen zijn nog niet gevuld")
        return False

    print("  OK voornaam en achternaam kolommen bestaan en zijn gevuld")
    return True


def parse_naam(volledige_naam):
    """
    Parse volledige naam naar voornaam + achternaam

    Heuristiek voor Belgische namen (format: ACHTERNAAM VOORNAAM):
    - Laatste woord = voornaam
    - Rest = achternaam (kan meerdere woorden zijn, bijv. "Van Geert")

    Voorbeelden:
    - "Turlinckx Tim" -> ("Tim", "Turlinckx")
    - "Van Geert Koen" -> ("Koen", "Van Geert")
    - "Van Den Ackerveken Stef" -> ("Stef", "Van Den Ackerveken")
    - "Administrator" -> ("", "Administrator") (edge case: single name)
    """
    if not volledige_naam:
        return ("", "")

    parts = volledige_naam.strip().split()

    if len(parts) == 0:
        return ("", "")
    elif len(parts) == 1:
        # Single name: put in achternaam, voornaam empty
        return ("", parts[0])
    else:
        # Laatste woord = voornaam, rest (alle woorden behalve laatste) = achternaam
        voornaam = parts[-1]
        achternaam = ' '.join(parts[:-1])
        return (voornaam, achternaam)


def add_naam_columns(cursor):
    """Voeg voornaam en achternaam kolommen toe"""
    print("\n[1/3] Toevoegen voornaam en achternaam kolommen...")

    # Check of kolommen al bestaan
    cursor.execute("PRAGMA table_info(gebruikers)")
    columns = [row[1] for row in cursor.fetchall()]

    # Voeg kolommen toe als ze nog niet bestaan
    if 'voornaam' not in columns:
        cursor.execute("ALTER TABLE gebruikers ADD COLUMN voornaam TEXT")
        print("  OK voornaam kolom toegevoegd")
    else:
        print("  -> voornaam kolom bestaat al")

    if 'achternaam' not in columns:
        cursor.execute("ALTER TABLE gebruikers ADD COLUMN achternaam TEXT")
        print("  OK achternaam kolom toegevoegd")
    else:
        print("  -> achternaam kolom bestaat al")


def populate_naam_columns(cursor):
    """Vul voornaam en achternaam kolommen met gesplitste data"""
    print("\n[2/3] Splitsen volledige_naam in voornaam + achternaam...")

    # Haal alle gebruikers op
    cursor.execute("SELECT id, volledige_naam FROM gebruikers")
    gebruikers = cursor.fetchall()

    total = len(gebruikers)
    print(f"  Verwerken {total} gebruikers...")

    # Parse en update elke gebruiker
    for idx, row in enumerate(gebruikers, 1):
        gebruiker_id = row[0]
        volledige_naam = row[1]

        # Parse naam
        voornaam, achternaam = parse_naam(volledige_naam)

        # Update
        cursor.execute("""
            UPDATE gebruikers
            SET voornaam = ?, achternaam = ?
            WHERE id = ?
        """, (voornaam, achternaam, gebruiker_id))

        # Debug output voor eerste paar entries
        if idx <= 5:
            print(f"    [{idx}/{total}] '{volledige_naam}' -> voornaam='{voornaam}', achternaam='{achternaam}'")

    if total > 5:
        print(f"    ... ({total - 5} meer)")

    print(f"  OK {total} gebruikers ge-update")


def update_db_version(cursor):
    """Update database versie naar 0.6.28"""
    print("\n[3/3] Updaten database versie...")

    cursor.execute("""
        INSERT INTO db_metadata (version_number, migration_description)
        VALUES (?, ?)
    """, ("0.6.28", "Split volledige_naam in voornaam + achternaam (ISSUE-002)"))

    print("  OK Database versie ge-update naar 0.6.28")


def main():
    """Voer upgrade uit"""
    db_path = Path("data/planning.db")

    if not db_path.exists():
        print("ERROR: Database niet gevonden op:", db_path)
        print("   Zorg dat het script wordt uitgevoerd vanuit de project root.")
        return

    print("\n" + "="*60)
    print("Database Upgrade: v0.6.27 -> v0.6.28")
    print("Split Volledige Naam in Voornaam + Achternaam")
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
            print("\nWaarschuwing: Database is al ge-upgrade naar v0.6.28")
            print("  Geen actie nodig.")
            conn.close()
            return

        # Voer upgrade stappen uit
        add_naam_columns(cursor)
        populate_naam_columns(cursor)
        update_db_version(cursor)

        # Commit
        conn.commit()

        print("\n" + "="*60)
        print("SUCCESS: Upgrade succesvol afgerond!")
        print("="*60)
        print("\nWijzigingen:")
        print("  - Nieuwe kolommen: voornaam, achternaam")
        print("  - Volledige_naam behouden (backward compatibility)")
        print("  - Sortering: eerst vaste mensen (op achternaam), dan reserves")
        print("  - Database versie: 0.6.28")
        print("\nVolgende stappen:")
        print("  1. Start de applicatie")
        print("  2. Ga naar Planning Editor")
        print("  3. Verifieer sortering: vaste mensen -> reserves (alfabetisch op achternaam)")
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
