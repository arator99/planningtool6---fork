"""
Database migratie: Typetabel naar Versioned Systeem
Migreert oude typetabel naar nieuwe versioned structuur met concept/actief/archief status

Run dit script één keer om je database te upgraden naar v0.7.0
"""
import sqlite3
from pathlib import Path
from datetime import datetime


def migrate_typetabel_to_versioned():
    """Migreer huidige typetabel naar versioned systeem"""
    db_path = Path("data/planning.db")

    if not db_path.exists():
        print("❌ Database niet gevonden!")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Check of migratie al uitgevoerd is
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='typetabel_versies'
        """)
        if cursor.fetchone():
            print("✓ Migratie al uitgevoerd - typetabel_versies bestaat al")
            conn.close()
            return

        print("🔄 Start migratie typetabel naar versioned systeem...")

        # Maak nieuwe tabellen
        print("  → Maak typetabel_versies tabel...")
        cursor.execute("""
            CREATE TABLE typetabel_versies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                versie_naam TEXT NOT NULL,
                aantal_weken INTEGER NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('actief', 'concept', 'archief')),
                actief_vanaf DATE,
                actief_tot DATE,
                aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                laatste_wijziging TIMESTAMP,
                opmerking TEXT
            )
        """)

        print("  → Maak typetabel_data tabel...")
        cursor.execute("""
            CREATE TABLE typetabel_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                versie_id INTEGER NOT NULL,
                week_nummer INTEGER NOT NULL,
                dag_nummer INTEGER NOT NULL,
                shift_type TEXT,
                UNIQUE(versie_id, week_nummer, dag_nummer),
                FOREIGN KEY (versie_id) REFERENCES typetabel_versies(id) ON DELETE CASCADE
            )
        """)

        # Check of oude typetabel bestaat en data bevat
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='typetabel'
        """)

        if cursor.fetchone():
            print("  → Migreer bestaande typetabel data...")

            # Haal oude data op
            cursor.execute("SELECT * FROM typetabel ORDER BY week_nummer, dag_nummer")
            oude_data = cursor.fetchall()

            if oude_data:
                # Bepaal aantal weken uit data
                cursor.execute("SELECT MAX(week_nummer) as max_week FROM typetabel")
                max_week = cursor.fetchone()['max_week']
                aantal_weken = max_week if max_week else 6

                # Maak actieve versie aan
                cursor.execute("""
                    INSERT INTO typetabel_versies 
                    (versie_naam, aantal_weken, status, actief_vanaf, opmerking, laatste_wijziging)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "Huidige typetabel",
                    aantal_weken,
                    "actief",
                    "2024-01-01",
                    "Automatisch gemigreerd van oude typetabel structuur",
                    datetime.now().isoformat()
                ))
                versie_id = cursor.lastrowid

                print(f"  → Kopieer {len(oude_data)} regels naar nieuwe structuur...")

                # Kopieer alle data
                for row in oude_data:
                    cursor.execute("""
                        INSERT INTO typetabel_data (versie_id, week_nummer, dag_nummer, shift_type)
                        VALUES (?, ?, ?, ?)
                    """, (
                        versie_id,
                        row['week_nummer'],
                        row['dag_nummer'],
                        row['shift_type']
                    ))

                # Hernoem oude tabel (backup, niet verwijderen!)
                print("  → Hernoem oude typetabel naar typetabel_old_backup...")
                cursor.execute("ALTER TABLE typetabel RENAME TO typetabel_old_backup")

                print(f"  ✓ {len(oude_data)} regels gemigreerd naar versie '{versie_id}'")
            else:
                print("  ⚠️ Oude typetabel is leeg - geen data te migreren")
        else:
            print("  ℹ️ Geen oude typetabel gevonden - start met lege versioned structuur")

        conn.commit()
        print("\n✅ Migratie succesvol voltooid!")
        print("\n📊 Resultaat:")

        # Toon resultaat
        cursor.execute("SELECT * FROM typetabel_versies")
        versies = cursor.fetchall()

        if versies:
            for v in versies:
                print(f"  • Versie {v['id']}: '{v['versie_naam']}' ({v['aantal_weken']} weken, status: {v['status']})")
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM typetabel_data WHERE versie_id = ?
                """, (v['id'],))
                cnt = cursor.fetchone()['cnt']
                print(f"    └─ {cnt} data punten")
        else:
            print("  • Nog geen typetabel versies aangemaakt")

    except sqlite3.Error as e:
        print(f"\n❌ Fout tijdens migratie: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("TYPETABEL VERSIONED SYSTEEM MIGRATIE")
    print("=" * 60)
    print()

    migrate_typetabel_to_versioned()

    print()
    print("=" * 60)
    print("Je kan nu het TypetabelBeheerScreen gebruiken!")
    print("=" * 60)