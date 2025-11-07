"""
Debug: RX gap over maandgrens

Scenario:
- RX op 26 oktober 2024
- RX op 6 november 2024
- Gap: 11 dagen (> 7 max)

Probleem: Validator laadt alleen data voor huidige maand
- Oktober validatie: ziet geen RX in november
- November validatie: ziet geen RX in oktober
- Gap wordt gemist!
"""
import sys
sys.path.insert(0, '.')

from datetime import date
from database.connection import get_connection
from services.planning_validator_service import PlanningValidator

def main():
    conn = get_connection()
    cursor = conn.cursor()

    print("=" * 70)
    print("RX GAP OVER MAANDGRENS: 26 OKT - 6 NOV")
    print("=" * 70)

    # Check data
    cursor.execute("""
        SELECT datum, shift_code
        FROM planning
        WHERE gebruiker_id = 11
            AND ((strftime('%Y-%m', datum) = '2024-10' AND datum >= '2024-10-26')
                 OR (strftime('%Y-%m', datum) = '2024-11' AND datum <= '2024-11-06'))
            AND shift_code IN ('RX', 'CX')
        ORDER BY datum
    """)

    rows = cursor.fetchall()

    print("\nRX/CX codes rond maandgrens:")
    for row in rows:
        print(f"  {row['datum']}: {row['shift_code']}")

    # Test oktober validatie
    print("\n" + "=" * 70)
    print("TEST 1: OKTOBER VALIDATIE")
    print("=" * 70)

    validator_okt = PlanningValidator(
        gebruiker_id=11,
        jaar=2024,
        maand=10
    )

    violations_okt = validator_okt.validate_all()
    rx_violations_okt = violations_okt.get('max_dagen_tussen_rx', [])

    print(f"\nOktober violations: {len(rx_violations_okt)}")
    if rx_violations_okt:
        for v in rx_violations_okt:
            print(f"  - {v.beschrijving}")
    else:
        print("  [PROBLEEM] Geen RX gap violations in oktober")

    # Check welke data oktober ziet
    planning_okt = validator_okt._get_planning_data()
    rx_in_okt = [p for p in planning_okt if p.shift_code == 'RX']
    print(f"\nRX codes die oktober validator ziet: {len(rx_in_okt)}")
    for rx in rx_in_okt:
        print(f"  - {rx.datum}: RX")

    # Test november validatie
    print("\n" + "=" * 70)
    print("TEST 2: NOVEMBER VALIDATIE")
    print("=" * 70)

    validator_nov = PlanningValidator(
        gebruiker_id=11,
        jaar=2024,
        maand=11
    )

    violations_nov = validator_nov.validate_all()
    rx_violations_nov = violations_nov.get('max_dagen_tussen_rx', [])

    print(f"\nNovember violations: {len(rx_violations_nov)}")
    if rx_violations_nov:
        for v in rx_violations_nov:
            print(f"  - {v.beschrijving}")
    else:
        print("  [PROBLEEM] Geen RX gap violations in november")

    # Check welke data november ziet
    planning_nov = validator_nov._get_planning_data()
    rx_in_nov = [p for p in planning_nov if p.shift_code == 'RX']
    print(f"\nRX codes die november validator ziet: {len(rx_in_nov)}")
    for rx in rx_in_nov:
        print(f"  - {rx.datum}: RX")

    print("\n" + "=" * 70)
    print("ROOT CAUSE ANALYSE")
    print("=" * 70)
    print("\nProbleem:")
    print("  - PlanningValidator laadt alleen data voor huidige maand")
    print("  - Query: strftime('%Y-%m', datum) = '2024-10' (of '2024-11')")
    print("  - Oktober validator ziet RX op 26/10, maar NIET RX op 6/11")
    print("  - November validator ziet RX op 6/11, maar NIET RX op 26/10")
    print("  - Beide validators zien slechts 1 RX → geen gap check!")
    print()
    print("Werkelijke gap: 26 okt → 6 nov = 11 dagen (> 7 max)")
    print()
    print("Oplossing nodig:")
    print("  - Validator moet buffer laden: vorige maand + huidige + volgende maand")
    print("  - Of: check moet ook RX uit aangrenzende maanden meenemen")

    conn.close()

if __name__ == "__main__":
    main()
