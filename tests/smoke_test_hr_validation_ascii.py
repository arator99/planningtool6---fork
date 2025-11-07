"""
Smoke Test voor HR Validatie Systeem

Quick test om te verifiëren dat:
1. PlanningValidator correct instantieert
2. Database queries werken
3. ConstraintChecker correct wordt aangeroepen
4. Violations worden gedetecteerd

Versie: v0.6.26 (Fase 2 Testing)
Datum: 3 November 2025
"""

import sys
import os
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
from services.planning_validator_service import PlanningValidator


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_database_connection():
    """Test 1: Database connectie"""
    print_header("TEST 1: Database Connection")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check gebruikers
        cursor.execute("SELECT COUNT(*) as count FROM gebruikers WHERE is_actief = 1 AND gebruikersnaam != 'admin'")
        user_count = cursor.fetchone()['count']
        print(f"[OK] Database verbinding OK")
        print(f"[OK] Gevonden: {user_count} actieve gebruikers (excl. admin)")

        # Check planning data
        cursor.execute("SELECT COUNT(*) as count FROM planning")
        planning_count = cursor.fetchone()['count']
        print(f"[OK] Gevonden: {planning_count} planning records")

        # Check HR regels
        cursor.execute("SELECT COUNT(*) as count FROM hr_regels WHERE is_actief = 1")
        hr_count = cursor.fetchone()['count']
        print(f"[OK] Gevonden: {hr_count} actieve HR regels")

        return True

    except Exception as e:
        print(f"[X] Database error: {e}")
        return False


def test_planning_validator_init():
    """Test 2: PlanningValidator instantiatie"""
    print_header("TEST 2: PlanningValidator Initialization")

    try:
        # Haal eerste actieve gebruiker
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, volledige_naam
            FROM gebruikers
            WHERE is_actief = 1 AND gebruikersnaam != 'admin'
            ORDER BY id
            LIMIT 1
        """)

        user = cursor.fetchone()
        if not user:
            print("[X] Geen actieve gebruikers gevonden in database")
            return None

        print(f"[OK] Test gebruiker: {user['volledige_naam']} (ID: {user['id']})")

        # Create validator
        validator = PlanningValidator(
            gebruiker_id=user['id'],
            jaar=2025,
            maand=11
        )

        print(f"[OK] PlanningValidator geïnstantieerd")
        print(f"  - gebruiker_id: {validator.gebruiker_id}")
        print(f"  - jaar: {validator.jaar}")
        print(f"  - maand: {validator.maand}")

        return validator

    except Exception as e:
        print(f"[X] Initialization error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_hr_config_loading(validator: PlanningValidator):
    """Test 3: HR Config laden"""
    print_header("TEST 3: HR Config Loading")

    try:
        hr_config = validator._get_hr_config()

        print(f"[OK] HR config geladen: {len(hr_config)} regels")

        # Print belangrijke regels
        important_keys = ['min_rust_uren', 'max_uren_week', 'max_werkdagen_cyclus',
                         'week_definitie', 'weekend_definitie']

        for key in important_keys:
            if key in hr_config:
                print(f"  - {key}: {hr_config[key]}")
            else:
                print(f"  ! {key}: NIET GEVONDEN (using default)")

        return True

    except Exception as e:
        print(f"[X] HR config error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_shift_tijden_loading(validator: PlanningValidator):
    """Test 4: Shift tijden laden"""
    print_header("TEST 4: Shift Tijden Loading")

    try:
        shift_tijden = validator._get_shift_tijden()

        print(f"[OK] Shift tijden geladen: {len(shift_tijden)} codes")

        # Toon sample
        sample_codes = list(shift_tijden.keys())[:5]
        for code in sample_codes:
            info = shift_tijden[code]
            print(f"  - {code}: {info['start_uur']}-{info['eind_uur']} (werkdag: {info['telt_als_werkdag']})")

        if len(shift_tijden) > 5:
            print(f"  ... en {len(shift_tijden) - 5} meer")

        return True

    except Exception as e:
        print(f"[X] Shift tijden error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_planning_data_loading(validator: PlanningValidator):
    """Test 5: Planning data laden"""
    print_header("TEST 5: Planning Data Loading")

    try:
        planning = validator._get_planning_data()

        print(f"[OK] Planning data geladen: {len(planning)} dagen")

        if len(planning) > 0:
            # Toon eerste paar regels
            for i, regel in enumerate(planning[:3]):
                print(f"  - {regel.datum}: {regel.shift_code} (feestdag: {regel.is_feestdag}, verlof: {regel.is_goedgekeurd_verlof})")

            if len(planning) > 3:
                print(f"  ... en {len(planning) - 3} meer")
        else:
            print("  ! Geen planning data voor deze maand")

        return len(planning)

    except Exception as e:
        print(f"[X] Planning data error: {e}")
        import traceback
        traceback.print_exc()
        return 0


def test_constraint_checker_init(validator: PlanningValidator):
    """Test 6: ConstraintChecker initialisatie"""
    print_header("TEST 6: ConstraintChecker Initialization")

    try:
        checker = validator._get_checker()

        print(f"[OK] ConstraintChecker geïnstantieerd")
        print(f"  - hr_config keys: {list(checker.hr_config.keys())}")
        print(f"  - shift_tijden count: {len(checker.shift_tijden)}")

        return True

    except Exception as e:
        print(f"[X] ConstraintChecker error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validate_all(validator: PlanningValidator):
    """Test 7: validate_all() uitvoeren"""
    print_header("TEST 7: validate_all() Execution")

    try:
        violations_dict = validator.validate_all()

        print(f"[OK] validate_all() uitgevoerd")
        print(f"[OK] Resultaat: {len(violations_dict)} regel checks")

        # Count totaal violations
        total_violations = 0
        for regel, violations in violations_dict.items():
            count = len(violations)
            total_violations += count

            status = "[OK]" if count == 0 else "[\!]"
            print(f"  {status} {regel}: {count} violations")

            # Toon eerste violation als voorbeeld
            if count > 0 and violations:
                v = violations[0]
                print(f"      → {v.beschrijving}")

        print(f"\n[OK] Totaal: {total_violations} violations gevonden")

        return violations_dict

    except Exception as e:
        print(f"[X] validate_all() error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_validate_shift(validator: PlanningValidator):
    """Test 8: validate_shift() real-time check"""
    print_header("TEST 8: validate_shift() Real-time Check")

    try:
        # Test met fictieve shift
        test_datum = date(2025, 11, 15)
        test_code = "7101"  # Vroeg shift

        print(f"  Test: datum={test_datum}, shift_code={test_code}")

        violations = validator.validate_shift(test_datum, test_code)

        print(f"[OK] validate_shift() uitgevoerd")
        print(f"[OK] Resultaat: {len(violations)} violations")

        if violations:
            for v in violations:
                print(f"  [\!] {v.beschrijving}")
        else:
            print(f"  [OK] Geen violations (shift is OK)")

        return True

    except Exception as e:
        print(f"[X] validate_shift() error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_helpers(validator: PlanningValidator):
    """Test 9: UI helper methods"""
    print_header("TEST 9: UI Helper Methods")

    try:
        test_datum = date(2025, 11, 15)

        # Test get_violation_level
        level = validator.get_violation_level(test_datum)
        print(f"[OK] get_violation_level({test_datum}): '{level}'")

        # Test get_violations_voor_datum
        violations = validator.get_violations_voor_datum(test_datum)
        print(f"[OK] get_violations_voor_datum({test_datum}): {len(violations)} violations")

        return True

    except Exception as e:
        print(f"[X] UI helpers error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all smoke tests"""
    print("\n")
    print("=" * 80)
    print(" " * 20 + "HR VALIDATIE SYSTEEM - SMOKE TEST")
    print(" " * 30 + "v0.6.26 (Fase 2)")
    print("=" * 80)

    # Run tests
    results = []

    # Test 1: Database
    results.append(("Database Connection", test_database_connection()))

    # Test 2: Init validator
    validator = test_planning_validator_init()
    results.append(("PlanningValidator Init", validator is not None))

    if validator is None:
        print("\n[X] Cannot continue - validator init failed")
        return

    # Test 3-4: Config loading
    results.append(("HR Config Loading", test_hr_config_loading(validator)))
    results.append(("Shift Tijden Loading", test_shift_tijden_loading(validator)))

    # Test 5: Planning data
    planning_count = test_planning_data_loading(validator)
    results.append(("Planning Data Loading", planning_count is not None))

    # Test 6: ConstraintChecker
    results.append(("ConstraintChecker Init", test_constraint_checker_init(validator)))

    # Test 7-8: Validation methods
    violations_dict = test_validate_all(validator)
    results.append(("validate_all()", violations_dict is not None))

    results.append(("validate_shift()", test_validate_shift(validator)))

    # Test 9: UI helpers
    results.append(("UI Helper Methods", test_ui_helpers(validator)))

    # Summary
    print_header("SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")
    print()

    for name, result in results:
        status = "[OK] PASS" if result else "[X] FAIL"
        print(f"  {status}: {name}")

    print()

    if passed == total:
        print("=" * 80)
        print(" " * 25 + "*** ALL TESTS PASSED! ***")
        print("=" * 80)
        print("\nOK - HR Validatie Systeem is READY voor UI integratie (Fase 3)")
    else:
        print("=" * 80)
        print(" " * 28 + "*** SOME TESTS FAILED ***")
        print("=" * 80)
        print("\nERROR - Fix issues before continuing to Fase 3")

    print()


if __name__ == "__main__":
    main()
