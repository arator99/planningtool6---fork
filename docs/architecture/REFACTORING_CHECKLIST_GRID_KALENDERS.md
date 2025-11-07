# REFACTORING CHECKLIST: Grid Kalender Code Cleanup

**Datum:** 27 Oktober 2025
**Doel:** Elimineer 170 regels code duplicatie tussen Planner en Teamlid grid kalenders
**Geschatte tijd:** 1-1.5 uur
**Status:** ⏸️ Klaar om te beginnen

---

## 📦 BACKUPS GEMAAKT ✅

**Locatie:** `backups/refactoring_grid_kalenders_20251027/`

- ✅ `grid_kalender_base_BEFORE_REFACTOR.py` (17K)
- ✅ `planner_grid_kalender_BEFORE_REFACTOR.py` (58K)
- ✅ `teamlid_grid_kalender_BEFORE_REFACTOR.py` (16K)

**Restore command (indien nodig):**
```bash
cp backups/refactoring_grid_kalenders_20251027/*.py gui/widgets/
# Verwijder dan _BEFORE_REFACTOR suffix
```

---

## 🎯 REFACTORING STAPPEN

### PHASE 1: GridKalenderBase - Voeg Gemeenschappelijke Methods Toe (~30 min)

#### Stap 1.1: load_rode_lijnen()
- [ ] Kopieer van `planner_grid_kalender.py` (regel 376-398)
- [ ] Plak in `grid_kalender_base.py` (na bestaande methods)
- [ ] Voeg docstring toe: "Laad rode lijnen (28-daagse HR-cycli) voor huidige periode"
- [ ] Voeg type hints toe: `-> None`

**Code om te verplaatsen:**
```python
def load_rode_lijnen(self) -> None:
    """Laad rode lijnen (28-daagse HR-cycli) voor huidige periode"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT start_datum, eind_datum, periode_nummer
        FROM rode_lijnen
        ORDER BY start_datum
    """)

    self.rode_lijnen_starts: Dict[str, int] = {}
    for row in cursor.fetchall():
        datum_str = row['start_datum']
        if 'T' in datum_str:
            datum_str = datum_str.split('T')[0]
        self.rode_lijnen_starts[datum_str] = row['periode_nummer']

    conn.close()
```

#### Stap 1.2: update_title()
- [ ] Kopieer van `planner_grid_kalender.py` (regel 315-319)
- [ ] Plak in `grid_kalender_base.py`

**Code om te verplaatsen:**
```python
def update_title(self) -> None:
    """Update titel met maand/jaar"""
    maanden = ['Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni',
               'Juli', 'Augustus', 'September', 'Oktober', 'November', 'December']
    self.title_label.setText(f"Planning {maanden[self.maand - 1]} {self.jaar}")
```

#### Stap 1.3: on_jaar_changed()
- [ ] Kopieer van `planner_grid_kalender.py` (regel 1454-1456)
- [ ] Plak in `grid_kalender_base.py`

**Code om te verplaatsen:**
```python
def on_jaar_changed(self, jaar_str: str) -> None:
    """Jaar gewijzigd"""
    self.refresh_data(int(jaar_str), self.maand)
```

#### Stap 1.4: on_maand_changed()
- [ ] Kopieer van `planner_grid_kalender.py` (regel 1458-1460)
- [ ] Plak in `grid_kalender_base.py`

**Code om te verplaatsen:**
```python
def on_maand_changed(self, index: int) -> None:
    """Maand gewijzigd"""
    self.refresh_data(self.jaar, index + 1)
```

#### Stap 1.5: open_filter_dialog()
- [ ] Kopieer van `teamlid_grid_kalender.py` (regel 304-309)
- [ ] Plak in `grid_kalender_base.py`
- [ ] Pas import aan indien nodig

**Code om te verplaatsen:**
```python
def open_filter_dialog(self) -> None:
    """Open dialog om gebruikers te filteren"""
    from gui.widgets.teamlid_grid_kalender import FilterDialog
    dialog = FilterDialog(self.gebruikers_data, self.filter_gebruikers, self)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        self.filter_gebruikers = dialog.get_filter()
        self.build_grid()
```

#### Stap 1.6: Template Method Pattern - get_header_extra_buttons()
- [ ] Voeg nieuwe method toe in `grid_kalender_base.py`:

```python
def get_header_extra_buttons(self) -> List[QPushButton]:
    """
    Override in subclass voor extra header buttons
    Returns: List van buttons om toe te voegen
    """
    return []  # Default: geen extra buttons
```

#### Stap 1.7: Refactor create_header() in Base
- [ ] **LET OP:** Dit is de meest complexe stap!
- [ ] Neem bestaande `create_header()` van planner als basis
- [ ] Vervang hardcoded "Vorige/Volgende Maand" buttons met:
```python
# Subclass hook voor extra buttons (bijv. vorige/volgende maand)
extra_buttons = self.get_header_extra_buttons()
for btn in extra_buttons:
    header.addWidget(btn)
```
- [ ] Test dat base versie werkt zonder extra buttons

---

### PHASE 2: PlannerGridKalender - Verwijder Duplicatie & Override (~20 min)

#### Stap 2.1: Verwijder Gedupliceerde Methods
- [ ] **DELETE:** `load_rode_lijnen()` (regel 376-398) - nu in base
- [ ] **DELETE:** `update_title()` (regel 315-319) - nu in base
- [ ] **DELETE:** `on_jaar_changed()` (regel 1454-1456) - nu in base
- [ ] **DELETE:** `on_maand_changed()` (regel 1458-1460) - nu in base
- [ ] **DELETE:** `open_filter_dialog()` (regel 1426-1432) - nu in base
- [ ] **DELETE:** `create_header()` volledig (regel 254-313) - nu in base

#### Stap 2.2: Override get_header_extra_buttons()
- [ ] Voeg nieuwe method toe voor navigatie buttons:

```python
def get_header_extra_buttons(self) -> List[QPushButton]:
    """Voeg vorige/volgende maand buttons toe"""
    buttons = []

    vorige_btn = QPushButton("← Vorige Maand")
    vorige_btn.setFixedSize(130, Dimensions.BUTTON_HEIGHT_NORMAL)
    vorige_btn.clicked.connect(self.vorige_maand)  # type: ignore
    vorige_btn.setStyleSheet(Styles.button_secondary())
    buttons.append(vorige_btn)

    volgende_btn = QPushButton("Volgende Maand →")
    volgende_btn.setFixedSize(150, Dimensions.BUTTON_HEIGHT_NORMAL)
    volgende_btn.clicked.connect(self.volgende_maand)  # type: ignore
    volgende_btn.setStyleSheet(Styles.button_secondary())
    buttons.append(volgende_btn)

    return buttons
```

#### Stap 2.3: Behoud Planner-Specifieke Methods
- [ ] **KEEP:** `vorige_maand()` - planner specifiek
- [ ] **KEEP:** `volgende_maand()` - planner specifiek
- [ ] Zorg dat deze methods blijven werken (worden aangeroepen via buttons)

---

### PHASE 3: TeamlidGridKalender - Verwijder Duplicatie (~15 min)

#### Stap 3.1: Verwijder Gedupliceerde Methods
- [ ] **DELETE:** `load_rode_lijnen()` (regel 140-162) - nu in base
- [ ] **DELETE:** `update_title()` (regel 101-105) - nu in base
- [ ] **DELETE:** `on_jaar_changed()` (regel 311-313) - nu in base
- [ ] **DELETE:** `on_maand_changed()` (regel 315-317) - nu in base
- [ ] **DELETE:** `open_filter_dialog()` (regel 304-309) - nu in base
- [ ] **DELETE:** `create_header()` volledig (regel 53-99) - nu in base

#### Stap 3.2: GEEN Override Nodig
- [ ] Teamlid gebruikt default `get_header_extra_buttons()` (lege lijst)
- [ ] Geen extra buttons = correct gedrag

---

### PHASE 4: Testing & Verificatie (~15-20 min)

#### Stap 4.1: Syntax Check
- [ ] Run `python -m py_compile gui/widgets/grid_kalender_base.py`
- [ ] Run `python -m py_compile gui/widgets/planner_grid_kalender.py`
- [ ] Run `python -m py_compile gui/widgets/teamlid_grid_kalender.py`
- [ ] Alle files moeten zonder errors compileren

#### Stap 4.2: Start Applicatie
- [ ] Run `python main.py`
- [ ] Applicatie moet starten zonder errors
- [ ] Login als admin

#### Stap 4.3: Test Planning Editor (Planner Grid)
- [ ] Open Planning Editor
- [ ] **Test:** Vorige/Volgende Maand buttons werken
- [ ] **Test:** Filter dialog opent en werkt
- [ ] **Test:** Jaar/maand dropdowns werken
- [ ] **Test:** Titel update correct
- [ ] **Test:** Rode lijnen zichtbaar op correcte data
- [ ] **Test:** Maand navigatie behoudt filter
- [ ] **Test:** Multi-cell selectie werkt (v0.6.17 feature)
- [ ] **Test:** Bulk operations werken

#### Stap 4.4: Test Mijn Planning (Teamlid Grid)
- [ ] Open Mijn Planning
- [ ] **Test:** GEEN Vorige/Volgende Maand buttons (correct!)
- [ ] **Test:** Filter dialog opent en werkt
- [ ] **Test:** Jaar/maand dropdowns werken
- [ ] **Test:** Titel update correct
- [ ] **Test:** Rode lijnen zichtbaar op correcte data
- [ ] **Test:** Alleen gepubliceerde planning zichtbaar

#### Stap 4.5: Regression Testing
- [ ] Test alle basis functionaliteit blijft werken:
  - [ ] Auto-generatie planning
  - [ ] Cel edit in planning grid
  - [ ] Notities toevoegen
  - [ ] Context menu opties
  - [ ] Status toggle (concept/gepubliceerd)
  - [ ] Bulk delete/fill (v0.6.17)

---

## 🚨 TROUBLESHOOTING

### Probleem: ImportError na refactoring
**Oplossing:** Check dat alle imports correct zijn in base class
```python
from typing import Dict, List, Optional
from PyQt6.QtWidgets import QPushButton
from database.connection import get_connection
```

### Probleem: AttributeError: 'PlannerGridKalender' object has no attribute 'title_label'
**Oplossing:** Zorg dat `super().__init__()` VOOR `self.init_ui()` wordt aangeroepen

### Probleem: Buttons verschijnen niet
**Oplossing:** Check dat `get_header_extra_buttons()` override correct geïmplementeerd is

### Probleem: Applicatie crasht bij openen grid
**Oplossing:**
1. Check logs voor exacte error
2. Restore backups en start opnieuw:
```bash
cp backups/refactoring_grid_kalenders_20251027/*.py gui/widgets/
# Verwijder _BEFORE_REFACTOR suffix
```

---

## 📊 VERIFICATIE CHECKLIST

Na voltooiing, verifieer:

- [ ] Code reductie: Planner ~-90 regels, Teamlid ~-80 regels
- [ ] Base class: ~+116 regels
- [ ] Netto: ~-54 regels (-2.3%)
- [ ] Alle tests slagen
- [ ] Geen console errors
- [ ] Gebruikers ervaring identiek (voor planner) of verbeterd (voor teamlid)

---

## ✅ NA VOLTOOIING

### Stap 1: Commit Changes
```bash
git add gui/widgets/grid_kalender_base.py
git add gui/widgets/planner_grid_kalender.py
git add gui/widgets/teamlid_grid_kalender.py
git commit -m "Refactoring - Grid Kalender Code Cleanup (v0.6.18)

- Verplaats 7 gedupliceerde methods naar GridKalenderBase
- Template method pattern voor create_header()
- PlannerGridKalender: override get_header_extra_buttons() voor navigatie
- TeamlidGridKalender: gebruik default (geen extra buttons)
- Code reductie: -54 regels netto (-2.3%)
- Maintainability: bugfixes in 1 plek = beide widgets fixed

Technical debt eliminated: 170 regels duplicatie verwijderd

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
"
```

### Stap 2: Update Documentatie
- [ ] Update `config.py`: `APP_VERSION = "0.6.18"`
- [ ] Update `DEV_NOTES.md`: Verplaats van TODO naar "Voltooid" sectie
- [ ] Update `PROJECT_INFO.md`: Voeg v0.6.18 sectie toe
- [ ] Update `DEVELOPMENT_GUIDE.md`: Verwijder "Known Technical Debt" sectie
- [ ] Update `CLAUDE.md`: Versie naar 0.6.18

### Stap 3: Volgende Features Implementeren
Nu kan je zonder duplicatie:
- [ ] Navigatie buttons in Mijn Planning (komt automatisch!)
- [ ] Status indicator voor teamleden (15-20 min)

---

## 📝 NOTITIES

**Belangrijkste risico's:**
- Signal/slot verbindingen: Let op `super().__init__()` volgorde
- Import dependencies: FilterDialog moet toegankelijk blijven
- Type hints: Voeg overal toe voor IDE support

**Voordelen na refactoring:**
- ✅ DRY principle
- ✅ Single source of truth
- ✅ Betere testability
- ✅ Klaar voor nieuwe features
- ✅ Minder bugs in de toekomst

**Geschatte besparing:**
- Development tijd: ~30% sneller voor toekomstige grid features
- Bug fixes: 1 plek ipv 2
- Code review: Veel simpeler

---

*Gemaakt op: 27 Oktober 2025*
*Voor: Grid Kalender Refactoring v0.6.18*
*Backup locatie: backups/refactoring_grid_kalenders_20251027/*
