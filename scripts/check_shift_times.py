#!/usr/bin/env python3
"""Check shift codes en hun tijden"""
import sys
sys.path.insert(0, 'C:\\Users\\arato\\PycharmProjects\\planningstool 6 - claude')

from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()

print("=== SHIFT CODES (Werkposten) - Nacht en Vroeg ===")
cursor.execute("""
    SELECT sc.code, sc.shift_type, sc.dag_type, sc.start_uur, sc.eind_uur, w.naam as werkpost
    FROM shift_codes sc
    JOIN werkposten w ON sc.werkpost_id = w.id
    WHERE sc.shift_type IN ('nacht', 'vroeg')
    ORDER BY sc.shift_type, w.naam, sc.dag_type
""")

for row in cursor.fetchall():
    print(f"{row['shift_type']:8} {row['werkpost']:15} {row['dag_type']:10} {row['code']:6} {row['start_uur']:5}-{row['eind_uur']:5}")

print("\n=== SPECIALE CODES (verlof/ziekte die kunnen breken) ===")
cursor.execute("""
    SELECT code, naam, term, telt_als_werkdag, breekt_werk_reeks
    FROM speciale_codes
    WHERE term IN ('verlof', 'ziek')
    ORDER BY code
""")

for row in cursor.fetchall():
    print(f"{row['code']:6} {row['naam']:30} term={row['term']:20} breekt_reeks={row['breekt_werk_reeks']}")

conn.close()
