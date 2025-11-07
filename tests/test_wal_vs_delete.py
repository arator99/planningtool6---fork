"""
Test: WAL vs DELETE mode comparison
Heavy load test met simultane readers en writers
"""
import sqlite3
import threading
import time
from pathlib import Path
from datetime import datetime
import statistics

results = {
    'reads': [],
    'writes': [],
    'errors': []
}
results_lock = threading.Lock()

def reader_task(reader_id: int, duration: int = 5):
    """Simuleer een reader die continu data leest"""
    db_path = Path("data/planning.db")
    read_count = 0
    start_time = time.time()

    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()

        while time.time() - start_time < duration:
            try:
                cursor.execute("SELECT COUNT(*) FROM planning")
                count = cursor.fetchone()[0]
                read_count += 1
                time.sleep(0.01)  # Kleine pauze tussen reads
            except sqlite3.OperationalError as e:
                with results_lock:
                    results['errors'].append(f"Reader {reader_id}: {e}")

        conn.close()

        with results_lock:
            results['reads'].append(read_count)

        print(f"[Reader {reader_id}] Completed {read_count} reads in {duration}s")

    except Exception as e:
        print(f"[Reader {reader_id}] ERROR: {e}")

def writer_task(writer_id: int, duration: int = 5):
    """Simuleer een writer die continu data schrijft"""
    db_path = Path("data/planning.db")
    write_count = 0
    start_time = time.time()

    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()

        while time.time() - start_time < duration:
            try:
                datum = f"2099-99-{writer_id:02d}"
                cursor.execute("""
                    INSERT OR REPLACE INTO planning (gebruiker_id, datum, shift_code, status)
                    VALUES (?, ?, ?, ?)
                """, (1, datum, f"W{writer_id}", "concept"))
                conn.commit()
                write_count += 1
                time.sleep(0.05)  # Langzamer dan reads
            except sqlite3.OperationalError as e:
                with results_lock:
                    results['errors'].append(f"Writer {writer_id}: {e}")

        conn.close()

        with results_lock:
            results['writes'].append(write_count)

        print(f"[Writer {writer_id}] Completed {write_count} writes in {duration}s")

    except Exception as e:
        print(f"[Writer {writer_id}] ERROR: {e}")

def run_load_test(num_readers: int = 3, num_writers: int = 2, duration: int = 5):
    """Run load test met multiple readers en writers"""
    global results
    results = {'reads': [], 'writes': [], 'errors': []}

    print(f"\nStarting {num_readers} readers + {num_writers} writers for {duration}s...")

    threads = []

    # Start readers
    for i in range(1, num_readers + 1):
        thread = threading.Thread(target=reader_task, args=(i, duration))
        threads.append(thread)
        thread.start()

    # Start writers
    for i in range(1, num_writers + 1):
        thread = threading.Thread(target=writer_task, args=(i, duration))
        threads.append(thread)
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join()

    return results

def print_results(results, mode_name):
    """Print test results"""
    print("\n" + "="*60)
    print(f"RESULTS: {mode_name}")
    print("="*60)

    if results['reads']:
        total_reads = sum(results['reads'])
        avg_reads = statistics.mean(results['reads'])
        print(f"Total Reads:  {total_reads}")
        print(f"Avg per Reader: {avg_reads:.1f}")
        print(f"Reads/sec:    {total_reads/5:.1f}")

    if results['writes']:
        total_writes = sum(results['writes'])
        avg_writes = statistics.mean(results['writes'])
        print(f"\nTotal Writes: {total_writes}")
        print(f"Avg per Writer: {avg_writes:.1f}")
        print(f"Writes/sec:   {total_writes/5:.1f}")

    if results['errors']:
        print(f"\nErrors: {len(results['errors'])}")
        for error in results['errors'][:5]:  # Show first 5
            print(f"  - {error}")
        if len(results['errors']) > 5:
            print(f"  ... and {len(results['errors']-5)} more")
    else:
        print("\nErrors: 0 (Perfect!)")

def switch_mode(mode: str):
    """Switch database journal mode"""
    db_path = Path("data/planning.db")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA journal_mode={mode}")
        new_mode = cursor.fetchone()[0]

        conn.close()
        return new_mode.upper()
    except Exception as e:
        print(f"ERROR switching mode: {e}")
        return None

def cleanup():
    """Cleanup test data"""
    db_path = Path("data/planning.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM planning WHERE datum LIKE '2099-99-%'")
        conn.commit()
        conn.close()
    except:
        pass

if __name__ == "__main__":
    print("\n" + "="*60)
    print("WAL vs DELETE MODE COMPARISON TEST")
    print("="*60)
    print("Heavy load: 3 readers + 2 writers for 5 seconds each mode")
    print()

    # Test 1: DELETE mode
    print("\n[TEST 1] Switching to DELETE mode...")
    mode = switch_mode("DELETE")
    print(f"Current mode: {mode}")
    time.sleep(0.5)

    results_delete = run_load_test(num_readers=3, num_writers=2, duration=5)
    print_results(results_delete, "DELETE MODE")

    time.sleep(1)

    # Test 2: WAL mode
    print("\n\n[TEST 2] Switching to WAL mode...")
    mode = switch_mode("WAL")
    print(f"Current mode: {mode}")
    time.sleep(0.5)

    results_wal = run_load_test(num_readers=3, num_writers=2, duration=5)
    print_results(results_wal, "WAL MODE")

    # Comparison
    print("\n" + "="*60)
    print("COMPARISON")
    print("="*60)

    if results_delete['reads'] and results_wal['reads']:
        delete_reads = sum(results_delete['reads'])
        wal_reads = sum(results_wal['reads'])
        improvement = ((wal_reads - delete_reads) / delete_reads) * 100
        print(f"Read throughput:  {improvement:+.1f}% with WAL")

    if results_delete['writes'] and results_wal['writes']:
        delete_writes = sum(results_delete['writes'])
        wal_writes = sum(results_wal['writes'])
        improvement = ((wal_writes - delete_writes) / delete_writes) * 100
        print(f"Write throughput: {improvement:+.1f}% with WAL")

    delete_errors = len(results_delete['errors'])
    wal_errors = len(results_wal['errors'])
    print(f"\nErrors: DELETE={delete_errors}, WAL={wal_errors}")

    # Cleanup
    cleanup()

    print("\n" + "="*60)
    print("RECOMMENDATION")
    print("="*60)
    print("WAL mode is enabled and recommended for:")
    print("  - Better concurrent read/write performance")
    print("  - Fewer 'database is locked' errors")
    print("  - Production multi-user environments")
    print("\nNote: May not work well on network drives!")
