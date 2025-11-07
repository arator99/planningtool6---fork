"""
Debug script: Gedetailleerde analyse van uren per week check
Volgt exact de constraint checker logica met overlap detection
"""
import sys
sys.path.insert(0, '.')

from datetime import date
from database.connection import get_connection
from services.constraint_checker import ConstraintChecker, PlanningRegel

def main():
    conn = get_connection()
    cursor = conn.cursor()

    print("=" * 70)
    print("GEDETAILLEERDE ANALYSE: UREN PER WEEK - BOB AERTS NOV 2024")
    print("=" * 70)

    # Haal planning op
    cursor.execute("""
        SELECT datum, shift_code
        FROM planning
        WHERE gebruiker_id = 11
            AND datum BETWEEN '2024-11-01' AND '2024-11-30'
            AND shift_code IS NOT NULL
        ORDER BY datum
    """)

    rows = cursor.fetchall()

    print("\nPlanning november 2024:")
    for row in rows:
        print(f"  {row['datum']}: {row['shift_code']}")

    # Haal shift tijden op
    cursor.execute("""
        SELECT sc.code, sc.start_uur, sc.eind_uur,
               w.telt_als_werkdag, w.reset_12u_rust, w.breekt_werk_reeks
        FROM shift_codes sc
        JOIN werkposten w ON sc.werkpost_id = w.id
        WHERE w.is_actief = 1
    """)

    shift_tijden = {}
    for row in cursor.fetchall():
        shift_tijden[row['code']] = {
            'start_uur': row['start_uur'],
            'eind_uur': row['eind_uur'],
            'telt_als_werkdag': bool(row['telt_als_werkdag']),
            'reset_12u_rust': bool(row['reset_12u_rust']),
            'breekt_werk_reeks': bool(row['breekt_werk_reeks'])
        }

    # Voeg speciale codes toe
    cursor.execute("""
        SELECT code, telt_als_werkdag, reset_12u_rust, breekt_werk_reeks
        FROM speciale_codes
    """)

    for row in cursor.fetchall():
        shift_tijden[row['code']] = {
            'start_uur': None,
            'eind_uur': None,
            'telt_als_werkdag': bool(row['telt_als_werkdag']),
            'reset_12u_rust': bool(row['reset_12u_rust']),
            'breekt_werk_reeks': bool(row['breekt_werk_reeks'])
        }

    # Setup constraint checker
    hr_config = {
        'min_rust_uren': 12.0,
        'max_uren_week': 50.0,
        'max_werkdagen_cyclus': 19,
        'max_dagen_tussen_rx': 7,
        'max_werkdagen_reeks': 7,
        'max_weekends_achter_elkaar': 6,
        'week_definitie': 'ma-00:00|zo-23:59',
        'weekend_definitie': 'vr-22:00|ma-06:00'
    }

    checker = ConstraintChecker(hr_config, shift_tijden)

    # Converteer naar PlanningRegel objecten
    planning_regels = []
    for row in rows:
        planning_regels.append(PlanningRegel(
            gebruiker_id=11,
            datum=date.fromisoformat(row['datum']),
            shift_code=row['shift_code']
        ))

    # Run check
    print("\n" + "=" * 70)
    print("CONSTRAINT CHECKER RESULTAAT")
    print("=" * 70)

    result = checker.check_max_uren_week(planning_regels, gebruiker_id=11)

    print(f"\nPassed: {result.passed}")
    print(f"Violations: {len(result.violations)}")
    print(f"Metadata: {result.metadata}")

    if result.violations:
        print("\n" + "=" * 70)
        print("VIOLATIONS GEVONDEN:")
        print("=" * 70)
        for i, v in enumerate(result.violations, 1):
            print(f"\nViolation #{i}:")
            print(f"  Beschrijving: {v.beschrijving}")
            print(f"  Datum range: {v.datum_range}")
            print(f"  Details:")
            for key, value in v.details.items():
                print(f"    {key}: {value}")
            print(f"  Affected shifts: {len(v.affected_shifts)}")
            for gebruiker_id, datum in v.affected_shifts:
                print(f"    - {datum}")
    else:
        print("\n[INFO] Geen violations gevonden")
        print("\nDit betekent dat volgens de constraint checker logica:")
        print("- Elke kalenderweek (ma-zo) heeft <= 50u")
        print("- Shifts worden correct verdeeld over weken")

    # Extra analyse: toon welke shifts in welke week vallen
    print("\n" + "=" * 70)
    print("WEEK VERDELING (zoals constraint checker ziet)")
    print("=" * 70)

    # Gebruik interne methode om weken te genereren
    min_datum = min(p.datum for p in planning_regels)
    max_datum = max(p.datum for p in planning_regels)

    start_dag, start_uur, eind_dag, eind_uur = checker._parse_periode_definitie('ma-00:00|zo-23:59')
    weken = checker._generate_weken(min_datum, max_datum, start_dag, start_uur, eind_dag, eind_uur)

    for week_start, week_eind, week_nr in weken:
        shifts_in_week = []

        for p in planning_regels:
            if not p.shift_code:
                continue

            # Check overlap
            if checker._shift_overlapt_week(p.datum, p.shift_code, week_start, week_eind):
                duur = checker._bereken_shift_duur(p.shift_code)
                shifts_in_week.append((p.datum, p.shift_code, duur))

        totaal_uren = sum(duur for _, _, duur in shifts_in_week if duur)

        print(f"\nWeek {week_start.date()} t/m {week_eind.date()} (week {week_nr}):")
        print(f"  Shifts: {len(shifts_in_week)}")
        print(f"  Totaal: {totaal_uren:.1f}u")

        if shifts_in_week:
            for datum, code, uren in shifts_in_week:
                print(f"    {datum}: {code} ({uren:.1f}u)")

    conn.close()

if __name__ == "__main__":
    main()
