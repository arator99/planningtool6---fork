#!/usr/bin/env python3
"""
Database Versie Detectie Tool

Analyseert een database en bepaalt welke versie het waarschijnlijk is
op basis van aanwezige tabellen en kolommen.

Gebruik:
    python detect_db_version.py
    python detect_db_version.py path/to/database.db

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


def get_all_tables(cursor):
    """Haal alle tabellen op"""
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    return [row[0] for row in cursor.fetchall()]


def detect_version(db_path):
    """
    Detecteer database versie op basis van schema analyse
    Returns: (version, confidence, details)
    """

    if not db_path.exists():
        return None, "error", f"Database niet gevonden: {db_path}"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Haal alle tabellen op
        tables = get_all_tables(cursor)

        print(f"\n{'='*60}")
        print(f"DATABASE ANALYSE: {db_path.name}")
        print(f"{'='*60}\n")

        print(f"Gevonden tabellen ({len(tables)}):")
        for table in tables:
            print(f"  - {table}")
        print()

        # Analyse starten
        details = []
        version = "Onbekend"
        confidence = "low"

        # Check db_metadata tabel (v0.6.13+)
        if 'db_metadata' in tables:
            cursor.execute("SELECT version_number, updated_at FROM db_metadata ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                version = result[0]
                confidence = "high"
                details.append(f"[OK] db_metadata tabel aanwezig - Versie: {version}")
                details.append(f"     Laatste update: {result[1]}")
                conn.close()
                return version, confidence, details

        # Check gebruikers tabel kolommen
        if 'gebruikers' not in tables:
            details.append("[FOUT] gebruikers tabel niet gevonden - Mogelijk corrupte database")
            conn.close()
            return "Pre-v0.6.0", "high", details

        gebruikers_cols = get_table_columns(cursor, 'gebruikers')
        details.append(f"\nGebruikers tabel kolommen ({len(gebruikers_cols)}):")
        for col in gebruikers_cols:
            details.append(f"  - {col}")

        # Versie detectie op basis van kolommen
        has_uuid = 'gebruiker_uuid' in gebruikers_cols
        has_shift_voorkeuren = 'shift_voorkeuren' in gebruikers_cols
        has_theme_voorkeur = 'theme_voorkeur' in gebruikers_cols
        has_startweek = 'startweek_typedienst' in gebruikers_cols

        # Check speciale tabellen
        has_typetabel_versies = 'typetabel_versies' in tables
        _has_typetabel_data = 'typetabel_data' in tables  # Unused but kept for completeness
        has_verlof_saldo = 'verlof_saldo' in tables
        has_rode_lijnen_config = 'rode_lijnen_config' in tables

        # Check speciale_codes tabel voor term kolom
        has_term_in_codes = False
        if 'speciale_codes' in tables:
            speciale_codes_cols = get_table_columns(cursor, 'speciale_codes')
            has_term_in_codes = 'term' in speciale_codes_cols

        print("\nKenmerken detectie:")
        print(f"  UUID systeem: {'JA' if has_uuid else 'NEE'}")
        print(f"  Shift voorkeuren kolom: {'JA' if has_shift_voorkeuren else 'NEE'}")
        print(f"  Theme voorkeur kolom: {'JA' if has_theme_voorkeur else 'NEE'}")
        print(f"  Startweek typedienst: {'JA' if has_startweek else 'NEE'}")
        print(f"  Typetabel versioned systeem: {'JA' if has_typetabel_versies else 'NEE'}")
        print(f"  Verlof saldo systeem: {'JA' if has_verlof_saldo else 'NEE'}")
        print(f"  Term-based codes: {'JA' if has_term_in_codes else 'NEE'}")
        print(f"  Rode lijnen config: {'JA' if has_rode_lijnen_config else 'NEE'}")
        print()

        # Versie bepaling (van nieuw naar oud)
        if has_theme_voorkeur:
            version = "0.6.12"
            confidence = "high"
            details.append("\n[DETECTIE] Versie 0.6.12 (Theme Per Gebruiker)")
            details.append("  Reden: theme_voorkeur kolom aanwezig")
            details.append("  Migratie: Alleen db_metadata tabel toevoegen")
            details.append("  Script: upgrade_to_v0_6_13.py (bestaand script is geschikt)")

        elif has_shift_voorkeuren:
            version = "0.6.11"
            confidence = "high"
            details.append("\n[DETECTIE] Versie 0.6.11 (Shift Voorkeuren)")
            details.append("  Reden: shift_voorkeuren kolom aanwezig, theme_voorkeur niet")
            details.append("  Migratie pad:")
            details.append("    1. Voeg theme_voorkeur kolom toe (v0.6.11 -> v0.6.12)")
            details.append("    2. Voeg db_metadata tabel toe (v0.6.12 -> v0.6.13)")

        elif has_verlof_saldo:
            version = "0.6.10"
            confidence = "high"
            details.append("\n[DETECTIE] Versie 0.6.10 (Verlof & KD Saldo)")
            details.append("  Reden: verlof_saldo tabel aanwezig, shift_voorkeuren kolom niet")
            details.append("  Migratie pad:")
            details.append("    1. Voeg shift_voorkeuren kolom toe (v0.6.10 -> v0.6.11)")
            details.append("    2. Voeg theme_voorkeur kolom toe (v0.6.11 -> v0.6.12)")
            details.append("    3. Voeg db_metadata tabel toe (v0.6.12 -> v0.6.13)")

        elif has_rode_lijnen_config:
            version = "0.6.8"
            confidence = "medium"
            details.append("\n[DETECTIE] Versie 0.6.8 of 0.6.9 (Rode Lijnen Config)")
            details.append("  Reden: rode_lijnen_config tabel aanwezig")
            details.append("  Note: v0.6.9 had geen DB wijzigingen (alleen GUI)")
            details.append("  Migratie pad: Meerdere stappen vereist (v0.6.10, v0.6.11, v0.6.12, v0.6.13)")

        elif has_term_in_codes:
            version = "0.6.7"
            confidence = "high"
            details.append("\n[DETECTIE] Versie 0.6.7 (Term-based Codes)")
            details.append("  Reden: term kolom in speciale_codes aanwezig")
            details.append("  Migratie pad: Vele stappen vereist - neem contact op")

        elif has_typetabel_versies:
            version = "0.6.6"
            confidence = "high"
            details.append("\n[DETECTIE] Versie 0.6.6 (Typetabel Versioned)")
            details.append("  Reden: typetabel_versies en typetabel_data tabellen aanwezig")
            details.append("  Migratie pad: Vele stappen vereist - neem contact op")

        elif has_uuid:
            version = "0.6.4 - 0.6.5"
            confidence = "medium"
            details.append("\n[DETECTIE] Versie 0.6.4 of 0.6.5 (Shift Codes Systeem)")
            details.append("  Reden: UUID systeem aanwezig, maar geen versioned typetabel")
            details.append("  Migratie pad: Vele stappen vereist - neem contact op")

        else:
            version = "Pre-v0.6.4"
            confidence = "low"
            details.append("\n[DETECTIE] Pre-v0.6.4 (Zeer Oude Database)")
            details.append("  Reden: Geen moderne kenmerken gevonden")
            details.append("  Migratie: Niet ondersteund - volledige rebuild aanbevolen")

        # Extra database info
        details.append("\n--- Database Statistieken ---")
        cursor.execute("SELECT COUNT(*) FROM gebruikers WHERE is_actief = 1")
        user_count = cursor.fetchone()[0]
        details.append(f"Actieve gebruikers: {user_count}")

        if 'planning' in tables:
            cursor.execute("SELECT COUNT(*) FROM planning")
            planning_count = cursor.fetchone()[0]
            details.append(f"Planning records: {planning_count}")

        if 'verlof_aanvragen' in tables:
            cursor.execute("SELECT COUNT(*) FROM verlof_aanvragen")
            verlof_count = cursor.fetchone()[0]
            details.append(f"Verlof aanvragen: {verlof_count}")

        conn.close()
        return version, confidence, details

    except sqlite3.Error as e:
        conn.close()
        return "Error", "error", [f"Database fout: {str(e)}"]


def main():
    """Main entry point"""

    # Bepaal database pad
    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])
    else:
        db_path = Path("data/planning.db")

    print("\n" + "="*60)
    print("DATABASE VERSIE DETECTIE TOOL")
    print("="*60)
    print(f"\nAnalyseren: {db_path}")
    print(f"Tijdstip: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    version, confidence, details = detect_version(db_path)

    # Print details
    for detail in details:
        print(detail)

    # Conclusie
    print(f"\n{'='*60}")
    print("CONCLUSIE")
    print(f"{'='*60}")
    print(f"Gedetecteerde versie: {version}")
    print(f"Betrouwbaarheid: {confidence.upper()}")

    if confidence == "high":
        print("\n[OK] Versie detectie betrouwbaar")
    elif confidence == "medium":
        print("\n[WAARSCHUWING] Versie detectie niet 100% zeker - handmatige verificatie aanbevolen")
    else:
        print("\n[WAARSCHUWING] Versie detectie onzeker - handmatige analyse vereist")

    print("\n" + "="*60)
    print()


if __name__ == '__main__':
    main()
