# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Planning Tool** - A shift scheduling application for self-rostering teams, built with Python and PyQt6. The application manages team schedules, leave requests, shift codes, and schedule templates (typetabellen) for shift-based work environments.

**Current Version:** 0.6.7 (Beta)
**Status:** Active development - Term-based system for special codes

## Running the Application

```bash
# Run the application
python main.py

# Run database migrations (if upgrading)
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
- `gebruikers` - Users with UUID-based identification
- `typetabel_versies` + `typetabel_data` - Versioned schedule templates (v0.6.6)
- `werkposten` + `shift_codes` - Team-specific shift codes
- `speciale_codes` - Global codes with optional term field (v0.6.7)
  - System codes: verlof, zondagrust, zaterdagrust, ziek, arbeidsduurverkorting
  - Free codes: VD, RDS, TCR, SCR, T, etc.
- `planning` - Daily schedule assignments
- `verlof_aanvragen` - Leave requests with approval workflow
- `feestdagen` - Holidays (fixed and variable)
- `rode_lijnen` - 28-day HR cycles

### GUI Layer (PyQt6)
- **Entry point:** `main.py` with QStackedWidget for screen navigation
- **Screens:** Located in `gui/screens/` - full-page views
- **Dialogs:** Located in `gui/dialogs/` - modal dialogs
- **Widgets:** Located in `gui/widgets/` - reusable components
- **Styling:** Centralized in `gui/styles.py` (Styles, Colors, Fonts, Dimensions)

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
   - **System codes** (protected): verlof, zondagrust, zaterdagrust, ziek, arbeidsduurverkorting
   - **Free codes**: VD, RDS, TCR, SCR, T, etc.
   - Codes can be renamed (VV→VL) but terms are fixed
   - System uses TermCodeService for dynamic lookups

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
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig

# Buttons
btn.setStyleSheet(Styles.button_primary())
btn.setFixedHeight(Dimensions.BUTTON_HEIGHT)

# Input fields
input.setStyleSheet(Styles.input_field())

# Tables
TableConfig.setup_table_widget(table, row_height=50)
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
- `gui/screens/dashboard_screen.py` - Main menu with role-based tabs
- `gui/screens/planning_editor_screen.py` - Schedule editor
- `gui/screens/typetabel_beheer_screen.py` - Template management (v0.6.6)
- `gui/screens/gebruikersbeheer_screen.py` - User management

**Reusable Components:**
- `gui/widgets/grid_kalender_base.py` - Base calendar widget
- `gui/widgets/planner_grid_kalender.py` - Planner calendar view
- `gui/styles.py` - All styling constants

**Documentation:**
- `PROJECT_INFO.md` - User-facing documentation
- `DEVELOPMENT_GUIDE.md` - Technical architecture details (~800 lines)
- `DEV_NOTES.md` - Development log and session notes

## Roadmap

**For v1.0 (December 2025):**
- Typetabel activation flow with validation
- HR rules management UI
- Complete planning editor with auto-generation
- Validation system with visual feedback
- Export functionality (Excel to HR)
- .EXE build for deployment

**Known Limitations:**
- Network latency when database on network drive
- Filter state resets on month navigation in calendars
- Typetabel activation not yet implemented (next priority)