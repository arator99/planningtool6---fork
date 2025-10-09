"""
Database migratie: Voeg is_variabel kolom toe aan feestdagen tabel
Run dit script één keer om je database te upgraden
"""
import sqlite3
from pathlib import Path


def migrate_feestdagen_type():
    """Voeg is_variabel kolom toe en markeer bestaande feestdagen correct"""

    db_path = Path("data/planning.db")

    if not db_path.exists():
        print("Database niet gevonden. Run eerst main.py om database aan te maken.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check of kolom al bestaat
    cursor.execute("PRAGMA table_info(feestdagen)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'is_variabel' in columns:
        print("✓ Kolom 'is_variabel' bestaat al")
        conn.close()
        return

    print("Toevoegen van 'is_variabel' kolom...")

    # Voeg kolom toe (default 0 = vast)
    cursor.execute("""
        ALTER TABLE feestdagen 
        ADD COLUMN is_variabel BOOLEAN DEFAULT 0
    """)

    # Markeer variabele feestdagen
    variabele_namen = ['Paasmaandag', 'O.H. Hemelvaart', 'Pinkstermaandag']

    for naam in variabele_namen:
        cursor.execute("""
            UPDATE feestdagen 
            SET is_variabel = 1 
            WHERE naam = ?
        """, (naam,))

    # Markeer extra feestdagen (niet in vaste of variabele lijst)
    vaste_namen = [
        'Nieuwjaar', 'Dag van de Arbeid', 'Nationale feestdag',
        'O.L.V. Hemelvaart', 'Allerheiligen', 'Wapenstilstand', 'Kerstmis'
    ]

    alle_bekende = vaste_namen + variabele_namen
    placeholders = ','.join('?' * len(alle_bekende))

    cursor.execute(f"""
        UPDATE feestdagen 
        SET is_variabel = 1 
        WHERE naam NOT IN ({placeholders})
    """, alle_bekende)

    conn.commit()

    # Verificatie
    cursor.execute("SELECT naam, is_variabel FROM feestdagen ORDER BY datum")
    print("\nFeestdagen na migratie:")
    for naam, is_variabel in cursor.fetchall():
        type_str = "Variabel/Extra" if is_variabel else "Vast"
        print(f"  - {naam}: {type_str}")

    conn.close()
    print("\n✓ Migratie succesvol afgerond!")


if __name__ == '__main__':
    migrate_feestdagen_type()