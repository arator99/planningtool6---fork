# AI Planning Generator - Future Uitbreiding

## Overzicht

Een geautomatiseerd planning generatie systeem dat intelligente roosters kan maken op basis van typetabellen, HR-regels, en teamvoorkeuren. Dit document beschrijft de architectuur en implementatiestrategie voor een AI-aangedreven planning module.

## Waarom is dit haalbaar?

### Sterke Fundering

Het huidige systeem heeft alle bouwstenen voor AI planning:

1. **Typetabel Systeem** (database/connection.py:175-199)
   - Herhalende shift patronen (1-52 weken)
   - Versioning systeem (CONCEPT → ACTIEF → ARCHIEF)
   - Per-gebruiker offset via `startweek_typedienst`

2. **Planning Data Model** (database/connection.py:123-133)
   - Simpele structuur: gebruiker_id + datum + shift_code
   - Status tracking (concept/gepubliceerd)
   - Unique constraint voorkomt dubbele entries

3. **Harde Constraints** (HR Regels)
   - 12 uur rust tussen shifts
   - Max 50 uur per week
   - Max 19 werkdagen per 28-dagen cyclus
   - Max 7 dagen tussen rustdagen (RX/CX)
   - Max 7 opeenvolgende werkdagen

4. **Context Data**
   - Verlofaanvragen met approval workflow
   - Feestdagen (vast en variabel)
   - Shift codes met tijdsduur parsing
   - Werkposten met eigenschappen (telt_als_werkdag, reset_12u_rust, etc.)

## Architectuur - 3 Niveaus

### Niveau 1: Regel-gebaseerd (Foundation Layer)

**Doel:** Genereer basis planning vanuit typetabel

```python
# services/planning_generator.py
class PlanningGenerator:
    """
    Genereert basis planning door typetabel te 'uitrollen' over periode
    """

    def genereer_vanuit_typetabel(
        self,
        versie_id: int,
        start_datum: date,
        eind_datum: date
    ) -> List[PlanningRegel]:
        """
        Stappen:
        1. Haal actieve typetabel + data op
        2. Haal alle actieve gebruikers op
        3. Loop door elke datum in periode
        4. Bereken week_nummer obv datum en typetabel lengte
        5. Pas startweek_typedienst per gebruiker toe
        6. Haal shift_type uit typetabel_data
        7. Converteer shift_type naar shift_code
        8. Check beschikbaarheid (verlof/feestdagen)
        9. Return planning regels
        """
        pass
```

**Features:**
- Automatisch vertalen typetabel naar daadwerkelijke planning
- Respecteert gebruiker offsets
- Blokkeert goedgekeurd verlof
- Markeert feestdagen
- Gegenereerde status: `gegenereerd_door = 'typetabel'`

**Tijdsinvestering:** 2-3 dagen

---

### Niveau 2: Constraint Satisfaction (Validation & Optimization)

**Doel:** Valideer en optimaliseer planning obv HR-regels

```python
# services/constraint_validator.py
class ConstraintValidator:
    """
    Valideert planning tegen alle HR regels en constraints
    """

    def validate_planning(
        self,
        planning: List[PlanningRegel],
        periode: Optional[DateRange] = None
    ) -> ValidationResult:
        """
        Checks:
        - 12u rust tussen shifts (check eindtijd shift N vs starttijd shift N+1)
        - Max uren per week (som shift durations per ISO week)
        - Max werkdagen per rode lijn cyclus
        - Max dagen tussen RX/CX codes
        - Max opeenvolgende werkdagen

        Returns:
        - List[Violation] met severity (ERROR/WARNING/INFO)
        - Per gebruiker, per datum
        - Suggested fixes waar mogelijk
        """
        pass

    def get_violations_summary(self) -> Dict[str, int]:
        """Aantal violations per type voor dashboard"""
        pass
```

```python
# services/planning_optimizer.py
from ortools.sat.python import cp_model

class PlanningOptimizer:
    """
    CSP solver voor intelligente planning optimalisatie
    """

    def optimize_planning(
        self,
        basis_planning: List[PlanningRegel],
        constraints: List[Constraint],
        preferences: Optional[Dict] = None
    ) -> OptimizedPlanning:
        """
        Gebruikt Google OR-Tools CP-SAT solver

        Variabelen:
        - (gebruiker, datum) → shift_code

        Harde Constraints:
        - HR regels (uit database)
        - Verlof en beschikbaarheid
        - Minimale bezetting per shift type
        - Competenties per werkpost

        Zachte Constraints (preferences):
        - Eerlijke verdeling zware shifts
        - Spreiding van weekend shifts
        - Voorkeur shifts per gebruiker
        - Team samenstelling (ervaren + junior mix)

        Doelfunctie:
        - Minimaliseer constraint violations
        - Maximaliseer fairness score
        - Minimaliseer afwijking van typetabel
        """
        pass

    def find_alternative_solutions(
        self,
        violation: Violation,
        max_alternatives: int = 3
    ) -> List[Alternative]:
        """Genereer alternatieve shift toewijzingen voor probleem"""
        pass
```

**Features:**
- Real-time validatie tijdens editing
- Auto-suggest fixes voor violations
- Multi-criteria optimalisatie
- Alternatieve oplossingen genereren
- Fairness monitoring

**Dependencies:**
```bash
pip install ortools  # Google's Constraint Programming solver
```

**Tijdsinvestering:** 3-5 dagen

---

### Niveau 3: Machine Learning (Advanced - Optioneel)

**Doel:** Leren van historische data voor betere voorspellingen

```python
# services/planning_ml_advisor.py
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

class PlanningMLAdvisor:
    """
    ML-model getraind op historische planningen
    Geeft aanbevelingen en voorspellingen
    """

    def train_on_history(
        self,
        historical_planning: pd.DataFrame,
        min_months: int = 6
    ):
        """
        Leer patronen uit minstens 6 maanden productie data

        Features:
        - Dag van de week, maand, seizoen
        - Typetabel week/dag
        - Gebruiker eigenschappen (seniority, voorkeuren)
        - Team samenstelling die dag
        - Historische violations op deze dag-combinaties

        Targets:
        - Kans op success voor shift combinatie
        - Predicted workload/stress level
        - Waarschijnlijkheid van ruil verzoek
        """
        pass

    def suggest_improvements(
        self,
        current_planning: List[PlanningRegel]
    ) -> List[Suggestion]:
        """
        Aanbevelingen op basis van geleerde patronen:
        - "Team X en Y werken goed samen op late shifts"
        - "Gebruiker Z heeft vaak ruil op vrijdag nacht"
        - "Deze combinatie gaf vaak 12u rust violations"
        """
        pass

    def predict_workload(
        self,
        date_range: DateRange
    ) -> Dict[date, float]:
        """Voorspel verwachte werkdruk per dag (0.0-1.0)"""
        pass
```

**Use Cases:**
- Aanbevelingen voor team samenstelling
- Voorspel probleempunten voordat ze gebeuren
- Leer van ruil-patronen
- Seizoens- en trendanalyse

**Dependencies:**
```bash
pip install scikit-learn pandas numpy
```

**Tijdsinvestering:** 5-7 dagen (na 6+ maanden productie data)

**Opmerking:** Dit niveau is NIET essentieel voor v1.0. Alleen implementeren als er genoeg historische data is en de ROI duidelijk is.

---

## Implementatie Roadmap

### Quick Win: Simpele Generator (Week 1)

Start met een basis implementatie zonder externe dependencies:

```python
# services/simple_planning_generator.py
def genereer_basis_planning(versie_id: int, jaar: int, maand: int):
    """
    Simpele typetabel expander - geen AI, gewoon patroon volgen

    Algoritme:
    1. Haal actieve typetabel versie + data op
    2. Haal alle actieve gebruikers (excl. admin) + startweek op
    3. Loop door alle dagen in maand
    4. Voor elke gebruiker:
       a. Bereken welke dag sinds typetabel.actief_vanaf
       b. Bereken week_nummer = (dagen_sinds // 7) % aantal_weken + 1
       c. Pas startweek_typedienst toe als offset
       d. Bereken dag_nummer = dagen_sinds % 7 + 1 (1=ma, 7=zo)
       e. Lookup shift_type in typetabel_data
       f. Converteer naar shift_code
       g. Check of datum = goedgekeurd verlof → skip of 'verlof' code
       h. Check of datum = feestdag → special handling
    5. Bulk insert in planning tabel
    6. Return aantal regels + warnings

    Deze functie maakt GEEN optimalisaties, volgt gewoon typetabel.
    Violations worden apart gedetecteerd door ConstraintValidator.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Implementatie hier...

    return {
        'regels_aangemaakt': count,
        'warnings': [],
        'verlof_geblokkeerd': verlof_count
    }
```

**Test Cases:**
```python
# tests/test_planning_generator.py
def test_genereer_basis_1_week_cyclus():
    """Test met simpele 1-week typetabel, 2 gebruikers"""
    pass

def test_genereer_met_verlof():
    """Test dat goedgekeurd verlof shift blokkeert"""
    pass

def test_startweek_offset():
    """Test dat startweek_typedienst correct offset geeft"""
    pass

def test_feestdag_handling():
    """Test feestdag logica"""
    pass
```

### Fase 1: Typetabel Expander (Week 1-2)

**Deliverables:**
- `services/planning_generator.py` - Volledige Niveau 1 implementatie
- Unit tests met 80%+ coverage
- Database migrations voor metadata kolommen (optioneel)
- Logging en error handling

**Database wijzigingen (optioneel):**
```sql
-- Voeg metadata toe aan planning tabel
ALTER TABLE planning ADD COLUMN gegenereerd_door TEXT
    CHECK(gegenereerd_door IN ('manual', 'typetabel', 'ai_optimizer'));

ALTER TABLE planning ADD COLUMN confidence_score REAL
    CHECK(confidence_score BETWEEN 0.0 AND 1.0);

ALTER TABLE planning ADD COLUMN alternatieve_opties TEXT; -- JSON array

ALTER TABLE planning ADD COLUMN laatst_gewijzigd_door INTEGER
    REFERENCES gebruikers(id);

CREATE INDEX idx_planning_gegenereerd ON planning(gegenereerd_door);
```

### Fase 2: Constraint Validator (Week 2-3)

**Deliverables:**
- `services/constraint_validator.py`
- `services/hr_rules_engine.py` - Dynamic rule loading from database
- `models/validation_result.py` - Data classes voor violations
- Integration in Planning Editor scherm (visuele feedback)

**Validation Types:**
```python
@dataclass
class Violation:
    type: str  # 'rust_12u', 'max_uren_week', etc.
    severity: str  # 'ERROR', 'WARNING', 'INFO'
    gebruiker_id: int
    datum: date
    message: str
    suggested_fix: Optional[str]

@dataclass
class ValidationResult:
    is_valid: bool
    violations: List[Violation]
    warnings: List[Violation]
    info: List[Violation]

    def get_by_user(self, user_id: int) -> List[Violation]:
        pass

    def get_by_severity(self, severity: str) -> List[Violation]:
        pass
```

### Fase 3: CSP Optimizer (Week 4-5)

**Deliverables:**
- `services/planning_optimizer.py` met OR-Tools integration
- `services/constraint_mapper.py` - Convert HR regels naar CP constraints
- GUI: "Optimaliseer Planning" knop in Planning Editor
- Performance benchmarking (max 30 sec voor maand planning)

**OR-Tools Example:**
```python
from ortools.sat.python import cp_model

def optimize_month_planning(year: int, month: int):
    model = cp_model.CpModel()

    # Variabelen: (user, day, shift) -> boolean
    assignments = {}
    for user in users:
        for day in days:
            for shift in shifts:
                assignments[(user, day, shift)] = model.NewBoolVar(
                    f'u{user}_d{day}_s{shift}'
                )

    # Constraint: Elke gebruiker max 1 shift per dag
    for user in users:
        for day in days:
            model.Add(sum(assignments[(user, day, s)] for s in shifts) <= 1)

    # Constraint: 12u rust
    for user in users:
        for day in range(len(days) - 1):
            # Als shift vandaag EN shift morgen, dan check tijden
            # Implementatie complex - vereist shift tijden lookup
            pass

    # Doelfunctie: Minimize violations weighted by severity
    model.Minimize(...)

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # Extract solution
        return optimized_planning
    else:
        return None  # No solution found
```

### Fase 4: GUI Integration (Week 5-6)

**Nieuwe Schermen:**

```python
# gui/screens/ai_planning_generator_screen.py
class AIPlanningGeneratorScreen(QWidget):
    """
    Wizard-achtige interface voor AI planning generatie

    Stap 1: Selectie
    - Kies typetabel versie (dropdown)
    - Kies periode (maand/kwartaal/jaar)
    - Kies modus: "Basis" / "Geoptimaliseerd"

    Stap 2: Preview
    - Toon aantal te genereren regels
    - Toon bestaande planning (overschrijf waarschuwing)
    - Preview eerste week als voorbeeld

    Stap 3: Validatie
    - Run constraint validator
    - Toon violations in tabel (severity, gebruiker, datum, type)
    - "Doorgaan ondanks warnings" checkbox

    Stap 4: Generatie
    - Progress bar
    - "Genereer" knop
    - Na generatie: toon samenvatting
    - Knop: "Bekijk in Planning Editor"

    Indien Geoptimaliseerd:
    - Extra stap: OR-Tools solver settings
    - Keuze: welke constraints zijn hard/soft
    - Weight sliders voor optimalisatie doelen
    """
    pass
```

**Dashboard Menu Item:**
```python
# In gui/screens/dashboard_screen.py
# Tab: "Planning Tools" (Admin/Planner)
scroll_layout.addWidget(self.create_menu_button(
    "AI Planning Generator",
    "Genereer planning automatisch vanuit typetabel"
))
```

**Planning Editor Integratie:**
```python
# Toevoegen aan gui/screens/planning_editor_screen.py
# Toolbar buttons:
# - "Genereer Maand" -> Quick generate current month
# - "Valideer" -> Run validator, toon violations
# - "Optimaliseer" -> Run CSP solver op geselecteerde periode

# Visual feedback in grid:
# - Violations: rode border
# - Warnings: oranje border
# - AI-gegenereerd: licht blauwe achtergrond
# - Manual edit: standaard wit
```

---

## Technische Specificaties

### Dependencies

```requirements.txt
# Core
PyQt6>=6.6.0
bcrypt>=4.1.0

# AI Planning (nieuwe requirements)
ortools>=9.8.0        # Google's Constraint Programming solver
numpy>=1.24.0         # Numerieke berekeningen
python-dateutil>=2.8  # Datum utilities

# Optioneel voor Niveau 3 (ML)
# scikit-learn>=1.3.0
# pandas>=2.0.0
```

### Performance Targets

| Operatie | Max Tijd | Notities |
|----------|----------|----------|
| Genereer 1 maand (30 users) | 2 sec | Niveau 1: Typetabel expander |
| Valideer 1 maand | 5 sec | Niveau 2: Constraint checks |
| Optimaliseer 1 maand | 30 sec | Niveau 2: CSP solver |
| Genereer 1 jaar (30 users) | 20 sec | Bulk operatie |

### Database Schema Updates

```sql
-- Nieuwe tabel: AI configuratie
CREATE TABLE IF NOT EXISTS ai_planning_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT UNIQUE NOT NULL,
    beschrijving TEXT,
    optimizer_mode TEXT CHECK(optimizer_mode IN ('basic', 'advanced')),
    max_solve_tijd_sec INTEGER DEFAULT 30,
    soft_constraints TEXT,  -- JSON
    weights TEXT,           -- JSON
    is_actief BOOLEAN DEFAULT 1,
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Nieuwe tabel: Generatie historiek (audit trail)
CREATE TABLE IF NOT EXISTS planning_generatie_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uitgevoerd_door INTEGER NOT NULL,
    typetabel_versie_id INTEGER NOT NULL,
    start_datum DATE NOT NULL,
    eind_datum DATE NOT NULL,
    generatie_type TEXT NOT NULL,  -- 'basic', 'optimized'
    aantal_regels INTEGER,
    violations_count INTEGER,
    solve_tijd_sec REAL,
    uitgevoerd_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uitgevoerd_door) REFERENCES gebruikers(id),
    FOREIGN KEY (typetabel_versie_id) REFERENCES typetabel_versies(id)
);

-- Index voor audit queries
CREATE INDEX idx_generatie_log_datum
ON planning_generatie_log(uitgevoerd_op);
```

---

## Ontwerpkeuzes & Trade-offs

### Waarom OR-Tools (niet custom algoritme)?

**Voordelen:**
- Battle-tested door Google (gebruikt in Google Maps routing)
- Snelle C++ core met Python bindings
- Excellent CP-SAT solver voor scheduling problemen
- Gratis en open source
- Goede documentatie + voorbeelden

**Nadelen:**
- Extra dependency (15-20 MB)
- Leercurve voor CP modellering
- Overkill voor simpele use cases

**Alternatief:** Python-constraint library (simpeler, maar trager)

### Waarom geen ML in v1.0?

**Redenen:**
- Geen historische data beschikbaar (nieuw systeem)
- ML vereist 6+ maanden training data
- Niveau 1+2 dekken al 90% van de use cases
- Beter om solide basis te bouwen eerst

**Wanneer WEL ML:**
- Na 1 jaar productie gebruik
- Als er patronen zijn die regels niet vangen
- Voor voorspellingen (workload, ruil kans, etc.)

### Soft vs Hard Constraints

**Hard Constraints (MOET gerespecteerd worden):**
- 12u rust tussen shifts (veiligheid)
- Max 50u/week (wettelijk)
- Goedgekeurd verlof (contractueel)
- Feestdagen zondagsrust

**Soft Constraints (LIEFST gerespecteerd, mag wijken):**
- Eerlijke verdeling zware shifts
- Voorkeur vroege/late shifts
- Weekend spreiding
- Typetabel adherence (bij optimalisatie)

CSP Solver kan weights toekennen aan soft constraints.

---

## Testing Strategie

### Unit Tests

```python
# tests/test_planning_generator.py
class TestPlanningGenerator:
    def test_genereer_1_week_cyclus_2_users(self):
        """Simpelste geval: 1 week patroon, 2 gebruikers"""

    def test_genereer_6_week_cyclus_offset(self):
        """Test startweek_typedienst offset werkt correct"""

    def test_verlof_blokkeert_generatie(self):
        """Goedgekeurd verlof moet shift blokkeren"""

    def test_feestdag_override(self):
        """Feestdagen krijgen speciale behandeling"""

# tests/test_constraint_validator.py
class TestConstraintValidator:
    def test_12u_rust_violation(self):
        """Detecteer te weinig rust tussen shifts"""

    def test_max_uren_week_violation(self):
        """Detecteer > 50u in 1 week"""

    def test_geen_violations_perfecte_planning(self):
        """Valide planning moet geen errors geven"""

# tests/test_planning_optimizer.py
class TestPlanningOptimizer:
    def test_optimize_fixes_12u_rust(self):
        """Optimizer moet 12u rust violations kunnen fixen"""

    def test_optimize_respects_verlof(self):
        """Optimizer mag geen verlof overschrijven"""

    def test_optimize_timeout(self):
        """Test dat solver stopt na max_time"""
```

### Integration Tests

```python
# tests/integration/test_full_generation_flow.py
def test_genereer_valideer_optimaliseer_maand():
    """
    End-to-end test:
    1. Maak typetabel versie
    2. Genereer maand planning
    3. Valideer (expect violations)
    4. Optimaliseer
    5. Valideer opnieuw (expect minder violations)
    6. Assert planning in database
    """
    pass
```

### Performance Tests

```python
# tests/performance/test_generation_speed.py
import time

def test_genereer_1_maand_30_users_onder_2_sec():
    start = time.time()
    genereer_basis_planning(versie_id=1, jaar=2025, maand=1)
    elapsed = time.time() - start
    assert elapsed < 2.0, f"Te traag: {elapsed:.2f}s"

def test_optimaliseer_1_week_onder_10_sec():
    # CSP solver performance check
    pass
```

---

## User Stories

### Story 1: Planner genereert maand planning

**Als** planner
**Wil ik** een volledige maand planning kunnen genereren met 1 klik
**Zodat** ik niet handmatig 30 dagen x 30 users = 900 cellen hoef in te vullen

**Acceptance Criteria:**
- [ ] Dashboard heeft menu item "AI Planning Generator"
- [ ] Generator scherm toont beschikbare typetabel versies
- [ ] Ik kan maand selecteren (jaar + maand dropdown)
- [ ] Preview toont aantal te genereren regels
- [ ] "Genereer" knop vult planning tabel
- [ ] Progress feedback tijdens generatie
- [ ] Samenvatting na generatie (X regels, Y warnings)
- [ ] Mogelijkheid om bestaande planning te overschrijven (met waarschuwing)

### Story 2: Planner valideert planning

**Als** planner
**Wil ik** de gegenereerde planning kunnen valideren
**Zodat** ik weet of er HR regel violations zijn

**Acceptance Criteria:**
- [ ] Planning Editor heeft "Valideer" knop
- [ ] Validatie toont lijst van violations per type
- [ ] Violations zijn gekleurd per severity (rood/oranje/blauw)
- [ ] Ik kan filteren op gebruiker
- [ ] Ik kan filteren op violation type
- [ ] Per violation zie ik suggested fix
- [ ] Violations zijn visueel in grid (rode border om cel)

### Story 3: Planner optimaliseert probleem planning

**Als** planner
**Wil ik** een planning met violations automatisch kunnen laten verbeteren
**Zodat** ik niet handmatig alle conflicts hoef op te lossen

**Acceptance Criteria:**
- [ ] Planning Editor heeft "Optimaliseer" knop
- [ ] Optimizer runt alleen op geselecteerde periode (niet hele jaar)
- [ ] Optimizer toont voortgang (% done)
- [ ] Na optimize: diff view (was → wordt)
- [ ] Ik kan changes accepteren of verwerpen
- [ ] Optimizer respecteert verlof en feestdagen (hard constraints)
- [ ] Optimizer stopt na max 30 seconden

### Story 4: Planner vergelijkt alternatieven

**Als** planner
**Wil ik** alternatieve oplossingen kunnen zien voor een conflict
**Zodat** ik de beste keuze kan maken voor het team

**Acceptance Criteria:**
- [ ] Bij violation zie ik "Toon alternatieven" link
- [ ] Dialog toont 2-3 alternatieve shift combinaties
- [ ] Per alternatief zie ik impact (welke andere shifts veranderen)
- [ ] Ik kan alternatief toepassen met 1 klik
- [ ] Planning wordt live bijgewerkt

---

## Configuratie & Settings

### AI Planning Settings Scherm

```python
# gui/screens/ai_planning_settings_screen.py
class AIPlanningSettingsScreen(QWidget):
    """
    Configuratie voor AI planning generator

    Tabbladen:

    1. Algemeen
       - Default optimizer mode (basic/advanced)
       - Max solve tijd (10-60 sec slider)
       - Auto-validatie na generatie (checkbox)

    2. Hard Constraints
       - Lijst van HR regels (uit database)
       - Toggle: hard/soft per regel
       - Niet editeerbaar: 12u rust, verlof (altijd hard)

    3. Soft Constraints & Weights
       - Eerlijke verdeling zware shifts (weight 0-10)
       - Weekend spreiding (weight 0-10)
       - Voorkeur shifts respecteren (weight 0-10)
       - Typetabel adherence (weight 0-10)

    4. Geavanceerd
       - Min bezetting per shift type
       - Max afwijking van typetabel (%)
       - Reserve pool gebruiken bij tekort (checkbox)
    """
    pass
```

**Opslag in database:**
```python
# Opgeslagen in ai_planning_config tabel
# JSON format voor complexe settings:
{
    "soft_constraints": {
        "fair_distribution": {"enabled": true, "weight": 8},
        "weekend_spread": {"enabled": true, "weight": 6},
        "preference_matching": {"enabled": false, "weight": 0},
        "typetabel_adherence": {"enabled": true, "weight": 5}
    },
    "weights": {
        "violation_error": 100,
        "violation_warning": 10,
        "violation_info": 1
    }
}
```

---

## Monitoring & Logging

### Logging Strategy

```python
# services/planning_generator.py
import logging

logger = logging.getLogger('planning_tool.ai')

def genereer_vanuit_typetabel(...):
    logger.info(f"Start generatie: versie_id={versie_id}, periode={start_datum} - {eind_datum}")

    try:
        # Generatie logica
        logger.debug(f"Verwerkt {count} regels voor {user.naam}")

    except Exception as e:
        logger.error(f"Generatie gefaald: {e}", exc_info=True)
        raise

    logger.info(f"Generatie compleet: {total_regels} regels, {warnings} warnings")
```

### Metrics Dashboard (Optioneel)

```python
# gui/widgets/ai_metrics_widget.py
class AIMetricsDashboard(QWidget):
    """
    Toont statistieken over AI planning gebruik

    Metrics:
    - Aantal generaties laatste maand
    - Gemiddelde solve tijd
    - Success rate (% zonder violations)
    - Meest voorkomende violation types
    - Optimizer improvements (violations voor/na)

    Visualisatie:
    - Bar chart: violations per type
    - Line chart: solve tijd over tijd
    - Pie chart: generatie types (basic/optimized)
    """
    pass
```

---

## Migratie Strategie

### Voor bestaande installaties

```python
# migratie_ai_planning.py
"""
Migratie script voor AI Planning features
Versie: v0.6.8 → v0.7.0
"""

def migrate():
    conn = get_connection()
    cursor = conn.cursor()

    # Check of migratie al gedaan is
    cursor.execute("PRAGMA table_info(planning)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'gegenereerd_door' in columns:
        print("AI Planning migratie al uitgevoerd")
        return

    print("Start AI Planning migratie...")

    # Stap 1: Voeg metadata kolommen toe aan planning
    cursor.execute("""
        ALTER TABLE planning
        ADD COLUMN gegenereerd_door TEXT
        CHECK(gegenereerd_door IN ('manual', 'typetabel', 'ai_optimizer'))
    """)

    cursor.execute("""
        ALTER TABLE planning
        ADD COLUMN confidence_score REAL
        CHECK(confidence_score BETWEEN 0.0 AND 1.0)
    """)

    cursor.execute("ALTER TABLE planning ADD COLUMN alternatieve_opties TEXT")

    # Stap 2: Update bestaande planning als 'manual'
    cursor.execute("UPDATE planning SET gegenereerd_door = 'manual' WHERE gegenereerd_door IS NULL")

    # Stap 3: Maak nieuwe tabellen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_planning_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT UNIQUE NOT NULL,
            beschrijving TEXT,
            optimizer_mode TEXT CHECK(optimizer_mode IN ('basic', 'advanced')),
            max_solve_tijd_sec INTEGER DEFAULT 30,
            soft_constraints TEXT,
            weights TEXT,
            is_actief BOOLEAN DEFAULT 1,
            aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS planning_generatie_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uitgevoerd_door INTEGER NOT NULL,
            typetabel_versie_id INTEGER NOT NULL,
            start_datum DATE NOT NULL,
            eind_datum DATE NOT NULL,
            generatie_type TEXT NOT NULL,
            aantal_regels INTEGER,
            violations_count INTEGER,
            solve_tijd_sec REAL,
            uitgevoerd_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uitgevoerd_door) REFERENCES gebruikers(id),
            FOREIGN KEY (typetabel_versie_id) REFERENCES typetabel_versies(id)
        )
    """)

    # Stap 4: Seed default config
    cursor.execute("""
        INSERT INTO ai_planning_config (naam, beschrijving, optimizer_mode, soft_constraints, weights)
        VALUES (
            'Standaard',
            'Standaard AI planning configuratie',
            'basic',
            '{"fair_distribution": {"enabled": true, "weight": 8}}',
            '{"violation_error": 100, "violation_warning": 10}'
        )
    """)

    # Stap 5: Indices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_planning_gegenereerd ON planning(gegenereerd_door)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_generatie_log_datum ON planning_generatie_log(uitgevoerd_op)")

    conn.commit()
    print("AI Planning migratie succesvol!")

if __name__ == '__main__':
    migrate()
```

---

## Veelgestelde Vragen (FAQ)

### Q: Kan de AI elke mogelijke planning oplossen?

**A:** Nee. Sommige constraint combinaties zijn wiskundig onoplosbaar (over-constrained problem). De CSP solver zal dit detecteren en rapporteren. In dat geval moet de planner:
- Constraints versoepelen (bv. toestaan 11u rust ipv 12u voor specifieke dag)
- Extra personeel inzetten (reserves)
- Typetabel aanpassen

### Q: Hoe lang duurt optimalisatie?

**A:**
- Basic generatie (Niveau 1): 1-2 seconden voor 1 maand
- Validatie (Niveau 2): 2-5 seconden
- CSP Optimalisatie (Niveau 2): 10-30 seconden afhankelijk van complexiteit
- We gebruiken een timeout van 30 sec, daarna geeft solver beste oplossing tot nu toe

### Q: Overschrijft de generator handmatige wijzigingen?

**A:** Alleen als je dat expliciet toestaat. Standaard:
- Waarschuwing als er al planning bestaat
- Optie: "Alleen lege cellen vullen"
- Optie: "Overschrijf alles (behalve goedgekeurd verlof)"
- Handmatige edits hebben altijd prioriteit bij re-generatie

### Q: Kan ik de AI resultaten vertrouwen?

**A:**
- Niveau 1 (typetabel expander) is 100% deterministisch - geen black box
- Niveau 2 (CSP solver) is wiskundig bewezen correct voor gegeven constraints
- Niveau 3 (ML) zou probabilistisch zijn - gebruik alleen als "suggestie"
- ALTIJD validatie draaien na generatie
- Planner heeft final review before publiceren

### Q: Wat als een gebruiker speciale voorkeuren heeft?

**A:** Toekomstige uitbreiding (na v0.7):
```sql
CREATE TABLE gebruiker_voorkeuren (
    id INTEGER PRIMARY KEY,
    gebruiker_id INTEGER,
    voorkeur_type TEXT,  -- 'shift_type', 'dag_van_week', 'nooit_combinatie'
    waarde TEXT,         -- JSON
    priority INTEGER,
    FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id)
);
```

Deze voorkeuren worden dan soft constraints in de optimizer.

### Q: Hoe test ik de AI generator veilig?

**A:**
1. Gebruik test database (kopieer productie DB)
2. Genereer in nieuwe "test" periode (ver in toekomst)
3. Status blijft 'concept' tot je publiceert
4. Rollback functie: verwijder alle planning met `gegenereerd_door = 'ai_optimizer'` voor datum range

---

## Risico's & Mitigatie

| Risico | Impact | Kans | Mitigatie |
|--------|--------|------|-----------|
| OR-Tools installeert niet op Windows | Hoog | Laag | Fallback naar python-constraint, of pre-compiled wheels |
| CSP solver vindt geen oplossing | Gemiddeld | Gemiddeld | Duidelijke error messages, suggest constraint relaxation |
| Performance te traag op grote datasets | Gemiddeld | Laag | Batch processing, incrementele optimalisatie |
| Gebruikers vertrouwen AI niet | Hoog | Gemiddeld | Transparantie (toon waarom beslissingen), always allow manual override |
| Bug in generator corrupt planning | Hoog | Laag | Extensive testing, staging environment, rollback mechanisme |

---

## Succes Metrics

Meet succes van AI Planning Generator aan:

1. **Adoptie**
   - % planningen gegenereerd met AI vs handmatig
   - Target: >70% van maandplanningen gebruikt AI generator

2. **Efficiency**
   - Tijd bespaard per maand planning
   - Target: van 4u handmatig naar 30min (review + tweaks)

3. **Kwaliteit**
   - % planningen zonder violations na eerste generatie
   - Target: >60% clean, >90% na optimalisatie

4. **Tevredenheid**
   - Planner survey: "AI generator helpt mijn werk"
   - Target: >4/5 sterren

5. **Performance**
   - Gemiddelde solve tijd
   - Target: <10 sec voor 1 maand

---

## Conclusie & Volgende Stappen

De AI Planning Generator is een **zeer haalbare** uitbreiding op het huidige systeem. De architectuur is er al klaar voor, en de business value is duidelijk: massive tijdsbesparing voor planners.

### Aanbevolen Aanpak

**v0.7.0 (Q1 2026):**
- Niveau 1: Typetabel Expander (simpel maar nuttig)
- Niveau 2a: Constraint Validator (essentieel voor kwaliteit)

**v0.8.0 (Q2 2026):**
- Niveau 2b: CSP Optimizer (echte AI power)
- GUI integration

**v0.9.0+ (Q3 2026):**
- Niveau 3: ML Advisor (optioneel, alleen als data beschikbaar)
- Geavanceerde features (voorkeuren, team matching, etc.)

### Start Simpel, Itereer Snel

Begin met de **Quick Win** implementatie (1 week):
- Basis typetabel expander zonder dependencies
- Bewijs de waarde
- Verzamel feedback
- Investeer dan in geavanceerdere features

---

**Document versie:** 1.0
**Laatst bijgewerkt:** 2025-10-19
**Status:** PLANNING - Nog niet geïmplementeerd
**Geschatte effort:** 4-6 weken (afhankelijk van scope)
