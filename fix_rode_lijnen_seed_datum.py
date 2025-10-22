#!/usr/bin/env python3
"""
Fix Rode Lijnen Seed Datum
Herstelt rode lijnen van 28 juli 2024 naar 29 juli 2024 (correcte cyclus)

Dit script:
1. Detecteert of de database de oude start datum heeft (28 juli 2024)
2. Verwijdert alle rode lijnen vanaf die datum
3. Regenereert rode lijnen vanaf 29 juli 2024
4. Update rode_lijnen_config indien nodig

Kan veilig meerdere keren gedraaid worden (idempotent).
"""

import sqlite3
from datetime import datetime, timedelta
import sys

DB_PATH = 'data/planning.db'
OUDE_START = '2024-07-28'
NIEUWE_START = '2024-07-29'
INTERVAL = 28


def main():
    print("=" * 60)
    print("Fix Rode Lijnen Seed Datum")
    print("=" * 60)

    # Verbind met database
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        print(f"[OK] Verbonden met database: {DB_PATH}\n")
    except sqlite3.Error as e:
        print(f"[ERROR] Kan niet verbinden met database: {e}")
        sys.exit(1)

    # Stap 1: Check huidige situatie
    print("Stap 1: Huidige situatie analyseren...")
    cursor.execute("SELECT MIN(start_datum) as eerste FROM rode_lijnen")
    result = cursor.fetchone()

    if not result or not result['eerste']:
        print("[WARNING] Geen rode lijnen gevonden in database")
        print("Script heeft niets te doen.")
        conn.close()
        return

    eerste_datum = result['eerste']
    # Strip timestamp als die er is
    if 'T' in eerste_datum:
        eerste_datum = eerste_datum.split('T')[0]

    print(f"  Huidige eerste rode lijn: {eerste_datum}")

    if eerste_datum == NIEUWE_START:
        print("[OK] Rode lijnen zijn al correct!")
        print("Script heeft niets te doen.")
        conn.close()
        return

    if eerste_datum != OUDE_START:
        print(f"[WARNING] Onverwachte start datum: {eerste_datum}")
        print(f"Script verwacht {OUDE_START} of {NIEUWE_START}")
        print("Wil je toch doorgaan en alle rode lijnen regenereren vanaf 29 juli 2024? (ja/nee)")
        antwoord = input("> ").strip().lower()
        if antwoord not in ['ja', 'j', 'yes', 'y']:
            print("Script afgebroken.")
            conn.close()
            return

    # Stap 2: Backup maken (tellen)
    print("\nStap 2: Backup informatie...")
    cursor.execute("SELECT COUNT(*) as aantal FROM rode_lijnen")
    aantal_oud = cursor.fetchone()['aantal']
    cursor.execute("SELECT MAX(periode_nummer) as max_periode FROM rode_lijnen")
    max_periode_oud = cursor.fetchone()['max_periode']
    print(f"  Huidige rode lijnen: {aantal_oud} periodes (t/m periode {max_periode_oud})")

    # Stap 3: Verwijder oude rode lijnen
    print("\nStap 3: Oude rode lijnen verwijderen...")
    cursor.execute("DELETE FROM rode_lijnen")
    verwijderd = cursor.rowcount
    print(f"  [OK] {verwijderd} rode lijnen verwijderd")

    # Stap 4: Genereer nieuwe rode lijnen
    print("\nStap 4: Nieuwe rode lijnen genereren vanaf 29 juli 2024...")
    start = datetime.strptime(NIEUWE_START, '%Y-%m-%d')

    # Genereer tot +2 jaar vanaf nu
    doel_datum = datetime.now() + timedelta(days=730)

    periode_nummer = 1
    huidige = start
    toegevoegd = 0

    while huidige <= doel_datum:
        eind_datum = huidige + timedelta(days=INTERVAL - 1)
        cursor.execute("""
            INSERT INTO rode_lijnen (periode_nummer, start_datum, eind_datum)
            VALUES (?, ?, ?)
        """, (periode_nummer, huidige.date().isoformat(), eind_datum.date().isoformat()))

        huidige += timedelta(days=INTERVAL)
        periode_nummer += 1
        toegevoegd += 1

    print(f"  [OK] {toegevoegd} nieuwe rode lijnen periodes gegenereerd")
    print(f"  Van: {start.strftime('%d-%m-%Y')}")
    print(f"  Tot: {(huidige - timedelta(days=INTERVAL)).strftime('%d-%m-%Y')}")

    # Stap 5: Update rode_lijnen_config indien nodig
    print("\nStap 5: Rode lijnen config controleren...")
    cursor.execute("""
        SELECT id, start_datum FROM rode_lijnen_config
        WHERE start_datum = ? AND is_actief = 1
    """, (OUDE_START,))

    oude_config = cursor.fetchone()

    if oude_config:
        print(f"  Oude config gevonden met start datum {OUDE_START}")
        print(f"  Updaten naar {NIEUWE_START}...")
        cursor.execute("""
            UPDATE rode_lijnen_config
            SET start_datum = ?
            WHERE id = ?
        """, (NIEUWE_START, oude_config['id']))
        print("  [OK] Config bijgewerkt")
    else:
        print("  [OK] Config is al correct of niet aanwezig")

    # Stap 6: Commit changes
    print("\nStap 6: Wijzigingen opslaan...")
    conn.commit()
    print("  [OK] Database wijzigingen opgeslagen")

    # Stap 7: Verificatie
    print("\nStap 7: Verificatie...")
    cursor.execute("SELECT COUNT(*) as aantal FROM rode_lijnen")
    aantal_nieuw = cursor.fetchone()['aantal']

    cursor.execute("""
        SELECT periode_nummer, start_datum, eind_datum
        FROM rode_lijnen
        ORDER BY start_datum
        LIMIT 3
    """)
    eerste_3 = cursor.fetchall()

    cursor.execute("""
        SELECT periode_nummer, start_datum, eind_datum
        FROM rode_lijnen
        WHERE start_datum <= '2025-10-31' AND start_datum >= '2025-10-01'
        ORDER BY start_datum
    """)
    oktober_2025 = cursor.fetchall()

    print(f"  Nieuwe rode lijnen: {aantal_nieuw} periodes")
    print("\n  Eerste 3 periodes:")
    for row in eerste_3:
        print(f"    Periode {row['periode_nummer']:2}: {row['start_datum']} t/m {row['eind_datum']}")

    print("\n  Oktober 2025 (verificatie periode 17 = 20 okt):")
    for row in oktober_2025:
        marker = " <- CORRECT!" if row['start_datum'].startswith('2025-10-20') else ""
        print(f"    Periode {row['periode_nummer']:2}: {row['start_datum']} t/m {row['eind_datum']}{marker}")

    conn.close()

    print("\n" + "=" * 60)
    print("[OK] Rode lijnen succesvol hersteld!")
    print("=" * 60)
    print("\nHerstart de applicatie om de nieuwe rode lijnen te zien.")
    print("De rode lijn voor periode 17 staat nu tussen 19 en 20 oktober 2025.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Script afgebroken door gebruiker")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
