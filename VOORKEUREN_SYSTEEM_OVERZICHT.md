# Shift Voorkeuren Systeem - Overzicht

**Versie:** 0.6.11
**Datum:** 21 Oktober 2025

---

## 📊 SYSTEEM ARCHITECTUUR

```
┌─────────────────────────────────────────────────────────┐
│                      Dashboard                           │
│                   (Persoonlijk Tab)                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Mijn Voorkeuren      │ ← VoorkeurenScreen
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  4 ComboBoxes:        │
         │  - Vroege Dienst      │
         │  - Late Dienst        │
         │  - Nachtdienst        │
         │  - Typetabel          │
         └───────────┬───────────┘
                     │
         ┌───────────▼────────────────────┐
         │  Prioriteit Selectie:          │
         │  ○ (Geen voorkeur)             │
         │  ● 1 (Hoogste)                 │
         │  ○ 2                           │
         │  ○ 3                           │
         │  ○ 4 (Laagste)                 │
         └───────────┬────────────────────┘
                     │
         ┌───────────▼────────────────────┐
         │  Live Preview:                 │
         │  "1. Vroeg > 2. Typetabel"     │
         └───────────┬────────────────────┘
                     │
         ┌───────────▼────────────────────┐
         │  Validatie:                    │
         │  ✓ Geen dubbele prioriteiten   │
         │  ✓ JSON format correct         │
         └───────────┬────────────────────┘
                     │
         ┌───────────▼────────────────────┐
         │  Database Opslag:              │
         │  gebruikers.shift_voorkeuren   │
         │  JSON: {"1": "vroeg", ...}     │
         └────────────────────────────────┘
```

---

## 🗂️ DATABASE SCHEMA

### Tabel: `gebruikers`

**Nieuwe Kolom (v0.6.11):**
```sql
shift_voorkeuren TEXT
```

**Data Format:**
```json
{
  "1": "vroeg",
  "2": "typetabel",
  "3": "laat",
  "4": "nacht"
}
```

**Mogelijke Waarden:**
- `NULL` - Geen voorkeuren ingesteld
- `"vroeg"` - Voorkeur voor vroege diensten
- `"laat"` - Voorkeur voor late diensten
- `"nacht"` - Voorkeur voor nachtdiensten
- `"typetabel"` - Volg het standaard rooster patroon

**Voorbeelden:**
```json
// Scenario 1: Alleen vroege diensten
{"1": "vroeg"}

// Scenario 2: Vroeg met typetabel fallback
{"1": "vroeg", "2": "typetabel"}

// Scenario 3: Alle voorkeuren
{"1": "nacht", "2": "vroeg", "3": "typetabel", "4": "laat"}

// Scenario 4: Geen voorkeuren
NULL
```

---

## 💻 CODE STRUCTUUR

### Hoofdbestanden

**1. VoorkeurenScreen** (`gui/screens/voorkeuren_screen.py`)
```python
class VoorkeurenScreen(QWidget):
    # Instance attributes
    vroeg_combo: QComboBox
    laat_combo: QComboBox
    nacht_combo: QComboBox
    typetabel_combo: QComboBox
    huidige_voorkeuren: Dict[str, str]

    # Methoden
    def load_voorkeuren()           # Laad uit database
    def apply_voorkeuren_to_ui()    # Zet UI op geladen waarden
    def update_preview()            # Live preview updates
    def validate_voorkeuren()       # Valideer duplicaten
    def opslaan_voorkeuren()        # Sla op in database
    def reset_voorkeuren()          # Reset naar leeg
```

**2. Database Migratie** (`migratie_shift_voorkeuren.py`)
```python
def migreer_shift_voorkeuren():
    # Check of kolom al bestaat
    # Voeg shift_voorkeuren toe
    # Idempotent - kan meerdere keren draaien
```

**3. Main Handler** (`main.py`)
```python
def on_voorkeuren_clicked(self):
    # Open VoorkeurenScreen met user data
    # Add to stack
    # Set as current widget
```

---

## 🎨 UI/UX COMPONENTEN

### Info Box
```
┌────────────────────────────────────────┐
│ ℹ️ Hoe werkt het?                      │
│                                        │
│ • Prioriteit 1 = hoogste voorkeur     │
│ • Je kunt opties leeg laten           │
│ • 'Typetabel' = standaard patroon     │
│ • Voorkeuren krijgen voorrang         │
│ • Geen voorkeuren = typetabel default │
└────────────────────────────────────────┘
```

### Formulier Layout
```
┌────────────────────────────────────────┐
│ Vroege Dienst:     [Dropdown ▼]       │
│                    Shifts ochtend      │
│                                        │
│ Late Dienst:       [Dropdown ▼]       │
│                    Shifts middag/avond │
│                                        │
│ Nachtdienst:       [Dropdown ▼]       │
│                    Shifts nacht        │
│                                        │
│ Typetabel:         [Dropdown ▼]       │
│                    Standaard patroon   │
└────────────────────────────────────────┘
```

### Live Preview
```
✓ Huidige volgorde: 1. Vroeg > 2. Typetabel > 3. Laat
```

### Acties
```
┌────────────────────────────────────────┐
│         [Reset]      [Opslaan]         │
└────────────────────────────────────────┘
```

---

## 🔄 USER FLOW

### Instellen van Voorkeuren

```
1. Login als teamlid
   ↓
2. Dashboard → Persoonlijk tab
   ↓
3. Klik "Mijn Voorkeuren"
   ↓
4. Selecteer prioriteiten via dropdowns
   ↓
5. Live preview toont volgorde
   ↓
6. Klik "Opslaan"
   ↓
7. Bevestiging: "Voorkeuren opgeslagen!"
   ↓
8. Terug naar Dashboard
```

### Reset van Voorkeuren

```
1. Open "Mijn Voorkeuren"
   ↓
2. Klik "Reset naar Standaard"
   ↓
3. Bevestig in dialog
   ↓
4. Alle dropdowns → "(Geen voorkeur)"
   ↓
5. Handmatig opslaan of terug
```

---

## ✅ VALIDATIE REGELS

### 1. Geen Dubbele Prioriteiten
```
❌ FOUT:
  Vroeg: 1
  Laat:  1  ← Error: Prioriteit 1 al gebruikt!

✓ CORRECT:
  Vroeg: 1
  Laat:  2
```

### 2. Gedeeltelijke Invulling Toegestaan
```
✓ GELDIG:
  Vroeg:     1
  Laat:      (Geen voorkeur)
  Nacht:     (Geen voorkeur)
  Typetabel: 2
```

### 3. Alle Leeg = Geen Voorkeuren
```
✓ GELDIG (default gedrag):
  Vroeg:     (Geen voorkeur)
  Laat:      (Geen voorkeur)
  Nacht:     (Geen voorkeur)
  Typetabel: (Geen voorkeur)

  → Database: NULL
  → Systeem gebruikt typetabel of vrije invulling
```

---

## 🔮 TOEKOMSTIG GEBRUIK

### Planning Generatie Algoritme

```python
def genereer_planning_met_voorkeuren(gebruiker_id, datum):
    # 1. Haal voorkeuren op
    voorkeuren = load_shift_voorkeuren(gebruiker_id)

    # 2. Loop door prioriteiten (1 → 4)
    for prioriteit in sorted(voorkeuren.keys()):
        shift_type = voorkeuren[prioriteit]

        # 3. Probeer shift toe te wijzen
        if is_shift_beschikbaar(shift_type, datum):
            if voldoet_aan_hr_regels(gebruiker_id, shift_type, datum):
                return assign_shift(gebruiker_id, shift_type, datum)

    # 4. Fallback: typetabel of vrije invulling
    return generate_from_typetabel(gebruiker_id, datum)
```

### Scenario's

**Scenario 1: Vroeg voorkeur**
```json
Voorkeuren: {"1": "vroeg", "2": "typetabel"}

Planning generatie:
1. Probeer vroege dienst → Beschikbaar? Ja → Toegewezen ✓
```

**Scenario 2: Vroeg voorkeur, maar niet beschikbaar**
```json
Voorkeuren: {"1": "vroeg", "2": "laat", "3": "typetabel"}

Planning generatie:
1. Probeer vroege dienst → Niet beschikbaar ✗
2. Probeer late dienst → Beschikbaar? Ja → Toegewezen ✓
```

**Scenario 3: Geen voorkeuren**
```json
Voorkeuren: NULL

Planning generatie:
1. Gebruik typetabel standaard → Toegewezen ✓
```

---

## 📈 STATISTIEKEN & MONITORING

### Toekomstige Analytics

**Voorkeur Verdeling:**
```sql
SELECT
    shift_voorkeuren,
    COUNT(*) as aantal_gebruikers
FROM gebruikers
WHERE shift_voorkeuren IS NOT NULL
GROUP BY shift_voorkeuren;
```

**Top Voorkeuren:**
```sql
-- Extract shift types from JSON
-- Count occurrences
-- Rank by popularity
```

**Voorkeur Satisfaction Rate:**
```
(Aantal shifts volgens voorkeur) / (Totaal aantal shifts) * 100%
```

---

## 🧪 TEST SCENARIOS

### Test 1: Opslaan Enkele Voorkeur
```
Input:  Vroeg = 1, rest leeg
Expect: JSON = {"1": "vroeg"}
Result: ✓ PASS
```

### Test 2: Opslaan Alle Voorkeuren
```
Input:  Vroeg=1, Laat=2, Nacht=3, Typetabel=4
Expect: JSON = {"1": "vroeg", "2": "laat", "3": "nacht", "4": "typetabel"}
Result: ✓ PASS
```

### Test 3: Validatie Dubbele Prioriteit
```
Input:  Vroeg=1, Laat=1
Expect: Error message + niet opgeslagen
Result: ✓ PASS
```

### Test 4: Reset Functionaliteit
```
Input:  Reset knop → Bevestig
Expect: Alle dropdowns → index 0
Result: ✓ PASS
```

### Test 5: Laden Bestaande Voorkeuren
```
Setup:  Database heeft {"1": "laat", "3": "vroeg"}
Expect: Laat=1, Vroeg=3, rest leeg
Result: ✓ PASS
```

### Test 6: Live Preview Update
```
Action: Change Vroeg van leeg naar 1
Expect: Preview updates onmiddellijk
Result: ✓ PASS
```

---

## 🎯 DESIGN DECISIONS

### Waarom JSON Storage?
✅ **Voordelen:**
- Flexibel: makkelijk uitbreidbaar met nieuwe shift types
- Simpel: geen extra tabel nodig
- Compact: alle voorkeuren in 1 veld
- Standard: JSON parsing in alle languages

❌ **Alternatieven overwogen:**
- Aparte tabel `shift_voorkeuren`: meer overhead, complexer
- Aparte kolommen per shift type: niet schaalbaar

### Waarom ComboBox ipv Drag-and-Drop?
✅ **Voordelen:**
- Duidelijker voor gebruikers
- Minder technisch complex
- Betere mobile/accessibility support
- Minder ruimte nodig

❌ **Alternatieven overwogen:**
- Drag-and-drop lijst: visueler maar complexer

### Waarom Optionele Voorkeuren?
✅ **Voordelen:**
- Gebruikersvriendelijk: geen verplichte invulling
- Flexibel: verschillende use cases
- Realistisch: niet iedereen heeft sterke voorkeuren

---

## 📚 DOCUMENTATIE LINKS

**Code:**
- `gui/screens/voorkeuren_screen.py` - Main implementation
- `migratie_shift_voorkeuren.py` - Database migration
- `main.py:123-131` - Handler implementation

**Database:**
- `database/connection.py:68` - Schema definition
- `data/planning.db` - Production database

**Documentatie:**
- `RELEASE_NOTES_v0.6.11.md` - Release notes
- `DEV_NOTES.md:42-123` - Sessie details
- `CLAUDE.md` - Version info

---

**Laatste Update:** 21 Oktober 2025
**Versie:** 0.6.11
**Status:** ✓ Compleet en Getest
