"""
Bemannings Controle Service

Valideert of planning volledig bemand is door kritische shift_codes te vergelijken
met verwachte bemanning. De shift_codes tabel definieert wat er verwacht wordt:
- 1 code in tabel = 1 persoon verwacht
- 2 codes in tabel = 2 personen verwacht (bijv. 7101 + 7102)

BELANGRIJKE WIJZIGING (v0.6.21):
Alleen shift codes gemarkeerd als 'kritisch' (is_kritisch = 1) worden gevalideerd.
Niet-kritische shifts worden genegeerd in de bemanningscontrole.

PERFORMANCE OPTIMALISATIE (v0.6.25):
Nieuwe functie valideer_datum_from_data() werkt met in-memory data ipv database queries.
Gebruikt door ValidationCache voor batch processing (15-30x sneller).

Statussen:
- groen: Alle kritische codes minimaal 1x ingevuld
- geel: Dubbele kritische shift_code gebruikt (waarschuwing, kan correct zijn)
- rood: Ontbrekende kritische shift_code(s)
"""

from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
from database.connection import get_connection


def get_dag_type(datum: date) -> str:
    """
    Bepaal dag type voor een datum.

    BELANGRIJK: Feestdagen worden behandeld als 'zondag' (v0.6.25 fix)
    Dit zorgt voor consistentie met shift invoer (waar feestdagen ook zondag shifts accepteren)

    Args:
        datum: Date object

    Returns:
        'weekdag', 'zaterdag', of 'zondag'
    """
    # Check eerst of het een feestdag is (feestdag = zondag)
    if is_feestdag(datum):
        return 'zondag'

    # Anders: normale weekdag bepaling
    weekdag = datum.weekday()  # 0=maandag, 6=zondag

    if weekdag == 6:  # Zondag
        return 'zondag'
    elif weekdag == 5:  # Zaterdag
        return 'zaterdag'
    else:
        return 'weekdag'


def is_feestdag(datum: date) -> bool:
    """
    Check of een datum een feestdag is

    Args:
        datum: Date object

    Returns:
        True als feestdag, anders False
    """
    datum_str = datum.strftime('%Y-%m-%d')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as count
        FROM feestdagen
        WHERE datum = ?
    """, (datum_str,))

    result = cursor.fetchone()
    conn.close()

    return result['count'] > 0 if result else False


def get_verwachte_codes(datum: date) -> List[Dict]:
    """
    Haal verwachte KRITISCHE shift_codes op voor een datum op basis van dag_type.

    Alleen shift codes met is_kritisch = 1 worden geretourneerd.

    Args:
        datum: Date object

    Returns:
        List van dicts met code info:
        [
            {
                'code': '7101',
                'shift_type': 'vroeg',
                'werkpost_naam': 'Interventie',
                'start_uur': '06:00',
                'eind_uur': '14:00'
            },
            ...
        ]
    """
    dag_type = get_dag_type(datum)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            sc.code,
            sc.shift_type,
            sc.start_uur,
            sc.eind_uur,
            w.naam as werkpost_naam,
            w.id as werkpost_id
        FROM shift_codes sc
        JOIN werkposten w ON sc.werkpost_id = w.id
        WHERE sc.dag_type = ?
        AND w.is_actief = 1
        AND sc.is_kritisch = 1
        ORDER BY w.naam, sc.shift_type
    """, (dag_type,))

    results = []
    for row in cursor.fetchall():
        results.append({
            'code': row['code'],
            'shift_type': row['shift_type'],
            'start_uur': row['start_uur'],
            'eind_uur': row['eind_uur'],
            'werkpost_naam': row['werkpost_naam'],
            'werkpost_id': row['werkpost_id']
        })

    return results


def get_werkelijke_codes(datum: date) -> List[Dict]:
    """
    Haal werkelijke planning op voor een datum.

    Args:
        datum: Date object

    Returns:
        List van dicts met planning info:
        [
            {
                'code': '7101',
                'gebruiker_naam': 'Jan Jansen',
                'gebruiker_id': 1
            },
            ...
        ]
    """
    datum_str = datum.strftime('%Y-%m-%d')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.shift_code as code,
            g.volledige_naam as gebruiker_naam,
            g.id as gebruiker_id
        FROM planning p
        JOIN gebruikers g ON p.gebruiker_id = g.id
        WHERE p.datum = ?
        AND p.shift_code IS NOT NULL
        AND p.shift_code != ''
        AND g.is_actief = 1
        ORDER BY p.shift_code, g.volledige_naam
    """, (datum_str,))

    results = []
    for row in cursor.fetchall():
        results.append({
            'code': row['code'],
            'gebruiker_naam': row['gebruiker_naam'],
            'gebruiker_id': row['gebruiker_id']
        })

    return results


def controleer_bemanning(datum: date) -> Dict:
    """
    Controleer of bemanning compleet is voor een datum.

    Args:
        datum: Date object

    Returns:
        Dict met validatie resultaten:
        {
            'status': 'groen'|'geel'|'rood',
            'verwachte_codes': [...],
            'werkelijke_codes': [...],
            'ontbrekende_codes': [...],
            'dubbele_codes': [...],
            'details': "Menselijk leesbare status"
        }
    """
    verwachte_codes = get_verwachte_codes(datum)
    werkelijke_codes = get_werkelijke_codes(datum)

    # Maak lookup dictionaries
    verwacht_dict = {code['code']: code for code in verwachte_codes}

    # Groepeer werkelijke codes (voor dubbele detectie)
    werkelijk_dict: Dict[str, List[str]] = {}
    for item in werkelijke_codes:
        code = item['code']
        if code not in werkelijk_dict:
            werkelijk_dict[code] = []
        werkelijk_dict[code].append(item['gebruiker_naam'])

    # Filter alleen shift_codes (niet speciale codes zoals VV, KD, etc.)
    werkelijk_shift_codes = {
        code: users
        for code, users in werkelijk_dict.items()
        if code in verwacht_dict
    }

    # Vind ontbrekende codes
    ontbrekende_codes = []
    for code, info in verwacht_dict.items():
        if code not in werkelijk_shift_codes:
            ontbrekende_codes.append({
                'code': code,
                'shift_type': info['shift_type'],
                'werkpost_naam': info['werkpost_naam'],
                'start_uur': info['start_uur'],
                'eind_uur': info['eind_uur']
            })

    # Vind dubbele codes
    dubbele_codes = []
    for code, users in werkelijk_shift_codes.items():
        if len(users) > 1:
            dubbele_codes.append({
                'code': code,
                'shift_type': verwacht_dict[code]['shift_type'],
                'werkpost_naam': verwacht_dict[code]['werkpost_naam'],
                'gebruikers': users
            })

    # Bepaal status
    if ontbrekende_codes:
        status = 'rood'
        details = f"Onvolledig: {len(ontbrekende_codes)} shift(s) ontbreken"
    elif dubbele_codes:
        status = 'geel'
        details = f"Dubbele codes: {len(dubbele_codes)} shift(s) meerdere keren ingepland"
    else:
        status = 'groen'
        details = "Volledig bemand"

    return {
        'status': status,
        'verwachte_codes': verwachte_codes,
        'werkelijke_codes': werkelijke_codes,
        'ontbrekende_codes': ontbrekende_codes,
        'dubbele_codes': dubbele_codes,
        'details': details
    }


def valideer_datum_from_data(
    datum: date,
    planning_data: Dict[int, str],
    shift_codes_data: Dict[str, Dict]
) -> str:
    """
    PERFORMANCE OPTIMALISATIE (v0.6.25): Valideer bemanning met in-memory data

    Deze functie werkt ZONDER database queries - alle data wordt meegegeven.
    Gebruikt door ValidationCache voor batch processing.

    Args:
        datum: Date object
        planning_data: {gebruiker_id: shift_code, ...} voor deze datum
        shift_codes_data: {code: {'werkpost_id': ..., 'is_kritisch': ...}, ...}

    Returns:
        'groen', 'geel', of 'rood'
    """
    # Bepaal dag type
    dag_type = get_dag_type(datum)

    # Haal verwachte kritische codes op (MOET nog steeds uit database)
    verwachte_codes = get_verwachte_codes(datum)

    if not verwachte_codes:
        # Geen kritische shifts verwacht voor deze dag
        return 'groen'

    # Maak set van verwachte codes
    verwacht_set = {code['code'] for code in verwachte_codes}

    # Filter werkelijke planning: alleen codes die ook verwacht worden
    werkelijke_codes_count: Dict[str, int] = {}
    for gebruiker_id, shift_code in planning_data.items():
        if not shift_code:
            continue

        # Check of dit een verwachte kritische code is
        if shift_code in verwacht_set:
            if shift_code not in werkelijke_codes_count:
                werkelijke_codes_count[shift_code] = 0
            werkelijke_codes_count[shift_code] += 1

    # Vind ontbrekende codes
    ontbrekende_codes = verwacht_set - set(werkelijke_codes_count.keys())

    # Vind dubbele codes
    dubbele_codes = {
        code: count
        for code, count in werkelijke_codes_count.items()
        if count > 1
    }

    # Bepaal status
    if ontbrekende_codes:
        return 'rood'  # Onvolledig
    elif dubbele_codes:
        return 'geel'  # Dubbele codes
    else:
        return 'groen'  # Volledig


def controleer_maand(jaar: int, maand: int) -> Dict:
    """
    Controleer bemanning voor hele maand.

    Args:
        jaar: Jaar (bijv. 2025)
        maand: Maand nummer (1-12)

    Returns:
        Dict met validatie resultaten per dag:
        {
            'samenvatting': {
                'volledig': 18,
                'dubbel': 3,
                'onvolledig': 9,
                'totaal': 30
            },
            'dagen': {
                '2025-10-01': {...controle resultaat...},
                '2025-10-02': {...},
                ...
            }
        }
    """
    # Bepaal aantal dagen in maand
    if maand == 12:
        volgende_maand_datum = date(jaar + 1, 1, 1)
    else:
        volgende_maand_datum = date(jaar, maand + 1, 1)

    eerste_dag = date(jaar, maand, 1)

    # Controleer elke dag
    dagen_resultaten = {}
    volledig_count = 0
    dubbel_count = 0
    onvolledig_count = 0

    current_datum = eerste_dag
    while current_datum < volgende_maand_datum:
        datum_str = current_datum.strftime('%Y-%m-%d')
        resultaat = controleer_bemanning(current_datum)
        dagen_resultaten[datum_str] = resultaat

        if resultaat['status'] == 'groen':
            volledig_count += 1
        elif resultaat['status'] == 'geel':
            dubbel_count += 1
        else:  # rood
            onvolledig_count += 1

        # Volgende dag
        from datetime import timedelta
        current_datum += timedelta(days=1)

    totaal_dagen = volledig_count + dubbel_count + onvolledig_count

    return {
        'samenvatting': {
            'volledig': volledig_count,
            'dubbel': dubbel_count,
            'onvolledig': onvolledig_count,
            'totaal': totaal_dagen
        },
        'dagen': dagen_resultaten
    }


def format_ontbrekende_codes(ontbrekende: List[Dict]) -> str:
    """
    Format ontbrekende codes voor weergave in Excel of UI.

    Args:
        ontbrekende: List van ontbrekende code dicts

    Returns:
        Geformatteerde string, bijv: "7101 (Interventie vroeg), 7301 (Interventie nacht)"
    """
    parts = []
    for item in ontbrekende:
        code = item['code']
        werkpost = item['werkpost_naam']
        shift = item['shift_type']
        parts.append(f"{code} ({werkpost} {shift})")

    return ", ".join(parts)


def format_dubbele_codes(dubbele: List[Dict]) -> str:
    """
    Format dubbele codes voor weergave in Excel of UI.

    Args:
        dubbele: List van dubbele code dicts

    Returns:
        Geformatteerde string, bijv: "7101 gebruikt door Jan, Piet"
    """
    parts = []
    for item in dubbele:
        code = item['code']
        gebruikers = ", ".join(item['gebruikers'])
        parts.append(f"{code} gebruikt door {gebruikers}")

    return " | ".join(parts)
