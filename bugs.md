# Known Bugs and Issues

Deze file tracked alle bekende bugs en issues in de Planning Tool applicatie.

## Fixed Bugs

### BUG-004: Dubbele Shift in validate_shift() Veroorzaakt Incorrecte Uren Telling
**Status:** FIXED (2025-11-03)
**Versie:** v0.6.26
**Severity:** HIGH

**Probleem:**
Bij cel focus op een bestaande shift toonde de info box een incorrecte "Te veel uren" violation. Bijvoorbeeld: "Te veel uren: 56.0u in week (maximaal 50u)" terwijl de werkelijke uren 48u waren.

**User Scenario:**
1. Bob Aerts heeft planning: di 5/11 t/m ma 11/11 (7 dagen @ 8u = 56u totaal)
2. Deze 7 dagen vallen in 2 kalender weken:
   - Week 45 (ma 4 - zo 10): 6 werkdagen = 48u ✅ OK
   - Week 46 (ma 11 - zo 17): 1 werkdag = 8u ✅ OK
3. Open Planning Editor → geen violations (correct)
4. Klik op cel 5 nov → info box toont "56u in week" ❌ FOUT!
5. Klik "Valideer Planning" knop → violations verdwijnen ✅ correct
6. Klik terug op cel 5 nov → violation verschijnt weer ❌ FOUT!

**Root Cause:**
`validate_shift()` method in `services/planning_validator_service.py` (line 396-434):

```python
# VOOR FIX (line 411-421):
planning = self._get_planning_data()  # Laadt planning uit DB (incl. 5 nov)

# Add de nieuwe shift tijdelijk (voor preview)
planning.append(PlanningRegel(
    gebruiker_id=self.gebruiker_id,
    datum=datum,              # ❌ 5 nov AL in planning!
    shift_code=shift_code,
    ...
))
```

**Probleem:**
- Planning data bevat al 5 nov met '1101' uit database
- validate_shift() voegt NOGMAALS 5 nov met '1101' toe
- Geen duplicate check!
- Resultaat: planning bevat 5 nov DUBBEL
- Week 45: 6 unieke dagen + 1 dubbele dag = 7 shifts @ 8u = **56u**

**Debug Output (voor fix):**
```
Planning data:
  2024-11-05: 1101
  2024-11-05: 1101  ← DUBBEL!
  ...
Week 45: 56.0u → VIOLATION
```

**Fix:**
Filter bestaande shift voor datum VOORDAT nieuwe wordt toegevoegd (line 414-416):

```python
# NA FIX (v0.6.26 - BUG-004):
planning = self._get_planning_data()

# CRITICAL FIX: Verwijder bestaande shift voor deze datum
planning = [p for p in planning if p.datum != datum]  # ✅ Remove duplicates

# Add de nieuwe shift tijdelijk
planning.append(PlanningRegel(
    gebruiker_id=self.gebruiker_id,
    datum=datum,
    shift_code=shift_code,
    ...
))
```

**Code Changes:**
- File: `services/planning_validator_service.py`
- Method: `validate_shift()` (line 396-434)
- Change: Line 414-416 toegevoegd (filter planning op datum)
- Comment: "CRITICAL FIX (v0.6.26 - BUG-004)"

**Test Results:**
Getest met `scripts/debug_cel_focus.py`:
- **Voor fix:** 17 planning regels, 5 nov dubbel → "56.0u" violation ❌
- **Na fix:** 16 planning regels, 5 nov enkelvoudig → GEEN violations ✅

**Impact:**
- ✅ Real-time validatie nu correct bij cel focus op bestaande shifts
- ✅ Info box toont juiste uren telling (48u ipv 56u)
- ✅ Consistentie tussen cel validatie en batch validatie
- ✅ Alle HR uren checks nu betrouwbaar

**Gerelateerd:**
- Dezelfde bug trof ook 12u rust check (dubbele shifts → verkeerde rust berekening)
- Fix lost beide checks op (uren per week + 12u rust)

---

### ISSUE-007: Real-time HR Validation - Irritante Popups en Ghost Violations
**Status:** FIXED (2025-11-04)
**Versie:** v0.6.26
**Severity:** HIGH

**Probleem 1: Irritante Popup bij Elke Edit**
Bij elke shift wijziging verscheen een QMessageBox met HR violations. Dit was zeer irritant wanneer je meerdere cellen moest aanpassen om een violation op te lossen.

**User Scenario:**
"Ik heb een violation op 9 november. Om die te kunnen fiksen moet ik voorgaande dagen/week aanpassen. Bij elke edit die ik doe, krijg ik steeds die foutmelding die ik moet wegklikken."

**Probleem 2: Ghost Violations in Voorgaande Week**
Real-time validation toonde violations op verkeerde datums:
- Violation op 9/11 (late na nacht op 8/11)
- Week ervoor toonde ook fouten
- Na "Valideer Planning" klik verdwenen die fouten

**Root Cause:**
1. **Popup:** `show_hr_violation_warning()` werd aangeroepen na elke `save_shift()` (line 2040)
2. **Ghost violations:** `update_hr_violations_voor_gebruiker()` gebruikte `validate_shift()` die violations retourneert voor meerdere datums (bijv. 8/11 én 9/11 bij 12u rust check), maar deze werden ALLEEN in cache gezet voor de geëdite datum (9/11). Dit veroorzaakte verkeerde violation overlays.

**Verschil validate_shift() vs validate_all():**
- `validate_shift()`: Snelle real-time check (alleen 12u rust + 50u week)
  - Kan violations geven voor meerdere datums (vorige dag, huidige dag, volgende dag, hele week)
  - Datum mapping probleem in cache update
- `validate_all()`: Accurate batch check (alle 6 HR checks)
  - Correcte datum mapping per violation
  - Gebruikt in "Valideer Planning" knop

**Fix:**
Real-time validation volledig uitgeschakeld - gebruiker moet "Valideer Planning" knop gebruiken:

**Code Changes:**
- File: `gui/widgets/planner_grid_kalender.py`
- Line 2035-2043: Commented out real-time validation in `save_shift()`
  ```python
  # DISABLED (v0.6.26 - USER FEEDBACK):
  # Real-time validation is te irritant (popup bij elke edit)
  # Ghost violations door verkeerde datum mapping
  # Gebruiker moet "Valideer Planning" knop gebruiken
  ```
- Line 2097-2101: Commented out validation clear in `delete_shift()`
- Line 15-21: Updated version header (real-time validation DISABLED)

**Impact:**
- ✅ Geen irritante popup meer bij elke cel edit
- ✅ Geen ghost violations op verkeerde datums
- ✅ Gebruiker kan rustig planning invullen zonder interruptions
- ✅ "Valideer Planning" knop + HR summary box geven accurate feedback
- ✅ Consistentie tussen overlay en summary (beide gebruiken validate_all)

**Trade-off:**
- ⚠ Geen instant feedback bij cel wijziging
- ✅ Maar: gebruiker moet expliciet valideren via knop (bewuste actie)

**User Feedback:**
"Verwijder die foutmelding. We hebben de validatieknop, en onze violation summary box. Foutmelding moet komen na een klik op de validatieknop en dan verwijzen naar de summary box."

**Gerelateerd:**
- HR Validatie Systeem v0.6.26 (Fase 3 - UI Integration)

---

### ISSUE-006: HR Violations Summary Box - Autohide, Scroll en Limits
**Status:** FIXED (2025-11-04)
**Versie:** v0.6.26
**Severity:** LOW

**Probleem:**
De HR violations summary box onderaan de Planning Editor had vier usability problemen:
1. Box werd verborgen (autohide) wanneer geen violations aanwezig
2. Tekst werd afgekapt zonder scroll mogelijkheid
3. Geen manier om door lange violation lijsten te scrollen
4. Max 5 gebruikers en max 5 violations per gebruiker (incomplete overzicht)

**User Feedback:**
"ik zag een autohide bij de violation summary box. Eigenlijk mag die er altijd staan. Zijn er geen violations, blijft die leeg. Verder staat er in bugs.md, issue 006 ook nog zaken over de violation summary box."
"summary box moet alle fouten geven, dus niet enkel de top 5"

**Root Cause:**
Implementatie gebruikte simpele QLabel met hide()/show() en hard limits:
- Line 330: `self.hr_summary_label.hide()` bij initialisatie
- Line 886: `self.hr_summary_label.hide()` wanneer geen violations
- Geen scroll container, dus lange teksten werden afgeknipt
- Line 917: `max_gebruikers = 5` - Toonde max 5 gebruikers
- Line 955: `max_violations_per_user = 5` - Toonde max 5 violations per gebruiker

**Fix:**
QLabel gewrapped in QScrollArea + alle limits verwijderd:

**Code Changes:**
- File: `gui/widgets/planner_grid_kalender.py`
- Lines 315-338: HR summary box setup
  - QLabel wrapped in QScrollArea
  - `setMaximumHeight(200)` voor scroll activatie bij lange content
  - Default tekst: "Geen HR violations gevonden"
  - Verwijderd: alle hide() calls
- Line 893: `setText()` ipv `hide()` bij geen violations
- Line 915-963: Verwijderd: max_gebruikers en max_violations_per_user limits
  - Toont nu ALLE gebruikers met violations
  - Toont nu ALLE violations per gebruiker
  - Beschrijving niet meer getruncate (volledige tekst)

**Nieuwe Implementatie:**
```python
# ScrollArea wrapper (altijd zichtbaar)
self.hr_summary_scroll = QScrollArea()
self.hr_summary_scroll.setWidgetResizable(True)
self.hr_summary_scroll.setMaximumHeight(200)  # Max hoogte voor scroll
self.hr_summary_scroll.setFrameShape(QScrollArea.Shape.NoFrame)

self.hr_summary_label = QLabel()
# ... styling ...
self.hr_summary_label.setText("Geen HR violations gevonden")  # Default

self.hr_summary_scroll.setWidget(self.hr_summary_label)
layout.addWidget(self.hr_summary_scroll)

# Update logica:
if not violations_per_gebruiker:
    self.hr_summary_label.setText("<i>Geen HR violations gevonden</i>")
    return  # Geen hide() meer!
```

**Impact:**
- ✅ Box altijd zichtbaar (consistent UI, geen verrassingen)
- ✅ Scroll functionaliteit bij lange violation lijsten (>200px)
- ✅ Duidelijke "geen violations" message ipv lege ruimte
- ✅ Volledig overzicht: ALLE gebruikers + ALLE violations (geen limits)
- ✅ Volledige beschrijvingen (geen truncate meer)
- ✅ Betere UX: gebruiker weet altijd dat validatie actief is

**Gerelateerd:**
- HR Validatie Systeem v0.6.26 (Fase 3 - UI Integration)

---

### BUG-003: RX vs CX Onderscheid in Max Dagen Tussen RX Regel
**Status:** FIXED (2025-11-03)
**Versie:** v0.6.26
**Severity:** HIGH

**Probleem:**
De constraint checker behandelde RX en CX identiek voor de "max 7 dagen tussen rustdagen" regel. Beide codes hadden `reset_12u_rust = True`, dus beide werden beschouwd als "rustdag" die de counter reset.

**User Scenario:**
1. Gebruiker plant: RX op 4/11, CX op 11/11, RX op 16/11
2. Gap tussen RX codes: 11 dagen (4/11 → 16/11)
3. **BUG:** Geen violation gedetecteerd (want CX op 11/11 reset de counter)
4. **Verwacht:** Violation! CX mag wel rust zijn, maar reset NIET de RX counter

**Business Rule Clarificatie:**
Gebruiker: "er is een verschil tussen rust en RX. Tussen elke RX mag er max 7 dagen zijn. Dan mag ik dit nog opvullen met CX, tenminste elke 8ste dag moet een RX zijn"

**Implicatie:**
- RX = speciale rustdag die verplicht elke 8 dagen moet voorkomen
- CX = compensatiedag, is rustdag voor 12u rust en werkdagen reeks
- Maar CX reset NIET de "dagen tussen RX" counter
- Alleen RX → RX gaps worden gechecked

**Root Cause:**
`check_max_dagen_tussen_rx()` in `services/constraint_checker.py` (line 854-928):
```python
# VOOR FIX (line 887 - FOUT):
if p.shift_code and self._reset_12u_teller(p.shift_code):
    rustdagen.append(p)  # ❌ Catch RX, CX én Z
```

Dit was logisch voor 12u rust regel, maar NIET voor RX gap regel.

**Fix:**
Gewijzigd naar expliciete RX check (line 887-891):
```python
# NA FIX (line 890 - CORRECT):
if p.shift_code == 'RX':
    rx_dagen.append(p)  # ✅ Alleen RX codes
```

**Code Changes:**
- File: `services/constraint_checker.py`
- Method: `check_max_dagen_tussen_rx()` (line 854-928)
- Wijzigingen:
  1. Docstring: "Maximaal 7 dagen tussen twee RX codes" (was: "tussen twee rustdagen")
  2. Business rules sectie uitgebreid met RX vs CX onderscheid
  3. Check: `if p.shift_code == 'RX'` (was: `if self._reset_12u_teller(p.shift_code)`)
  4. Variable naam: `rx_dagen` (was: `rustdagen`)
  5. Beschrijving: "Te lang tussen RX" (was: "tussen rustdagen")
  6. Suggested fix: "CX kan wel als rustdag maar reset niet de RX counter"

**Test Results:**
Getest met `scripts/test_rx_vs_cx.py`:
- ✅ RX elke 8 dagen (6 gap) → OK
- ✅ RX + CX + RX (7 gap) → OK
- ✅ RX + CX + RX (8 gap) → VIOLATION (correct!)
- ✅ Alleen CX, geen RX → OK (geen RX paren om te checken)
- ✅ Bob Aerts scenario (RX 4/11 + CX 11/11 + RX 16/11 = 11 gap) → VIOLATION (correct!)

**Impact:**
- RX gap regel nu correct geïmplementeerd volgens business rules
- CX blijft rustdag voor andere regels (12u rust, werkdagen reeks, weekend reeks)
- Alleen RX → RX gaps worden gechecked voor max 7 dagen regel
- Planning met te lange RX gaps wordt nu correct gedetecteerd

---

### BUG-002: HR Violations Cache Blijft Na Shift Verwijdering
**Status:** FIXED (2025-11-03)
**Versie:** v0.6.26
**Severity:** HIGH

**Probleem:**
Na het verwijderen van een shift blijft de oude HR violation (bijv. "te veel uren per week") zichtbaar in de UI. Gebruiker blijft warnings zien ondanks dat shifts verwijderd zijn uit de database.

**User Scenario:**
1. Gebruiker voegt te veel shifts toe (bijv. 56 uur in één week)
2. Constraint checker toont "Te veel uren: 56u in week (maximaal 50u)"
3. Gebruiker verwijdert shifts om terug te komen naar 48 uur
4. **BUG:** Gebruiker blijft "te veel uren" warning zien
5. Na herstart: Warning is weg (want cache is gereset)

**Root Cause:**
De `delete_shift()` method in `gui/widgets/planner_grid_kalender.py` clearde de HR violations cache NIET na shift verwijdering. Alleen `save_shift()` riep `update_hr_violations_voor_gebruiker()` aan.

**Vergelijking:**
```python
# save_shift() (line 1937) - HAD violations update
self.update_hr_violations_voor_gebruiker(datum_str, gebruiker_id, shift_code)

# delete_shift() (line 1992-1996) - MISTE violations update
self.update_bemannings_status_voor_datum(datum_str)
# ❌ Geen clear van hr_violations cache!
self.data_changed.emit()
```

**Fix:**
Toegevoegd: `clear_hr_violations_voor_gebruiker()` method die:
1. Verwijdert violation entry voor gebruiker+datum uit `self.hr_violations`
2. Update cel styling om oude rode overlay te verwijderen
3. Wordt aangeroepen in `delete_shift()` na database update

**Code Changes:**
- File: `gui/widgets/planner_grid_kalender.py`
- Nieuwe method: `clear_hr_violations_voor_gebruiker()` (line 2124-2151)
- Update: `delete_shift()` roept nu clear aan (line 1995-1997)

**Impact:**
- ✅ HR violations verdwijnen direct na shift verwijdering
- ✅ Geen herstart meer nodig om UI te synchroniseren
- ✅ Voorkomt verwarring bij gebruikers over inconsistente warnings

---

### BUG-001: 12u Rust Check Fout voor Nacht → Vroeg Patronen
**Status:** FIXED (2025-11-03)
**Versie:** v0.6.25
**Severity:** HIGH

**Probleem:**
De constraint checker detecteerde geen violation wanneer een nacht shift (22:00-06:00) direct gevolgd werd door een vroeg shift (06:00-14:00). Dit zou 0 uur rust opleveren, maar de checker berekende dit als 24 uur rust.

**Voorbeeld:**
- Bob Aerts op 2024-11-06: Nacht shift 1301 (22:00-06:00)
- Bob Aerts op 2024-11-07: Vroeg shift 1101 (06:00-14:00)
- Werkelijke rust: 0.0 uur (nacht eindigt 06:00, vroeg begint 06:00)
- Berekende rust (voor fix): 24.0 uur ❌
- Berekende rust (na fix): 0.0 uur ✅

**Root Cause:**
De `_bereken_rust_tussen_shifts` method in `services/constraint_checker.py` had geen kennis van de start_tijd van shift 1, dus kon niet detecteren dat de shift een middernacht crossing had. De eindtijd werd gecombineerd met datum1, terwijl bij een nacht shift de eindtijd eigenlijk op datum2 ligt.

**Fix:**
1. `_bereken_rust_tussen_shifts` accepteert nu ook `start_uur1` parameter
2. Check of `eind_tijd < start_tijd` (middernacht crossing detectie)
3. Als true, voeg 1 dag toe aan de eindtijd datetime

**Code Changes:**
- File: `services/constraint_checker.py`
- Method: `_bereken_rust_tussen_shifts` (line 497-551)
- Aanroep: `check_12u_rust` (line 456-459)

**Test Results:**
Getest met november 2024 data via `scripts/test_constraint_fix.py`:
- ✅ Detecteert nu correct 0.0 uur rust tussen nacht en vroeg
- ✅ Genereert violation: "Te weinig rust: 0.0u tussen shifts (minimaal 12u)"

**Impact:**
- Alle nacht shifts gevolgd door vroeg shifts worden nu correct gevalideerd
- Ook van toepassing op andere middernacht crossing patronen (bijv. laat → nacht)

### ISSUE-009: Planning Editor - Cross-Month Violations Bij Publicatie
**Status:** FIXED (2025-11-05)
**Versie:** v0.6.26
**Severity:** LOW

**Probleem:**
Bij het publiceren van een planning werden violations getoond die in de volgende maand plaatsvinden. Bijvoorbeeld: bij publiceren van november werden violations van december meegeteld.

**User Scenario:**
1. Plan november met shifts tot 30 november
2. Klik "Publiceren"
3. Pre-publicatie validatie toont violations
4. **BUG:** Violations bevatten ook datums in december (bijv. 12u rust tussen 30 nov en 1 dec)
5. **Verwacht:** Alleen violations IN november tonen (we publiceren alleen november)

**Root Cause:**
Pre-publicatie validatie in `planning_editor_screen.py` (line 453-457) telde ALLE violations uit `validate_all()`, inclusief violations met datum in volgende maand. De `PlanningValidator` laadt een buffer van +/- 1 maand voor cross-boundary checks (bijv. 12u rust tussen 30 nov en 1 dec), maar deze violations moeten gefilterd worden bij publicatie.

**Fix:**
Toegevoegd: datum filter in violations counting loop (line 456-459):
```python
# VOOR FIX (line 454):
violations_count = sum(len(v_list) for v_list in violations_dict.values())

# NA FIX (line 454-459 - ISSUE-009):
violations_count = 0
for v_list in violations_dict.values():
    for violation in v_list:
        # Filter: alleen violations waarvan datum in huidige maand valt
        if violation.datum and violation.datum.year == jaar and violation.datum.month == maand:
            violations_count += 1
```

**Code Changes:**
- File: `gui/screens/planning_editor_screen.py`
- Lines: 453-463 (pre-publicatie validation loop)
- Change: Loop door violations en tel alleen violations waar `datum.month == maand`

**Impact:**
- ✅ Pre-publicatie warning toont alleen violations in gepubliceerde maand
- ✅ Geen verwarrende warnings over toekomstige maanden
- ✅ Duidelijkere focus: "november bevat X violations IN november"
- ✅ Cross-month violations (bijv. 12u rust 30 nov → 1 dec) worden pas relevant bij publicatie december

**Gerelateerd:**
- HR Validatie Systeem v0.6.26 (FASE 4 - Pre-Publicatie Check)

---

### ISSUE-001: Feestdag Herkenning bij Kritische Shifts
**Status:** FIXED (v0.6.25)
**Severity:** LOW

**Probleem:**
1 januari werd niet herkend als feestdag bij kritische shifts bemanningscontrole.

**Root Cause:**
`get_dag_type()` functie in `services/bemannings_controle_service.py` checkte niet of een datum een feestdag was voordat weekdag type werd bepaald.

**Fix:**
Expliciete feestdag check toegevoegd in `get_dag_type()` (line 41-43):
```python
# BELANGRIJK: Feestdagen worden behandeld als 'zondag' (v0.6.25 fix)
if is_feestdag(datum):
    return 'zondag'
```

**Code Changes:**
- File: `services/bemannings_controle_service.py`
- Method: `get_dag_type()` (line 28-53)
- Change: Feestdag check vóór weekdag check

**Test Results:**
Getest met `test_issue_001.py` voor 1 januari 2025:
- ✅ is_feestdag(2025-01-01) returnt True
- ✅ get_dag_type(2025-01-01) returnt 'zondag'
- ✅ Verwachte kritische codes: zondag shifts (vroeg, laat, nacht)
- ✅ Bemanningscontrole werkt correct voor feestdagen

**Impact:**
- ✅ Alle feestdagen worden correct behandeld als zondag voor bemanningscontrole
- ✅ Verwachte kritische shifts zijn zondag shifts (niet weekdag shifts)
- ✅ Consistent met shift invoer logica (feestdagen accepteren zondag codes)

---

### ISSUE-002: Planning Editor - Kolom Sortering op Achternaam
**Status:** FIXED (2025-11-11)
**Versie:** v0.6.28
**Severity:** LOW

**Probleem:**
Teamlid kolommen in Planning Editor waren gesorteerd op volledige_naam (voornaam + achternaam als 1 string). Dit resulteerde in alfabetische sortering op voornaam ipv achternaam.

**User Scenario:**
1. Open Planning Editor
2. Kolommen tonen: Bob Aerts, Hegelmeers Alpha, Jacobs Tom, ... (gesorteerd op "B", "H", "J")
3. User wil: Aerts Bob, Hegelmeers Alpha, Jacobs Tom, ... (gesorteerd op achternaam)
4. Bovendien: vaste mensen eerst, dan reserves (beide gesorteerd op achternaam)

**Root Cause:**
Database had alleen `volledige_naam` kolom. Sortering gebeurde via:
```sql
ORDER BY volledige_naam
```

Voor Belgische namen (format "ACHTERNAAM VOORNAAM" zoals "Turlinckx Tim") sorteerde dit op voornaam ipv achternaam.

**Fix:**
Database schema uitbreiding (v0.6.28):
1. Nieuwe kolommen: `voornaam TEXT`, `achternaam TEXT`
2. Parse `volledige_naam` met heuristiek:
   - Laatste woord = voornaam
   - Rest = achternaam (ondersteunt samengestelde achternamen zoals "Van Geert")
3. Nieuwe sortering: `ORDER BY is_reserve, achternaam, voornaam`

**Code Changes:**
- **Database schema** (`database/connection.py` line 142-143):
  ```python
  voornaam TEXT,
  achternaam TEXT,
  ```
- **Migration script** (`migrations/upgrade_to_v0_6_28.py`):
  - Parse logica: laatste woord = voornaam, rest = achternaam
  - Voorbeeld: "Van Den Ackerveken Stef" → voornaam="Stef", achternaam="Van Den Ackerveken"
- **SQL sortering** (`gui/widgets/grid_kalender_base.py` line 59):
  ```python
  query += " ORDER BY is_reserve, achternaam, voornaam"
  ```

**Test Results:**
Sortering na fix (correct):
1. Vaste mensen (alfabetisch op achternaam):
   - Aerts Bob
   - Hegelmeers Alpha
   - Jacobs Tom
   - Test User
   - Turlinckx Tim
   - Van Den Ackerveken Stef
   - Van Geert Koen
   - Wouters Joeri
2. Reserves (alfabetisch op achternaam):
   - Dekrem Sander
   - Docx Glen
   - Theunis Glenn

**Impact:**
- ✅ Planners zien teamleden gesorteerd op achternaam
- ✅ Vaste mensen verschijnen voor reserves
- ✅ Samengestelde achternamen correct gesorteerd
- ✅ Backward compatibility: volledige_naam behouden voor display

---

### ISSUE-005: Planning Editor - HR Overlay Verdwijnt Bij Cel Klik
**Status:** FIXED (2025-11-12)
**Versie:** v0.6.28
**Severity:** MID

**Probleem:**
Wanneer een cel een HR violation overlay heeft (rood/geel), verdwijnt deze overlay zodra je op de cel klikt om te bewerken. De planner verliest visuele feedback over de violation tijdens het bewerken.

**Root Cause:**
Bij cel klik wordt een QLineEdit editor bovenop het EditableLabel geplaatst. Deze editor kreeg een harde `background-color: white` stylesheet (regel 84), waardoor de onderliggende HR overlay (rood rgba 70% opacity) volledig werd verborgen.

**Fix:**
1. **EditableLabel.overlay_kleur attribuut** toegevoegd om huidige overlay kleur te tracken
2. **Editor stylesheet aangepast** om overlay te behouden tijdens edit:
   ```python
   if self.overlay_kleur:
       background = self.overlay_kleur  # Behoud HR/verlof overlay
   else:
       background = "white"  # Default voor normale cellen
   ```
3. **Overlay updates** toegevoegd op 4 plaatsen waar cel styling wordt bijgewerkt:
   - `create_editable_cel()` - Bij cel creatie
   - `update_bemannings_status_voor_datum()` - Na bemannings update
   - `refresh_data()` - Na shift save/delete
   - `apply_selection_styling()` - Bij cel selectie

4. **HR overlay integratie** toegevoegd waar deze ontbrak:
   - Prioriteit: verlof overlay eerst, dan HR overlay
   - Consistent toegepast op alle cel update flows

**Code Changes:**
- File: `gui/widgets/planner_grid_kalender.py`
- Class: `EditableLabel` - `overlay_kleur` attribuut (regel 55)
- Method: `start_edit()` - Editor styling met overlay (regel 84-96)
- Method: `create_editable_cel()` - Overlay opslaan (regel 1455-1457)
- Method: `update_bemannings_status_voor_datum()` - HR overlay + opslaan (regel 1847-1851, 1894-1895)
- Method: `refresh_data()` - HR overlay + opslaan (regel 1980-1984, 2038-2039)
- Method: `apply_selection_styling()` - HR overlay + opslaan (regel 2557-2561, 2611-2612)
- Method: `on_valideer_planning_clicked()` - Friendly name werkpost_onbekend toegevoegd (regel 877)

**Impact:**
- ✅ HR overlay blijft zichtbaar tijdens cel edit (rood/geel achtergrond in editor)
- ✅ Planner heeft constante visuele feedback over violations
- ✅ Editor blends naadloos met onderliggende violation status
- ✅ Verlof overlays behouden ook tijdens edit
- ✅ Consistent gedrag op alle plaatsen waar cellen worden bijgewerkt

**Gerelateerd:**
- HR Validatie Systeem v0.6.26
- Werkpost Validatie v0.6.28

---

## Open Issues

### ISSUE-003: Planning Editor - Focus Behavior
**Status:** OPEN (mogelijk opgelost, wacht op netwerk test)
**Severity:** LOW
**Beschrijving:** Blauwe rand rond ganse maand. Als cel met blauwe rand focus verliest, verspringt die naar headers met dagen.
**Notitie (11 nov 2025):** Lijkt opgelost door realtime validatie fixes (v0.6.26). Nog testen op netwerk database voordat definitief closed.

### ISSUE-004: Mijn Planning - Notitie Indicator
**Status:** OPEN
**Severity:** LOW
**Beschrijving:** Geen visuele aanduiding van gemaakte notities in grid (hover tooltip wel OK).

### ISSUE-008: Planning Editor - bulk menu
**Status:** OPEN
**Severity:** LOW
**Beschrijving:** Nog niet alle bulkzaken geïmplementeerd die in het menu staat. Verschillende rechtermuisknop menu's bij cel in focus of uit focus

### ISSUE-010: Planning Editor - Filter
**Status:** OPEN
**Severity:** LOW
**Beschrijving:** In de handleiding wordt bij de planning verwezen naar een filter om het team te selecteren. Deze filter is er (nog) niet.

### ISSUE-011: Planning Editor - Werkpost Dropdown Filtering Ontbreekt
**Status:** PARTIAL FIX (2025-11-12)
**Severity:** MID (was: HIGH)
**Beschrijving:** Planning Editor filtert shift codes dropdown NIET op basis van gebruiker's werkpost koppelingen.

**Notitie (12 nov 2025):** Post-validatie geïmplementeerd in v0.6.28 (gele warning NA toewijzing verkeerde werkpost). Pre-filtering van dropdown nog niet geïmplementeerd, maar impact gereduceerd door waarschuwing.

**Probleem:**
Een planner kan elke shift code toewijzen aan elke gebruiker, ZONDER te checken of die gebruiker die werkpost kent (via gebruiker_werkposten tabel).

**User Scenario:**
1. Jan kent alleen PAT (werkpost_id = 1)
2. Planner opent cel voor Jan
3. Dropdown toont ALLE shift codes (PAT, Interventie, Servicecentrum)
4. Planner kan Interventie code "7201" toewijzen aan Jan
5. GEEN validatie → Jan krijgt shift voor werkpost die hij niet kent ❌

**Impact:**
- Gebruikers krijgen shifts voor onbekende werkposten
- Planning inconsistent met werkpost koppelingen
- Auto-generatie WEL correct (gebruikt werkpost prioriteit)
- Handmatige invoer NIET correct (geen check)

**Root Cause:**
`get_available_codes()` in `planner_grid_kalender.py` haalt ALLE shift codes op zonder filtering:
```python
# Huidige implementatie (INCORRECT):
cursor.execute("SELECT * FROM shift_codes")
# → Toont alle werkposten zonder check

# Zou moeten zijn:
cursor.execute("""
    SELECT sc.* FROM shift_codes sc
    INNER JOIN gebruiker_werkposten gw ON sc.werkpost_id = gw.werkpost_id
    WHERE gw.gebruiker_id = ?
    ORDER BY gw.prioriteit
""", (gebruiker_id,))
# → Toont alleen bekende werkposten
```

**Fix Nodig:**
1. Filter shift codes op gebruiker's werkpost koppelingen
2. Speciale codes (VV, KD, RX, CX, etc.) ALTIJD tonen
3. Tooltip: "Geen werkposten gekoppeld" als gebruiker geen werkposten kent
4. Mogelijk: Pre-validatie warning bij handmatige invoer (zoals typetabel validatie)

**Verwant aan:**
- Werkpost koppeling systeem (v0.6.14)
- Auto-generatie logic (gebruikt WEL werkpost filtering)