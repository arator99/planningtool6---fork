"""
Test script voor Planning Validator helper functions

Run met: python test_planning_validator_helpers.py
"""

from services.planning_validator_service import (
    bereken_shift_duur,
    bereken_rust_tussen_shifts,
    parse_periode_definitie,
    shift_overlapt_periode,
    dag_naar_weekday,
    parse_tijd
)
from datetime import datetime


def test_bereken_shift_duur():
    """Test shift duur berekening"""
    print("\n=== Test bereken_shift_duur() ===")

    # Normale shift
    assert bereken_shift_duur("06:00", "14:00") == 8.0, "Normale shift 8u"
    print("[OK] Normale shift 8u")

    # Middernacht crossing
    assert bereken_shift_duur("22:00", "06:00") == 8.0, "Nachtshift over middernacht"
    print("[OK] Nachtshift over middernacht")

    # Half uur
    assert bereken_shift_duur("14:30", "22:30") == 8.0, "Shift met halve uren"
    print("[OK] Shift met halve uren")

    # Kwartier
    duur = bereken_shift_duur("14:15", "22:45")
    assert abs(duur - 8.5) < 0.01, "Shift met kwartieren"
    print(f"[OK] Shift met kwartieren: {duur}u")


def test_bereken_rust_tussen_shifts():
    """Test rust berekening tussen shifts"""
    print("\n=== Test bereken_rust_tussen_shifts() ===")

    # Normale rust
    rust = bereken_rust_tussen_shifts("2025-11-15", "22:00", "2025-11-16", "06:00")
    assert rust == 8.0, f"Normale rust 8u (was: {rust})"
    print("[OK] Normale rust 8u")

    # Meer rust
    rust = bereken_rust_tussen_shifts("2025-11-15", "22:00", "2025-11-16", "08:30")
    assert rust == 10.5, f"Rust 10.5u (was: {rust})"
    print("[OK] Rust 10.5u")

    # Te weinig rust (violation!)
    rust = bereken_rust_tussen_shifts("2025-11-15", "22:00", "2025-11-16", "06:30")
    assert rust == 8.5, f"Te weinig rust 8.5u (was: {rust})"
    print(f"[OK] Te weinig rust 8.5u (violation als < 12u)")


def test_parse_periode_definitie():
    """Test periode parsing"""
    print("\n=== Test parse_periode_definitie() ===")

    # Week definitie
    result = parse_periode_definitie("ma-00:00|zo-23:59")
    assert result == ('ma', '00:00', 'zo', '23:59'), f"Week definitie (was: {result})"
    print("[OK] Week definitie parsed")

    # Weekend definitie
    result = parse_periode_definitie("vr-22:00|ma-06:00")
    assert result == ('vr', '22:00', 'ma', '06:00'), f"Weekend definitie (was: {result})"
    print("[OK] Weekend definitie parsed")


def test_dag_naar_weekday():
    """Test dag conversie"""
    print("\n=== Test dag_naar_weekday() ===")

    assert dag_naar_weekday('ma') == 0, "Maandag = 0"
    assert dag_naar_weekday('zo') == 6, "Zondag = 6"
    assert dag_naar_weekday('vr') == 4, "Vrijdag = 4"
    print("[OK] Dag naar weekday conversie OK")


def test_shift_overlapt_periode():
    """Test periode overlap detectie (exclusieve grenzen)"""
    print("\n=== Test shift_overlapt_periode() (Exclusieve Grenzen) ===")

    # Weekend: vr 22:00 - ma 06:00
    weekend_start = datetime(2025, 11, 14, 22, 0)  # Vrijdag 22:00
    weekend_eind = datetime(2025, 11, 17, 6, 0)    # Maandag 06:00

    # Shift EINDIGT OM 22:00 (op grens) = GEEN overlap
    overlap = shift_overlapt_periode("2025-11-14", "14:00", "22:00", weekend_start, weekend_eind)
    assert not overlap, "Shift eindigt OM grens = geen overlap"
    print("[OK] Shift eindigt OM grens (22:00) = GEEN overlap")

    # Shift EINDIGT NA 22:00 (binnen weekend) = WEL overlap
    overlap = shift_overlapt_periode("2025-11-14", "14:00", "22:01", weekend_start, weekend_eind)
    assert overlap, "Shift eindigt NA grens = wel overlap"
    print("[OK] Shift eindigt NA grens (22:01) = WEL overlap")

    # Shift BEGINT OM 06:00 (op grens) = GEEN overlap
    overlap = shift_overlapt_periode("2025-11-17", "06:00", "14:00", weekend_start, weekend_eind)
    assert not overlap, "Shift begint OM grens = geen overlap"
    print("[OK] Shift begint OM grens (06:00) = GEEN overlap")

    # Shift BEGINT VOOR 06:00 (binnen weekend) = WEL overlap
    overlap = shift_overlapt_periode("2025-11-17", "05:59", "14:00", weekend_start, weekend_eind)
    assert overlap, "Shift begint VOOR grens = wel overlap"
    print("[OK] Shift begint VOOR grens (05:59) = WEL overlap")

    # Shift volledig binnen weekend
    overlap = shift_overlapt_periode("2025-11-15", "10:00", "18:00", weekend_start, weekend_eind)
    assert overlap, "Shift volledig binnen weekend"
    print("[OK] Shift volledig binnen weekend = WEL overlap")

    # Shift buiten weekend (woensdag)
    overlap = shift_overlapt_periode("2025-11-12", "06:00", "14:00", weekend_start, weekend_eind)
    assert not overlap, "Shift buiten weekend"
    print("[OK] Shift buiten weekend = GEEN overlap")


def test_parse_tijd():
    """Test tijd parsing"""
    print("\n=== Test parse_tijd() ===")

    tijd = parse_tijd("14:30")
    assert tijd.hour == 14 and tijd.minute == 30, "Parse 14:30"
    print("[OK] Parse 14:30 OK")

    tijd = parse_tijd("06:00")
    assert tijd.hour == 6 and tijd.minute == 0, "Parse 06:00"
    print("[OK] Parse 06:00 OK")

    tijd = parse_tijd("23:59")
    assert tijd.hour == 23 and tijd.minute == 59, "Parse 23:59"
    print("[OK] Parse 23:59 OK")


def run_all_tests():
    """Run alle tests"""
    print("=" * 60)
    print("PLANNING VALIDATOR HELPER FUNCTIONS - TEST SUITE")
    print("=" * 60)

    try:
        test_bereken_shift_duur()
        test_bereken_rust_tussen_shifts()
        test_parse_periode_definitie()
        test_dag_naar_weekday()
        test_shift_overlapt_periode()
        test_parse_tijd()

        print("\n" + "=" * 60)
        print("[SUCCESS] ALLE TESTS GESLAAGD!")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n[FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
