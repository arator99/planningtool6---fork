#services/data_ensure_service.py
"""
Auto-generatie service voor ontbrekende data
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
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    maand = (h + l - 7 * m + 114) // 31
    dag = ((h + l - 7 * m + 114) % 31) + 1

    return datetime(jaar, maand, dag)


def ensure_jaar_data(jaar):
    """
    Zorg dat alle data bestaat voor een jaar
    Returns: dict met warnings voor gebruiker
    """
    warnings = []

    # Feestdagen
    if not feestdagen_bestaan(jaar):
        genereer_feestdagen_template(jaar)
        warnings.append({
            'type': 'feestdagen_gegenereerd',
            'jaar': jaar,
            'boodschap': f'Feestdagen voor {jaar} zijn automatisch aangemaakt met berekende datums.'
        })

    # Rode lijnen
    laatste_dag = datetime(jaar, 12, 31)
    if not rode_lijnen_bestaan_tot(laatste_dag):
        aantal = extend_rode_lijnen_tot(laatste_dag + timedelta(days=365))
        warnings.append({
            'type': 'rode_lijnen_gegenereerd',
            'jaar': jaar,
            'boodschap': f'{aantal} rode lijnen periodes automatisch toegevoegd.'
        })

    return warnings


def feestdagen_bestaan(jaar):
    """Check of er feestdagen zijn voor jaar"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM feestdagen WHERE jaar = ?", (jaar,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def genereer_feestdagen_template(jaar):
    """Genereer Belgische feestdagen voor jaar (inclusief berekende variabele datums)"""
    conn = get_connection()
    cursor = conn.cursor()

    # Vaste feestdagen
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
            INSERT INTO feestdagen (datum, naam, jaar, type, is_ingevuld)
            VALUES (?, ?, ?, 'vast', 1)
        """, (datum, naam, jaar))

    # Bereken variabele feestdagen op basis van Pasen
    pasen = bereken_pasen(jaar)
    paasmaandag = pasen + timedelta(days=1)
    hemelvaart = pasen + timedelta(days=39)  # 39 dagen na Pasen
    pinkstermaandag = pasen + timedelta(days=50)  # 50 dagen na Pasen

    variabele_feestdagen = [
        (paasmaandag, 'Paasmaandag'),
        (hemelvaart, 'O.H. Hemelvaart'),
        (pinkstermaandag, 'Pinkstermaandag'),
    ]

    for datum_obj, naam in variabele_feestdagen:
        datum = datum_obj.strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO feestdagen (datum, naam, jaar, type, is_ingevuld)
            VALUES (?, ?, ?, 'variabel', 1)
        """, (datum, naam, jaar))

    conn.commit()
    conn.close()
    print(f"  ✓ Feestdagen voor {jaar} gegenereerd (inclusief berekende variabele datums)")


def rode_lijnen_bestaan_tot(datum):
    """Check of rode lijnen bestaan tot datum"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(start_datum) FROM rode_lijnen
    """)
    result = cursor.fetchone()[0]
    conn.close()

    if not result:
        return False

    laatste = datetime.fromisoformat(result)
    return laatste >= datum


def extend_rode_lijnen_tot(doel_datum):
    """Extend rode lijnen tot doel_datum, return aantal toegevoegd"""
    conn = get_connection()
    cursor = conn.cursor()

    # Haal laatste rode lijn
    cursor.execute("SELECT MAX(start_datum) FROM rode_lijnen")
    result = cursor.fetchone()[0]

    if not result:
        # Geen rode lijnen, start vanaf bekende datum
        start = datetime(2024, 7, 28)
    else:
        start = datetime.fromisoformat(result) + timedelta(days=28)

    # Genereer tot doel
    toegevoegd = 0
    huidige = start

    while huidige <= doel_datum:
        cursor.execute("""
            INSERT INTO rode_lijnen (start_datum)
            VALUES (?)
        """, (huidige.isoformat(),))
        huidige += timedelta(days=28)
        toegevoegd += 1

    conn.commit()
    conn.close()

    if toegevoegd > 0:
        print(f"  ✓ {toegevoegd} rode lijnen periodes toegevoegd")

    return toegevoegd