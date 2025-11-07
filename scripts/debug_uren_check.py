"""
Debug script om te veel uren violation te onderzoeken voor Bob Aerts
6-8 november 2024 zonder shifts
"""
import sys
sys.path.insert(0, '.')

from datetime import date
from database.connection import get_connection
from services.constraint_checker import ConstraintChecker, PlanningRegel

def main():
    conn = get_connection()
    cursor = conn.cursor()

    print("=== BOB AERTS PLANNING - NOVEMBER 2024 ===\n")

    # Haal alle planning data voor Bob Aerts in november
    cursor.execute("""
        SELECT datum, shift_code
        FROM planning
        WHERE gebruiker_id = 11
            AND strftime('%Y-%m', datum) = '2024-11'
        ORDER BY datum
    """)

    rows = cursor.fetchall()
    print("Datum       | Shift Code")
    print("------------|------------")
    for row in rows:
        shift = row['shift_code'] if row['shift_code'] else "(leeg)"
        print(f"{row['datum']} | {shift}")

    # Check specifiek 6, 7, 8 november
    print("\n=== FOCUS: 6-8 NOVEMBER ===")
    cursor.execute("""
        SELECT datum, shift_code
        FROM planning
        WHERE gebruiker_id = 11
            AND datum BETWEEN '2024-11-06' AND '2024-11-08'
        ORDER BY datum
    """)

    focus_rows = cursor.fetchall()
    if focus_rows:
        for row in focus_rows:
            shift = row['shift_code'] if row['shift_code'] else "(LEEG - geen shift)"
            print(f"{row['datum']}: {shift}")
    else:
        print("Geen data gevonden voor 6-8 november")

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

    # Haal planning data voor Bob Aerts in november
    cursor.execute("""
        SELECT datum, shift_code, gebruiker_id
        FROM planning
        WHERE gebruiker_id = 11
            AND strftime('%Y-%m', datum) = '2024-11'
        ORDER BY datum
    """)

    planning_regels = []
    for row in cursor.fetchall():
        planning_regels.append(PlanningRegel(
            gebruiker_id=row['gebruiker_id'],
            datum=date.fromisoformat(row['datum']),
            shift_code=row['shift_code'],
            is_goedgekeurd_verlof=False,
            is_feestdag=False
        ))

    # Bereken handmatig uren voor week 4-10 november (ma-zo)
    print("\n=== HANDMATIGE BEREKENING: WEEK 4-10 NOVEMBER ===\n")
    print("Week definitie: maandag 00:00 - zondag 23:59")
    print("Week: 4 november (ma) t/m 10 november (zo)\n")

    week_shifts = [p for p in planning_regels
                   if date(2024, 11, 4) <= p.datum <= date(2024, 11, 10)]

    totaal_uren = 0
    for p in week_shifts:
        shift = p.shift_code if p.shift_code else "(leeg)"
        uren = 0
        if p.shift_code and p.shift_code in shift_tijden:
            duur = checker._bereken_shift_duur(p.shift_code)
            if duur:
                uren = duur
                totaal_uren += uren
        print(f"{p.datum}: {shift:10s} = {uren:5.1f}u")

    print(f"\nTotaal: {totaal_uren:.1f} uur (max: 50u)")
    if totaal_uren > 50:
        print("[FAIL] TE VEEL UREN!")
    else:
        print("[OK] Binnen limiet")

    # Run max uren per week check
    print("\n=== MAX UREN PER WEEK CHECK (CONSTRAINT CHECKER) ===\n")
    result = checker.check_max_uren_week(planning_regels, gebruiker_id=11)

    if result.passed:
        print("[OK] Geen violations gevonden")
    else:
        print(f"[FAIL] {len(result.violations)} violation(s) gevonden:\n")
        for v in result.violations:
            print(f"Violation: {v.beschrijving}")
            print(f"Details: {v.details}")

            # Toon welke shifts in deze week vallen
            if 'week_start' in v.details and 'week_eind' in v.details:
                week_start = v.details['week_start']
                week_eind = v.details['week_eind']
                print(f"\nWeek periode: {week_start} tot {week_eind}")

                # Zoek shifts in deze week
                print("\nShifts in deze week:")
                for p in planning_regels:
                    datum_str = p.datum.isoformat()
                    if week_start[:10] <= datum_str <= week_eind[:10]:
                        shift = p.shift_code if p.shift_code else "(leeg)"
                        # Bereken uren
                        uren = 0
                        if p.shift_code and p.shift_code in shift_tijden:
                            duur = checker._bereken_shift_duur(p.shift_code)
                            if duur:
                                uren = duur
                        print(f"  {datum_str}: {shift:10s} ({uren:.1f}u)")
            print("\n" + "="*60 + "\n")

    conn.close()

if __name__ == "__main__":
    main()
