# DEVELOPMENT GUIDE
Planning Tool - Technische Documentatie voor Ontwikkelaars

## VERSIE INFORMATIE
**Huidige versie:** 0.6.9 (Beta)
**Laatste update:** 20 Oktober 2025

---

## NIEUWE FEATURES IN 0.6.9

### Bug Fix: Calendar Widget Kolom Weergave
Verlof aanvragen kalender toont nu correct alle 7 kolommen (zondag niet meer afgesneden).

**Fix:**
- `min-width: 36px` en `min-height: 28px` toegevoegd aan `QAbstractItemView::item`
- `setMinimumWidth(300)` voor gehele kalender widget
- Toegepast op beide start_datum en eind_datum kalenders

**Code:**
- `gui/screens/verlof_aanvragen_screen.py` - Calendar widget styling (regel 127-184, 197-254)

### Bug Fix: Feestdagen Niet Herkend in Grid Kalender
Feestdagen van vorig/volgend jaar worden nu correct geladen voor buffer dagen.

**Fix:**
- Nieuwe methode `load_feestdagen_extended()` laadt 3 jaren (vorig, huidig, volgend)
- Auto-generatie via `ensure_jaar_data()` service
- Toegepast op beide PlannerGridKalender en TeamlidGridKalender

**Code:**
- `gui/widgets/planner_grid_kalender.py` - load_feestdagen_extended() (regel 324-345)

### Dark Mode (Nachtmodus)
Volledige dark mode ondersteuning met visuele theme toggle in dashboard.

**Architectuur:**
- **ThemeManager class**: Singleton pattern voor theme state (`_current_theme`)
- **Colors class**: Dynamische palette met `_LIGHT_THEME` en `_DARK_THEME` dictionaries
- **ThemeToggleWidget**: Visuele component met zon/maan iconen en schuifknop
- **Dashboard rebuild**: Bij theme toggle wordt dashboard opnieuw opgebouwd voor correcte styling
- **Persistence**: Theme voorkeur opgeslagen in `data/theme_preference.json`

**Thema Kleuren:**
| Element | Light Mode | Dark Mode |
|---------|-----------|-----------|
| BG_WHITE | #ffffff | #1e1e1e |
| TEXT_PRIMARY | #212529 | #e0e0e0 |
| PRIMARY | #007bff | #4a9eff |
| BORDER_DARK | #dee2e6 | #3d4349 |
| TABLE_HEADER_BG | #f8f9fa | #2b3035 |
| MENU_BUTTON_BG | #ffffff | #2b3035 |

**Code:**
- `gui/styles.py` - ThemeManager en Colors classes (regel 8-103)
- `main.py` - Theme loading/saving/apply (regel 240-311)
- `gui/screens/dashboard_screen.py` - Theme toggle integratie (regel 98-120)
- `gui/widgets/theme_toggle_widget.py` - NIEUW bestand (volledige implementatie)
- `gui/dialogs/handleiding_dialog.py` - Theme toggle info (regel 95-106)

**Gebruik:**
```python
from gui.styles import ThemeManager, Colors

# Check huidige theme
current = ThemeManager.get_theme()  # 'light' of 'dark'

# Toggle theme
new_theme = ThemeManager.toggle_theme()

# Set theme
ThemeManager.set_theme('dark')

# Gebruik dynamische kleuren
background = Colors.BG_WHITE  # Past automatisch aan bij theme switch
```

**Bekende Beperkingen:**
- Theme toggle alleen beschikbaar in dashboard
- QCalendarWidget behouden light mode styling (Qt limitation)

### Rode Lijnen Visualisatie in Grid Kalenders
28-daagse HR cycli worden nu visueel weergegeven met rode verticale lijnen.

**Functionaliteit:**
- Dikke rode linker border (4px, #dc3545) markeert periode start
- Doorlopende lijn van datum header tot alle data cellen
- Tooltip toont periode nummer: "Start Rode Lijn Periode X"
- Dictionary lookup voor O(1) performance
- Timestamp stripping fix (2024-07-28T00:00:00 → 2024-07-28)

**Architectuur:**
- `load_rode_lijnen()` methode laadt alle periode start datums in dictionary
- `{datum_str: periode_nummer}` mapping voor snelle lookup
- Border styling wordt toegevoegd in `build_grid()` en `create_editable_cel()`/`create_shift_cel()`

**Code:**
- `gui/widgets/planner_grid_kalender.py`:
  - `load_rode_lijnen()` methode (regel 347-369)
  - `load_initial_data()` aanroep (regel 312)
  - `build_grid()` datum headers check (regel 414-453)
  - `create_editable_cel()` data cellen styling (regel 499-516)

- `gui/widgets/teamlid_grid_kalender.py`:
  - Import `get_connection` (regel 15)
  - `load_rode_lijnen()` methode (regel 139-161)
  - `load_initial_data()` aanroep (regel 124)
  - `build_grid()` datum headers check (regel 203-231)
  - `create_shift_cel()` data cellen styling (regel 270-284)

**Gebruik:**
```python
# In grid kalender widget
self.rode_lijnen_starts: Dict[str, int] = {}  # {datum_str: periode_nr}

# Check of datum start van periode is
is_rode_lijn_start = datum_str in self.rode_lijnen_starts

# Voeg rode border toe aan styling
if is_rode_lijn_start:
    periode_nr = self.rode_lijnen_starts[datum_str]
    style += "border-left: 4px solid #dc3545;"
    tooltip = f"Start Rode Lijn Periode {periode_nr}"
```

**Database Query:**
```sql
SELECT start_datum, eind_datum, periode_nummer
FROM rode_lijnen
ORDER BY start_datum
```

---

## NIEUWE FEATURES IN 0.6.8

### Rode Lijnen Config Beheer
Implementatie van versioned configuratie systeem voor HR cyclus (rode lijnen) met UI voor beheer.

**Nieuwe Bestanden:**
- `migratie_rode_lijnen_config.py` - Database migratie script
- `gui/screens/rode_lijnen_beheer_screen.py` - Beheer scherm
- `gui/dialogs/rode_lijnen_config_dialog.py` - Configuratie dialog

**Database Wijzigingen:**
- `rode_lijnen_config` tabel toegevoegd (start_datum, interval_dagen, actief_vanaf, actief_tot, is_actief)
- Versioned systeem zoals HR regels

**Code Wijzigingen:**
- `services/data_ensure_service.py` - Gebruikt nu config tabel ipv hardcoded waarden
- `database/connection.py` - Seed functie voor rode_lijnen_config

### UX Verbeteringen
**Window Management:**
- Auto-maximize na login (main.py:147)
- Centreren bij logout (main.py:174)

**Handleiding Systeem:**
- Tab-based handleiding met 3 tabs (gui/dialogs/handleiding_dialog.py)
- Globaal F1 shortcut (main.py:92)
- Handleiding knop op dashboard (gui/screens/dashboard_screen.py)

**Filter State Preservation:**
- Filter blijft behouden bij maand navigatie (gui/widgets/planner_grid_kalender.py:107, teamlid_grid_kalender.py:114)
- `_filter_initialized` flag pattern

**Layout Fixes:**
- Mijn Planning scherm HBoxLayout met codes sidebar (gui/screens/mijn_planning_screen.py:47)
- Grid stretching opgelost met stretch factors (3:1 ratio)

**Keyboard Shortcuts:**
- F1: Globale handleiding
- F2: Shift codes helper in Planning Editor (was F1)

---

## NIEUWE FEATURES IN 0.6.7

### Term-based Systeem voor Speciale Codes
Implementatie van flexibel systeem waarbij codes aangepast kunnen worden maar systeemfuncties beschermd blijven via termen.

**Nieuwe Bestanden:**
- `migratie_systeem_termen.py` - Database migratie script
- `services/term_code_service.py` - Term-to-code mapping met cache

**Database Wijzigingen:**
- `speciale_codes.term` kolom toegevoegd (nullable, unique index)
- 5 verplichte termen: verlof, zondagrust, zaterdagrust, ziek, arbeidsduurverkorting
- Codes kunnen wijzigen (VV→VL) maar termen blijven behouden

**Code Wijzigingen:**
- `shift_codes_screen.py` - Verwijder-knop disabled voor systeemcodes
- `verlof_goedkeuring_screen.py` - Gebruikt TermCodeService.get_code_for_term()
- `grid_kalender_base.py` - Dynamische kleuren op basis van termen
- `speciale_code_dialog.py` - Waarschuwing voor systeemcodes

**Bugfix:** Verlofcode (VV) kan niet meer per ongeluk verwijderd worden, waardoor verlofgoedkeuring altijd blijft werken.

---

## NIEUWE FEATURES IN 0.6.6

### Typetabel Beheer Systeem
Complete implementatie van versioned typetabel systeem met status lifecycle (Concept/Actief/Archief), flexibel aantal weken (1-52), en multi-post support via shift codes met post nummers (V1, V2, L1, L2, etc.).

**Nieuwe Bestanden:**
- `migrate_typetabel_versioned.py` - Database migratie script
- `gui/screens/typetabel_beheer_screen.py` - Hoofdscherm
- `gui/dialogs/typetabel_dialogs.py` - NieuweTypetabelDialog
- `gui/dialogs/typetabel_editor_dialog.py` - Grid editor

**Database Wijzigingen:**
- Nieuwe tabellen: `typetabel_versies`, `typetabel_data`
- Oude tabel wordt `typetabel_old_backup` na migratie
- `connection.py` seed functie aangepast

---

## INHOUDSOPGAVE
1. [Technische Architectuur](#technische-architectuur)
2. [Database Schema](#database-schema)
3. [PyQt6 Best Practices](#pyqt6-best-practices)
4. [Typetabel Systeem](#typetabel-systeem)
5. [Shift Codes Systeem](#shift-codes-systeem)
6. [Known Issues](#known-issues)
7. [Code Templates](#code-templates)
8. [Dashboard & Main.py](#dashboard--mainpy)

---

## TECHNISCHE ARCHITECTUUR

### Stack
- **Database**: SQLite (data/planning.db)
  - Foreign keys enabled
  - Row factory voor dict access
  - UUID voor gebruikers
  - Timestamps voor audit trails
  - CASCADE delete voor relaties

- **GUI Framework**: PyQt6
  - Signal/Slot voor navigatie
  - QStackedWidget voor scherm wisseling
  - Centrale styling via `gui/styles.py`
  - Unicode emoji's vermeden (Windows compatibility)

- **Services**: Business logic gescheiden van GUI

### Project Structuur
```
root/
├── database/
│   ├── connection.py          # DB init & seed
│   └── __init__.py
├── gui/
│   ├── styles.py              # Centrale styling
│   ├── dialogs/               # Alle dialogs
│   ├── screens/               # Alle schermen
│   └── widgets/               # Herbruikbare widgets
├── services/
│   ├── data_ensure_service.py     # Auto-generatie
│   └── term_code_service.py       # Term-code mapping (v0.6.7)
├── data/
│   └── planning.db
├── migratie_systeem_termen.py      # v0.6.7
├── migrate_typetabel_versioned.py  # v0.6.6
├── main.py
└── config.py
```

### Styling Systeem
Gebruik ALTIJD centrale styling:
```python
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig

btn.setStyleSheet(Styles.button_primary())
TableConfig.setup_table_widget(self.tabel, row_height=50)
input.setStyleSheet(Styles.input_field())
```

---

## DATABASE SCHEMA

### Typetabel Systeem (v0.6.6)

#### typetabel_versies
```sql
CREATE TABLE typetabel_versies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    versie_naam TEXT NOT NULL,
    aantal_weken INTEGER NOT NULL,
    status TEXT CHECK (status IN ('actief', 'concept', 'archief')),
    actief_vanaf DATE,
    actief_tot DATE,
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    laatste_wijziging TIMESTAMP,
    opmerking TEXT
)
```

**Status Lifecycle:**
- **concept**: Voor trial & error, meerdere mogelijk
- **actief**: Huidig in gebruik, altijd exact 1
- **archief**: Oude versies, geschiedenis

#### typetabel_data
```sql
CREATE TABLE typetabel_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    versie_id INTEGER NOT NULL,
    week_nummer INTEGER NOT NULL,      -- 1 tot aantal_weken
    dag_nummer INTEGER NOT NULL,       -- 1-7 (Ma-Zo)
    shift_type TEXT,                   -- V1, L2, N, RX, etc.
    UNIQUE(versie_id, week_nummer, dag_nummer),
    FOREIGN KEY (versie_id) REFERENCES typetabel_versies(id) ON DELETE CASCADE
)
```

### Gebruikers
```sql
CREATE TABLE gebruikers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gebruiker_uuid TEXT UNIQUE NOT NULL,
    gebruikersnaam TEXT UNIQUE NOT NULL,
    wachtwoord_hash BLOB NOT NULL,
    volledige_naam TEXT NOT NULL,
    rol TEXT CHECK(rol IN ('planner', 'teamlid')),
    is_reserve BOOLEAN DEFAULT 0,
    startweek_typedienst INTEGER,      -- 1 tot aantal_weken actieve typetabel
    is_actief BOOLEAN DEFAULT 1,
    aangemaakt_op TIMESTAMP,
    gedeactiveerd_op TIMESTAMP,
    laatste_login TIMESTAMP
)
```

### Werkposten & Shift Codes (v0.6.4)

#### werkposten
```sql
CREATE TABLE werkposten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT UNIQUE NOT NULL,
    beschrijving TEXT,
    telt_als_werkdag BOOLEAN DEFAULT 1,
    reset_12u_rust BOOLEAN DEFAULT 1,
    breekt_werk_reeks BOOLEAN DEFAULT 0,
    is_actief BOOLEAN DEFAULT 1,
    aangemaakt_op TIMESTAMP,
    gedeactiveerd_op TIMESTAMP
)
```

#### shift_codes
```sql
CREATE TABLE shift_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    werkpost_id INTEGER NOT NULL,
    dag_type TEXT CHECK(dag_type IN ('weekdag', 'zaterdag', 'zondag')),
    shift_type TEXT CHECK(shift_type IN ('vroeg', 'laat', 'nacht', 'dag')),
    code TEXT NOT NULL,
    start_uur TEXT NOT NULL,           -- HH:MM
    eind_uur TEXT NOT NULL,            -- HH:MM
    FOREIGN KEY (werkpost_id) REFERENCES werkposten(id),
    UNIQUE(werkpost_id, dag_type, shift_type)
)
```

#### speciale_codes
```sql
CREATE TABLE speciale_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,         -- VV, RX, DA, etc.
    naam TEXT NOT NULL,
    telt_als_werkdag BOOLEAN DEFAULT 1,
    reset_12u_rust BOOLEAN DEFAULT 1,
    breekt_werk_reeks BOOLEAN DEFAULT 0
)
```

### Planning & Verlof

#### planning
```sql
CREATE TABLE planning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gebruiker_id INTEGER NOT NULL,
    datum TEXT NOT NULL,
    shift_code TEXT,
    status TEXT DEFAULT 'concept' CHECK(status IN ('concept', 'gepubliceerd')),
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id),
    UNIQUE(gebruiker_id, datum)
)
```

#### verlof_aanvragen
```sql
CREATE TABLE verlof_aanvragen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gebruiker_id INTEGER NOT NULL,
    start_datum DATE NOT NULL,
    eind_datum DATE NOT NULL,
    aantal_dagen INTEGER NOT NULL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'goedgekeurd', 'geweigerd')),
    opmerking TEXT,
    aangevraagd_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    behandeld_door INTEGER,
    behandeld_op TIMESTAMP,
    reden_weigering TEXT,
    FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id),
    FOREIGN KEY (behandeld_door) REFERENCES gebruikers(id)
)
```

### HR Regels & Rode Lijnen (v0.6.8)

#### hr_regels
```sql
CREATE TABLE hr_regels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT UNIQUE NOT NULL,
    waarde REAL NOT NULL,
    eenheid TEXT NOT NULL,
    beschrijving TEXT,
    actief_vanaf TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actief_tot TIMESTAMP,
    is_actief BOOLEAN DEFAULT 1
)
```

**Versioning Pattern:**
- `actief_vanaf`: Wanneer regel actief wordt
- `actief_tot`: Wanneer regel niet meer actief is (nullable)
- `is_actief`: Huidige status (1=actief, 0=archief)

#### rode_lijnen_config
```sql
CREATE TABLE rode_lijnen_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_datum DATE NOT NULL,
    interval_dagen INTEGER NOT NULL,
    actief_vanaf TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actief_tot TIMESTAMP,
    is_actief BOOLEAN DEFAULT 1
)
```

**Data Ensure Service:**
- `data_ensure_service.py` haalt actieve config uit tabel
- Genereert rode_lijnen tabel op basis van config
- Uitbreidbaar naar toekomst met `extend_rode_lijnen_tot()`

### Overige Tabellen

#### feestdagen
```sql
CREATE TABLE feestdagen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datum DATE NOT NULL UNIQUE,
    naam TEXT NOT NULL,
    is_zondagsrust BOOLEAN DEFAULT 1,
    is_variabel BOOLEAN DEFAULT 0       -- 0=vast, 1=variabel/extra
)
```

#### rode_lijnen
```sql
CREATE TABLE rode_lijnen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_datum DATE NOT NULL UNIQUE,
    eind_datum DATE NOT NULL,
    periode_nummer INTEGER NOT NULL
)
```

**Generatie:**
- Automatisch gegenereerd via `data_ensure_service.py`
- Gebruikt config uit `rode_lijnen_config` tabel
- Uitbreidbaar naar toekomst met configurable interval

### Database Migraties

**v0.6.8 - Rode Lijnen Config:**
```bash
python migratie_rode_lijnen_config.py
```

**Wat doet het:**
1. Check of rode_lijnen_config tabel al bestaat
2. Maak tabel met versioning columns
3. Seed default config (2024-07-28, interval 28 dagen)
4. Safe & idempotent

**v0.6.7 - Term-based Systeem:**
```bash
python migratie_systeem_termen.py
```

**v0.6.6 - Typetabel Versioned:**
```bash
python migrate_typetabel_versioned.py
```

**Wat doet het:**
1. Check of nieuwe tabellen al bestaan
2. Maak `typetabel_versies` en `typetabel_data`
3. Migreer oude `typetabel` data
4. Hernoem oude naar `typetabel_old_backup`
5. Safe & idempotent (kan meerdere keren)

**Voor schone database:**
- `connection.py` seed is bijgewerkt
- Maakt automatisch versioned structuur aan

---

## PYQT6 BEST PRACTICES

### 1. Signals als Class Attributes

✅ **CORRECT:**
```python
class MyWidget(QWidget):
    my_signal: pyqtSignal = pyqtSignal()
    data_signal: pyqtSignal = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
```

❌ **FOUT:**
```python
class MyWidget(QWidget):
    def __init__(self):
        self.my_signal = pyqtSignal()  # WERKT NIET!
```

**Type ignore bij connect/emit:**
```python
self.my_signal.connect(self.handler)  # type: ignore
self.my_signal.emit()  # type: ignore
```

### 2. Instance Attributes in `__init__`

✅ **CORRECT:**
```python
class MyScreen(QWidget):
    def __init__(self):
        super().__init__()
        # Declareer ALLE attributes hier
        self.tabel: QTableWidget = QTableWidget()
        self.data: List[Dict[str, Any]] = []
        self.init_ui()
```

### 3. Unicode/Emoji's VERMIJDEN

❌ **VERMIJD:**
```python
btn.setText("✅ Opslaan")  # Crasht op Windows!
```

✅ **GEBRUIK:**
```python
btn.setText("Opslaan")
lbl.setText("Status: Actief")
```

### 4. Button Widths in Tabellen

✅ **CORRECT:**
```python
# Toggle button ALTIJD zelfde width
if actief:
    toggle_btn = QPushButton("Deactiveren")
else:
    toggle_btn = QPushButton("Activeren")

toggle_btn.setFixedWidth(96)  # ALTIJD 96px!
toggle_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
toggle_btn.setStyleSheet(Styles.button_warning(Dimensions.BUTTON_HEIGHT_TINY))
```

### 5. Router Pattern voor Navigatie

```python
class MyScreen(QWidget):
    def __init__(self, router: Callable):
        super().__init__()
        self.router = router
        
        terug_btn = QPushButton("Terug")
        terug_btn.clicked.connect(self.router)  # type: ignore
```

### 6. Exception Handling

✅ **SPECIFIEK:**
```python
try:
    database_operatie()
except sqlite3.IntegrityError:
    QMessageBox.warning(self, "Fout", "Deze waarde bestaat al!")
except sqlite3.Error as e:
    QMessageBox.critical(self, "Database Fout", str(e))
```

❌ **TE BREED:**
```python
except Exception as e:  # Te algemeen!
```

---

## TYPETABEL SYSTEEM

### Concept & Gebruik

**Typetabel = Herhalend patroon:**
- X weken lang (1-52 configureerbaar)
- Personen krijgen startweek 1-X
- Patroon herhaalt automatisch
- Multi-post via codes (V1, V2, L1, etc.)

**Voorbeeld 6-weken:**
```
Week 1: V, V, RX, L, L, CX, RX
Week 2: L, L, RX, N, N, CX, RX
Week 3: N, N, RX, V, V, CX, RX
...
Week 7 = Week 1 (herhaalt)
```

**Multi-Post Voorbeeld (Officieren):**
```
Week 1: V1, V1, RX, L2, L2, CX, RX
Week 2: L1, L1, RX, N1, N1, CX, RX

Waarbij:
V1 = Vroeg Post 1
V2 = Vroeg Post 2
L1 = Laat Post 1
L2 = Laat Post 2
N1 = Nacht Post 1
```

### Database Operations

**Nieuwe typetabel maken:**
```python
cursor.execute("""
    INSERT INTO typetabel_versies 
    (versie_naam, aantal_weken, status, laatste_wijziging)
    VALUES (?, ?, 'concept', ?)
""", (naam, aantal_weken, datetime.now().isoformat()))

versie_id = cursor.lastrowid

# Initialiseer lege data
for week in range(1, aantal_weken + 1):
    for dag in range(1, 8):
        cursor.execute("""
            INSERT INTO typetabel_data 
            (versie_id, week_nummer, dag_nummer, shift_type)
            VALUES (?, ?, ?, NULL)
        """, (versie_id, week, dag))
```

**Kopiëren:**
```python
# Maak nieuwe versie
cursor.execute("""
    INSERT INTO typetabel_versies (versie_naam, aantal_weken, status, ...)
    VALUES (?, ?, 'concept', ...)
""", (...))

nieuwe_id = cursor.lastrowid

# Kopieer data
cursor.execute("""
    INSERT INTO typetabel_data (versie_id, week_nummer, dag_nummer, shift_type)
    SELECT ?, week_nummer, dag_nummer, shift_type
    FROM typetabel_data
    WHERE versie_id = ?
""", (nieuwe_id, oude_versie_id))
```

**Activeren (TODO - Volgende sessie):**
```python
# Transactie voor atomaire operatie
cursor.execute("BEGIN TRANSACTION")
try:
    # Oud actief → archief
    cursor.execute("""
        UPDATE typetabel_versies
        SET status = 'archief', actief_tot = ?
        WHERE status = 'actief'
    """, (startdatum,))
    
    # Nieuw → actief
    cursor.execute("""
        UPDATE typetabel_versies
        SET status = 'actief', actief_vanaf = ?
        WHERE id = ?
    """, (startdatum, versie_id))
    
    cursor.execute("COMMIT")
except:
    cursor.execute("ROLLBACK")
    raise
```

### Auto-Generatie uit Typetabel (TODO)

```python
def genereer_shift_voor_datum(gebruiker_id: int, datum: str) -> Optional[str]:
    """Genereer shift code o.b.v. actieve typetabel"""
    
    # Haal gebruiker startweek op
    cursor.execute("""
        SELECT startweek_typedienst FROM gebruikers WHERE id = ?
    """, (gebruiker_id,))
    startweek = cursor.fetchone()['startweek_typedienst']
    
    # Haal actieve typetabel op
    cursor.execute("""
        SELECT id, aantal_weken, actief_vanaf
        FROM typetabel_versies WHERE status = 'actief'
    """)
    typetabel = cursor.fetchone()
    
    # Bereken week in cyclus
    datum_obj = datetime.fromisoformat(datum)
    actief_vanaf = datetime.fromisoformat(typetabel['actief_vanaf'])
    dagen_verschil = (datum_obj - actief_vanaf).days
    
    # Met startweek offset
    week_in_cyclus = ((dagen_verschil // 7 + startweek - 1) % typetabel['aantal_weken']) + 1
    dag_nummer = datum_obj.isoweekday()
    
    # Haal shift code op
    cursor.execute("""
        SELECT shift_type FROM typetabel_data
        WHERE versie_id = ? AND week_nummer = ? AND dag_nummer = ?
    """, (typetabel['id'], week_in_cyclus, dag_nummer))
    
    result = cursor.fetchone()
    return result['shift_type'] if result else None
```

### Integratie met GebruikersBeheer (TODO)

```python
def get_max_startweek() -> int:
    """Haal max startweek uit actieve typetabel"""
    cursor.execute("""
        SELECT aantal_weken FROM typetabel_versies WHERE status = 'actief'
    """)
    result = cursor.fetchone()
    return result['aantal_weken'] if result else 6

# Bij gebruiker bewerken
max_week = get_max_startweek()
startweek_spin.setMaximum(max_week)
startweek_label.setText(f"Startweek (1-{max_week}):")
```

---

## SHIFT CODES SYSTEEM

### Architectuur (v0.6.4, updated v0.6.7)

Twee-laags systeem:
1. **Werkposten**: Team-specifieke shift codes
2. **Speciale Codes**: Globale codes met term-based systeem (v0.6.7)

### Term-based Systeem (v0.6.7)

Speciale codes hebben nu een optioneel `term` veld voor systeemfuncties:

**Database structuur:**
```sql
CREATE TABLE speciale_codes (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,     -- Kan wijzigen (VV → VL)
    naam TEXT NOT NULL,
    term TEXT UNIQUE,               -- Fixed (verlof, zondagrust, etc.)
    telt_als_werkdag BOOLEAN,
    reset_12u_rust BOOLEAN,
    breekt_werk_reeks BOOLEAN
);
```

**Verplichte termen (beschermd):**
- `verlof` - Gebruikt bij verlof goedkeuring
- `zondagrust` - Gebruikt voor RX regels
- `zaterdagrust` - Gebruikt voor CX regels
- `ziek` - Gebruikt voor ziekteregistratie
- `arbeidsduurverkorting` - Gebruikt voor ADV

**TermCodeService:**
```python
from services.term_code_service import TermCodeService

# Haal code op voor term (met fallback)
verlof_code = TermCodeService.get_code_for_term('verlof')
# Returns: 'VV' (of 'VL' als gebruiker dit heeft aangepast)

# Cache refresh na wijzigingen
TermCodeService.refresh()
```

**Gebruikersflow:**
1. Gebruiker kan VV bewerken naar VL (code wijzigt)
2. Term 'verlof' blijft gekoppeld
3. Bij verlof goedkeuren gebruikt systeem automatisch VL
4. Verwijderen geblokkeerd: term moet blijven bestaan

### Tijd Notatie Parsing

Flexibele parser accepteert:
```python
"6-14"        → "06:00" tot "14:00"  # Hele uren shortcut
"06:00-14:00" → "06:00" tot "14:00"  # Volledig
"06:30-14:30" → "06:30" tot "14:30"  # Halve uren
"14:15-22:45" → "14:15" tot "22:45"  # Kwartieren
"22:00-06:00" → "22:00" tot "06:00"  # Over middernacht
```

**Implementatie:**
```python
def parse_tijd(tijd_str: str) -> Tuple[str, str]:
    tijd_clean = tijd_str.replace(' ', '')
    parts = tijd_clean.split('-')
    
    # Parse start
    if ':' in parts[0]:
        start_parts = parts[0].split(':')
        start_uur = f"{start_parts[0].zfill(2)}:{start_parts[1].zfill(2)}"
    else:
        start_uur = f"{parts[0].zfill(2)}:00"
    
    # Parse eind (zelfde logica)
    if ':' in parts[1]:
        eind_parts = parts[1].split(':')
        eind_uur = f"{eind_parts[0].zfill(2)}:{eind_parts[1].zfill(2)}"
    else:
        eind_uur = f"{parts[1].zfill(2)}:00"
    
    return start_uur, eind_uur
```

### Code Eigenschappen

**Op werkpost niveau (gelden voor alle shifts):**
- `telt_als_werkdag`: Telt mee voor 19 dagen/28d regel
- `reset_12u_rust`: Reset de 12u rust periode
- `breekt_werk_reeks`: Breekt reeks werkdagen

**Voorbeeld combinaties:**
```python
# VV - Verlof
telt_als_werkdag=1, reset_12u=1, breekt=0

# RX - Zondagsrust
telt_als_werkdag=0, reset_12u=0, breekt=1

# Z - Ziek
telt_als_werkdag=0, reset_12u=1, breekt=1
```

---

## KNOWN ISSUES

### ✅ OPGELOST

**Filter State Reset (v0.6.8)** 🆕
- **Probleem:** Filter verdween bij maand navigatie in kalenders
- **Fix:** `_filter_initialized` flag pattern
- **Impact:** Filter blijft behouden bij navigatie
- **Locaties:** planner_grid_kalender.py:107, teamlid_grid_kalender.py:114

**Grid Stretching Full-screen (v0.6.8)** 🆕
- **Probleem:** Grid werd uitgerekt met witruimte op full-screen
- **Fix:** HBoxLayout met stretch factors (3:1 ratio) + codes sidebar
- **Locatie:** mijn_planning_screen.py:47

**F1 Shortcut Conflict (v0.6.8)** 🆕
- **Probleem:** F1 in Planning Editor botste met globale handleiding
- **Fix:** Shift codes helper verplaatst naar F2
- **Locatie:** planning_editor_screen.py:300

**Verlofcode Verwijderbaar (v0.6.7)**
- **Probleem:** VV kon verwijderd worden, verlofgoedkeuring crashte daarna
- **Fix:** Term-based systeem met beschermde codes
- **Impact:** Systeemcodes (verlof, zondagrust, etc.) zijn nu beschermd
- **Locaties:** shift_codes_screen.py, verlof_goedkeuring_screen.py, term_code_service.py

**Typetabel Seed Conflict (v0.6.6)**
- **Fix:** connection.py seed aangepast voor versioned systeem
- **Impact:** Schone database start werkt correct

**Admin in Kalenders (v0.6.4)**
- **Fix:** `WHERE gebruikersnaam != 'admin'` filter
- **Locatie:** grid_kalender_base.py

**Button Width Toggle (v0.6.4)**
- **Fix:** Uniform 96px voor Activeren/Deactiveren
- **Locaties:** gebruikersbeheer_screen.py, shift_codes_screen.py

### 🟡 BEKEND

**Netwerklatency**
- **Probleem:** Trage DB toegang op netwerkschijf
- **Impact:** Lichte vertraging bij opstarten
- **Workaround:** Database caching overwegen

---

## CODE TEMPLATES

### Nieuw Scherm (Skeleton)

```python
from typing import Callable, List, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from database.connection import get_connection
from gui.styles import Styles, Dimensions
import sqlite3

class MijnScherm(QWidget):
    def __init__(self, router: Callable):
        super().__init__()
        self.router = router
        self.data: List[Dict[str, Any]] = []
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        # Setup UI...
        
        terug_btn = QPushButton("Terug")
        terug_btn.clicked.connect(self.router)  # type: ignore
        layout.addWidget(terug_btn)
    
    def load_data(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
            self.data = cursor.fetchall()
            conn.close()
        except sqlite3.Error as e:
            # Handle error...
            pass
```

### Dialog (Skeleton)

```python
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLineEdit
from gui.styles import Styles

class MijnDialog(QDialog):
    def __init__(self, parent, data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.data = data
        self.setModal(True)
        self.input: QLineEdit = QLineEdit()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        # Setup UI...
        
        opslaan_btn = QPushButton("Opslaan")
        opslaan_btn.clicked.connect(self.accept)  # type: ignore
        layout.addWidget(opslaan_btn)
    
    def get_data(self) -> Dict[str, Any]:
        return {'field': self.input.text().strip()}
```

---

## DASHBOARD & MAIN.PY

### Signal Pattern

**Dashboard heeft signals:**
```python
class DashboardScreen(QWidget):
    # Signals als class attributes
    gebruikers_clicked = pyqtSignal()
    typedienst_clicked = pyqtSignal()  # Voor typetabel
    shift_codes_clicked = pyqtSignal()
    # etc...
```

**Main.py connect pattern:**
```python
def show_dashboard(self):
    dashboard = DashboardScreen(self.current_user)
    
    # Connect alle signals
    dashboard.typedienst_clicked.connect(self.on_typedienst_clicked)  # type: ignore
    # etc...
    
    self.stack.addWidget(dashboard)
    self.stack.setCurrentWidget(dashboard)

def on_typedienst_clicked(self):
    from gui.screens.typetabel_beheer_screen import TypetabelBeheerScreen
    scherm = TypetabelBeheerScreen(self.terug)
    self.stack.addWidget(scherm)
    self.stack.setCurrentWidget(scherm)
```

### Nieuwe Menu Item Toevoegen

**Stap 1:** Signal in dashboard:
```python
nieuw_scherm_clicked = pyqtSignal()
```

**Stap 2:** Button in create_XXX_tab():
```python
scroll_layout.addWidget(self.create_menu_button(
    "Nieuw Scherm",
    "Beschrijving van het scherm"
))
```

**Stap 3:** Handler in handle_menu_click():
```python
elif title == "Nieuw Scherm":
    self.nieuw_scherm_clicked.emit()
```

**Stap 4:** Connect in main.py:
```python
dashboard.nieuw_scherm_clicked.connect(self.on_nieuw_scherm_clicked)  # type: ignore
```

**Stap 5:** Handler implementeren:
```python
def on_nieuw_scherm_clicked(self):
    from gui.screens.nieuw_scherm import NieuwScherm
    scherm = NieuwScherm(self.terug)
    self.stack.addWidget(scherm)
    self.stack.setCurrentWidget(scherm)
```

---

## VERSIE GESCHIEDENIS

### v0.6.8 (19 Oktober 2025) - HUIDIG
**Rode Lijnen Config & UX Verbeteringen**
- Versioned rode lijnen configuratie beheer
- Auto-maximize window na login
- Tab-based handleiding systeem (F1)
- Filter state preservation bij navigatie
- Grid stretching fix + codes sidebar
- Keyboard shortcuts (F1/F2)
- Historiek standaard zichtbaar

### v0.6.7 (19 Oktober 2025)
**Term-based Systeem voor Speciale Codes**
- Systeemcodes beschermd tegen verwijdering
- TermCodeService met cache
- Dynamische code mapping via termen
- Database migratie + UI updates

### v0.6.6 (18 Oktober 2025)
**Typetabel Beheer Systeem**
- Versioned typetabellen (Concept/Actief/Archief)
- Grid editor voor patronen
- Kopiëren, verwijderen functionaliteit
- Database migratie + seed update
- Multi-post support (V1, V2, L1, etc.)

### v0.6.5 (16 Oktober 2025)
**Planning Editor & Verlof**
- Planning Editor eerste iteratie
- Editable cellen in kalender
- Verlof aanvragen/goedkeuring schermen

### v0.6.4 (15 Oktober 2025)
**Shift Codes Systeem**
- Werkposten met multi-team support
- Speciale codes beheer
- Flexibele tijd parsing
- Grid editor

### v0.6.3 (14 Oktober 2025)
**Feestdagen & Kalenders**
- Feestdagen verbeterd (variabel/vast)
- Paasberekening
- Grid Kalender widgets
- Database migratie systeem

### v0.6.0-0.6.2
- Login systeem
- Dashboard
- Gebruikersbeheer
- Database redesign
- Centrale styling

---

## DEPLOYMENT (TODO)

**Voor Release 1.0:**
- PyInstaller .exe build
- Netwerkschijf deployment guide
- Backup strategie
- Multi-user testing
- Performance optimalisatie

**Zie DEV_NOTES.md voor deployment checklist**

---

*Laatste update: 19 Oktober 2025*
*Versie: 0.6.8*

*Voor user-facing documentatie, zie PROJECT_INFO.md*
*Voor development logs, zie DEV_NOTES.md*