"""
Debug script: Simuleer cel focus op 5 november Bob Aerts

Dit volgt exact de flow van update_hr_violations_voor_gebruiker():
1. Create PlanningValidator(gebruiker_id=11, jaar=2024, maand=11)
2. Call validator.validate_shift(date(2024, 11, 5), '1101')
3. Show violations

Dit zou de "56u" violation moeten reproduceren.
"""
import sys
sys.path.insert(0, '.')

from datetime import date
from services.planning_validator_service import PlanningValidator

def main():
    print("=" * 70)
    print("CEL FOCUS SIMULATIE: 5 NOVEMBER BOB AERTS")
    print("=" * 70)

    # Create validator (exact zoals in grid kalender)
    validator = PlanningValidator(
        gebruiker_id=11,
        jaar=2024,
        maand=11
    )

    # Simulate clicking on cel 5 november met shift 1101
    # (note: deze shift staat al in DB, maar validate_shift voegt het tijdelijk toe)
    violations = validator.validate_shift(
        datum=date(2024, 11, 5),
        shift_code='1101'
    )

    print(f"\nViolations gevonden: {len(violations)}")

    if violations:
        print("\n" + "=" * 70)
        print("VIOLATIONS:")
        print("=" * 70)
        for i, v in enumerate(violations, 1):
            print(f"\nViolation #{i}:")
            print(f"  Type: {v.type.value}")
            print(f"  Beschrijving: {v.beschrijving}")
            print(f"  Severity: {v.severity.value}")

            if v.datum:
                print(f"  Datum: {v.datum}")
            if v.datum_range:
                print(f"  Datum range: {v.datum_range}")

            print(f"  Details:")
            for key, value in v.details.items():
                print(f"    {key}: {value}")

            if v.affected_shifts:
                print(f"  Affected shifts: {len(v.affected_shifts)}")
                for gebruiker_id, datum in v.affected_shifts[:10]:  # Max 10 tonen
                    print(f"    - {datum}")
    else:
        print("\n[OK] Geen violations gevonden")

    # Extra debug: bekijk planning data die validator gebruikt
    print("\n" + "=" * 70)
    print("PLANNING DATA DIE VALIDATOR GEBRUIKT:")
    print("=" * 70)

    planning_data = validator._get_planning_data()
    print(f"\nTotaal {len(planning_data)} planning regels geladen")
    print(f"Datum range: {min(p.datum for p in planning_data)} tot {max(p.datum for p in planning_data)}")

    print("\nAlle shifts:")
    for p in sorted(planning_data, key=lambda x: x.datum):
        print(f"  {p.datum}: {p.shift_code}")

    # Check HR config
    hr_config = validator._get_hr_config()
    print(f"\nWeek definitie: {hr_config.get('week_definitie', 'NIET GEVONDEN')}")
    print(f"Max uren per week: {hr_config.get('max_uren_week', 'NIET GEVONDEN')}")

if __name__ == "__main__":
    main()
