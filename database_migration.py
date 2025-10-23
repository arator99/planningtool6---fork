"""
Database migratie script
Voegt UUID en timestamp kolommen toe aan bestaande database
Run dit script één keer om je database te upgraden
"""

import sqlite3
import uuid
from pathlib import Path


def migrate_database():
    """Upgrade database schema met nieuwe kolommen"""

    db_path = Path("data/planning.db")

    if not db_path.exists():
        print("Database niet gevonden. Run eerst main.py om database aan te maken.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Start database migratie...")

    try:
        # Check of kolommen al bestaan
        cursor.execute("PRAGMA table_info(gebruikers)")
        columns = [col[1] for col in cursor.fetchall()]

        # Voeg nieuwe kolommen toe als ze nog niet bestaan
        if 'gebruiker_uuid' not in columns:
            print("- Toevoegen gebruiker_uuid kolom...")
            cursor.execute("""
                ALTER TABLE gebruikers 
                ADD COLUMN gebruiker_uuid TEXT
            """)

            # Genereer UUID's voor bestaande gebruikers
            cursor.execute("SELECT id FROM gebruikers")
            gebruiker_ids = cursor.fetchall()

            for (gebruiker_id,) in gebruiker_ids:
                nieuwe_uuid = str(uuid.uuid4())
                cursor.execute("""
                    UPDATE gebruikers 
                    SET gebruiker_uuid = ? 
                    WHERE id = ?
                """, (nieuwe_uuid, gebruiker_id))

            # Maak kolom NOT NULL en UNIQUE
            cursor.execute("""
                CREATE UNIQUE INDEX idx_gebruiker_uuid 
                ON gebruikers(gebruiker_uuid)
            """)
            print("  ✓ gebruiker_uuid kolom toegevoegd en UUID's gegenereerd")

        if 'aangemaakt_op' not in columns:
            print("- Toevoegen aangemaakt_op kolom...")
            cursor.execute("""
                ALTER TABLE gebruikers 
                ADD COLUMN aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            print("  ✓ aangemaakt_op kolom toegevoegd")

        if 'gedeactiveerd_op' not in columns:
            print("- Toevoegen gedeactiveerd_op kolom...")
            cursor.execute("""
                ALTER TABLE gebruikers 
                ADD COLUMN gedeactiveerd_op TIMESTAMP
            """)
            print("  ✓ gedeactiveerd_op kolom toegevoegd")

        if 'laatste_login' not in columns:
            print("- Toevoegen laatste_login kolom...")
            cursor.execute("""
                ALTER TABLE gebruikers 
                ADD COLUMN laatste_login TIMESTAMP
            """)
            print("  ✓ laatste_login kolom toegevoegd")

        # Check planning_maanden tabel
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='planning_maanden'
        """)

        if not cursor.fetchone():
            print("- Aanmaken planning_maanden tabel...")
            cursor.execute("""
                CREATE TABLE planning_maanden (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jaar INTEGER NOT NULL,
                    maand INTEGER NOT NULL,
                    status TEXT DEFAULT 'concept' 
                           CHECK(status IN ('concept', 'gepubliceerd')),
                    gepubliceerd_op TIMESTAMP,
                    gepubliceerd_door INTEGER REFERENCES gebruikers(id),
                    UNIQUE(jaar, maand)
                )
            """)
            print("  ✓ planning_maanden tabel aangemaakt")

        conn.commit()
        print("\n✅ Database migratie succesvol afgerond!")
        print("\nNieuwe kolommen in gebruikers tabel:")
        print("  - gebruiker_uuid (UNIQUE)")
        print("  - aangemaakt_op")
        print("  - gedeactiveerd_op")
        print("  - laatste_login")
        print("\nNieuwe tabel:")
        print("  - planning_maanden")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Fout bij migratie: {str(e)}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()