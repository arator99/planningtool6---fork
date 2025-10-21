# Release Notes v0.6.12

**Release Datum:** 21 Oktober 2025
**Status:** Beta - Theme Per Gebruiker Systeem

---

## 🎯 HOOFDFEATURE: THEME VOORKEUR PER GEBRUIKER

In v0.6.9 introduceerden we dark mode met een globaal JSON bestand. Dit zorgde ervoor dat alle gebruikers op dezelfde computer dezelfde theme deelden. In v0.6.12 hebben we dit verbeterd naar een **per gebruiker systeem**.

### Wat is Nieuw?

**✅ Persoonlijke Theme Voorkeur**
- Elke gebruiker kiest eigen light of dark mode
- Opgeslagen in database (kolom `gebruikers.theme_voorkeur`)
- Theme blijft behouden tussen sessies
- Onafhankelijk van andere gebruikers

**✅ Login Scherm Blijft Light**
- Login scherm toont altijd light mode
- Na inloggen wordt gebruiker's theme geladen
- Geen verwarring over welke theme actief is

**✅ Automatische Migratie**
- Oude globale theme voorkeur wordt gemigreerd naar alle gebruikers
- Oude `data/theme_preference.json` wordt verwijderd
- Database migratie: `migratie_theme_per_gebruiker.py`

---

## 🔧 TECHNISCHE DETAILS

### Database Wijzigingen

**Nieuwe Kolom: `gebruikers.theme_voorkeur`**
```sql
ALTER TABLE gebruikers
ADD COLUMN theme_voorkeur TEXT DEFAULT 'light';
```

**Mogelijke Waarden:**
- `'light'` - Light mode (standaard)
- `'dark'` - Dark mode

### Code Aanpassingen

**Main.py - Theme Loading/Saving:**
```python
def load_theme_preference(self) -> None:
    """Laad theme voorkeur van ingelogde gebruiker uit database"""
    if not self.current_user:
        ThemeManager.set_theme('light')  # Login scherm
        return

    # Laad uit database voor ingelogde gebruiker
    cursor.execute("""
        SELECT theme_voorkeur FROM gebruikers WHERE id = ?
    """, (self.current_user['id'],))

def save_theme_preference(self, theme: str) -> None:
    """Sla theme op in database voor ingelogde gebruiker"""
    cursor.execute("""
        UPDATE gebruikers SET theme_voorkeur = ? WHERE id = ?
    """, (theme, self.current_user['id']))
```

**Main.py - Logout Fix:**
```python
def on_logout(self) -> None:
    """Uitloggen"""
    self.current_user = None

    # Reset naar light mode voor login scherm
    ThemeManager.set_theme('light')
    self.apply_theme()
    # ... rest van logout
```

**Connection.py - Schema Update:**
```sql
CREATE TABLE gebruikers (
    -- ... andere kolommen
    shift_voorkeuren TEXT,              -- v0.6.11
    theme_voorkeur TEXT DEFAULT 'light', -- v0.6.12
    -- ... andere kolommen
)
```

---

## 🐛 BUG FIX

### Login Scherm Dark Mode Na Logout

**Probleem:**
Wanneer een gebruiker met dark mode uitlogde, bleef het login scherm in dark mode staan.

**Oorzaak:**
`on_logout()` resettte de theme niet terug naar light mode.

**Oplossing:**
```python
# In on_logout()
ThemeManager.set_theme('light')
self.apply_theme()
```

**Impact:**
Login scherm toont nu altijd light mode, ongeacht de vorige gebruiker's theme.

---

## 📊 USER EXPERIENCE

### Scenario 1: Jan gebruikt Dark Mode
```
1. Jan logt in
2. Theme wordt geladen uit database: 'dark'
3. Dashboard toont dark mode
4. Jan werkt in dark mode
5. Jan logt uit
6. Login scherm wordt light
7. Theme 'dark' blijft opgeslagen voor Jan
```

### Scenario 2: Piet gebruikt Light Mode
```
1. Piet logt in (na Jan)
2. Theme wordt geladen uit database: 'light'
3. Dashboard toont light mode
4. Piet werkt in light mode
5. Onafhankelijk van Jan's voorkeur!
```

### Scenario 3: Theme Switchen
```
1. Marie logt in met light mode
2. Marie switcht naar dark mode via toggle
3. Theme wordt opgeslagen in database
4. Marie logt uit en later weer in
5. Dark mode wordt automatisch geladen
```

---

## 🔄 UPGRADE INSTRUCTIES

### Voor Bestaande Databases (v0.6.11 → v0.6.12)

```bash
python migratie_theme_per_gebruiker.py
```

**Wat doet dit:**
1. Voegt `theme_voorkeur` kolom toe aan gebruikers tabel
2. Probeert oude globale theme te lezen uit `data/theme_preference.json`
3. Update alle gebruikers met de globale theme (of 'light' als default)
4. Informeert dat oude JSON bestand verwijderd kan worden

**Output Voorbeeld:**
```
============================================================
PLANNING TOOL - Database Migratie
Theme Voorkeur Per Gebruiker (v0.6.11 -> v0.6.12)
============================================================

Start migratie: theme_voorkeur kolom toevoegen...
Gevonden globale theme voorkeur: dark
Migratie succesvol! Theme voorkeur kolom toegevoegd.
3 gebruikers geupdate met theme 'dark'

LET OP: Het oude theme_preference.json bestand kan verwijderd worden.
Theme voorkeuren worden nu per gebruiker opgeslagen in de database.

============================================================
Migratie proces voltooid!
============================================================
```

### Voor Schone Database

Geen migratie nodig - kolom wordt automatisch aangemaakt met default 'light'.

---

## 📝 CODE CLEANUP

### Verwijderd

**Globaal Theme File Systeem:**
- ❌ `THEME_PREF_FILE = "data/theme_preference.json"` constant verwijderd
- ❌ JSON file lezen/schrijven code verwijderd
- ❌ Oude `data/theme_preference.json` bestand verwijderd

**Imports:**
- ❌ `import json` niet meer nodig in main.py (voor theme)
- ❌ `import os` niet meer nodig in main.py (voor theme)

### Toegevoegd

**Database Queries:**
- ✅ Theme loading uit database
- ✅ Theme saving naar database
- ✅ Per gebruiker theme management

---

## 🧪 TESTING

**Getest:**
- ✅ Theme opslaan per gebruiker in database
- ✅ Theme laden bij login
- ✅ Theme resetten bij logout naar light
- ✅ Login scherm altijd light mode
- ✅ Meerdere gebruikers met verschillende themes
- ✅ Theme switchen tijdens sessie
- ✅ Theme persistentie tussen sessies
- ✅ Database migratie van oude globale theme
- ✅ Schone database installatie

**Browser Support:**
N/A (Desktop applicatie)

---

## 📚 DOCUMENTATIE UPDATES

- ✅ `CLAUDE.md` - Versie 0.6.12, migratie lijst
- ✅ `DEV_NOTES.md` - Sessie 21 Oktober 2025 (Deel 2)
- ✅ `PROJECT_INFO.md` - Versie 0.6.12 sectie
- ✅ `DEVELOPMENT_GUIDE.md` - Database schema update
- ✅ `HANDLEIDING.md` - Dark mode per gebruiker vermeld

---

## 🎨 VOOR/NA VERGELIJKING

### VOOR (v0.6.11 en eerder)
```
Theme Opslag:     data/theme_preference.json (globaal)
Scope:            Hele applicatie / alle gebruikers
Login Scherm:     Volgt laatste gebruiker's theme
Probleem:         Jan's dark mode = Piet ziet ook dark
```

### NA (v0.6.12)
```
Theme Opslag:     database.gebruikers.theme_voorkeur (per user)
Scope:            Per gebruiker
Login Scherm:     Altijd light mode
Voordeel:         Jan's dark mode ≠ Piet's light mode
```

---

## 🔮 TOEKOMSTIGE VERBETERINGEN

**Mogelijke uitbreidingen:**
- Automatische theme switching (dag/nacht)
- Meer theme opties (bijv. high contrast)
- Theme preview voor aanpassen
- Sync met OS theme (Windows dark mode)

**Niet gepland:**
- Theme aanpassing per scherm (consistentie belangrijker)
- Custom kleuren per gebruiker (te complex)

---

## ⚠️ BEKENDE BEPERKINGEN

### QCalendarWidget Blijft Light
Het Qt QCalendarWidget component ondersteunt geen volledige dark mode styling. Dit is een Qt framework limitatie.

**Impact:**
- Kalender widgets in verlof aanvragen scherm blijven light
- Functioneel geen probleem
- Visueel kleine inconsistentie in dark mode

**Workaround:**
Geen - accepteren als Qt limitatie.

---

## 🚀 PERFORMANCE

**Impact op Performance:**
- ✅ Minimaal - één extra database query bij login
- ✅ Theme saving is async (geen UI blocking)
- ✅ Geen waarneembare vertraging

**Database Impact:**
- Nieuwe kolom: TEXT (max ~10 bytes per gebruiker)
- Verwaarloosbaar voor honderden gebruikers

---

## 🔗 GERELATEERDE RELEASES

**v0.6.11** - Shift Voorkeuren Systeem
**v0.6.10** - Verlof & KD Saldo Tracking
**v0.6.9** - Dark Mode (Globaal) - verbeterd in v0.6.12

---

## 📞 SUPPORT

**Bugs of problemen:**
- Neem contact op met je planner
- Vermeld versienummer (0.6.12)
- Beschrijf het probleem en stappen om te reproduceren

**Technische vragen:**
- Zie `DEVELOPMENT_GUIDE.md` voor architectuur details
- Zie `DEV_NOTES.md` voor ontwikkel geschiedenis

---

**Vorige versie:** v0.6.11 (Shift Voorkeuren Systeem)
**Volgende versie:** v0.6.13 (TBD)

*Laatste update: 21 Oktober 2025*
*Auteur: Claude Code Sessie 21 Oktober 2025*
