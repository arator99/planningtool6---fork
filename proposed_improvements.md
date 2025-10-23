# Proposed Improvements - Planning Tool

**Context:** Single-developer desktop app (PyQt6 + SQLite), beta fase richting v1.0 (December 2025)

## Prioritering Filosofie

1. **Hoge waarde, lage inspanning** - Quick wins eerst
2. **Specifiek voor dit project** - Geen enterprise overhead
3. **Pragmatisch** - Alleen wat echt helpt bij development/debugging
4. **v1.0 focus** - Verbeteringen die release-readiness ondersteunen

---

## A. High Priority (Toepassen voor v1.0)

### 1. Database Backup bij Migraties ⭐⭐⭐

**Probleem:** Migraties draaien direct tegen database zonder safety net. Bij fout of stroomuitval is data weg.

**Oplossing:** Automatische backup functie toevoegen aan alle migratie scripts.

```python
import shutil
from datetime import datetime

def backup_database(db_path: str) -> str:
    """Maak backup van database voor migratie"""
    backup_path = f"{db_path}.{datetime.now():%Y%m%d_%H%M%S}.backup"
    shutil.copyfile(db_path, backup_path)
    print(f"[BACKUP] Database backup: {backup_path}")
    return backup_path

# Gebruik in alle migratie scripts:
backup_database("data/planning.db")
```

**Impact:** Data safety verhoogd, confidence bij migraties verhoogd.

**Effort:** 1-2 uur voor alle migratie scripts.

**Files:**
- Alle `migratie_*.py` files
- Alle `upgrade_to_v*.py` files

---

### 2. Structured Logging voor Debugging ⭐⭐⭐

**Probleem:** `print()` statements zijn moeilijk te filteren, geen timestamps, verdwijnen in console clutter.

**Oplossing:** Python `logging` module met niveaus (INFO, WARNING, ERROR).

```python
# logging_config.py (nieuw bestand)
import logging
import sys
from datetime import datetime

def setup_logging(log_file: str = None):
    """Configure logging voor Planning Tool"""

    # Format: [2025-10-23 14:32:15] INFO: Message here
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Optional file handler
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Root logger
    logging.basicConfig(level=logging.DEBUG, handlers=handlers)

# main.py usage:
from logging_config import setup_logging
import logging

setup_logging()  # Of: setup_logging("logs/app.log")
logger = logging.getLogger(__name__)

logger.info("Applicatie gestart")
logger.warning("Database oudere versie gedetecteerd")
logger.error("Migratie gefaald", exc_info=True)  # Includes traceback
```

**Waar toepassen:**
- ✅ Migratie scripts (errors, warnings)
- ✅ Services (data_ensure_service, verlof_saldo_service)
- ✅ Database operations (connection errors)
- ❌ NIET: GUI code (PyQt6 heeft eigen error handling)

**Impact:** Debugging 5x sneller, betere error diagnostics voor gebruikers.

**Effort:** 2-3 uur implementatie + 1 uur refactoring bestaande prints.

**Files:**
- `logging_config.py` (nieuw)
- `main.py`
- Alle `services/*.py`
- Alle `migratie_*.py`

---

### 3. Batch Database Operations ⭐⭐

**Probleem:** Auto-generatie en bulk operaties doen nu één INSERT per iteratie (slow voor grote datasets).

**Oplossing:** `executemany()` voor bulk inserts + single transaction.

```python
# Voor - Slow (N queries)
for dag in dagen:
    cursor.execute("""
        INSERT INTO planning (gebruiker_id, datum, shift_code)
        VALUES (?, ?, ?)
    """, (user_id, dag, code))
    conn.commit()  # Commit per insert!

# Na - Fast (1 query)
data = [
    (user_id, dag, code)
    for dag, code in planning_data
]
cursor.executemany("""
    INSERT INTO planning (gebruiker_id, datum, shift_code)
    VALUES (?, ?, ?)
""", data)
conn.commit()  # Eén keer commit
```

**Impact:** 10-100x sneller voor bulk operaties (typetabel generation).

**Effort:** 1-2 uur refactoring.

**Files:**
- `gui/dialogs/auto_generatie_dialog.py`
- `services/data_ensure_service.py`

---

### 4. Consistente Database Connection Patterns ⭐⭐

**Probleem:** Mix van `get_connection()` + manual close vs. context managers (`with` blocks).

**Oplossing:** Overal context managers gebruiken voor automatic cleanup.

```python
# Voor - Manual cleanup (risk van resource leak)
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM gebruikers")
results = cursor.fetchall()
conn.close()  # Vergeten = resource leak

# Na - Context manager (automatic cleanup)
with get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gebruikers")
    results = cursor.fetchall()
# conn.close() automatisch geroepen
```

**Impact:** Geen resource leaks, cleaner code.

**Effort:** 2-3 uur refactoring (grep voor `get_connection()` patterns).

**Files:**
- Alle `gui/screens/*.py`
- Alle `gui/dialogs/*.py`

---

## B. Medium Priority (Nice-to-have voor v1.0)

### 5. Error Messages met Context ⭐

**Probleem:** Generic error messages helpen niet bij debugging ("Error: constraint failed").

**Oplossing:** Specifieke error messages met context.

```python
# Voor
try:
    cursor.execute("INSERT INTO planning ...")
except sqlite3.IntegrityError:
    QMessageBox.warning(self, "Error", "Constraint failed")

# Na
try:
    cursor.execute("INSERT INTO planning (gebruiker_id, datum) VALUES (?, ?)",
                   (user_id, datum))
except sqlite3.IntegrityError as e:
    QMessageBox.warning(
        self,
        "Database Error",
        f"Kan planning niet opslaan voor {user_name} op {datum}:\n{str(e)}"
    )
```

**Impact:** Betere user experience, snellere debugging.

**Effort:** Ongoing - toevoegen waar errors voorkomen.

---

### 6. Database Vacuum Functie ⭐

**Probleem:** SQLite databases fragmenteren na veel soft deletes (`is_actief=0`). File size groeit onnodig.

**Oplossing:** Maintenance functie voor database optimalisatie.

```python
# database/maintenance.py (nieuw)
def vacuum_database():
    """Optimize database (remove deleted records, rebuild indexes)"""
    with get_connection() as conn:
        # Vacuum requires no open transactions
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
    print("Database geoptimaliseerd")

# Roep aan vanuit admin tools of na grote cleanup operaties
```

**Impact:** Kleinere database size, betere performance.

**Effort:** 30 minuten implementatie.

---

### 7. Settings Validation ⭐

**Probleem:** Invalid configuratie kan leiden tot crashes (bijv. ongeldige rode lijnen config).

**Oplossing:** Validatie bij opslaan van configs.

```python
# Voorbeeld: Rode lijnen config validation
def validate_rode_lijnen_config(startdatum, frequentie_dagen):
    errors = []

    if not startdatum:
        errors.append("Startdatum is verplicht")

    if frequentie_dagen < 1 or frequentie_dagen > 365:
        errors.append("Frequentie moet tussen 1-365 dagen zijn")

    # Check startdatum is niet in verre toekomst
    if startdatum > datetime.now() + timedelta(days=365):
        errors.append("Startdatum mag niet meer dan 1 jaar in toekomst zijn")

    return errors

# Voor opslaan:
errors = validate_rode_lijnen_config(startdatum, freq)
if errors:
    QMessageBox.warning(self, "Validatie", "\n".join(errors))
    return
```

**Impact:** Voorkomt invalid state, betere UX.

**Effort:** 1-2 uur per config screen.

---

## C. Low Priority (Post v1.0)

### 8. Unit Tests voor Core Services

**Waarom Low Priority:** Tests zijn waardevol, maar overhead voor snelle iteratie in beta fase.

**Post v1.0 plan:**
```python
# tests/test_verlof_saldo_service.py
import unittest
from services.verlof_saldo_service import bereken_opgenomen_dagen

class TestVerlofSaldoService(unittest.TestCase):
    def test_bereken_opgenomen_dagen_vv(self):
        # Setup test database
        # Test berekening
        # Assert resultaat
        pass
```

**Prioriteit:** Doe dit NA v1.0 als codebase stabiel is.

---

### 9. Code Linting (ruff/flake8)

**Waarom Low Priority:** Code is al redelijk consistent, type hints aanwezig.

**Als je het toch wil:**
```bash
pip install ruff
ruff check .  # Find issues
ruff format .  # Auto-format
```

**Prioriteit:** Optioneel, weinig ROI voor solo dev.

---

### 10. Performance Profiling

**Waarom Low Priority:** Geen performance complaints, SQLite is fast genoeg voor local use.

**Als performance issue opduikt:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
auto_genereer_planning()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(20)  # Top 20 slowest functions
```

**Prioriteit:** Alleen als daadwerkelijk probleem.

---

## Implementation Roadmap

### Sprint 1 (1-2 dagen werk)
1. ✅ Database backup functie toevoegen aan alle migraties
2. ✅ Logging config setup + refactor migratie scripts
3. ✅ Batch operations in auto_generatie_dialog.py

### Sprint 2 (2-3 dagen werk)
4. ✅ Context managers overal consistent maken
5. ✅ Error messages met context verbeteren
6. ✅ Database vacuum functie toevoegen

### Sprint 3 (optioneel, post v1.0)
7. ⏳ Settings validation toevoegen
8. ⏳ Unit tests schrijven voor core services

---

## What NOT to Do (Anti-Patterns voor dit project)

❌ **CI/CD pipelines** - Geen server, geen deployments
❌ **Docker containers** - Desktop app, niet relevant
❌ **Microservices** - SQLite + PyQt6 is monolith by design
❌ **API versioning** - Geen API
❌ **Load balancers** - Single-user desktop app
❌ **i18n/l10n** - Nederlands-only project
❌ **ORM (SQLAlchemy)** - Overhead, raw SQL is fine

---

## Success Metrics (Praktisch)

- ✅ Geen data verlies bij migraties (backup werkt)
- ✅ Debugging 50% sneller (structured logging)
- ✅ Auto-generatie <2 seconden voor 12 maanden (batch ops)
- ✅ Geen resource warnings in lange sessies (context managers)
- ✅ Gebruikers begrijpen error messages (specifieke context)

---

## Next Steps

1. **Review dit plan** - Goedkeuring voor Sprint 1
2. **Start met #1** - Database backup (highest value, lowest risk)
3. **Incrementeel toepassen** - Niet alles tegelijk
4. **Test na elke change** - Run app, test migraties

**Estimated total effort:** 6-8 uur voor High Priority items.

**ROI:** Significant betere developer experience + v1.0 release readiness.
