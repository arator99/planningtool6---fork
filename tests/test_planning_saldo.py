"""
Test planning-based saldo berekening

Scenario:
- Gebruiker heeft 10 dagen verlof aangevraagd en goedgekeurd
- 8 dagen staan als VV in planning, 2 zijn handmatig gewijzigd naar CX/RX
- Saldo moet 8 dagen tonen, niet 10
"""

from database.connection import get_connection
from services.verlof_saldo_service import VerlofSaldoService

conn = get_connection()
cursor = conn.cursor()

# Zoek test gebruiker ACV7901
cursor.execute("""
    SELECT id, volledige_naam
    FROM gebruikers
    WHERE gebruikersnaam = 'ACV7901'
""")

gebruiker = cursor.fetchone()
if not gebruiker:
    print("Gebruiker ACV7901 niet gevonden")
    exit(1)

gebruiker_id = gebruiker['id']
naam = gebruiker['volledige_naam']

print(f"Test gebruiker: {naam} (ID: {gebruiker_id})")
print()

# Bereken via beide methoden
jaar = 2025

print("=== Berekening uit AANVRAGEN (oude methode) ===")
vv_aanvragen, kd_aanvragen = VerlofSaldoService.bereken_opgenomen_uit_aanvragen(
    gebruiker_id, jaar
)
print(f"VV opgenomen: {vv_aanvragen} dagen")
print(f"KD opgenomen: {kd_aanvragen} dagen")
print()

print("=== Berekening uit PLANNING (nieuwe methode) ===")
vv_planning, kd_planning = VerlofSaldoService.bereken_opgenomen_uit_planning(
    gebruiker_id, jaar
)
print(f"VV opgenomen: {vv_planning} dagen")
print(f"KD opgenomen: {kd_planning} dagen")
print()

# Tel handmatig in planning
cursor.execute("""
    SELECT
        p.datum,
        p.shift_code,
        COALESCE(sc.term, 'geen term') as term
    FROM planning p
    LEFT JOIN speciale_codes sc ON p.shift_code = sc.code
    WHERE p.gebruiker_id = ?
      AND STRFTIME('%Y', p.datum) = '2025'
      AND STRFTIME('%m', p.datum) = '11'
    ORDER BY p.datum
""", (gebruiker_id,))

print("=== Planning November 2025 (detail) ===")
planning_dagen = cursor.fetchall()
vv_count = 0
kd_count = 0
other_count = 0

for dag in planning_dagen:
    print(f"{dag['datum']}: {dag['shift_code']} (term: {dag['term']})")
    if dag['term'] == 'verlof':
        vv_count += 1
    elif dag['term'] == 'kompensatiedag':
        kd_count += 1
    else:
        other_count += 1

print()
print(f"Handmatige telling: {vv_count} VV, {kd_count} KD, {other_count} overig")
print()

# Haal saldo op (gebruikt nu nieuwe methode)
saldo = VerlofSaldoService.get_saldo(gebruiker_id, jaar)
print("=== get_saldo() resultaat (gebruikt planning methode) ===")
print(f"VV opgenomen: {saldo['vv_opgenomen']} dagen")
print(f"VV resterend: {saldo['vv_resterend']} dagen")
print()

if vv_planning == vv_count:
    print("OK - Planning methode komt overeen met handmatige telling")
else:
    print(f"FOUT - Planning methode ({vv_planning}) != handmatige telling ({vv_count})")
