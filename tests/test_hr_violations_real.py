"""
Test HR Validatie met daadwerkelijke violations

Test scenarios:
1. 12u rust violation: 2 shifts met 10 uur rust
2. 50u week violation: 60 uur in 1 week
3. 19 dagen cyclus violation: 20 werkdagen in 28-dagen periode
4. 7 dagen tussen RX: 10 dagen zonder RX
5. 7 werkdagen reeks: 9 opeenvolgende werkdagen
6. Max weekends: 7 opeenvolgende weekends werken

Versie: v0.6.26 (Fase 2 Testing)
Datum: 3 November 2025
"""

import sys
import os
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.constraint_checker import (
    ConstraintChecker,
    PlanningRegel,
    ViolationType
)


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def get_default_hr_config():
    """Get default HR config (alle vereiste velden)"""
    return {
        'min_rust_uren': 12.0,
        'max_uren_week': 50.0,
        'max_werkdagen_cyclus': 19,
        'max_dagen_tussen_rx': 7,
        'max_werkdagen_reeks': 7,
        'max_weekends_achter_elkaar': 6,
        'week_definitie': 'ma-00:00|zo-23:59',
        'weekend_definitie': 'za-00:00|zo-23:59'
    }


def test_12u_rust_violation():
    """Test 1: 12u rust violation"""
    print_header("TEST 1: 12u Rust Violation (10 uur tussen shifts)")

    # Setup
    hr_config = get_default_hr_config()
    shift_tijden = {
        '7101': {'start_uur': '06:00', 'eind_uur': '14:00', 'telt_als_werkdag': True,
                 'reset_12u_rust': False, 'breekt_werk_reeks': False},
        '7201': {'start_uur': '14:00', 'eind_uur': '22:00', 'telt_als_werkdag': True,
                 'reset_12u_rust': False, 'breekt_werk_reeks': False}
    }

    checker = ConstraintChecker(hr_config, shift_tijden)

    # Planning: dag 1 laat (eindigt 22:00), dag 2 vroeg (start 06:00) = 8u rust
    planning = [
        PlanningRegel(1, date(2025, 11, 1), '7201'),  # 14:00-22:00
        PlanningRegel(1, date(2025, 11, 2), '7101'),  # 06:00-14:00 (8u na vorige!)
    ]

    result = checker.check_12u_rust(planning, 1)

    print(f"Planning:")
    print(f"  - 2025-11-01: 7201 (14:00-22:00)")
    print(f"  - 2025-11-02: 7101 (06:00-14:00)")
    print(f"  -> Rust: 8 uur (VIOLATION - min 12u vereist)")
    print(f"\nResultaat: {len(result.violations)} violations")

    if result.violations:
        for v in result.violations:
            print(f"  [!] {v.beschrijving}")
            print(f"      Type: {v.type.value}, Severity: {v.severity.value}")
        return True
    else:
        print(f"  [X] FOUT: Geen violation gedetecteerd!")
        return False


def test_50u_week_violation():
    """Test 2: 50u week violation"""
    print_header("TEST 2: Max 50u per Week Violation (60 uur in week)")

    # Setup
    hr_config = get_default_hr_config()
    shift_tijden = {
        '7101': {'start_uur': '06:00', 'eind_uur': '14:00', 'telt_als_werkdag': True,
                 'reset_12u_rust': False, 'breekt_werk_reeks': False},  # 8u
        '7201': {'start_uur': '14:00', 'eind_uur': '22:00', 'telt_als_werkdag': True,
                 'reset_12u_rust': False, 'breekt_werk_reeks': False},  # 8u
    }

    checker = ConstraintChecker(hr_config, shift_tijden)

    # Planning: 7 dagen met 8u shifts + 1 dag met dubbele shift (60u totaal)
    start_datum = date(2025, 11, 3)  # Maandag
    planning = []

    for i in range(7):
        planning.append(PlanningRegel(1, start_datum + timedelta(days=i), '7101'))

    # Laatste dag dubbele shift (8u extra = 60u totaal)
    planning.append(PlanningRegel(1, start_datum + timedelta(days=6), '7201'))

    result = checker.check_max_uren_week(planning, 1)

    print(f"Planning: 7 dagen met 8u + 1 dag dubbel = 60 uur")
    print(f"Week definitie: ma-00:00 tot zo-23:59")
    print(f"\nResultaat: {len(result.violations)} violations")

    if result.violations:
        for v in result.violations:
            print(f"  [!] {v.beschrijving}")
            uren = v.details.get('totaal_uren', 0)
            print(f"      Totaal uren: {uren:.1f} (max 50u)")
        return True
    else:
        print(f"  [X] FOUT: Geen violation gedetecteerd!")
        return False


def test_9_werkdagen_reeks():
    """Test 3: 7 werkdagen reeks violation"""
    print_header("TEST 3: Max 7 Werkdagen Reeks Violation (9 dagen achter elkaar)")

    # Setup
    hr_config = get_default_hr_config()
    shift_tijden = {
        '7101': {'start_uur': '06:00', 'eind_uur': '14:00', 'telt_als_werkdag': True,
                 'reset_12u_rust': False, 'breekt_werk_reeks': False},
    }

    checker = ConstraintChecker(hr_config, shift_tijden)

    # Planning: 9 opeenvolgende werkdagen
    start_datum = date(2025, 11, 1)
    planning = []

    for i in range(9):
        planning.append(PlanningRegel(1, start_datum + timedelta(days=i), '7101'))

    result = checker.check_max_werkdagen_reeks(planning, 1)

    print(f"Planning: 9 opeenvolgende werkdagen (max 7)")
    print(f"  - 2025-11-01 t/m 2025-11-09: 7101 (vroeg shift)")
    print(f"\nResultaat: {len(result.violations)} violations")

    if result.violations:
        for v in result.violations:
            print(f"  [!] {v.beschrijving}")
            reeks_lengte = v.details.get('reeks_lengte', 0)
            print(f"      Reeks lengte: {reeks_lengte} dagen (max 7)")
        return True
    else:
        print(f"  [X] FOUT: Geen violation gedetecteerd!")
        return False


def test_20_werkdagen_cyclus():
    """Test 4: 19 werkdagen cyclus violation"""
    print_header("TEST 4: Max 19 Werkdagen per Cyclus Violation (20 dagen)")

    # Setup
    hr_config = get_default_hr_config()
    shift_tijden = {
        '7101': {'start_uur': '06:00', 'eind_uur': '14:00', 'telt_als_werkdag': True,
                 'reset_12u_rust': False, 'breekt_werk_reeks': False},
        'RX': {'start_uur': None, 'eind_uur': None, 'telt_als_werkdag': False,
               'reset_12u_rust': True, 'breekt_werk_reeks': True},
    }

    checker = ConstraintChecker(hr_config, shift_tijden)

    # Rode lijn periode: 28 dagen
    start_datum = date(2025, 11, 1)
    rode_lijnen = [{
        'start_datum': start_datum,
        'eind_datum': start_datum + timedelta(days=27),
        'periode_nummer': 1
    }]

    # Planning: 20 werkdagen + 8 rustdagen in 28-dagen periode
    planning = []
    dag_counter = 0

    for i in range(28):
        datum = start_datum + timedelta(days=i)
        # Werk 5 dagen, rust 2 dagen pattern (met 1 extra werkdag)
        if dag_counter % 7 < 5 or dag_counter == 27:  # 27e dag ook werken = 20 dagen
            planning.append(PlanningRegel(1, datum, '7101'))
        else:
            planning.append(PlanningRegel(1, datum, 'RX'))
        dag_counter += 1

    result = checker.check_max_werkdagen_cyclus(planning, 1, rode_lijnen)

    werk_count = sum(1 for p in planning if p.shift_code == '7101')
    print(f"Planning: {werk_count} werkdagen in 28-dagen cyclus (max 19)")
    print(f"Periode: 2025-11-01 t/m 2025-11-28")
    print(f"\nResultaat: {len(result.violations)} violations")

    if result.violations:
        for v in result.violations:
            print(f"  [!] {v.beschrijving}")
            dagen = v.details.get('werkdagen_count', 0)
            print(f"      Werkdagen: {dagen} (max 19)")
        return True
    else:
        print(f"  [X] FOUT: Geen violation gedetecteerd!")
        return False


def test_10_dagen_zonder_rx():
    """Test 5: Max 7 dagen tussen RX violation"""
    print_header("TEST 5: Max 7 Dagen Tussen RX Violation (10 dagen gap)")

    # Setup
    hr_config = get_default_hr_config()
    shift_tijden = {
        '7101': {'start_uur': '06:00', 'eind_uur': '14:00', 'telt_als_werkdag': True,
                 'reset_12u_rust': False, 'breekt_werk_reeks': False},
        'RX': {'start_uur': None, 'eind_uur': None, 'telt_als_werkdag': False,
               'reset_12u_rust': True, 'breekt_werk_reeks': True},
    }

    checker = ConstraintChecker(hr_config, shift_tijden)

    # Planning: RX op dag 1, dan 10 werkdagen, dan RX
    start_datum = date(2025, 11, 1)
    planning = [
        PlanningRegel(1, start_datum, 'RX'),
    ]

    # 10 werkdagen na RX
    for i in range(1, 11):
        planning.append(PlanningRegel(1, start_datum + timedelta(days=i), '7101'))

    planning.append(PlanningRegel(1, start_datum + timedelta(days=11), 'RX'))

    result = checker.check_max_dagen_tussen_rx(planning, 1)

    print(f"Planning:")
    print(f"  - 2025-11-01: RX")
    print(f"  - 2025-11-02 t/m 2025-11-11: 10 werkdagen (max 7 dagen tussen RX)")
    print(f"  - 2025-11-12: RX")
    print(f"\nResultaat: {len(result.violations)} violations")

    if result.violations:
        for v in result.violations:
            print(f"  [!] {v.beschrijving}")
            dagen = v.details.get('dagen_sinds_rx', 0)
            print(f"      Dagen sinds laatste RX: {dagen} (max 7)")
        return True
    else:
        print(f"  [X] FOUT: Geen violation gedetecteerd!")
        return False


def main():
    """Run all violation tests"""
    print("\n")
    print("=" * 80)
    print(" " * 15 + "HR VALIDATIE - REAL VIOLATION TESTING")
    print(" " * 30 + "v0.6.26 (Fase 2)")
    print("=" * 80)

    results = []

    # Run tests
    results.append(("12u Rust Violation", test_12u_rust_violation()))
    results.append(("50u Week Violation", test_50u_week_violation()))
    results.append(("9 Werkdagen Reeks", test_9_werkdagen_reeks()))
    results.append(("20 Werkdagen Cyclus", test_20_werkdagen_cyclus()))
    results.append(("10 Dagen Zonder RX", test_10_dagen_zonder_rx()))

    # Summary
    print_header("SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}\n")

    for name, result in results:
        status = "[OK] PASS" if result else "[X] FAIL"
        print(f"  {status}: {name}")

    print()

    if passed == total:
        print("=" * 80)
        print(" " * 20 + "*** ALL VIOLATION TESTS PASSED! ***")
        print("=" * 80)
        print("\nOK - HR Constraint Checker detecteert violations correct!")
    else:
        print("=" * 80)
        print(" " * 23 + "*** SOME TESTS FAILED ***")
        print("=" * 80)
        print(f"\nERROR - {total - passed} violation(s) niet gedetecteerd!")

    print()


if __name__ == "__main__":
    main()
