"""
Debug script voor bemannings controle
Toont wat er verwacht wordt vs wat er ingevuld is voor een specifieke datum
"""

from datetime import date
from services.bemannings_controle_service import (
    get_verwachte_codes,
    get_werkelijke_codes,
    controleer_bemanning,
    get_dag_type
)

# Test datum (pas aan naar de datum die je wilt testen)
test_datum = date(2025, 11, 4)  # 4 november

print(f"\n=== BEMANNINGS CONTROLE DEBUG ===")
print(f"Datum: {test_datum.strftime('%d-%m-%Y (%A)')}")
print(f"Dag type: {get_dag_type(test_datum)}")

print(f"\n--- VERWACHTE CODES (uit shift_codes tabel) ---")
verwachte = get_verwachte_codes(test_datum)
if verwachte:
    for item in verwachte:
        print(f"  Code: {item['code']} | {item['werkpost_naam']} {item['shift_type']} | {item['start_uur']}-{item['eind_uur']}")
else:
    print("  (geen verwachte codes - alle werkposten gedeactiveerd?)")

print(f"\n--- WERKELIJKE CODES (uit planning tabel) ---")
werkelijke = get_werkelijke_codes(test_datum)
if werkelijke:
    for item in werkelijke:
        print(f"  Code: {item['code']} | {item['gebruiker_naam']}")
else:
    print("  (geen codes ingevuld)")

print(f"\n--- VALIDATIE RESULTAAT ---")
resultaat = controleer_bemanning(test_datum)
print(f"Status: {resultaat['status'].upper()}")
print(f"Details: {resultaat['details']}")

if resultaat['ontbrekende_codes']:
    print(f"\nOntbrekende codes:")
    for item in resultaat['ontbrekende_codes']:
        print(f"  - {item['code']} ({item['werkpost_naam']} {item['shift_type']})")

if resultaat['dubbele_codes']:
    print(f"\nDubbele codes:")
    for item in resultaat['dubbele_codes']:
        print(f"  - {item['code']} gebruikt door: {', '.join(item['gebruikers'])}")

print("\n" + "="*50 + "\n")
