"""
Database migratie script voor theme voorkeur per gebruiker
v0.6.11 -> v0.6.12

Voegt theme_voorkeur kolom toe aan gebruikers tabel
Migreert bestaande globale theme voorkeur (indien aanwezig)
"""

import sqlite3
import json
from pathlib import Path


def migreer_theme_per_gebruiker():
    """Voeg theme_voorkeur kolom toe aan gebruikers tabel"""

    db_path = Path("data/planning.db")
    if not db_path.exists():
        print("Database niet gevonden. Run eerst main.py om database aan te maken.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check of kolom al bestaat
        cursor.execute("PRAGMA table_info(gebruikers)")
        kolommen = [row[1] for row in cursor.fetchall()]

        if 'theme_voorkeur' in kolommen:
            print("Theme voorkeur kolom bestaat al. Migratie al uitgevoerd.")
            conn.close()
            return

        print("Start migratie: theme_voorkeur kolom toevoegen...")

        # Voeg kolom toe met default 'light'
        cursor.execute("""
            ALTER TABLE gebruikers
            ADD COLUMN theme_voorkeur TEXT DEFAULT 'light'
        """)

        # Probeer oude globale theme voorkeur te migreren
        theme_file = Path("data/theme_preference.json")
        global_theme = 'light'  # default

        if theme_file.exists():
            try:
                with open(theme_file, 'r') as f:
                    data = json.load(f)
                    global_theme = data.get('theme', 'light')
                print(f"Gevonden globale theme voorkeur: {global_theme}")
            except (FileNotFoundError, json.JSONDecodeError):
                pass

        # Update alle bestaande gebruikers met de globale theme voorkeur
        cursor.execute("""
            UPDATE gebruikers
            SET theme_voorkeur = ?
            WHERE theme_voorkeur IS NULL OR theme_voorkeur = ''
        """, (global_theme,))

        updated_count = cursor.rowcount

        conn.commit()
        print("Migratie succesvol! Theme voorkeur kolom toegevoegd.")
        print(f"{updated_count} gebruikers geupdate met theme '{global_theme}'")

        # Info over oude JSON bestand
        if theme_file.exists():
            print("\nLET OP: Het oude theme_preference.json bestand kan verwijderd worden.")
            print("Theme voorkeuren worden nu per gebruiker opgeslagen in de database.")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database fout tijdens migratie: {e}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("PLANNING TOOL - Database Migratie")
    print("Theme Voorkeur Per Gebruiker (v0.6.11 -> v0.6.12)")
    print("=" * 60)
    print()

    migreer_theme_per_gebruiker()

    print()
    print("=" * 60)
    print("Migratie proces voltooid!")
    print("=" * 60)
