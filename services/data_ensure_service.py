#services/data_ensure_service.py
"""
Auto-generatie service voor ontbrekende data
Lazy initialization pattern: genereer alleen wat nodig is, wanneer het nodig is
"""

from datetime import datetime, timedelta
from database.connection import get_connection


def bereken_pasen(jaar):
    """
    Bereken Paaszondag voor gegeven jaar (Computus algoritme - Meeus/Jones/Butcher)
    Werkt voor Gregoriaanse kalender (vanaf 1583)
    """
    a = jaar % 19
    b = jaar // 100
    c = jaar % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    L = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * L) // 451
    maand = (h + L - 7 * m + 114) // 31
    dag = ((h + L - 7 * m + 114) % 31) + 1

    return datetime(jaar, maand, dag)


def ensure_jaar_data(jaar):
    """
    Zorg dat alle data bestaat voor een jaar
    Genereer on-demand: feestdagen + rode lijnen tot eind jaar + 3 maanden buffer
    Returns: dict met warnings voor gebruiker
    """
    warnings = []

    # Feestdagen
    if not feestdagen_bestaan(jaar):
        genereer_feestdagen_template(jaar)
        warnings.append({
            'type': 'feestdagen_gegenereerd',
            'jaar': jaar,
            'boodschap': f'Feestdagen voor {jaar} zijn automatisch aangemaakt.'
        })

    # Rode lijnen tot eind jaar + 3 maanden buffer
    doel_datum = datetime(jaar, 12, 31) + timedelta(days=90)
    if not rode_lijnen_bestaan_tot(doel_datum):
        aantal = extend_rode_lijnen_tot(doel_datum)
        if aantal > 0:
            warnings.append({
                'type': 'rode_lijnen_gegenereerd',
                'jaar': jaar,
                'boodschap': f'{aantal} rode lijnen periodes automatisch toegevoegd.'
            })

    return warnings


def ensure_rode_lijnen_tot(datum):
    """
    Publieke functie: zorg dat rode lijnen bestaan tot datum
    Kan aangeroepen worden vanuit validatie/planning services
    """
    if not rode_lijnen_bestaan_tot(datum):
        return extend_rode_lijnen_tot(datum)
    return 0


def feestdagen_bestaan(jaar):
    """Check of er feestdagen zijn voor jaar"""
    conn = get_connection()
    cursor = conn.cursor()
    # Jaar zit in de datum kolom (YYYY-MM-DD), gebruik LIKE of substr
    cursor.execute("""
        SELECT COUNT(*) FROM feestdagen 
        WHERE datum LIKE ?
    """, (f"{jaar}-%",))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def genereer_feestdagen_template(jaar):
    """Genereer Belgische feestdagen voor jaar (inclusief berekende variabele datums)"""
    conn = get_connection()
    cursor = conn.cursor()

    # Vaste feestdagen (is_variabel = 0)
    vaste_feestdagen = [
        (1, 1, 'Nieuwjaar'),
        (5, 1, 'Dag van de Arbeid'),
        (7, 21, 'Nationale feestdag'),
        (8, 15, 'O.L.V. Hemelvaart'),
        (11, 1, 'Allerheiligen'),
        (11, 11, 'Wapenstilstand'),
        (12, 25, 'Kerstmis'),
    ]

    for maand, dag, naam in vaste_feestdagen:
        datum = f"{jaar}-{maand:02d}-{dag:02d}"
        cursor.execute("""
            INSERT OR IGNORE INTO feestdagen (datum, naam, is_zondagsrust, is_variabel)
            VALUES (?, ?, 1, 0)
        """, (datum, naam))

    # Bereken variabele feestdagen op basis van Pasen (is_variabel = 1)
    pasen = bereken_pasen(jaar)
    paasmaandag = pasen + timedelta(days=1)
    hemelvaart = pasen + timedelta(days=39)
    pinkstermaandag = pasen + timedelta(days=50)

    variabele_feestdagen = [
        (paasmaandag, 'Paasmaandag'),
        (hemelvaart, 'O.H. Hemelvaart'),
        (pinkstermaandag, 'Pinkstermaandag'),
    ]

    for datum_obj, naam in variabele_feestdagen:
        datum = datum_obj.strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT OR IGNORE INTO feestdagen (datum, naam, is_zondagsrust, is_variabel)
            VALUES (?, ?, 1, 1)
        """, (datum, naam))

    conn.commit()
    conn.close()
    print(f"  ✓ Feestdagen voor {jaar} gegenereerd (inclusief berekende variabele datums)")


def rode_lijnen_bestaan_tot(datum):
    """Check of rode lijnen bestaan tot gegeven datum"""
    conn = get_connection()
    cursor = conn.cursor()

    # Haal actieve config op voor interval
    cursor.execute("""
        SELECT interval_dagen FROM rode_lijnen_config
        WHERE is_actief = 1
        ORDER BY actief_vanaf DESC
        LIMIT 1
    """)
    config = cursor.fetchone()
    interval = config[0] if config else 28  # Fallback naar 28

    cursor.execute("""
        SELECT MAX(start_datum) FROM rode_lijnen
    """)
    result = cursor.fetchone()[0]
    conn.close()

    if not result:
        return False

    laatste = datetime.fromisoformat(result)
    # Rode lijn periode duurt X dagen (volgens config), dus check of laatste + interval >= doel
    return (laatste + timedelta(days=interval)) >= datum


def extend_rode_lijnen_tot(doel_datum):
    """
    Extend rode lijnen tot doel_datum
    Returns: aantal toegevoegde periodes
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Haal actieve config op voor start en interval
    cursor.execute("""
        SELECT start_datum, interval_dagen FROM rode_lijnen_config
        WHERE is_actief = 1
        ORDER BY actief_vanaf DESC
        LIMIT 1
    """)
    config = cursor.fetchone()

    if not config:
        # Fallback naar oude defaults
        config_start_datum = datetime(2024, 7, 28)
        interval = 28
    else:
        config_start_datum = datetime.fromisoformat(config[0])
        interval = config[1]

    # Haal laatste rode lijn en hoogste periode nummer
    cursor.execute("SELECT MAX(start_datum), MAX(periode_nummer) FROM rode_lijnen")
    result = cursor.fetchone()
    laatste_datum = result[0]
    laatste_nummer = result[1] or 0  # Start bij 0 als er geen periodes zijn

    if not laatste_datum:
        # Geen rode lijnen, start vanaf config start datum
        start = config_start_datum
        periode_nummer = 1
    else:
        # Start na de laatste periode (gebruik interval uit config)
        start = datetime.fromisoformat(laatste_datum) + timedelta(days=interval)
        periode_nummer = laatste_nummer + 1

    # Genereer tot doel
    toegevoegd = 0
    huidige = start

    while huidige <= doel_datum:
        eind_datum = huidige + timedelta(days=interval - 1)  # X dagen cyclus (eind is inclusief)
        cursor.execute("""
            INSERT INTO rode_lijnen (periode_nummer, start_datum, eind_datum)
            VALUES (?, ?, ?)
        """, (periode_nummer, huidige.isoformat(), eind_datum.isoformat()))
        huidige += timedelta(days=interval)
        periode_nummer += 1
        toegevoegd += 1

    conn.commit()
    conn.close()

    if toegevoegd > 0:
        print(f"  ✓ {toegevoegd} rode lijnen periodes toegevoegd tot {doel_datum.strftime('%d-%m-%Y')}")

    return toegevoegd


def regenereer_rode_lijnen_vanaf(actief_vanaf_str: str):
    """
    Regenereer rode lijnen vanaf een bepaalde datum met nieuwe configuratie

    Gebruikt:
    - Na het wijzigen van rode lijnen configuratie
    - Verwijdert toekomstige rode lijnen vanaf actief_vanaf
    - Genereert nieuwe rode lijnen met nieuwe config tot +2 jaar

    Args:
        actief_vanaf_str: ISO datum string (YYYY-MM-DD) vanaf wanneer nieuwe config actief is
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        actief_vanaf = datetime.fromisoformat(actief_vanaf_str).date()

        # Stap 1: Verwijder alle rode lijnen vanaf actief_vanaf datum
        cursor.execute("""
            DELETE FROM rode_lijnen
            WHERE start_datum >= ?
        """, (actief_vanaf.isoformat(),))

        verwijderd = cursor.rowcount
        print(f"  [OK] {verwijderd} rode lijnen periodes verwijderd vanaf {actief_vanaf.isoformat()}")

        # Stap 2: Haal nieuwe actieve config op
        cursor.execute("""
            SELECT start_datum, interval_dagen FROM rode_lijnen_config
            WHERE is_actief = 1
            ORDER BY actief_vanaf DESC
            LIMIT 1
        """)
        config = cursor.fetchone()

        if not config:
            print("  [WARNING] Geen actieve rode lijnen configuratie gevonden")
            conn.close()
            return 0

        config_start_datum = datetime.fromisoformat(config[0]).date()
        interval = config[1]

        # Stap 3: Bepaal vanaf waar we moeten starten
        # Check of config_start_datum >= actief_vanaf (nieuwe cyclus start)
        if config_start_datum >= actief_vanaf:
            # Nieuwe cyclus: start vanaf config start datum
            start_datum = config_start_datum

            # Haal hoogste periode nummer voor nummering
            cursor.execute("SELECT MAX(periode_nummer) FROM rode_lijnen WHERE start_datum < ?",
                          (config_start_datum.isoformat(),))
            laatste_nummer = cursor.fetchone()[0] or 0
            periode_nummer = laatste_nummer + 1
        else:
            # Continue bestaande cyclus: haal laatste rode lijn vóór actief_vanaf
            cursor.execute("""
                SELECT MAX(start_datum), MAX(periode_nummer) FROM rode_lijnen
                WHERE start_datum < ?
            """, (actief_vanaf.isoformat(),))

            result = cursor.fetchone()
            laatste_datum_str = result[0]
            laatste_nummer = result[1] or 0

            if laatste_datum_str:
                # Er zijn rode lijnen voor actief_vanaf - continue vanaf daar
                laatste_datum = datetime.fromisoformat(laatste_datum_str).date()
                start_datum = laatste_datum + timedelta(days=interval)
                periode_nummer = laatste_nummer + 1
            else:
                # Geen rode lijnen voor actief_vanaf - start vanaf config start
                start_datum = config_start_datum
                periode_nummer = 1

        # Stap 4: Genereer nieuwe rode lijnen tot +2 jaar
        doel_datum = datetime.now().date() + timedelta(days=730)  # +2 jaar

        toegevoegd = 0
        huidige = start_datum

        while huidige <= doel_datum:
            eind_datum = huidige + timedelta(days=interval - 1)
            cursor.execute("""
                INSERT INTO rode_lijnen (periode_nummer, start_datum, eind_datum)
                VALUES (?, ?, ?)
            """, (periode_nummer, huidige.isoformat(), eind_datum.isoformat()))

            huidige += timedelta(days=interval)
            periode_nummer += 1
            toegevoegd += 1

        conn.commit()
        print(f"  [OK] {toegevoegd} nieuwe rode lijnen periodes gegenereerd tot {doel_datum.isoformat()}")

        return toegevoegd

    except Exception as e:
        conn.rollback()
        print(f"  [ERROR] Fout bij regenereren rode lijnen: {e}")
        raise
    finally:
        conn.close()