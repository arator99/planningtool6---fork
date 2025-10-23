# DEVELOPMENT GUIDE
Planning Tool - Technische Documentatie voor Ontwikkelaars

## VERSIE INFORMATIE
**Huidige versie:** 0.6.15 (Beta)
**Laatste update:** 23 Oktober 2025

---

## INHOUDSOPGAVE
1. [Versie Beheer Systeem](#versie-beheer-systeem-v0613)
2. [Technische Architectuur](#technische-architectuur)
3. [Database Schema](#database-schema)
4. [PyQt6 Best Practices](#pyqt6-best-practices)
5. [Typetabel Systeem](#typetabel-systeem)
6. [Shift Codes Systeem](#shift-codes-systeem)
7. [Design Beslissingen](#design-beslissingen)
8. [Known Issues](#known-issues)
9. [Code Templates](#code-templates)
10. [Dashboard & Main.py](#dashboard--mainpy)

---

## VERSIE BEHEER SYSTEEM (v0.6.13)

### Overzicht
Sinds v0.6.13 heeft de applicatie een centraal versiebeheersysteem:
- **APP_VERSION**: Verhoogt bij elke wijziging (GUI of DB)
- **MIN_DB_VERSION**: Verhoogt alleen bij DB schema wijzigingen
- **db_metadata tabel**: Slaat database versie op
- **Automatische compatibiliteit check**: Bij app startup

### Versie Update Checklist

**Voor ELKE wijziging:**
```python
# 1. Update config.py
APP_VERSION = "0.6.16"  # Altijd verhogen
```

**Bij DB schema wijzigingen:**
```python
# 1. Update beide versies in config.py
APP_VERSION = "0.6.16"
MIN_DB_VERSION = "0.6.16"  # Zelfde als APP_VERSION

# 2. Update connection.py
def create_tables(cursor):
    # Voeg nieuwe tabel/kolom toe

# 3. Maak upgrade script
# upgrade_to_v0_6_16.py

# 4. Update db_metadata
cursor.execute("""
    INSERT INTO db_metadata (version_number, migration_description)
    VALUES (?, ?)
""", ("0.6.16", "Beschrijving van wijziging"))
```

### Database Compatibiliteit
De app controleert bij startup of database compatibel is:
1. **Geen versie info** → Error: oude database, run upgrade script
2. **DB < MIN_DB_VERSION** → Error: database te oud
3. **DB > APP_VERSION** → Error: app te oud
4. **DB == MIN_DB_VERSION of hoger** → OK

### Helper Functies
```python
from database.connection import get_db_version, check_db_compatibility
from config import APP_VERSION, MIN_DB_VERSION

# Haal DB versie op
db_version = get_db_version()  # Returns "0.6.15" of None

# Check compatibiliteit
is_ok, db_ver, error_msg = check_db_compatibility()
if not is_ok:
    # Toon error en stop app
```

### Voorbeelden

**Scenario 1: GUI wijziging (button layout aanpassing)**
```python
# config.py
APP_VERSION = "0.6.16"      # ✅ Verhoogd
MIN_DB_VERSION = "0.6.15"   # ✅ Blijft gelijk (geen DB wijziging)
```

**Scenario 2: DB schema wijziging (nieuwe kolom)**
```python
# config.py
APP_VERSION = "0.6.16"      # ✅ Verhoogd
MIN_DB_VERSION = "0.6.16"   # ✅ Ook verhoogd (DB wijziging!)

# connection.py - create_tables()
cursor.execute("""
    ALTER TABLE gebruikers ADD COLUMN nieuwe_kolom TEXT
""")

# upgrade_to_v0_6_16.py
cursor.execute("ALTER TABLE gebruikers ADD COLUMN nieuwe_kolom TEXT")
cursor.execute("""
    INSERT INTO db_metadata (version_number, migration_description)
    VALUES ('0.6.16', 'Nieuwe kolom toegevoegd aan gebruikers')
""")
```

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
│   ├── term_code_service.py       # Term-code mapping
│   └── verlof_saldo_service.py    # Verlof & KD saldo
├── data/
│   └── planning.db
├── migratie_*.py              # Database migraties
├── main.py
└── config.py
```

### Styling Systeem
Gebruik ALTIJD centrale styling:
```python
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig, ThemeManager

btn.setStyleSheet(Styles.button_primary())
TableConfig.setup_table_widget(self.tabel, row_height=50)
input.setStyleSheet(Styles.input_field())

# Theme-aware colors (v0.6.9)
background = Colors.BG_WHITE  # Adapteert automatisch aan theme
text_color = Colors.TEXT_PRIMARY
```

---

## DATABASE SCHEMA

### Versie Beheer

#### db_metadata (v0.6.13)
```sql
CREATE TABLE db_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_number TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    migration_description TEXT
)
```

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
    shift_voorkeuren TEXT,              -- v0.6.11: JSON prioriteit mapping
    theme_voorkeur TEXT DEFAULT 'light', -- v0.6.12: 'light' of 'dark'
    is_actief BOOLEAN DEFAULT 1,
    aangemaakt_op TIMESTAMP,
    gedeactiveerd_op TIMESTAMP,
    laatste_login TIMESTAMP
)
```

### Werkposten & Shift Codes

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

#### gebruiker_werkposten (v0.6.14)
```sql
CREATE TABLE gebruiker_werkposten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gebruiker_id INTEGER NOT NULL,
    werkpost_id INTEGER NOT NULL,
    prioriteit INTEGER DEFAULT 1,         -- 1=eerste keuze, 2=fallback
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(gebruiker_id, werkpost_id),
    FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id) ON DELETE CASCADE,
    FOREIGN KEY (werkpost_id) REFERENCES werkposten(id) ON DELETE CASCADE
)

CREATE INDEX idx_gebruiker_werkposten_gebruiker
ON gebruiker_werkposten(gebruiker_id, prioriteit);
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
    code_naam TEXT UNIQUE NOT NULL,
    beschrijving TEXT,
    kleur TEXT,
    telt_als_werkdag BOOLEAN DEFAULT 0,
    reset_12u_rust BOOLEAN DEFAULT 1,
    breekt_werk_reeks BOOLEAN DEFAULT 0,
    term TEXT,                          -- v0.6.7: verlof, kompensatiedag, zondagrust, etc.
    is_actief BOOLEAN DEFAULT 1,
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gedeactiveerd_on TIMESTAMP
)
```

**Verplichte termen (v0.6.10):**
- verlof, kompensatiedag, zondagrust, zaterdagrust, ziek, arbeidsduurverkorting

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
    toegekende_code_term TEXT,          -- v0.6.10: 'verlof' of 'kompensatiedag'
    FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id),
    FOREIGN KEY (behandeld_door) REFERENCES gebruikers(id)
)
```

#### verlof_saldo (v0.6.10)
```sql
CREATE TABLE verlof_saldo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gebruiker_id INTEGER NOT NULL,
    jaar INTEGER NOT NULL,
    verlof_totaal REAL NOT NULL DEFAULT 0,
    verlof_overgedragen REAL NOT NULL DEFAULT 0,
    verlof_opgenomen REAL NOT NULL DEFAULT 0,
    kd_totaal REAL NOT NULL DEFAULT 0,
    kd_overgedragen REAL NOT NULL DEFAULT 0,
    kd_opgenomen REAL NOT NULL DEFAULT 0,
    opmerking TEXT,
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    laatste_wijziging TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(gebruiker_id, jaar),
    FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id)
)
```

### HR Regels & Rode Lijnen

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

#### rode_lijnen_config (v0.6.8)
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

**Activeren:**
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

---

## SHIFT CODES SYSTEEM

### Architectuur

Twee-laags systeem:
1. **Werkposten**: Team-specifieke shift codes
2. **Speciale Codes**: Globale codes met term-based systeem (v0.6.7)

### Term-based Systeem (v0.6.7)

Speciale codes hebben nu een optioneel `term` veld voor systeemfuncties:

**Verplichte termen (beschermd):**
- `verlof` - Gebruikt bij verlof goedkeuring
- `kompensatiedag` - Gebruikt voor KD tracking (v0.6.10)
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

### Code Eigenschappen

**Op werkpost niveau:**
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

## DESIGN BESLISSINGEN

### Typetabel Architectuur (v0.6.6)
**Beslissing:** Versioned systeem met status lifecycle
**Reden:**
- Trial & error workflow: Meerdere concepten naast elkaar
- Harde cutover datum: Actief tot X, nieuwe vanaf X
- Geschiedenis bewaren: Archief voor audit trail
- Simpel: Geen complexe gebruiker ↔ typetabel koppeling

**Status Lifecycle:**
```
CONCEPT → (valideer + activeer) → ACTIEF → (bij vervanging) → ARCHIEF
```

### Shift Codes in Typetabel
**Beslissing:** Post nummer in code (V1, V2, L1, L2, etc.)
**Reden:**
- Alle teamleden kunnen alle posten bemannen
- Post info zit IN de shift code zelf
- Geen aparte post kolom nodig
- Simpel en flexibel

**Voorbeelden:**
- Interventie (1 post): V, L, N, RX, CX
- Officieren (2 posten): V1, V2, L1, L2, N1, RX, CX
- Supervisors (4 posten): V1-V4, L1-L4, N1-N4, RX, CX

### Werkpost Koppeling (v0.6.14)
**Beslissing:** Many-to-many met prioriteit
**Reden:**
- Multi-post scenario's ondersteunen
- Fallback mechanisme voor auto-generatie
- Flexibiliteit voor cross-training
- Eenvoudige grid UI

**Auto-Generatie Logica:**
1. Typetabel: abstract shift type ("V", "L", "N")
2. Datum: bepaalt dag_type (weekdag/zaterdag/zondag)
3. Gebruiker werkposten: gesorteerd op prioriteit
4. Loop door werkposten tot match: (werkpost, dag_type, shift_type) → shift_code
5. Resultaat: concrete code (bijv. "7101")

### Shift Codes Systeem (v0.6.4)
**Beslissing:** Twee-laags systeem (werkposten + speciale codes)
**Reden:**
- Werkposten: Team-specifieke codes, flexibel per organisatie
- Speciale codes: Globaal, altijd beschikbaar (VV, RX, DA, etc.)
- Eigenschappen op werkpost niveau (simpeler beheer)
- Multi-team support zonder complexiteit

### Tijd Notatie Parsing (v0.6.4)
**Beslissing:** Flexibele parser met meerdere formaten
**Reden:**
- Gebruikers willen snel invoeren (6-14 sneller dan 06:00-14:00)
- Ondersteuning halve uren/kwartieren noodzakelijk
- Automatische normalisatie naar HH:MM in database

### Grid Editor vs Formulier
**Beslissing:** Grid editor (3x4) voor shift codes
**Reden:**
- Overzichtelijk alle shifts per werkpost
- Snel bulk invoeren
- Visuele structuur (dag types × shift types)
- Copy/paste mogelijk (toekomstig)

### Eigenschappen Niveau
**Beslissing:** Eigenschappen op werkpost niveau (niet per shift)
**Reden:**
- Simpeler beheer
- Meestal gelden regels voor alle shifts van een team
- Uitzonderingen zeldzaam
- Database normalisatie

### Soft Delete Pattern
**Beslissing:** is_actief flag + gedeactiveerd_op timestamp
**Reden:**
- Data behoud voor rapportage
- Historische planning blijft intact
- Heractivatie mogelijk
- Audit trail

### Theme Per Gebruiker (v0.6.12)
**Beslissing:** Database opslag per gebruiker ipv globaal JSON
**Reden:**
- Consistenter met rest van applicatie
- Elke gebruiker eigen voorkeur
- Login scherm altijd light (standaard look)
- Geen file locking issues bij multi-user

### Planning Status (v0.6.15)
**Beslissing:** Concept vs Gepubliceerd per maand
**Reden:**
- Planners kunnen experimenteren zonder teamleden te verwarren
- Per maand granulariteit (niet globaal of per week)
- Planners kunnen altijd wijzigen (ook gepubliceerd)
- Teamleden zien alleen gepubliceerde planning

---

## KNOWN ISSUES

### 🟡 BEKEND

**Netwerklatency**
- **Probleem:** Trage DB toegang op netwerkschijf
- **Impact:** Lichte vertraging bij opstarten
- **Workaround:** Database caching overwegen

**Theme Beperkingen (v0.6.9)**
- QCalendarWidget behouden light mode styling (Qt limitation)
- Theme toggle alleen beschikbaar in dashboard

**Verlof Saldo (v0.6.10)**
- Geen automatische cleanup overgedragen verlof op 1 mei
- Geen notificatie systeem voor vervaldatum warnings

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
    typedienst_clicked = pyqtSignal()
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

## LESSEN GELEERD

### PyQt6 Specifiek
1. **Signals moeten class attributes zijn** - Niet in `__init__` definiëren
2. **Instance attributes in `__init__`** - PyCharm warnings voorkomen
3. **Button widths consistent** - Zelfde width voor toggle buttons (96px)
4. **TableWidget cleanup** - Gebruik TableConfig.setup_table_widget()
5. **Unicode voorzichtig** - Emoji's in buttons crashen op Windows
6. **Type ignore voor signals** - Bij connect() en emit()

### Database
1. **Migratie scripts essentieel** - Check schema, pas aan indien nodig
2. **Seed functies up-to-date houden** - Anders mismatch bij schone start
3. **Foreign keys enable** - PRAGMA foreign_keys = ON
4. **Row factory** - sqlite3.Row voor dict access
5. **Prepared statements** - Altijd ? placeholders gebruiken
6. **Soft delete beter dan hard delete** - Data behoud + audit trail
7. **CASCADE delete** - Automatic cleanup bij parent delete

### UI/UX
1. **Consistency is key** - Zelfde patterns overal
2. **Feedback direct** - Geen silent fails
3. **Validatie vroeg** - Voor database operaties
4. **Confirmatie bij destructieve acties** - Voorkom ongelukken
5. **Overzicht belangrijk** - Grid views beter dan lange lijsten
6. **Snelkoppelingen waarderen** - Users type sneller dan ze klikken

### Architectuur
1. **Scheiding concerns** - GUI, Business Logic, Database apart
2. **Router pattern werkt goed** - Callback voor navigatie
3. **Centrale styling vermijdt duplicate code**
4. **Services voor herbruikbare logica**
5. **Inheritance voor widgets** - Base class + specifieke implementaties
6. **Versioning voor belangrijke data** - Zoals typetabellen

### Development Process
1. **Kleine stappen** - Feature per feature implementeren
2. **Test frequent** - Direct testen na changes
3. **Debug prints helpen** - Bij complexe bugs
4. **Documentation tijdens development** - Niet achteraf
5. **Git commits frequent** - Bij werkende staat

### Code Quality
1. **Linting essentieel** - Gebruik ruff voor code quality checks
2. **Fix linting issues** - Voorkom tech debt accumulation
3. **Specifieke exceptions** - Nooit bare `except:`, altijd specifieke errors
4. **Cleanup unused code** - Verwijder unused imports en variables
5. **Context managers** - Gebruik `with` blocks voor resource cleanup
6. **Type hints** - Verbeter code readability en IDE support

#### Ruff Usage
```bash
# Check voor issues
ruff check .

# Auto-fix safe issues
ruff check --fix .

# Format code
ruff format .
```

**Common Issues:**
- **F401**: Unused imports → Verwijder
- **F541**: Onnodige f-string prefix → Verwijder `f` prefix
- **E722**: Bare except → Gebruik `except ValueError:` of specifieke error
- **F841**: Unused variable → Verwijder of prefix met `_` als documentatie

---

*Voor versie geschiedenis en release notes, zie PROJECT_INFO.md*
*Voor recente development sessies, zie DEV_NOTES.md*
*Voor historische sessies, zie DEV_NOTES_ARCHIVE.md*

*Laatste update: 23 Oktober 2025*
*Versie: 0.6.15*
