# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## IMPORTANT: Session Workflow

**AT THE START OF EACH SESSION:**
1. **CLEAR `SESSION_LOG.md`** - Start met nieuwe sessie template voor crash recovery
2. **WRITE SESSION GOALS** - Noteer planning en doelen in SESSION_LOG.md
3. **READ `DEV_NOTES.md` FIRST** - Contains current development status, recent sessies (laatste maand), known issues, and next priorities (~600 lines)
4. **READ `DEVELOPMENT_GUIDE.md` SECOND** - Contains technical architecture, coding patterns, and implementation details (~990 lines - tijdloos)
5. **UNDERSTAND CURRENT STATE** - Check versie nummer, status, en openstaande taken before starting work
6. **For historical context:** Check `DEV_NOTES_ARCHIVE.md` for sessies ouder dan 1 maand

**DURING SESSION:**
- **UPDATE `SESSION_LOG.md` FREQUENTLY** - Mark steps completed, add crash recovery info
- Real-time tracking helpt bij herstel na stroomuitval/crashes

**AT THE END OF EACH SESSION:**
1. **SUMMARIZE SESSION** - Move session summary from SESSION_LOG.md to DEV_NOTES.md
2. **UPDATE `DEV_NOTES.md`** - Add session notes to top of recente sessies section
   - Keep rolling window (laatste maand only)
   - Move oude sessies (>1 maand) to DEV_NOTES_ARCHIVE.md when needed
3. **UPDATE `DEVELOPMENT_GUIDE.md`** - ONLY add timeless technical patterns/architecture changes (NOT version-specific features)
4. **UPDATE `PROJECT_INFO.md`** - Add new version entry to "VOLLEDIGE VERSIE GESCHIEDENIS" for user-facing changes
5. **UPDATE VERSION** - Follow version update workflow below
6. **CLEAR `SESSION_LOG.md`** - Ready for next session (optional: keep laatste sessie voor reference)

**DOCUMENTATION STRUCTURE (v0.6.15+):**
- **SESSION_LOG.md** (~200 lines): Real-time sessie tracking voor crash recovery (OVERSCHREVEN elke sessie)
- **DEV_NOTES.md** (600 lines): Recente sessies (laatste maand), TODO lijst, Known issues
- **DEV_NOTES_ARCHIVE.md** (1200+ lines): Historische sessies (ouder dan 1 maand)
- **DEVELOPMENT_GUIDE.md** (990 lines): Tijdloze technische referentie
- **PROJECT_INFO.md** (928 lines): User-facing info + volledige versie geschiedenis
- **CLAUDE.md** (548 lines): Claude instructies

## Version Update Workflow (v0.6.13+)

**IMPORTANT:** Since v0.6.13, version management is centralized in `config.py`. Always follow this checklist:

### For ANY Change (GUI or Database):
1. **Increment `APP_VERSION` in `config.py`**
   ```python
   APP_VERSION = "0.6.15"  # Always increment
   ```

2. **Update version in documentation:**
   - `CLAUDE.md` - Line 70: Current Version
   - `DEVELOPMENT_GUIDE.md` - Line 5: Huidige versie
   - `DEV_NOTES.md` - Line 4: CURRENT VERSION
   - `PROJECT_INFO.md` - Line 5: Huidige versie (+ footer line ~553)

### For Database Schema Changes ONLY:
3. **Also increment `MIN_DB_VERSION` in `config.py`**
   ```python
   APP_VERSION = "0.6.15"
   MIN_DB_VERSION = "0.6.15"  # Same as APP_VERSION when DB changes
   ```

4. **Update database schema in `database/connection.py`**
   - Modify `create_tables()` for new/changed tables
   - Update seed functions if needed

5. **Create upgrade script:** `upgrade_to_vX_Y_Z.py`
   ```python
   # Add schema changes
   # Update db_metadata table with new version
   ```

6. **Update `db_metadata` table:**
   ```sql
   INSERT INTO db_metadata (version_number, migration_description)
   VALUES ("0.6.15", "Description of schema change")
   ```

**⚠️ CRITICAL:** Migration scripts MUST update `db_metadata` or the app will refuse to start with "database version mismatch" error. Schema changes without version updates cause compatibility failures!

### Version Numbering Pattern:
- Pattern: `0.6.X` where X increments sequentially
- Examples: `0.6.9` → `0.6.10` → `0.6.11` → `0.6.12` → `0.6.13`
- Major features may increment to `0.7.0`, `0.8.0`, etc.
- Release 1.0 planned for December 2025

### Quick Reference:
- **GUI-only change:** APP_VERSION++ (MIN_DB_VERSION stays same)
- **DB schema change:** APP_VERSION++ AND MIN_DB_VERSION++ (both equal)

## Project Overview

**Planning Tool** - A shift scheduling application for self-rostering teams, built with Python and PyQt6. The application manages team schedules, leave requests, shift codes, and schedule templates (typetabellen) for shift-based work environments.

**Current Version:** 0.6.18 (Beta)
**Status:** Active development - Grid Kalender Refactoring & Teamlid Features

## Running the Application

```bash
# Run the application
python main.py

# Upgrade bestaande database (v0.6.13 → v0.6.14)
python migratie_gebruiker_werkposten.py  # Voegt gebruiker_werkposten tabel toe voor werkpost koppeling

# Run database migrations (if upgrading from older versions)
python upgrade_to_v0_6_13.py             # v0.6.12 → v0.6.13 (db_metadata tabel)
python migratie_theme_per_gebruiker.py  # v0.6.11 → v0.6.12 (theme per gebruiker)
python migratie_shift_voorkeuren.py      # v0.6.10 → v0.6.11 (shift voorkeuren)
python migratie_verlof_saldo.py          # v0.6.9 → v0.6.10 (verlof & KD saldo)
python migratie_rode_lijnen_config.py    # v0.6.7 → v0.6.8 (rode lijnen config)
python migratie_systeem_termen.py        # v0.6.6 → v0.6.7 (term-based codes)
python migratie_typetabel_versioned.py   # v0.6.5 → v0.6.6 (typetabel system)
python database_shift_codes_migration.py # Earlier → v0.6.4+ (shift codes)
```

**Default login credentials:**
- Username: `admin`
- Password: `admin`

## Architecture

### Database Layer
- **SQLite** database located at `data/planning.db`
- Connection management in `database/connection.py`
- Foreign keys enabled via `PRAGMA foreign_keys = ON`
- Row factory set to `sqlite3.Row` for dict-like access
- All tables use soft delete pattern (is_actief flag + timestamps)

**Key Tables:**
- `db_metadata` - Database version tracking (v0.6.13)
- `gebruikers` - Users with UUID-based identification (kolom: `volledige_naam`, niet `naam`)
- `gebruiker_werkposten` - Many-to-many user-to-werkpost mapping with priority (v0.6.14: NIEUW)
- `typetabel_versies` + `typetabel_data` - Versioned schedule templates (v0.6.6)
- `werkposten` + `shift_codes` - Team-specific shift codes
- `speciale_codes` - Global codes with optional term field (v0.6.7)
  - System codes: verlof, kompensatiedag, zondagrust, zaterdagrust, ziek, arbeidsduurverkorting (v0.6.10)
  - Free codes: VD, RDS, TCR, SCR, T, etc.
- `planning` - Daily schedule assignments
- `verlof_aanvragen` - Leave requests with approval workflow (v0.6.10: + `toegekende_code_term`)
- `verlof_saldo` - Yearly leave and KD balances per user (v0.6.10: NIEUW)
- `feestdagen` - Holidays (fixed and variable, GEEN `is_actief` kolom)
- `rode_lijnen` - 28-day HR cycles
- `rode_lijnen_config` - Versioned configuration for HR cycles (v0.6.8)

### Version Management (v0.6.13)
**Centralized Version Control:**
- `config.py` bevat `APP_VERSION` en `MIN_DB_VERSION`
- `APP_VERSION`: verhoogt bij elke wijziging (GUI of DB)
- `MIN_DB_VERSION`: verhoogt alleen bij DB schema wijzigingen
- Versie weergave op loginscherm en About dialog
- Automatische compatibiliteit check bij app start

**Database Versie Tracking:**
- `db_metadata` tabel slaat database versie op
- `get_db_version()` haalt huidige DB versie op
- `check_db_compatibility()` controleert app ↔ DB compatibiliteit
- Bij incompatibele database: error dialog met contactinformatie (geen automatische migratie)

**Upgrade Workflow:**
1. Download nieuwe app versie
2. Run `upgrade_to_v0_6_13.py` (of nieuwere upgrade script)
3. Start app - versie check gebeurt automatisch
4. Bij error: neem contact op met beheerder voor handmatige upgrade

### GUI Layer (PyQt6)
- **Entry point:** `main.py` with QStackedWidget for screen navigation
- **Screens:** Located in `gui/screens/` - full-page views
- **Dialogs:** Located in `gui/dialogs/` - modal dialogs
- **Widgets:** Located in `gui/widgets/` - reusable components
- **Styling:** Centralized in `gui/styles.py` (Styles, Colors, Fonts, Dimensions, ThemeManager)

**Theme System (v0.6.9):**
- **ThemeManager**: Singleton class for theme state (`_current_theme`)
- **Colors class**: Dynamic palette with `_LIGHT_THEME` and `_DARK_THEME` dictionaries
- **Theme persistence**: Saved in `data/theme_preference.json`
- **Dashboard rebuild**: On theme toggle, dashboard is rebuilt for correct styling
- **ThemeToggleWidget**: Visual toggle component with sun/moon icons (only in dashboard)

**Navigation Pattern:**
- Main window uses QStackedWidget
- Each screen receives a `router` callback for "back" navigation
- Dashboard emits PyQt signals for menu actions
- Main.py connects signals to screen handlers

**IMPORTANT PyQt6 Patterns:**
- Signals MUST be class attributes, not instance attributes
- All instance attributes should be declared in `__init__` with type hints
- Use `# type: ignore` comments for signal.connect() and signal.emit()
- AVOID Unicode/emoji in UI text (Windows compatibility issues)

### Services Layer
- `services/data_ensure_service.py` - Auto-generation of holidays and HR cycles
- `services/term_code_service.py` - Term-to-code mapping with cache (v0.6.7)
- `services/verlof_saldo_service.py` - Leave and KD balance management (v0.6.10)

### Grid Kalenders (v0.6.9)
**Feestdagen Loading:**
- `load_feestdagen_extended()` - Loads holidays for 3 years (previous, current, next)
- Required for buffer days (8 days before/after month) in PlannerGridKalender
- Auto-generates missing holidays via `ensure_jaar_data()`

**Rode Lijnen Visualisatie:**
- `load_rode_lijnen()` - Loads all HR cycle start dates into dictionary
- `{datum_str: periode_nummer}` mapping for O(1) lookup performance
- Timestamp stripping: `2024-07-28T00:00:00` → `2024-07-28`
- Visual marker: 4px red left border on column start of new period
- Tooltip: "Start Rode Lijn Periode X"
- Implemented in both `PlannerGridKalender` and `TeamlidGridKalender`

## Core Concepts

### Typetabel System (Schedule Templates)
A **typetabel** is a repeating schedule pattern (1-52 weeks) used to auto-generate team schedules:
- **Versioned system:** CONCEPT → ACTIEF → ARCHIEF status lifecycle
- Only 1 typetabel can be ACTIEF at a time
- Each user has a `startweek_typedienst` (1 to N) to offset their position in the pattern
- Multi-post support via shift codes with post numbers (V1, V2, L1, L2, etc.)

### Shift Codes System
Two-tier system:
1. **Werkposten** (Work Posts) - Team-specific shift definitions with 3x4 grid (day_type × shift_type)
2. **Speciale Codes** - Global codes with term-based system (v0.6.7)
   - **System codes** (protected): verlof, kompensatiedag, zondagrust, zaterdagrust, ziek, arbeidsduurverkorting (6 terms sinds v0.6.10)
   - **Free codes**: VD, RDS, TCR, SCR, T, etc.
   - Codes can be renamed (VV→VL, KD→CD) but terms are fixed
   - System uses TermCodeService for dynamic lookups

### Werkpost Koppeling System (v0.6.14)
**Many-to-many relatie tussen gebruikers en werkposten:**
- Elke gebruiker kan meerdere werkposten kennen
- Prioriteit systeem (1 = eerste keuze, 2 = fallback, etc.)
- UI: Grid met checkboxes (gebruikers × werkposten)
- Filters: naam zoeken + toon reserves

**Slimme Auto-Generatie:**
1. Typetabel bevat abstract shift types ("V", "L", "N", "dag")
2. Datum bepaalt dag_type (weekdag/zaterdag/zondag)
3. Gebruiker's werkposten bepalen welke concrete codes beschikbaar zijn
4. Algoritme: loop door werkposten (op prioriteit) totdat shift_code match gevonden
5. Resultaat: typetabel "V" + weekdag + werkpost PAT → shift_code "7101"

**Voorbeeld multi-post scenario:**
- Jan kent: PAT (prio 1), Interventie (prio 2)
- Typetabel: "N" op maandag
- PAT heeft geen nacht op weekdag → skip
- Interventie heeft wel nacht op weekdag = "7201" → gebruik deze

### Verlof & KD Saldo Systeem (v0.6.10)
**Admin beheer:**
- Jaarlijks contingent per gebruiker (handmatig input voor deeltijders)
- Overdracht management (VV vervalt 1 mei, KD max 35 dagen)
- Nieuw jaar bulk aanmaken functie
- Opmerking veld voor notities (bijv. "80% deeltijd")

**Teamlid view:**
- VerlofSaldoWidget toont eigen saldo (VV en KD)
- Specifieke labels: "Overdracht uit vorig jaar" (VV) vs "Overdracht uit voorgaande jaren" (KD)
- Warning countdown voor vervaldatum overgedragen verlof (1 mei)
- Auto-refresh na nieuwe aanvraag

**Planner workflow:**
- VerlofTypeDialog bij goedkeuring: kies VV of KD
- Real-time saldo preview met kleurcodering (rood/geel/groen)
- Planning records gegenereerd met gekozen code
- Auto-sync saldo na goedkeuring

**Business rules:**
- Opgenomen dagen auto-berekend uit goedgekeurde aanvragen (term-based)
- Negatief saldo toegestaan (wordt schuld volgend jaar)
- Teamlid vraagt "verlof", planner beslist VV of KD

**Time Notation Parser** - Flexible formats:
- `6-14` → `06:00-14:00` (shortcut for full hours)
- `06:00-14:00` → Full format
- `06:30-14:30` → Half hours
- `14:15-22:45` → Quarter hours

### HR Rules
System checks:
- 12 hour rest between shifts
- Max 50 hours per week
- Max 19 working days per 28-day cycle
- Max 7 days between RX/CX
- Max 7 consecutive working days

## Development Workflow

### Adding a New Screen

1. **Create screen file** in `gui/screens/your_screen.py`:
```python
from typing import Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from gui.styles import Styles, Dimensions

class YourScreen(QWidget):
    def __init__(self, router: Callable):
        super().__init__()
        self.router = router
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # Build UI...

        terug_btn = QPushButton("Terug")
        terug_btn.clicked.connect(self.router)  # type: ignore
        layout.addWidget(terug_btn)
```

2. **Add signal to DashboardScreen** (`gui/screens/dashboard_screen.py`):
```python
your_screen_clicked = pyqtSignal()
```

3. **Add menu button** in appropriate tab method:
```python
scroll_layout.addWidget(self.create_menu_button(
    "Your Screen",
    "Description"
))
```

4. **Handle click** in `handle_menu_click()`:
```python
elif title == "Your Screen":
    self.your_screen_clicked.emit()
```

5. **Connect in main.py**:
```python
def show_dashboard(self):
    # ...
    dashboard.your_screen_clicked.connect(self.on_your_screen_clicked)  # type: ignore

def on_your_screen_clicked(self):
    from gui.screens.your_screen import YourScreen
    scherm = YourScreen(self.terug)
    self.stack.addWidget(scherm)
    self.stack.setCurrentWidget(scherm)
```

### Database Operations

**Always use prepared statements:**
```python
from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# Good - parameterized query
cursor.execute("SELECT * FROM gebruikers WHERE id = ?", (user_id,))

# Bad - SQL injection risk
cursor.execute(f"SELECT * FROM gebruikers WHERE id = {user_id}")
```

**Soft delete pattern:**
```python
cursor.execute("""
    UPDATE werkposten
    SET is_actief = 0, gedeactiveerd_op = ?
    WHERE id = ?
""", (datetime.now().isoformat(), post_id))
```

### Styling

**Always use centralized styles:**
```python
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig, ThemeManager

# Buttons
btn.setStyleSheet(Styles.button_primary())
btn.setFixedHeight(Dimensions.BUTTON_HEIGHT)

# Input fields
input.setStyleSheet(Styles.input_field())

# Tables
TableConfig.setup_table_widget(table, row_height=50)

# Dynamic colors (v0.6.9 - theme aware)
background = Colors.BG_WHITE  # Automatically adapts to current theme
text_color = Colors.TEXT_PRIMARY  # Changes between light/dark mode
```

**Common button pattern:**
```python
btn = QPushButton("Label")
btn.setFixedWidth(96)  # Consistent width for toggle buttons
btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
btn.setStyleSheet(Styles.button_primary(Dimensions.BUTTON_HEIGHT_TINY))
```

## Common Issues

### PyQt6 Signal Issues
**Problem:** Signals not working
**Solution:** Signals must be class attributes:
```python
class MyWidget(QWidget):
    my_signal: pyqtSignal = pyqtSignal()  # Correct - class level

    def __init__(self):
        super().__init__()
        # NOT here!
```

### Unicode/Emoji Crashes
**Problem:** Application crashes with Unicode characters in buttons
**Solution:** Use plain text only, no emoji in UI elements

### Button Width Toggle
**Problem:** Buttons change width when text changes
**Solution:** Use fixed width (96px) for toggle buttons (Activeren/Deactiveren)

### Admin in Calendars
**Problem:** Admin account appears in user calendars
**Solution:** Filter with `WHERE gebruikersnaam != 'admin'`

### Calendar Widget Columns (v0.6.9)
**Problem:** Right column (Sunday) partially cut off in QCalendarWidget
**Solution:** Set minimum width and item sizes:
```python
calendar.setMinimumWidth(300)
calendar.setStyleSheet("""
    QAbstractItemView::item {
        min-width: 36px;
        max-width: 36px;
        min-height: 28px;
    }
""")
```

### Theme Switching (v0.6.9)
**Problem:** Widget styles don't update when theme changes
**Solution:** Dashboard rebuild strategy:
```python
# In main.py
def rebuild_dashboard(self):
    """Rebuild dashboard met huidige theme"""
    current = self.stack.currentWidget()
    if current:
        self.stack.removeWidget(current)
        current.deleteLater()
    self.show_dashboard()
```
**Note:** Theme toggle only available in dashboard. Other screens automatically use selected theme on load.

### Multiscreen Setup (v0.6.15)
**Problem:** Window spreads across multiple monitors in multiscreen setups
**Solution:** Use `maximize_on_primary_screen()` instead of `showMaximized()`:
```python
def maximize_on_primary_screen(self) -> None:
    """Maximaliseer window op primair scherm (multiscreen compatible)"""
    primary_screen = QApplication.primaryScreen()
    if not primary_screen:
        self.showMaximized()  # Fallback
        return

    screen_geometry = primary_screen.availableGeometry()
    self.setGeometry(screen_geometry)
    self.showNormal()  # Prevent multi-screen spread
```
**Note:** `showMaximized()` behavior is OS and configuration dependent on multiscreen setups. Using `primaryScreen().availableGeometry()` ensures window stays on primary screen.

## Database Migrations

When schema changes are needed:
1. Create a migration script (e.g., `migrate_*.py`)
2. Check if migration already applied using `PRAGMA table_info(table_name)`
3. Apply changes safely with transaction handling
4. Update `database/connection.py` seed functions for clean installs
5. Test both migration path AND clean install path

**Example migration check:**
```python
cursor.execute("PRAGMA table_info(typetabel_versies)")
columns = [row[1] for row in cursor.fetchall()]
if 'versie_naam' not in columns:
    # Apply migration
```

## Key Files Reference

**Entry Points:**
- `main.py` - Application entry point
- `database/connection.py` - Database initialization and schema

**Core Screens:**
- `gui/screens/dashboard_screen.py` - Main menu with role-based tabs (theme toggle v0.6.9)
- `gui/screens/planning_editor_screen.py` - Schedule editor (auto-generatie v0.6.14, concept/gepubliceerd v0.6.15)
- `gui/screens/typetabel_beheer_screen.py` - Template management (v0.6.6)
- `gui/screens/gebruikersbeheer_screen.py` - User management
- `gui/screens/werkpost_koppeling_screen.py` - User-to-werkpost mapping grid (v0.6.14: NIEUW)
- `gui/screens/verlof_aanvragen_screen.py` - Leave requests (saldo widget + layout fixes v0.6.10)
- `gui/screens/verlof_goedkeuring_screen.py` - Leave approval (type selection v0.6.10)
- `gui/screens/verlof_saldo_beheer_screen.py` - Leave balance management (v0.6.10)
- `gui/screens/rode_lijnen_beheer_screen.py` - HR cycles config (v0.6.8)

**Reusable Components:**
- `gui/widgets/grid_kalender_base.py` - Base calendar widget (filter preservation v0.6.15, alleen_gepubliceerd parameter v0.6.15)
- `gui/widgets/planner_grid_kalender.py` - Planner calendar view (feestdagen extended + rode lijnen v0.6.9, maand_changed signal v0.6.15)
- `gui/widgets/teamlid_grid_kalender.py` - Teamlid calendar view (rode lijnen v0.6.9, gepubliceerd filter v0.6.15)
- `gui/widgets/verlof_saldo_widget.py` - Leave balance display widget (v0.6.10)
- `gui/widgets/theme_toggle_widget.py` - Theme toggle component (v0.6.9)
- `gui/styles.py` - All styling constants (ThemeManager + dynamic Colors v0.6.9)

**Dialogs:**
- `gui/dialogs/auto_generatie_dialog.py` - Auto-generate planning from typetabel (v0.6.14: NIEUW)
- `gui/dialogs/verlof_saldo_bewerken_dialog.py` - Edit user leave balance (v0.6.10)

**Documentation:**
- `PROJECT_INFO.md` - User-facing documentation
- `DEVELOPMENT_GUIDE.md` - Technical architecture details (~1000 lines)
- `DEV_NOTES.md` - Development log and session notes
- `proposed_improvements.md` - Pragmatic code quality improvement plan

## Roadmap

**For v1.0 (December 2025):**
- Typetabel activation flow with validation
- HR rules management UI
- Complete planning editor (bulk operaties, validatie feedback) ← concept/gepubliceerd ✅ compleet in v0.6.15
- Validation system with visual feedback
- Export functionality (Excel to HR)
- .EXE build for deployment

**Known Limitations:**
- Network latency when database on network drive
- Typetabel activation not yet implemented (next priority)
- Theme toggle only available in dashboard (v0.6.9)
- QCalendarWidget behouden light mode styling (Qt limitation v0.6.9)
- Geen automatische cleanup overgedragen verlof op 1 mei (v0.6.10)

**v0.6.17 Features Completed:**
- ✅ Multi-Cell Selectie Systeem - Bulk operaties in Planning Editor
  - **Cel Selectie:** Ctrl+Click (individueel), Shift+Click (rectangle range)
  - **Visuele feedback:** Lichtblauwe gradient overlay op geselecteerde cellen
  - **Status label:** "X cellen geselecteerd (ESC om te wissen)" (witte achtergrond)
  - **Bulk Wissen:** Context menu "Wis Selectie" met bescherming speciale codes
  - **Bulk Invullen:** Context menu "Vul Selectie In..." met code validatie
  - **Notities behoud:** Notities ALTIJD behouden bij bulk operaties
  - **Gepubliceerde maand blokkering:** Duidelijke waarschuwing + cel reset
- ✅ Status Visualisatie Verbeteringen - Duidelijke concept/gepubliceerd indicatie
  - **8px gekleurde rand:** Geel (#FFE082) voor concept, groen (#81C784) voor gepubliceerd
  - **Border frame:** Hele scherm omlijst met status kleur
  - **Info box relocatie:** Naast maandnaam ipv aparte toolbar rij
- ✅ Planning Editor Layout Optimalisatie - Meer verticale ruimte
  - **Compacte header:** Knoppen op info label regel (Auto-Genereren, Wis Maand, Publiceren)
  - **Kalender header geïntegreerd:** Maandnaam + navigatie op 1 rij met info box
  - **Tooltip alleen onderaan:** Dubbele tooltip verwijderd
  - **Verticale ruimte:** 2 rijen gewonnen voor toekomstige HR features
- ✅ ESC Key Handler - Focus management voor keyboard shortcuts
- ✅ Gepubliceerde Maand Bescherming - Preventie user errors
  - Blokkering: cel edit, bulk delete, bulk fill, vul week, notitie edit
  - Duidelijke error: "Zet eerst terug naar concept via Planning Editor"

**v0.6.16 Features Completed:**
- ✅ Notitie naar Planner - Bidirectionele communicatie teamleden ↔ planner
  - Menu knop "Notitie naar Planner" in Mijn Planning tab (teamleden)
  - NotitieNaarPlannerDialog met datum selectie + tekst editor
  - Automatische opslag in planning tabel bij juiste persoon
  - Groen hoekje indicator verschijnt automatisch in grid
- ✅ Naam Prefix voor Notities - Traceerbaarheid
  - Teamlid notities: `[Naam]: tekst`
  - Planner notities: `[Planner]: tekst`
  - Slimme logica: bestaande prefix niet overschrijven
- ✅ Notitie Indicator Kleur Verbetering
  - #17a2b8 (teal) → #00E676 (Material Design bright green)
  - 70% beter zichtbaar
- ✅ Database Versie Fix
  - upgrade_to_v0_6_16.py voor versie synchronisatie
  - Documentatie: migratie best practices (db_metadata update verplicht)
  - test_migratie.py uitgebreid voor diagnose

**v0.6.15 Features Completed:**
- ✅ Concept vs Gepubliceerd Toggle - Volledig status management systeem
  - Planning status per maand (concept = verborgen, gepubliceerd = zichtbaar)
  - Teamleden zien ALLEEN gepubliceerde planning
  - Planners kunnen altijd wijzigen (ook na publicatie)
  - Dynamische UI met visuele indicatoren (geel/groen info boxes)
  - Bevestiging dialogs bij status wijziging
- ✅ Feestdag specifieke error messages in Planning Editor
- ✅ Filter state preservation bij maand navigatie (smart merge logica)
- ✅ Rode lijnen auto-regeneratie na config wijziging
- ✅ Naam kolom verbreed naar 280px voor lange namen
- ✅ Bug fixes: 5 commits (49d6886, a2f6025, b51c24e, 4e3e435, 377d2c6)

**v0.6.14 Features Completed:**
- ✅ Werkpost Koppeling systeem (many-to-many gebruikers ↔ werkposten)
- ✅ Slimme auto-generatie: typetabel "V" → shift_codes "7101" lookup
- ✅ Multi-post support met prioriteit fallback
- ✅ UI: Grid met checkboxes, filters (naam + reserves)
- ✅ Bescherming speciale codes en handmatige wijzigingen
- ✅ Bug fix: nieuwe werkpost reset_12u standaard uit
- ✅ Database: gebruiker_werkposten tabel + migratie script

**v0.6.10 Features Completed:**
- ✅ Complete verlof & KD saldo tracking systeem
- ✅ Admin: contingent input, overdracht management, nieuw jaar bulk aanmaken
- ✅ Teamlid: saldo widget in verlof aanvragen scherm
- ✅ Planner: type selectie (VV/KD) bij goedkeuring met saldo preview
- ✅ Auto-sync saldo na goedkeuring
- ✅ Term-based queries voor code-onafhankelijk systeem
- ✅ UI/UX: "t/m:" label, specifieke overdracht teksten, compactere layouts

**v0.6.9 Features Completed:**
- ✅ Dark mode with theme toggle
- ✅ Rode lijnen visualisatie in grid kalenders
- ✅ Feestdagen extended loading (3 years)
- ✅ Calendar widget column fix