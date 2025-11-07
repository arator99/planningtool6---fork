"""
Check of nacht shift (22:00-06:00) mogelijk dubbel meetelt in week berekening
door middernacht crossing
"""
import sys
sys.path.insert(0, '.')

from datetime import date, datetime, timedelta
from database.connection import get_connection
from services.constraint_checker import ConstraintChecker, PlanningRegel

def main():
    print("=== MOGELIJKE BUG: NACHT SHIFT OVERLAP MET WEEK ===\n")

    # Setup minimal checker
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
        '1301': {
            'start_uur': '22:00',
            'eind_uur': '06:00',
            'telt_als_werkdag': True,
            'reset_12u_rust': False,
            'breekt_werk_reeks': False
        }
    }

    checker = ConstraintChecker(hr_config, shift_tijden)

    # Test: nacht shift op woensdag 6 november
    print("Test scenario: Nacht shift op woensdag 6 november 2024")
    print("Shift: 1301 (22:00-06:00)")
    print("Start: wo 6 nov 22:00")
    print("Eind: do 7 nov 06:00 (middernacht crossing!)\n")

    # Week 1: ma 4 nov - zo 10 nov
    print("Week 1: ma 4 nov 00:00 - zo 10 nov 23:59")

    shift_datum = date(2024, 11, 6)
    shift_start = datetime(2024, 11, 6, 22, 0)  # wo 22:00
    shift_eind = datetime(2024, 11, 7, 6, 0)    # do 06:00

    week1_start = datetime(2024, 11, 4, 0, 0)   # ma 00:00
    week1_eind = datetime(2024, 11, 10, 23, 59) # zo 23:59

    # Check overlap
    overlapt = checker._shift_overlapt_week(shift_datum, '1301', week1_start, week1_eind)
    print(f"Shift overlapt met Week 1? {overlapt}")

    if overlapt:
        duur = checker._bereken_shift_duur('1301')
        print(f"Shift duur: {duur} uur")
        print("[OK] Shift telt 1x mee in Week 1")

    # Week 2: ma 11 nov - zo 17 nov
    print("\nWeek 2: ma 11 nov 00:00 - zo 17 nov 23:59")
    week2_start = datetime(2024, 11, 11, 0, 0)   # ma 00:00
    week2_eind = datetime(2024, 11, 17, 23, 59)  # zo 23:59

    overlapt2 = checker._shift_overlapt_week(shift_datum, '1301', week2_start, week2_eind)
    print(f"Shift overlapt met Week 2? {overlapt2}")

    if overlapt2:
        print("[BUG!] Shift telt ook mee in Week 2 (verkeerd!)")

    # Test weekend overlap logica
    print("\n=== TEST: WEEKEND OVERLAP (REFERENTIE) ===\n")
    print("Weekend definitie: vr 22:00 - ma 06:00")
    print("Shift op vrijdag 22:00-06:00 (zaterdag ochtend)\n")

    weekend_start = datetime(2024, 11, 8, 22, 0)  # vr 22:00
    weekend_eind = datetime(2024, 11, 11, 6, 0)   # ma 06:00

    vr_shift_datum = date(2024, 11, 8)  # vrijdag
    vr_shift_overlapt = checker._shift_overlapt_weekend(
        vr_shift_datum, '1301', weekend_start, weekend_eind
    )

    print(f"Vrijdag nacht shift overlapt met weekend? {vr_shift_overlapt}")
    print("(Verwacht: True - shift loopt door in weekend)")

if __name__ == "__main__":
    main()
