"""
PlanningValidator Service - Wrapper Layer voor HR Validatie

Dit service is een wrapper rond ConstraintChecker (pure business logic).
Het handelt:
- Database queries (planning, shift_codes, hr_regels)
- Data conversie (DB rows → PlanningRegel objects)
- Caching (planning data, violations)
- UI formattering (violations → user messages)

Versie: v0.6.26 (Fase 2 - Database Integration)
Datum: 3 November 2025
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import date, datetime, timedelta
from database.connection import get_connection

# Import pure business logic layer
from services.constraint_checker import (
    ConstraintChecker,
    PlanningRegel,
    Violation,
    ConstraintCheckResult,
    ViolationType,
    ViolationSeverity
)

# Import existing services
from services.hr_regels_service import HRRegelsService
from services.term_code_service import TermCodeService


# ============================================================================
# PLANNING VALIDATOR WRAPPER
# ============================================================================

class PlanningValidator:
    """
    Wrapper rond ConstraintChecker voor database integratie

    Usage:
        validator = PlanningValidator(gebruiker_id=123, jaar=2025, maand=11)

        # Batch validatie (alle checks)
        violations = validator.validate_all()

        # Real-time validatie (light checks only)
        violations = validator.validate_shift(datum=date(2025, 11, 15), shift_code="7101")

        # Violation level voor UI overlay
        level = validator.get_violation_level(datum=date(2025, 11, 15))

    Design Pattern: Wrapper + Dependency Injection
    - ConstraintChecker bevat pure business logic (geen DB)
    - PlanningValidator handelt DB queries + caching
    - Data conversie: DB rows → PlanningRegel → ConstraintChecker
    """

    def __init__(self, gebruiker_id: int, jaar: int, maand: int):
        """
        Initialize validator voor gebruiker + maand

        Args:
            gebruiker_id: ID van gebruiker om te valideren
            jaar: Jaar (YYYY)
            maand: Maand (1-12)
        """
        self.gebruiker_id = gebruiker_id
        self.jaar = jaar
        self.maand = maand

        # Services
        self.hr_service = HRRegelsService()
        self.term_service = TermCodeService()

        # Caches
        self._hr_config_cache: Optional[Dict[str, Any]] = None
        self._shift_tijden_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._planning_cache: Optional[List[PlanningRegel]] = None
        self._violations_cache: Optional[Dict[str, List[Violation]]] = None
        self._rode_lijnen_cache: Optional[List[Dict]] = None

        # ConstraintChecker instance (lazy init)
        self._checker: Optional[ConstraintChecker] = None

    def _get_checker(self) -> ConstraintChecker:
        """
        Lazy init ConstraintChecker instance

        Returns:
            Configured ConstraintChecker
        """
        if self._checker is None:
            hr_config = self._get_hr_config()
            shift_tijden = self._get_shift_tijden()
            self._checker = ConstraintChecker(hr_config, shift_tijden)

        return self._checker

    # ========================================================================
    # DATABASE QUERIES - Haal configuratie en planning data op
    # ========================================================================
    # Deze sectie bevat alle database query methods:
    # - _get_hr_config - Laad HR regels configuratie
    # - _get_shift_tijden - Laad shift codes met tijden en flags
    # - _get_gebruiker_werkposten_map - Laad werkpost koppelingen
    # - _get_shift_code_werkpost_map - Laad shift→werkpost mapping
    # - _get_planning_data - Laad planning regels voor gebruiker
    # - _get_rode_lijnen - Laad 28-dagen HR cycli
    # ========================================================================

    def _get_hr_config(self) -> Dict[str, Any]:
        """
        Laad HR configuratie uit database

        Returns:
            Dict met HR regel waarden:
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
        """
        if self._hr_config_cache is not None:
            return self._hr_config_cache

        # Direct database query (HRRegelsService heeft geen get_all_regels)
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT naam, waarde, eenheid, beschrijving
            FROM hr_regels
            WHERE is_actief = 1
        """)

        # Map naar config dict
        config = {}
        for row in cursor.fetchall():
            naam = row['naam']
            waarde = row['waarde']
            eenheid = row['eenheid']
            beschrijving = row['beschrijving']

            # Convert naar juiste type
            if eenheid == 'uur':
                config[naam] = float(waarde)
            elif eenheid == 'dagen':
                config[naam] = int(waarde)
            elif eenheid == 'periode':
                config[naam] = waarde  # String (bijv. 'ma-00:00|zo-23:59')
            elif eenheid == 'terms':
                # Voor term-based regels: sla beschrijving op als waarde
                config[naam] = beschrijving  # String (bijv. 'verlof,ziek')
            else:
                config[naam] = waarde

        # Defaults (fallback als niet geconfigureerd)
        config.setdefault('min_rust_uren', 12.0)
        config.setdefault('max_uren_week', 50.0)
        config.setdefault('max_werkdagen_cyclus', 19)
        config.setdefault('max_dagen_tussen_rx', 7)
        config.setdefault('max_werkdagen_reeks', 7)
        config.setdefault('max_weekends_achter_elkaar', 6)
        config.setdefault('week_definitie', 'ma-00:00|zo-23:59')
        config.setdefault('weekend_definitie', 'vr-22:00|ma-06:00')

        self._hr_config_cache = config
        return config

    def _get_shift_tijden(self) -> Dict[str, Dict[str, Any]]:
        """
        Laad shift tijden + flags uit database

        Returns:
            Dict met shift code → info mapping:
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
        if self._shift_tijden_cache is not None:
            return self._shift_tijden_cache

        conn = get_connection()
        cursor = conn.cursor()

        shift_tijden = {}

        # 1. Werkposten shift codes (shift_codes table)
        cursor.execute("""
            SELECT
                sc.code,
                sc.start_uur,
                sc.eind_uur,
                sc.shift_type,
                w.naam as werkpost_naam,
                w.telt_als_werkdag,
                w.reset_12u_rust
            FROM shift_codes sc
            JOIN werkposten w ON sc.werkpost_id = w.id
            WHERE w.is_actief = 1
        """)

        for row in cursor.fetchall():
            shift_tijden[row['code']] = {
                'start_uur': row['start_uur'],
                'eind_uur': row['eind_uur'],
                'shift_type': row['shift_type'],
                'werkpost_naam': row['werkpost_naam'],  # v0.6.28 voor error messages
                'telt_als_werkdag': bool(row['telt_als_werkdag']),
                'reset_12u_rust': bool(row['reset_12u_rust']),
                'breekt_werk_reeks': bool(row['reset_12u_rust']),  # Same flag
                'term': None  # Werkpost shifts hebben geen term
            }

        # 2. Speciale codes (speciale_codes table)
        cursor.execute("""
            SELECT
                code,
                term,
                telt_als_werkdag,
                reset_12u_rust,
                breekt_werk_reeks
            FROM speciale_codes
        """)

        for row in cursor.fetchall():
            shift_tijden[row['code']] = {
                'start_uur': None,  # Speciale codes hebben geen tijden
                'eind_uur': None,
                'shift_type': None,  # Speciale codes hebben geen shift_type
                'term': row['term'],  # IMPORTANT: term voor RX/CX detectie
                'telt_als_werkdag': bool(row['telt_als_werkdag']),
                'reset_12u_rust': bool(row['reset_12u_rust']),
                'breekt_werk_reeks': bool(row['breekt_werk_reeks'])
            }

        self._shift_tijden_cache = shift_tijden
        conn.close()
        return shift_tijden

    def _get_gebruiker_werkposten_map(self) -> Dict[int, List[int]]:
        """
        Laad gebruiker → werkposten mapping uit database (v0.6.28)

        Returns:
            Dict met gebruiker_id → list van werkpost_ids:
            {
                123: [1, 2],   # Jan kent PAT en Interventie
                456: [1],      # Piet kent alleen PAT
                ...
            }
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT gebruiker_id, werkpost_id
            FROM gebruiker_werkposten
            ORDER BY gebruiker_id, prioriteit
        """)

        mapping = {}
        for row in cursor.fetchall():
            gebruiker_id = row['gebruiker_id']
            werkpost_id = row['werkpost_id']

            if gebruiker_id not in mapping:
                mapping[gebruiker_id] = []

            mapping[gebruiker_id].append(werkpost_id)

        conn.close()
        return mapping

    def _get_shift_code_werkpost_map(self) -> Dict[str, int]:
        """
        Laad shift_code → werkpost_id mapping uit database (v0.6.28)

        Returns:
            Dict met shift_code → werkpost_id:
            {
                '7101': 1,  # PAT vroeg
                '7201': 1,  # PAT laat
                '7301': 2,  # Interventie vroeg
                ...
            }

        Note: Speciale codes (VV, KD, RX, CX) zitten NIET in deze mapping
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT code, werkpost_id
            FROM shift_codes sc
            JOIN werkposten w ON sc.werkpost_id = w.id
            WHERE w.is_actief = 1
        """)

        mapping = {}
        for row in cursor.fetchall():
            mapping[row['code']] = row['werkpost_id']

        conn.close()
        return mapping

    def _get_planning_data(self) -> List[PlanningRegel]:
        """
        Laad planning data en converteer naar PlanningRegel objects

        CRITICAL (v0.6.26 - BUG-003c): Laadt buffer van +/- 1 maand voor cross-month RX gap detection

        Returns:
            List van PlanningRegel objects voor gebruiker + maand (+ buffer)
        """
        if self._planning_cache is not None:
            return self._planning_cache

        conn = get_connection()
        cursor = conn.cursor()

        planning_regels = []

        # Bereken datum range: vorige maand t/m volgende maand (v0.6.26 - BUG-003c fix)
        # Dit zorgt dat RX gaps over maandgrenzen correct gedetecteerd worden
        from datetime import date as date_cls
        from calendar import monthrange

        # Start datum: eerste dag van vorige maand
        if self.maand == 1:
            start_jaar = self.jaar - 1
            start_maand = 12
        else:
            start_jaar = self.jaar
            start_maand = self.maand - 1
        start_datum = date_cls(start_jaar, start_maand, 1)

        # Eind datum: laatste dag van volgende maand
        if self.maand == 12:
            eind_jaar = self.jaar + 1
            eind_maand = 1
        else:
            eind_jaar = self.jaar
            eind_maand = self.maand + 1
        _, laatste_dag = monthrange(eind_jaar, eind_maand)
        eind_datum = date_cls(eind_jaar, eind_maand, laatste_dag)

        # Haal planning voor gebruiker + datum range (met buffer)
        cursor.execute("""
            SELECT
                p.datum,
                p.shift_code,
                p.gebruiker_id
            FROM planning p
            WHERE p.gebruiker_id = ?
              AND p.datum >= ?
              AND p.datum <= ?
            ORDER BY p.datum
        """, (self.gebruiker_id, start_datum.isoformat(), eind_datum.isoformat()))
        planning_rows = cursor.fetchall()  # BEWAAR resultaten voordat andere queries

        # Haal feestdagen (met buffer voor cross-month detection)
        cursor.execute("""
            SELECT datum
            FROM feestdagen
            WHERE datum >= ?
              AND datum <= ?
        """, (start_datum.isoformat(), eind_datum.isoformat()))
        feestdagen = {row['datum'] for row in cursor.fetchall()}

        # Haal goedgekeurde verlof aanvragen (met buffer)
        cursor.execute("""
            SELECT
                p.datum
            FROM planning p
            JOIN speciale_codes sc ON p.shift_code = sc.code
            WHERE p.gebruiker_id = ?
              AND sc.term = 'verlof'
              AND p.datum >= ?
              AND p.datum <= ?
        """, (self.gebruiker_id, start_datum.isoformat(), eind_datum.isoformat()))
        goedgekeurd_verlof = {row['datum'] for row in cursor.fetchall()}

        # Convert planning rows naar PlanningRegel objects
        for row in planning_rows:
            datum_str = row['datum']
            datum_obj = datetime.strptime(datum_str, "%Y-%m-%d").date()

            planning_regels.append(PlanningRegel(
                gebruiker_id=row['gebruiker_id'],
                datum=datum_obj,
                shift_code=row['shift_code'],
                is_goedgekeurd_verlof=(datum_str in goedgekeurd_verlof),
                is_feestdag=(datum_str in feestdagen)
            ))

        self._planning_cache = planning_regels
        return planning_regels

    def _get_rode_lijnen(self) -> List[Dict]:
        """
        Laad rode lijn periodes voor cyclus check

        Returns:
            List van rode lijn periode dicts:
            [{
                'start_datum': date(2025, 1, 6),
                'eind_datum': date(2025, 2, 2),
                'periode_nummer': 1
            }, ...]
        """
        if self._rode_lijnen_cache is not None:
            return self._rode_lijnen_cache

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                periode_nummer,
                start_datum
            FROM rode_lijnen
            WHERE strftime('%Y', start_datum) = ?
            ORDER BY start_datum
        """, (str(self.jaar),))

        periodes = []
        for row in cursor.fetchall():
            start = datetime.strptime(row['start_datum'], "%Y-%m-%d").date()
            eind = start + timedelta(days=27)  # 28-dagen periode

            periodes.append({
                'start_datum': start,
                'eind_datum': eind,
                'periode_nummer': row['periode_nummer']
            })

        self._rode_lijnen_cache = periodes
        return periodes

    # ========================================================================
    # VALIDATION METHODS - Public API voor HR validaties
    # ========================================================================
    # Deze sectie bevat de public methods voor validatie:
    # - validate_all - Batch validatie (alle 7 HR checks + werkpost check)
    # - validate_shift - Real-time validatie (snelle checks: 12u rust, 50u week, werkpost)
    # - get_violation_level - Bepaal UI overlay kleur (none/warning/error)
    # - get_violations_voor_datum - Haal violations voor specifieke datum
    # ========================================================================

    def validate_all(self) -> Dict[str, List[Violation]]:
        """
        Run alle HR validaties + data consistency checks (batch mode)

        Returns:
            Dict met violations per regel:
            {
                'min_rust_12u': [Violation(...), ...],
                'max_uren_week': [...],
                ...
                'werkpost_koppeling': [...],  # v0.6.28
            }
        """
        # Haal data
        planning = self._get_planning_data()
        rode_lijnen = self._get_rode_lijnen()

        # Get werkpost mappings (v0.6.28)
        gebruiker_werkposten_map = self._get_gebruiker_werkposten_map()
        shift_code_werkpost_map = self._get_shift_code_werkpost_map()

        # Get checker
        checker = self._get_checker()

        # Run alle checks (inclusief werkpost check)
        results = checker.check_all(
            planning,
            self.gebruiker_id,
            rode_lijnen,
            gebruiker_werkposten_map,
            shift_code_werkpost_map
        )

        # Convert ConstraintCheckResult → violations dict
        violations_dict = {}
        for regel_naam, result in results.items():
            violations_dict[regel_naam] = result.violations

        # Cache result
        self._violations_cache = violations_dict

        return violations_dict

    def validate_shift(self, datum: date, shift_code: str) -> List[Violation]:
        """
        Light validatie voor real-time feedback (cel edit)

        Checks alleen:
        - 12u rust (vorige/volgende dag)
        - 50u week (huidige week)

        Args:
            datum: Datum van shift
            shift_code: Code van shift

        Returns:
            Flat list van violations
        """
        # Haal planning data (incl. buffer voor omliggende dagen)
        planning = self._get_planning_data()

        # CRITICAL FIX (v0.6.26 - BUG-004): Verwijder bestaande shift voor deze datum
        # Anders krijgen we dubbele shifts (56u ipv 48u voor week)
        planning = [p for p in planning if p.datum != datum]

        # Add de nieuwe shift tijdelijk (voor preview)
        planning.append(PlanningRegel(
            gebruiker_id=self.gebruiker_id,
            datum=datum,
            shift_code=shift_code,
            is_goedgekeurd_verlof=False,
            is_feestdag=False
        ))

        # Sort op datum
        planning = sorted(planning, key=lambda p: p.datum)

        # Get checker
        checker = self._get_checker()

        # Get werkpost mappings (v0.6.28)
        gebruiker_werkposten_map = self._get_gebruiker_werkposten_map()
        shift_code_werkpost_map = self._get_shift_code_werkpost_map()

        # Run alleen snelle checks (+ werkpost check)
        violations = []
        violations.extend(checker.check_12u_rust(planning, self.gebruiker_id).violations)
        violations.extend(checker.check_max_uren_week(planning, self.gebruiker_id).violations)
        violations.extend(checker.check_werkpost_koppeling(
            planning,
            self.gebruiker_id,
            gebruiker_werkposten_map,
            shift_code_werkpost_map
        ).violations)

        return violations

    def get_violation_level(self, datum: date) -> str:
        """
        Voor UI overlay kleur bepaling

        Args:
            datum: Datum om te checken

        Returns:
            'none', 'warning', 'error'
        """
        if self._violations_cache is None:
            self.validate_all()

        # Check cached violations voor deze datum
        for violations_list in self._violations_cache.values():
            for v in violations_list:
                # Check of violation matched deze datum
                if v.datum == datum:
                    return 'error' if v.severity == ViolationSeverity.ERROR else 'warning'

                # Check datum_range
                if v.datum_range:
                    start, eind = v.datum_range
                    if start <= datum <= eind:
                        return 'error' if v.severity == ViolationSeverity.ERROR else 'warning'

        return 'none'

    def get_violations_voor_datum(self, datum: date) -> List[Violation]:
        """
        Haal violations voor specifieke datum (voor tooltip)

        Args:
            datum: Datum om te checken

        Returns:
            List van Violation objects
        """
        if self._violations_cache is None:
            self.validate_all()

        violations = []

        for violations_list in self._violations_cache.values():
            for v in violations_list:
                # Check exacte datum match
                if v.datum == datum:
                    violations.append(v)

                # Check datum_range
                elif v.datum_range:
                    start, eind = v.datum_range
                    if start <= datum <= eind:
                        violations.append(v)

        return violations

    # ========================================================================
    # CACHE MANAGEMENT
    # ========================================================================

    def invalidate_cache(self):
        """Clear alle caches (na planning wijziging)"""
        self._planning_cache = None
        self._violations_cache = None
        self._checker = None  # Force re-init bij volgende gebruik

    def invalidate_datum_cache(self, datum: date):
        """
        Light invalidatie: alleen violations cache clearen

        Args:
            datum: Datum die gewijzigd is (voor logging/debugging)
        """
        self._violations_cache = None
