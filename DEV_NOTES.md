# DEV NOTES
Active Development Notes & Session Logs

## CURRENT VERSION: 0.6.15

**Last Updated:** 23 Oktober 2025
**Status:** Beta - Actieve Ontwikkeling

**Rolling Window:** Dit document bevat alleen sessies van de laatste maand (20 okt+)
**Voor oudere sessies:** Zie DEV_NOTES_ARCHIVE.md

---

## 🎯 FOCUS VOOR VOLGENDE SESSIE

### Prioriteit 1: Planning Editor Bulk Operaties
- Copy week functie (kopieer week X naar week Y)
- Paste functie (plak gekopieerde shifts)
- Clear week/range functie (verwijder shifts in bulk)
- Keyboard shortcuts (Ctrl+C, Ctrl+V, Delete)

### Prioriteit 2: Typetabel Activatie Flow
- Activeren dialog met datum picker
- Validatie (alle weken ingevuld?)
- Status transitie (concept → actief, oud actief → archief)
- Gebruikers controle (startweek binnen bereik?)

### Prioriteit 3: Validatie Systeem (HR Regels)
- PlanningValidator class implementeren
- 12u rust check tussen shifts
- 50u/week maximum check
- 19 dagen per 28-dagen cyclus check
- Visuele feedback (rood/geel/groen in grid)

---

## 📝 RECENTE SESSIES

### Sessie 23 Oktober 2025 - Code Quality Improvements (Ruff Linting)
**Duur:** ~30 min
**Focus:** Code quality verbetering met ruff linting tool

**Voltooid:**
- ✅ **Ruff Linting Fixes (100 issues resolved)**
  - 86 automatische fixes via `ruff check --fix`
  - 14 handmatige fixes voor kritieke issues

**Details:**

#### 1. Automatische Fixes (86 issues)
- **F401**: 60+ unused imports verwijderd
  - Vele PyQt6 imports die niet gebruikt werden
  - typing imports (Dict, Any, List, Optional)
  - datetime/timedelta imports
- **F541**: 20+ onnodige f-string prefixes verwijderd
  - `f"static text"` → `"static text"`
- **F811**: Duplicate imports opgeruimd
  - `QScrollArea`, `QTextEdit` werden 2x geïmporteerd in mijn_planning_screen.py

#### 2. Handmatige Fixes (14 issues)
- **E722 - Bare except statements (6 fixes):**
  - `gui/dialogs/auto_generatie_dialog.py`: `except (ValueError, TypeError)` voor datetime parsing
  - `gui/dialogs/typetabel_editor_dialog.py`: `except (ValueError, TypeError)`
  - `gui/screens/typetabel_beheer_screen.py`: 2x specifieke exceptions
  - `gui/widgets/planner_grid_kalender.py`: datetime parsing error handling
  - `migratie_theme_per_gebruiker.py`: `except (FileNotFoundError, json.JSONDecodeError)`

- **F841 - Unused variables (5 fixes):**
  - `detect_db_version.py`: `has_typetabel_data` → prefix met `_` voor documentatie
  - `grid_kalender_base.py`: `oude_gebruiker_ids` verwijderd (leftover code)
  - `verlof_saldo_widget.py`: 2x unused TermCodeService lookups verwijderd
  - `export_service.py`: `datum_fill` en `datum_font` verwijderd

- **E741 - Ambiguous variable name (1 fix):**
  - `services/data_ensure_service.py`: Easter algorithm `l` → `L` (leesbaarder)

- **E402 - Import location (1 fix):**
  - `verify_planning_editor_readiness.py`: datetime import naar top verplaatst

#### 3. Proposed Improvements Document
**Nieuw bestand:** `proposed_improvements.md`
- Pragmatisch verbeteringsplan specifiek voor dit project
- Focus: High value, low effort improvements
- Weggegooid: Enterprise overhead (CI/CD, sprints, teams, etc.)
- High priority items voor v1.0:
  1. Database backup bij migraties (1-2 uur)
  2. Structured logging (2-3 uur)
  3. Batch database operations (1-2 uur)
  4. Consistente context managers (2-3 uur)

**Impact:**
- ✅ Cleaner codebase (geen unused imports/variables)
- ✅ Better error handling (specifieke exceptions i.p.v. bare except)
- ✅ Improved readability en maintainability
- ✅ Foundation voor toekomstige code quality improvements

**Tool:** ruff (Python linter)

**Commit:** `6d366ec` - Code Quality - Ruff Linting Fixes (100 issues resolved)

---

### Sessie 22 Oktober 2025 (Deel 6) - Planning Editor Compleet (v0.6.15)
**Duur:** ~4 uur
**Focus:** Planning Editor Priority 1 afmaken + Multiple bug fixes uit live testing

**Voltooid:**
- ✅ **Concept vs Gepubliceerd Toggle** - Volledig status management systeem
- ✅ **Feestdag Error Messages** - Specifieke foutmeldingen voor feestdagen
- ✅ **Filter State Preservation** - Filter blijft behouden bij maand navigatie
- ✅ **Rode Lijnen Auto-Regeneratie** - Automatisch hertekenen na config wijziging
- ✅ **UI Layout Fix** - Naam kolom verbreed voor lange namen (280px)

#### 1. Concept vs Gepubliceerd Status Toggle
**Doel:** Planners kunnen planning publiceren zodat teamleden deze kunnen zien.

**Geïmplementeerd:**
- **Status Tracking per Maand:**
  - `load_maand_status()` haalt status op uit planning records
  - Status kan 'concept' of 'gepubliceerd' zijn
  - Auto-reload bij maand navigatie via `maand_changed` signal

- **Dynamische UI:**
  - **Concept modus** (geel warning info box):
    - "⚠️ Planning is in CONCEPT. Teamleden zien deze planning nog niet."
    - Button: "Publiceren" (groen, primary style)
  - **Gepubliceerd modus** (groen success info box):
    - "✓ Planning is GEPUBLICEERD. Teamleden kunnen deze planning bekijken."
    - Button: "Terug naar Concept" (oranje, warning style)

- **Dialogs met Bevestiging:**
  - Publiceren: "Weet je zeker dat je de planning voor [maand] wilt publiceren?"
  - Terug naar concept: Waarschuwing dat teamleden planning niet meer kunnen zien

- **Database Updates:**
  - UPDATE alle planning records voor maand: `SET status = 'gepubliceerd'` of `'concept'`
  - Query gebruikt datum range (eerste dag maand → eerste dag volgende maand)

- **Teamlid View Filter:**
  - Teamleden zien ALLEEN gepubliceerde planning (nieuwe parameter `alleen_gepubliceerd=True`)
  - `load_planning_data()` in base class: `WHERE p.status = 'gepubliceerd'` voor teamleden
  - Planners zien altijd alles (concept + gepubliceerd)

**Workflow:**
1. Planner maakt planning → status = 'concept'
2. Teamleden zien NIETS (concept is verborgen)
3. Planner klikt "Publiceren" → bevestiging dialog
4. Status wordt 'gepubliceerd' voor hele maand
5. Teamleden zien planning nu WEL
6. Planner kan ALTIJD nog wijzigen (ook in gepubliceerd modus voor zieken/last-minute)
7. Optioneel: "Terug naar Concept" → teamleden zien weer niets

**Code Wijzigingen:**
- `gui/screens/planning_editor_screen.py`:
  - `load_maand_status()` - regel 160-175
  - `publiceer_planning()` - regel 176-209
  - `terug_naar_concept()` - regel 211-244
  - `on_maand_changed()` handler - regel 146-149
  - Dynamic UI update - regel 82-130

- `gui/widgets/planner_grid_kalender.py`:
  - `maand_changed` signal toegevoegd (regel 33)
  - Emit signal in `refresh_data()` - regel 315

- `gui/widgets/grid_kalender_base.py`:
  - `load_planning_data()` parameter `alleen_gepubliceerd: bool = False` - regel 250
  - WHERE clause met status filter - regel 264-265

- `gui/widgets/teamlid_grid_kalender.py`:
  - Aanroep `load_planning_data(..., alleen_gepubliceerd=True)` - regel 135

#### 2. Feestdag Specifieke Error Messages
**Doel:** Duidelijke foutmeldingen wanneer gebruiker verkeerde shift code invoert op feestdag.

**Geïmplementeerd:**
- `get_feestdag_naam()` helper methode in PlannerGridKalender
- Laadt feestdag namen in dictionary bij `load_feestdagen_extended()`
- Specifieke error messages in `on_cel_edited()`:
  - Feestdag: "Deze datum is een feestdag (Kerstmis). Op feestdagen moeten zondagdiensten worden gebruikt."
  - Weekdag/weekend: "Deze datum is een weekdag/zaterdag/zondag. Gebruik een shift code voor weekdag/zaterdag/zondag."

**Code Wijzigingen:**
- `gui/widgets/planner_grid_kalender.py`:
  - `feestdag_namen: Dict[str, str]` attribute - regel 179
  - `load_feestdagen_extended()` laadt namen - regel 336-349
  - `get_feestdag_naam()` helper - regel 645-647
  - `on_cel_edited()` specifieke messages - regel 587-605

#### 3. Filter State Preservation Fix
**Probleem:** Filter resette naar "iedereen" bij maand navigatie in kalenders.

**Oorzaak:** `load_gebruikers()` overschreef altijd `self.filter_gebruikers` met nieuwe dictionary.

**Oplossing:**
- Check of `filter_gebruikers` al bestaat
- Bij eerste keer: initialiseer met allemaal True
- Bij herlaad: behoud bestaande filter, update alleen voor nieuwe/verwijderde gebruikers
- Merge logica: voeg nieuwe toe, verwijder oude, behoud rest

**Code Wijzigingen:**
- `gui/widgets/grid_kalender_base.py`:
  - Smart filter merge in `load_gebruikers()` - regel 115-130

#### 4. Rode Lijnen Auto-Regeneratie Fix
**Probleem:** Rode lijnen config wijzigen werkte, maar rode lijnen werden niet hertekend in kalenders.

**Oorzaak:**
- `rode_lijnen_config` tabel werd geupdate ✓
- Maar `rode_lijnen` tabel (daadwerkelijke periodes) werd NIET geregenereerd ✗
- Kalender laadt rode lijnen uit `rode_lijnen` tabel → toonde oude data

**Oplossing:**
- Nieuwe functie: `regenereer_rode_lijnen_vanaf(actief_vanaf_str)` in data_ensure_service
- Workflow:
  1. DELETE alle rode lijnen >= actief_vanaf datum
  2. Haal nieuwe actieve config op
  3. Bepaal start punt (laatste rode lijn vóór actief_vanaf, of config start)
  4. Genereer nieuwe rode lijnen tot +2 jaar in toekomst
- Aanroepen na config opslaan in rode_lijnen_beheer_screen

**Code Wijzigingen:**
- `services/data_ensure_service.py`:
  - `regenereer_rode_lijnen_vanaf()` functie - regel 228-320

- `gui/screens/rode_lijnen_beheer_screen.py`:
  - Aanroep na commit - regel 290-299
  - Success dialog met instructie: "Sluit en heropen planning schermen"

#### 5. Naam Kolom Width Fix
**Probleem:** Collega met 25 letters + 3 spaties (28 karakters) naam paste niet in kolom.

**Oplossing:**
- Verhoogd van 200px naar 280px in beide kalenders

**Code Wijzigingen:**
- `gui/widgets/planner_grid_kalender.py`: regel 397, 451
- `gui/widgets/teamlid_grid_kalender.py`: regel 199, 254

**Commits:**
- `49d6886` - Feestdag specifieke error messages
- `a2f6025` - Concept vs Gepubliceerd toggle
- `b51c24e` - Filter preservation fix
- `4e3e435` - Rode lijnen regeneratie
- `377d2c6` - Naam kolom width fix

---

### Sessie 22 Oktober 2025 (Deel 9) - Grid Kalender Tekst Leesbaarheid Fix (Dark Mode)
**Duur:** ~15 min
**Focus:** UX fix - Tekstkleur in grid kalender cellen niet leesbaar in dark mode

**Probleem:**
- Tekst in grid kalender cellen was te licht grijs in dark mode
- Cel achtergronden zijn hardcoded licht (wit, lichtgrijs, geel)
- Tekstkleur was dynamisch via `Colors.TEXT_PRIMARY` (wit in dark mode)
- Resultaat: witte tekst op witte achtergrond = onleesbaar

**Oplossing:**
- Hardcode cel tekstkleur naar zwart (`#000000`) in `create_cel_stylesheet()`
- Niet theme-aware maken (altijd zwart)
- Cel achtergronden blijven ongewijzigd (light colored)

**Code Wijzigingen:**
- `gui/widgets/grid_kalender_base.py`: regel 408, 420
- `gui/widgets/planner_grid_kalender.py`: regel 437, 450
- `gui/widgets/teamlid_grid_kalender.py`: regel 218, 230

**Verificatie:**
- ✅ Applicatie start zonder errors
- ✅ Tekst in cellen nu altijd zwart
- ✅ Goed leesbaar in zowel light als dark mode

---

### Sessie 22 Oktober 2025 (Deel 8) - Multiscreen Setup Fix
**Duur:** ~30 min
**Focus:** Bug fix - Window over meerdere schermen bij multiscreen setup

**Probleem:**
- "Mijn Planning" scherm werd over 2 monitors getoond
- `showMaximized()` maximaliseert over alle beschikbare schermen op multiscreen setups

**Oplossing:**
- Nieuwe methode: `maximize_on_primary_screen()`
- Gebruikt `QApplication.primaryScreen()` om primair scherm te identificeren
- Gebruikt `availableGeometry()` voor beschikbare ruimte (minus taskbar)
- Gebruikt `showNormal()` in plaats van `showMaximized()`

**Code Wijzigingen:**
- `main.py`:
  - `on_login_success()`: `showMaximized()` → `maximize_on_primary_screen()` - regel 52
  - **NIEUW:** `maximize_on_primary_screen()` methode - regel 55-74

---

### Sessie 22 Oktober 2025 (Deel 7) - Rode Lijnen Seed Datum Fix & Migratie
**Duur:** ~1.5 uur
**Focus:** Correctie rode lijnen seed datum + nieuwe cyclus logica fix + migratie script

**Probleem:**
- Rode lijnen werden 1 dag te vroeg getekend (tussen 18-19 okt i.p.v. 19-20 okt)
- Seed datum in `database/connection.py` was 28 juli 2024, correct is 29 juli 2024

**Fixes:**

#### 1. Regeneratie Logica Fix
**Probleem:** `regenereer_rode_lijnen_vanaf()` continueerde altijd vanuit oude cyclus, negeerde nieuwe config start_datum.

**Oplossing:**
- Check toegevoegd: `if config_start_datum >= actief_vanaf`
- True: Start nieuwe cyclus vanaf config_start_datum
- False: Continueer oude cyclus (backward compatibility)

#### 2. Seed Datum Correctie
- `database/connection.py`: start_datum van 2024-07-28 → 2024-07-29
- Comments toegevoegd: "uitkomend op periode 17 = 20 oktober 2025"

#### 3. Unicode Fixes voor Windows Console
- Alle Unicode karakters vervangen met ASCII (✓ → [OK], ✗ → [ERROR])

#### 4. Migratie Script Creatie
**Nieuw bestand:** `fix_rode_lijnen_seed_datum.py`
- Detectie: Check eerste rode lijn start datum
- Delete: Verwijder ALLE rode lijnen
- Regenerate: vanaf 29 juli 2024 tot +2 jaar
- Config Update: indien nodig
- Verificatie: Toon eerste 3 periodes + oktober 2025

---

### Sessie 22 Oktober 2025 (Deel 2) - Feestdag Behandeling in Auto-Generatie Fix
**Duur:** ~30 min
**Focus:** Bug fix - Feestdagen krijgen verkeerde shift codes bij auto-generatie

**Probleem:**
- Bij auto-generatie uit typetabel kregen feestdagen normale weekdag codes
- Voorbeeld: Typetabel zegt "V" op feestdag → kreeg 7101 (weekdag vroeg)
- MOET ZIJN: Feestdagen = zondag codes → 7701 (zondag vroeg)

**Oplossing:**
- Auto-generatie dialog: feestdagen laden uit database
- `bereken_shift_slim()`: check of datum feestdag is
- Als feestdag: `dag_type = 'zondag'` ipv weekdag/zaterdag

---

### Sessie 22 Oktober 2025 - Werkpost Koppeling & Slimme Auto-Generatie (v0.6.14)
**Duur:** ~3 uur
**Focus:** Many-to-many werkpost koppeling met intelligente auto-generatie uit typetabel

**Voltooid:**
- ✅ **Database Migratie**
  - Nieuwe tabel `gebruiker_werkposten` (many-to-many met prioriteit)
  - Index `idx_gebruiker_werkposten_gebruiker` voor performance
  - Migratie script `migratie_gebruiker_werkposten.py`
  - Auto-seed: koppel alle gebruikers aan eerste actieve werkpost

- ✅ **Werkpost Koppeling UI**
  - Nieuw scherm `werkpost_koppeling_screen.py`
  - Grid layout: gebruikers (Y-as) × werkposten (X-as)
  - Checkboxes voor koppelingen + prioriteit spinboxes
  - Filters: naam zoeken + toon reserves
  - Reserves visueel onderscheiden ([RESERVE] label + grijze achtergrond)

- ✅ **Slimme Auto-Generatie**
  - Nieuwe dialog `auto_generatie_dialog.py`
  - Algoritme: typetabel "V" → dag_type + werkpost → shift_code "7101"
  - Multi-post support met prioriteit fallback
  - Bescherming: speciale codes en handmatige wijzigingen blijven behouden
  - Preview functionaliteit met statistieken

**Technische Details:**
- **Auto-Generatie Logica:**
  1. Laad typetabel data in memory: `{(week, dag): shift_type}`
  2. Laad gebruiker werkposten: `{gebruiker_id: [(werkpost_id, prioriteit), ...]}`
  3. Laad shift_codes mapping: `{(werkpost_id, dag_type, shift_type): code}`
  4. Per gebruiker per datum: bereken shift_type uit typetabel
  5. Bepaal dag_type uit datum (weekdag/zaterdag/zondag)
  6. Loop door gebruiker's werkposten (op prioriteit) totdat match
  7. Insert shift_code in planning (bescherm speciale codes!)

- **Prioriteit Fallback:**
  - Jan kent PAT (prio 1) en Interventie (prio 2)
  - Typetabel zegt "N" op maandag
  - PAT heeft geen nacht op weekdag → skip
  - Interventie heeft wel nacht → gebruik "7201"

---

### Sessie 21 Oktober 2025 (Deel 3) - Database Versie Beheer Systeem (v0.6.13)
**Duur:** ~1 uur
**Focus:** Centraal versie beheer systeem voor app en database compatibiliteit

**Voltooid:**
- ✅ **Config.py Versie Management**
  - `APP_VERSION = "0.6.13"` - verhoogt bij elke wijziging
  - `MIN_DB_VERSION = "0.6.12"` - verhoogt alleen bij DB schema wijzigingen
  - Gescheiden versie nummers voor app en database

- ✅ **Database Metadata Tabel (v0.6.13)**
  - Nieuwe tabel: `db_metadata` (version_number, updated_at, migration_description)
  - Helper functies: `get_db_version()`, `check_db_compatibility()`

- ✅ **Versie Check bij App Start**
  - `check_db_compatibility()` in main.py
  - Bij incompatibiliteit: duidelijke foutmelding met contactinformatie
  - Geen automatische migratie - handmatige upgrade vereist

- ✅ **UI Versie Weergave**
  - LoginScreen: App versie + DB versie onderaan
  - AboutDialog: App versie + DB versie in header

- ✅ **Upgrade Script**
  - `upgrade_to_v0_6_13.py` voor bestaande databases

---

### Sessie 21 Oktober 2025 (Deel 2) - Theme Per Gebruiker (v0.6.12)
**Duur:** ~1 uur
**Focus:** Theme voorkeur van globaal naar per gebruiker verplaatsen

**Voltooid:**
- ✅ **Database Migratie v0.6.11 → v0.6.12**
  - Nieuwe kolom: `gebruikers.theme_voorkeur` (TEXT, default 'light')
  - Migratie van oude globale theme preference naar alle gebruikers
  - Oude `data/theme_preference.json` verwijderd

- ✅ **Main.py Theme Management Refactor**
  - `load_theme_preference()`: Laadt theme uit database per gebruiker
  - `save_theme_preference()`: Slaat theme op in database per gebruiker
  - Login scherm: Altijd light mode
  - Logout fix: Reset naar light mode

---

### Sessie 21 Oktober 2025 (Deel 1) - Shift Voorkeuren Systeem (v0.6.11)
**Duur:** ~1.5 uur
**Focus:** Shift voorkeuren voor gebruikers - input voor toekomstige automatische planning

**Voltooid:**
- ✅ **Database Migratie v0.6.10 → v0.6.11**
  - Nieuwe kolom: `gebruikers.shift_voorkeuren` (TEXT, JSON format)
  - Migratie script: `migratie_shift_voorkeuren.py`

- ✅ **VoorkeurenScreen Implementatie**
  - Dashboard → Persoonlijk → Mijn Voorkeuren
  - 4 ComboBoxes voor shift types: Vroeg, Laat, Nacht, Typetabel
  - Prioriteit selectie: 1 (hoogste) tot 4 (laagste), of geen voorkeur
  - Live preview van gekozen volgorde
  - Validatie: voorkomt dubbele prioriteiten

- ✅ **JSON Data Model**
  - Format: `{"1": "vroeg", "2": "typetabel", "3": "laat"}`

---

### Sessie 20 Oktober 2025 (Deel 2) - Verlof & KD Saldo Systeem (v0.6.10)
**Duur:** ~2 uur
**Focus:** Complete verlof en kompensatiedag saldo tracking systeem

**Voltooid:**
- ✅ **Database Migratie v0.6.9 → v0.6.10**
  - Nieuwe tabel: `verlof_saldo` voor tracking van VV en KD per gebruiker/jaar
  - Nieuwe speciale code: KD met term 'kompensatiedag'
  - Nieuwe kolom: `verlof_aanvragen.toegekende_code_term`

- ✅ **Service Layer: VerlofSaldoService**
  - `get_saldo()`: Real-time berekening van opgenomen dagen
  - `bereken_opgenomen_uit_aanvragen()`: Term-based query
  - `check_voldoende_saldo()`: Validatie voor negatief saldo

- ✅ **Admin Scherm: Verlof Saldo Beheer**
  - Overzicht alle gebruikers met VV en KD saldi per jaar
  - "Nieuw Jaar Aanmaken" functie voor bulk setup
  - Opmerking veld voor notities

- ✅ **Teamlid Widget: VerlofSaldoWidget**
  - Read-only weergave van eigen saldo
  - Warning voor overgedragen verlof vervaldatum (1 mei)

- ✅ **Planner Goedkeuring: Type Selectie Dialog**
  - VerlofTypeDialog bij goedkeuring: kies tussen VV of KD
  - Real-time saldo preview met kleurcodering

**Business Rules:**
- Verlof overdracht vervalt 1 mei (handmatig cleanup door admin)
- KD overdracht max 35 dagen (validatie in dialog)
- Negatief saldo toegestaan (wordt schuld voor volgend jaar)

---

### Sessie 20 Oktober 2025 (Deel 1) - Dark Mode & Rode Lijnen Visualisatie (v0.6.9)
**Duur:** ~3 uur
**Focus:** Bug fixes, dark mode implementatie, en rode lijnen visualisatie

**Voltooid:**
- ✅ **Bug Fix: Calendar Widget Kolom Weergave**
  - Rechtse kolom (zondag) viel gedeeltelijk weg
  - Fix: `min-width: 36px` voor QAbstractItemView::item

- ✅ **Bug Fix: Feestdagen Niet Herkend in Grid Kalender**
  - Buffer dagen buiten huidig jaar werden niet geladen
  - Fix: `load_feestdagen_extended()` laadt 3 jaren

- ✅ **Feature: Dark Mode (Nachtmodus)**
  - ThemeManager singleton class
  - Colors class met _LIGHT_THEME en _DARK_THEME
  - ThemeToggleWidget met zon/maan iconen
  - Dashboard rebuild strategie

- ✅ **Feature: Rode Lijnen Visualisatie**
  - Visuele weergave van 28-daagse HR cycli
  - Dikke rode linker border (4px) markeert periode start
  - Tooltip met periode nummer

---

## 🛠️ KNOWN ISSUES

### 🟢 KLEIN (Quality of Life)

**Geen openstaande issues!** ✅

---

## 📋 TODO LIST

### Voor Release 1.0 (December 2025)

**Planning Editor** (HOOGSTE PRIORITEIT)
- [x] Grid kalender met editable cells (basis) ✅
- [x] Shift codes invoer per cel ✅
- [x] Save/delete functionaliteit ✅
- [x] Auto-generatie uit typetabel ✅ v0.6.14
- [x] Concept vs Gepubliceerd status toggle ✅ v0.6.15
- [x] Bulk delete maand (met bescherming speciale codes) ✅ v0.6.16
- [x] Notities systeem (basis) ✅ v0.6.16
- [ ] Bulk operations (copy week, paste, clear)
- [ ] Undo/Redo functionaliteit
- [ ] Validatie integratie (rood/geel/groen feedback)

**Notities Systeem Verbeteringen** (Medium/Hoge Prioriteit)
- [ ] Grafische indicator ipv "*" karakter (niet-verwijderbaar overlay)
- [ ] Bidirectionele notities (teamlid ↔ planner communicatie)
- [ ] Notitie richting kolom in database ('planner_naar_teamlid', 'teamlid_naar_planner', 'beide')
- [ ] Verschillende visuele indicators per richting
- [ ] Notitie naar planner vanuit "Mijn Planning" (teamlid view)

**Typetabel Systeem**
- [x] Database migratie naar versioned systeem ✅
- [x] TypetabelBeheerScreen met overzicht ✅
- [x] Nieuwe typetabel concept maken ✅
- [x] Grid editor met dropdowns ✅
- [x] Kopiëren functionaliteit ✅
- [x] Verwijderen concept ✅
- [ ] Activeren flow met datum picker
- [ ] Validatie (alle weken ingevuld, realistische patronen)
- [ ] Bulk operaties (kopieer week, vul reeks)
- [ ] GebruikersBeheer integratie (dynamische max startweek)

**Validatie Systeem** (Hoge Prioriteit)
- [ ] PlanningValidator service class
- [ ] 12u rust check implementeren
- [ ] 50u per week check implementeren
- [ ] 19 dagen per 28d cyclus check
- [ ] Max 7 dagen tussen RX/CX check
- [ ] Max 7 werkdagen reeks check
- [ ] **BELANGRIJK: Feestdagen behandelen als zondag**
- [ ] Visuele feedback in planning grid
- [ ] Violation messages tooltip
- [ ] Blokkeer publicatie bij violations

**Export Functionaliteit** (Medium Prioriteit)
- [ ] Publiceer naar HR (Excel format)
- [ ] Template voor HR export
- [ ] Maandelijks overzicht export (Excel/PDF)
- [ ] Archief export (volledige planning)

**Build & Deployment** (Voor Release)
- [x] .EXE build met PyInstaller ✅
- [ ] Icon voor applicatie
- [ ] Netwerkschijf deployment guide
- [ ] Backup script/cronjob setup
- [ ] Multi-user testing
- [ ] Performance testing
- [ ] Training materiaal
- [ ] Gebruikers handleiding

---

## 💡 LESSEN GELEERD (Recente Sessies)

### PyQt6 Specifiek
1. **Signals moeten class attributes zijn** - Niet in `__init__` definiëren
2. **Type ignore voor signals** - Bij connect() en emit()
3. **Unicode voorzichtig** - Emoji's in buttons crashen op Windows
4. **Button widths consistent** - Zelfde width voor toggle buttons (96px)

### Database
1. **Prepared statements** - Altijd ? placeholders gebruiken
2. **Soft delete beter dan hard delete** - Data behoud + audit trail
3. **CASCADE delete** - Automatic cleanup bij parent delete
4. **Migratie scripts essentieel** - Check schema, pas aan indien nodig

### UI/UX
1. **Consistency is key** - Zelfde patterns overal
2. **Feedback direct** - Geen silent fails
3. **Validatie vroeg** - Voor database operaties
4. **Confirmatie bij destructieve acties** - Voorkom ongelukken

### Architectuur
1. **Scheiding concerns** - GUI, Business Logic, Database apart
2. **Router pattern werkt goed** - Callback voor navigatie
3. **Centrale styling vermijdt duplicate code**
4. **Services voor herbruikbare logica**
5. **Versioning voor belangrijke data** - Zoals typetabellen

### Development Process
1. **Kleine stappen** - Feature per feature implementeren
2. **Test frequent** - Direct testen na changes
3. **Documentation tijdens development** - Niet achteraf
4. **Git commits frequent** - Bij werkende staat

---

## 🎯 VOLGENDE SESSIE VOORBEREIDING

**Prioriteit 1: Planning Editor Bulk Operaties**

1. **Copy Week:**
   - Button "Kopieer Week"
   - Dialog met week selectie
   - Opslaan in geheugen

2. **Paste Week:**
   - Button "Plak Week"
   - Dialog met doelweek selectie
   - Overschrijf waarschuwing

3. **Clear Range:**
   - Button "Wis Range"
   - Dialog met start/eind datum
   - Bevestiging voor delete

4. **Keyboard Shortcuts:**
   - Ctrl+C: Copy selected week
   - Ctrl+V: Paste to current week
   - Delete: Clear selected cells

**Geschatte tijd:** 3-4 uur

---

**Prioriteit 2: Typetabel Activatie Flow**

1. **Activeren Dialog:**
   - Datum picker voor startdatum
   - Validatie checklist tonen
   - Gebruikers impact preview

2. **Validatie:**
   - Check: Alle weken ingevuld?
   - Check: Realistische codes?
   - Check: Gebruikers startweek binnen bereik?

3. **Status transitie:**
   - Oud actief → archief (met actief_tot datum)
   - Nieuw concept → actief (met actief_vanaf datum)
   - Database transactie (rollback bij fout)

**Geschatte tijd:** 3-4 uur

---

*Voor historische sessies: zie DEV_NOTES_ARCHIVE.md*
*Voor technische referentie: zie DEVELOPMENT_GUIDE.md*
*Voor release info: zie PROJECT_INFO.md*

*Laatste update: 23 Oktober 2025*
*Versie: 0.6.15*
