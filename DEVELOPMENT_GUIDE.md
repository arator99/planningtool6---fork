# DEVELOPMENT GUIDE
Planning Tool - Technische Documentatie voor Ontwikkelaars

## INHOUDSOPGAVE
1. [Technische Architectuur](#technische-architectuur)
2. [Database Schema](#database-schema)
3. [PyQt6 & PyCharm Best Practices](#pyqt6--pycharm-best-practices)
4. [Known Issues & Oplossingen](#known-issues--oplossingen)
5. [Shift Codes Systeem](#shift-codes-systeem)
6. [HR Regels](#hr-regels)
7. [Code Templates](#code-templates)
8. [Optimalisatie voor .EXE](#optimalisatie-voor-exe)
9. [Dashboard & main.py – Menu Systeem](#dashboard--mainpy---menu-systeem)


---

## TECHNISCHE ARCHITECTUUR

### Stack
- **Database**: SQLite (data/planning.db)
  - Foreign keys enabled
  - Row factory voor dict access
  - UUID voor gebruikers als permanente ID
  - Timestamps voor audit trails
  - Migratie systeem voor schema updates

- **GUI Framework**: PyQt6
  - Signal/Slot voor navigatie
  - QStackedWidget voor scherm wisseling
  - Centrale styling via gui/styles.py
  - Unicode emoji's vermeden (Windows compatibility)

- **Services Laag**:
  - Scheiding business logic van GUI
  - Herbruikbare validatie/planning functies
  - Database abstractie
  - Auto-generatie services

### Project Structuur
```
root/
├── database/
│   ├── connection.py          # DB init & seed data
│   └── __init__.py
├── gui/
│   ├── styles.py              # Centrale styling
│   ├── dialogs/
│   │   └── about_dialog.py
│   ├── screens/
│   │   ├── login_screen.py
│   │   ├── dashboard_screen.py
│   │   ├── feestdagen_screen.py
│   │   └── gebruikersbeheer_screen.py
│   └── __init__.py
├── models/                     # Dataclasses (toekomstig)
├── services/
│   ├── data_ensure_service.py # Auto-generatie
│   └── __init__.py
├── data/
│   └── planning.db            # SQLite database
├── main.py                    # Entry point
└── config.py                  # Configuratie
```

### Styling Systeem
Centrale styling in `gui/styles.py`:
- **Colors class**: Kleuren palette
- **Fonts class**: Font configuratie
- **Dimensions class**: Spacing en afmetingen
- **Styles class**: Pre-built stylesheet methods
- **TableConfig class**: Helper voor tabellen

Gebruik altijd de centrale styling:
```python
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig

# Buttons
btn.setStyleSheet(Styles.button_primary())
btn.setStyleSheet(Styles.button_danger(Dimensions.BUTTON_HEIGHT_TINY))

# Tables
TableConfig.setup_table_widget(self.tabel, row_height=50)

# Input fields
input.setStyleSheet(Styles.input_field())
```

---

## DATABASE SCHEMA

### Belangrijke Tabellen

#### gebruikers
```sql
- id (PK)
- gebruiker_uuid (UNIQUE, permanent ID)
- gebruikersnaam (UNIQUE, format: ABC1234)
- wachtwoord_hash (bcrypt)
- volledige_naam
- rol (planner/teamlid)
- is_reserve (BOOLEAN)
- startweek_typedienst (1-6, NULL voor reserves)
- is_actief (BOOLEAN)
- aangemaakt_op (TIMESTAMP)
- gedeactiveerd_op (TIMESTAMP)
- laatste_login (TIMESTAMP)
```

#### feestdagen
```sql
- id (PK)
- datum (UNIQUE, YYYY-MM-DD)
- naam
- is_zondagsrust (BOOLEAN)
- is_variabel (BOOLEAN, 0=vast, 1=variabel/extra)
```

#### rode_lijnen
```sql
- id (PK)
- periode_nummer
- start_datum (UNIQUE, 28-dagen cyclus)
- eind_datum
```

#### typetabel
```sql
- id (PK)
- week_nummer (1-6)
- dag_nummer (1-7)
- shift_type (V/L/N/RX/CX/T)
```

### Database Migraties
Bij schema wijzigingen altijd een migratie script maken:
```python
# example_migration.py
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/planning.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check of migratie nodig is
    cursor.execute("PRAGMA table_info(table_name)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'new_column' in columns:
        print("✓ Migratie al uitgevoerd")
        conn.close()
        return
    
    # Voer migratie uit
    cursor.execute("ALTER TABLE table_name ADD COLUMN new_column TEXT")
    conn.commit()
    conn.close()
    print("✓ Migratie succesvol")

if __name__ == '__main__':
    migrate()
```

---

## PYQT6 & PYCHARM BEST PRACTICES

### 1. PYQT6 SIGNALS

❌ **FOUT** - Signal in `__init__`:
```python
class MyWidget(QWidget):
    def __init__(self):
        self.my_signal = pyqtSignal()  # WERKT NIET!
```

✅ **CORRECT** - Signal als class attribute:
```python
class MyWidget(QWidget):
    my_signal: pyqtSignal = pyqtSignal()
    my_data_signal: pyqtSignal = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
```

Type ignore gebruiken bij connect/emit:
```python
self.my_signal.connect(self.handler)  # type: ignore
self.my_signal.emit()  # type: ignore
```

### 2. INSTANCE ATTRIBUTES

❌ **FOUT** - Attributes buiten `__init__`:
```python
class MyScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.tabel = QTableWidget()  # PyCharm warning!
```

✅ **CORRECT** - Alle attributes in `__init__`:
```python
class MyScreen(QWidget):
    def __init__(self):
        super().__init__()
        # Declareer ALLE instance attributes hier
        self.tabel: QTableWidget = QTableWidget()
        self.input: QLineEdit = QLineEdit()
        self.data: List[Dict[str, Any]] = []
        self.init_ui()
```

### 3. EXCEPTION HANDLING

❌ **FOUT** - Te breed:
```python
try:
    database_operatie()
except Exception as e:  # Te breed!
    print(f"Error: {e}")
```

✅ **CORRECT** - Specifieke exceptions:
```python
import sqlite3

try:
    database_operatie()
except sqlite3.Error as e:
    QMessageBox.critical(self, "Database Fout", str(e))
except ValueError as e:
    QMessageBox.warning(self, "Validatie Fout", str(e))
except Exception as e:
    QMessageBox.critical(self, "Onverwachte Fout", str(e))
```

### 4. LAMBDA'S IN LOOPS

❌ **FOUT** - Lambda met mutable default:
```python
for item in items:
    btn.clicked.connect(lambda: self.handle(item))  # BUG!
    btn.clicked.connect(lambda checked, i=item: self.handle(i))  # Warning
```

✅ **CORRECT** - Callback factory method:
```python
for item in items:
    btn.clicked.connect(self.create_callback(item))  # type: ignore

def create_callback(self, item):
    """Factory method voorkomt closure problemen"""
    def callback():
        self.handle(item)
    return callback
```

### 5. BUTTONS IN TABELLEN

✅ **Crashproof pattern**:
```python
def laad_data(self):
    for row, item in enumerate(data):
        # Simpele HBox zonder nested layouts
        actie_widget = QWidget()
        actie_layout = QHBoxLayout()
        actie_layout.setContentsMargins(0, 0, 0, 0)
        actie_layout.setSpacing(Dimensions.SPACING_SMALL)
        actie_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Buttons met expliciete afmetingen
        btn = QPushButton("Actie")
        btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
        btn.setFixedWidth(80)
        btn.setStyleSheet(Styles.button_primary(Dimensions.BUTTON_HEIGHT_TINY))
        btn.clicked.connect(self.create_callback(item))  # type: ignore
        actie_layout.addWidget(btn)
        
        # Expliciet setLayout aanroepen
        actie_widget.setLayout(actie_layout)
        self.tabel.setCellWidget(row, col, actie_widget)
```

**Key points:**
- Geen VBox nested layouts (crashes!)
- `setLayout()` expliciet aanroepen
- Margins op 0
- `AlignCenter` op layout
- `setMinimumHeight` + `setFixedWidth`
- Callback factory methods

### 6. TABLE ROW HEIGHT

Voor buttons van 26px (TINY):
```python
TableConfig.setup_table_widget(self.tabel, row_height=50)
```

**Wiskunde:**
- Button height: 26px
- Row height: 50px
- Ruimte over: 24px (~12px boven + ~12px onder)

### 7. BUTTON STYLING - HEIGHT-AWARE

Automatische font-size in `styles.py`:
```python
@staticmethod
def button_primary(height=None):
    h = height or Dimensions.BUTTON_HEIGHT_NORMAL
    font_size = Fonts.SIZE_TINY if h <= 26 else Fonts.SIZE_BUTTON
    return f"""
        QPushButton {{
            font-size: {font_size}px;
            padding: 0px 12px;
            min-height: {h}px;
            max-height: {h}px;
            ...
        }}
    """
```

**Result:**
- TINY buttons (≤26px): 11px font
- Normal buttons (>26px): 12px font

### 8. QDIALOGBUTTONBOX

❌ **Type error met bitwise OR:**
```python
buttons = QDialogButtonBox(
    QDialogButtonBox.StandardButton.Ok | 
    QDialogButtonBox.StandardButton.Cancel
)  # PyCharm type error
```

✅ **Gebruik addButton:**
```python
buttons = QDialogButtonBox()
buttons.addButton(QDialogButtonBox.StandardButton.Ok)
buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
buttons.accepted.connect(self.accept)  # type: ignore
buttons.rejected.connect(self.reject)  # type: ignore
```

### 9. TYPE HINTS

Gebruik type hints voor betere code quality:
```python
from typing import Dict, Any, List, Optional, Callable

class MyScreen(QWidget):
    def __init__(self, router: Callable):
        self.router = router
        self.data: List[Dict[str, Any]] = []
    
    def load_data(self) -> None:
        ...
    
    def process(self, item: Dict[str, Any]) -> Optional[str]:
        ...
```
## STYLES.PY REFERENTIE

### Overzicht
Alle styling wordt centraal beheerd in `gui/styles.py`. Gebruik ALTIJD deze centrale styling voor consistentie en onderhoudbaarheid.

```python
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
```

---

### Colors Class

**Primary & State Colors:**
```python
Colors.PRIMARY          # "#007bff" - Hoofdkleur
Colors.PRIMARY_HOVER    # "#0056b3" - Hover state
Colors.SUCCESS          # "#28a745" - Groen (succes)
Colors.SUCCESS_HOVER    # "#218838"
Colors.WARNING          # "#ffc107" - Geel/Oranje (waarschuwing)
Colors.WARNING_HOVER    # "#e0a800"
Colors.DANGER           # "#dc3545" - Rood (gevaar)
Colors.DANGER_HOVER     # "#c82333"
Colors.INFO             # "#17a2b8" - Blauw (info)
Colors.INFO_HOVER       # "#117a8b"
```

**Neutral Colors:**
```python
Colors.SECONDARY        # "#6c757d" - Grijs
Colors.SECONDARY_HOVER  # "#5a6268"
Colors.LIGHT            # "#f8f9fa"
Colors.DARK             # "#343a40"
```

**Backgrounds:**
```python
Colors.BG_WHITE         # "#ffffff"
Colors.BG_LIGHT         # "#f8f9fa"
Colors.BG_DARK          # "#343a40"
```

**Borders:**
```python
Colors.BORDER_LIGHT     # "#dee2e6"
Colors.BORDER_MEDIUM    # "#ced4da"
Colors.BORDER_DARK      # "#6c757d"
```

**Text:**
```python
Colors.TEXT_PRIMARY     # "#212529" - Hoofdtekst
Colors.TEXT_SECONDARY   # "#6c757d" - Subtekst
Colors.TEXT_MUTED       # "#999999" - Gedempte tekst
Colors.TEXT_WHITE       # "#ffffff"
Colors.TEXT_BLACK       # "#000000"
```

**Table:**
```python
Colors.TABLE_GRID       # "#dee2e6" - Grid lijnen
Colors.TABLE_HEADER_BG  # "#f8f9fa" - Header achtergrond
Colors.TABLE_HOVER      # "#e9ecef" - Hover state
```

---

### Fonts Class

**Font Families:**
```python
Fonts.FAMILY            # "Arial" - Standaard font
Fonts.FAMILY_ALT        # "Segoe UI" - Alternatief
```

**Font Sizes:**
```python
Fonts.SIZE_LARGE        # 24px - Grote titels
Fonts.SIZE_TITLE        # 18px - Hoofdtitels
Fonts.SIZE_HEADING      # 16px - Subkoppen
Fonts.SIZE_NORMAL       # 14px - Normale tekst
Fonts.SIZE_SMALL        # 12px - Kleine tekst
Fonts.SIZE_TINY         # 9px - Zeer klein
Fonts.SIZE_BUTTON       # 12px - Uniforme button tekst
```

**Font Weights:**
```python
Fonts.WEIGHT_NORMAL     # "normal"
Fonts.WEIGHT_BOLD       # "bold"
```

---

### Dimensions Class

**Button Heights:**
```python
Dimensions.BUTTON_HEIGHT_LARGE    # 40px
Dimensions.BUTTON_HEIGHT_NORMAL   # 32px - Standaard
Dimensions.BUTTON_HEIGHT_SMALL    # 28px
Dimensions.BUTTON_HEIGHT_TINY     # 20px
```

**Table Heights:**
```python
Dimensions.TABLE_ROW_HEIGHT         # 50px - Standaard rij hoogte
Dimensions.TABLE_ROW_HEIGHT_COMPACT # 45px - Compacte rijen
```

**Spacing:**
```python
Dimensions.SPACING_SMALL    # 5px
Dimensions.SPACING_MEDIUM   # 10px
Dimensions.SPACING_LARGE    # 20px
```

**Margins:**
```python
Dimensions.MARGIN_SMALL     # 5px
Dimensions.MARGIN_MEDIUM    # 20px
Dimensions.MARGIN_LARGE     # 40px
```

**Border Radius:**
```python
Dimensions.RADIUS_SMALL     # 3px
Dimensions.RADIUS_MEDIUM    # 4px
Dimensions.RADIUS_LARGE     # 5px
Dimensions.RADIUS_XL        # 8px
```

---

### Styles Class - Methods

**Button Styling:**

```python
# Primary button (blauw)
btn.setStyleSheet(Styles.button_primary())
btn.setStyleSheet(Styles.button_primary(height=Dimensions.BUTTON_HEIGHT_TINY))

# Success button (groen) - Opslaan, Activeren
btn.setStyleSheet(Styles.button_success())

# Warning button (geel/oranje) - Bewerken, Deactiveren
btn.setStyleSheet(Styles.button_warning())

# Danger button (rood) - Verwijderen, Uitloggen
btn.setStyleSheet(Styles.button_danger())

# Secondary button (grijs) - Terug, Annuleren
btn.setStyleSheet(Styles.button_secondary())

# Custom large action button
btn.setStyleSheet(Styles.button_large_action(Colors.INFO, Colors.INFO_HOVER))
```

**Input Fields:**

```python
# Werkt voor QLineEdit, QComboBox, QDateEdit
input_field.setStyleSheet(Styles.input_field())
```

**Tables:**

```python
table.setStyleSheet(Styles.table_widget())
```

**Info Boxes:**

```python
# Default info box (blauw)
label.setStyleSheet(Styles.info_box())

# Custom kleuren
label.setStyleSheet(Styles.info_box(
    bg_color="#fff3cd",
    border_color="#ffc107", 
    text_color="#856404"
))
```

**Menu Buttons:**

```python
btn.setStyleSheet(Styles.menu_button())
```

---

### TableConfig Class

**Setup Helper:**

```python
# Standaard setup (50px rows)
TableConfig.setup_table_widget(self.tabel)

# Custom row height
TableConfig.setup_table_widget(self.tabel, row_height=45)
```

Deze methode configureert automatisch:
- Table styling
- Alternating row colors
- Selection behavior (hele rijen)
- Edit triggers (read-only)
- Row height

---

### BELANGRIJKE OPMERKINGEN

**❌ WAT BESTAAT NIET:**
```python
# Deze bestaan NIET - gebruik alternatieven hieronder
Dimensions.INPUT_HEIGHT              # ❌ Gebruik BUTTON_HEIGHT_NORMAL
Dimensions.ROW_HEIGHT                # ❌ Gebruik TABLE_ROW_HEIGHT
Fonts.SIZE_MEDIUM                    # ❌ Gebruik SIZE_NORMAL
Colors.PRIMARY_LIGHT                 # ❌ Gebruik BG_LIGHT of TABLE_HOVER
```

**✅ JUISTE ALTERNATIEVEN:**
```python
# Voor input field heights
input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)  # 32px

# Voor table row heights
TableConfig.setup_table_widget(table, row_height=Dimensions.TABLE_ROW_HEIGHT)

# Voor medium text
label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
```

**💡 BEST PRACTICES:**

1. **Gebruik ALTIJD de centrale constanten:**
   ```python
   # ❌ Fout
   btn.setStyleSheet("background-color: #007bff;")
   
   # ✅ Correct
   btn.setStyleSheet(Styles.button_primary())
   ```

2. **Button heights in tables:**
   ```python
   # Voor buttons in 50px table rows
   btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)  # 20px
   TableConfig.setup_table_widget(table, row_height=50)
   ```

3. **Consistent spacing:**
   ```python
   layout.setSpacing(Dimensions.SPACING_MEDIUM)
   layout.setContentsMargins(
       Dimensions.SPACING_LARGE,
       Dimensions.SPACING_LARGE,
       Dimensions.SPACING_LARGE,
       Dimensions.SPACING_LARGE
   )
   ```

4. **Height-aware button styling:**
   ```python
   # Automatic font-size adjustment gebaseerd op height
   btn.setStyleSheet(Styles.button_primary(Dimensions.BUTTON_HEIGHT_TINY))
   # Font wordt automatisch 11px voor tiny buttons
   ```

---

### VOORBEELDEN

**Complete Button Setup:**
```python
btn = QPushButton("Opslaan")
btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
btn.setFixedWidth(100)
btn.setStyleSheet(Styles.button_success())
btn.setCursor(Qt.CursorShape.PointingHandCursor)
btn.clicked.connect(self.save_data)  # type: ignore
```

**Complete Input Field Setup:**
```python
input = QLineEdit()
input.setPlaceholderText("Voer waarde in")
input.setStyleSheet(Styles.input_field())
input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
```

**Complete Table Setup:**
```python
self.tabel = QTableWidget()
self.tabel.setColumnCount(3)
self.tabel.setHorizontalHeaderLabels(['Kolom 1', 'Kolom 2', 'Acties'])
TableConfig.setup_table_widget(self.tabel, row_height=50)
```

**Buttons in Table Cells:**
```python
# Crashproof pattern voor buttons in tables
actie_widget = QWidget()
actie_layout = QHBoxLayout()
actie_layout.setContentsMargins(0, 0, 0, 0)
actie_layout.setSpacing(Dimensions.SPACING_SMALL)
actie_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

btn = QPushButton("Bewerken")
btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
btn.setFixedWidth(80)
btn.setStyleSheet(Styles.button_warning(Dimensions.BUTTON_HEIGHT_TINY))
btn.clicked.connect(self.create_callback(item))  # type: ignore

actie_layout.addWidget(btn)
actie_widget.setLayout(actie_layout)
self.tabel.setCellWidget(row, col, actie_widget)
```

---

### WIJZIGINGEN AAN STYLES.PY

Als je nieuwe kleuren, fonts of dimensies nodig hebt:

1. **Voeg toe aan de juiste class** in `styles.py`
2. **Update deze documentatie sectie**
3. **Test grondig** in bestaande schermen
4. **Commit met duidelijke message**

Voorkom "magic numbers" - voeg altijd een constante toe in plaats van hard-coded waardes te gebruiken!

---

*Laatste update: Oktober 2025*
---

## KNOWN ISSUES & OPLOSSINGEN

### ✅ OPGELOST: PyQt6 Unicode Crashes
**Probleem**: Unicode arrows/emoji's in buttons crashen de app  
**Oplossing**: Gebruik gewone tekst in buttons
```python
# ❌ btn.setText("← Terug")  # Crash!
# ✅ btn.setText("Terug")     # OK
```

### ✅ OPGELOST: Nested Layout Crashes (0xC0000409)
**Probleem**: Nested VBox/HBox in table cells crashen  
**Oplossing**: Simpele HBox met AlignCenter, geen VBox
```python
# ❌ VBox met stretch nested in HBox - CRASH
# ✅ Simpele HBox met AlignCenter - OK
```

### ✅ OPGELOST: Lambda Closure Problemen
**Probleem**: Lambda in loop gebruikt altijd laatste waarde  
**Oplossing**: Callback factory methods

### ✅ OPGELOST: PyCharm Type Errors
**Probleem**: PyCharm klaagt over pyqtSignal types  
**Oplossing**: Type hints + `# type: ignore` comments

### ✅ OPGELOST: Buttons Niet Gecentreerd
**Probleem**: Buttons in table rows niet gecentreerd  
**Oplossing**: HBoxLayout met AlignCenter + row_height=50

### ✅ OPGELOST: Grid Layout Row Height Issues
**Probleem**: Planner kalender had te hoge rijen (3-4x hoger dan teamlid kalender)  
**Oorzaak**: QGridLayout probeert uniform row heights te maken, header rij met 3-regelige labels (buffer dagen) maakte alle rijen hoger  
**Oplossing**: Container height begrenzen op basis van aantal rijen
```python
self.grid_container.setMaximumHeight(grid_layout.rowCount() * Dimensions.TABLE_ROW_HEIGHT)
```
Dit forceert de grid om binnen 50px per rij te blijven, ongeacht header label hoogte.
**Probleem**: Lange labels passen niet op buttons  
**Oplossing**: Height-aware font sizing (11px voor TINY, 12px voor normal)

### Database Connecties
- Gebruik altijd proper cleanup (conn.close())
- Best practice: context managers
- Gescheiden database/GUI operaties

### Router Pattern
- Geef method door (`self.terug`), niet object (`self`)

### Schema Mismatches
- Altijd migratie scripts bij DB wijzigingen
- Check kolommen met `PRAGMA table_info()`

---

## SHIFT CODES SYSTEEM

### Interventie Post Codes

**Weekdag:**
- 7101 (V): 06:00-14:00 (8u)
- 7201 (L): 14:00-22:00 (8u)
- 7301 (N): 22:00-06:00 (8u)

**Zaterdag:**
- 7401 (V): 06:00-14:00 (8u)
- 7501 (L): 14:00-22:00 (8u)
- 7601 (N): 22:00-06:00 (8u)

**Zondag/RX:**
- 7701 (V): 06:00-14:00 (8u)
- 7801 (L): 14:00-22:00 (8u)
- 7901 (N): 22:00-06:00 (8u)

### Speciale Codes

| Code | Naam | Werkdag | Reset 12u | Breekt Reeks | Configureerbaar |
|------|------|---------|-----------|--------------|-----------------|
| VV | Verlof | ✓ | ✓ | ✗ | Eigenschappen |
| VD | Vrij van dienst | ✓ | ✓ | ✗ | Eigenschappen |
| DA | Arbeidsduurverkorting | ✓ | ✓ | ✗ | Eigenschappen |
| RX | Zondagsrust | ✗ | ✗ | ✓ | Eigenschappen |
| CX | Zaterdagsrust | ✗ | ✗ | ✓ | Eigenschappen |
| Z | Ziek | ✗ | ✓ | ✓ | Eigenschappen |
| RDS | Roadshow/Meeting | ✓ | ✗ | ✗ | Volledig |
| TCR/SCR | Opleiding | ✓ | ✗ | ✗ | Volledig |
| T | Reserve/Thuis | ✗ | ✗ | ✗ | Eigenschappen |

**Configuratie:**
- Alle speciale codes worden via seed data aangemaakt
- Planners kunnen via Speciale Codes scherm:
  - Nieuwe codes toevoegen (bijv. SCR als alternatief voor TCR)
  - Bestaande codes bewerken (naam, eigenschappen)
  - Codes verwijderen (alleen als niet in gebruik)
  - Eigenschappen instellen per code:
    * `telt_als_werkdag`: Telt mee voor 19 dagen/28d regel
    * `reset_12u_rust`: Reset de 12u rust periode
    * `breekt_werk_reeks`: Breekt reeks van werkdagen
    * `heeft_vaste_uren`: Code heeft vaste tijden (bijv. RDS 10:00-18:00)

### Typediensttabel
- 6-weken roterend patroon
- Bevat V/L/N/RX/CX/T codes
- Template voor planning generatie
- Reserves volgen GEEN typetabel

---

## HR REGELS

### Configureerbare Regels

1. **Min 12u rust** tussen shifts
   - VV/DA/VD reset deze regel
   - Z reset ook (maar breekt reeks)

2. **Max 50u/week**
   - Zondag 00:00 - zondag 23:59

3. **Max 19 gewerkte dagen/28d** (rode lijn)
   - RX/CX tellen NIET als gewerkte dag
   - Z telt NIET als gewerkte dag

4. **Max 7 dagen tussen RX/CX**
   - Kalenderdagen tussen rustdagen

5. **Max 7 werkdagen achter elkaar**
   - RX/CX breken de reeks
   - Z breekt ook de reeks

### Rode Lijnen Systeem

- 28-dagen cycli voor arbeidsduur validatie
- Start: 28 juli 2024
- Auto-extend via `ensure_jaar_data()`
- Periode nummers voor tracking

---

## CODE TEMPLATES

### Scherm Template

```python
"""
Scherm naam - Beschrijving
"""
from typing import Dict, Any, List, Optional, Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import sqlite3
from database.connection import get_connection
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig


class MijnScherm(QWidget):
    """Docstring"""
    
    # Signals als class attributes
    data_changed: pyqtSignal = pyqtSignal(dict)
    
    def __init__(self, router: Callable):
        super().__init__()
        self.router = router
        
        # Declareer ALLE instance attributes
        self.tabel: QTableWidget = QTableWidget()
        self.data: List[Dict[str, Any]] = []
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self) -> None:
        """Bouw UI"""
        layout = QVBoxLayout(self)
        
        # Header met terug knop
        header = QHBoxLayout()
        title = QLabel("Titel")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE))
        header.addWidget(title)
        header.addStretch()
        
        terug_btn = QPushButton("Terug")
        terug_btn.setFixedSize(100, Dimensions.BUTTON_HEIGHT_NORMAL)
        terug_btn.clicked.connect(self.router.terug)  # type: ignore
        terug_btn.setStyleSheet(Styles.button_secondary())
        header.addWidget(terug_btn)
        layout.addLayout(header)
        
        # Tabel
        self.tabel.setColumnCount(3)
        self.tabel.setHorizontalHeaderLabels(['Col1', 'Col2', 'Acties'])
        TableConfig.setup_table_widget(self.tabel, row_height=50)
        layout.addWidget(self.tabel)
    
    def load_data(self) -> None:
        """Laad data uit database"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
            self.data = cursor.fetchall()
            conn.close()
            self.display_data()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Fout", str(e))
    
    def display_data(self) -> None:
        """Toon data in tabel"""
        self.tabel.setRowCount(len(self.data))
        
        for row, item in enumerate(self.data):
            self.tabel.setItem(row, 0, QTableWidgetItem(str(item['field1'])))
            
            # Acties buttons
            actie_widget = QWidget()
            actie_layout = QHBoxLayout()
            actie_layout.setContentsMargins(0, 0, 0, 0)
            actie_layout.setSpacing(Dimensions.SPACING_SMALL)
            actie_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            btn = QPushButton("Actie")
            btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            btn.setFixedWidth(80)
            btn.setStyleSheet(Styles.button_primary(Dimensions.BUTTON_HEIGHT_TINY))
            btn.clicked.connect(self.create_callback(dict(item)))  # type: ignore
            actie_layout.addWidget(btn)
            
            actie_widget.setLayout(actie_layout)
            self.tabel.setCellWidget(row, 2, actie_widget)
    
    def create_callback(self, item: Dict[str, Any]):
        """Factory voor callbacks"""
        def callback():
            self.handle_action(item)
        return callback
    
    def handle_action(self, item: Dict[str, Any]) -> None:
        """Handle button click"""
        pass
```

### Dialog Template

```python
class MijnDialog(QDialog):
    """Dialog beschrijving"""
    
    def __init__(self, parent: Optional[QWidget] = None, data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("Dialog Titel")
        self.setModal(True)
        
        # Instance attributes
        self.input: QLineEdit = QLineEdit()
        
        self.init_ui()
    
    def init_ui(self) -> None:
        layout = QVBoxLayout()
        
        # Input field
        self.input.setPlaceholderText("Placeholder")
        self.input.setStyleSheet(Styles.input_field())
        layout.addWidget(self.input)
        
        # Buttons
        buttons = QDialogButtonBox()
        buttons.addButton(QDialogButtonBox.StandardButton.Ok)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.valideer_en_accept)  # type: ignore
        buttons.rejected.connect(self.reject)  # type: ignore
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def valideer_en_accept(self) -> None:
        """Valideer input"""
        if not self.input.text().strip():
            QMessageBox.warning(self, 'Fout', 'Vul een waarde in!')
            return
        self.accept()
    
    def get_data(self) -> str:
        """Return data"""
        return self.input.text().strip()
```

---

## OPTIMALISATIE VOOR .EXE

Bij conversie naar .exe voor netwerkschijf:

### PyInstaller Settings
```bash
pyinstaller --onefile --windowed \
    --exclude-module matplotlib \
    --exclude-module numpy \
    --exclude-module pandas \
    main.py
```

### UPX Compressie
```bash
# Installeer UPX
# Linux: apt-get install upx
# Windows: Download van upx.github.io

pyinstaller --onefile --windowed --upx-dir=/path/to/upx main.py
```

### Minimale Dependencies
- Virtual environment met alleen essentiële packages
- PyQt6 minimaal (geen QtWebEngine, etc.)
- SQLite embedded
- Geen externe dependencies waar mogelijk

### Performance Testing
- Test vanaf netwerkschijf
- Meet laadtijden
- Check latency bij database operaties
- Valideer memory usage

### Relatieve Paths
```python
# In main.py
if getattr(sys, 'frozen', False):
    # Running as .exe
    application_path = os.path.dirname(sys.executable)
else:
    # Running as script
    application_path = os.path.dirname(__file__)

db_path = os.path.join(application_path, 'data', 'planning.db')
```

---

## BELANGRIJKE CREDENTIALS

**Admin login:**
- Gebruikersnaam: `admin`
- Wachtwoord: `admin`

**Eerste run:**
- Database wordt automatisch aangemaakt
- Seed data wordt geladen
- Admin user wordt aangemaakt

---

## DEVELOPMENT WORKFLOW

### Voor Nieuwe Features
1. Check roadmap in PROJECT_INFO.md
2. Maak feature branch (optioneel)
3. Schrijf database migratie indien nodig
4. Gebruik scherm/dialog templates
5. Volg PyQt6 best practices
6. Test grondig (vooral table layouts!)
7. Update documentatie

### Voor Bugfixes
1. Reproduceer bug
2. Check Known Issues sectie
3. Fix implementeren
4. Test oplossing
5. Document in DEVELOPMENT_GUIDE.md

### Voor Database Changes
1. Schrijf migratie script
2. Test migratie op kopie
3. Update connection.py (create_tables)
4. Update seed data indien nodig
5. Commit migratie script

---

## DASHBOARD & MAIN.PY - MENU SYSTEEM

### Hoe het Dashboard Menu Werkt

Het dashboard gebruikt een **centraal event handling systeem** via signals en één handler methode.

#### Architectuur
Dashboard Menu Button
↓ (click)
create_menu_button() - Maakt widget met titel
↓ (mousePressEvent)
handle_menu_click(title) - Centraal routing punt
↓ (emit signal)
Signal (bijv. planning_clicked)
↓ (connected in main.py)
MainWindow handler (bijv. on_planning_clicked)
↓
Toon scherm via stack.addWidget()

### Stap-voor-Stap: Nieuw Menu Item Toevoegen

#### 1. Dashboard Signal Declareren

In `gui/screens/dashboard_screen.py` (class-level, rond regel 20):
```python
class DashboardScreen(QWidget):
    # Bestaande signals
    gebruikers_clicked = pyqtSignal()
    planning_clicked = pyqtSignal()
    # ... etc
    
    # NIEUW signal toevoegen
    jouw_nieuwe_feature_clicked = pyqtSignal()
```
###  2. Menu Button Maken   
In de juiste tab methode (create_beheer_tab, create_persoonlijk_tab, of create_instellingen_tab):
```python
scroll_layout.addWidget(self.create_menu_button(
    "Jouw Feature Naam",
    "Beschrijving van wat deze knop doet"
))
```
### 3. Handler Toevoegen
In handle_menu_click(self, title: str) methode (rond regel 380):
```python
def handle_menu_click(self, title: str) -> None:
    """Handle menu button clicks"""
    # ... bestaande handlers ...
    
    elif title == "Jouw Feature Naam":
        self.jouw_nieuwe_feature_clicked.emit()  # type: ignore
```
⚠️ BELANGRIJK: Titel in create_menu_button() moet EXACT matchen met titel in handle_menu_click()!

###4. Signal Connecten in Main
In main.py in de show_dashboard() methode (rond regel 60):
```python
def show_dashboard(self) -> None:
    """Toon dashboard"""
    dashboard = DashboardScreen(self.current_user)
    
    # Bestaande connections
    dashboard.planning_clicked.connect(self.on_planning_clicked)  # type: ignore
    # ... etc
    
    # NIEUW connection toevoegen
    dashboard.jouw_nieuwe_feature_clicked.connect(self.on_jouw_nieuwe_feature_clicked)  # type: ignore
```

### 5. Handler Methode in Main
In main.py (rond regel 150):
```python
def on_jouw_nieuwe_feature_clicked(self) -> None:
    """Jouw feature scherm openen"""
    if not self.current_user:
        return
    
    from types import SimpleNamespace
    router = SimpleNamespace(terug=self.terug)
    scherm = JouwFeatureScreen(router, self.current_user['id'])  # type: ignore[arg-type]
    self.stack.addWidget(scherm)
    self.stack.setCurrentWidget(scherm)
```
Pattern voor router:
✅ Gebruik SimpleNamespace(terug=self.terug) voor schermen die router.terug() aanroepen
✅ Gebruik self.terug direct voor schermen die router() aanroepen (zoals GebruikersbeheerScreen)

### 6. Bestaande Menu Items & Handlers
✅ VOLLEDIG GEÏMPLEMENTEERD
### Menu Systeem - Screens & Handlers

| Menu Item         | Tab         | Signal               | Handler                  | Screen File               |
|-------------------|-------------|-----------------------|---------------------------|---------------------------|
| Gebruikersbeheer  | Beheer      | `gebruikers_clicked`  | `on_gebruikers_clicked()` | `gebruikersbeheer_screen.py` |
| Feestdagen        | Instellingen| `feestdagen_clicked`  | `on_feestdagen_clicked()` | `feestdagen_screen.py`       |
| Kalender Test     | Beheer      | `kalender_test_clicked` | `on_kalender_test_clicked()` | `kalender_test_screen.py`    |
| Mijn Planning     | Persoonlijk | `planning_clicked`    | `on_planning_clicked()`   | `mijn_planning_screen.py`    |
| Wijzig Wachtwoord | Persoonlijk | N/A                   | `show_wachtwoord_dialog()` | (dialog in dashboard)        |

🔨 TODO (Signals bestaan, maar geen implementatie)
### Menu Systeem Overzicht

| Menu Item               | Tab             | Signal                | Handler               | Status |
|-------------------------|-----------------|------------------------|------------------------|--------|
| Planning Editor         | Beheer          | `planning_clicked`     | `on_planning_clicked()` | ⚠️ Gebruikt zelfde signal als "Mijn Planning" |
| Verlof Aanvragen        | Persoonlijk     | `verlof_clicked`       | `on_verlof_clicked()`   | TODO |
| Verlof Goedkeuring      | Beheer          | `verlof_clicked`       | `on_verlof_clicked()`   | TODO – zelfde handler |
| Mijn Voorkeuren         | Persoonlijk     | `voorkeuren_clicked`   | `on_voorkeuren_clicked()` | TODO |
| HR Regels               | Instellingen    | `hr_regels_clicked`    | `on_hr_regels_clicked()` | TODO |
| Shift Codes & Posten    | Instellingen    | `shift_codes_clicked`  | `on_shift_codes_clicked()` | TODO |
| Rode Lijnen             | Instellingen    | `rode_lijnen_clicked`  | `on_rode_lijnen_clicked()` | TODO |

⚠️ BELANGRIJK: Planning Editor vs Mijn Planning
Probleem: Beide menu items gebruiken hetzelfde signal (planning_clicked)!
Huidige situatie:

"Planning Editor" (Beheer tab) → emit planning_clicked
"Mijn Planning" (Persoonlijk tab) → emit planning_clicked
Beide roepen on_planning_clicked() aan
Handler toont MijnPlanningScreen (teamlid view)

Oplossing voor Planning Editor:
Wanneer je Planning Editor implementeert, heb je 2 opties:
Optie A: Apart signal voor Planning Editor
```python
# Dashboard
planning_editor_clicked = pyqtSignal()

# handle_menu_click
elif title == "Planning Editor":
    self.planning_editor_clicked.emit()  # type: ignore

# main.py
dashboard.planning_editor_clicked.connect(self.on_planning_editor_clicked)  # type: ignore

def on_planning_editor_clicked(self) -> None:
    """Planning editor voor planners"""
    # Toon PlannerGridKalender in editable mode
```
Optie B: Rol-based routing in handler
```python
def on_planning_clicked(self) -> None:
    """Planning scherm - rol afhankelijk"""
    if not self.current_user:
        return
    
    if self.current_user['rol'] == 'planner':
        # Toon Planning Editor (PlannerGridKalender)
        router = SimpleNamespace(terug=self.terug)
        scherm = PlanningEditorScreen(router)
        self.stack.addWidget(scherm)
        self.stack.setCurrentWidget(scherm)
    else:
        # Toon Mijn Planning (TeamlidGridKalender)
        router = SimpleNamespace(terug=self.terug)
        scherm = MijnPlanningScreen(router, self.current_user['id'])
        self.stack.addWidget(scherm)
        self.stack.setCurrentWidget(scherm)
```
Aanbeveling: Optie A is cleaner en volgt de bestaande architectuur beter.

### 7.Common Pitfalls
❌ FOUT - Titel niet exact gelijk:
```python
# In create_menu_button
"Gebruikers Beheer"  # Met spatie

# In handle_menu_click
elif title == "Gebruikersbeheer":  # Zonder spatie - WERKT NIET!
```
❌ FOUT - Verkeerd router object:
```python
# Dit werkt NIET
scherm = MijnScreen(self.terug, user_id)

# Dit werkt WEL
from types import SimpleNamespace
router = SimpleNamespace(terug=self.terug)
scherm = MijnScreen(router, user_id)
```
❌ FOUT - Signal vergeten connecten:
```python
# Signal gedeclareerd in dashboard ✓
# Handler toegevoegd aan handle_menu_click ✓
# Methode in main.py gemaakt ✓
# MAAR: Signal niet geconnect in show_dashboard() ✗
# Resultaat: Button doet niks!
```
Debugging Tips
Button doet niks bij klikken:

Check of titel in create_menu_button() exact matcht met handle_menu_click()
Check of signal emit statement bestaat in handle_menu_click()
Check of signal connected is in show_dashboard()
Check of handler methode bestaat in main.py

AttributeError bij router:

Gebruik SimpleNamespace(terug=self.terug) voor nieuwe schermen
Check of screen verwacht router.terug() of router()

Print debug in handle_menu_click:
```python
def handle_menu_click(self, title: str) -> None:
    """Handle menu button clicks"""
    print(f"DEBUG: Menu clicked - {title}")  # ADD THIS
    
    if title == "...":
        # ...
```
Dit toont je exact welke titel wordt doorgegeven.

of run main.py in terminal:
```bash
python main.py
```
Dit toont je alle print statements in de terminal.

*Laatste update: Oktober 2025*
*Versie: 1.0*