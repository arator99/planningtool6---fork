# HR Validatie Systeem - Technisch Design Document

**Versie:** 1.0
**Datum:** 30 Oktober 2025
**Status:** ✅ **ACTIEF DESIGN** - Ready for Implementation (3 nov 2025)
**Target Release:** v0.6.26 of later (na v0.6.25 cache release)

⚠️ **Implementatie Strategie:** Hybride benadering
- **Dit document:** Concrete implementatie details, algoritmes, edge cases
- **Geïntegreerde Architectuur:** Zie `GEINTEGREERDE_CONSTRAINT_ARCHITECTUUR.md` voor toekomstbestendige structuur
- **Doel:** Slim bouwen met ConstraintChecker laag zodat AI integratie later geen volledige refactor vereist

---

## 1. Executive Summary

Het HR Validatie Systeem controleert automatisch 6 HR regels tijdens het roosteren. Violations krijgen **rode overlay** in planning grid (consistent met bemanningscontrole v0.6.20). Publicatie toont **warning dialog** maar blokkeert niet (soft waarschuwing).

**Scope:**
- ✅ 6 HR regels validatie (12u rust, 50u/week, 19 dagen/cyclus, 7 dagen tussen RX/CX, 7 werkdagen reeks, max weekends)
- ✅ Real-time feedback tijdens roosteren
- ✅ Pre-publicatie validatie rapport
- ✅ Typetabel pre-activatie check

**Effort Estimate:** 28-38 uur over 5-6 sessies

---

## 2. Architectuur Overzicht

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Planning Editor UI                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Grid Kalender│  │ Publicatie   │  │ Typetabel    │ │
│  │ + Rode       │  │ Rapport      │  │ Activatie    │ │
│  │   Overlay    │  │ Dialog       │  │ Validatie    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
          ┌──────────────────────────────────────┐
          │    PlanningValidator Service         │
          │  ┌────────────────────────────────┐  │
          │  │ validate_all()                 │  │
          │  │ validate_shift()               │  │
          │  │ get_violation_level()          │  │
          │  │                                │  │
          │  │ check_12u_rust()               │  │
          │  │ check_max_uren_week()          │  │
          │  │ check_max_werkdagen_cyclus()   │  │
          │  │ check_max_dagen_tussen_rx()    │  │
          │  │ check_max_werkdagen_reeks()    │  │
          │  │ check_max_weekends()           │  │
          │  └────────────────────────────────┘  │
          └──────────┬──────────────┬────────────┘
                     │              │
          ┌──────────▼──────┐  ┌────▼─────────────┐
          │ HRRegelsService │  │ Database         │
          │ - get regels    │  │ - shift_codes    │
          │ - parse periode │  │ - planning       │
          └─────────────────┘  │ - hr_regels      │
                               │ - speciale_codes │
                               └──────────────────┘
```

### 2.2 Data Flow

**Real-time Validatie (Cel Edit):**
```
User edit cel → save shift → PlanningValidator.validate_shift()
→ check violations → update cache → refresh cel overlay + tooltip
→ show warning dialog (non-blocking)
```

**Batch Validatie (Publicatie):**
```
User click "Publiceren" → PlanningValidator.validate_all() voor alle gebruikers
→ collect violations → show HRValidatieRapportDialog
→ User bevestigt → publiceer ondanks violations
```

---

## 3. Data Model

### 3.1 Violation Data Class

```python
@dataclass
class Violation:
    """Data class voor HR regel overtredingen"""
    regel: str                    # 'min_rust_12u', 'max_uren_week', etc.
    datum: str                    # '2025-11-15' of None voor range violations
    datum_range: Optional[Tuple[str, str]]  # Voor week/periode violations
    gebruiker_id: int
    beschrijving: str             # NL tekst: "Te weinig rust: 10.5u tussen shifts"
    severity: str                 # 'error' of 'warning'
    details: Dict[str, Any]       # Extra context (shift codes, uren, etc.)

    def to_dict(self) -> dict:
        """Serialisatie voor caching/logging"""

    def to_user_message(self) -> str:
        """User-friendly bericht voor dialogs"""
```

### 3.2 Database Schema (Bestaand)

**shift_codes** - Shift tijden opslag
```sql
code TEXT,
start_uur TEXT NOT NULL,  -- "06:00", "14:00", "22:00"
eind_uur TEXT NOT NULL,   -- "14:00", "22:00", "06:00"
```

**planning** - Planning records
```sql
datum TEXT NOT NULL,      -- "2025-11-15"
shift_code TEXT,          -- Kan shift_code OF speciale_code zijn
```

**hr_regels** - Configuratie
```sql
naam TEXT,                -- 'min_rust_uren', 'max_uren_week', etc.
waarde TEXT,              -- '12.0', '50.0', 'ma-00:00|zo-23:59'
eenheid TEXT,             -- 'uur', 'dagen', 'periode'
```

---

## 4. PlanningValidator Service

### 4.1 Class Structuur

```python
class PlanningValidator:
    """
    Centraal validatie systeem voor alle HR regels

    Usage:
        validator = PlanningValidator(gebruiker_id=123, jaar=2025, maand=11)
        violations = validator.validate_all()
    """

    def __init__(self, gebruiker_id: int, jaar: int, maand: int):
        self.gebruiker_id = gebruiker_id
        self.jaar = jaar
        self.maand = maand

        # Laad HR regels uit database
        self.hr_config = self._load_hr_config()

        # Laad planning data voor maand
        self.planning_data = self._load_planning_data()

        # Cache voor shift tijden
        self._shift_tijden_cache: Dict[str, Tuple[str, str]] = {}

    def validate_all(self) -> Dict[str, List[Violation]]:
        """
        Run alle validaties voor complete maand

        Returns: {
            'min_rust_12u': [Violation(...), ...],
            'max_uren_week': [...],
            ...
        }
        """
        results = {}
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
        """
        violations = []
        violations.extend(self._check_12u_rust_single(datum))
        violations.extend(self._check_50u_week_single(datum))
        return violations

    def get_violation_level(self, datum: str) -> str:
        """
        Voor UI overlay kleur bepaling

        Returns: 'none', 'warning', 'error'
        """
        violations = self.validate_shift(datum, None)
        if not violations:
            return 'none'
        has_errors = any(v.severity == 'error' for v in violations)
        return 'error' if has_errors else 'warning'
```

### 4.2 Helper Functions

```python
# Tijd berekening helpers
def bereken_shift_duur(start_uur: str, eind_uur: str) -> float:
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

def bereken_rust_tussen_shifts(
    datum1: str, eind_uur1: str,
    datum2: str, start_uur2: str
) -> float:
    """
    Bereken rust tussen twee shifts in uren

    Returns: Aantal uren rust (kan negatief zijn als overlap)
    """
    dt1 = datetime.strptime(f"{datum1} {eind_uur1}", "%Y-%m-%d %H:%M")
    dt2 = datetime.strptime(f"{datum2} {start_uur2}", "%Y-%m-%d %H:%M")
    delta = dt2 - dt1
    return delta.total_seconds() / 3600

# Periode parsing helpers
def parse_periode_definitie(waarde: str) -> Tuple[str, str, str, str]:
    """
    Parse 'ma-00:00|zo-23:59' → (start_dag, start_uur, eind_dag, eind_uur)

    Returns: ('ma', '00:00', 'zo', '23:59')
    """
    start, eind = waarde.split('|')
    start_dag, start_uur = start.split('-', 1)
    eind_dag, eind_uur = eind.split('-', 1)
    return (start_dag.strip(), start_uur.strip(),
            eind_dag.strip(), eind_uur.strip())

def shift_overlapt_periode(
    shift_datum: str, shift_start: str, shift_eind: str,
    periode_start: datetime, periode_eind: datetime
) -> bool:
    """
    Check of shift overlapt met periode (exclusieve grenzen)

    Logica: (shift_start < periode_eind) AND (shift_eind > periode_start)

    Returns: True als overlap, False als geen overlap
    """
    shift_start_dt = datetime.strptime(f"{shift_datum} {shift_start}", "%Y-%m-%d %H:%M")
    shift_eind_dt = datetime.strptime(f"{shift_datum} {shift_eind}", "%Y-%m-%d %H:%M")

    # Middernacht crossing
    if shift_eind_dt < shift_start_dt:
        shift_eind_dt += timedelta(days=1)

    return (shift_start_dt < periode_eind) and (shift_eind_dt > periode_start)
```

---

## 5. HR Regels Specificatie (Compact)

### 5.1 Regel: 12u Rust Tussen Shifts 🔴 CRITICAL

**Business Rule:** Tussen twee opeenvolgende shifts moet minimaal 12 uur rust zitten.

**Algoritme:**
```
1. Haal planning records sorted by datum
2. Loop door opeenvolgende dagen (N, N+1)
3. Voor elk paar:
   a. Haal shift tijden op
   b. Check reset_12u_rust flag (RX, CX, Z)
   c. Bereken rust = shift2_start - shift1_eind
   d. Als rust < 12u → Violation
```

**Query Pattern:**
```sql
SELECT
    p1.datum, p1.shift_code,
    sc1.eind_uur as shift1_eind,
    p2.datum as next_datum, p2.shift_code as next_code,
    sc2.start_uur as shift2_start,
    spc1.reset_12u_rust
FROM planning p1
LEFT JOIN planning p2 ON p2.gebruiker_id = p1.gebruiker_id
    AND p2.datum = date(p1.datum, '+1 day')
LEFT JOIN shift_codes sc1 ON p1.shift_code = sc1.code
LEFT JOIN shift_codes sc2 ON p2.shift_code = sc2.code
LEFT JOIN speciale_codes spc1 ON p1.shift_code = spc1.code
WHERE p1.gebruiker_id = ?
ORDER BY p1.datum
```

**Edge Cases:**
- Middernacht crossing (shift 22:00-06:00)
- RX/CX/Z codes resetten 12u teller
- Speciale codes zonder shift tijden (skip)
- Meerdere dagen vrij tussen shifts (altijd OK)

**Violation Output:**
```python
Violation(
    regel='min_rust_12u',
    datum='2025-11-15',
    beschrijving='Te weinig rust: 10.5u tussen shifts (minimaal 12u)',
    severity='error',
    details={'shift1': 'L (14:00-22:00)', 'shift2': 'V (06:30-14:00)',
             'rust_uren': 10.5}
)
```

### 5.2 Regel: Maximum 50u per Week 🟡 MEDIUM

**Business Rule:** Maximum 50 uur gewerkt per week.

**Week Definitie:** Configureerbaar via hr_regels (default: ma-00:00|zo-23:59)

**Algoritme:**
```
1. Haal week_definitie uit hr_regels
2. Bepaal alle weken in maand
3. Per week:
   a. Haal shifts in week range
   b. Bereken shift duur per shift
   c. Tel totaal uren
   d. Als > 50u → Violation
```

**Violation Output:**
```python
Violation(
    regel='max_uren_week',
    datum_range=('2025-11-10', '2025-11-16'),
    beschrijving='Te veel uren: 52.5u in week 46 (maximaal 50u)',
    severity='error',
    details={'week': 46, 'totaal_uren': 52.5}
)
```

### 5.3 Regel: 19 Werkdagen per Cyclus ✅ HERGEBRUIK

**Business Rule:** Max 19 werkdagen per 28-dagen cyclus (rode lijn periode).

**Status:** Visueel al geïmplementeerd (v0.6.19) - alleen validatie toevoegen.

**Hergebruik:**
```python
def check_max_werkdagen_cyclus(self):
    # Hergebruik uit planner_grid_kalender.py:
    # - get_relevante_rode_lijn_periodes()
    # - tel_gewerkte_dagen()

    periodes = self.get_relevante_rode_lijn_periodes()
    for periode in periodes:
        dagen = tel_gewerkte_dagen(self.gebruiker_id,
                                   periode.start, periode.eind)
        if dagen > 19:
            yield Violation(...)
```

### 5.4 Regel: 7 Dagen Tussen RX/CX 🟡 MEDIUM

**Business Rule:** Max 7 dagen tussen twee rustdagen (RX of CX).

**Algoritme:**
```
1. Haal alle RX/CX codes (term-based query)
2. Loop door opeenvolgende rustdagen
3. Bereken dagen tussen rustdagen
4. Als > 7 dagen → Violation
```

**Query:** Term-based via TermCodeService (speciale_codes.term IN ('zondagrust', 'zaterdagrust'))

### 5.5 Regel: 7 Werkdagen Achter Elkaar 🟡 MEDIUM

**Business Rule:** Max 7 werkdagen achter elkaar zonder rustdag.

**Algoritme (State Machine):**
```
werkdagen_reeks = 0
for dag in maand:
    if dag heeft shift AND telt_als_werkdag=1:
        werkdagen_reeks += 1
    elif dag heeft breekt_werk_reeks=1 OR geen shift:
        werkdagen_reeks = 0  # Reset

    if werkdagen_reeks > 7:
        yield Violation(...)
```

### 5.6 Regel: Max Weekends Achter Elkaar 🟡 MEDIUM

**Business Rule:** Max 6 weekends achter elkaar werken.

**Weekend Definitie:** Configureerbaar (default: vr-22:00|ma-06:00)

**Algoritme:**
```
1. Haal weekend_definitie
2. Bepaal alle weekends in range
3. Per weekend: check of shift overlapt (exclusieve grenzen)
4. Tel opeenvolgende weekends met shifts
5. Als > 6 → Violation
```

---

## 6. UI Integratie Specificatie

### 6.1 Rode Overlay in Grid Kalender

**Pattern:** Hergebruik bemanningscontrole overlay (v0.6.20)

**CSS Styling:**
```python
# Error (rood - 40% opacity)
"""
background: qlineargradient(
    x1:0, y1:0, x2:1, y2:1,
    stop:0 rgba(229, 115, 115, 0.4),
    stop:1 rgba(229, 115, 115, 0.4)
);
"""

# Warning (geel - 40% opacity) - optioneel
"""
background: qlineargradient(
    x1:0, y1:0, x2:1, y2:1,
    stop:0 rgba(255, 224, 130, 0.4),
    stop:1 rgba(255, 224, 130, 0.4)
);
"""
```

**Implementatie in planner_grid_kalender.py:**
```python
# Instance variable
self.hr_violations: Dict[str, Dict[int, List[Violation]]] = {}

def load_hr_violations(self):
    """Laad violations voor alle gebruikers"""
    for gebruiker_id in self.filter_gebruikers:
        validator = PlanningValidator(gebruiker_id, self.jaar, self.maand)
        violations = validator.validate_all()
        # Map naar {datum: {user: [violations]}}

def get_hr_overlay_kleur(self, datum_str, gebruiker_id) -> str:
    """Return qlineargradient CSS of empty string"""

def get_hr_tooltip(self, datum_str, gebruiker_id) -> str:
    """Return HTML formatted violation list"""

def update_hr_status_voor_datum(self, datum_str):
    """Real-time update na cel edit"""
```

### 6.2 Warning Dialog (Non-Blocking)

**Trigger:** Na cel edit met violations

**UI:**
```
┌────────────────────────────────────────┐
│  HR Regel Overtredingen                │
├────────────────────────────────────────┤
│  De volgende overtredingen gevonden:   │
│                                        │
│  • Te weinig rust: 10.5u tussen shifts │
│  • Te veel uren: 52.5u in week 46     │
│                                        │
│  De wijziging is opgeslagen.           │
│  Controleer planning voor publicatie.  │
│                                        │
│             [ OK ]                     │
└────────────────────────────────────────┘
```

**Code:**
```python
def show_hr_violation_warning(self, violations: List[Violation]):
    msg = "De volgende HR regel overtredingen zijn gedetecteerd:\n\n"
    for v in violations:
        msg += f"• {v.beschrijving}\n"
    msg += "\nDe wijziging is opgeslagen. Controleer de planning voor publicatie."
    QMessageBox.warning(self, "HR Regel Overtredingen", msg)
```

### 6.3 Pre-Publicatie Rapport Dialog

**Nieuw bestand:** `gui/dialogs/hr_validatie_rapport_dialog.py`

**UI Layout:**
```
┌─────────────────────────────────────────────────────┐
│  HR Validatie Rapport - November 2025               │
├─────────────────────────────────────────────────────┤
│  ⚠ Er zijn HR regel overtredingen gevonden          │
│                                                      │
│  Samenvatting:                                       │
│  ✗ 12u rust: 5 violations                           │
│  ✗ 50u/week: 2 violations                           │
│  ⚠ 7 werkdagen reeks: 3 warnings                    │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ Naam          Regel    Datum      Details   │   │
│  ├─────────────────────────────────────────────┤   │
│  │ Jan Vermeer   12u rust 15-11  10.5u rust   │   │
│  │ Marie Klaas   50u week week 46 52.5u        │   │
│  │ ...                                         │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  Wilt u toch publiceren?                             │
│                                                      │
│  [ Annuleren ]          [ Toch Publiceren ]         │
└─────────────────────────────────────────────────────┘
```

**Integratie:**
```python
# In planning_editor_screen.py
def publiceer_planning(self):
    # Run volledige HR validatie
    all_violations = self.run_volledige_hr_validatie()

    if all_violations:
        dialog = HRValidatieRapportDialog(self, all_violations)
        if dialog.exec() == QDialog.DialogCode.Rejected:
            return  # Annuleren

    # Excel export + database update (bestaande code)
```

---

## 7. Typetabel Validatie

### 7.1 Pre-Activatie Check

**Locatie:** `gui/screens/typetabel_beheer_screen.py`

**Validatie Types:**

**A. Structurele Validatie:**
```python
def validate_typetabel_structuur(versie_id) -> List[str]:
    errors = []

    # Check 1: Alle weken ingevuld?
    # Check 2: Alle dagen hebben shift_type?
    # Check 3: Realistische codes?

    return errors  # Block activation als errors
```

**B. Pattern Validatie (Simulatie):**
```python
def validate_typetabel_pattern(versie_id) -> Dict[str, List[Violation]]:
    # Simuleer planning voor fictieve gebruiker
    fictief_gebruiker_id = -1

    # Genereer planning uit typetabel (1 cyclus)
    planning_data = simuleer_planning(versie_id)

    # Run validator
    validator = PlanningValidator(fictief_gebruiker_id, 2025, 1)
    validator.planning_data = planning_data
    violations = validator.validate_all()

    return violations  # Warn, maar niet blokkeren
```

**UI Flow:**
```
Activeren button → Structuur check → Errors? → Block
                                   ↓
                              Pattern check → Violations? → Warning dialog
                                              ↓
                                         Datum picker → Bevestiging → Activeren
```

---

## 8. Implementation Roadmap

### Fase 1: Service Layer (6-8 uur)
**Files:**
- `services/planning_validator_service.py` (NIEUW - ~600 regels)
- `services/hr_regels_service.py` (UPDATE - +100 regels)

**Deliverables:**
- Violation class
- PlanningValidator class skeleton
- Helper functions (tijd, periode)
- HRRegelsService extensions

### Fase 2: Core Validaties (14-18 uur)
**Methods in PlanningValidator:**
- check_12u_rust() - 6-8 uur (complex)
- check_max_uren_week() - 4-6 uur
- check_max_werkdagen_cyclus() - 2-3 uur (hergebruik)
- check_max_dagen_tussen_rx() - 3-4 uur
- check_max_werkdagen_reeks() - 3-4 uur
- check_max_weekends_achter_elkaar() - 4-5 uur

**Testing:**
- Unit tests per regel
- Edge case tests

### Fase 3: UI Integratie (6-8 uur)
**Files:**
- `gui/widgets/planner_grid_kalender.py` (UPDATE - +200 regels)

**Deliverables:**
- load_hr_violations()
- get_hr_overlay_kleur()
- get_hr_tooltip()
- update_hr_status_voor_datum()
- show_hr_violation_warning()

### Fase 4: Rapporten (4-6 uur)
**Files:**
- `gui/dialogs/hr_validatie_rapport_dialog.py` (NIEUW - ~200 regels)
- `gui/screens/planning_editor_screen.py` (UPDATE - +100 regels)

**Deliverables:**
- HRValidatieRapportDialog
- Pre-publicatie validatie flow
- Tabel layout met violations

### Fase 5: Typetabel Validatie (4-6 uur)
**Files:**
- `gui/screens/typetabel_beheer_screen.py` (UPDATE - +150 regels)

**Deliverables:**
- validate_typetabel_structuur()
- validate_typetabel_pattern()
- TypetabelValidatieDialog (optioneel)
- Pre-activatie flow

**Totaal: 34-46 uur**

---

## 9. Testing Strategie

### Unit Tests (tests/test_planning_validator.py)

**Per Regel:**
- test_12u_rust_normal_case()
- test_12u_rust_midnight_crossing()
- test_12u_rust_reset_by_rx()
- test_50u_week_normal_case()
- test_50u_week_custom_week_definitie()
- test_19_dagen_exact_limit()
- test_7_dagen_tussen_rx_violation()
- test_7_werkdagen_reeks_with_reset()
- test_max_weekends_consecutive()

**Helper Functions:**
- test_bereken_shift_duur()
- test_bereken_rust_tussen_shifts()
- test_parse_periode_definitie()
- test_shift_overlapt_periode()

### Integration Tests

**Scenario 1: Complete Maand Validatie**
```python
def test_full_month_validation():
    # Setup: gebruiker met diverse shifts
    # Execute: validator.validate_all()
    # Assert: expected violations count & types
```

**Scenario 2: Real-time Update**
```python
def test_realtime_validation_on_edit():
    # Setup: planning grid met cel edit
    # Execute: on_cel_edited()
    # Assert: hr_violations cache updated, overlay visible
```

### Manual Test Scenarios

**Checklist:**
- [ ] Rode overlay verschijnt bij 12u rust violation
- [ ] Tooltip toont violation details (NL tekst)
- [ ] Warning dialog na cel edit (non-blocking)
- [ ] Pre-publicatie rapport toont alle violations
- [ ] Publicatie slaagt ondanks violations
- [ ] Typetabel activatie blokkeert bij structuur errors
- [ ] Typetabel pattern warnings tonen
- [ ] Performance OK bij 30 gebruikers × 30 dagen

---

## 10. Performance Overwegingen

### Caching Strategie

```python
class PlanningValidator:
    def __init__(self):
        # Cache shift tijden lookup (read-heavy)
        self._shift_tijden_cache: Dict[str, Tuple[str, str]] = {}

        # Cache HR regels config (read-heavy)
        self._hr_config_cache: Dict[str, Any] = None

        # Cache validation results (per datum)
        self._validation_cache: Dict[str, List[Violation]] = {}
```

**Cache Invalidation:**
- Cel edit → invalideer datum + omliggende dagen (12u rust check)
- Maand navigatie → clear alle caches
- HR regels wijziging → clear config cache

### Incremental Updates

**Real-time (Light):**
- validate_shift() - alleen 12u rust + 50u week
- Scope: 1 datum + omliggende dagen
- Performance: <100ms

**Batch (Full):**
- validate_all() - alle 6 regels
- Scope: complete maand
- Performance: <2 sec voor 30 gebruikers

### Query Optimization

**Pattern:** Batch queries ipv N+1
```python
# GOOD: 1 query voor alle shifts
SELECT * FROM planning WHERE gebruiker_id = ? AND maand = ?

# BAD: 30 queries (1 per dag)
for dag in maand:
    SELECT * FROM planning WHERE datum = ?
```

---

## 11. Open Questions & Decisions

### Design Decisions (Gemaakt)

✅ **Validatie Strictheid:** WAARSCHUWEN (niet BLOKKEREN)
✅ **UI Feedback:** Rode overlay alleen bij errors
✅ **Versie Planning:** v0.6.25 single release
✅ **HR Regel Waarden:** Correct volgens organisatie

### Open Questions (Te bespreken tijdens implementatie)

**Error Messages:**
- Wording validation descriptions (NL) - review met gebruikers
- Tooltip formatting (HTML layout) - optimaliseren voor leesbaarheid

**Performance:**
- Target response time real-time validatie: <100ms?
- Target response time batch validatie: <2 sec?
- Cache TTL: oneindig of timeout?

**Future Enhancements:**
- Violations export naar Excel (extra sheet)?
- Violations logging (audit trail)?
- Custom HR regels (plugin systeem)?

---

## 12. Reference Code (Bestaand)

### Bemanningscontrole Overlay (v0.6.20)

**Patroon voor HR validatie overlay:**
```python
# Uit planner_grid_kalender.py:1720-1750
def get_bemannings_overlay_kleur(self, datum_str: str) -> str:
    status = self.bemannings_status.get(datum_str)
    if status == 'rood':
        return """
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:1,
            stop:0 rgba(229, 115, 115, 0.4),
            stop:1 rgba(229, 115, 115, 0.4)
        );
        """
    # ... etc
```

**Herbruikbaar voor HR violations:**
- Zelfde CSS pattern
- Zelfde opacity (40%)
- Zelfde tooltip pattern

### HR Kolommen Code (v0.6.19)

**Patroon voor werkdagen telling:**
```python
# Uit planner_grid_kalender.py:353-464
def tel_gewerkte_dagen(self, gebruiker_id, start, eind):
    cursor.execute("""
        SELECT COUNT(DISTINCT p.datum)
        FROM planning p
        LEFT JOIN shift_codes sc ON p.shift_code = sc.code
        LEFT JOIN werkposten w ON sc.werkpost_id = w.id
        LEFT JOIN speciale_codes spc ON p.shift_code = spc.code
        WHERE p.gebruiker_id = ?
          AND p.datum BETWEEN ? AND ?
          AND (w.telt_als_werkdag = 1 OR spc.telt_als_werkdag = 1)
          AND p.shift_code IS NOT NULL
          AND p.shift_code != ''
    """, (gebruiker_id, start, eind))
```

**Herbruikbaar voor 19 dagen cyclus validatie**

---

## 13. Conclusion

Dit design document bevat alle specificaties voor implementatie van het HR Validatie Systeem. Het systeem bouwt voort op bestaande patterns (bemanningscontrole v0.6.20, HR kolommen v0.6.19) en introduceert een robuuste validator service voor alle 6 HR regels.

**Klaar voor implementatie:** Alle algoritmes, queries, en UI patterns zijn gedocumenteerd.

**Geschatte effort:** 34-46 uur over 5-6 sessies.

**Target release:** v0.6.25 (single release).

---

**Document Versie:** 1.0
**Auteur:** Planning Tool Development Team
**Review Status:** Ready for Implementation
**Laatste Update:** 30 Oktober 2025
