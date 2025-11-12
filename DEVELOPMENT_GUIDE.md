# DEVELOPMENT GUIDE
Planning Tool - Technische Documentatie voor Ontwikkelaars

## VERSIE INFORMATIE
**Huidige versie:** 0.6.27 (Beta)
**Laatste update:** 11 November 2025

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
11. [HR Validatie Systeem](#hr-validatie-systeem-design)

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

# 4. Update db_metadata (VERPLICHT!)
cursor.execute("""
    INSERT INTO db_metadata (version_number, migration_description)
    VALUES (?, ?)
""", ("0.6.16", "Beschrijving van wijziging"))
```

**⚠️ KRITIEK: Migratie Scripts MOETEN db_metadata Updaten!**

Elk migratie script dat de database schema wijzigt MOET de `db_metadata` tabel updaten:

```python
# FOUT: Schema wijziging zonder versie update
cursor.execute("ALTER TABLE planning ADD COLUMN notitie TEXT")
conn.commit()
# ❌ App zal crashen met "database versie mismatch" error!

# CORRECT: Schema wijziging met versie update
cursor.execute("ALTER TABLE planning ADD COLUMN notitie TEXT")
cursor.execute("""
    INSERT INTO db_metadata (version_number, migration_description)
    VALUES (?, ?)
""", ("0.6.16", "Planning notitie kolom toegevoegd"))
conn.commit()
# ✅ Database versie is gesynchroniseerd met schema
```

**Waarom dit essentieel is:**
- App controleert bij startup: `db_version >= MIN_DB_VERSION`
- Zonder db_metadata update → versie mismatch → app weigert te starten
- Gebruikers krijgen: "Database versie X.Y.Z is ouder dan vereist"

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
    volledige_naam TEXT NOT NULL,        -- Display name (backward compatibility)
    voornaam TEXT,                       -- v0.6.28: Voor sortering
    achternaam TEXT,                     -- v0.6.28: Voor sortering
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

### HR Rules Visualisatie (v0.6.19)

De Planning Editor toont 2 HR kolommen die werkdagen tracking implementeren per 28-daagse rode lijn cyclus.

#### Implementatie Architectuur

**Locatie:** `gui/widgets/planner_grid_kalender.py`

**Kerncomponenten:**
1. **Periode Detectie** - `get_relevante_rode_lijn_periodes()`
2. **Werkdagen Telling** - `tel_gewerkte_dagen()`
3. **Real-time Updates** - `update_hr_cijfers_voor_gebruiker()`

#### Slimme Periode Detectie

```python
def get_relevante_rode_lijn_periodes(self) -> None:
    """
    2-stappen logica voor optimale periode selectie:
    STAP 1: Zoek rode lijn die START binnen deze maand (meest zichtbaar)
    STAP 2: Als niet gevonden, gebruik periode waar maand in valt
    """
    # Voorbeeld: September 2025
    # - Rode lijn start 22 sept (periode 16) → gebruik periode 16
    # - Voor RL = periode 15 (25 aug - 21 sept)
    # - Na RL = periode 16 (22 sept - 19 okt)
```

**Business Logic:**
- **Voor RL**: Vorige periode (periode_nummer - 1)
- **Na RL**: Huidige periode (gedetecteerde periode)
- Database-first: Geen date arithmetic, exact start/eind uit `rode_lijnen` tabel

#### Werkdagen Telling Query

```python
def tel_gewerkte_dagen(self, gebruiker_id: int, start_datum: str, eind_datum: str) -> int:
    """
    Tel alleen shifts met telt_als_werkdag = 1
    Ondersteunt beide werkposten EN speciale codes
    """
    cursor.execute("""
        SELECT COUNT(*) as werkdagen
        FROM planning p
        LEFT JOIN shift_codes sc ON p.shift_code = sc.code
        LEFT JOIN werkposten w ON sc.werkpost_id = w.id
        LEFT JOIN speciale_codes spc ON p.shift_code = spc.code
        WHERE p.gebruiker_id = ?
          AND p.datum BETWEEN ? AND ?
          AND p.shift_code IS NOT NULL
          AND p.shift_code != ''
          AND (
              (sc.code IS NOT NULL AND w.telt_als_werkdag = 1)
              OR
              (spc.code IS NOT NULL AND spc.telt_als_werkdag = 1)
          )
    """, (gebruiker_id, start_datum, eind_datum))
```

**Belangrijk:**
- Empty cells (NULL/empty string) tellen NIET mee
- Beide concept EN gepubliceerd status worden geteld
- Dual-source check: werkposten OF speciale_codes

#### Performance Optimalisatie

**Cache Strategie:**
```python
# Instance variables
self.hr_werkdagen_cache: Dict[int, Dict[str, int]] = {}
# {gebruiker_id: {'voor': X, 'na': Y}}

self.hr_cel_widgets: Dict[int, Dict[str, QLabel]] = {}
# {gebruiker_id: {'voor': QLabel, 'na': QLabel}}
```

**Optimized Update Pattern:**
```python
def save_shift(self, datum_str: str, gebruiker_id: int, shift_code: str):
    # Save to database
    conn.commit()

    # ✓ Direct cel update (geen rebuild)
    self.cel_widgets[datum_str][gebruiker_id].setText(shift_code)

    # ✓ Clear cache voor deze gebruiker
    del self.hr_werkdagen_cache[gebruiker_id]

    # ✓ Update alleen HR cijfers (geen volledige rebuild)
    self.update_hr_cijfers_voor_gebruiker(gebruiker_id)
```

**Waarom dit belangrijk is:**
- Voorkomt crashes (geen rebuild met stale data)
- Shifts zijn direct zichtbaar (setText vs rebuild)
- HR cijfers updaten real-time (3 labels vs 1500+ cells rebuild)
- Geen flicker (alleen gewijzigde cells)

#### UI Specificaties

**Kolom Layout:**
```
| Teamlid (280px) | Voor RL (50px) | Na RL (50px) | Datum1 (60px) | ... |
|                 |       10       |      8       |     7101      | ... |
```

**Styling Details:**
- **Border tussen kolommen:** 3px solid #dc3545 (rode lijn visualisatie)
- **Rode overlay:** `rgba(255, 0, 0, 0.3)` als individuele cel > 19 dagen
- **Font:** Bold, SIZE_SMALL
- **Tooltips:** "Gewerkte dagen: X/19\nPeriode N: start t/m eind"

**Rode Overlay Logica:**
```python
# Check ELKE periode apart (niet het totaal!)
is_voor_overschrijding = voor_dagen > 19
is_na_overschrijding = na_dagen > 19

# Per cel apart stylen
voor_achtergrond = "rgba(255, 0, 0, 0.3)" if is_voor_overschrijding else Colors.BG_LIGHT
na_achtergrond = "rgba(255, 0, 0, 0.3)" if is_na_overschrijding else Colors.BG_LIGHT
```

#### Grid Column Shift

Met HR kolommen:
```python
datum_start_col = 3 if self.rode_lijn_periodes else 1
# Kolom 0: Naam
# Kolom 1: Voor RL (als HR enabled)
# Kolom 2: Na RL (als HR enabled)
# Kolom 3+: Datums
```

Zonder HR kolommen (fallback):
```python
# Kolom 0: Naam
# Kolom 1+: Datums
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

### 7. Atomic Operations (v0.6.21)

**Principe:** Multi-step operaties moeten atomic zijn - alles slaagt of alles faalt.

**FOUT - Niet-atomisch:**
```python
def publiceer_planning():
    # Database EERST updaten
    conn = get_connection()
    cursor.execute("UPDATE planning SET status = 'gepubliceerd' ...")
    conn.commit()  # ❌ Te vroeg!

    # Excel export daarna (kan falen)
    try:
        export_maand_naar_excel(jaar, maand)  # 💥 FAALT
    except Exception as e:
        # ❌ Te laat! Database is al gecommit
        QMessageBox.warning(self, "Error", str(e))
```

**Gevolg:** Inconsistent state - database gepubliceerd, maar geen Excel.

**CORRECT - Atomisch:**
```python
def publiceer_planning():
    # STAP 1: Excel export EERST (kan falen zonder side-effects)
    try:
        excel_pad = export_maand_naar_excel(jaar, maand)
    except PermissionError:
        QMessageBox.critical(self, "Geannuleerd",
                            "Bestand is open in Excel. Sluit eerst het bestand.")
        return  # ✅ Early return - database blijft ongewijzigd
    except (IOError, OSError) as e:
        QMessageBox.critical(self, "Geannuleerd",
                            f"Kan niet schrijven: {str(e)}")
        return  # ✅ Early return

    # STAP 2: Database update (alleen als export succesvol)
    try:
        conn = get_connection()
        cursor.execute("UPDATE planning SET status = 'gepubliceerd' ...")
        conn.commit()  # ✅ Veilig - Excel bestaat al

        QMessageBox.information(self, "Success",
                                f"Gepubliceerd + Excel: {excel_pad}")
    except Exception as e:
        QMessageBox.critical(self, "Fout", str(e))
```

**Voordelen:**
- ✅ Data integriteit gegarandeerd
- ✅ Geen rollback logica nodig (database nooit gewijzigd bij fout)
- ✅ Duidelijke error messages
- ✅ Gebruiker kan retry zonder inconsistent state

**Algemene regel:** Bij multi-step operaties - volgorde bewust kiezen:
1. Voer eerst stappen uit die kunnen falen (external I/O, file ops)
2. Pas daarna interne state wijzigen (database, memory)
3. Early return bij elke fout

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

## FUTURE CONSIDERATIONS

### GUI Pattern: QMenuBar voor Complexe Schermen

**Concept:** Voor schermen met veel functionaliteit (zoals Planning Editor) kan een menu bar boven aan het scherm de UX verbeteren.

**Implementatie:**
```python
class PlanningEditorScreen(QWidget):
    def __init__(self, router: Callable):
        super().__init__()
        self.router = router

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Menu bar bovenaan
        menu_bar = QMenuBar()
        layout.addWidget(menu_bar)

        # Planning menu
        planning_menu = menu_bar.addMenu("Planning")
        planning_menu.addAction("Auto-Genereren...", self.on_auto_genereren)
        planning_menu.addAction("Wis Maand", self.on_wis_maand)
        planning_menu.addSeparator()
        planning_menu.addAction("Publiceren", self.toggle_publicatie_status)

        # Bewerken menu
        bewerk_menu = menu_bar.addMenu("Bewerken")
        bewerk_menu.addAction("Vul Week...", self.vul_week)
        bewerk_menu.addAction("Wis Selectie", self.wis_selectie)

        # Weergave menu
        weergave_menu = menu_bar.addMenu("Weergave")
        weergave_menu.addAction("Verberg Reserves", self.toggle_reserves)

        # Terug knop rechts
        menu_bar.addAction("← Terug", self.router)

        # Rest van UI
        layout.addWidget(self.kalender_widget)
```

**Voordelen:**
- Meer verticale ruimte voor content
- Logische groepering van functionaliteit
- Keyboard shortcuts (Alt+P voor Planning, etc.)
- Schaalbaar voor nieuwe features
- Professionele uitstraling

**Nadelen:**
- Extra klik nodig (dropdown ipv directe button)
- Functionaliteit minder zichtbaar
- Gebruikers moeten menu structuur leren

**Hybride Aanpak:**
Combineer menu bar met compacte header:
- Menu bar: Minder gebruikte functies
- Header: Meest gebruikte acties (bijv. Publiceren)
- Context menu: Cel-specifieke acties

**Wanneer Gebruiken:**
- Schermen met >6 acties/knoppen
- Duidelijke groepering mogelijk (Planning/Bewerken/Weergave)
- Verticale ruimte schaars
- Desktop applicatie workflow (niet mobile-first)

**Status:** Gedocumenteerd voor toekomstige evaluatie wanneer alle functionaliteit geïmplementeerd is.

---

## LESSEN GELEERD

### PyQt6 Specifiek
1. **Signals moeten class attributes zijn** - Niet in `__init__` definiëren
2. **Instance attributes in `__init__`** - PyCharm warnings voorkomen
3. **Button widths consistent** - Zelfde width voor toggle buttons (96px)
4. **TableWidget cleanup** - Gebruik TableConfig.setup_table_widget()
5. **Unicode voorzichtig** - Emoji's in buttons crashen op Windows
6. **Type ignore voor signals** - Bij connect() en emit()
7. **Qt CSS overlays met qlineargradient** - Qt CSS ondersteunt GEEN standard CSS `linear-gradient()`, gebruik `qlineargradient()` syntax:
   ```python
   # ❌ FOUT - standard CSS syntax werkt NIET in Qt
   overlay = "linear-gradient(rgba(129, 199, 132, 0.4), rgba(129, 199, 132, 0.4))"

   # ✅ CORRECT - Qt CSS syntax
   overlay = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(129, 199, 132, 0.4), stop:1 rgba(129, 199, 132, 0.4))"

   # Toepassen: replace background-color met background
   base_style = base_style.replace(
       f"background-color: {base_color}",
       f"background: {overlay}"
   )
   ```
   **Pattern gebruikt in:** Cell selection (v0.6.17), Bemannings overlay (v0.6.20)

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

## HR VALIDATIE SYSTEEM (v0.6.26)

**Status:** ✅ GEÏMPLEMENTEERD (74% compleet - FASE 1-4)
**Versie:** v0.6.26 (Beta - Actief in productie)
**Design Document:** `docs/architecture/HR_VALIDATIE_SYSTEEM_DESIGN.md`
**Checklist:** `docs/architecture/HR_VALIDATIE_IMPLEMENTATIE_CHECKLIST.md`

### Overzicht

Automatische validatie van **7 HR regels** tijdens roosteren:
1. **12u rust tussen shifts** (wettelijk verplicht) ✅
2. **Max 50u per week** (wettelijk verplicht) ✅
3. **Max 19 werkdagen per 28-dagen cyclus** (organisatie regel) ✅
4. **Max 7 dagen tussen RX/CX** (organisatie regel) ✅
5. **Max 7 werkdagen achter elkaar** (organisatie regel) ✅
6. **Max weekends achter elkaar** (organisatie regel) ✅
7. **Nacht gevolgd door vroeg verboden** (organisatie regel - configureerbaar) ✅

### Architectuur (Geïmplementeerd)

**Core Layer (FASE 1):**
- `services/constraint_checker.py` (~1600 regels) ✅
  - `ConstraintChecker` class - Pure business logic (geen database)
  - `PlanningRegel` dataclass - Input data model
  - `Violation` dataclass - Structured error reporting
  - `ConstraintCheckResult` - Result wrapper met metadata
  - 7 check methods: één per HR regel
  - Segmented planning check (BUG-005 fix)

**Database Wrapper (FASE 2):**
- `services/planning_validator_service.py` (~540 regels) ✅
  - `PlanningValidator` class - Database integratie
  - Query methods: HR config, shift tijden, planning, rode lijnen
  - Caching: config, shift tijden, planning, violations
  - Buffer loading: +/- 1 maand voor cross-month checks
  - Public API: `validate_all()`, `validate_shift()`, `get_violation_level()`

**UI Integratie (FASE 3+4):**
- `gui/widgets/planner_grid_kalender.py` (+250 regels) ✅
  - **Rode/gele overlay** in grid cellen (70% opacity)
  - **Tooltips** met violation details per datum
  - **HR Summary Box** onderaan grid (scrollable, max 200px)
  - **"Valideer Planning" knop** voor on-demand batch check
  - Real-time updates DISABLED (te irritant tijdens invoer)
- `gui/screens/planning_editor_screen.py` (+60 regels) ✅
  - **Pre-publicatie validatie** check (STAP 1 voor Excel export)
  - Warning dialog met violations count per gebruiker
  - Keuze: annuleren of toch publiceren

**Validatie Strategie (Aangepast):**
- **On-demand:** Batch via "Valideer Planning" knop ✅
- **Pre-publicatie:** Full validation voor Excel export ✅
- **Real-time:** DISABLED (user feedback - te storend) ❌
- **Soft waarschuwing:** Violations blokkeren niet, alleen waarschuwen ✅

### Geïmplementeerde Bestanden

**Nieuwe bestanden:**
1. ✅ `services/constraint_checker.py` (1600 regels) - Core logic
2. ✅ `services/planning_validator_service.py` (540 regels) - DB wrapper
3. ✅ `scripts/test_constraint_scenarios.py` (489 regels) - Automated tests (13/13 PASSED)
4. ✅ `scripts/test_segmented_rx_check.py` (230 regels) - Segmented RX tests
5. ❌ `gui/dialogs/hr_validatie_rapport_dialog.py` - NIET geïmplementeerd (QMessageBox voldoende)

**Gewijzigde bestanden:**
1. ✅ `gui/widgets/planner_grid_kalender.py` (+250 regels) - Overlay + summary box + validatie knop
2. ✅ `gui/screens/planning_editor_screen.py` (+60 regels) - Pre-publicatie check
3. ✅ `gui/dialogs/hr_regel_edit_dialog.py` (+100 regels) - Term-based UI voor nacht→vroeg
4. ⏸️ `gui/screens/typetabel_beheer_screen.py` - PENDING (FASE 5)

**Daadwerkelijke effort:** 28 uur (74% compleet)
- FASE 1: ConstraintChecker Core (8u) ✅
- FASE 2: PlanningValidator Wrapper (6u) ✅
- FASE 3: UI Grid Overlay (9u) ✅
- FASE 4: Pre-Publicatie Validatie (5u) ✅
- FASE 5: Typetabel Pre-Activatie (0u) ⏸️

### Key Features (Geïmplementeerd)

**On-Demand Validatie via Knop:**
```python
# In planner_grid_kalender.py (lines 785-859)
def on_valideer_planning_clicked(self):
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

    try:
        # Batch validatie
        self.load_hr_violations()  # Alle gebruikers
        self.build_grid()  # Toon rode overlays

        # Tel violations
        totaal = sum(len(v) for datum_dict in self.hr_violations.values()
                     for gebruiker_list in datum_dict.values()
                     for v in gebruiker_list)

        # Show samenvatting
        if totaal == 0:
            QMessageBox.information(self, "Validatie Compleet",
                                   "Geen HR violations gevonden!")
        else:
            QMessageBox.warning(self, "HR Violations Gevonden",
                               f"{totaal} violations - zie grid overlays")
    finally:
        QApplication.restoreOverrideCursor()
```

**Pre-Publicatie Validatie:**
```python
# In planning_editor_screen.py (lines 424-482)
def publiceer_planning(self):
    # STAP 1: HR Validatie
    gebruikers = get_actieve_gebruikers()
    violations_count = 0

    for gebruiker in gebruikers:
        validator = PlanningValidator(gebruiker['id'], jaar, maand)
        violations_dict = validator.validate_all()
        violations_count += sum(len(v) for v in violations_dict.values())

    # Waarschuwing met keuze
    if violations_count > 0:
        reply = QMessageBox.warning(
            self, "Waarschuwing: HR Violations",
            f"Planning bevat {violations_count} violations.\n"
            "Bent u zeker dat u wil publiceren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return  # Annuleren

    # STAP 2: Excel export + publiceer
    ...
```

**Grid Overlay & Tooltips:**
```python
# In planner_grid_kalender.py
def get_hr_overlay_kleur(self, datum_str: str, gebruiker_id: int) -> str:
    violations = self.hr_violations.get(datum_str, {}).get(gebruiker_id, [])

    if not violations:
        return ""

    # Check severity
    has_error = any(v.severity == ViolationSeverity.ERROR for v in violations)

    if has_error:
        return "rgba(229, 115, 115, 0.7)"  # Rood
    else:
        return "rgba(255, 213, 79, 0.7)"   # Geel
```

**Typetabel Pre-validatie:**
```python
# PENDING (FASE 5 - Not yet implemented)
# Planned voor toekomstige release
```

### Design Highlights

**12u Rust Check (Meest Complex):**
- Middernacht crossing handling (`22:00-06:00`)
- Reset flags (RX, CX, Z codes resetten 12u teller)
- Speciale codes zonder shift tijden
- Query optimization (LEFT JOIN shift_codes + speciale_codes)

**50u Week Check:**
- Week definitie parsing (`ma-00:00|zo-23:59`)
- Overlap berekening (exclusieve grenzen)
- Shift duur berekening over middernacht

**Performance:**
- Caching strategie (shift tijden, HR config, validation results)
- Incremental updates (real-time scope: 1 datum + omliggende)
- Batch queries (geen N+1 queries)
- Target: <100ms real-time, <2s batch

### Testing (Status)

**Automated Tests:** ✅ COMPLEET
- `scripts/test_constraint_scenarios.py` - 13 scenarios (13/13 PASSED)
  - RX/CX gap detection (10 dagen)
  - 7 vs 8 werkdagen boundary
  - RX breekt werkdagen reeks
  - VV telt als werkdag
  - 48u vs 56u week boundary
  - 12u rust cross-month
  - RX gap cross-year
  - 19 vs 20 dagen cyclus boundary
- `scripts/test_segmented_rx_check.py` - 3 scenarios (3/3 PASSED)
  - Partial planning (weekend-only) geen valse violations
  - Complete planning met correct gap detection
  - Gap > 7 dagen binnen segment gedetecteerd

**Manual Tests:** ✅ VERIFIED
- 30 gebruikers grid loading: <1 sec (met ValidationCache)
- Violations overlay + tooltips: werkend
- "Valideer Planning" knop: werkend
- Pre-publicatie warning: werkend

**Pending Tests:**
- [ ] Comprehensive unit tests (40+ test cases)
- [ ] UI integration tests (automated)
- [ ] Typetabel pre-activatie tests (FASE 5)

### Reference

Voor volledige technische specificatie, zie **`HR_VALIDATIE_SYSTEEM_DESIGN.md`**:
- Algoritmes per regel (stap-voor-stap pseudocode)
- SQL queries met comments
- Edge cases & error handling
- UI mockups (ASCII art)
- Implementation roadmap (5 fases)
- Code voorbeelden

---

*Voor versie geschiedenis en release notes, zie PROJECT_INFO.md*
*Voor recente development sessies, zie DEV_NOTES.md*
*Voor historische sessies, zie DEV_NOTES_ARCHIVE.md*

*Laatste update: 30 Oktober 2025*
*Versie: 0.6.23*
