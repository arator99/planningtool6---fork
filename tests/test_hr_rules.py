#!/usr/bin/env python
"""Test HR rules implementation with new logic"""
from database.connection import get_connection

def test_periode_detectie(jaar, maand):
    """Test nieuwe periode detectie logica"""
    conn = get_connection()
    cursor = conn.cursor()

    maand_start = f"{jaar}-{maand:02d}-01"

    print(f"\n{'='*60}")
    print(f"Test voor maand: {jaar}-{maand:02d}")
    print('='*60)

    # STAP 1: Zoek rode lijn die START binnen deze maand
    cursor.execute("""
        SELECT periode_nummer, start_datum, eind_datum
        FROM rode_lijnen
        WHERE start_datum LIKE ?
        ORDER BY start_datum ASC
        LIMIT 1
    """, (f"{jaar}-{maand:02d}-%",))

    huidige = cursor.fetchone()

    if huidige:
        print(f"STAP 1: Rode lijn START in deze maand gevonden")
        print(f"  Periode {huidige['periode_nummer']}: {huidige['start_datum']} t/m {huidige['eind_datum']}")
    else:
        print(f"STAP 1: Geen rode lijn start in deze maand")

        # STAP 2: Gebruik periode waar maand in valt
        cursor.execute("""
            SELECT periode_nummer, start_datum, eind_datum
            FROM rode_lijnen
            WHERE start_datum <= ? AND eind_datum >= ?
            ORDER BY start_datum DESC
            LIMIT 1
        """, (maand_start, maand_start))

        huidige = cursor.fetchone()

        if huidige:
            print(f"STAP 2: Gebruik periode waar maand in valt")
            print(f"  Periode {huidige['periode_nummer']}: {huidige['start_datum']} t/m {huidige['eind_datum']}")

    if huidige:
        # Haal vorige periode op
        vorig_periode_nr = huidige['periode_nummer'] - 1
        cursor.execute("""
            SELECT periode_nummer, start_datum, eind_datum
            FROM rode_lijnen
            WHERE periode_nummer = ?
        """, (vorig_periode_nr,))

        vorige = cursor.fetchone()

        if vorige:
            print(f"\nVorige periode:")
            print(f"  Periode {vorige['periode_nummer']}: {vorige['start_datum']} t/m {vorige['eind_datum']}")

            print(f"\n{'Voor RL':15} = Periode {vorige['periode_nummer']} ({vorige['start_datum']} t/m {vorige['eind_datum']})")
            print(f"{'Na RL':15} = Periode {huidige['periode_nummer']} ({huidige['start_datum']} t/m {huidige['eind_datum']})")

    conn.close()

def test_werkdagen_telling():
    """Test werkdagen telling"""
    conn = get_connection()
    cursor = conn.cursor()

    # Haal gebruiker met planning data
    cursor.execute("""
        SELECT DISTINCT g.id, g.volledige_naam
        FROM gebruikers g
        JOIN planning p ON g.id = p.gebruiker_id
        WHERE g.gebruikersnaam != 'admin'
        LIMIT 1
    """)

    gebruiker = cursor.fetchone()

    if gebruiker:
        gebruiker_id = gebruiker['id']
        print(f"\n{'='*60}")
        print(f"Werkdagen telling voor: {gebruiker['volledige_naam']} (ID: {gebruiker_id})")
        print('='*60)

        # Haal alle planning op voor deze gebruiker
        cursor.execute("""
            SELECT datum, shift_code
            FROM planning
            WHERE gebruiker_id = ?
            ORDER BY datum
        """, (gebruiker_id,))

        rows = cursor.fetchall()
        print(f"\nPlanning records: {len(rows)}")
        if rows:
            print(f"Eerste: {rows[0]['datum']} ({rows[0]['shift_code']})")
            print(f"Laatste: {rows[-1]['datum']} ({rows[-1]['shift_code']})")

    conn.close()

if __name__ == "__main__":
    # Test september 2025 (rode lijn op 22 sept)
    test_periode_detectie(2025, 9)

    # Test oktober 2025 (geen rode lijn in maand)
    test_periode_detectie(2025, 10)

    # Test werkdagen telling
    test_werkdagen_telling()
