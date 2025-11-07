"""
Database Versie Update: v0.6.21/22 -> v0.6.23
Vereenvoudigen vervaldatum overgedragen verlof: dag + maand -> één datum veld

Wijzigingen:
- HR Regels: "Vervaldatum overgedragen verlof (dag)" en "(maand)" samenvoegen
- Nieuwe regel: "Vervaldatum overgedragen verlof" met DD-MM format (bijv. "01-05" voor 1 mei)
- Default waarde: "01-05" (1 mei, Nederlandse standaard)
- Oude regels worden gearchiveerd (is_actief=0)
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

def upgrade():
    """Update database versie naar 0.6.23"""

    db_path = Path("data/planning.db")

    if not db_path.exists():
        print("[ERROR] Database niet gevonden: data/planning.db")
        sys.exit(1)

    print("\n=== Database Versie Update: v0.6.21/22 -> v0.6.23 ===\n")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Check huidige versie
        cursor.execute("SELECT version_number FROM db_metadata ORDER BY version_number DESC LIMIT 1")
        current_version = cursor.fetchone()

        if current_version:
            print(f"[INFO] Huidige database versie: {current_version[0]}")
        else:
            print("[ERROR] Geen versie gevonden in db_metadata")
            sys.exit(1)

        if current_version[0] == "0.6.23":
            print("[OK] Database is al op versie 0.6.23 - geen update nodig")
            conn.close()
            return

        # Zoek oude dag/maand regels
        print("[...] Zoeken naar oude vervaldatum regels...")

        cursor.execute("""
            SELECT id, naam, waarde
            FROM hr_regels
            WHERE naam IN (
                'Vervaldatum overgedragen verlof (dag)',
                'Vervaldatum overgedragen verlof (maand)'
            )
            AND is_actief = 1
        """)

        oude_regels = cursor.fetchall()

        dag_waarde = None
        maand_waarde = None
        oude_regel_ids = []

        for regel in oude_regels:
            oude_regel_ids.append(regel['id'])
            if 'dag' in regel['naam'].lower():
                dag_waarde = int(regel['waarde'])
                print(f"[GEVONDEN] Dag: {dag_waarde}")
            elif 'maand' in regel['naam'].lower():
                maand_waarde = int(regel['waarde'])
                print(f"[GEVONDEN] Maand: {maand_waarde}")

        # Bepaal nieuwe waarde
        if dag_waarde and maand_waarde:
            nieuwe_waarde = f"{dag_waarde:02d}-{maand_waarde:02d}"
            print(f"[INFO] Converteer naar nieuw format: {nieuwe_waarde}")
        else:
            nieuwe_waarde = "01-05"  # Default: 1 mei
            print(f"[INFO] Geen oude regels gevonden - gebruik default: {nieuwe_waarde} (1 mei)")

        # Deactiveer oude regels
        if oude_regel_ids:
            print(f"[...] Deactiveren van {len(oude_regel_ids)} oude regels...")

            now = datetime.now().isoformat()

            for regel_id in oude_regel_ids:
                cursor.execute("""
                    UPDATE hr_regels
                    SET is_actief = 0, actief_tot = ?
                    WHERE id = ?
                """, (now, regel_id))

            print(f"[OK] Oude regels gearchiveerd")

        # Check of nieuwe regel al bestaat
        cursor.execute("""
            SELECT id FROM hr_regels
            WHERE naam = 'Vervaldatum overgedragen verlof'
            AND is_actief = 1
        """)

        bestaande_regel = cursor.fetchone()

        if bestaande_regel:
            print("[OK] Nieuwe regel bestaat al - geen insert nodig")
        else:
            # Insert nieuwe regel
            print(f"[...] Aanmaken nieuwe regel met waarde: {nieuwe_waarde}...")

            cursor.execute("""
                INSERT INTO hr_regels (naam, waarde, eenheid, beschrijving, is_actief)
                VALUES (?, ?, ?, ?, 1)
            """, (
                'Vervaldatum overgedragen verlof',
                nieuwe_waarde,
                'datum',
                'Datum waarop overgedragen verlof vervalt (DD-MM format)'
            ))

            print("[OK] Nieuwe regel aangemaakt")

        # Update versie naar 0.6.23
        print("[...] Updaten database versie naar 0.6.23...")

        cursor.execute("""
            INSERT INTO db_metadata (version_number, migration_description)
            VALUES (?, ?)
        """, (
            "0.6.23",
            "HR Regels: vervaldatum overgedragen verlof vereenvoudigd naar één datum veld (DD-MM format)"
        ))

        conn.commit()
        print("[OK] Database versie updated naar 0.6.23")

        # Verificatie
        print("[...] Verificatie...")

        cursor.execute("SELECT version_number FROM db_metadata ORDER BY version_number DESC LIMIT 1")
        new_version = cursor.fetchone()

        cursor.execute("""
            SELECT naam, waarde, eenheid
            FROM hr_regels
            WHERE naam = 'Vervaldatum overgedragen verlof'
            AND is_actief = 1
        """)

        nieuwe_regel_check = cursor.fetchone()

        if new_version and new_version[0] == "0.6.23" and nieuwe_regel_check:
            print("[OK] Verificatie geslaagd")
            print("\n[SUCCESS] Database upgrade voltooid!")
            print("\nDatabase is nu compatible met Planning Tool v0.6.23")
            print("\nWijzigingen:")
            print(f"- Vervaldatum overgedragen verlof: {nieuwe_regel_check['waarde']} (eenheid: {nieuwe_regel_check['eenheid']})")
            if oude_regel_ids:
                print(f"- {len(oude_regel_ids)} oude regels (dag/maand) gearchiveerd")
            else:
                print("- Nieuwe regel toegevoegd met default waarde (1 mei)")
            print("\nGebruik: HR Regels Beheer scherm voor wijzigingen\n")
        else:
            print("[ERROR] Verificatie gefaald")
            conn.rollback()
            sys.exit(1)

    except sqlite3.Error as e:
        print(f"[ERROR] Database fout: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    upgrade()
