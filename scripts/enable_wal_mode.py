"""
Enable WAL (Write-Ahead Logging) mode for SQLite database
WAL mode allows better concurrency: multiple readers + 1 writer simultaneously
"""
import sqlite3
from pathlib import Path

def enable_wal_mode():
    """Enable WAL mode on the database"""
    db_path = Path("data/planning.db")

    print("="*60)
    print("ENABLE WAL MODE")
    print("="*60)
    print(f"Database: {db_path}")
    print()

    try:
        # Connect
        print("1. Connecting to database...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check current mode
        print("2. Checking current journal mode...")
        cursor.execute("PRAGMA journal_mode")
        current_mode = cursor.fetchone()[0]
        print(f"   Current: {current_mode}")

        if current_mode.upper() == 'WAL':
            print("   -> Already in WAL mode!")
            conn.close()
            return

        # Enable WAL mode
        print("3. Enabling WAL mode...")
        cursor.execute("PRAGMA journal_mode=WAL")
        new_mode = cursor.fetchone()[0]
        print(f"   New mode: {new_mode}")

        # Verify
        cursor.execute("PRAGMA journal_mode")
        verify_mode = cursor.fetchone()[0]

        if verify_mode.upper() == 'WAL':
            print("   -> SUCCESS: WAL mode enabled!")

            # Show additional WAL settings
            print("\n4. WAL Configuration:")

            cursor.execute("PRAGMA synchronous")
            sync = cursor.fetchone()[0]
            print(f"   Synchronous: {sync} (2=FULL, 1=NORMAL, 0=OFF)")

            cursor.execute("PRAGMA wal_autocheckpoint")
            checkpoint = cursor.fetchone()[0]
            print(f"   WAL Auto-checkpoint: {checkpoint} pages")

            print("\n5. Benefits of WAL mode:")
            print("   - Multiple readers + 1 writer simultaneously")
            print("   - Readers never block writers")
            print("   - Writers never block readers")
            print("   - Better performance under concurrent load")

            print("\n6. Trade-offs:")
            print("   - Creates additional files: .db-wal and .db-shm")
            print("   - Requires filesystem that supports mmap")
            print("   - May not work well on network drives")

        else:
            print(f"   -> ERROR: Mode is {verify_mode}, expected WAL")

        conn.close()

    except Exception as e:
        print(f"\nERROR: {e}")
        return False

    return True

def check_wal_files():
    """Check if WAL files exist"""
    db_path = Path("data/planning.db")
    wal_path = Path("data/planning.db-wal")
    shm_path = Path("data/planning.db-shm")

    print("\n" + "="*60)
    print("WAL FILES CHECK")
    print("="*60)

    print(f"Main DB: {db_path.exists()} - {db_path.stat().st_size if db_path.exists() else 0} bytes")
    print(f"WAL file: {wal_path.exists()} - {wal_path.stat().st_size if wal_path.exists() else 0} bytes")
    print(f"SHM file: {shm_path.exists()} - {shm_path.stat().st_size if shm_path.exists() else 0} bytes")

if __name__ == "__main__":
    success = enable_wal_mode()

    if success:
        check_wal_files()

        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("1. Run: python test_concurrent_db_access_v2.py")
        print("2. Compare results with previous test")
        print("3. WAL mode persists - no need to re-enable")
