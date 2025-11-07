#!/usr/bin/env python3
"""
Voeg HR regel toe: Nacht gevolgd door vroeg verboden

Deze regel voorkomt dat een vroege shift direct na een nacht shift komt,
tenzij er verlof of ziekte tussen zit.
"""
import sys
sys.path.insert(0, 'C:\\Users\\arato\\PycharmProjects\\planningstool 6 - claude')

from database.connection import get_connection
from datetime import datetime

def add_nacht_vroeg_regel():
    conn = get_connection()
    cursor = conn.cursor()

    # Check of regel al bestaat
    cursor.execute("""
        SELECT id FROM hr_regels
        WHERE naam = 'Nacht gevolgd door vroeg verboden'
        AND is_actief = 1
    """)

    if cursor.fetchone():
        print("  [SKIP] HR regel 'Nacht gevolgd door vroeg verboden' bestaat al")
        conn.close()
        return

    # Voeg regel toe
    # Waarde: niet gebruikt (we gebruiken beschrijving voor de configuratie)
    # Eenheid: 'terms' - geeft aan dat beschrijving een lijst van terms bevat
    # Beschrijving: comma-separated lijst van terms die mogen breken
    cursor.execute("""
        INSERT INTO hr_regels (naam, waarde, eenheid, beschrijving, is_actief)
        VALUES (?, ?, ?, ?, ?)
    """, (
        'Nacht gevolgd door vroeg verboden',
        0,  # Niet gebruikt
        'terms',
        'verlof,ziek',  # Terms die nacht->vroeg mogen breken
        1
    ))

    conn.commit()
    print(f"  [OK] HR regel toegevoegd: 'Nacht gevolgd door vroeg verboden'")
    print(f"       Breek terms: verlof, ziek")

    conn.close()

if __name__ == '__main__':
    print("=== Nacht gevolgd door Vroeg Regel Toevoegen ===\n")
    add_nacht_vroeg_regel()
    print("\nGereed!")
