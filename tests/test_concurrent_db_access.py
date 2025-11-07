"""
Test: Concurrent Database Access
Simuleert 2 gebruikers die tegelijk naar de database schrijven
"""
import sqlite3
import threading
import time
from pathlib import Path
from datetime import datetime

def write_to_db(user_id: int, delay: float = 0):
    """Simuleer een database write operatie"""
    db_path = Path("data/planning.db")

    try:
        print(f"[User {user_id}] Connecting to database...")
        conn = sqlite3.connect(db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Simuleer een langere transactie
        print(f"[User {user_id}] Starting transaction...")
        cursor.execute("BEGIN TRANSACTION")

        # Lees huidige data
        cursor.execute("SELECT COUNT(*) FROM planning")
        count = cursor.fetchone()[0]
        print(f"[User {user_id}] Current planning records: {count}")

        # Simuleer denktijd
        if delay > 0:
            print(f"[User {user_id}] Processing... (sleep {delay}s)")
            time.sleep(delay)

        # Probeer iets te schrijven
        print(f"[User {user_id}] Attempting INSERT...")
        cursor.execute("""
            INSERT INTO planning (gebruiker_id, datum, shift_code, status)
            VALUES (?, ?, ?, ?)
        """, (1, f"2025-01-{10 + user_id:02d}", f"TEST{user_id}", "concept"))

        print(f"[User {user_id}] Committing...")
        conn.commit()
        print(f"[User {user_id}] SUCCESS - Write committed")

        conn.close()

    except sqlite3.OperationalError as e:
        print(f"[User {user_id}] ERROR - OPERATIONAL: {e}")
    except sqlite3.DatabaseError as e:
        print(f"[User {user_id}] ERROR - DATABASE: {e}")
    except Exception as e:
        print(f"[User {user_id}] ERROR - UNEXPECTED: {type(e).__name__}: {e}")

def test_sequential():
    """Test: Sequentieel (geen concurrency)"""
    print("\n" + "="*60)
    print("TEST 1: Sequential Access (Baseline)")
    print("="*60)

    write_to_db(1)
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
    """Test: User 1 houdt lock lang vast, User 2 moet wachten"""
    print("\n" + "="*60)
    print("TEST 3: Concurrent Access (User 1 holds lock 3 seconds)")
    print("="*60)

    thread1 = threading.Thread(target=write_to_db, args=(5, 3))  # 3 sec delay
    thread2 = threading.Thread(target=write_to_db, args=(6, 0))   # No delay

    print("[INFO] User 5 will hold transaction for 3 seconds")
    print("[INFO] User 6 will try to write immediately")

    thread1.start()
    time.sleep(0.1)  # Zorg dat thread1 eerst start
    thread2.start()

    thread1.join()
    thread2.join()

def test_concurrent_very_slow():
    """Test: User 1 houdt lock te lang vast (> timeout)"""
    print("\n" + "="*60)
    print("TEST 4: Concurrent Access (User 1 holds lock > timeout)")
    print("="*60)

    thread1 = threading.Thread(target=write_to_db, args=(7, 7))  # 7 sec > 5 sec timeout
    thread2 = threading.Thread(target=write_to_db, args=(8, 0))

    print("[INFO] User 7 will hold transaction for 7 seconds (> 5 sec timeout)")
    print("[INFO] User 8 will try to write immediately and should timeout")

    thread1.start()
    time.sleep(0.1)
    thread2.start()

    thread1.join()
    thread2.join()

def cleanup():
    """Verwijder test data"""
    print("\n" + "="*60)
    print("CLEANUP: Removing test data")
    print("="*60)

    try:
        db_path = Path("data/planning.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM planning WHERE shift_code LIKE 'TEST%'")
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"SUCCESS - Removed {deleted} test records")
    except Exception as e:
        print(f"ERROR - Cleanup failed: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CONCURRENT DATABASE ACCESS TEST")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Database: data/planning.db")
    print(f"SQLite timeout: 5 seconds")

    # Run tests
    test_sequential()
    time.sleep(1)

    test_concurrent_fast()
    time.sleep(1)

    test_concurrent_slow()
    time.sleep(1)

    test_concurrent_very_slow()
    time.sleep(1)

    # Cleanup
    cleanup()

    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)
