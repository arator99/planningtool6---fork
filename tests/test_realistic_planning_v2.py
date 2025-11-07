"""
Test: Realistic Planning Scenario v2
User 1: Vult maand in, commit na elke dag (realistischer)
User 2: Past shifts aan zodra ze zichtbaar zijn
"""
import sqlite3
import threading
import time
from pathlib import Path
from datetime import datetime, date, timedelta

def gebruiker1_vult_maand_in():
    """Gebruiker 1 vult maand in, commit na elke dag"""
    db_path = Path("data/planning.db")

    print(f"[Gebruiker 1] START - Maand invullen (commit per dag)...")
    start_time = time.time()

    try:
        conn = sqlite3.connect(db_path, timeout=15.0)
        cursor = conn.cursor()

        start_datum = date(2099, 1, 1)
        teamleden = [10, 11, 12]
        shift_codes = ['7101', '7201', '7301', 'VV', 'RX']

        total_shifts = 0
        errors = 0

        # Per dag invullen en committen
        for dag_nr in range(31):
            datum = start_datum + timedelta(days=dag_nr)
            datum_str = datum.isoformat()

            dag_shifts = 0

            for teamlid_id in teamleden:
                shift_code = shift_codes[dag_nr % len(shift_codes)]

                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO planning
                        (gebruiker_id, datum, shift_code, status, aangemaakt_op)
                        VALUES (?, ?, ?, 'concept', CURRENT_TIMESTAMP)
                    """, (teamlid_id, datum_str, shift_code))

                    dag_shifts += 1
                    time.sleep(0.02)  # 20ms per shift

                except sqlite3.Error as e:
                    errors += 1
                    print(f"[Gebruiker 1] ERROR: {e}")

            # COMMIT NA ELKE DAG
            try:
                conn.commit()
                total_shifts += dag_shifts
                if (dag_nr + 1) % 5 == 0:
                    print(f"[Gebruiker 1] Dag {dag_nr+1}/31 compleet ({total_shifts} shifts ingevoerd)")
            except sqlite3.Error as e:
                errors += 1
                print(f"[Gebruiker 1] COMMIT ERROR dag {dag_nr+1}: {e}")

        elapsed = time.time() - start_time
        print(f"[Gebruiker 1] KLAAR - {total_shifts} shifts in {elapsed:.2f}s ({errors} errors)")

        conn.close()
        return total_shifts, errors

    except Exception as e:
        print(f"[Gebruiker 1] FATAL ERROR: {e}")
        return 0, 1

def gebruiker2_past_shifts_aan(start_delay: float = 0.3):
    """Gebruiker 2 past bestaande shifts aan"""
    time.sleep(start_delay)

    db_path = Path("data/planning.db")

    print(f"[Gebruiker 2] START - Shifts aanpassen...")
    start_time = time.time()

    try:
        conn = sqlite3.connect(db_path, timeout=15.0)
        cursor = conn.cursor()

        shifts_updated = 0
        errors = 0
        iterations = 0

        # Blijf zoeken naar shifts tot user 1 klaar is (max 4 seconden)
        while time.time() - start_time < 4.0:
            iterations += 1

            try:
                # Haal shifts op die nog niet aangepast zijn
                cursor.execute("""
                    SELECT id, gebruiker_id, datum, shift_code
                    FROM planning
                    WHERE datum BETWEEN '2099-01-01' AND '2099-01-31'
                    AND status = 'concept'
                    AND (aangepast_op IS NULL OR aangepast_op = '')
                    ORDER BY datum
                    LIMIT 20
                """)

                shifts_to_update = cursor.fetchall()

                if not shifts_to_update:
                    # Geen nieuwe shifts, wacht even
                    time.sleep(0.1)
                    continue

                print(f"[Gebruiker 2] Gevonden {len(shifts_to_update)} nieuwe shifts, aanpassen...")

                for shift in shifts_to_update:
                    shift_id, gebruiker_id, datum, old_code = shift

                    new_code = '7201' if old_code == '7101' else '7301'

                    try:
                        cursor.execute("""
                            UPDATE planning
                            SET shift_code = ?, aangepast_op = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (new_code, shift_id))

                        shifts_updated += 1
                        time.sleep(0.03)  # 30ms per update

                    except sqlite3.Error as e:
                        errors += 1
                        print(f"[Gebruiker 2] UPDATE ERROR: {e}")
                        time.sleep(0.2)  # Extra wachttijd bij error

                # Commit na batch
                conn.commit()

                if shifts_updated % 20 == 0 and shifts_updated > 0:
                    print(f"[Gebruiker 2] {shifts_updated} shifts aangepast tot nu toe...")

            except sqlite3.Error as e:
                errors += 1
                print(f"[Gebruiker 2] QUERY ERROR (iteration {iterations}): {e}")
                time.sleep(0.2)

        elapsed = time.time() - start_time
        print(f"[Gebruiker 2] KLAAR - {shifts_updated} updates in {elapsed:.2f}s ({errors} errors, {iterations} iterations)")

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

def test_scenario(delay: float = 0.3):
    """Run het realistische scenario"""
    print("\n" + "="*70)
    print(f"REALISTIC PLANNING SCENARIO - v2")
    print(f"User 2 start delay: {delay}s na User 1")
    print("="*70)

    results = {}

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

    errors1 = errors2 = 0

    if 'user1' in results:
        inserts, errors1 = results['user1']
        print(f"Gebruiker 1: {inserts} shifts ingevoerd ({errors1} errors)")

    if 'user2' in results:
        updates, errors2 = results['user2']
        print(f"Gebruiker 2: {updates} shifts aangepast ({errors2} errors)")

    print(f"\nTotal elapsed: {overall_elapsed:.2f}s")

    total_errors = errors1 + errors2

    if total_errors == 0:
        print("\nSTATUS: SUCCESS - Geen database locking errors!")
    else:
        print(f"\nSTATUS: {total_errors} ERRORS - Check logs above")

    return total_errors

if __name__ == "__main__":
    print("\n" + "="*70)
    print("REALISTIC PLANNING SCENARIO TEST v2")
    print("="*70)
    print("Verbeteringen:")
    print("  - User 1 commit na elke dag (shifts direct zichtbaar)")
    print("  - User 2 zoekt continu naar nieuwe shifts om aan te passen")
    print()
    print("Database mode: DELETE (no WAL)")
    print("Timeout: 15 seconds")

    # Test met verschillende delays
    print("\n\n" + "="*70)
    print("TEST: User 2 start 0.3 seconde na User 1")
    print("="*70)
    errors = test_scenario(delay=0.3)

    cleanup()

    # Final summary
    print("\n\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"Total errors: {errors}")

    if errors == 0:
        print("\nCONCLUSIE: Database handelt concurrent gebruik perfect af!")
        print("- Geen 'database is locked' errors")
        print("- Beide gebruikers kunnen tegelijk werken")
        print("- SQLite busy timeout voorkomt blokkades")
    else:
        print("\nCONCLUSIE: Er zijn locking issues opgetreden.")
        print("Dit kan gebeuren bij:")
        print("  - Extreem hoge concurrent load")
        print("  - Lange transacties")
        print("  - Network drive latency")
