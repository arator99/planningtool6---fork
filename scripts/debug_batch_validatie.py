"""
Debug script om het verschil te tonen tussen real-time validatie en batch validatie
Scenario: Bob Aerts november 2024
"""
import sys
sys.path.insert(0, '.')

from datetime import date
from database.connection import get_connection

def main():
    conn = get_connection()
    cursor = conn.cursor()

    print("=== BOB AERTS SCENARIO - NOVEMBER 2024 ===\n")
    print("User plant:")
    print("- 4/11: RX")
    print("- 5/11: 1101 (vroeg 06:00-14:00)")
    print("- 6/11: (leeg)")
    print("- 7/11 t/m 15/11: shifts")
    print()

    # Haal daadwerkelijke planning op
    cursor.execute("""
        SELECT datum, shift_code
        FROM planning
        WHERE gebruiker_id = 11
            AND datum BETWEEN '2024-11-04' AND '2024-11-15'
        ORDER BY datum
    """)

    rows = cursor.fetchall()

    print("=== ACTUELE DATABASE ===\n")
    print("Datum       | Shift Code | Uren")
    print("------------|------------|-----")

    for row in rows:
        shift = row['shift_code'] if row['shift_code'] else "(leeg)"
        uren = "0u"

        # Bereken uren als het een shift code is
        if row['shift_code'] and row['shift_code'].startswith(('1', '3', '7')):
            uren = "8u"  # Alle shifts zijn 8u
        elif row['shift_code'] in ('RX', 'CX', 'Z'):
            uren = "0u (rust)"

        print(f"{row['datum']} | {shift:10s} | {uren}")

    # Tel uren per week
    print("\n=== UREN PER WEEK ===\n")

    # Week 45: 4-10 november (ma-zo)
    cursor.execute("""
        SELECT COUNT(*) as shifts
        FROM planning
        WHERE gebruiker_id = 11
            AND datum BETWEEN '2024-11-04' AND '2024-11-10'
            AND shift_code IS NOT NULL
            AND shift_code NOT IN ('RX', 'CX', 'Z', 'VV', 'KD')
    """)
    week1_shifts = cursor.fetchone()['shifts']
    week1_uren = week1_shifts * 8

    print(f"Week 45 (4-10 nov):  {week1_shifts} shifts = {week1_uren}u")
    if week1_uren > 50:
        print("  [ERROR] Te veel uren!")
    else:
        print("  [OK]")

    # Week 46: 11-17 november (ma-zo)
    cursor.execute("""
        SELECT COUNT(*) as shifts
        FROM planning
        WHERE gebruiker_id = 11
            AND datum BETWEEN '2024-11-11' AND '2024-11-17'
            AND shift_code IS NOT NULL
            AND shift_code NOT IN ('RX', 'CX', 'Z', 'VV', 'KD')
    """)
    week2_shifts = cursor.fetchone()['shifts']
    week2_uren = week2_shifts * 8

    print(f"Week 46 (11-17 nov): {week2_shifts} shifts = {week2_uren}u")
    if week2_uren > 50:
        print("  [ERROR] Te veel uren!")
    else:
        print("  [OK]")

    print("\n=== PROBLEEM: REAL-TIME VALIDATIE ===\n")
    print("Bij elke shift save:")
    print("1. validate_shift() checkt ALLEEN die ene datum")
    print("2. Kan niet weten hoeveel uren er AL in die week zijn")
    print("3. Bijvoorbeeld shift 7/11: 8u (lijkt OK in isolatie)")
    print("4. Maar TOTAAL week 45 = 48u (shift 5/11 + 7/11 + ...)")
    print()
    print("GEVOLG:")
    print("- Tijdens plannen: Geen error (single shift check)")
    print("- Na heropenen: Batch validatie ziet HELE week context → 30 errors!")

    print("\n=== MOGELIJKE VIOLATIONS ===\n")
    print("Laat me raden welke 30 errors dit zijn:")
    print("- 12u rust violations (nacht → vroeg)")
    print("- Max uren per week (als totaal > 50u)")
    print("- Max werkdagen cyclus (als > 19 dagen in 28d)")
    print("- Max dagen tussen RX (als > 7 dagen zonder rust)")

    conn.close()

if __name__ == "__main__":
    main()
