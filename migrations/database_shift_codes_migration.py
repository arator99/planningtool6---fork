# database_shift_codes_migration.py
"""
Database migratie voor Shift Codes systeem
FIXED: Herstructureer shift_codes tabel als schema niet klopt
"""
import sqlite3
from pathlib import Path


def migrate_shift_codes():
    """Migreer naar shift codes systeem"""
    db_path = Path("data/planning.db")

    print("=" * 60)
    print("SHIFT CODES MIGRATIE START")
    print("=" * 60)

    if not db_path.exists():
        print("❌ Database niet gevonden!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check shift_codes schema
    print("\n1. Controleer shift_codes schema...")
    cursor.execute("PRAGMA table_info(shift_codes)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"   Huidige kolommen: {', '.join(columns)}")

    # Als werkpost_id niet bestaat, herstructureer tabel
    if 'werkpost_id' not in columns:
        print("\n   ⚠️  Verkeerd schema gedetecteerd - tabel herstructureren...")

        # Verwijder oude tabel
        cursor.execute("DROP TABLE IF EXISTS shift_codes")
        print("   ✓ Oude shift_codes tabel verwijderd")

        # Maak nieuwe tabel met correct schema
        cursor.execute("""
            CREATE TABLE shift_codes (
                id INTEGER PRIMARY KEY,
                werkpost_id INTEGER NOT NULL,
                dag_type TEXT NOT NULL,
                shift_type TEXT NOT NULL,
                code TEXT NOT NULL,
                start_uur TEXT,
                eind_uur TEXT,
                FOREIGN KEY (werkpost_id) REFERENCES werkposten(id),
                UNIQUE(werkpost_id, dag_type, shift_type)
            )
        """)
        print("   ✓ Nieuwe shift_codes tabel aangemaakt")
    else:
        print("   ✓ Schema is correct")

    # Check werkposten
    print("\n2. Controleer werkposten...")
    cursor.execute("SELECT COUNT(*) FROM werkposten")
    wp_count = cursor.fetchone()[0]
    print(f"   Aantal werkposten: {wp_count}")

    if wp_count == 0:
        print("\n3. Interventie werkpost aanmaken...")
        cursor.execute("""
            INSERT INTO werkposten (naam, beschrijving, telt_als_werkdag, reset_12u_rust, breekt_werk_reeks)
            VALUES ('Interventie', 'Hulpverleningspost', 1, 1, 0)
        """)
        interventie_id = cursor.lastrowid
        print(f"   ✓ Werkpost aangemaakt met ID: {interventie_id}")

        print("\n4. Shift codes toevoegen...")
        interventie_shifts = [
            (interventie_id, 'weekdag', 'vroeg', '7101', '06:00', '14:00'),
            (interventie_id, 'weekdag', 'laat', '7201', '14:00', '22:00'),
            (interventie_id, 'weekdag', 'nacht', '7301', '22:00', '06:00'),
            (interventie_id, 'zaterdag', 'vroeg', '7401', '06:00', '14:00'),
            (interventie_id, 'zaterdag', 'laat', '7501', '14:00', '22:00'),
            (interventie_id, 'zaterdag', 'nacht', '7601', '22:00', '06:00'),
            (interventie_id, 'zondag', 'vroeg', '7701', '06:00', '14:00'),
            (interventie_id, 'zondag', 'laat', '7801', '14:00', '22:00'),
            (interventie_id, 'zondag', 'nacht', '7901', '22:00', '06:00'),
        ]

        cursor.executemany("""
            INSERT INTO shift_codes (werkpost_id, dag_type, shift_type, code, start_uur, eind_uur)
            VALUES (?, ?, ?, ?, ?, ?)
        """, interventie_shifts)
        print(f"   ✓ {len(interventie_shifts)} shift codes toegevoegd")
    else:
        print("\n3. Werkposten aanwezig - seed overgeslagen")

    conn.commit()
    conn.close()

    # Toon eindstatus
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM werkposten")
    wp = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM shift_codes")
    sc = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM speciale_codes")
    spc = cursor.fetchone()[0]
    conn.close()

    print("\n" + "=" * 60)
    print("MIGRATIE VOLTOOID")
    print("=" * 60)
    print("\nEindstatus:")
    print(f"  • {wp} werkpost(en)")
    print(f"  • {sc} shift code(s)")
    print(f"  • {spc} speciale code(s)")
    print("\n✓ Klaar voor gebruik!")


if __name__ == '__main__':
    migrate_shift_codes()