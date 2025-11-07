"""
Database Migratie Script - Verlof & KD Saldo Systeem
Versie: 0.6.9 -> 0.6.10

Wijzigingen:
1. Nieuwe tabel: verlof_saldo (jaarlijks contingent + overdracht tracking)
2. Nieuwe speciale code: KD (Kompensatiedag) met term 'kompensatiedag'
3. Nieuwe kolom: verlof_aanvragen.toegekende_code_term (VV of KD bij goedkeuring)
4. HR regel: Max KD overdracht (35 dagen)
5. HR regel: Verlof vervaldatum (1 mei)

Run dit script VOOR het opstarten van de applicatie na update naar v0.6.10
"""

import sqlite3
from datetime import datetime
from pathlib import Path


def get_database_path():
    """Haal database path op"""
    return Path(__file__).parent / "data" / "planning.db"


def migrate():
    """Voer migratie uit"""
    db_path = get_database_path()

    if not db_path.exists():
        print(f"[X] Database niet gevonden: {db_path}")
        return False

    print(f"Database: {db_path}")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        # ===== STAP 1: Maak verlof_saldo tabel =====
        print("\n[1/5] Controleer verlof_saldo tabel...")
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='verlof_saldo'
        """)

        if not cursor.fetchone():
            print("  > Aanmaken verlof_saldo tabel...")
            cursor.execute("""
                CREATE TABLE verlof_saldo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gebruiker_id INTEGER NOT NULL,
                    jaar INTEGER NOT NULL,

                    -- Verlof (VV/TH/etc - via term 'verlof')
                    verlof_totaal INTEGER DEFAULT 0,
                    verlof_overgedragen INTEGER DEFAULT 0,
                    verlof_opgenomen INTEGER DEFAULT 0,

                    -- Kompensatiedagen (KD/CD/etc - via term 'kompensatiedag')
                    kd_totaal INTEGER DEFAULT 0,
                    kd_overgedragen INTEGER DEFAULT 0,
                    kd_opgenomen INTEGER DEFAULT 0,

                    -- Meta
                    opmerking TEXT,
                    aangemaakt_op TEXT NOT NULL,
                    gewijzigd_op TEXT,

                    FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id) ON DELETE CASCADE,
                    UNIQUE(gebruiker_id, jaar)
                )
            """)
            print("  [OK] Tabel verlof_saldo aangemaakt")
        else:
            print("  [OK] Tabel verlof_saldo bestaat al")

        # ===== STAP 2: Voeg KD toe als speciale code met term =====
        print("\n[2/5] Controleer KD speciale code...")
        cursor.execute("""
            SELECT code FROM speciale_codes WHERE term = 'kompensatiedag'
        """)

        if not cursor.fetchone():
            # Check of KD als code al bestaat (zonder term)
            cursor.execute("SELECT id FROM speciale_codes WHERE code = 'KD'")
            bestaande_kd = cursor.fetchone()

            if bestaande_kd:
                # Update bestaande KD met term
                print("  > Update bestaande KD code met term 'kompensatiedag'...")
                cursor.execute("""
                    UPDATE speciale_codes
                    SET term = 'kompensatiedag',
                        naam = 'Kompensatiedag'
                    WHERE code = 'KD'
                """)
                print("  [OK] KD code geüpdatet met term")
            else:
                # Maak nieuwe KD code aan
                print("  > Aanmaken KD speciale code met term 'kompensatiedag'...")
                cursor.execute("""
                    INSERT INTO speciale_codes
                    (code, naam, term, telt_als_werkdag, reset_12u_rust, breekt_werk_reeks)
                    VALUES ('KD', 'Kompensatiedag', 'kompensatiedag', 1, 1, 0)
                """)
                print("  [OK] KD code aangemaakt")
        else:
            print("  [OK] KD code met term 'kompensatiedag' bestaat al")

        # ===== STAP 3: Voeg toegekende_code_term kolom toe aan verlof_aanvragen =====
        print("\n[3/5] Controleer verlof_aanvragen.toegekende_code_term kolom...")
        cursor.execute("PRAGMA table_info(verlof_aanvragen)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'toegekende_code_term' not in columns:
            print("  > Toevoegen kolom toegekende_code_term...")
            cursor.execute("""
                ALTER TABLE verlof_aanvragen
                ADD COLUMN toegekende_code_term TEXT
            """)
            print("  [OK] Kolom toegekende_code_term toegevoegd")

            # Migreer bestaande goedgekeurde aanvragen naar 'verlof'
            cursor.execute("""
                UPDATE verlof_aanvragen
                SET toegekende_code_term = 'verlof'
                WHERE status = 'goedgekeurd'
                  AND toegekende_code_term IS NULL
            """)
            migrated_count = cursor.rowcount
            if migrated_count > 0:
                print(f"  [OK] {migrated_count} bestaande aanvragen gemigreerd naar term 'verlof'")
        else:
            print("  [OK] Kolom toegekende_code_term bestaat al")

        # ===== STAP 4: Voeg HR regels toe =====
        print("\n[4/5] Controleer HR regels voor verlof systeem...")

        hr_regels = [
            ('Vervaldatum overgedragen verlof (maand)', 5, 'maand', 'Maand waarin overgedragen verlof vervalt'),
            ('Vervaldatum overgedragen verlof (dag)', 1, 'dag', 'Dag waarop overgedragen verlof vervalt'),
            ('Max overdracht KD naar volgend jaar', 35, 'dagen', 'Maximum aantal KD dagen overdraagbaar'),
        ]

        for naam, waarde, eenheid, beschrijving in hr_regels:
            cursor.execute("""
                SELECT id FROM hr_regels
                WHERE naam = ? AND is_actief = 1
            """, (naam,))

            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO hr_regels
                    (naam, waarde, eenheid, beschrijving, actief_vanaf, is_actief)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (
                    naam,
                    waarde,
                    eenheid,
                    beschrijving,
                    datetime.now().date().isoformat()
                ))
                print(f"  [OK] HR regel '{naam}' toegevoegd")
            else:
                print(f"  [OK] HR regel '{naam}' bestaat al")

        # ===== STAP 5: Seed verlof_saldo voor huidige actieve gebruikers =====
        print("\n[5/5] Seed verlof_saldo voor actieve gebruikers...")

        # Haal huidige jaar op
        current_year = datetime.now().year

        # Haal alle actieve gebruikers (exclusief admin)
        cursor.execute("""
            SELECT id, volledige_naam, gebruikersnaam
            FROM gebruikers
            WHERE is_actief = 1 AND gebruikersnaam != 'admin'
        """)
        gebruikers = cursor.fetchall()

        seeded_count = 0
        for gebruiker_id, naam, gebruikersnaam in gebruikers:
            # Check of al bestaat
            cursor.execute("""
                SELECT id FROM verlof_saldo
                WHERE gebruiker_id = ? AND jaar = ?
            """, (gebruiker_id, current_year))

            if not cursor.fetchone():
                # Maak standaard saldo aan (0 dagen, moet handmatig ingevuld worden)
                cursor.execute("""
                    INSERT INTO verlof_saldo
                    (gebruiker_id, jaar, verlof_totaal, verlof_overgedragen,
                     kd_totaal, kd_overgedragen, aangemaakt_op, opmerking)
                    VALUES (?, ?, 0, 0, 0, 0, ?, 'Handmatig in te vullen')
                """, (gebruiker_id, current_year, datetime.now().isoformat()))
                seeded_count += 1

        if seeded_count > 0:
            print(f"  [OK] {seeded_count} verlof_saldo records aangemaakt voor {current_year}")
        else:
            print(f"  [OK] Alle gebruikers hebben al een saldo record voor {current_year}")

        # Commit alle wijzigingen
        conn.commit()

        print("\n" + "=" * 60)
        print("[OK] Migratie succesvol voltooid!")
        print("\nSamenvatting:")
        print("  - Tabel 'verlof_saldo' aangemaakt")
        print("  - KD code toegevoegd met term 'kompensatiedag'")
        print("  - Kolom 'toegekende_code_term' toegevoegd aan verlof_aanvragen")
        print("  - HR regels toegevoegd (vervaldatum + max overdracht)")
        print(f"  - {seeded_count} saldo records aangemaakt voor {current_year}")
        print("\n[!] BELANGRIJK:")
        print("  Vul handmatig de verlof/KD contingenten in via het nieuwe")
        print("  'Verlof Saldo Beheer' scherm in de applicatie!")
        print("=" * 60)

        return True

    except sqlite3.Error as e:
        print(f"\n[X] Database error: {e}")
        conn.rollback()
        return False

    except Exception as e:
        print(f"\n[X] Onverwachte fout: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    print(">>> Start Verlof & KD Saldo Migratie")
    print("Versie: 0.6.9 -> 0.6.10")
    print()

    success = migrate()

    if success:
        print("\n[OK] Migratie compleet! Je kunt nu de applicatie starten.")
    else:
        print("\n[FOUT] Migratie mislukt. Controleer de errors hierboven.")
        print("   Neem contact op met development team indien nodig.")

    input("\nDruk op Enter om af te sluiten...")
