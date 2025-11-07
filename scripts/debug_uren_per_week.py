"""
Debug script: Uren per week check voor Bob Aerts november 2024
Scenario: dinsdag 5/11 t/m maandag 11/11 = 7 dagen

User report: "6 dagen x 8u = 48u + shiften in andere week"
Suggereert dat week definitie verkeerd werkt
"""
import sys
sys.path.insert(0, '.')

from datetime import date, datetime, timedelta
from database.connection import get_connection

def parse_week_definitie(week_def: str):
    """Parse week_definitie string naar start en eind"""
    # Format: "ma-00:00|zo-23:59"
    start_str, eind_str = week_def.split('|')

    dag_map = {
        'ma': 0, 'di': 1, 'wo': 2, 'do': 3,
        'vr': 4, 'za': 5, 'zo': 6
    }

    start_dag, start_tijd = start_str.split('-')
    eind_dag, eind_tijd = eind_str.split('-')

    return {
        'start_weekdag': dag_map[start_dag],
        'start_tijd': start_tijd,
        'eind_weekdag': dag_map[eind_dag],
        'eind_tijd': eind_tijd
    }

def get_week_start(datum: date, week_def: dict) -> date:
    """Bepaal start van de week voor deze datum"""
    # Week start op week_def['start_weekdag'] (0=ma, 6=zo)
    start_weekdag = week_def['start_weekdag']

    # Zoek vorige of huidige start_weekdag
    days_since_start = (datum.weekday() - start_weekdag) % 7
    week_start = datum - timedelta(days=days_since_start)

    return week_start

def main():
    conn = get_connection()
    cursor = conn.cursor()

    print("=" * 70)
    print("DEBUG: UREN PER WEEK - BOB AERTS NOVEMBER 2024")
    print("=" * 70)

    # Haal week definitie op
    cursor.execute("""
        SELECT waarde
        FROM hr_regels
        WHERE naam = 'week_definitie'
            AND is_actief = 1
        LIMIT 1
    """)
    row = cursor.fetchone()
    week_def_str = row['waarde'] if row else 'ma-00:00|zo-23:59'

    print(f"\nWeek Definitie: {week_def_str}")
    week_def = parse_week_definitie(week_def_str)
    print(f"  Start: {['ma','di','wo','do','vr','za','zo'][week_def['start_weekdag']]} {week_def['start_tijd']}")
    print(f"  Eind:  {['ma','di','wo','do','vr','za','zo'][week_def['eind_weekdag']]} {week_def['eind_tijd']}")

    # Haal planning op voor november 2024
    cursor.execute("""
        SELECT datum, shift_code
        FROM planning
        WHERE gebruiker_id = 11
            AND datum BETWEEN '2024-11-01' AND '2024-11-30'
            AND shift_code IS NOT NULL
        ORDER BY datum
    """)

    rows = cursor.fetchall()

    print(f"\n{'='*70}")
    print("PLANNING NOVEMBER 2024 (Bob Aerts)")
    print('='*70)
    print(f"{'Datum':<12} {'Dag':<4} {'Shift':<6} {'Uren':<5} {'Week Start':<12}")
    print('-'*70)

    # Haal shift tijden op
    cursor.execute("""
        SELECT sc.code, sc.start_uur, sc.eind_uur,
               w.telt_als_werkdag
        FROM shift_codes sc
        JOIN werkposten w ON sc.werkpost_id = w.id
        WHERE w.is_actief = 1
    """)

    shift_tijden = {}
    for row in cursor.fetchall():
        shift_tijden[row['code']] = {
            'start_uur': row['start_uur'],
            'eind_uur': row['eind_uur'],
            'telt_als_werkdag': bool(row['telt_als_werkdag'])
        }

    # Voeg speciale codes toe
    cursor.execute("""
        SELECT code, telt_als_werkdag
        FROM speciale_codes
    """)

    for row in cursor.fetchall():
        shift_tijden[row['code']] = {
            'start_uur': None,
            'eind_uur': None,
            'telt_als_werkdag': bool(row['telt_als_werkdag'])
        }

    # Groepeer per week
    weken = {}
    dagen_namen = ['ma', 'di', 'wo', 'do', 'vr', 'za', 'zo']

    for row in rows:
        datum = date.fromisoformat(row['datum'])
        shift_code = row['shift_code']

        # Bereken uren
        uren = 0
        if shift_code in shift_tijden and shift_tijden[shift_code]['telt_als_werkdag']:
            if shift_tijden[shift_code]['start_uur'] and shift_tijden[shift_code]['eind_uur']:
                # Parse tijden
                start = datetime.strptime(shift_tijden[shift_code]['start_uur'], '%H:%M')
                eind = datetime.strptime(shift_tijden[shift_code]['eind_uur'], '%H:%M')

                # Check midnight crossing
                if eind <= start:
                    eind += timedelta(days=1)

                delta = eind - start
                uren = delta.total_seconds() / 3600

        # Bepaal week start
        week_start = get_week_start(datum, week_def)
        week_key = week_start.isoformat()

        if week_key not in weken:
            weken[week_key] = []

        weken[week_key].append({
            'datum': datum,
            'shift_code': shift_code,
            'uren': uren
        })

        dag_naam = dagen_namen[datum.weekday()]
        print(f"{row['datum']:<12} {dag_naam:<4} {shift_code:<6} {uren:>4.1f}u {week_start.isoformat():<12}")

    # Toon per week samenvatting
    print(f"\n{'='*70}")
    print("SAMENVATTING PER WEEK")
    print('='*70)

    for week_key in sorted(weken.keys()):
        week_start = date.fromisoformat(week_key)
        week_eind = week_start + timedelta(days=6)

        shifts = weken[week_key]
        totaal_uren = sum(s['uren'] for s in shifts)
        aantal_dagen = len(shifts)

        status = "OK" if totaal_uren <= 50 else "VIOLATION!"

        print(f"\nWeek {week_key} t/m {week_eind.isoformat()}:")
        print(f"  Aantal shifts: {aantal_dagen}")
        print(f"  Totaal uren:   {totaal_uren:.1f}u")
        print(f"  Status:        [{status}]")

        if totaal_uren > 50:
            print(f"  Overschrijding: {totaal_uren - 50:.1f}u")

    # Scenario specifiek: 5/11 t/m 11/11
    print(f"\n{'='*70}")
    print("SCENARIO: DINSDAG 5/11 T/M MAANDAG 11/11")
    print('='*70)

    scenario_dates = [date(2024, 11, d) for d in range(5, 12)]
    scenario_shifts = []

    for datum in scenario_dates:
        for week_shifts in weken.values():
            for shift in week_shifts:
                if shift['datum'] == datum:
                    scenario_shifts.append(shift)
                    break

    print(f"\nShifts in periode:")
    totaal = 0
    for s in scenario_shifts:
        print(f"  {s['datum']}: {s['shift_code']} ({s['uren']:.1f}u)")
        totaal += s['uren']

    print(f"\nTotaal: {len(scenario_shifts)} shifts = {totaal:.1f}u")
    print(f"User verwachting: {len(scenario_shifts)} x 8u = {len(scenario_shifts) * 8}u")

    if totaal != len(scenario_shifts) * 8:
        print(f"\n[WAARSCHUWING] Uren komen niet overeen!")
        print(f"  Shifts met ongelijke uren gedetecteerd")

    # Check hoe constraint checker deze zou verdelen
    print(f"\n{'='*70}")
    print("CONSTRAINT CHECKER ANALYSE")
    print('='*70)

    # Simuleer constraint checker logica
    from services.constraint_checker import ConstraintChecker, PlanningRegel

    hr_config = {
        'min_rust_uren': 12.0,
        'max_uren_week': 50.0,
        'max_werkdagen_cyclus': 19,
        'max_dagen_tussen_rx': 7,
        'max_werkdagen_reeks': 7,
        'max_weekends_achter_elkaar': 6,
        'week_definitie': week_def_str,
        'weekend_definitie': 'vr-22:00|ma-06:00'
    }

    checker = ConstraintChecker(hr_config, shift_tijden)

    # Converteer naar PlanningRegel objecten
    planning_regels = []
    for week_shifts in weken.values():
        for shift in week_shifts:
            planning_regels.append(PlanningRegel(
                gebruiker_id=11,
                datum=shift['datum'],
                shift_code=shift['shift_code']
            ))

    # Run check
    result = checker.check_max_uren_week(planning_regels, gebruiker_id=11)

    print(f"\nConstraint Checker Result:")
    print(f"  Passed: {result.passed}")
    print(f"  Violations: {len(result.violations)}")

    if result.violations:
        print(f"\nViolations gevonden:")
        for v in result.violations:
            print(f"\n  {v.beschrijving}")
            print(f"  Details: {v.details}")
    else:
        print(f"\n[OK] Geen violations")

    conn.close()

if __name__ == "__main__":
    main()
