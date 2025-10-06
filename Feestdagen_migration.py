import sqlite3
from pathlib import Path


def migrate_feestdagen():
    db_path = Path("data/planning.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check welke kolommen bestaan
    cursor.execute("PRAGMA table_info(feestdagen)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'type' not in columns:
        cursor.execute("ALTER TABLE feestdagen ADD COLUMN type TEXT DEFAULT 'vast'")

    if 'is_ingevuld' not in columns:
        cursor.execute("ALTER TABLE feestdagen ADD COLUMN is_ingevuld BOOLEAN DEFAULT 1")

    if 'jaar' not in columns:
        cursor.execute("ALTER TABLE feestdagen ADD COLUMN jaar INTEGER")
        # Extract jaar uit datum
        cursor.execute("""
            UPDATE feestdagen 
            SET jaar = CAST(substr(datum, 1, 4) AS INTEGER)
        """)

    conn.commit()
    conn.close()
    print("Feestdagen tabel gemigreerd")


if __name__ == "__main__":
    migrate_feestdagen()