"""Check welke shift codes gedefinieerd zijn voor een werkpost"""

from database.connection import get_connection

werkpost_naam = "Traffic Officer"

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT
        w.naam as werkpost,
        w.is_actief,
        sc.dag_type,
        sc.shift_type,
        sc.code,
        sc.start_uur,
        sc.eind_uur
    FROM shift_codes sc
    JOIN werkposten w ON sc.werkpost_id = w.id
    WHERE w.naam = ?
    ORDER BY
        CASE sc.dag_type
            WHEN 'weekdag' THEN 1
            WHEN 'zaterdag' THEN 2
            WHEN 'zondag' THEN 3
        END,
        CASE sc.shift_type
            WHEN 'vroeg' THEN 1
            WHEN 'dag' THEN 2
            WHEN 'laat' THEN 3
            WHEN 'nacht' THEN 4
        END
""", (werkpost_naam,))

print(f"\n=== SHIFT CODES VOOR '{werkpost_naam}' ===\n")
print(f"Actief: {cursor.fetchone()}")

cursor.execute("""
    SELECT
        w.naam as werkpost,
        w.is_actief,
        sc.dag_type,
        sc.shift_type,
        sc.code,
        sc.start_uur,
        sc.eind_uur
    FROM shift_codes sc
    JOIN werkposten w ON sc.werkpost_id = w.id
    WHERE w.naam = ?
    ORDER BY
        CASE sc.dag_type
            WHEN 'weekdag' THEN 1
            WHEN 'zaterdag' THEN 2
            WHEN 'zondag' THEN 3
        END,
        CASE sc.shift_type
            WHEN 'vroeg' THEN 1
            WHEN 'dag' THEN 2
            WHEN 'laat' THEN 3
            WHEN 'nacht' THEN 4
        END
""", (werkpost_naam,))

rows = cursor.fetchall()

if not rows:
    print(f"Geen codes gevonden voor '{werkpost_naam}'")
else:
    # Groepeer per dag_type
    current_dag_type = None
    for row in rows:
        dag_type = row['dag_type']

        if dag_type != current_dag_type:
            print(f"\n{dag_type.upper()}:")
            current_dag_type = dag_type

        print(f"  {row['shift_type']:8} | Code: {row['code']:6} | {row['start_uur']}-{row['eind_uur']}")

    print(f"\nTotaal: {len(rows)} codes")

conn.close()
print("\n" + "="*50 + "\n")
