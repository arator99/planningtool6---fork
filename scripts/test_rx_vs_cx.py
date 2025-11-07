"""
Test RX vs CX verschil in max_dagen_tussen_rx check

Business rule (v0.6.26):
- RX moet elke 8 dagen (max 7 dagen gap tussen RX codes)
- CX is rustdag maar reset NIET de RX counter
"""
import sys
sys.path.insert(0, '.')

from datetime import date
from services.constraint_checker import ConstraintChecker, PlanningRegel

def test_scenario(naam: str, planning: list, verwacht_pass: bool):
    """Helper om scenario te testen"""
    print(f"\n{'='*60}")
    print(f"SCENARIO: {naam}")
    print('='*60)

    # Toon planning
    print("\nPlanning:")
    for p in planning:
        print(f"  {p.datum}: {p.shift_code}")

    # Extract gebruiker_id from first regel
    gebruiker_id = planning[0].gebruiker_id if planning else 1

    # Setup checker
    shift_tijden = {
        'RX': {
            'start_uur': None,
            'eind_uur': None,
            'telt_als_werkdag': False,
            'reset_12u_rust': True,
            'breekt_werk_reeks': True
        },
        'CX': {
            'start_uur': None,
            'eind_uur': None,
            'telt_als_werkdag': False,
            'reset_12u_rust': True,
            'breekt_werk_reeks': True
        },
        '1101': {
            'start_uur': '06:00',
            'eind_uur': '14:00',
            'telt_als_werkdag': True,
            'reset_12u_rust': False,
            'breekt_werk_reeks': False
        }
    }

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

    # Run check
    result = checker.check_max_dagen_tussen_rx(planning, gebruiker_id=gebruiker_id)

    # Analyse
    print(f"\nResultaat:")
    print(f"  Passed: {result.passed}")
    print(f"  Violations: {len(result.violations)}")

    if result.violations:
        for v in result.violations:
            print(f"\n  {v.beschrijving}")
            print(f"  Details: {v.details}")

    # Verificatie
    if result.passed == verwacht_pass:
        print(f"\n[OK] Test geslaagd (verwacht passed={verwacht_pass})")
        return True
    else:
        print(f"\n[FAIL] Test gefaald (verwacht passed={verwacht_pass}, kreeg passed={result.passed})")
        return False


def main():
    print("="*60)
    print("TEST: RX vs CX - Max Dagen Tussen RX")
    print("="*60)

    alle_tests_ok = True

    # TEST 1: RX elke 7 dagen (6 dagen gap) - OK
    test1 = [
        PlanningRegel(1, date(2024, 11, 1), 'RX'),
        PlanningRegel(1, date(2024, 11, 2), '1101'),
        PlanningRegel(1, date(2024, 11, 3), '1101'),
        PlanningRegel(1, date(2024, 11, 4), '1101'),
        PlanningRegel(1, date(2024, 11, 5), '1101'),
        PlanningRegel(1, date(2024, 11, 6), '1101'),
        PlanningRegel(1, date(2024, 11, 7), '1101'),
        PlanningRegel(1, date(2024, 11, 8), 'RX'),  # 6 dagen gap
    ]
    if not test_scenario("RX elke 8 dagen (6 gap) - MOET OK ZIJN", test1, verwacht_pass=True):
        alle_tests_ok = False

    # TEST 2: RX op dag 1, CX op dag 4, RX op dag 9 (7 dagen gap) - OK
    test2 = [
        PlanningRegel(1, date(2024, 11, 1), 'RX'),
        PlanningRegel(1, date(2024, 11, 2), '1101'),
        PlanningRegel(1, date(2024, 11, 3), '1101'),
        PlanningRegel(1, date(2024, 11, 4), 'CX'),     # CX reset NIET RX counter
        PlanningRegel(1, date(2024, 11, 5), '1101'),
        PlanningRegel(1, date(2024, 11, 6), '1101'),
        PlanningRegel(1, date(2024, 11, 7), '1101'),
        PlanningRegel(1, date(2024, 11, 8), '1101'),
        PlanningRegel(1, date(2024, 11, 9), 'RX'),     # 7 dagen gap (exact limiet)
    ]
    if not test_scenario("RX met CX tussen (7 gap) - MOET OK ZIJN", test2, verwacht_pass=True):
        alle_tests_ok = False

    # TEST 3: RX op dag 1, CX op dag 4, RX op dag 10 (8 dagen gap) - VIOLATION
    test3 = [
        PlanningRegel(1, date(2024, 11, 1), 'RX'),
        PlanningRegel(1, date(2024, 11, 2), '1101'),
        PlanningRegel(1, date(2024, 11, 3), '1101'),
        PlanningRegel(1, date(2024, 11, 4), 'CX'),     # CX reset NIET RX counter
        PlanningRegel(1, date(2024, 11, 5), '1101'),
        PlanningRegel(1, date(2024, 11, 6), '1101'),
        PlanningRegel(1, date(2024, 11, 7), '1101'),
        PlanningRegel(1, date(2024, 11, 8), '1101'),
        PlanningRegel(1, date(2024, 11, 9), '1101'),
        PlanningRegel(1, date(2024, 11, 10), 'RX'),    # 8 dagen gap - TE LANG!
    ]
    if not test_scenario("RX met CX tussen (8 gap) - MOET VIOLATION ZIJN", test3, verwacht_pass=False):
        alle_tests_ok = False

    # TEST 4: Alleen CX, geen RX - Moet OK zijn (geen RX paren om te checken)
    test4 = [
        PlanningRegel(1, date(2024, 11, 1), 'CX'),
        PlanningRegel(1, date(2024, 11, 2), '1101'),
        PlanningRegel(1, date(2024, 11, 3), '1101'),
        PlanningRegel(1, date(2024, 11, 4), 'CX'),
        PlanningRegel(1, date(2024, 11, 5), '1101'),
    ]
    if not test_scenario("Alleen CX, geen RX - MOET OK ZIJN", test4, verwacht_pass=True):
        alle_tests_ok = False

    # TEST 5: November 2024 Bob Aerts scenario (echt data)
    # RX op 4/11, CX op 11/11, maar gap tussen RX te groot
    test5 = [
        PlanningRegel(11, date(2024, 11, 4), 'RX'),
        PlanningRegel(11, date(2024, 11, 5), '1101'),
        PlanningRegel(11, date(2024, 11, 7), '1101'),
        PlanningRegel(11, date(2024, 11, 8), '1101'),
        PlanningRegel(11, date(2024, 11, 9), '1101'),
        PlanningRegel(11, date(2024, 11, 10), '1101'),
        PlanningRegel(11, date(2024, 11, 11), 'CX'),    # CX telt niet voor RX gap
        PlanningRegel(11, date(2024, 11, 12), '1101'),
        PlanningRegel(11, date(2024, 11, 13), '1101'),
        PlanningRegel(11, date(2024, 11, 14), '1101'),
        PlanningRegel(11, date(2024, 11, 15), '1101'),
        PlanningRegel(11, date(2024, 11, 16), 'RX'),    # 11 dagen gap!
    ]
    if not test_scenario("Bob Aerts november (11 gap met CX) - MOET VIOLATION ZIJN", test5, verwacht_pass=False):
        alle_tests_ok = False

    # Totaal resultaat
    print("\n" + "="*60)
    if alle_tests_ok:
        print("[SUCCESS] Alle tests geslaagd!")
        print("\nBusiness rule correct geimplementeerd:")
        print("- RX moet elke 8 dagen (max 7 dagen gap)")
        print("- CX reset NIET de RX counter")
        print("- CX is wel rustdag voor andere regels")
    else:
        print("[FAILURE] Sommige tests gefaald!")
    print("="*60)


if __name__ == "__main__":
    main()
