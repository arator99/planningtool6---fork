"""
Test: Concurrent Database Access v2
Verbeterde test met proper error handling en rollback
"""
import sqlite3
import threading
import time
from pathlib import Path
from datetime import datetime
import random

def write_to_db(user_id: int, delay: float = 0):
    """Simuleer een database write operatie met proper error handling"""
    db_path = Path("data/planning.db")
    conn = None

    try:
        print(f"[User {user_id}] Connecting to database...")
        conn = sqlite3.connect(db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Lees huidige data
        print(f"[User {user_id}] Reading data...")
        cursor.execute("SELECT COUNT(*) FROM planning")
        count = cursor.fetchone()[0]
        print(f"[User {user_id}] Current planning records: {count}")

        # Simuleer denktijd (binnen transaction)
        if delay > 0:
            print(f"[User {user_id}] Processing... (sleep {delay}s)")
            time.sleep(delay)

        # Unieke datum per user
        datum = f"2099-12-{user_id:02d}"

        # Probeer iets te schrijven
        print(f"[User {user_id}] Attempting INSERT (datum={datum})...")
        cursor.execute("""
            INSERT INTO planning (gebruiker_id, datum, shift_code, status)
            VALUES (?, ?, ?, ?)
        """, (1, datum, f"TEST{user_id}", "concept"))

        print(f"[User {user_id}] Committing...")
        conn.commit()
        print(f"[User {user_id}] SUCCESS - Write committed")

    except sqlite3.OperationalError as e:
        print(f"[User {user_id}] ERROR - OPERATIONAL: {e}")
        if conn:
            conn.rollback()
    except sqlite3.IntegrityError as e:
        print(f"[User {user_id}] ERROR - INTEGRITY: {e}")
        if conn:
            conn.rollback()
    except sqlite3.DatabaseError as e:
        print(f"[User {user_id}] ERROR - DATABASE: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"[User {user_id}] ERROR - UNEXPECTED: {type(e).__name__}: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print(f"[User {user_id}] Connection closed")

def test_sequential():
    """Test: Sequentieel (geen concurrency)"""
    print("\n" + "="*60)
    print("TEST 1: Sequential Access (Baseline)")
    print("="*60)

    write_to_db(1)
    print()
    write_to_db(2)

def test_concurrent_fast():
    """Test: Beide users schrijven tegelijk (snel)"""
    print("\n" + "="*60)
    print("TEST 2: Concurrent Access (No Delay)")
    print("="*60)

    thread1 = threading.Thread(target=write_to_db, args=(3, 0))
    thread2 = threading.Thread(target=write_to_db, args=(4, 0))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

def test_concurrent_slow():
    """Test: User 1 houdt connectie lang vast, User 2 moet wachten"""
    print("\n" + "="*60)
    print("TEST 3: Concurrent Access (User 1 processes 2 seconds)")
    print("="*60)

    print("[INFO] User 5 will process for 2 seconds")
    print("[INFO] User 6 will try to write immediately")
    print()

    thread1 = threading.Thread(target=write_to_db, args=(5, 2))
    thread2 = threading.Thread(target=write_to_db, args=(6, 0))

    thread1.start()
    time.sleep(0.2)  # Zorg dat thread1 eerst start
    thread2.start()

    thread1.join()
    thread2.join()

def test_many_concurrent():
    """Test: Veel users tegelijk (stress test)"""
    print("\n" + "="*60)
    print("TEST 4: Many Concurrent Users (5 users simultaneously)")
    print("="*60)

    threads = []
    for i in range(7, 12):  # Users 7-11
        thread = threading.Thread(target=write_to_db, args=(i, random.uniform(0, 1)))
        threads.append(thread)

    # Start alle threads
    for thread in threads:
        thread.start()
        time.sleep(0.05)  # Kleine delay tussen starts

    # Wacht tot alle threads klaar zijn
    for thread in threads:
        thread.join()

def cleanup():
    """Verwijder test data"""
    print("\n" + "="*60)
    print("CLEANUP: Removing test data")
    print("="*60)

    try:
        db_path = Path("data/planning.db")
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM planning WHERE datum LIKE '2099-%'")
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"SUCCESS - Removed {deleted} test records")
    except Exception as e:
        print(f"ERROR - Cleanup failed: {e}")

def check_wal_mode():
    """Check of database in WAL mode is"""
    print("\n" + "="*60)
    print("DATABASE CONFIGURATION CHECK")
    print("="*60)

    try:
        db_path = Path("data/planning.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check journal mode
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        print(f"Journal Mode: {journal_mode}")

        # Check locking mode
        cursor.execute("PRAGMA locking_mode")
        locking_mode = cursor.fetchone()[0]
        print(f"Locking Mode: {locking_mode}")

        # Check timeout
        cursor.execute("PRAGMA busy_timeout")
        timeout = cursor.fetchone()[0]
        print(f"Busy Timeout: {timeout}ms")

        conn.close()

        if journal_mode.upper() != 'WAL':
            print("\n[WARNING] Database is NOT in WAL mode!")
            print("  WAL mode allows multiple readers + 1 writer concurrently")
            print("  Without WAL, only 1 connection can write at a time")
            print("\n  To enable WAL mode, run:")
            print("    PRAGMA journal_mode=WAL;")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CONCURRENT DATABASE ACCESS TEST v2")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Database: data/planning.db")
    print(f"SQLite timeout: 10 seconds")

    # Check configuration
    check_wal_mode()

    # Run tests
    test_sequential()
    time.sleep(0.5)

    test_concurrent_fast()
    time.sleep(0.5)

    test_concurrent_slow()
    time.sleep(0.5)

    test_many_concurrent()
    time.sleep(0.5)

    # Cleanup
    cleanup()

    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)
    print("\nCONCLUSIONS:")
    print("- Check for 'database is locked' errors above")
    print("- SQLite default mode allows only 1 writer at a time")
    print("- Consider enabling WAL mode for better concurrency")
    print("- Network drives make locking worse (slower)")
