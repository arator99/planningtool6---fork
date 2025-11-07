"""
Test verlof berekening fix
13-22 november 2025 zou 10 kalenderdagen moeten zijn
"""

from services.verlof_saldo_service import VerlofSaldoService

# Test scenario: 13-22 nov 2025
start = "2025-11-13"  # donderdag
eind = "2025-11-22"   # zaterdag

dagen = VerlofSaldoService._bereken_werkdagen(start, eind)

print(f"Periode: {start} t/m {eind}")
print(f"Berekende dagen: {dagen}")
print(f"Verwacht: 10 kalenderdagen")
print(f"Resultaat: {'OK - CORRECT' if dagen == 10 else f'FOUT (kreeg {dagen})'}")

# Extra test: 1 dag
start2 = "2025-11-13"
eind2 = "2025-11-13"
dagen2 = VerlofSaldoService._bereken_werkdagen(start2, eind2)
print(f"\nTest 1 dag: {dagen2} (verwacht: 1) {'OK' if dagen2 == 1 else 'FOUT'}")

# Extra test: inclusief weekend
start3 = "2025-11-14"  # vrijdag
eind3 = "2025-11-17"   # maandag (over weekend)
dagen3 = VerlofSaldoService._bereken_werkdagen(start3, eind3)
print(f"Test over weekend (vr-ma): {dagen3} (verwacht: 4) {'OK' if dagen3 == 4 else 'FOUT'}")
