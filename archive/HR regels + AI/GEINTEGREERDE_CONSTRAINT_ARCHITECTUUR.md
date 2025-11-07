# Geïntegreerde Constraint Architectuur
## HR Validatie + AI Planning Generator (Optie 2)

**Versie:** 1.0  
**Datum:** 31 Oktober 2025  
**Status:** Design Document - Ready for Implementation  
**Target Release:** v0.6.25 (HR Validatie) + v0.7.0 (AI Generator Optie 2)

---

## 1. Executive Summary

Dit document beschrijft een **geïntegreerde architectuur** die de HR Validatie (v0.6.25) en AI Planning Generator Optie 2 (v0.7.0) combineert door een gedeelde constraint checking laag. Door nu slim te ontwerpen, besparen we ~20 uur bij de latere implementatie van de AI generator.

**Kernprincipe:** Bouw de constraint logica **één keer**, gebruik het **twee keer**.

### Voordelen

✅ **Code hergebruik:** Constraint checks 1× implementeren, 2× gebruiken  
✅ **Consistentie:** HR-validatie en AI generator gebruiken dezelfde business rules  
✅ **Onderhoudbaarheid:** Bug fix of regelwijziging op één plek  
✅ **Toekomstbestendig:** Gemakkelijk uitbreiden met nieuwe constraints  
✅ **Testbaarheid:** Constraints geïsoleerd testen zonder UI dependencies

### Tijdsinvestering

| Fase | Origineel Plan | Met Integratie | Verschil |
|------|---------------|----------------|----------|
| HR Validatie v0.6.25 | 34-46 uur | 38-50 uur | +4 uur (betere architectuur) |
| AI Generator Optie 2 v0.7.0 | 24-40 uur | 20-30 uur | -10 uur (hergebruik) |
| **Totaal** | **58-86 uur** | **58-80 uur** | **-6 uur netto** |

**Plus:** Betere codekwaliteit en onderhoudbaarheid voor de toekomst.

---

## 2. Architectuur Overzicht

### 2.1 Drie-Laags Model

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  ┌──────────────────────┐  ┌────────────────────────────┐  │
│  │  PlanningValidator   │  │  PlanningOptimizer         │  │
│  │  (HR Validatie UI)   │  │  (AI Generator Optie 2)    │  │
│  │                      │  │                            │  │
│  │  v0.6.25             │  │  v0.7.0 (TOEKOMST)        │  │
│  └──────────┬───────────┘  └──────────┬─────────────────┘  │
└─────────────┼────────────────────────┼─────────────────────┘
              │                        │
              └────────────┬───────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           ConstraintChecker (SHARED CORE)            │  │
│  │                                                      │  │
│  │  • check_12u_rust()                                 │  │
│  │  • check_max_uren_week()                           │  │
│  │  • check_max_werkdagen_cyclus()                    │  │
│  │  • check_max_dagen_tussen_rx()                     │  │
│  │  • check_max_werkdagen_reeks()                     │  │
│  │  • check_max_weekends()                            │  │
│  │                                                      │  │
│  │  Pure business logic - geen UI, geen DB calls       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAYER                               │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Database       │  │ HRRegels     │  │ ShiftCodes     │  │
│  │ - planning     │  │ Service      │  │ Service        │  │
│  │ - hr_regels    │  │              │  │                │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow - Twee Gebruiksscenario's

**Scenario A: HR Validatie (v0.6.25)**
```
UI Edit Cel → PlanningValidator.validate_shift()
            → ConstraintChecker.check_12u_rust()
            → ConstraintChecker.check_max_uren_week()
            → Return violations
            → Update UI (rode overlay + tooltip)
```

**Scenario B: AI Generator (v0.7.0 - Toekomst)**
```
User: "Genereer planning" → PlanningOptimizer.optimize_planning()
                          → ConstraintChecker.check_all() (voor ALL users)
                          → Build OR-Tools constraint model
                          → Solve CSP
                          → Return optimized planning
```

---

## 3. Data Model - Uitgebreid

### 3.1 PlanningRegel (Input Data Class)

```python
from dataclasses import dataclass
from typing import Optional
from datetime import date

@dataclass
class PlanningRegel:
    """
    Generieke planning regel - gebruikt door BEIDE systemen
    Niet gebonden aan database schema
    """
    gebruiker_id: int
    datum: date  # Python date object (niet string)
    shift_code: Optional[str]  # None voor lege cel
    
    # Metadata (optioneel)
    is_goedgekeurd_verlof: bool = False
    is_feestdag: bool = False
    gegenereerd_door: Optional[str] = None  # 'manual', 'typetabel', 'ai_optimizer'
    
    def __hash__(self):
        """Hashable voor set operations"""
        return hash((self.gebruiker_id, self.datum))
    
    def is_werkdag(self) -> bool:
        """Check of dit een werkdag shift is (niet RX/CX/verlof/leeg)"""
        if not self.shift_code:
            return False
        if self.shift_code in ['RX', 'CX', 'V', 'VK', 'ZV']:
            return False
        return True
```

### 3.2 Violation (Output Data Class)

```python
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

class ViolationSeverity(Enum):
    """Violation ernst classificatie"""
    ERROR = "error"      # Harde regel violation
    WARNING = "warning"  # Zachte regel violation
    INFO = "info"       # Informatief (geen violation)

class ViolationType(Enum):
    """Type constraint violation"""
    MIN_RUST_12U = "min_rust_12u"
    MAX_UREN_WEEK = "max_uren_week"
    MAX_WERKDAGEN_CYCLUS = "max_werkdagen_cyclus"
    MAX_DAGEN_TUSSEN_RX = "max_dagen_tussen_rx"
    MAX_WERKDAGEN_REEKS = "max_werkdagen_reeks"
    MAX_WEEKENDS = "max_weekends"

@dataclass
class Violation:
    """
    Uitgebreide violation class - voor beide systemen
    """
    # Basis identificatie
    type: ViolationType
    severity: ViolationSeverity
    gebruiker_id: int
    
    # Datum info
    datum: Optional[date] = None  # Single date violation
    datum_range: Optional[Tuple[date, date]] = None  # Range violation (week/cyclus)
    
    # User-facing info (voor UI)
    beschrijving: str = ""  # NL tekst: "Te weinig rust: 10.5u tussen shifts"
    
    # Technical details (voor debugging/logging)
    details: Dict[str, Any] = None
    
    # NIEUW: Voor AI Optimizer
    affected_shifts: List[Tuple[int, date]] = None  # Welke shifts betrokken
    suggested_fixes: List[str] = None  # Mogelijke oplossingen
    
    # Confidence score (voor ML toekomst)
    confidence: float = 1.0  # 0.0-1.0
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.affected_shifts is None:
            self.affected_shifts = []
        if self.suggested_fixes is None:
            self.suggested_fixes = []
    
    def to_dict(self) -> dict:
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
            'confidence': self.confidence
        }
    
    def to_user_message(self) -> str:
        """User-friendly bericht voor dialogs (UI)"""
        msg = f"[{self.severity.value.upper()}] {self.beschrijving}"
        if self.datum:
            msg = f"{self.datum.strftime('%d-%m-%Y')}: {msg}"
        elif self.datum_range:
            start, eind = self.datum_range
            msg = f"{start.strftime('%d-%m')}-{eind.strftime('%d-%m')}: {msg}"
        return msg
    
    def to_optimizer_constraint(self) -> str:
        """
        Converteer naar constraint string voor OR-Tools
        Gebruikt in PlanningOptimizer (v0.7.0)
        """
        # Voorbeeld implementatie - wordt uitgewerkt in v0.7.0
        return f"constraint_{self.type.value}_{self.gebruiker_id}"
```

### 3.3 ConstraintCheckResult

```python
@dataclass
class ConstraintCheckResult:
    """
    Resultaat van constraint check - voor beide systemen
    """
    regel_naam: str
    violations: List[Violation]
    check_duration_ms: float  # Performance monitoring
    
    @property
    def is_valid(self) -> bool:
        """Check of er geen ERROR violations zijn"""
        return not any(v.severity == ViolationSeverity.ERROR for v in self.violations)
    
    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == ViolationSeverity.ERROR)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == ViolationSeverity.WARNING)
    
    def summary(self) -> str:
        """Voor logging"""
        return f"{self.regel_naam}: {self.error_count} errors, {self.warning_count} warnings"
```

---

## 4. ConstraintChecker - Core Implementation

### 4.1 Class Structuur

```python
# services/constraint_checker.py
from typing import List, Dict, Tuple, Optional
from datetime import date, datetime, timedelta
from collections import defaultdict
import time

class ConstraintChecker:
    """
    SHARED CORE - Constraint checking business logic
    
    Gebruikt door:
    - PlanningValidator (v0.6.25) - per gebruiker validatie
    - PlanningOptimizer (v0.7.0) - batch validatie alle gebruikers
    
    Design principes:
    1. Stateless - geen instance state tussen checks
    2. Pure functions - geen side effects
    3. Database agnostic - werkt met PlanningRegel objects
    4. Geen UI dependencies
    5. Goed gedocumenteerd met voorbeelden
    """
    
    def __init__(self, hr_config: Dict[str, Any], shift_tijden: Dict[str, Tuple[str, str]]):
        """
        Args:
            hr_config: HR regel configuratie uit database
                {
                    'min_rust_uren': 12.0,
                    'max_uren_week': 50.0,
                    'max_werkdagen_cyclus': 19,
                    'week_start_dag': 'ma',
                    'week_definitie': 'ma-00:00|zo-23:59',
                    'cyclus_dagen': 28,
                    'max_dagen_tussen_rx': 7,
                    'max_werkdagen_reeks': 7,
                    'max_weekends_achter_elkaar': 3
                }
            shift_tijden: Shift code → (start_uur, eind_uur) mapping
                {
                    'E': ('06:00', '14:00'),
                    'L': ('14:00', '22:00'),
                    'N': ('22:00', '06:00')
                }
        """
        self.hr_config = hr_config
        self.shift_tijden = shift_tijden
        
        # Parse week definitie bij initialisatie
        self.week_start_dag, self.week_start_uur, \
        self.week_eind_dag, self.week_eind_uur = \
            self._parse_periode_definitie(hr_config['week_definitie'])
    
    # ========== PUBLIC API - Constraint Checks ==========
    
    def check_12u_rust(
        self, 
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> ConstraintCheckResult:
        """
        Check minimale 12 uur rust tussen shifts
        
        Args:
            planning: Lijst van planning regels (gesorteerd op datum)
            gebruiker_id: Optioneel - filter op specifieke gebruiker
        
        Returns:
            ConstraintCheckResult met violations
        
        Business Rules:
        - 12u rust vanaf einde shift N tot start shift N+1
        - Reset bij RX/CX code (telt niet als shift)
        - Midnight crossing shifts worden correct afgehandeld
        - Check alleen opeenvolgende werkdagen
        
        Example:
            planning = [
                PlanningRegel(gebruiker_id=1, datum=date(2025,11,1), shift_code='E'),  # 06:00-14:00
                PlanningRegel(gebruiker_id=1, datum=date(2025,11,2), shift_code='N'),  # 22:00-06:00
            ]
            result = checker.check_12u_rust(planning, gebruiker_id=1)
            # Result: violations omdat 14:00 → 22:00 = 8u rust (< 12u)
        """
        start_time = time.time()
        violations = []
        
        # Filter en sorteer planning
        if gebruiker_id:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]
        planning = sorted(planning, key=lambda p: (p.gebruiker_id, p.datum))
        
        # Groepeer per gebruiker
        per_gebruiker = defaultdict(list)
        for regel in planning:
            if regel.shift_code:  # Skip lege cellen
                per_gebruiker[regel.gebruiker_id].append(regel)
        
        # Check per gebruiker
        for uid, regels in per_gebruiker.items():
            for i in range(len(regels) - 1):
                huidige = regels[i]
                volgende = regels[i + 1]
                
                # Skip als huidige of volgende = rustdag
                if self._is_rustdag(huidige.shift_code) or self._is_rustdag(volgende.shift_code):
                    continue
                
                # Bereken rust
                rust_uren = self._bereken_rust_tussen_shifts(
                    huidige.datum, huidige.shift_code,
                    volgende.datum, volgende.shift_code
                )
                
                # Check violation
                min_rust = self.hr_config['min_rust_uren']
                if rust_uren < min_rust:
                    violations.append(Violation(
                        type=ViolationType.MIN_RUST_12U,
                        severity=ViolationSeverity.ERROR,
                        gebruiker_id=uid,
                        datum=volgende.datum,  # Violation op de tweede shift
                        beschrijving=f"Te weinig rust: {rust_uren:.1f}u tussen shifts (minimum {min_rust}u)",
                        details={
                            'rust_uren': rust_uren,
                            'vorige_datum': huidige.datum.isoformat(),
                            'vorige_shift': huidige.shift_code,
                            'huidige_shift': volgende.shift_code,
                            'min_rust': min_rust
                        },
                        affected_shifts=[
                            (uid, huidige.datum),
                            (uid, volgende.datum)
                        ],
                        suggested_fixes=[
                            f"Verplaats {volgende.shift_code} shift naar later in de week",
                            f"Verander {huidige.shift_code} naar eerdere shift type",
                            f"Voeg rustdag in tussen {huidige.datum} en {volgende.datum}"
                        ]
                    ))
        
        duration_ms = (time.time() - start_time) * 1000
        return ConstraintCheckResult(
            regel_naam="12u rust",
            violations=violations,
            check_duration_ms=duration_ms
        )
    
    def check_max_uren_week(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> ConstraintCheckResult:
        """
        Check maximaal 50 uur per week
        
        Args:
            planning: Lijst van planning regels
            gebruiker_id: Optioneel - filter op specifieke gebruiker
        
        Returns:
            ConstraintCheckResult met violations
        
        Business Rules:
        - Week loopt van maandag 00:00 tot zondag 23:59 (configureerbaar)
        - Alleen werkshifts tellen (niet RX/CX/verlof)
        - Shifts die over week grens lopen worden proportioneel verdeeld
        - Maximaal 50u per week (configureerbaar)
        
        Example:
            # 6 shifts van 8u = 48u (OK)
            # 7 shifts van 8u = 56u (VIOLATION)
        """
        start_time = time.time()
        violations = []
        max_uren = self.hr_config['max_uren_week']
        
        # Filter planning
        if gebruiker_id:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]
        
        # Groepeer per gebruiker en week
        per_gebruiker_week = defaultdict(lambda: defaultdict(float))
        
        for regel in planning:
            if not regel.is_werkdag():
                continue
            
            # Bepaal week nummer(s) die shift overlapt
            shift_start, shift_eind = self.shift_tijden.get(regel.shift_code, ('00:00', '00:00'))
            shift_duur = self._bereken_shift_duur(shift_start, shift_eind)
            
            # Bereken welke week(en) deze shift in valt
            week_nr = self._get_week_nummer(regel.datum)
            per_gebruiker_week[regel.gebruiker_id][week_nr] += shift_duur
        
        # Check violations per week
        for uid, weken in per_gebruiker_week.items():
            for week_nr, totaal_uren in weken.items():
                if totaal_uren > max_uren:
                    # Vind datums in deze week
                    week_start = self._get_week_start_date(week_nr)
                    week_eind = week_start + timedelta(days=6)
                    
                    violations.append(Violation(
                        type=ViolationType.MAX_UREN_WEEK,
                        severity=ViolationSeverity.ERROR,
                        gebruiker_id=uid,
                        datum_range=(week_start, week_eind),
                        beschrijving=f"Te veel uren: {totaal_uren:.1f}u in week {week_nr} (maximum {max_uren}u)",
                        details={
                            'totaal_uren': totaal_uren,
                            'max_uren': max_uren,
                            'week_nummer': week_nr,
                            'overschrijding': totaal_uren - max_uren
                        },
                        suggested_fixes=[
                            f"Verwijder {(totaal_uren - max_uren) / 8:.1f} diensten deze week",
                            "Verplaats shifts naar volgende week",
                            "Vervang lange shifts door kortere shifts"
                        ]
                    ))
        
        duration_ms = (time.time() - start_time) * 1000
        return ConstraintCheckResult(
            regel_naam="Max uren per week",
            violations=violations,
            check_duration_ms=duration_ms
        )
    
    def check_max_werkdagen_cyclus(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> ConstraintCheckResult:
        """
        Check maximaal 19 werkdagen per 28-dagen cyclus (rode lijn periode)
        
        Args:
            planning: Lijst van planning regels
            gebruiker_id: Optioneel - filter op specifieke gebruiker
        
        Returns:
            ConstraintCheckResult met violations
        
        Business Rules:
        - Cyclus = 28 dagen (4 weken)
        - Alleen shifts met telt_als_werkdag=1
        - RX/CX/verlof tellen NIET als werkdag
        - Rolling window check (elke 28-dagen periode)
        """
        start_time = time.time()
        violations = []
        max_werkdagen = self.hr_config['max_werkdagen_cyclus']
        cyclus_dagen = self.hr_config['cyclus_dagen']
        
        # Filter planning
        if gebruiker_id:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]
        
        # Groepeer per gebruiker
        per_gebruiker = defaultdict(list)
        for regel in planning:
            if regel.is_werkdag():
                per_gebruiker[regel.gebruiker_id].append(regel)
        
        # Check per gebruiker met rolling window
        for uid, regels in per_gebruiker.items():
            regels = sorted(regels, key=lambda r: r.datum)
            
            if not regels:
                continue
            
            # Loop door alle mogelijke 28-dagen periodes
            start_datum = regels[0].datum
            eind_datum = regels[-1].datum
            
            current_date = start_datum
            while current_date <= eind_datum:
                periode_eind = current_date + timedelta(days=cyclus_dagen - 1)
                
                # Tel werkdagen in deze periode
                werkdagen_in_periode = [
                    r for r in regels
                    if current_date <= r.datum <= periode_eind
                ]
                
                aantal_werkdagen = len(werkdagen_in_periode)
                
                if aantal_werkdagen > max_werkdagen:
                    violations.append(Violation(
                        type=ViolationType.MAX_WERKDAGEN_CYCLUS,
                        severity=ViolationSeverity.ERROR,
                        gebruiker_id=uid,
                        datum_range=(current_date, periode_eind),
                        beschrijving=f"Te veel werkdagen: {aantal_werkdagen} in {cyclus_dagen}-dagen cyclus (maximum {max_werkdagen})",
                        details={
                            'aantal_werkdagen': aantal_werkdagen,
                            'max_werkdagen': max_werkdagen,
                            'cyclus_dagen': cyclus_dagen,
                            'overschrijding': aantal_werkdagen - max_werkdagen
                        },
                        affected_shifts=[(uid, r.datum) for r in werkdagen_in_periode],
                        suggested_fixes=[
                            f"Verwijder {aantal_werkdagen - max_werkdagen} werkdagen uit deze periode",
                            "Vervang werkdagen door RX/CX rustdagen",
                            "Verplaats shifts naar volgende cyclus"
                        ]
                    ))
                
                # Move window 1 week forward voor performance
                current_date += timedelta(days=7)
        
        duration_ms = (time.time() - start_time) * 1000
        return ConstraintCheckResult(
            regel_naam="Max werkdagen per cyclus",
            violations=violations,
            check_duration_ms=duration_ms
        )
    
    def check_max_dagen_tussen_rx(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> ConstraintCheckResult:
        """
        Check maximaal 7 dagen tussen rustdagen (RX/CX codes)
        
        Business Rules:
        - Maximaal 7 werkdagen tussen twee RX of CX codes
        - Eerste RX/CX reset de teller
        - Alleen werkdagen tellen (geen verlof/feestdagen)
        """
        start_time = time.time()
        violations = []
        max_dagen = self.hr_config['max_dagen_tussen_rx']
        
        # Filter planning
        if gebruiker_id:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]
        
        # Groepeer per gebruiker
        per_gebruiker = defaultdict(list)
        for regel in planning:
            if regel.shift_code:  # Niet lege cellen
                per_gebruiker[regel.gebruiker_id].append(regel)
        
        # Check per gebruiker
        for uid, regels in per_gebruiker.items():
            regels = sorted(regels, key=lambda r: r.datum)
            
            laatste_rx_datum = None
            werkdagen_sinds_rx = 0
            
            for regel in regels:
                if self._is_rustdag(regel.shift_code):
                    # Reset teller
                    laatste_rx_datum = regel.datum
                    werkdagen_sinds_rx = 0
                elif regel.is_werkdag():
                    werkdagen_sinds_rx += 1
                    
                    # Check violation
                    if werkdagen_sinds_rx > max_dagen:
                        violations.append(Violation(
                            type=ViolationType.MAX_DAGEN_TUSSEN_RX,
                            severity=ViolationSeverity.ERROR,
                            gebruiker_id=uid,
                            datum=regel.datum,
                            beschrijving=f"Te lang zonder rustdag: {werkdagen_sinds_rx} dagen (maximum {max_dagen})",
                            details={
                                'dagen_sinds_rx': werkdagen_sinds_rx,
                                'max_dagen': max_dagen,
                                'laatste_rx': laatste_rx_datum.isoformat() if laatste_rx_datum else None
                            },
                            suggested_fixes=[
                                f"Voeg RX of CX rustdag in voor {regel.datum}",
                                f"Vervang werkdag op {regel.datum} door rustdag"
                            ]
                        ))
        
        duration_ms = (time.time() - start_time) * 1000
        return ConstraintCheckResult(
            regel_naam="Max dagen tussen rustdagen",
            violations=violations,
            check_duration_ms=duration_ms
        )
    
    def check_max_werkdagen_reeks(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> ConstraintCheckResult:
        """
        Check maximaal 7 opeenvolgende werkdagen
        
        Business Rules:
        - Maximaal 7 werkdagen op rij zonder rustdag
        - Rustdag (RX/CX) breekt de reeks
        - Verlof breekt de reeks ook
        """
        start_time = time.time()
        violations = []
        max_reeks = self.hr_config['max_werkdagen_reeks']
        
        # Filter planning
        if gebruiker_id:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]
        
        # Groepeer per gebruiker
        per_gebruiker = defaultdict(list)
        for regel in planning:
            if regel.shift_code:
                per_gebruiker[regel.gebruiker_id].append(regel)
        
        # Check per gebruiker
        for uid, regels in per_gebruiker.items():
            regels = sorted(regels, key=lambda r: r.datum)
            
            huidige_reeks = 0
            reeks_start = None
            
            for regel in regels:
                if regel.is_werkdag():
                    if huidige_reeks == 0:
                        reeks_start = regel.datum
                    huidige_reeks += 1
                    
                    # Check violation
                    if huidige_reeks > max_reeks:
                        violations.append(Violation(
                            type=ViolationType.MAX_WERKDAGEN_REEKS,
                            severity=ViolationSeverity.ERROR,
                            gebruiker_id=uid,
                            datum=regel.datum,
                            beschrijving=f"Te lange werkdagen reeks: {huidige_reeks} dagen op rij (maximum {max_reeks})",
                            details={
                                'reeks_lengte': huidige_reeks,
                                'max_reeks': max_reeks,
                                'reeks_start': reeks_start.isoformat() if reeks_start else None
                            },
                            suggested_fixes=[
                                f"Voeg rustdag in na {max_reeks} werkdagen",
                                f"Breek reeks bij dag {max_reeks}"
                            ]
                        ))
                else:
                    # Rustdag of verlof - reset reeks
                    huidige_reeks = 0
                    reeks_start = None
        
        duration_ms = (time.time() - start_time) * 1000
        return ConstraintCheckResult(
            regel_naam="Max opeenvolgende werkdagen",
            violations=violations,
            check_duration_ms=duration_ms
        )
    
    def check_max_weekends_achter_elkaar(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> ConstraintCheckResult:
        """
        Check maximaal 3 weekends achter elkaar werken
        
        Business Rules:
        - Weekend = zaterdag + zondag
        - Alleen als BEIDE dagen gewerkt worden telt het als weekend
        - Maximaal 3 weekends op rij
        """
        start_time = time.time()
        violations = []
        max_weekends = self.hr_config.get('max_weekends_achter_elkaar', 3)
        
        # Filter planning
        if gebruiker_id:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]
        
        # Groepeer per gebruiker
        per_gebruiker = defaultdict(list)
        for regel in planning:
            if regel.is_werkdag():
                per_gebruiker[regel.gebruiker_id].append(regel)
        
        # Check per gebruiker
        for uid, regels in per_gebruiker.items():
            regels = sorted(regels, key=lambda r: r.datum)
            
            # Vind alle weekends
            weekends_gewerkt = []
            
            # Groepeer op week
            weken = defaultdict(list)
            for regel in regels:
                week_nr = regel.datum.isocalendar()[1]
                weken[week_nr].append(regel)
            
            for week_nr, week_regels in sorted(weken.items()):
                # Check of zaterdag EN zondag gewerkt
                datums = {r.datum.weekday() for r in week_regels}
                if 5 in datums and 6 in datums:  # 5=zaterdag, 6=zondag
                    weekend_datum = min(r.datum for r in week_regels if r.datum.weekday() == 5)
                    weekends_gewerkt.append(weekend_datum)
            
            # Check opeenvolgende weekends
            opeenvolgende = 1
            for i in range(1, len(weekends_gewerkt)):
                # Check of weekends opeenvolgend zijn (7 dagen verschil)
                verschil = (weekends_gewerkt[i] - weekends_gewerkt[i-1]).days
                if verschil == 7:
                    opeenvolgende += 1
                    
                    if opeenvolgende > max_weekends:
                        violations.append(Violation(
                            type=ViolationType.MAX_WEEKENDS,
                            severity=ViolationSeverity.WARNING,  # Vaak een warning, geen error
                            gebruiker_id=uid,
                            datum=weekends_gewerkt[i],
                            beschrijving=f"Te veel weekends op rij: {opeenvolgende} (maximum {max_weekends})",
                            details={
                                'weekends_op_rij': opeenvolgende,
                                'max_weekends': max_weekends
                            },
                            suggested_fixes=[
                                f"Geef weekend vrij na {max_weekends} weekends",
                                "Plan rustdag op zaterdag of zondag"
                            ]
                        ))
                else:
                    opeenvolgende = 1  # Reset
        
        duration_ms = (time.time() - start_time) * 1000
        return ConstraintCheckResult(
            regel_naam="Max opeenvolgende weekends",
            violations=violations,
            check_duration_ms=duration_ms
        )
    
    # ========== Convenience Methods ==========
    
    def check_all(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> Dict[str, ConstraintCheckResult]:
        """
        Run alle constraint checks in één keer
        
        Returns:
            {
                'min_rust_12u': ConstraintCheckResult(...),
                'max_uren_week': ConstraintCheckResult(...),
                ...
            }
        """
        results = {
            'min_rust_12u': self.check_12u_rust(planning, gebruiker_id),
            'max_uren_week': self.check_max_uren_week(planning, gebruiker_id),
            'max_werkdagen_cyclus': self.check_max_werkdagen_cyclus(planning, gebruiker_id),
            'max_dagen_tussen_rx': self.check_max_dagen_tussen_rx(planning, gebruiker_id),
            'max_werkdagen_reeks': self.check_max_werkdagen_reeks(planning, gebruiker_id),
            'max_weekends': self.check_max_weekends_achter_elkaar(planning, gebruiker_id)
        }
        return results
    
    def get_all_violations(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> List[Violation]:
        """
        Haal alle violations op in één flat list
        Handig voor rapportage en UI
        """
        results = self.check_all(planning, gebruiker_id)
        all_violations = []
        for result in results.values():
            all_violations.extend(result.violations)
        return all_violations
    
    # ========== PRIVATE Helper Methods ==========
    
    def _bereken_shift_duur(self, start_uur: str, eind_uur: str) -> float:
        """
        Bereken shift duur in uren (handelt middernacht crossing)
        
        Examples:
            "06:00" → "14:00" = 8.0 uur
            "22:00" → "06:00" = 8.0 uur (over middernacht)
            "14:15" → "22:45" = 8.5 uur
        """
        start = datetime.strptime(start_uur, "%H:%M")
        eind = datetime.strptime(eind_uur, "%H:%M")
        
        if eind < start:  # Middernacht crossing
            eind += timedelta(days=1)
        
        delta = eind - start
        return delta.total_seconds() / 3600
    
    def _bereken_rust_tussen_shifts(
        self,
        datum1: date, shift_code1: str,
        datum2: date, shift_code2: str
    ) -> float:
        """
        Bereken rust tussen twee shifts in uren
        
        Returns: Aantal uren rust (kan negatief zijn als overlap)
        """
        # Haal shift tijden op
        _, eind_uur1 = self.shift_tijden.get(shift_code1, ('00:00', '00:00'))
        start_uur2, _ = self.shift_tijden.get(shift_code2, ('00:00', '00:00'))
        
        # Bouw datetimes
        dt1 = datetime.combine(datum1, datetime.strptime(eind_uur1, "%H:%M").time())
        dt2 = datetime.combine(datum2, datetime.strptime(start_uur2, "%H:%M").time())
        
        # Handel middernacht crossing voor shift 1
        if eind_uur1 < self.shift_tijden.get(shift_code1, ('00:00', '00:00'))[0]:
            dt1 += timedelta(days=1)
        
        delta = dt2 - dt1
        return delta.total_seconds() / 3600
    
    def _parse_periode_definitie(self, waarde: str) -> Tuple[str, str, str, str]:
        """
        Parse 'ma-00:00|zo-23:59' → (start_dag, start_uur, eind_dag, eind_uur)
        
        Returns: ('ma', '00:00', 'zo', '23:59')
        """
        start, eind = waarde.split('|')
        start_dag, start_uur = start.split('-', 1)
        eind_dag, eind_uur = eind.split('-', 1)
        return (start_dag.strip(), start_uur.strip(),
                eind_dag.strip(), eind_uur.strip())
    
    def _is_rustdag(self, shift_code: str) -> bool:
        """Check of shift code een rustdag is"""
        return shift_code in ['RX', 'CX']
    
    def _get_week_nummer(self, datum: date) -> int:
        """Haal ISO week nummer op"""
        return datum.isocalendar()[1]
    
    def _get_week_start_date(self, week_nr: int, jaar: Optional[int] = None) -> date:
        """Bereken start datum van een week nummer"""
        if jaar is None:
            jaar = date.today().year
        # ISO week 1 start op eerste maandag met >3 dagen in januari
        jan_4 = date(jaar, 1, 4)
        week_1_start = jan_4 - timedelta(days=jan_4.weekday())
        return week_1_start + timedelta(weeks=week_nr - 1)
```

### 4.2 Usage Examples

```python
# ========== Example 1: HR Validatie (Single User) ==========

from services.constraint_checker import ConstraintChecker
from datetime import date

# Setup
hr_config = {
    'min_rust_uren': 12.0,
    'max_uren_week': 50.0,
    'max_werkdagen_cyclus': 19,
    'week_definitie': 'ma-00:00|zo-23:59',
    'cyclus_dagen': 28,
    'max_dagen_tussen_rx': 7,
    'max_werkdagen_reeks': 7,
    'max_weekends_achter_elkaar': 3
}

shift_tijden = {
    'E': ('06:00', '14:00'),
    'L': ('14:00', '22:00'),
    'N': ('22:00', '06:00'),
    'RX': ('00:00', '00:00'),
    'CX': ('00:00', '00:00')
}

checker = ConstraintChecker(hr_config, shift_tijden)

# Planning data (vanuit UI edit)
planning = [
    PlanningRegel(gebruiker_id=1, datum=date(2025, 11, 1), shift_code='E'),
    PlanningRegel(gebruiker_id=1, datum=date(2025, 11, 2), shift_code='E'),
    PlanningRegel(gebruiker_id=1, datum=date(2025, 11, 3), shift_code='L'),
    PlanningRegel(gebruiker_id=1, datum=date(2025, 11, 4), shift_code='N'),
    PlanningRegel(gebruiker_id=1, datum=date(2025, 11, 5), shift_code='E'),  # Te weinig rust!
]

# Check single constraint
result = checker.check_12u_rust(planning, gebruiker_id=1)
print(f"Check duurde: {result.check_duration_ms:.2f}ms")
print(f"Violations: {len(result.violations)}")
for v in result.violations:
    print(f"  - {v.to_user_message()}")

# Check alle constraints
all_results = checker.check_all(planning, gebruiker_id=1)
for naam, result in all_results.items():
    print(f"\n{result.summary()}")

# ========== Example 2: AI Optimizer (Batch - All Users) ==========

# Planning voor 3 gebruikers
planning_batch = [
    # Gebruiker 1
    PlanningRegel(gebruiker_id=1, datum=date(2025, 11, 1), shift_code='E'),
    PlanningRegel(gebruiker_id=1, datum=date(2025, 11, 2), shift_code='L'),
    # Gebruiker 2
    PlanningRegel(gebruiker_id=2, datum=date(2025, 11, 1), shift_code='L'),
    PlanningRegel(gebruiker_id=2, datum=date(2025, 11, 2), shift_code='N'),
    # Gebruiker 3
    PlanningRegel(gebruiker_id=3, datum=date(2025, 11, 1), shift_code='N'),
    PlanningRegel(gebruiker_id=3, datum=date(2025, 11, 2), shift_code='E'),
]

# Check voor ALLE gebruikers tegelijk (geen filter)
all_results = checker.check_all(planning_batch)

# Get flat list van violations voor optimizer
all_violations = checker.get_all_violations(planning_batch)
print(f"\nTotaal violations: {len(all_violations)}")
for v in all_violations:
    print(f"  Gebruiker {v.gebruiker_id}: {v.beschrijving}")
```

---

## 5. Presentation Layer - PlanningValidator (v0.6.25)

### 5.1 Implementation

```python
# services/planning_validator.py
from typing import Dict, List
from datetime import date
from services.constraint_checker import ConstraintChecker, PlanningRegel, Violation
from services.hr_regels_service import HRRegelsService
from database.connection import get_connection

class PlanningValidator:
    """
    UI-WRAPPER voor HR Validatie (v0.6.25)
    Gebruikt ConstraintChecker voor business logic
    
    Verantwoordelijk voor:
    - Database queries (planning ophalen)
    - Caching (performance)
    - UI-specifieke formattering
    - Real-time vs batch mode
    """
    
    def __init__(self, gebruiker_id: int, jaar: int, maand: int):
        self.gebruiker_id = gebruiker_id
        self.jaar = jaar
        self.maand = maand
        
        # Laad config
        self.hr_config = self._load_hr_config()
        self.shift_tijden = self._load_shift_tijden()
        
        # Initialiseer checker
        self.checker = ConstraintChecker(self.hr_config, self.shift_tijden)
        
        # Cache
        self._planning_cache: List[PlanningRegel] = None
        self._violations_cache: Dict[str, List[Violation]] = {}
    
    # ========== PUBLIC API - Voor UI ==========
    
    def validate_all(self) -> Dict[str, List[Violation]]:
        """
        Volledig validatie - voor publicatie rapport
        Gebruikt door: HRValidatieRapportDialog
        """
        planning = self._get_planning_data()
        results = self.checker.check_all(planning, self.gebruiker_id)
        
        # Convert results naar violations dict
        violations_dict = {}
        for naam, result in results.items():
            violations_dict[naam] = result.violations
        
        # Update cache
        self._violations_cache = violations_dict
        
        return violations_dict
    
    def validate_shift(self, datum: date, shift_code: str) -> List[Violation]:
        """
        Light validatie voor real-time feedback (cel edit)
        Gebruikt door: PlannerGridKalender.on_cel_edited()
        
        Checks alleen:
        - 12u rust (snel)
        - 50u week (snel)
        
        Niet: cyclus, weekends (te zwaar voor real-time)
        """
        planning = self._get_planning_data()
        
        # Add nieuwe shift to planning
        nieuwe_regel = PlanningRegel(
            gebruiker_id=self.gebruiker_id,
            datum=datum,
            shift_code=shift_code
        )
        planning.append(nieuwe_regel)
        
        # Check alleen snelle regels
        violations = []
        violations.extend(self.checker.check_12u_rust(planning, self.gebruiker_id).violations)
        violations.extend(self.checker.check_max_uren_week(planning, self.gebruiker_id).violations)
        
        return violations
    
    def get_violation_level(self, datum: date) -> str:
        """
        Voor UI overlay kleur bepaling
        Gebruikt door: PlannerGridKalender.get_hr_overlay_kleur()
        
        Returns: 'none', 'warning', 'error'
        """
        # Check cache eerst
        if datum.isoformat() in self._violations_cache:
            violations = self._violations_cache[datum.isoformat()]
            if not violations:
                return 'none'
            has_errors = any(v.severity.value == 'error' for v in violations)
            return 'error' if has_errors else 'warning'
        
        # Fallback: validate on-the-fly (voor real-time updates)
        planning = self._get_planning_data()
        violations = self.checker.get_all_violations(planning, self.gebruiker_id)
        
        # Filter op datum
        datum_violations = [v for v in violations if v.datum == datum]
        
        if not datum_violations:
            return 'none'
        has_errors = any(v.severity.value == 'error' for v in datum_violations)
        return 'error' if has_errors else 'warning'
    
    def get_violations_voor_datum(self, datum: date) -> List[Violation]:
        """
        Haal alle violations voor specifieke datum
        Gebruikt door: Tooltip generatie
        """
        planning = self._get_planning_data()
        all_violations = self.checker.get_all_violations(planning, self.gebruiker_id)
        return [v for v in all_violations if v.datum == datum or 
                (v.datum_range and v.datum_range[0] <= datum <= v.datum_range[1])]
    
    # ========== PRIVATE - Data Loading ==========
    
    def _load_hr_config(self) -> Dict:
        """Laad HR configuratie uit database"""
        service = HRRegelsService()
        return {
            'min_rust_uren': service.get_regel_waarde('min_rust_uren', default=12.0),
            'max_uren_week': service.get_regel_waarde('max_uren_week', default=50.0),
            'max_werkdagen_cyclus': service.get_regel_waarde('max_werkdagen_cyclus', default=19),
            'week_definitie': service.get_regel_waarde('week_definitie', default='ma-00:00|zo-23:59'),
            'cyclus_dagen': service.get_regel_waarde('cyclus_dagen', default=28),
            'max_dagen_tussen_rx': service.get_regel_waarde('max_dagen_tussen_rx', default=7),
            'max_werkdagen_reeks': service.get_regel_waarde('max_werkdagen_reeks', default=7),
            'max_weekends_achter_elkaar': service.get_regel_waarde('max_weekends', default=3)
        }
    
    def _load_shift_tijden(self) -> Dict:
        """Laad shift codes uit database"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT code, start_uur, eind_uur FROM shift_codes")
        return {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
    
    def _get_planning_data(self) -> List[PlanningRegel]:
        """Laad planning data voor maand uit database (met cache)"""
        if self._planning_cache is not None:
            return self._planning_cache
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Query voor één maand, één gebruiker
        cursor.execute("""
            SELECT datum, shift_code
            FROM planning
            WHERE gebruiker_id = ? AND jaar = ? AND maand = ?
            ORDER BY datum
        """, (self.gebruiker_id, self.jaar, self.maand))
        
        planning = []
        for row in cursor.fetchall():
            datum_str, shift_code = row
            planning.append(PlanningRegel(
                gebruiker_id=self.gebruiker_id,
                datum=date.fromisoformat(datum_str),
                shift_code=shift_code
            ))
        
        self._planning_cache = planning
        return planning
    
    def invalidate_cache(self):
        """Clear cache na planning wijziging"""
        self._planning_cache = None
        self._violations_cache = {}
```

---

## 6. Presentation Layer - PlanningOptimizer (v0.7.0 - Toekomst)

### 6.1 Skeleton Implementation

```python
# services/planning_optimizer.py
from typing import List, Dict, Optional
from ortools.sat.python import cp_model
from services.constraint_checker import ConstraintChecker, PlanningRegel, Violation
from datetime import date, timedelta

class PlanningOptimizer:
    """
    AI OPTIMIZER - Gebruikt ConstraintChecker voor constraint definitions
    v0.7.0 (TOEKOMST)
    
    Verantwoordelijk voor:
    - CSP model bouwen met OR-Tools
    - Constraint definities (gebruikt ConstraintChecker)
    - Oplossing zoeken (solver)
    - Alternatieve oplossingen genereren
    """
    
    def __init__(self, hr_config: Dict, shift_tijden: Dict):
        self.hr_config = hr_config
        self.shift_tijden = shift_tijden
        
        # Hergebruik checker voor constraint validatie
        self.checker = ConstraintChecker(hr_config, shift_tijden)
        
        # OR-Tools model
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
    
    def optimize_planning(
        self,
        basis_planning: List[PlanningRegel],
        gebruikers: List[int],
        datum_range: tuple[date, date],
        fixed_shifts: Optional[List[PlanningRegel]] = None
    ) -> OptimizedPlanningResult:
        """
        Optimaliseer planning met CSP solver
        
        Args:
            basis_planning: Basis planning vanuit typetabel
            gebruikers: Lijst van gebruiker IDs
            datum_range: (start_datum, eind_datum)
            fixed_shifts: Locked shifts (goedgekeurd verlof, etc.)
        
        Returns:
            OptimizedPlanningResult met oplossing of error
        """
        start_datum, eind_datum = datum_range
        
        # Stap 1: Valideer basis planning met checker
        initial_violations = self.checker.get_all_violations(basis_planning)
        
        if not initial_violations:
            # Basis planning is al geldig!
            return OptimizedPlanningResult(
                success=True,
                planning=basis_planning,
                violations=[],
                improvements="Basis planning was al geldig, geen optimalisatie nodig"
            )
        
        # Stap 2: Bouw CSP variabelen
        # (gebruiker, datum) → shift_code
        shift_vars = {}
        for gebruiker_id in gebruikers:
            for single_date in self._date_range(start_datum, eind_datum):
                var_name = f"shift_u{gebruiker_id}_d{single_date.isoformat()}"
                # Domein = alle mogelijke shift codes + None (leeg)
                shift_vars[(gebruiker_id, single_date)] = self.model.NewIntVar(
                    0, len(self.shift_tijden), var_name
                )
        
        # Stap 3: Add constraints (GEBRUIKT CHECKER!)
        self._add_12u_rust_constraints(shift_vars, gebruikers)
        self._add_max_uren_week_constraints(shift_vars, gebruikers)
        self._add_max_werkdagen_cyclus_constraints(shift_vars, gebruikers)
        # ... etc voor alle constraints
        
        # Stap 4: Add zachte constraints (doelfunctie)
        objective_terms = []
        objective_terms.extend(self._fairness_objectives(shift_vars, gebruikers))
        objective_terms.extend(self._preference_objectives(shift_vars, gebruikers))
        
        # Stap 5: Solve
        self.model.Minimize(sum(objective_terms))
        status = self.solver.Solve(self.model, timeout=30)  # 30 sec timeout
        
        # Stap 6: Extract oplossing
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            optimized_planning = self._extract_solution(shift_vars, gebruikers)
            
            # Valideer oplossing met checker (sanity check)
            final_violations = self.checker.get_all_violations(optimized_planning)
            
            return OptimizedPlanningResult(
                success=True,
                planning=optimized_planning,
                violations=final_violations,
                improvements=f"Violations: {len(initial_violations)} → {len(final_violations)}",
                solve_time=self.solver.WallTime()
            )
        else:
            # Geen oplossing gevonden
            return OptimizedPlanningResult(
                success=False,
                planning=basis_planning,
                violations=initial_violations,
                improvements=None,
                error="CSP solver kon geen geldige oplossing vinden - mogelijk over-constrained"
            )
    
    # ========== PRIVATE - Constraint Definities ==========
    
    def _add_12u_rust_constraints(self, shift_vars, gebruikers):
        """
        Voeg 12u rust constraints toe aan OR-Tools model
        GEBRUIKT: self.checker voor logica definitie
        
        Voor elke (gebruiker, dag N, dag N+1):
            Als shift_N = X en shift_N+1 = Y:
                Dan rust_tussen(X, Y) >= 12u
        """
        for gebruiker_id in gebruikers:
            # ... OR-Tools constraint definitie
            # Hergebruikt helper methods van checker:
            #   - self.checker._bereken_rust_tussen_shifts()
            #   - self.checker._is_rustdag()
            pass
    
    def _add_max_uren_week_constraints(self, shift_vars, gebruikers):
        """Voeg max uren per week constraint toe"""
        # Gebruikt self.checker._bereken_shift_duur()
        pass
    
    # ... Andere constraint methods ...
    
    # ========== PRIVATE - Helpers ==========
    
    def _date_range(self, start: date, end: date):
        """Generator voor datum range"""
        current = start
        while current <= end:
            yield current
            current += timedelta(days=1)
    
    def _extract_solution(self, shift_vars, gebruikers) -> List[PlanningRegel]:
        """Converteer OR-Tools oplossing naar PlanningRegel objecten"""
        planning = []
        for (gebruiker_id, datum), var in shift_vars.items():
            shift_index = self.solver.Value(var)
            if shift_index > 0:  # 0 = lege cel
                shift_code = list(self.shift_tijden.keys())[shift_index - 1]
                planning.append(PlanningRegel(
                    gebruiker_id=gebruiker_id,
                    datum=datum,
                    shift_code=shift_code,
                    gegenereerd_door='ai_optimizer'
                ))
        return planning

@dataclass
class OptimizedPlanningResult:
    """Result van optimalisatie"""
    success: bool
    planning: List[PlanningRegel]
    violations: List[Violation]
    improvements: Optional[str]
    solve_time: float = 0.0
    error: Optional[str] = None
```

---

## 7. Implementation Roadmap

### Fase 1: Core Infrastructure (Week 1 - 8-10 uur)

**Focus:** Bouw herbruikbare ConstraintChecker

**Files:**
- `services/constraint_checker.py` (NIEUW - ~800 regels)
- `tests/test_constraint_checker.py` (NIEUW - ~400 regels)

**Deliverables:**
- ✅ PlanningRegel en Violation data classes
- ✅ ConstraintChecker class met alle 6 check methods
- ✅ Helper functions (tijd berekening, periode parsing)
- ✅ Comprehensive unit tests

**Testing:**
```python
# Unit tests voor elke constraint
def test_12u_rust_normal_case()
def test_12u_rust_midnight_crossing()
def test_50u_week_boundary_cases()
def test_19_dagen_cyclus_rolling_window()
# ... etc
```

### Fase 2: PlanningValidator (Week 2-3 - 20-25 uur)

**Focus:** UI wrapper voor HR Validatie v0.6.25

**Files:**
- `services/planning_validator.py` (NIEUW - ~300 regels)
- `gui/widgets/planner_grid_kalender.py` (UPDATE - +200 regels)
- `gui/dialogs/hr_validatie_rapport_dialog.py` (NIEUW - ~200 regels)

**Deliverables:**
- ✅ PlanningValidator wrapper met caching
- ✅ Real-time validatie (cel edit)
- ✅ Batch validatie (publicatie)
- ✅ UI integratie (rode overlay, tooltips)
- ✅ HRValidatieRapportDialog

**Testing:**
- Integration tests met UI
- Performance tests (30 gebruikers × 30 dagen)

### Fase 3: Documentation & Polish (Week 3 - 5-8 uur)

**Files:**
- `docs/HR_VALIDATIE_GEBRUIKERSHANDLEIDING.md`
- Code comments en docstrings
- Performance profiling

**Deliverables:**
- ✅ Gebruikersdocumentatie
- ✅ Developer documentation
- ✅ Performance optimalisaties

**→ RELEASE v0.6.25** (HR Validatie compleet)

---

### Fase 4: PlanningOptimizer Skeleton (Week 4-5 - 10-15 uur)

**Focus:** Voorbereiden voor v0.7.0 AI Generator

**Files:**
- `services/planning_optimizer.py` (NIEUW - skeleton ~300 regels)
- `requirements.txt` (UPDATE - add ortools)

**Deliverables:**
- ✅ PlanningOptimizer class structuur
- ✅ CSP model basics
- ✅ Integration met ConstraintChecker (hergebruik!)
- ✅ Proof of concept met simpel scenario

**Testing:**
- Basic CSP solving test
- Validatie dat checker correct wordt hergebruikt

### Fase 5: Full Optimizer (Week 6-8 - 20-30 uur)

**Focus:** Complete AI Generator Optie 2

**Files:**
- `services/planning_optimizer.py` (COMPLETE - ~600 regels)
- `gui/dialogs/ai_generator_dialog.py` (NIEUW - ~300 regels)
- `tests/test_planning_optimizer.py` (NIEUW - ~300 regels)

**Deliverables:**
- ✅ Alle 6 constraints in OR-Tools
- ✅ Zachte constraints (fairness, preferences)
- ✅ GUI voor generator
- ✅ Performance optimalisatie
- ✅ Error handling (over-constrained cases)

**→ RELEASE v0.7.0** (AI Generator Optie 2 compleet)

---

## 8. Testing Strategie

### 8.1 Unit Tests - ConstraintChecker

```python
# tests/test_constraint_checker.py
import unittest
from datetime import date
from services.constraint_checker import ConstraintChecker, PlanningRegel

class TestConstraintChecker(unittest.TestCase):
    
    def setUp(self):
        """Setup test data"""
        self.hr_config = {
            'min_rust_uren': 12.0,
            'max_uren_week': 50.0,
            'max_werkdagen_cyclus': 19,
            'week_definitie': 'ma-00:00|zo-23:59',
            'cyclus_dagen': 28,
            'max_dagen_tussen_rx': 7,
            'max_werkdagen_reeks': 7,
            'max_weekends_achter_elkaar': 3
        }
        
        self.shift_tijden = {
            'E': ('06:00', '14:00'),
            'L': ('14:00', '22:00'),
            'N': ('22:00', '06:00'),
            'RX': ('00:00', '00:00')
        }
        
        self.checker = ConstraintChecker(self.hr_config, self.shift_tijden)
    
    def test_12u_rust_normal_case(self):
        """Test normale 12u rust tussen E en L shifts"""
        planning = [
            PlanningRegel(1, date(2025, 11, 1), 'E'),  # 06:00-14:00
            PlanningRegel(1, date(2025, 11, 2), 'L'),  # 14:00-22:00 (volgende dag)
        ]
        result = self.checker.check_12u_rust(planning, gebruiker_id=1)
        
        # 14:00 → 14:00 volgende dag = 24u rust = OK
        self.assertEqual(len(result.violations), 0)
    
    def test_12u_rust_violation(self):
        """Test 12u rust violation"""
        planning = [
            PlanningRegel(1, date(2025, 11, 1), 'E'),  # 06:00-14:00
            PlanningRegel(1, date(2025, 11, 2), 'E'),  # 06:00-14:00 (volgende dag)
        ]
        result = self.checker.check_12u_rust(planning, gebruiker_id=1)
        
        # 14:00 → 06:00 volgende dag = 16u rust = OK
        self.assertEqual(len(result.violations), 0)
        
        # Maar als we N shift toevoegen:
        planning.append(PlanningRegel(1, date(2025, 11, 3), 'N'))  # 22:00-06:00
        result = self.checker.check_12u_rust(planning, gebruiker_id=1)
        
        # 14:00 → 22:00 volgende dag = 8u rust = VIOLATION
        self.assertGreater(len(result.violations), 0)
        self.assertEqual(result.violations[0].type.value, 'min_rust_12u')
    
    def test_12u_rust_midnight_crossing(self):
        """Test 12u rust met midnight crossing shifts"""
        planning = [
            PlanningRegel(1, date(2025, 11, 1), 'N'),  # 22:00-06:00 (next day)
            PlanningRegel(1, date(2025, 11, 2), 'E'),  # 06:00-14:00
        ]
        result = self.checker.check_12u_rust(planning, gebruiker_id=1)
        
        # N eindigt 06:00 op dag 2, E start 06:00 op dag 2 = 0u rust = VIOLATION
        self.assertGreater(len(result.violations), 0)
    
    def test_12u_rust_reset_by_rx(self):
        """Test dat RX/CX rust reset"""
        planning = [
            PlanningRegel(1, date(2025, 11, 1), 'N'),   # 22:00-06:00
            PlanningRegel(1, date(2025, 11, 2), 'RX'),  # Rustdag
            PlanningRegel(1, date(2025, 11, 3), 'E'),   # 06:00-14:00
        ]
        result = self.checker.check_12u_rust(planning, gebruiker_id=1)
        
        # RX breekt de check - geen violation
        self.assertEqual(len(result.violations), 0)
    
    def test_50u_week_normal_case(self):
        """Test normale week met <50u"""
        planning = [
            # Week 1: 6 × 8u = 48u
            PlanningRegel(1, date(2025, 11, 3), 'E'),  # ma
            PlanningRegel(1, date(2025, 11, 4), 'E'),  # di
            PlanningRegel(1, date(2025, 11, 5), 'E'),  # wo
            PlanningRegel(1, date(2025, 11, 6), 'E'),  # do
            PlanningRegel(1, date(2025, 11, 7), 'E'),  # vr
            PlanningRegel(1, date(2025, 11, 8), 'E'),  # za
        ]
        result = self.checker.check_max_uren_week(planning, gebruiker_id=1)
        
        self.assertEqual(len(result.violations), 0)
    
    def test_50u_week_violation(self):
        """Test week met >50u"""
        planning = [
            # Week 1: 7 × 8u = 56u > 50u
            PlanningRegel(1, date(2025, 11, 3), 'E'),   # ma
            PlanningRegel(1, date(2025, 11, 4), 'E'),   # di
            PlanningRegel(1, date(2025, 11, 5), 'E'),   # wo
            PlanningRegel(1, date(2025, 11, 6), 'E'),   # do
            PlanningRegel(1, date(2025, 11, 7), 'E'),   # vr
            PlanningRegel(1, date(2025, 11, 8), 'E'),   # za
            PlanningRegel(1, date(2025, 11, 9), 'E'),   # zo
        ]
        result = self.checker.check_max_uren_week(planning, gebruiker_id=1)
        
        self.assertGreater(len(result.violations), 0)
        self.assertEqual(result.violations[0].type.value, 'max_uren_week')
    
    # ... Meer tests voor andere constraints ...

if __name__ == '__main__':
    unittest.main()
```

### 8.2 Integration Tests

```python
# tests/integration/test_hr_validatie_flow.py
def test_real_time_validation_on_cel_edit():
    """Test complete flow: UI edit → validator → overlay update"""
    # Setup planning grid
    # Edit cel
    # Assert: violations detected, overlay shown, tooltip correct
    pass

def test_publicatie_validation_flow():
    """Test complete flow: publicatie → validator → rapport dialog"""
    # Setup planning met violations
    # Click publiceren
    # Assert: rapport dialog shown met violations lijst
    # Confirm publicatie
    # Assert: planning gepubliceerd ondanks violations
    pass
```

### 8.3 Performance Tests

```python
# tests/performance/test_constraint_checker_performance.py
def test_checker_performance_large_dataset():
    """Test checker performance met 30 gebruikers × 30 dagen"""
    import time
    
    # Generate 900 planning regels
    planning = []
    for gebruiker_id in range(1, 31):
        for dag in range(1, 31):
            planning.append(PlanningRegel(
                gebruiker_id=gebruiker_id,
                datum=date(2025, 11, dag),
                shift_code='E'
            ))
    
    # Benchmark
    start = time.time()
    result = checker.check_all(planning)
    duration = time.time() - start
    
    # Assert: <2 sec voor batch validatie
    assert duration < 2.0, f"Performance te traag: {duration}s"
```

---

## 9. Migration & Rollout

### 9.1 Database Migraties - Geen nodig!

**Voordeel van deze architectuur:** Alle data classes (PlanningRegel, Violation) zijn **database-agnostic**.

Voor v0.6.25 (HR Validatie):
- ✅ Geen schema wijzigingen nodig
- ✅ Werkt met bestaande tables

Voor v0.7.0 (AI Generator):
- Optioneel: Add metadata kolommen aan `planning` tabel
  ```sql
  ALTER TABLE planning ADD COLUMN gegenereerd_door TEXT
  ALTER TABLE planning ADD COLUMN confidence_score REAL
  ```

### 9.2 Rollout Strategy

**v0.6.25 - HR Validatie:**
1. Deploy in test omgeving
2. Run performance tests
3. UAT met 2-3 planners
4. Geleidelijke rollout (feature flag?)
5. Monitor violations rapportage

**v0.7.0 - AI Generator:**
1. Deploy optimizer in "preview" mode
2. Genereer planning in test maand (parallel aan handmatige)
3. Vergelijk resultaten
4. UAT met early adopters
5. Production rollout

---

## 10. Success Metrics

### v0.6.25 - HR Validatie

**Functionaliteit:**
- ✅ 6 HR regels correct gevalideerd
- ✅ Violations accuracy: >95%
- ✅ Real-time feedback: <100ms
- ✅ Batch validatie: <2 sec voor 30 gebruikers

**Usability:**
- ✅ Planners begrijpen violation messages
- ✅ Rode overlay is duidelijk
- ✅ Warnings blokkeren niet (soft warning)

### v0.7.0 - AI Generator

**Performance:**
- ✅ Solve tijd: <30 sec voor 1 maand
- ✅ >60% planningen zonder violations na eerste generatie
- ✅ >90% na optimalisatie

**Adoption:**
- ✅ >50% van maandplanningen gebruikt AI generator binnen 3 maanden
- ✅ Planner satisfaction: >4/5 sterren

**Efficiency:**
- ✅ Tijd bespaard: 4u handmatig → 30min (review + tweaks)

---

## 11. Risks & Mitigatie

| Risico | Impact | Kans | Mitigatie |
|--------|--------|------|-----------|
| ConstraintChecker bugs impact beide systemen | Hoog | Laag | Extensive unit tests, code review |
| Performance bottleneck in checker | Gemiddeld | Laag | Profiling, caching, optimalisatie |
| OR-Tools installatie problemen (Windows) | Hoog | Laag | Pre-compiled wheels, fallback plan |
| Over-engineering voor v0.6.25 | Laag | Gemiddeld | Stay focused, YAGNI voor nu niet nodige features |
| Checker logica te complex voor onderhoud | Gemiddeld | Laag | Goede documentatie, helper methods, tests |

---

## 12. Conclusie

Deze geïntegreerde architectuur biedt **het beste van beide werelden**:

✅ **Nu (v0.6.25):** Robuuste HR validatie met herbruikbare core  
✅ **Toekomst (v0.7.0):** Gemakkelijke integratie van AI optimizer  
✅ **Onderhoud:** Constraint logica op één plek  
✅ **Kwaliteit:** Consistent gedrag, goed getest  
✅ **Efficiency:** ~6 uur netto besparing over beide releases

**Aanbeveling:** START met Fase 1 (ConstraintChecker) deze week, dan Fase 2 (PlanningValidator) volgende week. Dit geeft v0.6.25 binnen 3-4 weken, met perfecte basis voor v0.7.0 later.

---

**Document versie:** 1.0  
**Auteur:** Claude (Anthropic) + Planning Tool Development Team  
**Status:** READY FOR IMPLEMENTATION  
**Laatste update:** 31 Oktober 2025

**Next steps:**
1. Review dit document met team
2. Start Fase 1: Implementeer ConstraintChecker
3. Setup test framework
4. Begin met unit tests

Veel succes! 🚀
