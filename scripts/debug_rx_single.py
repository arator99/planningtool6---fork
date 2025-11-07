"""
Debug: RX gap detection met maar 1 RX in maand

Scenario gebruiker:
- 3/11: RX
- 4/11 t/m 12/11: CX (9 dagen)
- Geen tweede RX

Probleem: check_max_dagen_tussen_rx kijkt alleen naar gaps TUSSEN twee RX codes.
Als er maar 1 RX is, zijn er geen "paren" om te checken!
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
    print("RX GAP PROBLEEM: MAAR 1 RX IN MAAND")
    print("=" * 70)

    # Check actuele data
    cursor.execute("""
        SELECT datum, shift_code
        FROM planning
        WHERE gebruiker_id = 11
            AND strftime('%Y-%m', datum) = '2024-11'
            AND (shift_code = 'RX' OR shift_code = 'CX')
        ORDER BY datum
    """)

    rows = cursor.fetchall()

    print("\nRX en CX codes in november 2024:")
    rx_count = 0
    cx_count = 0
    for row in rows:
        code = row['shift_code']
        print(f"  {row['datum']}: {code}")
        if code == 'RX':
            rx_count += 1
        elif code == 'CX':
            cx_count += 1

    print(f"\nTotaal: {rx_count} RX, {cx_count} CX")

    # Haal shift tijden op
    cursor.execute("""
        SELECT code, telt_als_werkdag, reset_12u_rust, breekt_werk_reeks
        FROM speciale_codes
    """)

    shift_tijden = {}
    for row in cursor.fetchall():
        shift_tijden[row['code']] = {
            'start_uur': None,
            'eind_uur': None,
            'telt_als_werkdag': bool(row['telt_als_werkdag']),
            'reset_12u_rust': bool(row['reset_12u_rust']),
            'breekt_werk_reeks': bool(row['breekt_werk_reeks'])
        }

    # Setup checker
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

    # Haal alle planning
    cursor.execute("""
        SELECT datum, shift_code
        FROM planning
        WHERE gebruiker_id = 11
            AND strftime('%Y-%m', datum) = '2024-11'
            AND shift_code IS NOT NULL
        ORDER BY datum
    """)

    planning_regels = []
    for row in cursor.fetchall():
        planning_regels.append(PlanningRegel(
            gebruiker_id=11,
            datum=date.fromisoformat(row['datum']),
            shift_code=row['shift_code']
        ))

    # Run check
    print("\n" + "=" * 70)
    print("CONSTRAINT CHECKER RESULTAAT")
    print("=" * 70)

    result = checker.check_max_dagen_tussen_rx(planning_regels, gebruiker_id=11)

    print(f"\nPassed: {result.passed}")
    print(f"Violations: {len(result.violations)}")
    print(f"Metadata: {result.metadata}")

    if result.violations:
        print("\nViolations:")
        for v in result.violations:
            print(f"  - {v.beschrijving}")
            print(f"    Details: {v.details}")
    else:
        print("\n[PROBLEEM] Geen violations gevonden!")
        print("\nANALYSE:")
        print("  - Als er maar 1 RX is in de maand, checkt de constraint checker geen gap")
        print("  - De loop: 'for i in range(len(rx_dagen) - 1)' is leeg als len == 1")
        print("  - Er worden alleen gaps TUSSEN twee RX codes gecheckt")
        print("  - Er wordt NIET gecheckt of de laatste RX te lang geleden is")

    # Extra analyse
    print("\n" + "=" * 70)
    print("PROBLEEM ANALYSE")
    print("=" * 70)

    # Vind alle RX codes
    rx_codes = [p for p in planning_regels if p.shift_code == 'RX']

    print(f"\nAantal RX codes gevonden: {len(rx_codes)}")
    for rx in rx_codes:
        print(f"  - {rx.datum}: RX")

    if len(rx_codes) <= 1:
        print("\n[ROOT CAUSE] Slechts 1 RX gevonden!")
        print("De check_max_dagen_tussen_rx method heeft deze logica:")
        print("  for i in range(len(rx_dagen) - 1):")
        print("      rx1 = rx_dagen[i]")
        print("      rx2 = rx_dagen[i + 1]")
        print("      # Check gap tussen rx1 en rx2")
        print()
        print("Als len(rx_dagen) == 1:")
        print("  range(len(rx_dagen) - 1) = range(0) = leeg")
        print("  Loop wordt niet uitgevoerd")
        print("  Geen violations!")
        print()
        print("OPLOSSING NODIG:")
        print("  - Check ook gap vanaf laatste RX tot 'nu' of einde planning periode")
        print("  - Of: check dat er minimaal 1 RX per X dagen moet zijn")

    conn.close()

if __name__ == "__main__":
    main()
