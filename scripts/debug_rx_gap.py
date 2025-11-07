"""
Debug script om max dagen tussen RX/CX te testen
Bob Aerts november 2024
"""
import sys
sys.path.insert(0, '.')

from datetime import date
from database.connection import get_connection
from services.constraint_checker import ConstraintChecker, PlanningRegel

def main():
    conn = get_connection()
    cursor = conn.cursor()

    print("=== BOB AERTS - RUSTDAGEN IN NOVEMBER 2024 ===\n")

    # Haal planning op
    cursor.execute("""
        SELECT datum, shift_code
        FROM planning
        WHERE gebruiker_id = 11
            AND strftime('%Y-%m', datum) = '2024-11'
        ORDER BY datum
    """)

    rows = cursor.fetchall()

    # Check welke codes als rustdag worden beschouwd
    cursor.execute("""
        SELECT code, reset_12u_rust
        FROM speciale_codes
        WHERE code IN ('RX', 'CX', 'Z')
    """)

    print("Speciale codes configuratie:")
    for row in cursor.fetchall():
        print(f"  {row['code']}: reset_12u_rust = {row['reset_12u_rust']}")

    print("\n=== PLANNING MET RUSTDAGEN HIGHLIGHT ===\n")
    print("Datum       | Shift Code | Is Rustdag?")
    print("------------|------------|------------")

    rustdagen = []
    for row in rows:
        shift = row['shift_code'] if row['shift_code'] else "(leeg)"
        is_rust = "YES" if row['shift_code'] in ('RX', 'CX', 'Z') else ""

        if is_rust:
            rustdagen.append((row['datum'], row['shift_code']))

        print(f"{row['datum']} | {shift:10s} | {is_rust}")

    print(f"\n=== RUSTDAGEN GEVONDEN: {len(rustdagen)} ===\n")
    for datum, code in rustdagen:
        print(f"  {datum}: {code}")

    print("\n=== GAPS TUSSEN RUSTDAGEN ===\n")
    for i in range(len(rustdagen) - 1):
        datum1, code1 = rustdagen[i]
        datum2, code2 = rustdagen[i + 1]

        d1 = date.fromisoformat(datum1)
        d2 = date.fromisoformat(datum2)

        dagen_tussen = (d2 - d1).days - 1  # Exclusief rustdagen zelf

        status = "[OK]" if dagen_tussen <= 7 else "[VIOLATION!]"
        print(f"{datum1} ({code1}) -> {datum2} ({code2}): {dagen_tussen} dagen {status}")

    print("\n=== RUN CONSTRAINT CHECKER ===\n")

    # Haal shift tijden op
    cursor.execute("""
        SELECT sc.code, sc.start_uur, sc.eind_uur,
               w.telt_als_werkdag, w.reset_12u_rust, w.breekt_werk_reeks
        FROM shift_codes sc
        JOIN werkposten w ON sc.werkpost_id = w.id
        WHERE w.is_actief = 1
    """)

    shift_tijden = {}
    for row in cursor.fetchall():
        shift_tijden[row['code']] = {
            'start_uur': row['start_uur'],
            'eind_uur': row['eind_uur'],
            'telt_als_werkdag': bool(row['telt_als_werkdag']),
            'reset_12u_rust': bool(row['reset_12u_rust']),
            'breekt_werk_reeks': bool(row['breekt_werk_reeks'])
        }

    # Voeg speciale codes toe
    cursor.execute("""
        SELECT code, telt_als_werkdag, reset_12u_rust, breekt_werk_reeks
        FROM speciale_codes
    """)

    for row in cursor.fetchall():
        shift_tijden[row['code']] = {
            'start_uur': None,
            'eind_uur': None,
            'telt_als_werkdag': bool(row['telt_als_werkdag']),
            'reset_12u_rust': bool(row['reset_12u_rust']),
            'breekt_werk_reeks': bool(row['breekt_werk_reeks'])
        }

    print("Speciale codes in shift_tijden dict:")
    for code in ['RX', 'CX', 'Z']:
        if code in shift_tijden:
            print(f"  {code}: reset_12u_rust = {shift_tijden[code]['reset_12u_rust']}")

    # Setup constraint checker
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

    # Haal planning data
    cursor.execute("""
        SELECT datum, shift_code, gebruiker_id
        FROM planning
        WHERE gebruiker_id = 11
            AND strftime('%Y-%m', datum) = '2024-11'
        ORDER BY datum
    """)

    planning_regels = []
    for row in cursor.fetchall():
        if row['shift_code']:  # Alleen rows met shift_code
            planning_regels.append(PlanningRegel(
                gebruiker_id=row['gebruiker_id'],
                datum=date.fromisoformat(row['datum']),
                shift_code=row['shift_code'],
                is_goedgekeurd_verlof=False,
                is_feestdag=False
            ))

    # Run check
    result = checker.check_max_dagen_tussen_rx(planning_regels, gebruiker_id=11)

    print(f"\nConstraint Checker Result:")
    print(f"  Passed: {result.passed}")
    print(f"  Violations: {len(result.violations)}")

    if result.violations:
        print("\nViolations gevonden:")
        for v in result.violations:
            print(f"  - {v.beschrijving}")
            print(f"    Details: {v.details}")
    else:
        print("\n[BUG] Geen violations gevonden, maar er MOET een violation zijn!")

    conn.close()

if __name__ == "__main__":
    main()
