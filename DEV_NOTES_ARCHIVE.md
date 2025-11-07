# DEV NOTES ARCHIVE
Historische Development Logs (Sessies ouder dan 1 maand)

**Doel:** Bewaar ontwikkelingsgeschiedenis voor context en referentie
**Bereik:** Sessies van vóór 20 Oktober 2025 (v0.6.8 en ouder)

Voor recente sessies, zie: `DEV_NOTES.md`

---

## INHOUDSOPGAVE
- [Oktober 2025](#oktober-2025)
  - [Sessie 19 Oktober - Rode Lijnen Config & Term-based Systeem](#sessie-19-oktober-2025)
  - [Sessie 18 Oktober - Typetabel Beheer](#sessie-18-oktober-2025)
  - [Sessie 16 Oktober - Planning Editor & Verlof](#sessie-16-oktober-2025)
  - [Sessie 15 Oktober - Shift Codes Systeem](#sessie-15-oktober-2025)
  - [Sessie 14 Oktober - Grid Kalender Widgets](#sessie-14-oktober-2025)
  - [Sessie 13 Oktober - Feestdagen Verbetering](#sessie-13-oktober-2025)
  - [Sessie 12 Oktober - Gebruikersbeheer & Styling](#sessie-12-oktober-2025)
  - [Sessie 11 Oktober - Gebruikersbeheer Complete](#sessie-11-oktober-2025)
  - [Sessie 10 Oktober - Dashboard & Login](#sessie-10-oktober-2025)

---

## OKTOBER 2025

### Sessie 19 Oktober 2025 (DEEL 2) - Rode Lijnen Config & UX Verbeteringen (v0.6.8)
**Duur:** ~4 uur
**Focus:** Config beheer systeem en gebruiksvriendelijkheid

**Voltooid:**
- ✅ **Rode Lijnen Config Beheer**
  - Database migratie script (`migratie_rode_lijnen_config.py`)
  - `RodeLijnenBeheerScreen` met actieve config + historiek
  - `RodeLijnenConfigDialog` voor bewerken (QDateEdit + QSpinBox)
  - Versioned systeem (actief_vanaf, actief_tot, is_actief)
  - `data_ensure_service.py` gebruikt nu config ipv hardcoded waarden
  - Seed functie in `connection.py` toegevoegd

- ✅ **Window Management**
  - Auto-maximize na login (`main.py:147`)
  - Centreren bij logout met geometry calculation (`main.py:174`)
  - Betere gebruikservaring op full-screen

- ✅ **Handleiding Systeem**
  - Tab-based HandleidingDialog met 3 tabs
  - Eerste Gebruik / Voor Planners / Voor Teamleden
  - Globaal F1 shortcut in alle schermen
  - Dashboard heeft Handleiding knop
  - Kalender Test knop verwijderd

- ✅ **Filter State Preservation**
  - `_filter_initialized` flag pattern toegepast
  - Filter blijft behouden bij maand navigatie
  - Zowel PlannerGridKalender als TeamlidGridKalender
  - Betere UX bij navigeren

- ✅ **Layout Fixes**
  - Mijn Planning scherm HBoxLayout met stretch factors (3:1)
  - Codes sidebar toegevoegd (zoals Planning Editor)
  - Grid stretching probleem opgelost
  - Betere ruimte-indeling op full-screen

- ✅ **Keyboard Shortcuts**
  - F1: Globale handleiding (alle schermen)
  - F2: Shift codes helper in Planning Editor (was F1)
  - Conflict opgelost

- ✅ **Historiek Standaard Zichtbaar**
  - HR Regels beheer: historiek standaard aan
  - Rode Lijnen beheer: historiek standaard aan
  - Betere overzicht voor gebruikers

**Nieuwe Bestanden:**
- `migratie_rode_lijnen_config.py`
- `gui/screens/rode_lijnen_beheer_screen.py`
- `gui/dialogs/rode_lijnen_config_dialog.py`
- `gui/dialogs/handleiding_dialog.py`

**Aangepaste Bestanden:**
- `main.py` - Window management, F1 shortcut, rode lijnen handler
- `database/connection.py` - Seed rode_lijnen_config
- `services/data_ensure_service.py` - Config-based generatie
- `gui/screens/dashboard_screen.py` - Handleiding knop, Kalender Test verwijderd
- `gui/screens/hr_regels_beheer_screen.py` - Historiek standaard aan
- `gui/widgets/planner_grid_kalender.py` - Filter preservation
- `gui/widgets/teamlid_grid_kalender.py` - Filter preservation
- `gui/screens/mijn_planning_screen.py` - HBoxLayout + codes sidebar
- `gui/screens/planning_editor_screen.py` - F1 → F2

**Bug Fixes:**
- ✅ Colors.BORDER → Colors.BORDER_LIGHT
- ✅ F1 werkte niet in dashboard → Local shortcut verwijderd
- ✅ Filter reset bij maand navigatie → Flag pattern
- ✅ Grid stretching → HBoxLayout met stretch factors
- ✅ Shift codes helper conflict → F2 ipv F1

**Geleerde Lessen:**
- Stretch factors in layouts: 3:1 ratio voor main content vs sidebar
- `hasattr()` pattern voor initialization tracking
- Global vs local shortcuts hierarchie in PyQt6
- QShortcut op main window werkt voor alle child widgets
- Datum formatting: `strftime("%d-%m-%Y")` voor NL notatie

**Design Beslissingen:**
- Rode Lijnen config versioned net als HR regels (consistency)
- Handleiding tab-based ipv scrollable (betere organisatie)
- F1 globaal voor handleiding, F2 voor context-specifieke hulp
- Historiek standaard zichtbaar (transparantie)
- Auto-maximize na login (optimaal schermgebruik)

---

### Sessie 19 Oktober 2025 (DEEL 1) - Term-based Systeem voor Speciale Codes (v0.6.7)
**Duur:** ~3 uur
**Focus:** Bugfix - Verlofcode beschermen tegen verwijdering

**Probleem:**
- VV (verlof) kon verwijderd worden uit speciale codes
- Bij verlof goedkeuren werd hardcoded 'VV' gebruikt
- Als VV verwijderd was, crashte het systeem bij verlof goedkeuring

**Oplossing - Term-based Systeem:**
- ✅ **Database Wijzigingen**
  - `term` kolom toegevoegd aan `speciale_codes` (nullable, unique index)
  - 5 verplichte termen: verlof, zondagrust, zaterdagrust, ziek, arbeidsduurverkorting
  - Codes kunnen wijzigen (VV→VL) maar termen blijven bestaan

- ✅ **TermCodeService** (`services/term_code_service.py`)
  - Singleton met cache voor performance
  - `get_code_for_term('verlof')` → dynamische lookup
  - Fallback naar standaard codes (VV, RX, CX, Z, DA)
  - Auto-refresh na wijzigingen in ShiftCodesScreen

- ✅ **UI Wijzigingen**
  - `shift_codes_screen.py`: Verwijder-knop disabled voor systeemcodes + [SYSTEEM] indicator
  - `verlof_goedkeuring_screen.py`: Gebruikt TermCodeService ipv hardcoded 'VV'
  - `grid_kalender_base.py`: Dynamische kleuren op basis van termen
  - `speciale_code_dialog.py`: Waarschuwing banner voor systeemcodes

- ✅ **Database Migratie** (`migratie_systeem_termen.py`)
  - Voegt term kolom toe (zonder UNIQUE constraint - SQLite beperking)
  - Markeert VV, RX, CX, Z, DA als systeemcodes
  - UNIQUE index via partial index (WHERE term IS NOT NULL)

- ✅ **Clean Install Support**
  - `connection.py` seed functie aangepast met term kolom
  - Beide migratiepaden getest (upgrade + clean install)

**Geleerde Lessen:**
- `sqlite3.Row` heeft geen `.get()` method - gebruik directe key access
- SQLite accepteert geen UNIQUE constraint via ALTER TABLE ADD COLUMN
- Partial unique index als workaround: `CREATE UNIQUE INDEX ... WHERE term IS NOT NULL`
- Cache refresh cruciaal na wijzigingen voor consistency

**Kleine Issues (geen prioriteit):**
- [SYSTEEM] indicator staat bij code ipv naam (schoonheidsfoutje)
- Oude planning records behouden oude codes (historisch correct)

---

### Sessie 18 Oktober 2025 - Typetabel Beheer Systeem (v0.6.6)
**Duur:** ~5 uur
**Focus:** Complete implementatie versioned typetabel systeem

**Voltooid:**
- ✅ **Database Migratie Script** (`migrate_typetabel_versioned.py`)
  - Converteert oude `typetabel` naar `typetabel_versies` + `typetabel_data`
  - Behoudt oude data als backup (`typetabel_old_backup`)
  - Safe & idempotent (kan meerdere keren runnen)
- ✅ **TypetabelBeheerScreen** (hoofdscherm)
  - Overzicht actieve/concept/archief versies
  - Status badges en color-coded cards
  - Gebruikers telling voor actieve versie
  - Nieuwe typetabel concept maken
  - Kopiëren functionaliteit
  - Verwijderen concept
- ✅ **NieuweTypetabelDialog**
  - Naam + aantal weken (1-52)
  - Dynamische info over herhalend patroon
  - Optionele opmerking
- ✅ **TypetabelEditorDialog**
  - Grid editor (Weken × 7 dagen)
  - Dropdowns met veelgebruikte codes
  - Editable vs read-only mode
  - Auto-save tracking
  - Opmerking bewerken
- ✅ **Database Schema Update in connection.py**
  - `seed_typetabel()` aangepast voor versioned systeem
  - `create_tables()` met nieuwe typetabel_versies structuur
- ✅ **Dashboard & Main.py Integratie**
  - Typetabel knop in Instellingen tab
  - Signal + handler geïmplementeerd
- ✅ **Documentatie Update**
  - DEV_NOTES.md bijgewerkt
  - DEVELOPMENT_GUIDE.md gefocust (~800 lijnen)
  - PROJECT_INFO.md gefocust (~600 lijnen)

**Design Beslissingen:**
- **Flexibele shift codes:** Post nummer ZIT in code (V1, V2, L1, etc.)
- **Status lifecycle:** Concept → Actief → Archief
- **Geen gebruiker koppeling:** Iedereen gebruikt DE actieve typetabel
- **Herhalend patroon:** Automatisch herhalen bij meer personen dan weken
- **Multi-post support:** Teams met meerdere posten gebruiken codes zoals V1, V2, L1, L2

**Nieuwe Bestanden:**
- `migrate_typetabel_versioned.py` (root)
- `gui/screens/typetabel_beheer_screen.py`
- `gui/dialogs/typetabel_dialogs.py`
- `gui/dialogs/typetabel_editor_dialog.py`

**Database Changes:**
- Nieuwe tabellen: `typetabel_versies`, `typetabel_data`
- Oude tabel: blijft als `typetabel_old_backup` na migratie
- Seed functie volledig herschreven

**Openstaande Items:**
- Activeren flow met validatie
- Bulk operaties in editor
- Wijzig aantal weken functionaliteit
- GebruikersBeheer integratie
- Auto-generatie uit typetabel

---

### Sessie 16 Oktober 2025 - Planning Editor & Verlof Beheer (v0.6.5)
**Duur:** ~3 uur
**Focus:** Implementatie kernschermen

**Voltooid:**
- ✅ PlanningEditorScreen (hoofdscherm) aangemaakt
- ✅ PlannerGridKalender uitgebreid met EditableLabel
- ✅ Cel editing, keyboard navigatie, save/delete logica
- ✅ Context menu voor snelle acties
- ✅ VerlofAanvragenScreen (teamleden)
- ✅ VerlofGoedkeuringScreen (planners)
- ✅ Database initialisatie geüpdatet naar v0.6.4+ schema

**Nieuwe Bestanden:**
- `gui/screens/planning_editor_screen.py`
- `gui/screens/verlof_aanvragen_screen.py`
- `gui/screens/verlof_goedkeuring_screen.py`

**Openstaande Items:**
- Validatie integratie (rood/geel/groen feedback)
- Auto-generatie uit typetabel
- Concept vs Gepubliceerd status toggle
- Bulk operations

---

### Sessie 15 Oktober 2025 - Shift Codes Systeem (v0.6.4)
**Duur:** ~3 uur
**Focus:** Complete shift codes implementatie

**Voltooid:**
- ✅ Database migratie (werkposten, shift_codes, speciale_codes)
- ✅ SpecialeCodeDialog - CRUD voor globale codes
- ✅ WerkpostNaamDialog - Naam/beschrijving input
- ✅ ShiftCodesGridDialog - 3x4 grid editor
- ✅ ShiftCodesScreen - Hoofdscherm
- ✅ Tijd parsing met flexibele formaten
- ✅ Multi-team support via werkposten
- ✅ Halve uren en kwartieren support
- ✅ Soft delete voor werkposten

**Bug Fixes:**
- ✅ Grid header te breed → Simpeler "Tijd" label
- ✅ Tijd parsing error → Variabele scope fix
- ✅ Button width "Deactiveren" → Uniform 96px
- ✅ Admin in kalenders → Filter toegevoegd
- ✅ Planning tabel missing → Basis tabel aangemaakt

**Technische Details:**
- DELETE + INSERT pattern bij grid opslaan
- Flexibele tijd parser accepteert meerdere formaten
- Grid 3x4: dag_type × shift_type
- Eigenschappen op werkpost niveau

**Nieuwe Bestanden:**
- `gui/dialogs/speciale_code_dialog.py`
- `gui/dialogs/werkpost_naam_dialog.py`
- `gui/dialogs/shift_codes_grid_dialog.py`
- `gui/screens/shift_codes_screen.py`
- `migrate_shift_codes.py`

---

### Sessie 14 Oktober 2025 - Grid Kalender Widgets (v0.6.3)
**Duur:** ~2 uur
**Focus:** Herbruikbare kalender componenten

**Voltooid:**
- ✅ GridKalenderBase - Base class voor kalenders
- ✅ PlannerGridKalender - Planner specifieke view
- ✅ TeamlidGridKalender - Teamlid view met filter
- ✅ FilterDialog voor gebruiker selectie
- ✅ Verlof/DA/VD overlays (gekleurde achtergronden)
- ✅ Feestdagen markering (gele achtergrond)
- ✅ KalenderTestScreen voor development

**Technische Details:**
- Inheritance pattern: Base → Specifieke implementaties
- Signal/Slot voor filter callbacks
- QTableWidget met custom cell widgets
- Lazy loading van planning data

**Nieuwe Bestanden:**
- `gui/widgets/grid_kalender_base.py`
- `gui/widgets/planner_grid_kalender.py`
- `gui/widgets/teamlid_grid_kalender.py`
- `gui/screens/kalender_test_screen.py`

---

### Sessie 13 Oktober 2025 - Feestdagen Verbetering (v0.6.3)
**Duur:** ~2 uur
**Focus:** Feestdagen systeem herwerken

**Voltooid:**
- ✅ is_variabel flag: 0=vast, 1=variabel/extra
- ✅ Paasberekening algoritme (Computus)
- ✅ Beveiliging vaste feestdagen (niet bewerkbaar)
- ✅ Database migratie systeem
- ✅ Variabele feestdagen correctie mogelijk
- ✅ Extra feestdagen toevoegen

**Technische Details:**
- Paasberekening: Gauss algoritme
- Migratie check: PRAGMA table_info
- UI: Disabled state voor vaste feestdagen
- Validatie: Blokkeer wijzigingen vaste feestdagen

---

### Sessie 12 Oktober 2025 - Gebruikersbeheer & Styling (v0.6.2)
**Duur:** ~2 uur
**Focus:** Centrale styling + gebruikersbeheer stabiliteit

**Voltooid:**
- ✅ Centrale styling systeem (`gui/styles.py`)
- ✅ Colors, Fonts, Dimensions classes
- ✅ Styles class met pre-built methods
- ✅ TableConfig helper
- ✅ Gebruikersbeheer crashproof
- ✅ Table layouts stabiliteit

**Bug Fixes:**
- ✅ Unicode karakters → Plain tekst in buttons
- ✅ Table layout crashes → TableConfig helper
- ✅ Button tekst overlap → Vaste widths

---

### Sessie 11 Oktober 2025 - Gebruikersbeheer Complete (v0.6.1)
**Duur:** ~3 uur
**Focus:** Volledige gebruikersbeheer implementatie

**Voltooid:**
- ✅ UUID systeem voor permanente gebruikers-ID's
- ✅ Timestamp tracking (aangemaakt, gedeactiveerd, laatste login)
- ✅ Reserve functionaliteit
- ✅ Startweek typedienst instellen
- ✅ Wachtwoord reset
- ✅ Zoeken op naam/gebruikersnaam
- ✅ Soft delete (deactiveren ipv verwijderen)

**Database Changes:**
- ✅ gebruiker_uuid kolom toegevoegd
- ✅ Timestamps toegevoegd
- ✅ is_reserve flag toegevoegd

---

### Sessie 10 Oktober 2025 - Dashboard & Login (v0.6.0)
**Duur:** ~4 uur
**Focus:** Login systeem en dashboard

**Voltooid:**
- ✅ Login systeem met bcrypt
- ✅ Rol-gebaseerde toegang (planner/teamlid)
- ✅ Dashboard met tabs
- ✅ Menu systeem
- ✅ About dialog
- ✅ Wachtwoord wijzigen functionaliteit
- ✅ Auto-generatie feestdagen
- ✅ Auto-generatie rode lijnen

**Database Redesign:**
- ✅ Volledige schema herwerking
- ✅ Foreign keys enabled
- ✅ Row factory voor dict access
- ✅ Seed data functions

---

## DATABASE SCHEMA EVOLUTIE

### v0.6.8 - Rode Lijnen Config (19 Oktober 2025)
**Nieuwe tabel:**
- `rode_lijnen_config` (start_datum, interval_dagen, actief_vanaf, actief_tot, is_actief)

**Seed functie:**
- `seed_rode_lijnen_config()` toegevoegd

### v0.6.7 - Term-based Systeem (19 Oktober 2025)
**Wijzigingen:**
- `speciale_codes`: Kolom `term` toegevoegd (TEXT, nullable)
- UNIQUE index op term (WHERE term IS NOT NULL)
- 5 verplichte termen gedefinieerd

### v0.6.6 - Typetabel Versioned Systeem (18 Oktober 2025)
**Nieuwe tabellen:**
- `typetabel_versies` (id, versie_naam, aantal_weken, status, actief_vanaf, actief_tot, ...)
- `typetabel_data` (id, versie_id, week_nummer, dag_nummer, shift_type)

**Verwijderd:**
- `typetabel` (oude structuur, wordt `typetabel_old_backup` na migratie)

**Seed functie:**
- `seed_typetabel()` volledig herschreven

### v0.6.4 - Shift Codes Systeem (15 Oktober 2025)
**Nieuwe tabellen:**
- `werkposten`
- `shift_codes`
- `speciale_codes`
- `planning` (basis)

### v0.6.3 - Feestdagen Herwerking (13 Oktober 2025)
**Wijzigingen:**
- `feestdagen`: Toegevoegd `is_variabel` flag

### v0.6.1 - Gebruikers UUID (11 Oktober 2025)
**Wijzigingen:**
- `gebruikers`: Toegevoegd `gebruiker_uuid`, timestamps

### v0.6.0 - Database Redesign (10 Oktober 2025)
**Nieuwe structuur:**
- Foreign keys enabled
- Row factory voor dict access
- Timestamps overal
- Soft delete pattern

---

## OPGELOSTE BUGS (Archief)

**Filter State Reset** (v0.6.8)
- **Fix:** `_filter_initialized` flag pattern
- **Impact:** Filter blijft behouden bij maand navigatie
- **Locaties:** `planner_grid_kalender.py:107`, `teamlid_grid_kalender.py:114`

**Grid Stretching Full-screen** (v0.6.8)
- **Fix:** HBoxLayout met stretch factors (3:1) + codes sidebar
- **Locatie:** `mijn_planning_screen.py:47`

**F1 Shortcut Conflict** (v0.6.8)
- **Fix:** Shift codes helper verplaatst naar F2
- **Locatie:** `planning_editor_screen.py:300`

**F1 Werkte Niet in Dashboard** (v0.6.8)
- **Fix:** Local F1 shortcut verwijderd uit dashboard
- **Locatie:** `dashboard_screen.py`

**Verlofcode Verwijderbaar** (v0.6.7)
- **Fix:** Term-based systeem met beschermde codes
- **Impact:** Systeemcodes kunnen niet meer verwijderd worden
- **Locaties:** `shift_codes_screen.py`, `verlof_goedkeuring_screen.py`, `term_code_service.py`

**Typetabel Seed Conflict** (v0.6.6)
- **Fix:** `connection.py` seed_typetabel() aangepast voor versioned systeem
- **Impact:** Schone database start werkt correct

**Admin Account in Kalenders** (v0.6.4)
- **Fix:** `WHERE gebruikersnaam != 'admin'` in load_gebruikers()
- **Locatie:** `gui/widgets/grid_kalender_base.py`

**Shift Codes Opslaan Error** (v0.6.4)
- **Fix:** Variabele scope correctie in tijd parsing
- **Locatie:** `gui/dialogs/shift_codes_grid_dialog.py`

**Button Width "Deactiveren"** (v0.6.4)
- **Fix:** Uniform 96px voor BEIDE Activeren/Deactiveren
- **Locaties:** `gebruikersbeheer_screen.py`, `shift_codes_screen.py`

**Grid Header Te Breed** (v0.6.4)
- **Fix:** Simpeler "Tijd" label zonder HH:MM-HH:MM
- **Locatie:** `gui/dialogs/shift_codes_grid_dialog.py`

**Feestdagen Bewerken Onbeschermd** (v0.6.3)
- **Fix:** is_variabel flag + UI disable voor vaste feestdagen
- **Locatie:** `gui/screens/feestdagen_screen.py`

**Database Schema Changes Breaking** (v0.6.3)
- **Fix:** Migratie scripts met checks
- **Pattern:** Check bestaande schema → Voer migratie uit indien nodig

---

*Dit archief wordt niet meer actief bijgewerkt*
*Voor recente sessies, zie DEV_NOTES.md*
*Laatst gearchiveerd: 19 Oktober 2025*
