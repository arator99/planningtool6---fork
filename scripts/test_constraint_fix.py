"""
Test script om de constraint checker fix te verifiëren
Test specifiek: nacht (22:00-06:00) gevolgd door vroeg (06:00-14:00)
"""
import sys
sys.path.insert(0, '.')

from datetime import date
from database.connection import get_connection
from services.constraint_checker import ConstraintChecker, PlanningRegel

def main():
    conn = get_connection()
    cursor = conn.cursor()

    # Haal shift tijden op voor Bob Aerts (ID: 11) in november 2024
    print("=== TEST: Bob Aerts - November 2024 ===\n")

    cursor.execute("""
        SELECT p.datum, p.shift_code, sc.start_uur, sc.eind_uur, sc.shift_type
        FROM planning p
        LEFT JOIN shift_codes sc ON p.shift_code = sc.code
        WHERE p.gebruiker_id = 11
            AND strftime('%Y-%m', p.datum) = '2024-11'
            AND p.datum BETWEEN '2024-11-06' AND '2024-11-07'
        ORDER BY p.datum
    """)

    rows = cursor.fetchall()
    for row in rows:
        shift_info = ""
        if row['start_uur']:
            shift_info = f" ({row['start_uur']}-{row['eind_uur']})"
        print(f"{row['datum']}  {row['shift_code']}{shift_info}")

    # Haal alle shift tijden op voor constraint checker
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

    # Haal planning data voor Bob Aerts in november
    cursor.execute("""
        SELECT datum, shift_code, gebruiker_id
        FROM planning
        WHERE gebruiker_id = 11
            AND strftime('%Y-%m', datum) = '2024-11'
        ORDER BY datum
    """)

    planning_regels = []
    for row in cursor.fetchall():
        planning_regels.append(PlanningRegel(
            gebruiker_id=row['gebruiker_id'],
            datum=date.fromisoformat(row['datum']),
            shift_code=row['shift_code'],
            is_goedgekeurd_verlof=False,
            is_feestdag=False
        ))

    # Run 12u rust check
    print("\n=== CONSTRAINT CHECK RESULTAAT ===\n")
    result = checker.check_12u_rust(planning_regels, gebruiker_id=11)

    if result.passed:
        print("[OK] Geen violations gevonden")
    else:
        print(f"[FAIL] {len(result.violations)} violation(s) gevonden:\n")
        for v in result.violations:
            print(f"  {v.beschrijving}")
            print(f"  Details: {v.details}\n")

    # Test specifiek de problematische dagen
    print("=== HANDMATIGE TEST: 6-7 november ===\n")
    p1 = PlanningRegel(11, date(2024, 11, 6), "1301", False, False)
    p2 = PlanningRegel(11, date(2024, 11, 7), "1101", False, False)

    rust = checker._bereken_rust_tussen_shifts(
        p1.datum, "22:00", "06:00",  # Nacht: 22:00-06:00
        p2.datum, "06:00"             # Vroeg: 06:00-14:00
    )

    print(f"Nacht shift: 2024-11-06 22:00 eindigt 2024-11-07 06:00")
    print(f"Vroeg shift: 2024-11-07 06:00 begint 2024-11-07 06:00")
    print(f"Rust tussen shifts: {rust:.1f} uur")

    if rust < 12:
        print("[FAIL] VIOLATION: Te weinig rust!")
    else:
        print("[OK] Voldoende rust")

    conn.close()

if __name__ == "__main__":
    main()
