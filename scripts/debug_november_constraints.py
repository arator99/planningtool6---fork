"""
Debug script om constraint checker issues te onderzoeken in november 2024
"""
from datetime import date, datetime
from database.connection import get_connection
from services.constraint_checker import ConstraintChecker, PlanningRegel

def main():
    conn = get_connection()
    cursor = conn.cursor()

    # Haal shift_codes op om te zien welke codes nacht/vroeg zijn
    print("=== SHIFT CODES ===")
    cursor.execute("""
        SELECT sc.code, sc.start_uur, sc.eind_uur, sc.shift_type,
               w.telt_als_werkdag, w.reset_12u_rust, w.naam as werkpost
        FROM shift_codes sc
        JOIN werkposten w ON sc.werkpost_id = w.id
        WHERE w.is_actief = 1
        ORDER BY sc.code
    """)
    shift_codes = cursor.fetchall()
    for row in shift_codes:
        print(f"{row['code']:8s} {row['shift_type']:8s} {row['start_uur']:8s}-{row['eind_uur']:8s}  werkdag={row['telt_als_werkdag']}  reset={row['reset_12u_rust']}  ({row['werkpost']})")

    # Haal planning data voor november 2024
    print("\n=== PLANNING NOVEMBER 2024 (eerste 50 regels) ===")
    cursor.execute("""
        SELECT p.datum, p.shift_code, g.volledige_naam, p.gebruiker_id
        FROM planning p
        JOIN gebruikers g ON p.gebruiker_id = g.id
        WHERE strftime('%Y-%m', p.datum) = '2024-11'
            AND p.shift_code IS NOT NULL
            AND g.gebruikersnaam != 'admin'
        ORDER BY p.gebruiker_id, p.datum
        LIMIT 50
    """)
    planning_rows = cursor.fetchall()

    current_user = None
    for row in planning_rows:
        if row['gebruiker_id'] != current_user:
            current_user = row['gebruiker_id']
            print(f"\n--- {row['volledige_naam']} (ID: {row['gebruiker_id']}) ---")
        print(f"  {row['datum']}  {row['shift_code']}")

    # Zoek specifiek naar nacht gevolgd door vroeg patronen
    print("\n=== NACHT GEVOLGD DOOR VROEG PATRONEN ===")
    cursor.execute("""
        SELECT p1.datum as datum1, p1.shift_code as code1,
               p2.datum as datum2, p2.shift_code as code2,
               g.volledige_naam,
               sc1.eind_uur as eind1, sc2.start_uur as start2
        FROM planning p1
        JOIN planning p2 ON p2.gebruiker_id = p1.gebruiker_id
            AND p2.datum = date(p1.datum, '+1 day')
        JOIN gebruikers g ON p1.gebruiker_id = g.id
        LEFT JOIN shift_codes sc1 ON p1.shift_code = sc1.code
        LEFT JOIN shift_codes sc2 ON p2.shift_code = sc2.code
        WHERE strftime('%Y-%m', p1.datum) = '2024-11'
            AND p1.shift_code IS NOT NULL
            AND p2.shift_code IS NOT NULL
            AND g.gebruikersnaam != 'admin'
            AND sc1.eind_uur IS NOT NULL
            AND sc2.start_uur IS NOT NULL
            -- Nacht eindigt tussen 04:00 en 08:00
            AND sc1.eind_uur >= '04:00' AND sc1.eind_uur <= '08:00'
            -- Vroeg begint tussen 05:00 en 07:00
            AND sc2.start_uur >= '05:00' AND sc2.start_uur <= '07:00'
        ORDER BY p1.datum
    """)

    patterns = cursor.fetchall()
    for row in patterns:
        print(f"{row['volledige_naam']}: {row['datum1']} {row['code1']} ({row['eind1']}) → {row['datum2']} {row['code2']} ({row['start2']})")

        # Bereken rust
        dt1 = datetime.strptime(f"{row['datum1']} {row['eind1']}", "%Y-%m-%d %H:%M")
        dt2 = datetime.strptime(f"{row['datum2']} {row['start2']}", "%Y-%m-%d %H:%M")
        rust = (dt2 - dt1).total_seconds() / 3600
        print(f"  → Rust: {rust:.1f} uur")

    conn.close()

if __name__ == "__main__":
    main()
