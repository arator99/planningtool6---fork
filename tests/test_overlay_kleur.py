"""Test of de overlay kleur correct wordt gegenereerd"""

from datetime import date
from services.bemannings_controle_service import controleer_bemanning

test_datum = date(2025, 11, 4)

resultaat = controleer_bemanning(test_datum)

print(f"\n=== OVERLAY KLEUR TEST ===")
print(f"Datum: {test_datum}")
print(f"Status: {resultaat['status']}")

# Simuleer de get_bemannings_overlay_kleur functie
status = resultaat['status']

if status == 'groen':
    overlay = "rgba(129, 199, 132, 0.2)"  # #81C784
    print(f"Overlay kleur: {overlay} (LICHTGROEN)")
elif status == 'geel':
    overlay = "rgba(255, 224, 130, 0.3)"  # #FFE082
    print(f"Overlay kleur: {overlay} (GEEL)")
elif status == 'rood':
    overlay = "rgba(229, 115, 115, 0.2)"  # #E57373
    print(f"Overlay kleur: {overlay} (ROOD)")
else:
    overlay = None
    print(f"Overlay kleur: None (GEEN OVERLAY)")

print(f"\nDeze kleur zou over de weekend/weekdag achtergrond heen moeten komen.")
print("="*50 + "\n")
