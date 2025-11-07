"""
Debug: 12u rust cross-month scenario

Scenario:
- Nacht 31 okt (22:00-06:00) eindigt 1 nov 06:00
- Vroeg 1 nov (06:00-14:00) begint 1 nov 06:00
- Rust = 0 uren
"""
import sys
sys.path.insert(0, '.')

from datetime import date
from database.connection import get_connection
from services.planning_validator_service import PlanningValidator

def main():
    conn = get_connection()
    cursor = conn.cursor()

    # Test gebruiker ID
    TEST_USER_ID = 999

    print("=" * 70)
    print("12U RUST CROSS-MONTH DEBUG")
    print("=" * 70)

    # Setup: insert shifts
    print("\nSetup test data...")
    cursor.execute("DELETE FROM planning WHERE gebruiker_id = ?", (TEST_USER_ID,))

    # Nacht 31 okt
    cursor.execute("""
        INSERT INTO planning (gebruiker_id, datum, shift_code)
        VALUES (?, '2024-10-31', '7301')
    """, (TEST_USER_ID,))

    # Vroeg 1 nov
    cursor.execute("""
        INSERT INTO planning (gebruiker_id, datum, shift_code)
        VALUES (?, '2024-11-01', '7101')
    """, (TEST_USER_ID,))

    conn.commit()

    # Check shift tijden
    print("\nShift tijden:")
    cursor.execute("SELECT code, start_uur, eind_uur FROM shift_codes WHERE code IN ('7301', '7101')")
    for row in cursor.fetchall():
        print(f"  {row['code']}: {row['start_uur']}-{row['eind_uur']}")

    # Test oktober validatie
    print("\n" + "=" * 70)
    print("OKTOBER VALIDATIE")
    print("=" * 70)

    validator_okt = PlanningValidator(
        gebruiker_id=TEST_USER_ID,
        jaar=2024,
        maand=10
    )

    violations_okt = validator_okt.validate_all()
    rust_violations_okt = violations_okt.get('min_rust_12u', [])

    print(f"\nOktober rust violations: {len(rust_violations_okt)}")
    for v in rust_violations_okt:
        print(f"  - {v.beschrijving}")
        print(f"    Details: {v.details}")

    # Check planning data die oktober ziet
    planning_okt = validator_okt._get_planning_data()
    print(f"\nOktober ziet {len(planning_okt)} planning regels:")
    for p in planning_okt:
        print(f"  - {p.datum}: {p.shift_code}")

    # Test november validatie
    print("\n" + "=" * 70)
    print("NOVEMBER VALIDATIE")
    print("=" * 70)

    validator_nov = PlanningValidator(
        gebruiker_id=TEST_USER_ID,
        jaar=2024,
        maand=11
    )

    violations_nov = validator_nov.validate_all()
    rust_violations_nov = violations_nov.get('min_rust_12u', [])

    print(f"\nNovember rust violations: {len(rust_violations_nov)}")
    for v in rust_violations_nov:
        print(f"  - {v.beschrijving}")
        print(f"    Details: {v.details}")

    # Check planning data die november ziet
    planning_nov = validator_nov._get_planning_data()
    print(f"\nNovember ziet {len(planning_nov)} planning regels:")
    for p in planning_nov:
        print(f"  - {p.datum}: {p.shift_code}")

    # Totaal
    total_violations = len(rust_violations_okt) + len(rust_violations_nov)
    print("\n" + "=" * 70)
    print(f"TOTAAL: {total_violations} rust violations")
    print("=" * 70)

    if total_violations == 0:
        print("\n[BUG] Geen violations gedetecteerd!")
        print("Verwachting: 0 uur rust tussen nacht 31/10 en vroeg 1/11")
        print("\nMogelijke oorzaken:")
        print("  1. Buffer loading werkt, maar oktober validatie stopt bij 31 okt")
        print("  2. November validatie ziet 31 okt niet (buffer probleem)")
        print("  3. Check_12u_rust skipt dit scenario om andere reden")
    else:
        print(f"\n[OK] {total_violations} violation(s) correct gedetecteerd")

    # Cleanup
    cursor.execute("DELETE FROM planning WHERE gebruiker_id = ?", (TEST_USER_ID,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
