"""
Test: Realistic Planning Scenario
User 1: Vult hele maand aan shifts in (30 dagen x 3 teamleden)
User 2: Begint kort daarna dezelfde shifts aan te passen
"""
import sqlite3
import threading
import time
from pathlib import Path
from datetime import datetime, date, timedelta

def gebruiker1_vult_maand_in():
    """Gebruiker 1 vult een hele maand aan planning in"""
    db_path = Path("data/planning.db")
    user_id = 1

    print(f"[Gebruiker 1] START - Maand invullen...")
    start_time = time.time()

    try:
        conn = sqlite3.connect(db_path, timeout=15.0)
        cursor = conn.cursor()

        # Maand: januari 2099
        start_datum = date(2099, 1, 1)

        # 3 teamleden, 31 dagen = 93 shifts
        teamleden = [10, 11, 12]  # Gebruiker IDs
        shift_codes = ['7101', '7201', '7301', 'VV', 'RX']  # Vroeg, Laat, Nacht, Verlof, Rust

        shifts_inserted = 0
        errors = 0

        print(f"[Gebruiker 1] Begin INSERT van ~93 shifts (3 teamleden x 31 dagen)...")

        for dag_nr in range(31):
            datum = start_datum + timedelta(days=dag_nr)
            datum_str = datum.isoformat()

            for teamlid_id in teamleden:
                # Willekeurig shift code (simuleer verschillende shifts)
                shift_code = shift_codes[dag_nr % len(shift_codes)]

                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO planning
                        (gebruiker_id, datum, shift_code, status, aangemaakt_op)
                        VALUES (?, ?, ?, 'concept', CURRENT_TIMESTAMP)
                    """, (teamlid_id, datum_str, shift_code))

                    shifts_inserted += 1

                    # Simuleer denktijd tussen shifts (realistische snelheid)
                    time.sleep(0.02)  # 20ms per shift = ~50 shifts/sec

                    # Progress indicator
                    if shifts_inserted % 10 == 0:
                        print(f"[Gebruiker 1] {shifts_inserted}/93 shifts ingevoerd...")

                except sqlite3.Error as e:
                    errors += 1
                    print(f"[Gebruiker 1] ERROR op shift {shifts_inserted+1}: {e}")

        print(f"[Gebruiker 1] Committing {shifts_inserted} shifts...")
        conn.commit()

        elapsed = time.time() - start_time
        print(f"[Gebruiker 1] KLAAR - {shifts_inserted} shifts in {elapsed:.2f}s ({errors} errors)")

        conn.close()
        return shifts_inserted, errors

    except Exception as e:
        print(f"[Gebruiker 1] FATAL ERROR: {e}")
        return 0, 1

def gebruiker2_past_shifts_aan(start_delay: float = 1.0):
    """Gebruiker 2 past bestaande shifts aan (kort na user 1 start)"""
    db_path = Path("data/planning.db")

    # Wacht tot user 1 begonnen is
    time.sleep(start_delay)

    print(f"[Gebruiker 2] START - Shifts aanpassen (na {start_delay}s delay)...")
    start_time = time.time()

    try:
        conn = sqlite3.connect(db_path, timeout=15.0)
        cursor = conn.cursor()

        shifts_updated = 0
        errors = 0

        # Haal alle concept shifts op van januari 2099
        print(f"[Gebruiker 2] Selecteren shifts om aan te passen...")
        cursor.execute("""
            SELECT id, gebruiker_id, datum, shift_code
            FROM planning
            WHERE datum BETWEEN '2099-01-01' AND '2099-01-31'
            AND status = 'concept'
            ORDER BY datum
        """)

        shifts_to_update = cursor.fetchall()
        total_shifts = len(shifts_to_update)

        print(f"[Gebruiker 2] Gevonden {total_shifts} shifts, begin aanpassen...")

        for shift in shifts_to_update:
            shift_id, gebruiker_id, datum, old_code = shift

            # Pas shift code aan (bijv. van vroeg naar laat)
            new_code = '7201' if old_code == '7101' else '7301'

            try:
                cursor.execute("""
                    UPDATE planning
                    SET shift_code = ?, aangepast_op = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_code, shift_id))

                shifts_updated += 1

                # Simuleer denktijd tussen updates
                time.sleep(0.03)  # 30ms per update = ~33 updates/sec

                # Progress indicator
                if shifts_updated % 10 == 0:
                    print(f"[Gebruiker 2] {shifts_updated}/{total_shifts} shifts aangepast...")

            except sqlite3.Error as e:
                errors += 1
                print(f"[Gebruiker 2] ERROR op shift {shift_id}: {e}")

        print(f"[Gebruiker 2] Committing {shifts_updated} updates...")
        conn.commit()

        elapsed = time.time() - start_time
        print(f"[Gebruiker 2] KLAAR - {shifts_updated} updates in {elapsed:.2f}s ({errors} errors)")

        conn.close()
        return shifts_updated, errors

    except Exception as e:
        print(f"[Gebruiker 2] FATAL ERROR: {e}")
        return 0, 1

def cleanup():
    """Verwijder test data"""
    print("\n[CLEANUP] Verwijderen test data...")
    db_path = Path("data/planning.db")

    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM planning WHERE datum BETWEEN '2099-01-01' AND '2099-01-31'")
        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        print(f"[CLEANUP] {deleted} test shifts verwijderd")

    except Exception as e:
        print(f"[CLEANUP] ERROR: {e}")

def test_scenario(delay: float = 1.0):
    """Run het realistische scenario"""
    print("\n" + "="*70)
    print(f"REALISTIC PLANNING SCENARIO TEST")
    print(f"User 2 start delay: {delay}s na User 1")
    print("="*70)

    results = {}

    # Start beide gebruikers
    thread1 = threading.Thread(target=lambda: results.update({'user1': gebruiker1_vult_maand_in()}))
    thread2 = threading.Thread(target=lambda: results.update({'user2': gebruiker2_past_shifts_aan(delay)}))

    overall_start = time.time()

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    overall_elapsed = time.time() - overall_start

    # Results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)

    if 'user1' in results:
        inserts, errors1 = results['user1']
        print(f"Gebruiker 1: {inserts} shifts ingevoerd ({errors1} errors)")

    if 'user2' in results:
        updates, errors2 = results['user2']
        print(f"Gebruiker 2: {updates} shifts aangepast ({errors2} errors)")

    print(f"\nTotal elapsed: {overall_elapsed:.2f}s")

    total_errors = (errors1 if 'user1' in results else 0) + (errors2 if 'user2' in results else 0)

    if total_errors == 0:
        print("\nSTATUS: SUCCESS - Geen database locking errors!")
    else:
        print(f"\nSTATUS: {total_errors} ERRORS - Check logs above")

    return total_errors

if __name__ == "__main__":
    print("\n" + "="*70)
    print("REALISTIC PLANNING SCENARIO TEST")
    print("="*70)
    print("Scenario: 2 gebruikers werken tegelijk aan planning")
    print("  - Gebruiker 1: Vult hele maand in (93 shifts)")
    print("  - Gebruiker 2: Past shifts aan zodra ze verschijnen")
    print()
    print("Database mode: DELETE (WAL disabled)")
    print("Timeout: 15 seconds")

    # Test 1: User 2 start na 1 seconde
    print("\n\n" + "="*70)
    print("TEST 1: User 2 start 1 seconde na User 1")
    print("="*70)
    errors1 = test_scenario(delay=1.0)

    cleanup()
    time.sleep(1)

    # Test 2: User 2 start bijna gelijk (0.5 sec)
    print("\n\n" + "="*70)
    print("TEST 2: User 2 start 0.5 seconde na User 1 (meer overlap)")
    print("="*70)
    errors2 = test_scenario(delay=0.5)

    cleanup()

    # Final summary
    print("\n\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"Test 1 (1s delay): {errors1} errors")
    print(f"Test 2 (0.5s delay): {errors2} errors")

    if errors1 == 0 and errors2 == 0:
        print("\nCONCLUSIE: Database handelt concurrent gebruik goed af!")
        print("SQLite busy timeout (5-15s) voorkomt locking errors.")
    else:
        print("\nCONCLUSIE: Er zijn locking issues opgetreden.")
        print("Overweeg langere timeout of optimize workflow.")
