# verify_planning_editor_readiness.py
"""
Verificatie script: Check of alles klaar is voor Planning Editor
"""
import sqlite3
from pathlib import Path

db_path = Path("data/planning.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print("PLANNING EDITOR READINESS CHECK")
print("=" * 60)

# 1. Check planning tabel
print("\n1. PLANNING TABEL:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='planning'")
if cursor.fetchone():
    print("   ✓ Planning tabel bestaat")
    cursor.execute("PRAGMA table_info(planning)")
    cols = [row['name'] for row in cursor.fetchall()]
    print(f"   Kolommen: {', '.join(cols)}")
    cursor.execute("SELECT COUNT(*) as count FROM planning")
    count = cursor.fetchone()['count']
    print(f"   Aantal entries: {count}")
else:
    print("   ✗ Planning tabel NIET gevonden!")

# 2. Check shift_codes
print("\n2. SHIFT CODES:")
cursor.execute("""
    SELECT COUNT(*) as count 
    FROM shift_codes sc
    JOIN werkposten w ON sc.werkpost_id = w.id
    WHERE w.is_actief = 1
""")
count = cursor.fetchone()['count']
print(f"   Shift codes (actieve werkposten): {count}")

if count > 0:
    cursor.execute("""
        SELECT w.naam, COUNT(*) as count
        FROM shift_codes sc
        JOIN werkposten w ON sc.werkpost_id = w.id
        WHERE w.is_actief = 1
        GROUP BY w.naam
    """)
    for row in cursor.fetchall():
        print(f"   - {row['naam']}: {row['count']} codes")

# 3. Check speciale codes
print("\n3. SPECIALE CODES:")
cursor.execute("SELECT COUNT(*) as count FROM speciale_codes")
count = cursor.fetchone()['count']
print(f"   Speciale codes: {count}")

if count > 0:
    cursor.execute("SELECT code, naam FROM speciale_codes ORDER BY code LIMIT 10")
    codes = [f"{row['code']} ({row['naam']})" for row in cursor.fetchall()]
    print(f"   Voorbeelden: {', '.join(codes)}")

# 4. Check gebruikers (excl admin, excl reserves)
print("\n4. GEBRUIKERS (voor planning):")
cursor.execute("""
    SELECT COUNT(*) as count 
    FROM gebruikers 
    WHERE is_actief = 1 
      AND gebruikersnaam != 'admin'
      AND is_reserve = 0
""")
count = cursor.fetchone()['count']
print(f"   Actieve gebruikers (geen admin/reserves): {count}")

if count > 0:
    cursor.execute("""
        SELECT volledige_naam, startweek_typedienst
        FROM gebruikers
        WHERE is_actief = 1
          AND gebruikersnaam != 'admin'
          AND is_reserve = 0
        ORDER BY volledige_naam
        LIMIT 5
    """)
    for row in cursor.fetchall():
        sw = row['startweek_typedienst'] or '?'
        print(f"   - {row['volledige_naam']} (startweek: {sw})")

# 5. Check typetabel
print("\n5. TYPETABEL:")
cursor.execute("SELECT COUNT(*) as count FROM typetabel")
count = cursor.fetchone()['count']
print(f"   Typetabel entries: {count}")

if count == 42:  # 6 weken x 7 dagen
    print("   ✓ Volledig (6 weken x 7 dagen)")
else:
    print(f"   ⚠ Verwacht 42 entries (6x7), gevonden {count}")

# 6. Check feestdagen (voor huidige maand)
from datetime import datetime
huidige_jaar = datetime.now().year
huidige_maand = datetime.now().month

print(f"\n6. FEESTDAGEN ({huidige_jaar}):")
cursor.execute("""
    SELECT COUNT(*) as count 
    FROM feestdagen 
    WHERE strftime('%Y', datum) = ?
""", (str(huidige_jaar),))
count = cursor.fetchone()['count']
print(f"   Feestdagen dit jaar: {count}")

if count > 0:
    cursor.execute("""
        SELECT datum, naam 
        FROM feestdagen 
        WHERE strftime('%Y', datum) = ?
        ORDER BY datum
    """, (str(huidige_jaar),))
    for row in cursor.fetchall():
        print(f"   - {row['datum']}: {row['naam']}")

# 7. Samenvatting
print("\n" + "=" * 60)
print("SAMENVATTING:")

all_good = True
if count == 0:
    print("⚠ Geen shift codes - voeg werkpost toe met codes")
    all_good = False

cursor.execute("""
    SELECT COUNT(*) as count 
    FROM gebruikers 
    WHERE is_actief = 1 
      AND gebruikersnaam != 'admin'
      AND is_reserve = 0
""")
if cursor.fetchone()['count'] == 0:
    print("⚠ Geen gebruikers - voeg teamleden toe")
    all_good = False

cursor.execute("SELECT COUNT(*) as count FROM typetabel")
if cursor.fetchone()['count'] != 42:
    print("⚠ Typetabel incompleet")
    all_good = False

if all_good:
    print("✓ ALLES KLAAR VOOR PLANNING EDITOR!")
else:
    print("⚠ Los bovenstaande punten eerst op")

print("=" * 60)

conn.close()