#!/usr/bin/env python3
"""
Cumulatieve Database Migratie: v0.6.4/0.6.5 -> v0.6.13

Dit script voert ALLE tussenliggende migraties uit:
- v0.6.5 -> v0.6.6: Typetabel versioned systeem
- v0.6.6 -> v0.6.7: Term-based speciale codes
- v0.6.7 -> v0.6.8: Rode lijnen config (OPTIONEEL - alleen structuur)
- v0.6.8 -> v0.6.10: Verlof saldo systeem
- v0.6.10 -> v0.6.11: Shift voorkeuren
- v0.6.11 -> v0.6.12: Theme voorkeur
- v0.6.12 -> v0.6.13: Database versie tracking

BELANGRIJK: Maak ALTIJD een backup voor je dit script draait!

Gebruik:
    python migrate_v0_6_4_to_v0_6_13.py
    python migrate_v0_6_4_to_v0_6_13.py path/to/database.db

Auteur: Planning Tool Team
Datum: 21 Oktober 2025
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime


def get_table_columns(cursor, table_name):
    """Haal alle kolommen van een tabel op"""
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]
    except sqlite3.Error:
        return []


def table_exists(cursor, table_name):
    """Check of tabel bestaat"""
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None


def migrate_to_v0_6_6(conn, cursor):
    """
    v0.6.5 -> v0.6.6: Typetabel Versioned Systeem
    Oude 'typetabel' tabel wordt vervangen door 'typetabel_versies' + 'typetabel_data'
    """
    print("\n[STAP 1/7] Migratie v0.6.5 -> v0.6.6: Typetabel Versioned Systeem")

    if table_exists(cursor, 'typetabel_versies'):
        print("  [SKIP] typetabel_versies tabel bestaat al")
        return True

    try:
        # Maak nieuwe versioned tabellen
        print("  [>>] Aanmaken typetabel_versies tabel...")
        cursor.execute("""
            CREATE TABLE typetabel_versies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                versie_naam TEXT NOT NULL,
                aantal_weken INTEGER NOT NULL CHECK(aantal_weken BETWEEN 1 AND 52),
                status TEXT NOT NULL CHECK(status IN ('concept', 'actief', 'archief')),
                actief_vanaf TEXT,
                laatste_wijziging TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                opmerkingen TEXT
            )
        """)

        print("  [>>] Aanmaken typetabel_data tabel...")
        cursor.execute("""
            CREATE TABLE typetabel_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                versie_id INTEGER NOT NULL,
                week_nummer INTEGER NOT NULL CHECK(week_nummer BETWEEN 1 AND 52),
                dag_nummer INTEGER NOT NULL CHECK(dag_nummer BETWEEN 1 AND 7),
                shift_type TEXT,
                UNIQUE(versie_id, week_nummer, dag_nummer),
                FOREIGN KEY (versie_id) REFERENCES typetabel_versies(id) ON DELETE CASCADE
            )
        """)

        # Migreer oude data indien aanwezig
        if table_exists(cursor, 'typetabel'):
            print("  [>>] Migreren oude typetabel data...")

            # Maak concept versie aan
            cursor.execute("""
                INSERT INTO typetabel_versies (versie_naam, aantal_weken, status, opmerkingen)
                VALUES ('Gemigreerd van oude typetabel', 6, 'concept', 'Automatisch gemigreerd bij upgrade naar v0.6.6')
            """)
            versie_id = cursor.lastrowid

            # Kopieer data
            cursor.execute("""
                INSERT INTO typetabel_data (versie_id, week_nummer, dag_nummer, shift_type)
                SELECT ?, week_nummer, dag_nummer, shift_type
                FROM typetabel
            """, (versie_id,))

            rows_migrated = cursor.rowcount
            print(f"  [OK] {rows_migrated} typetabel records gemigreerd")

        conn.commit()
        print("  [OK] Typetabel versioned systeem aangemaakt")
        return True

    except sqlite3.Error as e:
        print(f"  [FOUT] Migratie v0.6.6 mislukt: {e}")
        conn.rollback()
        return False


def migrate_to_v0_6_7(conn, cursor):
    """
    v0.6.6 -> v0.6.7: Term-based Speciale Codes + Schema Update
    Voegt 'term' kolom toe aan speciale_codes tabel
    Update oude schema (code + naam) naar nieuw schema (code_naam)
    """
    print("\n[STAP 2/7] Migratie v0.6.6 -> v0.6.7: Term-based Codes + Schema Update")

    cols = get_table_columns(cursor, 'speciale_codes')

    # Check of we oude of nieuwe schema hebben
    has_code_naam = 'code_naam' in cols
    has_separate_code_naam = 'code' in cols and 'naam' in cols

    if has_separate_code_naam and not has_code_naam:
        print("  [INFO] Oude schema gedetecteerd (code + naam gescheiden)")
        print("  [>>] Converteren naar nieuwe schema (code_naam)...")

        try:
            # Stap 1: Hernoem oude tabel
            cursor.execute("ALTER TABLE speciale_codes RENAME TO speciale_codes_old")

            # Stap 2: Maak nieuwe tabel met correcte schema
            cursor.execute("""
                CREATE TABLE speciale_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_naam TEXT UNIQUE NOT NULL,
                    beschrijving TEXT,
                    kleur TEXT,
                    telt_als_werkdag BOOLEAN DEFAULT 0,
                    reset_12u_rust BOOLEAN DEFAULT 1,
                    breekt_werk_reeks BOOLEAN DEFAULT 0,
                    term TEXT,
                    is_actief BOOLEAN DEFAULT 1,
                    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    gedeactiveerd_op TIMESTAMP
                )
            """)

            # Stap 3: Kopieer data met code als code_naam
            cursor.execute("""
                INSERT INTO speciale_codes
                (id, code_naam, beschrijving, telt_als_werkdag, reset_12u_rust,
                 breekt_werk_reeks, term, is_actief)
                SELECT
                    id, code, beschrijving, telt_als_werkdag, reset_12u_rust,
                    breekt_werk_reeks, term, 1
                FROM speciale_codes_old
            """)

            # Stap 4: Verwijder oude tabel
            cursor.execute("DROP TABLE speciale_codes_old")

            print("  [OK] Schema geconverteerd naar nieuwe structuur")

        except sqlite3.Error as e:
            print(f"  [FOUT] Schema conversie mislukt: {e}")
            conn.rollback()
            return False

    # Check/voeg term kolom toe
    cols = get_table_columns(cursor, 'speciale_codes')
    if 'term' not in cols:
        try:
            print("  [>>] Toevoegen term kolom aan speciale_codes...")
            cursor.execute("ALTER TABLE speciale_codes ADD COLUMN term TEXT")
        except sqlite3.Error as e:
            print(f"  [FOUT] Toevoegen term kolom mislukt: {e}")
            conn.rollback()
            return False

    # Update bestaande codes met terms
    try:
        print("  [>>] Updaten bestaande codes met terms...")
        term_mapping = {
            'VV': 'verlof',
            'verlof': 'verlof',
            'RX': 'zondagrust',
            'CX': 'zaterdagrust',
            'Z': 'ziek',
            'DA': 'arbeidsduurverkorting',
            'ADV': 'arbeidsduurverkorting'
        }

        for code_naam, term in term_mapping.items():
            cursor.execute("""
                UPDATE speciale_codes
                SET term = ?
                WHERE code_naam = ? AND (term IS NULL OR term = '')
            """, (term, code_naam))

        conn.commit()
        print("  [OK] Term-based codes systeem toegevoegd")
        return True

    except sqlite3.Error as e:
        print(f"  [FOUT] Migratie v0.6.7 mislukt: {e}")
        conn.rollback()
        return False


def migrate_to_v0_6_8(conn, cursor):
    """
    v0.6.7 -> v0.6.8: Rode Lijnen Config
    Voegt rode_lijnen_config tabel toe (versioned configuratie)
    """
    print("\n[STAP 3/7] Migratie v0.6.7 -> v0.6.8: Rode Lijnen Config")

    if table_exists(cursor, 'rode_lijnen_config'):
        print("  [SKIP] rode_lijnen_config tabel bestaat al")
        return True

    try:
        print("  [>>] Aanmaken rode_lijnen_config tabel...")
        cursor.execute("""
            CREATE TABLE rode_lijnen_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                versie_naam TEXT NOT NULL,
                start_datum TEXT NOT NULL,
                cyclus_dagen INTEGER NOT NULL DEFAULT 28,
                status TEXT NOT NULL CHECK(status IN ('concept', 'actief', 'archief')),
                actief_vanaf TEXT,
                laatste_wijziging TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                opmerkingen TEXT
            )
        """)

        conn.commit()
        print("  [OK] Rode lijnen config tabel aangemaakt")
        print("  [INFO] Rode lijnen config is leeg - admin kan dit later configureren")
        return True

    except sqlite3.Error as e:
        print(f"  [FOUT] Migratie v0.6.8 mislukt: {e}")
        conn.rollback()
        return False


def migrate_to_v0_6_10(conn, cursor):
    """
    v0.6.8 -> v0.6.10: Verlof & KD Saldo Systeem
    (v0.6.9 had geen DB wijzigingen)
    """
    print("\n[STAP 4/7] Migratie v0.6.8 -> v0.6.10: Verlof & KD Saldo Systeem")

    if table_exists(cursor, 'verlof_saldo'):
        print("  [INFO] verlof_saldo tabel bestaat al - check schema...")

        # Check of tabel correcte kolomnamen heeft
        cols = get_table_columns(cursor, 'verlof_saldo')

        # Oude namen: vv_contingent, vv_overgedragen, vv_opgenomen
        # Nieuwe namen: verlof_totaal, verlof_overgedragen, verlof_opgenomen
        if 'vv_contingent' in cols:
            print("  [INFO] Oude schema gedetecteerd - converteren naar nieuwe kolomnamen...")

            try:
                # Hernoem oude tabel
                cursor.execute("ALTER TABLE verlof_saldo RENAME TO verlof_saldo_old")

                # Maak nieuwe tabel met correcte kolomnamen
                cursor.execute("""
                    CREATE TABLE verlof_saldo (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        gebruiker_id INTEGER NOT NULL,
                        jaar INTEGER NOT NULL,
                        verlof_totaal REAL NOT NULL DEFAULT 0,
                        verlof_overgedragen REAL NOT NULL DEFAULT 0,
                        verlof_opgenomen REAL NOT NULL DEFAULT 0,
                        kd_totaal REAL NOT NULL DEFAULT 0,
                        kd_overgedragen REAL NOT NULL DEFAULT 0,
                        kd_opgenomen REAL NOT NULL DEFAULT 0,
                        opmerking TEXT,
                        aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        laatste_wijziging TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(gebruiker_id, jaar),
                        FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id)
                    )
                """)

                # Kopieer data met nieuwe kolomnamen
                cursor.execute("""
                    INSERT INTO verlof_saldo
                    (id, gebruiker_id, jaar, verlof_totaal, verlof_overgedragen, verlof_opgenomen,
                     kd_totaal, kd_overgedragen, kd_opgenomen, opmerking, aangemaakt_op, laatste_wijziging)
                    SELECT
                        id, gebruiker_id, jaar, vv_contingent, vv_overgedragen, vv_opgenomen,
                        kd_contingent, kd_overgedragen, kd_opgenomen, opmerking, aangemaakt_op, laatste_wijziging
                    FROM verlof_saldo_old
                """)

                # Verwijder oude tabel
                cursor.execute("DROP TABLE verlof_saldo_old")

                conn.commit()
                print("  [OK] Schema geconverteerd naar nieuwe kolomnamen")

            except sqlite3.Error as e:
                print(f"  [FOUT] Schema conversie mislukt: {e}")
                conn.rollback()
                return False

        else:
            print("  [SKIP] verlof_saldo heeft al correcte schema")

        return True

    try:
        # Maak verlof_saldo tabel
        print("  [>>] Aanmaken verlof_saldo tabel...")
        cursor.execute("""
            CREATE TABLE verlof_saldo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gebruiker_id INTEGER NOT NULL,
                jaar INTEGER NOT NULL,
                vv_contingent REAL NOT NULL DEFAULT 0,
                vv_overgedragen REAL NOT NULL DEFAULT 0,
                vv_opgenomen REAL NOT NULL DEFAULT 0,
                kd_contingent REAL NOT NULL DEFAULT 0,
                kd_overgedragen REAL NOT NULL DEFAULT 0,
                kd_opgenomen REAL NOT NULL DEFAULT 0,
                opmerking TEXT,
                aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                laatste_wijziging TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(gebruiker_id, jaar),
                FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id)
            )
        """)

        # Voeg KD speciale code toe indien niet bestaat
        print("  [>>] Controleren KD speciale code...")
        cursor.execute("""
            SELECT COUNT(*) FROM speciale_codes WHERE term = 'kompensatiedag'
        """)

        if cursor.fetchone()[0] == 0:
            print("  [>>] Toevoegen KD speciale code...")

            # Check welke kolom structuur de tabel heeft (oude vs nieuwe schema)
            cols = get_table_columns(cursor, 'speciale_codes')

            if 'code_naam' in cols:
                # Nieuwe structuur (v0.6.6+)
                cursor.execute("""
                    INSERT INTO speciale_codes
                    (code_naam, beschrijving, kleur, telt_als_werkdag, reset_12u_rust,
                     breekt_werk_reeks, term, is_actief)
                    VALUES ('KD', 'Kompensatiedag', '#FFA500', 0, 1, 1, 'kompensatiedag', 1)
                """)
            else:
                # Oude structuur (v0.6.4/0.6.5): 'code' en 'naam' gescheiden
                cursor.execute("""
                    INSERT INTO speciale_codes
                    (code, naam, beschrijving, telt_als_werkdag, reset_12u_rust,
                     breekt_werk_reeks, term)
                    VALUES ('KD', 'Kompensatiedag', 'Kompensatiedag', 0, 1, 1, 'kompensatiedag')
                """)

        # Voeg toegekende_code_term kolom toe aan verlof_aanvragen
        cols = get_table_columns(cursor, 'verlof_aanvragen')
        if 'toegekende_code_term' not in cols:
            print("  [>>] Toevoegen toegekende_code_term kolom...")
            cursor.execute("""
                ALTER TABLE verlof_aanvragen ADD COLUMN toegekende_code_term TEXT
            """)

        conn.commit()
        print("  [OK] Verlof & KD saldo systeem aangemaakt")
        return True

    except sqlite3.Error as e:
        print(f"  [FOUT] Migratie v0.6.10 mislukt: {e}")
        conn.rollback()
        return False


def migrate_to_v0_6_11(conn, cursor):
    """
    v0.6.10 -> v0.6.11: Shift Voorkeuren
    Voegt shift_voorkeuren kolom toe aan gebruikers
    """
    print("\n[STAP 5/7] Migratie v0.6.10 -> v0.6.11: Shift Voorkeuren")

    cols = get_table_columns(cursor, 'gebruikers')
    if 'shift_voorkeuren' in cols:
        print("  [SKIP] shift_voorkeuren kolom bestaat al")
        return True

    try:
        print("  [>>] Toevoegen shift_voorkeuren kolom...")
        cursor.execute("""
            ALTER TABLE gebruikers ADD COLUMN shift_voorkeuren TEXT
        """)

        conn.commit()
        print("  [OK] Shift voorkeuren kolom toegevoegd")
        return True

    except sqlite3.Error as e:
        print(f"  [FOUT] Migratie v0.6.11 mislukt: {e}")
        conn.rollback()
        return False


def migrate_to_v0_6_12(conn, cursor):
    """
    v0.6.11 -> v0.6.12: Theme Voorkeur Per Gebruiker
    Voegt theme_voorkeur kolom toe aan gebruikers
    """
    print("\n[STAP 6/7] Migratie v0.6.11 -> v0.6.12: Theme Voorkeur")

    cols = get_table_columns(cursor, 'gebruikers')
    if 'theme_voorkeur' in cols:
        print("  [SKIP] theme_voorkeur kolom bestaat al")
        return True

    try:
        print("  [>>] Toevoegen theme_voorkeur kolom...")
        cursor.execute("""
            ALTER TABLE gebruikers ADD COLUMN theme_voorkeur TEXT DEFAULT 'light'
        """)

        conn.commit()
        print("  [OK] Theme voorkeur kolom toegevoegd")
        return True

    except sqlite3.Error as e:
        print(f"  [FOUT] Migratie v0.6.12 mislukt: {e}")
        conn.rollback()
        return False


def migrate_to_v0_6_13(conn, cursor):
    """
    v0.6.12 -> v0.6.13: Database Versie Tracking
    Voegt db_metadata tabel toe
    """
    print("\n[STAP 7/7] Migratie v0.6.12 -> v0.6.13: Database Versie Tracking")

    if table_exists(cursor, 'db_metadata'):
        print("  [SKIP] db_metadata tabel bestaat al")
        return True

    try:
        print("  [>>] Aanmaken db_metadata tabel...")
        cursor.execute("""
            CREATE TABLE db_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_number TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                migration_description TEXT
            )
        """)

        # Initialiseer met v0.6.13
        print("  [>>] Initialiseren database versie...")
        cursor.execute("""
            INSERT INTO db_metadata (version_number, migration_description)
            VALUES ('0.6.13', 'Cumulatieve migratie van v0.6.4/0.6.5 naar v0.6.13')
        """)

        conn.commit()
        print("  [OK] Database versie tracking toegevoegd (versie: 0.6.13)")
        return True

    except sqlite3.Error as e:
        print(f"  [FOUT] Migratie v0.6.13 mislukt: {e}")
        conn.rollback()
        return False


def main():
    """Main migratie functie"""

    # Bepaal database pad
    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])
    else:
        db_path = Path("data/planning.db")

    print("\n" + "="*60)
    print("CUMULATIEVE DATABASE MIGRATIE")
    print("v0.6.4/0.6.5 -> v0.6.13")
    print("="*60)
    print(f"\nDatabase: {db_path}")
    print(f"Tijdstip: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not db_path.exists():
        print(f"\n[FOUT] Database niet gevonden: {db_path}")
        print("="*60)
        return False

    # Waarschuwing
    print("\n" + "!"*60)
    print("WAARSCHUWING: Deze migratie wijzigt je database permanent!")
    print("Zorg dat je een BACKUP hebt gemaakt voor je doorgaat!")
    print("!"*60)

    response = input("\nDoorgaan met migratie? (ja/nee): ").strip().lower()
    if response != 'ja':
        print("\n[STOP] Migratie geannuleerd door gebruiker")
        print("="*60)
        return False

    # Open database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Voer migraties uit (in volgorde)
    migrations = [
        migrate_to_v0_6_6,
        migrate_to_v0_6_7,
        migrate_to_v0_6_8,
        migrate_to_v0_6_10,
        migrate_to_v0_6_11,
        migrate_to_v0_6_12,
        migrate_to_v0_6_13
    ]

    print("\n" + "="*60)
    print("START MIGRATIE PROCES")
    print("="*60)

    for i, migration in enumerate(migrations, 1):
        success = migration(conn, cursor)
        if not success:
            print(f"\n[FOUT] Migratie gestopt bij stap {i}")
            conn.close()
            return False

    conn.close()

    # Verificatie
    print("\n" + "="*60)
    print("VERIFICATIE")
    print("="*60)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT version_number FROM db_metadata ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()

    if result and result[0] == "0.6.13":
        print("\n[OK] Database succesvol gemigreerd naar v0.6.13")
        print(f"[OK] Database versie: {result[0]}")
    else:
        print("\n[WAARSCHUWING] Database versie niet correct ingesteld")

    conn.close()

    print("\n" + "="*60)
    print("MIGRATIE VOLTOOID")
    print("="*60)
    print("\nJe kunt nu de applicatie starten met:")
    print("  python main.py")
    print("\n" + "="*60 + "\n")

    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[STOP] Migratie geannuleerd door gebruiker (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FOUT] Onverwachte fout: {e}")
        sys.exit(1)
