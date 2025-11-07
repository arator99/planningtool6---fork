"""
Test: Datum Gap Segmentation (BUG-005b)

Scenario uit user test:
- RX op 27/09/2024
- Alleen za/zo shifts tot 20/10
- RX op 21/10
- Ma-vr NIET ingevuld (geen records in DB)
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
    print("DATUM GAP SEGMENTATION TEST (BUG-005b)")
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

    # Cleanup
    cursor.execute("DELETE FROM planning WHERE gebruiker_id = ?", (TEST_USER_ID,))
    conn.commit()

    # USER SCENARIO: RX 27/09, alleen weekends t/m 20/10, RX 21/10
    print("\nUser scenario: RX 27/09, weekends only, RX 21/10")
    print("Ma-vr NIET ingevuld (datum gaps tussen weekends)")

    # September weekends + RX
    shifts = [
        (date(2024, 9, 27), 'RX'),   # vr
        (date(2024, 9, 28), '7101'),  # za
        (date(2024, 9, 29), '7101'),  # zo
        # ma 30/09 - vr 04/10: LEEG (5 dagen)
    ]

    # Oktober weekends
    oktober_weekends = [
        (5, 6),   # za/zo
        (12, 13),
        (19, 20),
    ]

    for za, zo in oktober_weekends:
        shifts.append((date(2024, 10, za), '7101'))
        shifts.append((date(2024, 10, zo), '7101'))
        # ma-vr tussen weekends: LEEG

    # RX op 21/10
    shifts.append((date(2024, 10, 21), 'RX'))

    # Insert shifts
    for datum, code in shifts:
        cursor.execute("""
            INSERT INTO planning (gebruiker_id, datum, shift_code)
            VALUES (?, ?, ?)
        """, (TEST_USER_ID, datum.isoformat(), code))
    conn.commit()

    print(f"\n{len(shifts)} shifts ingepland:")
    for datum, code in shifts:
        print(f"  {datum.strftime('%a %d/%m')}: {code}")

    # Valideer september
    print("\n" + "=" * 70)
    print("SEPTEMBER VALIDATIE")
    print("=" * 70)

    validator_sep = PlanningValidator(gebruiker_id=TEST_USER_ID, jaar=2024, maand=9)
    violations_sep = validator_sep.validate_all()

    rx_violations_sep = violations_sep.get('max_dagen_tussen_rx', [])
    reeks_violations_sep = violations_sep.get('max_werkdagen_reeks', [])

    print(f"\nRX violations: {len(rx_violations_sep)}")
    if rx_violations_sep:
        print("[FAIL] Valse RX violations in september:")
        for v in rx_violations_sep:
            print(f"  - {v.beschrijving}")
    else:
        print("[PASS] Geen RX violations in september")

    print(f"\nWerkdagen reeks violations: {len(reeks_violations_sep)}")
    if reeks_violations_sep:
        print("[FAIL] Valse werkdagen violations in september:")
        for v in reeks_violations_sep:
            print(f"  - {v.beschrijving}")
    else:
        print("[PASS] Geen werkdagen violations in september")

    # Valideer oktober
    print("\n" + "=" * 70)
    print("OKTOBER VALIDATIE")
    print("=" * 70)

    validator_okt = PlanningValidator(gebruiker_id=TEST_USER_ID, jaar=2024, maand=10)
    violations_okt = validator_okt.validate_all()

    rx_violations_okt = violations_okt.get('max_dagen_tussen_rx', [])
    reeks_violations_okt = violations_okt.get('max_werkdagen_reeks', [])

    print(f"\nRX violations: {len(rx_violations_okt)}")
    if rx_violations_okt:
        print("[FAIL] Valse RX violations in oktober:")
        for v in rx_violations_okt:
            print(f"  - {v.beschrijving}")
    else:
        print("[PASS] Geen RX violations in oktober")

    print(f"\nWerkdagen reeks violations: {len(reeks_violations_okt)}")
    if reeks_violations_okt:
        print("[FAIL] Valse werkdagen violations in oktober:")
        for v in reeks_violations_okt:
            print(f"  - {v.beschrijving}")
    else:
        print("[PASS] Geen werkdagen violations in oktober")

    # Analyse
    print("\n" + "=" * 70)
    print("SEGMENT ANALYSE")
    print("=" * 70)

    from services.constraint_checker import ConstraintChecker

    # Haal HR config + shift tijden
    cursor.execute("SELECT naam, waarde FROM hr_regels WHERE is_actief = 1")
    hr_config = {row['naam']: row['waarde'] for row in cursor.fetchall()}
    hr_config['min_rust_uren'] = 12.0
    hr_config['max_uren_week'] = 50.0
    hr_config['max_dagen_tussen_rx'] = 7

    cursor.execute("SELECT code FROM shift_codes LIMIT 1")
    shift_tijden = {row['code']: {'start_uur': '06:00', 'eind_uur': '14:00',
                                    'telt_als_werkdag': True, 'reset_12u_rust': False,
                                    'breekt_werk_reeks': False}
                    for row in cursor.fetchall()}
    shift_tijden['RX'] = {'start_uur': None, 'eind_uur': None,
                          'telt_als_werkdag': False, 'reset_12u_rust': True,
                          'breekt_werk_reeks': True}

    checker = ConstraintChecker(hr_config, shift_tijden)

    # Get planning data
    planning = validator_okt._get_planning_data()
    print(f"\nOktober planning data: {len(planning)} regels")

    # Test segmentatie
    segments = checker._segment_planning_op_lege_cellen(planning)
    print(f"\nAantal segmenten: {len(segments)}")
    for i, seg in enumerate(segments, 1):
        if seg:
            start = seg[0].datum
            eind = seg[-1].datum
            codes = [p.shift_code for p in seg]
            print(f"  Segment {i}: {start} - {eind} ({len(seg)} dagen)")
            print(f"    Codes: {', '.join(codes)}")

    # Cleanup
    cursor.execute("DELETE FROM planning WHERE gebruiker_id = ?", (TEST_USER_ID,))
    conn.commit()
    conn.close()

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
