"""
Test script voor werkpost validatie check

Scenario:
1. Gebruiker heeft shift code die behoort bij werkpost die hij/zij niet kent
2. Check of violation wordt gegenereerd
3. Check of violation juiste severity heeft (WARNING)
4. Check of beschrijving correct is

Run: python test_werkpost_validation.py
"""

from datetime import date
from services.constraint_checker import ConstraintChecker, PlanningRegel

def test_werkpost_validation():
    """Test werkpost koppeling validatie"""

    # Setup HR config (minimaal voor test)
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

    # Setup shift tijden
    shift_tijden = {
        '7101': {  # PAT vroeg
            'start_uur': '06:00',
            'eind_uur': '14:00',
            'shift_type': 'vroeg',
            'werkpost_naam': 'PAT',
            'telt_als_werkdag': True,
            'reset_12u_rust': False,
            'breekt_werk_reeks': False,
            'term': None
        },
        '7301': {  # Interventie vroeg
            'start_uur': '06:00',
            'eind_uur': '14:00',
            'shift_type': 'vroeg',
            'werkpost_naam': 'Interventie',
            'telt_als_werkdag': True,
            'reset_12u_rust': False,
            'breekt_werk_reeks': False,
            'term': None
        }
    }

    # Setup gebruiker werkposten mapping
    # Gebruiker 1 kent alleen PAT (werkpost_id=1), NIET Interventie (werkpost_id=2)
    gebruiker_werkposten_map = {
        1: [1]  # Gebruiker 1 kent alleen werkpost 1 (PAT)
    }

    # Setup shift code → werkpost mapping
    shift_code_werkpost_map = {
        '7101': 1,  # PAT vroeg → werkpost 1
        '7301': 2   # Interventie vroeg → werkpost 2
    }

    # Create planning regel: gebruiker 1 heeft Interventie shift (die hij NIET kent)
    planning = [
        PlanningRegel(
            gebruiker_id=1,
            datum=date(2025, 11, 12),
            shift_code='7301',  # Interventie vroeg (werkpost 2)
            is_goedgekeurd_verlof=False,
            is_feestdag=False
        )
    ]

    # Run check
    checker = ConstraintChecker(hr_config, shift_tijden)
    result = checker.check_werkpost_koppeling(
        planning,
        gebruiker_id=1,
        gebruiker_werkposten_map=gebruiker_werkposten_map,
        shift_code_werkpost_map=shift_code_werkpost_map
    )

    # Verify results
    print("\n" + "="*60)
    print("TEST: Werkpost Validatie Check")
    print("="*60)

    print(f"\nPassed: {result.passed}")
    print(f"Aantal violations: {len(result.violations)}")

    if result.violations:
        for v in result.violations:
            print(f"\nViolation gevonden:")
            print(f"  Type: {v.type.value}")
            print(f"  Severity: {v.severity.value}")
            print(f"  Datum: {v.datum}")
            print(f"  Beschrijving: {v.beschrijving}")
            print(f"  Gebruiker ID: {v.gebruiker_id}")

    # Assertions
    assert result.passed == False, "Check zou FALSE moeten zijn (violation gevonden)"
    assert len(result.violations) == 1, "Moet exact 1 violation zijn"
    assert result.violations[0].type.value == 'werkpost_onbekend', "Type moet werkpost_onbekend zijn"
    assert result.violations[0].severity.value == 'warning', "Severity moet warning zijn"
    assert 'Interventie' in result.violations[0].beschrijving, "Beschrijving moet werkpost naam bevatten"

    print("\nALLE TESTS GESLAAGD!")
    print("="*60 + "\n")


def test_werkpost_validation_ok():
    """Test dat er GEEN violation is als gebruiker wel werkpost kent"""

    # Setup (zelfde als hierboven)
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

    shift_tijden = {
        '7101': {
            'start_uur': '06:00',
            'eind_uur': '14:00',
            'shift_type': 'vroeg',
            'werkpost_naam': 'PAT',
            'telt_als_werkdag': True,
            'reset_12u_rust': False,
            'breekt_werk_reeks': False,
            'term': None
        }
    }

    # Gebruiker 1 kent PAT (werkpost_id=1)
    gebruiker_werkposten_map = {
        1: [1]
    }

    shift_code_werkpost_map = {
        '7101': 1
    }

    # Planning: gebruiker 1 heeft PAT shift (die hij WEL kent)
    planning = [
        PlanningRegel(
            gebruiker_id=1,
            datum=date(2025, 11, 12),
            shift_code='7101',  # PAT vroeg (werkpost 1)
            is_goedgekeurd_verlof=False,
            is_feestdag=False
        )
    ]

    # Run check
    checker = ConstraintChecker(hr_config, shift_tijden)
    result = checker.check_werkpost_koppeling(
        planning,
        gebruiker_id=1,
        gebruiker_werkposten_map=gebruiker_werkposten_map,
        shift_code_werkpost_map=shift_code_werkpost_map
    )

    # Verify
    print("\n" + "="*60)
    print("TEST: Werkpost Validatie Check (Positief Scenario)")
    print("="*60)

    print(f"\nPassed: {result.passed}")
    print(f"Aantal violations: {len(result.violations)}")

    # Assertions
    assert result.passed == True, "Check zou TRUE moeten zijn (geen violations)"
    assert len(result.violations) == 0, "Moet 0 violations zijn"

    print("\nTEST GESLAAGD - Geen violations zoals verwacht!")
    print("="*60 + "\n")


if __name__ == '__main__':
    test_werkpost_validation()
    test_werkpost_validation_ok()
