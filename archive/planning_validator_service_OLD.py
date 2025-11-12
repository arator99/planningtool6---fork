# services/planning_validator_service.py
"""
Planning Validator Service - HR Regels Validatie Systeem

Dit service valideert planning records tegen 6 HR regels:
1. Minimum 12u rust tussen shifts
2. Maximum 50u per week
3. Maximum 19 werkdagen per 28-dagen cyclus
4. Maximum 7 dagen tussen rustdagen (RX/CX)
5. Maximum 7 werkdagen achter elkaar
6. Maximum weekends achter elkaar

Versie: v0.6.25 (Fase 1 - Service Layer)
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, time as time_type
from database.connection import get_connection


@dataclass
class Violation:
    """
    Data class voor HR regel overtredingen

    Attributes:
        regel: Identificatie van de regel (bijv. 'min_rust_12u')
        datum: Datum van violation (voor single-day violations)
        datum_range: Tuple (start, eind) voor multi-day violations (bijv. week violations)
        gebruiker_id: ID van gebruiker met violation
        beschrijving: User-friendly Nederlandse beschrijving
        severity: 'error' of 'warning'
        details: Extra context (shift codes, uren, etc.)
    """
    regel: str
    gebruiker_id: int
    beschrijving: str
    severity: str = 'error'
    datum: Optional[str] = None
    datum_range: Optional[Tuple[str, str]] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialiseer naar dictionary voor caching/logging"""
        return asdict(self)

    def to_user_message(self) -> str:
        """
        User-friendly bericht voor dialogs

        Returns:
            Formatted string met beschrijving + datum context
        """
        msg = self.beschrijving

        if self.datum:
            msg += f" (datum: {self.datum})"
        elif self.datum_range:
            start, eind = self.datum_range
            msg += f" (periode: {start} t/m {eind})"

        return msg

    def __repr__(self) -> str:
        """String representatie voor debugging"""
        return f"Violation(regel={self.regel}, datum={self.datum}, severity={self.severity})"


# ============================================================================
# HELPER FUNCTIONS - Tijd Berekening
# ============================================================================

def parse_tijd(tijd_str: str) -> time_type:
    """
    Parse tijd string naar time object

    Args:
        tijd_str: Tijd in format "HH:MM" (bijv. "14:30")

    Returns:
        time object

    Raises:
        ValueError: Als format incorrect is
    """
    try:
        parts = tijd_str.split(':')
        if len(parts) != 2:
            raise ValueError(f"Invalid tijd format: {tijd_str}")

        uur = int(parts[0])
        minuut = int(parts[1])

        if not (0 <= uur <= 23 and 0 <= minuut <= 59):
            raise ValueError(f"Tijd out of range: {tijd_str}")

        return time_type(uur, minuut)

    except (ValueError, IndexError) as e:
        raise ValueError(f"Kan tijd niet parsen: {tijd_str}") from e


def bereken_shift_duur(start_uur: str, eind_uur: str) -> float:
    """
    Bereken shift duur in uren (handelt middernacht crossing)

    Args:
        start_uur: Start tijd "HH:MM"
        eind_uur: Eind tijd "HH:MM"

    Returns:
        Shift duur in uren (float)

    Examples:
        >>> bereken_shift_duur("06:00", "14:00")
        8.0
        >>> bereken_shift_duur("22:00", "06:00")  # Over middernacht
        8.0
        >>> bereken_shift_duur("14:15", "22:45")
        8.5
    """
    try:
        start = datetime.strptime(start_uur, "%H:%M")
        eind = datetime.strptime(eind_uur, "%H:%M")

        # Check middernacht crossing
        if eind < start:
            eind += timedelta(days=1)

        delta = eind - start
        return delta.total_seconds() / 3600

    except ValueError as e:
        raise ValueError(f"Kan shift duur niet berekenen: {start_uur} - {eind_uur}") from e


def bereken_rust_tussen_shifts(
    datum1: str,
    eind_uur1: str,
    datum2: str,
    start_uur2: str
) -> float:
    """
    Bereken rust tussen twee shifts in uren

    Args:
        datum1: Datum eerste shift "YYYY-MM-DD"
        eind_uur1: Eind tijd eerste shift "HH:MM"
        datum2: Datum tweede shift "YYYY-MM-DD"
        start_uur2: Start tijd tweede shift "HH:MM"

    Returns:
        Aantal uren rust (kan negatief zijn bij overlap)

    Examples:
        >>> bereken_rust_tussen_shifts("2025-11-15", "22:00", "2025-11-16", "06:00")
        8.0
        >>> bereken_rust_tussen_shifts("2025-11-15", "22:00", "2025-11-16", "08:30")
        10.5
    """
    try:
        dt1_eind = datetime.strptime(f"{datum1} {eind_uur1}", "%Y-%m-%d %H:%M")
        dt2_start = datetime.strptime(f"{datum2} {start_uur2}", "%Y-%m-%d %H:%M")

        delta = dt2_start - dt1_eind
        return delta.total_seconds() / 3600

    except ValueError as e:
        raise ValueError(
            f"Kan rust niet berekenen: {datum1} {eind_uur1} -> {datum2} {start_uur2}"
        ) from e


# ============================================================================
# HELPER FUNCTIONS - Periode Parsing
# ============================================================================

def parse_periode_definitie(waarde: str) -> Tuple[str, str, str, str]:
    """
    Parse periode definitie string

    Args:
        waarde: Format "dag-HH:MM|dag-HH:MM" (bijv. "ma-00:00|zo-23:59")

    Returns:
        Tuple (start_dag, start_uur, eind_dag, eind_uur)

    Examples:
        >>> parse_periode_definitie("ma-00:00|zo-23:59")
        ('ma', '00:00', 'zo', '23:59')
        >>> parse_periode_definitie("vr-22:00|ma-06:00")
        ('vr', '22:00', 'ma', '06:00')

    Raises:
        ValueError: Als format incorrect is
    """
    try:
        start, eind = waarde.split('|')
        start_dag, start_uur = start.split('-', 1)
        eind_dag, eind_uur = eind.split('-', 1)

        return (
            start_dag.strip(),
            start_uur.strip(),
            eind_dag.strip(),
            eind_uur.strip()
        )

    except (ValueError, IndexError) as e:
        raise ValueError(f"Kan periode definitie niet parsen: {waarde}") from e


def dag_naar_weekday(dag_kort: str) -> int:
    """
    Converteer dag afkorting naar weekday nummer

    Args:
        dag_kort: 'ma', 'di', 'wo', 'do', 'vr', 'za', 'zo'

    Returns:
        Weekday nummer (0=maandag, 6=zondag)

    Raises:
        ValueError: Als dag onbekend is
    """
    mapping = {
        'ma': 0, 'di': 1, 'wo': 2, 'do': 3,
        'vr': 4, 'za': 5, 'zo': 6
    }

    if dag_kort not in mapping:
        raise ValueError(f"Onbekende dag: {dag_kort}")

    return mapping[dag_kort]


def shift_overlapt_periode(
    shift_datum: str,
    shift_start: str,
    shift_eind: str,
    periode_start: datetime,
    periode_eind: datetime
) -> bool:
    """
    Check of shift overlapt met periode (exclusieve grenzen)

    Logica: (shift_start < periode_eind) AND (shift_eind > periode_start)

    Shift op de grens = GEEN overlap (exclusieve grenzen)

    Args:
        shift_datum: "YYYY-MM-DD"
        shift_start: "HH:MM"
        shift_eind: "HH:MM"
        periode_start: datetime object
        periode_eind: datetime object

    Returns:
        True als overlap, False anders

    Examples:
        Weekend vr 22:00 - ma 06:00:
        - Shift vr 14:00-22:00 → False (eindigt OP grens, niet binnen)
        - Shift vr 14:00-22:01 → True (eindigt NA grens, wel binnen)
        - Shift ma 06:00-14:00 → False (begint OP grens, niet binnen)
        - Shift ma 05:59-14:00 → True (begint VOOR grens, wel binnen)
    """
    try:
        shift_start_dt = datetime.strptime(f"{shift_datum} {shift_start}", "%Y-%m-%d %H:%M")
        shift_eind_dt = datetime.strptime(f"{shift_datum} {shift_eind}", "%Y-%m-%d %H:%M")

        # Middernacht crossing handling
        if shift_eind_dt <= shift_start_dt:
            shift_eind_dt += timedelta(days=1)

        # Exclusieve grenzen check
        return (shift_start_dt < periode_eind) and (shift_eind_dt > periode_start)

    except ValueError as e:
        raise ValueError(
            f"Kan overlap niet bepalen: {shift_datum} {shift_start}-{shift_eind}"
        ) from e


# ============================================================================
# PLANNING VALIDATOR CLASS
# ============================================================================

class PlanningValidator:
    """
    Centraal validatie systeem voor alle HR regels

    Usage:
        validator = PlanningValidator(gebruiker_id=123, jaar=2025, maand=11)
        violations = validator.validate_all()

        # Of voor real-time validatie:
        violations = validator.validate_shift(datum="2025-11-15", shift_code="7101")
    """

    def __init__(self, gebruiker_id: int, jaar: int, maand: int):
        """
        Initialize validator voor specifieke gebruiker + maand

        Args:
            gebruiker_id: ID van gebruiker
            jaar: Jaar (YYYY)
            maand: Maand (1-12)
        """
        self.gebruiker_id = gebruiker_id
        self.jaar = jaar
        self.maand = maand

        # Laad HR regels configuratie uit database
        self.hr_config = self._load_hr_config()

        # Laad planning data voor maand
        self.planning_data: List[Dict[str, Any]] = self._load_planning_data()

        # Cache voor shift tijden lookups
        self._shift_tijden_cache: Dict[str, Optional[Tuple[str, str]]] = {}

    def _load_hr_config(self) -> Dict[str, Any]:
        """
        Laad HR regels configuratie uit database

        Returns:
            Dictionary met HR regel waarden
        """
        from services.hr_regels_service import HRRegelsService

        return {
            'min_rust_uren': HRRegelsService.get_min_rust_uren(),
            'max_uren_week': HRRegelsService.get_max_uren_week(),
            'max_werkdagen_cyclus': HRRegelsService.get_max_werkdagen_cyclus(),
            'max_dagen_tussen_rx': HRRegelsService.get_max_dagen_tussen_rx(),
            'max_werkdagen_reeks': HRRegelsService.get_max_werkdagen_reeks(),
            'max_weekends': HRRegelsService.get_max_weekends_achter_elkaar(),
            'week_definitie': HRRegelsService.get_week_definitie(),
            'weekend_definitie': HRRegelsService.get_weekend_definitie(),
        }

    def _load_planning_data(self) -> List[Dict[str, Any]]:
        """
        Laad planning data voor gebruiker + maand

        Returns:
            List van planning records (datum, shift_code, notitie)
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Bepaal datum range voor maand
        start_datum = f"{self.jaar}-{self.maand:02d}-01"

        # Eind datum = eerste dag volgende maand
        if self.maand == 12:
            eind_datum = f"{self.jaar + 1}-01-01"
        else:
            eind_datum = f"{self.jaar}-{self.maand + 1:02d}-01"

        cursor.execute("""
            SELECT datum, shift_code, notitie, status
            FROM planning
            WHERE gebruiker_id = ?
              AND datum >= ?
              AND datum < ?
            ORDER BY datum
        """, (self.gebruiker_id, start_datum, eind_datum))

        rows = cursor.fetchall()

        return [
            {
                'datum': row[0],
                'shift_code': row[1],
                'notitie': row[2],
                'status': row[3]
            }
            for row in rows
        ]

    def get_shift_tijden(self, shift_code: str) -> Optional[Tuple[str, str]]:
        """
        Haal shift start/eind tijden op (met caching)

        Args:
            shift_code: Shift code (bijv. "7101", "VV")

        Returns:
            Tuple (start_uur, eind_uur) of None als niet gevonden
        """
        # Check cache
        if shift_code in self._shift_tijden_cache:
            return self._shift_tijden_cache[shift_code]

        conn = get_connection()
        cursor = conn.cursor()

        # Probeer eerst shift_codes tabel
        cursor.execute("""
            SELECT start_uur, eind_uur
            FROM shift_codes
            WHERE code = ?
        """, (shift_code,))

        row = cursor.fetchone()
        if row:
            result = (row[0], row[1])
            self._shift_tijden_cache[shift_code] = result
            return result

        # Speciale codes hebben geen tijden
        self._shift_tijden_cache[shift_code] = None
        return None

    # ========================================================================
    # PUBLIC API - Validatie Methodes
    # ========================================================================

    def validate_all(self) -> Dict[str, List[Violation]]:
        """
        Run alle validaties voor complete maand

        Returns:
            Dictionary met violations per regel:
            {
                'min_rust_12u': [Violation(...), ...],
                'max_uren_week': [...],
                'max_werkdagen_cyclus': [...],
                'max_dagen_tussen_rx': [...],
                'max_werkdagen_reeks': [...],
                'max_weekends': [...]
            }
        """
        results = {}

        # TODO Fase 2: Implementeer checks
        results['min_rust_12u'] = self.check_12u_rust()
        results['max_uren_week'] = self.check_max_uren_week()
        results['max_werkdagen_cyclus'] = self.check_max_werkdagen_cyclus()
        results['max_dagen_tussen_rx'] = self.check_max_dagen_tussen_rx()
        results['max_werkdagen_reeks'] = self.check_max_werkdagen_reeks()
        results['max_weekends'] = self.check_max_weekends_achter_elkaar()

        return results

    def validate_shift(self, datum: str, shift_code: str) -> List[Violation]:
        """
        Light validatie voor single shift (real-time feedback)

        Checks alleen:
        - 12u rust (vorige/volgende dag)
        - 50u week (huidige week)

        Niet: 19 dagen cyclus, weekends (te zwaar voor real-time)

        Args:
            datum: Datum "YYYY-MM-DD"
            shift_code: Shift code

        Returns:
            List van violations
        """
        violations = []

        # TODO Fase 2: Light checks implementeren
        violations.extend(self._check_12u_rust_single(datum))
        violations.extend(self._check_50u_week_single(datum))

        return violations

    def get_violation_level(self, datum: str) -> str:
        """
        Bepaal violation level voor UI overlay kleur

        Args:
            datum: Datum "YYYY-MM-DD"

        Returns:
            'none', 'warning', of 'error'
        """
        # Voor nu: dummy implementation
        # TODO Fase 3: Implementeren met cache lookup
        return 'none'

    # ========================================================================
    # HR REGELS - Check Methodes (STUBS - Fase 2 implementatie)
    # ========================================================================

    def check_12u_rust(self) -> List[Violation]:
        """
        Check minimum 12u rust tussen shifts

        Business rules:
        - Minimum 12u rust verplicht tussen opeenvolgende shifts
        - Reset codes (RX, CX, Z) breken de reeks (geen check na deze codes)
        - Speciale codes zonder tijden (VV, KD, etc.) tellen niet als shift
        - Edge cases: laatste dag vorige maand + eerste dag volgende maand

        Returns:
            List van Violation objecten
        """
        violations = []

        # Haal extended planning data (met buffer voor edge cases)
        shifts = self._get_shifts_with_buffer()

        if len(shifts) < 2:
            return violations  # Niet genoeg shifts om te checken

        # Loop door opeenvolgende shift dagen
        for i in range(len(shifts) - 1):
            huidige = shifts[i]
            volgende = shifts[i + 1]

            # Check of volgende shift reset flag heeft
            if self._heeft_reset_flag(volgende['shift_code']):
                continue  # Reset code: geen 12u rust check nodig

            # Haal shift tijden op
            huidige_tijden = self.get_shift_tijden(huidige['shift_code'])
            volgende_tijden = self.get_shift_tijden(volgende['shift_code'])

            if not huidige_tijden or not volgende_tijden:
                continue  # Geen tijden beschikbaar

            # Bereken rust tussen shifts
            rust_uren = bereken_rust_tussen_shifts(
                huidige['datum'],
                huidige_tijden[1],  # eind_uur
                volgende['datum'],
                volgende_tijden[0]  # start_uur
            )

            # Check violation
            if rust_uren < self.hr_config['min_rust_uren']:
                violations.append(Violation(
                    regel='min_rust_12u',
                    gebruiker_id=self.gebruiker_id,
                    beschrijving=f"Slechts {rust_uren:.1f}u rust tussen shifts (minimum {self.hr_config['min_rust_uren']:.0f}u vereist)",
                    severity='error',
                    datum_range=(huidige['datum'], volgende['datum']),
                    details={
                        'shift1_datum': huidige['datum'],
                        'shift1_code': huidige['shift_code'],
                        'shift1_eind': huidige_tijden[1],
                        'shift2_datum': volgende['datum'],
                        'shift2_code': volgende['shift_code'],
                        'shift2_start': volgende_tijden[0],
                        'rust_uren': round(rust_uren, 1),
                        'min_vereist': self.hr_config['min_rust_uren']
                    }
                ))

        return violations

    def check_max_uren_week(self) -> List[Violation]:
        """
        Check maximum 50u per week

        Business rules:
        - Week definitie configureerbaar (default: ma 00:00 - zo 23:59)
        - Shifts die overlappen met week tellen mee
        - Exclusieve grenzen: shift op grens = geen overlap

        Returns:
            List van Violation objecten
        """
        violations = []

        # Parse week definitie
        week_def = self.hr_config['week_definitie']
        start_dag, start_uur, eind_dag, eind_uur = week_def

        # Bepaal alle weken in relevante range (met buffer)
        weken = self._get_weken_in_range(start_dag, start_uur, eind_dag, eind_uur)

        # Check elke week
        for week_start, week_eind in weken:
            uren_totaal = 0.0
            shifts_in_week = []

            # Loop door alle planning records
            for record in self.planning_data:
                shift_code = record['shift_code']
                if not shift_code:
                    continue

                # Haal shift tijden op
                tijden = self.get_shift_tijden(shift_code)
                if not tijden:
                    continue  # Speciale code zonder tijden

                # Check of shift overlapt met week
                if shift_overlapt_periode(
                    record['datum'],
                    tijden[0],  # start_uur
                    tijden[1],  # eind_uur
                    week_start,
                    week_eind
                ):
                    # Bereken shift duur
                    duur = bereken_shift_duur(tijden[0], tijden[1])
                    uren_totaal += duur
                    shifts_in_week.append({
                        'datum': record['datum'],
                        'code': shift_code,
                        'uren': duur
                    })

            # Check violation
            if uren_totaal > self.hr_config['max_uren_week']:
                # Bepaal datum range voor violation
                eerste_datum = min(s['datum'] for s in shifts_in_week)
                laatste_datum = max(s['datum'] for s in shifts_in_week)

                violations.append(Violation(
                    regel='max_uren_week',
                    gebruiker_id=self.gebruiker_id,
                    beschrijving=f"{uren_totaal:.1f}u gewerkt in week (maximum {self.hr_config['max_uren_week']:.0f}u)",
                    severity='error',
                    datum_range=(eerste_datum, laatste_datum),
                    details={
                        'uren_totaal': round(uren_totaal, 1),
                        'max_uren': self.hr_config['max_uren_week'],
                        'week_start': week_start.isoformat(),
                        'week_eind': week_eind.isoformat(),
                        'shifts': shifts_in_week
                    }
                ))

        return violations

    def check_max_werkdagen_cyclus(self) -> List[Violation]:
        """
        Check maximum 19 werkdagen per 28-dagen cyclus

        TODO Fase 2: Implementeer logica
        - Hergebruik logic uit planner_grid_kalender.py
        - get_relevante_rode_lijn_periodes()
        - tel_gewerkte_dagen()
        - Return violations als > 19 dagen

        Returns:
            List van Violation objecten
        """
        # STUB - Fase 2
        return []

    def check_max_dagen_tussen_rx(self) -> List[Violation]:
        """
        Check maximum 7 dagen tussen rustdagen (RX/CX)

        TODO Fase 2: Implementeer logica
        - Haal alle RX/CX codes (term-based)
        - Loop door opeenvolgende rustdagen
        - Bereken dagen tussen
        - Return violations als > 7 dagen

        Returns:
            List van Violation objecten
        """
        # STUB - Fase 2
        return []

    def check_max_werkdagen_reeks(self) -> List[Violation]:
        """
        Check maximum 7 werkdagen achter elkaar

        TODO Fase 2: Implementeer logica
        - State machine: tel werkdagen
        - Reset bij breekt_werk_reeks flag of lege cel
        - Track max reeks
        - Return violations als > 7 dagen

        Returns:
            List van Violation objecten
        """
        # STUB - Fase 2
        return []

    def check_max_weekends_achter_elkaar(self) -> List[Violation]:
        """
        Check maximum weekends achter elkaar

        TODO Fase 2: Implementeer logica
        - Parse weekend definitie
        - Bepaal alle weekends in range
        - Per weekend: check shift overlap
        - Tel opeenvolgende weekends met shifts
        - Return violations als > 6 weekends

        Returns:
            List van Violation objecten
        """
        # STUB - Fase 2
        return []

    # ========================================================================
    # PRIVATE HELPERS - Data Loading
    # ========================================================================

    def _get_shifts_with_buffer(self) -> List[Dict]:
        """
        Haal planning records met buffer voor edge cases

        Laadt:
        - Laatste 2 dagen vorige maand
        - Huidige maand
        - Eerste 2 dagen volgende maand

        Filtert alleen records met shift tijden (geen speciale codes zonder tijden)

        Returns:
            List van dicts met 'datum' en 'shift_code', gesorteerd op datum
        """
        from datetime import date
        from dateutil.relativedelta import relativedelta

        conn = get_connection()
        cursor = conn.cursor()

        # Bepaal date range
        huidige_maand_start = date(self.jaar, self.maand, 1)
        vorige_maand_start = huidige_maand_start - relativedelta(months=1)
        volgende_maand_start = huidige_maand_start + relativedelta(months=1)
        volgende_maand_eind = volgende_maand_start + relativedelta(days=2)

        # Query extended range
        cursor.execute("""
            SELECT datum, shift_code
            FROM planning
            WHERE gebruiker_id = ?
              AND datum >= date(?, '-2 days')
              AND datum < ?
            ORDER BY datum
        """, (
            self.gebruiker_id,
            huidige_maand_start.isoformat(),
            volgende_maand_eind.isoformat()
        ))

        rows = cursor.fetchall()
        conn.close()

        # Filter alleen shifts met tijden (geen VV, KD, etc.)
        shifts = []
        for row in rows:
            shift_code = row['shift_code']
            if not shift_code:
                continue

            # Check of shift tijden heeft
            tijden = self.get_shift_tijden(shift_code)
            if tijden:  # Alleen toevoegen als tijden beschikbaar
                shifts.append({
                    'datum': row['datum'],
                    'shift_code': shift_code
                })

        return shifts

    def _heeft_reset_flag(self, shift_code: str) -> bool:
        """
        Check of shift_code reset_12u_rust flag heeft

        Reset codes (RX, CX, Z) breken de 12u rust reeks

        Args:
            shift_code: Shift code om te checken

        Returns:
            True als code reset flag heeft, anders False
        """
        if not shift_code:
            return False

        conn = get_connection()
        cursor = conn.cursor()

        # Check speciale_codes tabel voor reset flag
        cursor.execute("""
            SELECT reset_12u_rust
            FROM speciale_codes
            WHERE code = ?
        """, (shift_code,))

        row = cursor.fetchone()
        conn.close()

        if row and row['reset_12u_rust']:
            return True

        return False

    def _get_weken_in_range(self, start_dag: str, start_uur: str,
                           eind_dag: str, eind_uur: str) -> List[Tuple[datetime, datetime]]:
        """
        Bepaal alle weken in relevante range (maand + buffer)

        Week definitie: bijv. ma-00:00 tot zo-23:59

        Args:
            start_dag: Week start dag ('ma', 'di', etc.)
            start_uur: Week start uur ('00:00', etc.)
            eind_dag: Week eind dag ('zo', etc.)
            eind_uur: Week eind uur ('23:59', etc.)

        Returns:
            List van (week_start, week_eind) datetime tuples
        """
        from datetime import date, timedelta

        # Bepaal range (maand + 7 dagen buffer aan beide kanten)
        eerste_dag_maand = date(self.jaar, self.maand, 1)
        range_start = eerste_dag_maand - timedelta(days=7)

        # Laatste dag van maand
        if self.maand == 12:
            laatste_dag_maand = date(self.jaar + 1, 1, 1) - timedelta(days=1)
        else:
            laatste_dag_maand = date(self.jaar, self.maand + 1, 1) - timedelta(days=1)
        range_eind = laatste_dag_maand + timedelta(days=7)

        # Bepaal weekday nummers
        start_weekday = dag_naar_weekday(start_dag)

        # Vind eerste week start in range
        current_date = range_start
        while current_date.weekday() != start_weekday:
            current_date += timedelta(days=1)

        # Genereer alle weken
        weken = []
        while current_date <= range_eind:
            # Week start
            week_start = datetime.combine(current_date, parse_tijd(start_uur).time())

            # Week eind (7 dagen later, maar op eind_dag)
            # Bereken dagen tot eind_dag
            eind_weekday = dag_naar_weekday(eind_dag)
            dagen_verschil = (eind_weekday - start_weekday) % 7
            if dagen_verschil == 0:
                dagen_verschil = 7  # Volledige week

            week_eind_date = current_date + timedelta(days=dagen_verschil)
            week_eind = datetime.combine(week_eind_date, parse_tijd(eind_uur).time())

            weken.append((week_start, week_eind))

            # Volgende week (7 dagen later)
            current_date += timedelta(days=7)

        return weken

    # ========================================================================
    # PRIVATE HELPERS - Light Validatie
    # ========================================================================

    def _check_12u_rust_single(self, datum: str) -> List[Violation]:
        """
        Light 12u rust check voor single datum (real-time)

        Checks alleen vorige en volgende dag

        Args:
            datum: Datum "YYYY-MM-DD"

        Returns:
            List van violations
        """
        # STUB - Fase 2
        return []

    def _check_50u_week_single(self, datum: str) -> List[Violation]:
        """
        Light 50u week check voor single datum (real-time)

        Checks week waar datum in valt

        Args:
            datum: Datum "YYYY-MM-DD"

        Returns:
            List van violations
        """
        # STUB - Fase 2
        return []
