"""
Test ISSUE-001: Feestdag Herkenning bij Kritische Shifts

Test of 1 januari correct wordt herkend als feestdag en of de juiste
zondag shift codes worden verwacht.
"""

from datetime import date
from services.bemannings_controle_service import (
    is_feestdag,
    get_dag_type,
    get_verwachte_codes,
    controleer_bemanning
)


def test_issue_001():
    """Test 1 januari 2025 feestdag herkenning"""

    test_datum = date(2025, 1, 1)  # Woensdag

    print("="*60)
    print("TEST ISSUE-001: Feestdag Herkenning (1 januari 2025)")
    print("="*60)
    print(f"\nDatum: {test_datum} (woensdag)")

    # Test 1: is_feestdag()
    is_feest = is_feestdag(test_datum)
    print(f"\n1. is_feestdag(): {is_feest}")
    print(f"   Status: {'[OK] CORRECT' if is_feest else '[FOUT] zou True moeten zijn'}")

    # Test 2: get_dag_type()
    dag_type = get_dag_type(test_datum)
    print(f"\n2. get_dag_type(): '{dag_type}'")
    print(f"   Status: {'[OK] CORRECT' if dag_type == 'zondag' else '[FOUT] zou zondag moeten zijn'}")

    # Test 3: get_verwachte_codes()
    verwachte_codes = get_verwachte_codes(test_datum)
    print(f"\n3. Verwachte kritische codes (dag_type='{dag_type}'):")
    if verwachte_codes:
        for code in verwachte_codes:
            print(f"   - {code['code']}: {code['werkpost_naam']} {code['shift_type']} ({code['start_uur']}-{code['eind_uur']})")
    else:
        print("   (geen kritische codes verwacht)")

    # Test 4: controleer_bemanning()
    resultaat = controleer_bemanning(test_datum)
    print(f"\n4. controleer_bemanning():")
    print(f"   Status: {resultaat['status']}")
    print(f"   Details: {resultaat['details']}")
    print(f"   Verwachte codes: {len(resultaat['verwachte_codes'])}")
    print(f"   Werkelijke codes: {len(resultaat['werkelijke_codes'])}")

    # Conclusie
    print("\n" + "="*60)
    if is_feest and dag_type == 'zondag':
        print("CONCLUSIE: [OK] Bug NIET GEREPRODUCEERD")
        print("1 januari wordt CORRECT herkend als feestdag (zondag)")
        print("De bug is mogelijk al opgelost of bestaat niet meer.")
    else:
        print("CONCLUSIE: [FOUT] Bug GEREPRODUCEERD")
        print("1 januari wordt NIET correct herkend als feestdag!")
    print("="*60)


if __name__ == "__main__":
    test_issue_001()
