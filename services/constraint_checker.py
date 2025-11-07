"""
ConstraintChecker - Pure Business Logic Layer voor HR Regels Validatie

Dit is de kernlaag van het HR Validatie Systeem. Het bevat ALLEEN business logic
(geen database queries, geen UI dependencies). Kan later hergebruikt worden door
AI optimizer voor automatische planning (v0.7.0+).

Usage:
    # Setup
    checker = ConstraintChecker(hr_config, shift_tijden)

    # Run validaties
    result = checker.check_12u_rust(planning_regels, gebruiker_id)
    all_results = checker.check_all(planning_regels, gebruiker_id)

    # Get violations
    violations = all_results['min_rust_12u'].violations

Design Pattern: Pure Functions + Dependency Injection
- Geen side effects
- Testbaar zonder database
- Herbruikbaar voor AI optimizer

Versie: 1.0
Datum: 3 November 2025
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ============================================================================
# ENUMS
# ============================================================================

class ViolationType(Enum):
    """HR regel types"""
    MIN_RUST_12U = "min_rust_12u"
    MAX_UREN_WEEK = "max_uren_week"
    MAX_WERKDAGEN_CYCLUS = "max_werkdagen_cyclus"
    MAX_DAGEN_TUSSEN_RX = "max_dagen_tussen_rx"
    MAX_WERKDAGEN_REEKS = "max_werkdagen_reeks"
    MAX_WEEKENDS = "max_weekends_achter_elkaar"
    NACHT_VROEG_VERBODEN = "nacht_vroeg_verboden"


class ViolationSeverity(Enum):
    """Violation ernst niveau"""
    ERROR = "error"      # Rode overlay
    WARNING = "warning"  # Gele overlay


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PlanningRegel:
    """
    Representeert 1 dag planning voor 1 gebruiker

    Pure data object - geen database dependencies
    """
    gebruiker_id: int
    datum: date
    shift_code: Optional[str] = None
    is_goedgekeurd_verlof: bool = False
    is_feestdag: bool = False

    def __post_init__(self):
        """Type validation"""
        if not isinstance(self.datum, date):
            raise TypeError(f"datum moet date object zijn, niet {type(self.datum)}")
        if not isinstance(self.gebruiker_id, int):
            raise TypeError(f"gebruiker_id moet int zijn, niet {type(self.gebruiker_id)}")


@dataclass
class Violation:
    """
    Representeert 1 HR regel overtreding

    Extended versie met velden voor toekomstige AI optimizer:
    - affected_shifts: Welke shifts betrokken bij violation (voor AI wijzigingen)
    - suggested_fixes: Mogelijke oplossingen (voor AI decision making)
    """
    type: ViolationType
    severity: ViolationSeverity
    gebruiker_id: int
    datum: Optional[date]
    datum_range: Optional[Tuple[date, date]]
    beschrijving: str
    details: Dict[str, Any] = field(default_factory=dict)

    # Voor AI optimizer (v0.7.0+)
    affected_shifts: List[Tuple[int, date]] = field(default_factory=list)
    suggested_fixes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialisatie voor caching/logging"""
        return {
            'type': self.type.value,
            'severity': self.severity.value,
            'gebruiker_id': self.gebruiker_id,
            'datum': self.datum.isoformat() if self.datum else None,
            'datum_range': [d.isoformat() for d in self.datum_range] if self.datum_range else None,
            'beschrijving': self.beschrijving,
            'details': self.details,
            'affected_shifts': [(uid, d.isoformat()) for uid, d in self.affected_shifts],
            'suggested_fixes': self.suggested_fixes,
        }

    def to_user_message(self) -> str:
        """User-friendly bericht voor dialogs"""
        return self.beschrijving


@dataclass
class ConstraintCheckResult:
    """
    Resultaat van 1 constraint check

    Bevat:
    - passed: True als geen violations
    - violations: Lijst van violations
    - metadata: Extra info (bijv. telling, statistieken)
    """
    passed: bool
    violations: List[Violation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        """Allow: if result: ..."""
        return self.passed


# ============================================================================
# CONSTRAINT CHECKER
# ============================================================================

class ConstraintChecker:
    """
    Pure business logic voor HR regels validatie

    Dependencies geïnjecteerd via constructor (geen globals, geen database)

    Args:
        hr_config: Dict met HR regel configuratie
            {
                'min_rust_uren': 12.0,
                'max_uren_week': 50.0,
                'max_werkdagen_cyclus': 19,
                'max_dagen_tussen_rx': 7,
                'max_werkdagen_reeks': 7,
                'max_weekends_achter_elkaar': 6,
                'week_definitie': 'ma-00:00|zo-23:59',
                'weekend_definitie': 'vr-22:00|ma-06:00'
            }
        shift_tijden: Dict met shift timing info
            {
                '7101': {
                    'start_uur': '06:00',
                    'eind_uur': '14:00',
                    'telt_als_werkdag': True,
                    'reset_12u_rust': False,
                    'breekt_werk_reeks': False
                },
                'VV': {
                    'start_uur': None,
                    'eind_uur': None,
                    'telt_als_werkdag': False,
                    'reset_12u_rust': True,
                    'breekt_werk_reeks': True
                },
                ...
            }
    """

    def __init__(self, hr_config: Dict[str, Any], shift_tijden: Dict[str, Dict[str, Any]]):
        """
        Initialize checker met configuratie

        Args:
            hr_config: HR regel waarden
            shift_tijden: Shift timing + flags
        """
        self.hr_config = hr_config
        self.shift_tijden = shift_tijden

        # Validatie
        self._validate_config()

    def _validate_config(self) -> None:
        """Valideer hr_config en shift_tijden structuur"""
        required_hr_keys = [
            'min_rust_uren',
            'max_uren_week',
            'max_werkdagen_cyclus',
            'max_dagen_tussen_rx',
            'max_werkdagen_reeks',
            'max_weekends_achter_elkaar',
            'week_definitie',
            'weekend_definitie'
        ]

        for key in required_hr_keys:
            if key not in self.hr_config:
                raise ValueError(f"hr_config mist verplicht veld: {key}")

        if not isinstance(self.shift_tijden, dict):
            raise TypeError("shift_tijden moet dict zijn")

    # ========================================================================
    # HELPER METHODS (Sectie 1.2)
    # ========================================================================

    def _bereken_shift_duur(self, shift_code: str) -> Optional[float]:
        """
        Bereken shift duur in uren

        Handelt middernacht crossing (22:00-06:00 = 8u)

        Args:
            shift_code: Code van shift (bijv. '7101', 'VV')

        Returns:
            Uren als float, of None als geen tijden (speciale code)

        Examples:
            _bereken_shift_duur('7101')  # "06:00-14:00" → 8.0
            _bereken_shift_duur('7103')  # "22:00-06:00" → 8.0
            _bereken_shift_duur('VV')    # None (geen tijden)
        """
        if shift_code not in self.shift_tijden:
            return None

        shift_info = self.shift_tijden[shift_code]
        start_uur = shift_info.get('start_uur')
        eind_uur = shift_info.get('eind_uur')

        if not start_uur or not eind_uur:
            return None

        # Parse tijden
        start = self._parse_tijd(start_uur)
        eind = self._parse_tijd(eind_uur)

        # Bereken duur (handle middernacht crossing)
        start_dt = datetime.combine(date.today(), start)
        eind_dt = datetime.combine(date.today(), eind)

        if eind_dt < start_dt:  # Middernacht crossing
            eind_dt += timedelta(days=1)

        delta = eind_dt - start_dt
        return delta.total_seconds() / 3600

    def _parse_tijd(self, tijd_str: str) -> time:
        """
        Parse tijd string naar time object

        Supported formats:
        - "06:00" (standaard)
        - "14:30" (half uur)
        - "22:15" (kwartier)

        Args:
            tijd_str: Tijd string

        Returns:
            time object

        Raises:
            ValueError: Bij ongeldige format
        """
        try:
            return datetime.strptime(tijd_str, "%H:%M").time()
        except ValueError:
            raise ValueError(f"Ongeldige tijd format: {tijd_str}. Verwacht HH:MM")

    def _check_periode_overlap(
        self,
        shift_start: datetime,
        shift_eind: datetime,
        periode_start: datetime,
        periode_eind: datetime
    ) -> bool:
        """
        Check of shift overlapt met periode (exclusieve grenzen)

        Logica: (shift_start < periode_eind) AND (shift_eind > periode_start)

        Voorbeelden:
            Shift 14:00-22:00 (vr), Weekend vr-22:00 → ma-06:00
            → shift_eind (22:00) == periode_start (22:00) → GEEN overlap

            Shift 14:00-22:01 (vr), Weekend vr-22:00 → ma-06:00
            → shift_eind (22:01) > periode_start (22:00) → WEL overlap

        Args:
            shift_start: Shift start datetime
            shift_eind: Shift eind datetime
            periode_start: Periode start datetime
            periode_eind: Periode eind datetime

        Returns:
            True als overlap, False als geen overlap
        """
        return (shift_start < periode_eind) and (shift_eind > periode_start)

    def _get_dag_type(self, datum: date, is_feestdag: bool) -> str:
        """
        Bepaal dag type voor shift code lookup

        Args:
            datum: Datum
            is_feestdag: True als feestdag

        Returns:
            'feestdag', 'zondag', 'zaterdag', of 'weekdag'
        """
        if is_feestdag:
            return 'feestdag'

        weekday = datum.weekday()  # 0=maandag, 6=zondag

        if weekday == 6:
            return 'zondag'
        elif weekday == 5:
            return 'zaterdag'
        else:
            return 'weekdag'

    def _is_werkdag_shift(self, shift_code: Optional[str]) -> bool:
        """
        Check of shift telt als werkdag

        Args:
            shift_code: Code van shift

        Returns:
            True als telt_als_werkdag=1, False anders
        """
        if not shift_code:
            return False

        if shift_code not in self.shift_tijden:
            return False

        return self.shift_tijden[shift_code].get('telt_als_werkdag', False)

    def _reset_12u_teller(self, shift_code: Optional[str]) -> bool:
        """
        Check of shift reset 12u rust teller (RX, CX, Z)

        Args:
            shift_code: Code van shift

        Returns:
            True als reset_12u_rust=1, False anders
        """
        if not shift_code:
            return False

        if shift_code not in self.shift_tijden:
            return False

        return self.shift_tijden[shift_code].get('reset_12u_rust', False)

    def _breekt_werk_reeks(self, shift_code: Optional[str]) -> bool:
        """
        Check of shift werk reeks breekt (RX, CX, verlof)

        Args:
            shift_code: Code van shift

        Returns:
            True als breekt_werk_reeks=1, False anders
        """
        if not shift_code:
            return True  # Geen shift = reeks breekt

        if shift_code not in self.shift_tijden:
            return False

        return self.shift_tijden[shift_code].get('breekt_werk_reeks', False)

    def _is_shift_type(self, shift_code: str, shift_type: str) -> bool:
        """
        Check of een shift code een bepaald shift type heeft (v0.6.26)

        Args:
            shift_code: Shift code (bijv. '1301', 'VV')
            shift_type: Type ('nacht', 'vroeg', 'laat', 'dag')

        Returns:
            True als shift dit type heeft
        """
        if not shift_code:
            return False

        if shift_code not in self.shift_tijden:
            return False

        # shift_tijden heeft 'shift_type' veld voor werkpost codes
        return self.shift_tijden[shift_code].get('shift_type') == shift_type

    def _has_term_match(self, code: str, terms: set) -> bool:
        """
        Check of een code een van de gegeven terms heeft (v0.6.26)

        Args:
            code: Shift code
            terms: Set van terms om te matchen (bijv. {'verlof', 'ziek'})

        Returns:
            True als code één van de terms heeft
        """
        if not code:
            return False

        if code not in self.shift_tijden:
            return False

        # shift_tijden heeft 'term' veld voor speciale codes
        code_term = self.shift_tijden[code].get('term')
        return code_term and code_term in terms

    # ========================================================================
    # CONSTRAINT CHECKS (Sectie 1.3 - 1.8)
    # ========================================================================

    def check_12u_rust(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> ConstraintCheckResult:
        """
        Check: Minimaal 12u rust tussen twee opeenvolgende shifts

        Business Rules:
        - Rust = tijd tussen eind shift N en start shift N+1
        - RX/CX/Z codes resetten 12u teller (volgende shift OK ongeacht rust)
        - Middernacht crossing handelen (shift 22:00-06:00)
        - Meerdere dagen gap tussen shifts = altijd OK

        Args:
            planning: Lijst van planning regels (gesorteerd op datum)
            gebruiker_id: Optioneel filter op gebruiker

        Returns:
            ConstraintCheckResult met violations
        """
        violations = []
        min_rust_uren = float(self.hr_config['min_rust_uren'])

        # Filter op gebruiker indien opgegeven
        if gebruiker_id:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]

        # Sort op datum (defensive)
        planning = sorted(planning, key=lambda p: p.datum)

        # Loop door opeenvolgende dagen
        for i in range(len(planning) - 1):
            p1 = planning[i]
            p2 = planning[i + 1]

            # Skip als geen shift codes
            if not p1.shift_code or not p2.shift_code:
                continue

            # Skip als shift1 reset 12u teller (RX, CX, Z)
            if self._reset_12u_teller(p1.shift_code):
                continue

            # Check alleen opeenvolgende dagen
            dagen_verschil = (p2.datum - p1.datum).days
            if dagen_verschil != 1:
                continue  # Gap > 1 dag = altijd OK

            # Haal shift tijden op
            if p1.shift_code not in self.shift_tijden:
                continue
            if p2.shift_code not in self.shift_tijden:
                continue

            shift1_info = self.shift_tijden[p1.shift_code]
            shift2_info = self.shift_tijden[p2.shift_code]

            # Skip als geen tijden (speciale codes)
            if not shift1_info.get('eind_uur') or not shift2_info.get('start_uur'):
                continue

            # Bereken rust tussen shifts
            rust_uren = self._bereken_rust_tussen_shifts(
                p1.datum, shift1_info['start_uur'], shift1_info['eind_uur'],
                p2.datum, shift2_info['start_uur']
            )

            # Violation als < min_rust_uren
            if rust_uren < min_rust_uren:
                violations.append(Violation(
                    type=ViolationType.MIN_RUST_12U,
                    severity=ViolationSeverity.ERROR,
                    gebruiker_id=p1.gebruiker_id,
                    datum=p2.datum,  # Violation op dag 2
                    datum_range=None,
                    beschrijving=f"Te weinig rust: {rust_uren:.1f}u tussen shifts (minimaal {min_rust_uren:.0f}u)",
                    details={
                        'shift1_datum': p1.datum.isoformat(),
                        'shift1_code': p1.shift_code,
                        'shift1_tijd': f"{shift1_info.get('start_uur')}-{shift1_info.get('eind_uur')}",
                        'shift2_datum': p2.datum.isoformat(),
                        'shift2_code': p2.shift_code,
                        'shift2_tijd': f"{shift2_info.get('start_uur')}-{shift2_info.get('eind_uur')}",
                        'rust_uren': rust_uren,
                        'min_rust_uren': min_rust_uren
                    },
                    affected_shifts=[
                        (p1.gebruiker_id, p1.datum),
                        (p2.gebruiker_id, p2.datum)
                    ],
                    suggested_fixes=[
                        f"Verplaats shift op {p2.datum.isoformat()}",
                        f"Wijzig shift type op {p1.datum.isoformat()} of {p2.datum.isoformat()}",
                        "Plan rustdag (RX/CX) tussen de shifts"
                    ]
                ))

        return ConstraintCheckResult(
            passed=len(violations) == 0,
            violations=violations,
            metadata={'checked_shifts': len(planning), 'violations_count': len(violations)}
        )

    def _bereken_rust_tussen_shifts(
        self,
        datum1: date,
        start_uur1: str,
        eind_uur1: str,
        datum2: date,
        start_uur2: str
    ) -> float:
        """
        Bereken rust tussen twee shifts in uren

        Handelt middernacht crossing correct: als shift 1 eindigt NA middernacht
        (eind_uur < start_uur), dan eindigt de shift de volgende dag.

        Args:
            datum1: Datum shift 1
            start_uur1: Start tijd shift 1 (bijv. "22:00")
            eind_uur1: Eind tijd shift 1 (bijv. "06:00")
            datum2: Datum shift 2
            start_uur2: Start tijd shift 2 (bijv. "06:00")

        Returns:
            Aantal uren rust (kan negatief zijn als overlap)

        Examples:
            # Normale shift (geen middernacht crossing)
            _bereken_rust_tussen_shifts(
                date(2025, 11, 15), "06:00", "14:00",
                date(2025, 11, 16), "06:00"
            ) → 16.0

            # Nacht shift (middernacht crossing)
            _bereken_rust_tussen_shifts(
                date(2025, 11, 15), "22:00", "06:00",
                date(2025, 11, 16), "06:00"
            ) → 0.0  (nacht eindigt 06:00 op 16e, vroeg begint 06:00 op 16e)
        """
        # Parse tijden
        start_tijd1 = self._parse_tijd(start_uur1)
        eind_tijd1 = self._parse_tijd(eind_uur1)
        start_tijd2 = self._parse_tijd(start_uur2)

        # Bereken eindtijd shift 1
        dt1 = datetime.combine(datum1, eind_tijd1)

        # Check middernacht crossing: als eind_tijd < start_tijd, dan eindigt shift volgende dag
        if eind_tijd1 < start_tijd1:
            dt1 += timedelta(days=1)

        # Bereken starttijd shift 2
        dt2 = datetime.combine(datum2, start_tijd2)

        # Bereken rust
        delta = dt2 - dt1
        return delta.total_seconds() / 3600

    def check_max_uren_week(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> ConstraintCheckResult:
        """
        Check: Maximaal 50u gewerkt per week

        Week definitie: Configureerbaar via hr_config (default: ma-00:00|zo-23:59)

        Business Rules:
        - Bereken totaal shift uren per week
        - Week grens exclusief: shift moet BINNEN week vallen, niet op grens eindigen
        - Violation bij > max_uren_week

        Args:
            planning: Lijst van planning regels
            gebruiker_id: Optioneel filter op gebruiker

        Returns:
            ConstraintCheckResult met violations
        """
        violations = []
        max_uren = float(self.hr_config['max_uren_week'])
        week_def = self.hr_config['week_definitie']

        # Filter op gebruiker indien opgegeven
        if gebruiker_id:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]

        # Parse week definitie
        start_dag, start_uur, eind_dag, eind_uur = self._parse_periode_definitie(week_def)

        # Bepaal weken in planning periode
        if not planning:
            return ConstraintCheckResult(passed=True, violations=[], metadata={})

        min_datum = min(p.datum for p in planning)
        max_datum = max(p.datum for p in planning)

        # Generate weken (sliding window)
        weken = self._generate_weken(min_datum, max_datum, start_dag, start_uur, eind_dag, eind_uur)

        # Check elke week
        for week_start, week_eind, week_nummer in weken:
            # Haal shifts in deze week
            shifts_in_week = []
            for p in planning:
                if not p.shift_code:
                    continue

                # Check of shift overlapt met week
                shift_overlapt = self._shift_overlapt_week(
                    p.datum, p.shift_code, week_start, week_eind
                )

                if shift_overlapt:
                    shifts_in_week.append(p)

            # Bereken totaal uren
            totaal_uren = 0.0
            for p in shifts_in_week:
                duur = self._bereken_shift_duur(p.shift_code)
                if duur:
                    totaal_uren += duur

            # Violation?
            if totaal_uren > max_uren:
                violations.append(Violation(
                    type=ViolationType.MAX_UREN_WEEK,
                    severity=ViolationSeverity.ERROR,
                    gebruiker_id=gebruiker_id or shifts_in_week[0].gebruiker_id,
                    datum=None,
                    datum_range=(week_start.date(), week_eind.date()),
                    beschrijving=f"Te veel uren: {totaal_uren:.1f}u in week (maximaal {max_uren:.0f}u)",
                    details={
                        'week_start': week_start.isoformat(),
                        'week_eind': week_eind.isoformat(),
                        'week_nummer': week_nummer,
                        'totaal_uren': totaal_uren,
                        'max_uren': max_uren,
                        'shifts_count': len(shifts_in_week)
                    },
                    affected_shifts=[(p.gebruiker_id, p.datum) for p in shifts_in_week],
                    suggested_fixes=[
                        f"Verwijder {totaal_uren - max_uren:.1f}u aan shifts uit week {week_nummer}",
                        "Verplaats shift naar andere week",
                        "Gebruik kortere shift types"
                    ]
                ))

        return ConstraintCheckResult(
            passed=len(violations) == 0,
            violations=violations,
            metadata={'checked_weeks': len(weken), 'violations_count': len(violations)}
        )

    def _parse_periode_definitie(self, waarde: str) -> Tuple[str, str, str, str]:
        """
        Parse 'ma-00:00|zo-23:59' → (start_dag, start_uur, eind_dag, eind_uur)

        Args:
            waarde: Periode string (bijv. 'ma-00:00|zo-23:59')

        Returns:
            Tuple (start_dag, start_uur, eind_dag, eind_uur)

        Example:
            _parse_periode_definitie('ma-00:00|zo-23:59')
            → ('ma', '00:00', 'zo', '23:59')
        """
        start, eind = waarde.split('|')
        start_dag, start_uur = start.split('-', 1)
        eind_dag, eind_uur = eind.split('-', 1)
        return (start_dag.strip(), start_uur.strip(),
                eind_dag.strip(), eind_uur.strip())

    def _generate_weken(
        self,
        min_datum: date,
        max_datum: date,
        start_dag: str,
        start_uur: str,
        eind_dag: str,
        eind_uur: str
    ) -> List[Tuple[datetime, datetime, int]]:
        """
        Generate lijst van week periodes

        Returns:
            List van (week_start, week_eind, week_nummer) tuples
        """
        # Map dag naam naar weekday nummer
        dag_map = {
            'ma': 0, 'di': 1, 'wo': 2, 'do': 3,
            'vr': 4, 'za': 5, 'zo': 6
        }

        start_weekday = dag_map.get(start_dag.lower(), 0)

        # Vind eerste week start (op of voor min_datum)
        current = min_datum
        while current.weekday() != start_weekday:
            current -= timedelta(days=1)

        weken = []
        week_nummer = current.isocalendar()[1]

        while current <= max_datum:
            # Week start
            week_start = datetime.combine(current, self._parse_tijd(start_uur))

            # Week eind (meestal 6 dagen later, maar kan variëren)
            eind_weekday = dag_map.get(eind_dag.lower(), 6)
            dagen_tot_eind = (eind_weekday - start_weekday) % 7
            if dagen_tot_eind == 0:
                dagen_tot_eind = 7

            week_eind_datum = current + timedelta(days=dagen_tot_eind)
            week_eind = datetime.combine(week_eind_datum, self._parse_tijd(eind_uur))

            weken.append((week_start, week_eind, week_nummer))

            # Volgende week
            current += timedelta(days=7)
            week_nummer += 1

        return weken

    def _shift_overlapt_week(
        self,
        shift_datum: date,
        shift_code: str,
        week_start: datetime,
        week_eind: datetime
    ) -> bool:
        """
        Check of shift overlapt met week periode

        Args:
            shift_datum: Datum van shift
            shift_code: Code van shift
            week_start: Week start datetime
            week_eind: Week eind datetime

        Returns:
            True als shift overlapt met week
        """
        if shift_code not in self.shift_tijden:
            return False

        shift_info = self.shift_tijden[shift_code]
        start_uur = shift_info.get('start_uur')
        eind_uur = shift_info.get('eind_uur')

        if not start_uur or not eind_uur:
            return False

        # Bereken shift start/eind datetime
        shift_start = datetime.combine(shift_datum, self._parse_tijd(start_uur))
        shift_eind = datetime.combine(shift_datum, self._parse_tijd(eind_uur))

        # Handle middernacht crossing
        if shift_eind < shift_start:
            shift_eind += timedelta(days=1)

        # Check overlap (exclusieve grenzen)
        return self._check_periode_overlap(shift_start, shift_eind, week_start, week_eind)

    # ========================================================================
    # ADDITIONAL CONSTRAINT CHECKS (Sectie 1.5 - 1.8)
    # ========================================================================

    def check_max_werkdagen_cyclus(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None,
        rode_lijnen: Optional[List[Dict]] = None
    ) -> ConstraintCheckResult:
        """
        Check: Maximaal 19 werkdagen per 28-dagen rode lijn cyclus

        Business Rules:
        - Rode lijn cyclus = 28 dagen periode
        - Werkdag = shift met telt_als_werkdag=1
        - Violation bij > max_werkdagen_cyclus

        Args:
            planning: Lijst van planning regels
            gebruiker_id: Optioneel filter op gebruiker
            rode_lijnen: Lijst met rode lijn periodes
                [{
                    'start_datum': date(2025, 1, 6),
                    'eind_datum': date(2025, 2, 2),
                    'periode_nummer': 1
                }, ...]

        Returns:
            ConstraintCheckResult met violations
        """
        violations = []
        max_dagen = int(self.hr_config.get('max_werkdagen_cyclus', 19))

        # Filter op gebruiker indien opgegeven
        if gebruiker_id:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]

        # Rode lijnen verplicht
        if not rode_lijnen:
            return ConstraintCheckResult(
                passed=True,
                violations=[],
                metadata={'warning': 'Geen rode lijnen info - check overgeslagen'}
            )

        # Check elke rode lijn periode
        for periode in rode_lijnen:
            start = periode['start_datum']
            eind = periode['eind_datum']
            periode_nr = periode.get('periode_nummer', 0)

            # Tel werkdagen in deze periode
            werkdagen = 0
            shifts_in_periode = []

            for p in planning:
                if start <= p.datum <= eind:
                    if p.shift_code and self._is_werkdag_shift(p.shift_code):
                        werkdagen += 1
                        shifts_in_periode.append(p)

            # Violation?
            if werkdagen > max_dagen:
                violations.append(Violation(
                    type=ViolationType.MAX_WERKDAGEN_CYCLUS,
                    severity=ViolationSeverity.ERROR,
                    gebruiker_id=gebruiker_id or shifts_in_periode[0].gebruiker_id,
                    datum=None,
                    datum_range=(start, eind),
                    beschrijving=f"Te veel werkdagen: {werkdagen} dagen in periode {periode_nr} (maximaal {max_dagen})",
                    details={
                        'periode_nummer': periode_nr,
                        'periode_start': start.isoformat(),
                        'periode_eind': eind.isoformat(),
                        'werkdagen': werkdagen,
                        'max_dagen': max_dagen
                    },
                    affected_shifts=[(p.gebruiker_id, p.datum) for p in shifts_in_periode],
                    suggested_fixes=[
                        f"Verwijder {werkdagen - max_dagen} werkdag(en) uit periode {periode_nr}",
                        "Vervang werkdag door rustdag (RX/CX)",
                        "Verplaats shifts naar andere periode"
                    ]
                ))

        return ConstraintCheckResult(
            passed=len(violations) == 0,
            violations=violations,
            metadata={'checked_periodes': len(rode_lijnen), 'violations_count': len(violations)}
        )

    def check_max_dagen_tussen_rx(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> ConstraintCheckResult:
        """
        Check: Maximaal 7 dagen tussen twee RX codes

        Business Rules (v0.6.26 - CRITICAL FIX):
        - Alleen RX codes tellen voor deze regel (niet CX, niet Z)
        - CX is rustdag voor andere regels (12u rust, werkdagen reeks)
        - Maar CX reset NIET de "dagen tussen RX" counter
        - Tel dagen tussen opeenvolgende RX codes
        - Violation bij gap > max_dagen_tussen_rx (default 7)
        - Elke 8ste dag moet een RX zijn (max 7 dagen tussen RX)

        Segmented Check (v0.6.26 - BUG-005):
        - Lege cellen breken het segment
        - Check RX gaps alleen binnen elk continu segment
        - Voorkomt valse violations tijdens partial planning invoer

        Args:
            planning: Lijst van planning regels (gesorteerd op datum)
            gebruiker_id: Optioneel filter op gebruiker

        Returns:
            ConstraintCheckResult met violations
        """
        violations = []
        max_gap = int(self.hr_config.get('max_dagen_tussen_rx', 7))

        # Filter op gebruiker indien opgegeven
        if gebruiker_id:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]

        # Sort op datum
        planning = sorted(planning, key=lambda p: p.datum)

        # CRITICAL (v0.6.26 - BUG-005): Segment planning op lege cellen
        # Lege cel breekt segment -> check elk segment apart
        segments = self._segment_planning_op_lege_cellen(planning)

        # Check elk segment apart
        total_rx_count = 0
        for segment in segments:
            segment_violations = self._check_rx_gap_in_segment(segment, max_gap)
            violations.extend(segment_violations)

            # Tel RX codes voor metadata
            rx_in_segment = sum(1 for p in segment if p.shift_code == 'RX')
            total_rx_count += rx_in_segment

        return ConstraintCheckResult(
            passed=len(violations) == 0,
            violations=violations,
            metadata={
                'rx_dagen_count': total_rx_count,
                'violations_count': len(violations),
                'segments_count': len(segments)
            }
        )

    def _segment_planning_op_lege_cellen(self, planning: List[PlanningRegel]) -> List[List[PlanningRegel]]:
        """
        Segment planning op lege cellen (v0.6.26 - BUG-005 + BUG-005b)

        Business Rule:
        - Lege cel (geen shift_code) breekt segment
        - Datum gap (> 1 dag verschil) breekt segment (BUG-005b)
        - VV, KD, CX, RX, etc blijven in segment (bewuste keuzes)

        Args:
            planning: Gesorteerde lijst van planning regels

        Returns:
            List van segments (elk segment = list van planning regels)

        Example:
            Input:  [shift 1/11, shift 2/11, LEEG 3/11, shift 5/11]
            Output: [[shift 1/11, shift 2/11], [shift 5/11]]
                    (gap 2/11 -> 5/11 breekt segment)
        """
        segments = []
        current_segment = []
        vorige_datum = None

        for p in planning:
            # Lege cel = segment breekt
            if not p.shift_code or p.shift_code.strip() == '':
                if current_segment:
                    segments.append(current_segment)
                    current_segment = []
                vorige_datum = p.datum
                continue

            # BUG-005b: Datum gap check (> 1 dag verschil)
            if vorige_datum and (p.datum - vorige_datum).days > 1:
                # Er zijn lege dagen tussen vorige en deze shift
                if current_segment:
                    segments.append(current_segment)
                    current_segment = []

            # Shift met code = blijft in segment
            current_segment.append(p)
            vorige_datum = p.datum

        # Laatste segment toevoegen
        if current_segment:
            segments.append(current_segment)

        return segments

    def _check_rx_gap_in_segment(self, segment: List[PlanningRegel], max_gap: int) -> List[Violation]:
        """
        Check RX gaps binnen een continu segment (v0.6.26 - BUG-005)

        Dit is de originele RX gap check logic, nu per segment.

        Args:
            segment: Continu segment van planning regels (geen lege cellen)
            max_gap: Maximaal aantal dagen tussen RX codes

        Returns:
            List van Violation objects
        """
        violations = []

        # Vind alle RX codes in segment (v0.6.26 - CRITICAL FIX: alleen RX, niet CX/Z)
        rx_dagen = []
        for p in segment:
            if p.shift_code == 'RX':
                rx_dagen.append(p)

        # Check gaps tussen RX codes
        for i in range(len(rx_dagen) - 1):
            rx1 = rx_dagen[i]
            rx2 = rx_dagen[i + 1]

            dagen_tussen = (rx2.datum - rx1.datum).days - 1  # Exclusief RX dagen zelf

            if dagen_tussen > max_gap:
                violations.append(Violation(
                    type=ViolationType.MAX_DAGEN_TUSSEN_RX,
                    severity=ViolationSeverity.ERROR,
                    gebruiker_id=rx1.gebruiker_id,
                    datum=None,
                    datum_range=(rx1.datum, rx2.datum),
                    beschrijving=f"Te lang tussen RX: {dagen_tussen} dagen (maximaal {max_gap})",
                    details={
                        'rx1_datum': rx1.datum.isoformat(),
                        'rx1_code': rx1.shift_code,
                        'rx2_datum': rx2.datum.isoformat(),
                        'rx2_code': rx2.shift_code,
                        'dagen_tussen': dagen_tussen,
                        'max_gap': max_gap
                    },
                    affected_shifts=[(rx1.gebruiker_id, rx1.datum), (rx2.gebruiker_id, rx2.datum)],
                    suggested_fixes=[
                        f"Plan RX tussen {rx1.datum.isoformat()} en {rx2.datum.isoformat()}",
                        "Verplaats shifts om RX te creëren",
                        "CX kan wel als rustdag maar reset niet de RX counter"
                    ]
                ))

        # CRITICAL FIX (v0.6.26 - BUG-003b): Check ook gap NA laatste RX
        # Als er maar 1 RX is, of als laatste RX te lang geleden is, moet dit gedetecteerd worden
        if rx_dagen and segment:
            laatste_rx = rx_dagen[-1]
            laatste_datum = max(p.datum for p in segment)

            # Check of er shifts zijn NA laatste RX
            shifts_na_rx = [p for p in segment if p.datum > laatste_rx.datum]

            if shifts_na_rx:
                # Bereken gap tussen laatste RX en laatste shift
                dagen_na_rx = (laatste_datum - laatste_rx.datum).days - 1  # Exclusief RX zelf

                if dagen_na_rx > max_gap:
                    violations.append(Violation(
                        type=ViolationType.MAX_DAGEN_TUSSEN_RX,
                        severity=ViolationSeverity.ERROR,
                        gebruiker_id=laatste_rx.gebruiker_id,
                        datum=None,
                        datum_range=(laatste_rx.datum, laatste_datum),
                        beschrijving=f"Te lang na laatste RX: {dagen_na_rx} dagen zonder nieuwe RX (maximaal {max_gap})",
                        details={
                            'laatste_rx_datum': laatste_rx.datum.isoformat(),
                            'laatste_shift_datum': laatste_datum.isoformat(),
                            'dagen_na_rx': dagen_na_rx,
                            'max_gap': max_gap,
                            'shifts_na_rx': len(shifts_na_rx)
                        },
                        affected_shifts=[(p.gebruiker_id, p.datum) for p in shifts_na_rx],
                        suggested_fixes=[
                            f"Plan RX na {laatste_rx.datum.isoformat()} (uiterlijk {laatste_rx.datum + timedelta(days=max_gap + 1)})",
                            "Elke 8ste dag moet een RX zijn",
                            "CX kan als rustdag maar vervangt geen RX"
                        ]
                    ))

        return violations

    def check_max_werkdagen_reeks(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> ConstraintCheckResult:
        """
        Check: Maximaal 7 opeenvolgende werkdagen zonder rustdag

        Business Rules:
        - State machine: tel opeenvolgende werkdagen
        - Reset bij: RX/CX/verlof (breekt_werk_reeks=1) of geen shift
        - Reset bij: Datum gap > 1 dag (BUG-005b)
        - Violation bij reeks > max_werkdagen_reeks

        Args:
            planning: Lijst van planning regels (gesorteerd op datum)
            gebruiker_id: Optioneel filter op gebruiker

        Returns:
            ConstraintCheckResult met violations
        """
        violations = []
        max_reeks = int(self.hr_config.get('max_werkdagen_reeks', 7))

        # Filter op gebruiker indien opgegeven
        if gebruiker_id:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]

        # Sort op datum
        planning = sorted(planning, key=lambda p: p.datum)

        if not planning:
            return ConstraintCheckResult(passed=True, violations=[], metadata={})

        # State machine
        werkdagen_reeks = 0
        reeks_start_datum = None
        reeks_shifts = []
        vorige_datum = None

        for p in planning:
            # BUG-005b: Check datum gap (lege dagen tussen shifts)
            if vorige_datum and (p.datum - vorige_datum).days > 1:
                # Reset reeks want er zijn lege dagen tussen
                werkdagen_reeks = 0
                reeks_start_datum = None
                reeks_shifts = []
            # Werkdag?
            if p.shift_code and self._is_werkdag_shift(p.shift_code):
                # Breekt deze shift de reeks? (RX/CX/verlof)
                if self._breekt_werk_reeks(p.shift_code):
                    # Reset reeks
                    werkdagen_reeks = 0
                    reeks_start_datum = None
                    reeks_shifts = []
                else:
                    # Voeg toe aan reeks
                    if werkdagen_reeks == 0:
                        reeks_start_datum = p.datum
                    werkdagen_reeks += 1
                    reeks_shifts.append(p)

                    # Check violation
                    if werkdagen_reeks > max_reeks:
                        violations.append(Violation(
                            type=ViolationType.MAX_WERKDAGEN_REEKS,
                            severity=ViolationSeverity.ERROR,
                            gebruiker_id=p.gebruiker_id,
                            datum=p.datum,
                            datum_range=(reeks_start_datum, p.datum),
                            beschrijving=f"Te veel opeenvolgende werkdagen: {werkdagen_reeks} dagen achter elkaar (maximaal {max_reeks})",
                            details={
                                'reeks_start': reeks_start_datum.isoformat() if reeks_start_datum else None,
                                'reeks_eind': p.datum.isoformat(),
                                'werkdagen_reeks': werkdagen_reeks,
                                'max_reeks': max_reeks
                            },
                            affected_shifts=[(s.gebruiker_id, s.datum) for s in reeks_shifts],
                            suggested_fixes=[
                                f"Plan rustdag (RX/CX) na {werkdagen_reeks - max_reeks} werkdagen",
                                "Verwijder shift uit reeks",
                                "Vervang werkdag door verlof/rustdag"
                            ]
                        ))
            else:
                # Geen shift of niet-werkdag → reset reeks
                werkdagen_reeks = 0
                reeks_start_datum = None
                reeks_shifts = []

            # Update vorige datum voor gap detection
            vorige_datum = p.datum

        return ConstraintCheckResult(
            passed=len(violations) == 0,
            violations=violations,
            metadata={'violations_count': len(violations)}
        )

    def check_max_weekends_achter_elkaar(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> ConstraintCheckResult:
        """
        Check: Maximaal 6 weekends achter elkaar werken

        Weekend definitie: Configureerbaar (default: vr-22:00|ma-06:00)

        Business Rules:
        - Weekend = tijd tussen vr 22:00 en ma 06:00 (exclusieve grenzen)
        - Weekend telt als "gewerkt" als shift overlapt met weekend periode
        - Tel opeenvolgende weekends met shifts
        - Violation bij > max_weekends_achter_elkaar

        Args:
            planning: Lijst van planning regels
            gebruiker_id: Optioneel filter op gebruiker

        Returns:
            ConstraintCheckResult met violations
        """
        violations = []
        max_weekends = int(self.hr_config.get('max_weekends_achter_elkaar', 6))
        weekend_def = self.hr_config.get('weekend_definitie', 'vr-22:00|ma-06:00')

        # Filter op gebruiker indien opgegeven
        if gebruiker_id:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]

        if not planning:
            return ConstraintCheckResult(passed=True, violations=[], metadata={})

        # Parse weekend definitie
        start_dag, start_uur, eind_dag, eind_uur = self._parse_periode_definitie(weekend_def)

        # Bepaal datumbereik
        min_datum = min(p.datum for p in planning)
        max_datum = max(p.datum for p in planning)

        # Generate weekends
        weekends = self._generate_weekends(min_datum, max_datum, start_dag, start_uur, eind_dag, eind_uur)

        # Check welke weekends gewerkt zijn
        gewerkte_weekends = []
        for weekend_start, weekend_eind in weekends:
            heeft_shifts = False
            weekend_shifts = []

            for p in planning:
                if not p.shift_code:
                    continue

                # Check of shift overlapt met weekend
                if self._shift_overlapt_weekend(p.datum, p.shift_code, weekend_start, weekend_eind):
                    heeft_shifts = True
                    weekend_shifts.append(p)

            if heeft_shifts:
                gewerkte_weekends.append({
                    'start': weekend_start,
                    'eind': weekend_eind,
                    'shifts': weekend_shifts
                })

        # Tel opeenvolgende gewerkte weekends
        if len(gewerkte_weekends) > 0:
            reeks_length = 1
            reeks_start = gewerkte_weekends[0]

            for i in range(1, len(gewerkte_weekends)):
                # Check of opeenvolgend (7 dagen verschil)
                dagen_verschil = (gewerkte_weekends[i]['start'].date() - gewerkte_weekends[i-1]['start'].date()).days

                if dagen_verschil == 7:  # Opeenvolgend weekend
                    reeks_length += 1

                    # Check violation
                    if reeks_length > max_weekends:
                        all_shifts = []
                        for j in range(i - reeks_length + 1, i + 1):
                            all_shifts.extend(gewerkte_weekends[j]['shifts'])

                        violations.append(Violation(
                            type=ViolationType.MAX_WEEKENDS,
                            severity=ViolationSeverity.ERROR,
                            gebruiker_id=gebruiker_id or all_shifts[0].gebruiker_id,
                            datum=None,
                            datum_range=(reeks_start['start'].date(), gewerkte_weekends[i]['eind'].date()),
                            beschrijving=f"Te veel weekends achter elkaar: {reeks_length} weekends gewerkt (maximaal {max_weekends})",
                            details={
                                'reeks_start': reeks_start['start'].isoformat(),
                                'reeks_eind': gewerkte_weekends[i]['eind'].isoformat(),
                                'weekends_count': reeks_length,
                                'max_weekends': max_weekends
                            },
                            affected_shifts=[(s.gebruiker_id, s.datum) for s in all_shifts],
                            suggested_fixes=[
                                f"Verwijder weekend shift uit {reeks_length - max_weekends} weekend(s)",
                                "Plan weekend vrij",
                                "Verplaats shift naar buiten weekend periode"
                            ]
                        ))
                else:
                    # Reeks breekt
                    reeks_length = 1
                    reeks_start = gewerkte_weekends[i]

        return ConstraintCheckResult(
            passed=len(violations) == 0,
            violations=violations,
            metadata={'total_weekends': len(weekends), 'gewerkte_weekends': len(gewerkte_weekends), 'violations_count': len(violations)}
        )

    def _generate_weekends(
        self,
        min_datum: date,
        max_datum: date,
        start_dag: str,
        start_uur: str,
        eind_dag: str,
        eind_uur: str
    ) -> List[Tuple[datetime, datetime]]:
        """
        Generate lijst van weekend periodes

        Args:
            min_datum: Eerste datum
            max_datum: Laatste datum
            start_dag: Weekend start dag (bijv. 'vr')
            start_uur: Weekend start tijd (bijv. '22:00')
            eind_dag: Weekend eind dag (bijv. 'ma')
            eind_uur: Weekend eind tijd (bijv. '06:00')

        Returns:
            List van (weekend_start, weekend_eind) datetime tuples
        """
        dag_map = {
            'ma': 0, 'di': 1, 'wo': 2, 'do': 3,
            'vr': 4, 'za': 5, 'zo': 6
        }

        start_weekday = dag_map.get(start_dag.lower(), 4)  # Default vrijdag

        # Vind eerste weekend start (vrijdag op of voor min_datum)
        current = min_datum
        while current.weekday() != start_weekday:
            current -= timedelta(days=1)

        weekends = []

        while current <= max_datum:
            # Weekend start
            weekend_start = datetime.combine(current, self._parse_tijd(start_uur))

            # Weekend eind (meestal maandag, 3 dagen later)
            eind_weekday = dag_map.get(eind_dag.lower(), 0)  # Default maandag
            dagen_tot_eind = (eind_weekday - start_weekday) % 7
            if dagen_tot_eind == 0:
                dagen_tot_eind = 7

            weekend_eind_datum = current + timedelta(days=dagen_tot_eind)
            weekend_eind = datetime.combine(weekend_eind_datum, self._parse_tijd(eind_uur))

            weekends.append((weekend_start, weekend_eind))

            # Volgende weekend (7 dagen later)
            current += timedelta(days=7)

        return weekends

    def _shift_overlapt_weekend(
        self,
        shift_datum: date,
        shift_code: str,
        weekend_start: datetime,
        weekend_eind: datetime
    ) -> bool:
        """
        Check of shift overlapt met weekend periode

        Args:
            shift_datum: Datum van shift
            shift_code: Code van shift
            weekend_start: Weekend start datetime
            weekend_eind: Weekend eind datetime

        Returns:
            True als shift overlapt met weekend
        """
        if shift_code not in self.shift_tijden:
            return False

        shift_info = self.shift_tijden[shift_code]
        start_uur = shift_info.get('start_uur')
        eind_uur = shift_info.get('eind_uur')

        if not start_uur or not eind_uur:
            return False

        # Bereken shift start/eind datetime
        shift_start = datetime.combine(shift_datum, self._parse_tijd(start_uur))
        shift_eind = datetime.combine(shift_datum, self._parse_tijd(eind_uur))

        # Handle middernacht crossing
        if shift_eind < shift_start:
            shift_eind += timedelta(days=1)

        # Check overlap (exclusieve grenzen)
        return self._check_periode_overlap(shift_start, shift_eind, weekend_start, weekend_eind)

    def check_nacht_gevolgd_door_vroeg(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> ConstraintCheckResult:
        """
        Check: Nacht shift activeert "nacht-modus" totdat patroon doorbroken wordt (v0.6.26)

        Business Rules:
        - Na nacht shift: "nacht-modus" actief
        - RX/CX shifts of lege dagen: blijven IN nacht-modus (fysiek herstel, maar niet genoeg)
        - Breek codes (VV, Z, etc.): EXIT nacht-modus (volledig herstel)
        - Vroeg tijdens nacht-modus: VERBODEN
        - Andere shifts (laat, nacht): EXIT nacht-modus (patroon onderbroken)

        Voorbeelden:
        - Nacht -> RX -> CX -> RX -> Vroeg: VIOLATION (eindeloos in nacht-modus)
        - Nacht -> RX -> VV -> Vroeg: OK (VV breekt nacht-modus)
        - Nacht -> RX -> Laat: OK (laat breekt nacht-modus)

        Args:
            planning: Lijst van planning regels
            gebruiker_id: Optioneel filter op gebruiker

        Returns:
            ConstraintCheckResult met violations
        """
        # Lees breek terms uit HR config (default: verlof,ziek)
        breek_terms_str = self.hr_config.get('Nacht gevolgd door vroeg verboden', 'verlof,ziek')
        breek_terms = {term.strip() for term in breek_terms_str.split(',')}

        # Filter planning op gebruiker
        if gebruiker_id is not None:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]

        # Sort op datum
        planning = sorted(planning, key=lambda p: p.datum)

        violations = []

        # Loop door planning om nacht shifts te vinden
        for i, huidige in enumerate(planning):
            # Check of huidige shift een nacht is
            if not huidige.shift_code:
                continue

            is_nacht = self._is_shift_type(huidige.shift_code, 'nacht')
            if not is_nacht:
                continue

            # Nacht gevonden - activeer "nacht-modus" en scan vooruit
            nacht_datum = huidige.datum
            verwachte_datum = nacht_datum

            # Scan vooruit totdat patroon doorbroken wordt
            for j in range(i + 1, len(planning)):
                volgende = planning[j]
                verwachte_datum = verwachte_datum + timedelta(days=1)

                # Check of we nog consecutive dagen hebben
                if volgende.datum != verwachte_datum:
                    # Gap in planning - exit nacht-modus
                    break

                # Lege dag (geen shift_code) - blijf in nacht-modus, continue scan
                if not volgende.shift_code:
                    continue

                # Check of dit een breek code is (VV, Z, etc.)
                heeft_breek_code = self._has_term_match(volgende.shift_code, breek_terms)
                if heeft_breek_code:
                    # Breek code gevonden - exit nacht-modus
                    break

                # Check of dit RX of CX is
                is_rx_of_cx = self._is_rx_of_cx(volgende.shift_code)
                if is_rx_of_cx:
                    # RX/CX - blijf in nacht-modus, continue scan
                    continue

                # Check of dit een vroeg shift is
                is_vroeg = self._is_shift_type(volgende.shift_code, 'vroeg')
                if is_vroeg:
                    # VIOLATION: Vroeg tijdens nacht-modus
                    # Bepaal tussenliggende dagen voor beschrijving
                    dagen_tussen = (volgende.datum - nacht_datum).days - 1

                    if dagen_tussen > 0:
                        tussen_info = f" (na {dagen_tussen} rustdag(en))"
                    else:
                        tussen_info = " (direct)"

                    violations.append(Violation(
                        type=ViolationType.NACHT_VROEG_VERBODEN,
                        severity=ViolationSeverity.ERROR,
                        gebruiker_id=volgende.gebruiker_id,
                        datum=volgende.datum,
                        datum_range=(nacht_datum, volgende.datum),
                        beschrijving=f"Vroeg shift na nacht shift zonder volledig herstel{tussen_info}: nacht op {nacht_datum.strftime('%d %b')} -> vroeg op {volgende.datum.strftime('%d %b')}",
                        details={
                            'nacht_shift': huidige.shift_code,
                            'nacht_datum': nacht_datum.isoformat(),
                            'vroeg_shift': volgende.shift_code,
                            'vroeg_datum': volgende.datum.isoformat(),
                            'breek_terms': list(breek_terms),
                            'dagen_tussen': dagen_tussen
                        },
                        affected_shifts=[
                            (huidige.gebruiker_id, nacht_datum),
                            (volgende.gebruiker_id, volgende.datum)
                        ],
                        suggested_fixes=[
                            f"Plan volledig herstel (verlof/ziekte) voor vroeg shift op {volgende.datum.strftime('%d %b')}",
                            f"Verander vroeg shift op {volgende.datum.strftime('%d %b')} naar laat of nacht",
                            f"Verander nacht shift op {nacht_datum.strftime('%d %b')} naar laat"
                        ]
                    ))
                    # Exit nacht-modus na violation detectie
                    break

                # Andere shift (laat, nacht) - exit nacht-modus
                break

        return ConstraintCheckResult(
            passed=len(violations) == 0,
            violations=violations,
            metadata={'violations_count': len(violations)}
        )

    def _is_rx_of_cx(self, shift_code: str) -> bool:
        """
        Check of shift_code een RX (zondagrust) of CX (zaterdagrust) is

        Args:
            shift_code: Code van shift

        Returns:
            True als RX of CX, anders False
        """
        if shift_code not in self.shift_tijden:
            return False

        shift_info = self.shift_tijden[shift_code]
        term = shift_info.get('term')

        return term in ('zondagrust', 'zaterdagrust')

    # ========================================================================
    # INTEGRATION & CONVENIENCE
    # ========================================================================

    def check_all(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None,
        rode_lijnen: Optional[List[Dict]] = None
    ) -> Dict[str, ConstraintCheckResult]:
        """
        Run alle constraint checks

        Args:
            planning: Planning regels
            gebruiker_id: Optioneel filter op gebruiker
            rode_lijnen: Rode lijn periodes (voor cyclus check)

        Returns:
            Dict met results per regel:
            {
                'min_rust_12u': ConstraintCheckResult(...),
                'max_uren_week': ConstraintCheckResult(...),
                ...
            }
        """
        results = {}

        # Run alle checks
        results['min_rust_12u'] = self.check_12u_rust(planning, gebruiker_id)
        results['max_uren_week'] = self.check_max_uren_week(planning, gebruiker_id)
        results['max_werkdagen_cyclus'] = self.check_max_werkdagen_cyclus(planning, gebruiker_id, rode_lijnen)
        results['max_dagen_tussen_rx'] = self.check_max_dagen_tussen_rx(planning, gebruiker_id)
        results['max_werkdagen_reeks'] = self.check_max_werkdagen_reeks(planning, gebruiker_id)
        results['max_weekends'] = self.check_max_weekends_achter_elkaar(planning, gebruiker_id)
        results['nacht_vroeg_verboden'] = self.check_nacht_gevolgd_door_vroeg(planning, gebruiker_id)

        return results

    def get_all_violations(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None,
        rode_lijnen: Optional[List[Dict]] = None
    ) -> List[Violation]:
        """
        Convenience method: flatten alle violations

        Args:
            planning: Planning regels
            gebruiker_id: Optioneel filter op gebruiker
            rode_lijnen: Rode lijn periodes

        Returns:
            Flat list van alle violations, gesorteerd op datum
        """
        results = self.check_all(planning, gebruiker_id, rode_lijnen)

        all_violations = []
        for result in results.values():
            all_violations.extend(result.violations)

        # Sort op datum (None dates last)
        all_violations.sort(key=lambda v: v.datum or date.max)

        return all_violations
