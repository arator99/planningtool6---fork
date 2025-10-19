#!/usr/bin/env python3
"""
Database Migratie v0.6.6 → v0.6.7 - Systeem Termen
Voegt term kolom toe aan speciale_codes tabel en markeert verplichte systeemcodes

ACHTERGROND:
- Voorheen waren codes hardcoded (VV voor verlof, RX voor zondagrust, etc.)
- Nu werken we met termen die flexibele codes kunnen hebben
- Teams kunnen codes aanpassen (VV → VL), maar termen blijven beschermd

VERPLICHTE TERMEN:
1. verlof (standaard: VV)
2. zondagrust (standaard: RX)
3. zaterdagrust (standaard: CX)
4. ziek (standaard: Z)
5. arbeidsduurverkorting (standaard: DA)
"""

import sqlite3
from pathlib import Path


def migratie_systeem_termen():
    """Voeg term kolom toe en markeer 5 verplichte systeemcodes"""
    db_path = Path("data/planning.db")

    if not db_path.exists():
        print("❌ Database niet gevonden op: data/planning.db")
        print("   Start eerst de applicatie om een database aan te maken.")
        return False

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Check of kolom al bestaat
        cursor.execute("PRAGMA table_info(speciale_codes)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'term' in columns:
            print("✓ Kolom 'term' bestaat al in speciale_codes tabel")
            print("  Migratie is al uitgevoerd, niets te doen.")
            conn.close()
            return True

        print("="*60)
        print("Database Migratie v0.6.6 → v0.6.7")
        print("="*60)
        print()

        # Stap 1: Voeg kolom toe (zonder UNIQUE constraint - SQLite beperking)
        print("[1/3] Term kolom toevoegen...")
        cursor.execute("""
            ALTER TABLE speciale_codes
            ADD COLUMN term TEXT
        """)
        print("      ✓ Kolom 'term' toegevoegd (zonder UNIQUE constraint)")

        # Stap 2: Markeer bestaande codes met termen
        print("\n[2/3] Systeem-termen toewijzen aan bestaande codes...")

        term_mapping = [
            ('verlof', 'VV'),
            ('zondagrust', 'RX'),
            ('zaterdagrust', 'CX'),
            ('ziek', 'Z'),
            ('arbeidsduurverkorting', 'DA')
        ]

        toegewezen = 0
        for term, code in term_mapping:
            cursor.execute("""
                UPDATE speciale_codes
                SET term = ?
                WHERE code = ?
            """, (term, code))

            if cursor.rowcount > 0:
                print(f"      ✓ '{code}' → term '{term}'")
                toegewezen += 1
            else:
                print(f"      ⚠ Code '{code}' niet gevonden (mogelijk hernoemd)")

        print(f"\n      {toegewezen}/5 termen toegewezen")

        # Stap 2.5: Voeg UNIQUE index toe aan term kolom
        print("\n[2.5/3] UNIQUE constraint toevoegen via index...")
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_speciale_codes_term
            ON speciale_codes(term)
            WHERE term IS NOT NULL
        """)
        print("      ✓ UNIQUE index toegevoegd op term kolom")

        # Stap 3: Validatie
        print("\n[3/3] Validatie...")
        cursor.execute("""
            SELECT term, code, naam
            FROM speciale_codes
            WHERE term IS NOT NULL
            ORDER BY term
        """)

        systeem_codes = cursor.fetchall()
        print(f"      ✓ {len(systeem_codes)} systeemcodes geregistreerd:")
        for row in systeem_codes:
            print(f"        - {row['term']:25} → {row['code']:4} ({row['naam']})")

        # Commit
        conn.commit()

        print("\n" + "="*60)
        print("✅ Migratie succesvol voltooid!")
        print("="*60)
        print("\nWAT IS ER VERANDERD:")
        print("- Speciale codes hebben nu een optioneel 'term' veld")
        print("- 5 codes zijn gemarkeerd als systeemcodes (niet verwijderbaar)")
        print("- Je kunt de code wijzigen (VV→VL), maar term blijft behouden")
        print("- Het systeem gebruikt termen voor automatische functies")
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
    success = migratie_systeem_termen()
    print()

    if success:
        print("Je kunt nu de applicatie starten met de nieuwe functionaliteit.")
    else:
        print("Migratie mislukt. Controleer de foutmeldingen hierboven.")

    print()
