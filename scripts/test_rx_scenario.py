"""
Test exact scenario dat gebruiker beschreef:
- 4/11: RX
- 5/11: 1101
- 6/11: leeg
- 7-15/11: shiften
- Geen RX/CX tussen 4/11 en volgende rustdag

Dit zou een violation moeten zijn!
"""
import sys
sys.path.insert(0, '.')

from datetime import date
from services.constraint_checker import ConstraintChecker, PlanningRegel

def main():
    print("=== TEST SCENARIO: 11 DAGEN ZONDER RUSTDAG ===\n")
    print("Planning:")
    print("  4 nov: RX")
    print("  5 nov: 1101 (shift)")
    print("  6 nov: (leeg)")
    print("  7-15 nov: shiften (9 dagen)")
    print("  16 nov: RX (volgende rustdag)")
    print()
    print("Gap tussen RX: 16 - 4 - 1 = 11 dagen")
    print("Limiet: 7 dagen")
    print("Verwachting: VIOLATION!\n")

    # Setup
    shift_tijden = {
        '1101': {
            'start_uur': '06:00',
            'eind_uur': '14:00',
            'telt_als_werkdag': True,
            'reset_12u_rust': False,
            'breekt_werk_reeks': False
        },
        'RX': {
            'start_uur': None,
            'eind_uur': None,
            'telt_als_werkdag': False,
            'reset_12u_rust': True,  # NU TRUE (na fix)
            'breekt_werk_reeks': True
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

    # Planning data (exact scenario)
    planning = [
        PlanningRegel(11, date(2024, 11, 4), 'RX'),
        PlanningRegel(11, date(2024, 11, 5), '1101'),
        # 6/11 leeg
        PlanningRegel(11, date(2024, 11, 7), '1101'),
        PlanningRegel(11, date(2024, 11, 8), '1101'),
        PlanningRegel(11, date(2024, 11, 9), '1101'),
        PlanningRegel(11, date(2024, 11, 10), '1101'),
        PlanningRegel(11, date(2024, 11, 11), '1101'),
        PlanningRegel(11, date(2024, 11, 12), '1101'),
        PlanningRegel(11, date(2024, 11, 13), '1101'),
        PlanningRegel(11, date(2024, 11, 14), '1101'),
        PlanningRegel(11, date(2024, 11, 15), '1101'),
        PlanningRegel(11, date(2024, 11, 16), 'RX'),
    ]

    # Run check
    result = checker.check_max_dagen_tussen_rx(planning, gebruiker_id=11)

    print("=== CONSTRAINT CHECKER RESULT ===\n")
    print(f"Passed: {result.passed}")
    print(f"Violations: {len(result.violations)}\n")

    if result.violations:
        print("[OK] Violation gedetecteerd!")
        for v in result.violations:
            print(f"\n{v.beschrijving}")
            print(f"Details: {v.details}")
    else:
        print("[BUG] Geen violation gedetecteerd!")
        print("Dit is een probleem - er zijn 11 dagen zonder rustdag!")

if __name__ == "__main__":
    main()
