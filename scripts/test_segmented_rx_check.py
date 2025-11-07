"""
Test: Segmented RX Check (BUG-005)

Scenario:
- Gebruiker vult alleen weekends in (za/zo)
- Werkdagen blijven leeg
- RX check moet NIET triggeren (partial planning)
"""
import sys
sys.path.insert(0, '.')

from datetime import date
from database.connection import get_connection
from services.planning_validator_service import PlanningValidator
import uuid

TEST_USER_ID = 999

def main():
    conn = get_connection()
    cursor = conn.cursor()

    print("=" * 70)
    print("SEGMENTED RX CHECK TEST (BUG-005)")
    print("=" * 70)

    # Setup test gebruiker
    cursor.execute("SELECT id FROM gebruikers WHERE id = ?", (TEST_USER_ID,))
    if not cursor.fetchone():
        test_uuid = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO gebruikers (id, gebruiker_uuid, gebruikersnaam, wachtwoord_hash, volledige_naam, rol)
            VALUES (?, ?, 'testuser', 'dummy', 'Test User', 'teamlid')
        """, (TEST_USER_ID, test_uuid))
        conn.commit()
        print(f"Test gebruiker {TEST_USER_ID} aangemaakt")

    # Cleanup oude data
    cursor.execute("DELETE FROM planning WHERE gebruiker_id = ?", (TEST_USER_ID,))
    conn.commit()

    # SCENARIO 1: Alleen weekends invullen (za/zo)
    print("\n" + "=" * 70)
    print("SCENARIO 1: Alleen weekends (za/zo) - GEEN RX")
    print("=" * 70)

    # November 2024: alleen za/zo invullen
    weekends = [
        (date(2024, 11, 2), '7101'),   # za
        (date(2024, 11, 3), '7101'),   # zo
        # ma-vr LEEG (5 dagen)
        (date(2024, 11, 9), '7101'),   # za
        (date(2024, 11, 10), '7101'),  # zo
        # ma-vr LEEG (5 dagen)
        (date(2024, 11, 16), '7101'),  # za
        (date(2024, 11, 17), '7101'),  # zo
        # ma-vr LEEG (5 dagen)
        (date(2024, 11, 23), '7101'),  # za
        (date(2024, 11, 24), '7101'),  # zo
    ]

    for datum, code in weekends:
        cursor.execute("""
            INSERT INTO planning (gebruiker_id, datum, shift_code)
            VALUES (?, ?, ?)
        """, (TEST_USER_ID, datum.isoformat(), code))
    conn.commit()

    print(f"\n{len(weekends)} weekend shifts ingepland (za/zo)")
    print("Werkdagen ma-vr: LEEG")

    # Valideer
    validator = PlanningValidator(gebruiker_id=TEST_USER_ID, jaar=2024, maand=11)
    violations = validator.validate_all()
    rx_violations = violations.get('max_dagen_tussen_rx', [])

    print(f"\nRX violations: {len(rx_violations)}")
    if rx_violations:
        print("\n[FAIL] Valse RX violations gedetecteerd:")
        for v in rx_violations:
            print(f"  - {v.beschrijving}")
    else:
        print("\n[PASS] Geen RX violations - segmented check werkt!")

    # SCENARIO 2: Complete week met RX
    print("\n" + "=" * 70)
    print("SCENARIO 2: Complete planning met RX gaps")
    print("=" * 70)

    cursor.execute("DELETE FROM planning WHERE gebruiker_id = ?", (TEST_USER_ID,))
    conn.commit()

    # Complete week: RX op 7 nov, shifts 8-14 nov, RX op 15 nov
    complete_planning = [
        (date(2024, 11, 7), 'RX'),
        (date(2024, 11, 8), '7101'),
        (date(2024, 11, 9), '7101'),
        (date(2024, 11, 10), '7101'),
        (date(2024, 11, 11), '7101'),
        (date(2024, 11, 12), '7101'),
        (date(2024, 11, 13), '7101'),
        (date(2024, 11, 14), '7101'),
        (date(2024, 11, 15), 'RX'),
    ]

    for datum, code in complete_planning:
        cursor.execute("""
            INSERT INTO planning (gebruiker_id, datum, shift_code)
            VALUES (?, ?, ?)
        """, (TEST_USER_ID, datum.isoformat(), code))
    conn.commit()

    print(f"\n{len(complete_planning)} shifts ingepland (RX + 7 shifts + RX)")

    # Valideer
    validator = PlanningValidator(gebruiker_id=TEST_USER_ID, jaar=2024, maand=11)
    violations = validator.validate_all()
    rx_violations = violations.get('max_dagen_tussen_rx', [])

    print(f"\nRX violations: {len(rx_violations)}")
    if rx_violations:
        print("\n[FAIL] Onverwachte violations in complete planning:")
        for v in rx_violations:
            print(f"  - {v.beschrijving}")
    else:
        print("\n[PASS] Geen violations - 7 dagen tussen RX is OK")

    # SCENARIO 3: Gap > 7 dagen in segment
    print("\n" + "=" * 70)
    print("SCENARIO 3: RX gap > 7 dagen BINNEN segment")
    print("=" * 70)

    cursor.execute("DELETE FROM planning WHERE gebruiker_id = ?", (TEST_USER_ID,))
    conn.commit()

    # RX, dan 10 dagen shifts (> 7 max)
    gap_planning = [
        (date(2024, 11, 1), 'RX'),
        (date(2024, 11, 2), '7101'),
        (date(2024, 11, 3), '7101'),
        (date(2024, 11, 4), '7101'),
        (date(2024, 11, 5), '7101'),
        (date(2024, 11, 6), '7101'),
        (date(2024, 11, 7), '7101'),
        (date(2024, 11, 8), '7101'),
        (date(2024, 11, 9), '7101'),
        (date(2024, 11, 10), '7101'),
        (date(2024, 11, 11), '7101'),  # 10 dagen na RX
    ]

    for datum, code in gap_planning:
        cursor.execute("""
            INSERT INTO planning (gebruiker_id, datum, shift_code)
            VALUES (?, ?, ?)
        """, (TEST_USER_ID, datum.isoformat(), code))
    conn.commit()

    print(f"\n{len(gap_planning)} shifts (RX + 10 dagen zonder nieuwe RX)")

    # Valideer
    validator = PlanningValidator(gebruiker_id=TEST_USER_ID, jaar=2024, maand=11)
    violations = validator.validate_all()
    rx_violations = violations.get('max_dagen_tussen_rx', [])

    print(f"\nRX violations: {len(rx_violations)}")
    if rx_violations:
        print("\n[PASS] Correct: RX gap > 7 dagen gedetecteerd")
        for v in rx_violations:
            print(f"  - {v.beschrijving}")
    else:
        print("\n[FAIL] RX gap > 7 dagen niet gedetecteerd!")

    # Cleanup
    cursor.execute("DELETE FROM planning WHERE gebruiker_id = ?", (TEST_USER_ID,))
    conn.commit()

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    conn.close()


if __name__ == "__main__":
    main()
