# DEV NOTES
Active Development Notes & Session Logs

## CURRENT VERSION: 0.6.14

**Last Updated:** 22 Oktober 2025
**Status:** Beta - Actieve Ontwikkeling (Werkpost Koppeling & Slimme Auto-Generatie Compleet)

---

## 🎯 FOCUS VOOR VOLGENDE SESSIE

### Prioriteit 1: Planning Editor Afmaken
- ✅ Auto-generatie uit typetabel (GEDAAN v0.6.14)
- Concept vs Gepubliceerd toggle
- Bulk operaties (copy week, paste, clear)
- Validatie feedback integratie

### Prioriteit 2: Typetabel Activatie Flow
- Activeren dialog met datum picker
- Validatie (alle weken ingevuld?)
- Status transitie (concept → actief, oud actief → archief)
- Gebruikers controle (startweek binnen bereik?)
- Bulk operaties (kopieer week, vul reeks)

### Prioriteit 2: GebruikersBeheer Integratie
- Dynamische max startweek uit actieve typetabel
- Validatie bij startweek instellen
- Warning bij gebruikers buiten bereik

### Prioriteit 3: Validatie Systeem (HR Regels)
- PlanningValidator class implementeren
- 12u rust check tussen shifts
- 50u/week maximum check
- 19 dagen per 28-dagen cyclus check
- Visuele feedback (rood/geel/groen in grid)

---

## 📝 RECENTE SESSIES

### Sessie 22 Oktober 2025 (Deel 2) - Feestdag Behandeling in Auto-Generatie Fix
**Duur:** ~30 min
**Focus:** Bug fix - Feestdagen krijgen verkeerde shift codes bij auto-generatie

**Probleem:**
- Bij auto-generatie uit typetabel kregen feestdagen normale weekdag codes
- Voorbeeld: Typetabel zegt "V" (vroeg) op feestdag → kreeg 7101 (weekdag vroeg)
- MOET ZIJN: Feestdagen = zondag codes → 7701 (zondag vroeg)

**Oplossing:**
- ✅ Auto-generatie dialog: feestdagen laden uit database
- ✅ `bereken_shift_slim()`: check of datum feestdag is
- ✅ Als feestdag: `dag_type = 'zondag'` ipv weekdag/zaterdag
- ✅ Lookup shift_codes met zondag: (werkpost, 'zondag', 'vroeg') → 7701
- ✅ Info box en preview updaten met feestdag info
- ✅ Documentatie: PlanningValidator TODO updated (toekomstig)

**Code Wijzigingen:**
- `gui/dialogs/auto_generatie_dialog.py`:
  - Nieuwe instance attribute: `self.feestdagen: Dict[str, bool]` (regel 41)
  - Load feestdagen in `load_data()` (regel 169-175)
  - `bereken_shift_slim()`: feestdag check (regel 497-510)
  - Info box en preview tekst updated (regel 58, 232-234)

- `gui/widgets/planner_grid_kalender.py`:
  - Instance attribute: `self.feestdag_namen: Dict[str, str]` (regel 179)
  - `load_feestdagen_extended()`: laadt nu ook namen (regel 336-349)
  - `get_feestdag_naam()`: helper methode (regel 645-647)
  - `on_cel_edited()`: specifieke foutmelding voor feestdagen (regel 587-605)

**Business Logic:**
```python
# Auto-generatie:
if is_feestdag:
    dag_type = 'zondag'  # Altijd zondag codes voor feestdagen
# Resultaat: V → 7701, L → 7801, N → 7901 op feestdagen

# Handmatige invoer foutmelding:
if is_feestdag:
    "Deze datum is een feestdag (Kerstmis). Op feestdagen moeten zondagdiensten worden gebruikt."
else:
    "Deze datum is een zondag/zaterdag/weekdag. Gebruik een shift code voor zondag/zaterdag/weekdag."
```

**Toekomstig (PlanningValidator):**
- Wanneer validator wordt gemaakt: ook feestdagen als zondag behandelen
- Documentatie toegevoegd aan DEV_NOTES.md TODO sectie

**Testing:**
- ⏳ Nog testen: genereer planning met feestdagen en verifieer codes

---

### Sessie 22 Oktober 2025 - Werkpost Koppeling & Slimme Auto-Generatie (v0.6.14)
**Duur:** ~3 uur
**Focus:** Many-to-many werkpost koppeling met intelligente auto-generatie uit typetabel

**Voltooid:**
- ✅ **Database Migratie**
  - Nieuwe tabel `gebruiker_werkposten` (many-to-many met prioriteit)
  - Index `idx_gebruiker_werkposten_gebruiker` voor performance
  - Migratie script `migratie_gebruiker_werkposten.py`
  - Auto-seed: koppel alle gebruikers aan eerste actieve werkpost

- ✅ **Werkpost Koppeling UI**
  - Nieuw scherm `werkpost_koppeling_screen.py`
  - Grid layout: gebruikers (Y-as) × werkposten (X-as)
  - Checkboxes voor koppelingen + prioriteit spinboxes
  - Filters: naam zoeken + toon reserves
  - Reserves visueel onderscheiden ([RESERVE] label + grijze achtergrond)
  - Menu item toegevoegd aan Beheer tab (was eerst in Instellingen)

- ✅ **Slimme Auto-Generatie**
  - Nieuwe dialog `auto_generatie_dialog.py`
  - Algoritme: typetabel "V" → dag_type + werkpost → shift_code "7101"
  - Multi-post support met prioriteit fallback
  - Bescherming: speciale codes en handmatige wijzigingen blijven behouden
  - Preview functionaliteit met statistieken
  - Datum range selectie met QDateEdit
  - Bevestiging dialog met overzicht

- ✅ **Planning Editor Integratie**
  - "Auto-Genereren uit Typetabel" knop geactiveerd
  - Link naar auto_generatie_dialog
  - Refresh kalender na generatie

- ✅ **Bug Fixes**
  - Nieuwe werkpost: `reset_12u` standaard UIT (0 ipv 1)
  - Speciale codes query: geen `is_actief` kolom (runtime error fix)
  - Kalender attribute fix: `jaar` en `maand` ipv `current_year/month`

- ✅ **Documentatie Updates**
  - `config.py`: APP_VERSION = "0.6.14", MIN_DB_VERSION = "0.6.14"
  - `CLAUDE.md`: Key tables, features, running instructions
  - `DEVELOPMENT_GUIDE.md`: Database schema, nieuwe features sectie
  - `DEV_NOTES.md`: Sessie log
  - `PROJECT_INFO.md`: (TODO)

**Technische Details:**
- **Auto-Generatie Logica:**
  1. Laad typetabel data in memory: `{(week, dag): shift_type}`
  2. Laad gebruiker werkposten: `{gebruiker_id: [(werkpost_id, prioriteit), ...]}`
  3. Laad shift_codes mapping: `{(werkpost_id, dag_type, shift_type): code}`
  4. Per gebruiker per datum: bereken shift_type uit typetabel
  5. Bepaal dag_type uit datum (weekdag/zaterdag/zondag)
  6. Loop door gebruiker's werkposten (op prioriteit) totdat match
  7. Insert shift_code in planning (bescherm speciale codes!)

- **Prioriteit Fallback:**
  - Jan kent PAT (prio 1) en Interventie (prio 2)
  - Typetabel zegt "N" op maandag
  - PAT heeft geen nacht op weekdag → skip
  - Interventie heeft wel nacht → gebruik "7201"

**Openstaande Issues:**
- Geen

**Geleerde Lessen:**
- ✅ Many-to-many relaties met prioriteit zijn krachtig voor multi-post scenarios
- ✅ In-memory data caching voor performance bij grote datasets
- ✅ Filters (naam + checkbox) maken UI's veel gebruiksvriendelijker
- ✅ Preview dialogen geven gebruiker controle en vertrouwen

**Volgende Stappen:**
- Concept vs Gepubliceerd toggle in Planning Editor
- Bulk operaties (copy week, paste, clear)
- Validatie feedback integratie

---

### Sessie 21 Oktober 2025 (Deel 3) - Database Versie Beheer Systeem (v0.6.13)
**Duur:** ~1 uur
**Focus:** Centraal versie beheer systeem voor app en database compatibiliteit

**Voltooid:**
- ✅ **Config.py Versie Management**
  - `APP_VERSION = "0.6.13"` - verhoogt bij elke wijziging
  - `MIN_DB_VERSION = "0.6.12"` - verhoogt alleen bij DB schema wijzigingen
  - Gescheiden versie nummers voor app en database
  - Centrale versie bron voor hele applicatie

- ✅ **Database Metadata Tabel (v0.6.13)**
  - Nieuwe tabel: `db_metadata` (version_number, updated_at, migration_description)
  - Seed functie: `seed_db_version()` initialiseert versie
  - Helper functies: `get_db_version()`, `check_db_compatibility()`
  - Automatische versie tracking voor alle nieuwe databases

- ✅ **Versie Check bij App Start**
  - `check_db_compatibility()` in main.py
  - 3 scenario's gehandeld:
    1. Geen versie info → oude database → error dialog
    2. DB te oud (< MIN_DB_VERSION) → error dialog
    3. DB nieuwer dan app → error dialog
  - Bij incompatibiliteit: duidelijke foutmelding met contactinformatie
  - Geen automatische migratie - handmatige upgrade vereist

- ✅ **UI Versie Weergave**
  - LoginScreen: App versie + DB versie onderaan (kleine grijze tekst)
  - AboutDialog: App versie + DB versie in header
  - Centrale import uit config.py (geen hardcoded versies meer)
  - Dynamic versie display via `get_db_version()`

- ✅ **Upgrade Script**
  - `upgrade_to_v0_6_13.py` voor bestaande databases
  - Voegt db_metadata tabel toe (SCHEMA WIJZIGING!)
  - Initialiseert versie op 0.6.13 (huidige versie)
  - Idempotent: kan meerdere keren gedraaid worden
  - Windows console compatible (geen Unicode emoji's)

- ✅ **Connection.py Updates**
  - db_metadata tabel toegevoegd aan create_tables()
  - seed_db_version() toegevoegd aan seed_data()
  - get_db_version() - haalt huidige DB versie op
  - check_db_compatibility() - controleert compatibiliteit

**Technische Beslissingen:**
- **Geen automatische migratie**: Bij incompatibiliteit toont app error en sluit af
- **Handmatige upgrade**: Beheerder draait upgrade script, dan start app
- **Gescheiden versies**: APP_VERSION voor alle changes, MIN_DB_VERSION alleen voor DB schema
- **Centrale versie bron**: config.py is single source of truth
- **User-friendly errors**: Duidelijke foutmeldingen met instructies

**User Experience:**
- Tester met oude database → error dialog met uitleg
- Beheerder draait `upgrade_to_v0_6_13.py`
- Database krijgt versie tracking
- App start normaal, versies zichtbaar op loginscherm
- About dialog toont beide versies

**Versie Systeem Voorbeelden:**
```
Scenario 1 - GUI wijziging:
  v0.6.13 → v0.6.14
  APP_VERSION = "0.6.14"
  MIN_DB_VERSION = "0.6.13" (blijft gelijk - geen schema wijziging)

Scenario 2 - DB schema wijziging:
  v0.6.14 → v0.6.15
  APP_VERSION = "0.6.15"
  MIN_DB_VERSION = "0.6.15" (gaat omhoog - wel schema wijziging)
  Database krijgt: INSERT INTO db_metadata VALUES ("0.6.15", ...)
```

**Belangrijk:**
- v0.6.13 is een DB schema wijziging (db_metadata tabel toegevoegd)
- Daarom: APP_VERSION = MIN_DB_VERSION = "0.6.13"

**Testing:**
- ✅ Upgrade script werkt op bestaande v0.6.12 database
- ✅ App start zonder errors na upgrade
- ✅ Versies correct weergegeven op loginscherm
- ✅ About dialog toont beide versies
- ✅ Nieuwe database krijgt automatisch versie tracking

**Nieuwe Bestanden:**
- `upgrade_to_v0_6_13.py` - Upgrade script voor bestaande databases

**Aangepaste Bestanden:**
- `config.py` - APP_VERSION en MIN_DB_VERSION toegevoegd
- `database/connection.py` - db_metadata tabel, versie functies
- `main.py` - Versie check bij startup
- `gui/screens/login_screen.py` - Versie weergave onderaan
- `gui/dialogs/about_dialog.py` - Versie weergave in header
- `gui/screens/verlof_saldo_beheer_screen.py` - UI layout fix (terug knop + jaar selector)
- `CLAUDE.md` - Versie 0.6.13, version management sectie
- `DEV_NOTES.md` - Deze sessie

**UI/UX Improvements:**
- ✅ **VerlofSaldoBeheerScreen Layout Consistency**
  - Terug knop verplaatst van onderaan naar rechtsboven
  - Jaar selector verplaatst van header naar toolbar (naast "Nieuw Jaar Aanmaken")
  - Nu consistent met alle andere schermen in de applicatie

**Known Issues:**
Geen bekende issues.

**VERSIE UPDATE CHECKLIST (v0.6.13+):**

**Voor ELKE wijziging (GUI of DB):**
1. ✅ Increment `APP_VERSION` in `config.py`
2. ✅ Update versie in CLAUDE.md (line 69), DEVELOPMENT_GUIDE.md (line 5), DEV_NOTES.md (line 4), PROJECT_INFO.md (line 5 + footer)
3. ✅ Voeg nieuwe feature toe aan PROJECT_INFO.md "WAT IS NIEUW" sectie
4. ✅ Voeg sessie notities toe aan DEV_NOTES.md

**EXTRA bij DB schema wijzigingen:**
4. ✅ Increment ook `MIN_DB_VERSION` in config.py (zelfde als APP_VERSION)
5. ✅ Update schema in `database/connection.py` (create_tables + seed functies)
6. ✅ Maak upgrade script: `upgrade_to_vX_Y_Z.py`
7. ✅ Update db_metadata tabel in upgrade script
8. ✅ Test upgrade pad (oude DB → nieuwe versie)
9. ✅ Test clean install pad (nieuwe DB)
10. ✅ Documenteer schema wijzigingen in DEVELOPMENT_GUIDE.md

**Quick check:**
- GUI-only: APP_VERSION++, MIN_DB_VERSION blijft gelijk
- DB schema: APP_VERSION++, MIN_DB_VERSION++ (beide gelijk)

---

### Sessie 21 Oktober 2025 (Deel 2) - Theme Per Gebruiker (v0.6.12)
**Duur:** ~1 uur
**Focus:** Theme voorkeur van globaal naar per gebruiker verplaatsen

**Voltooid:**
- ✅ **Database Migratie v0.6.11 → v0.6.12**
  - Nieuwe kolom: `gebruikers.theme_voorkeur` (TEXT, default 'light')
  - Migratie van oude globale theme preference naar alle gebruikers
  - Migratie script: `migratie_theme_per_gebruiker.py`
  - Oude `data/theme_preference.json` verwijderd

- ✅ **Main.py Theme Management Refactor**
  - `load_theme_preference()`: Laadt theme uit database per gebruiker
  - `save_theme_preference()`: Slaat theme op in database per gebruiker
  - Login scherm: Altijd light mode (geen gebruiker ingelogd)
  - Na login: Gebruiker's theme geladen en toegepast
  - Logout fix: Reset naar light mode voor login scherm

- ✅ **Connection.py Schema Update**
  - `theme_voorkeur TEXT DEFAULT 'light'` toegevoegd aan gebruikers tabel
  - Seed functie up-to-date voor schone installs

- ✅ **Code Cleanup**
  - `THEME_PREF_FILE` constant verwijderd
  - Onnodige imports (json, os) verwijderd uit main.py
  - Globale theme file systeem volledig vervangen door database

**Probleem Opgelost:**
- Bug: Login scherm toonde dark theme na logout van dark mode gebruiker
- Fix: `on_logout()` reset theme naar light + apply_theme() call

**Technische Beslissingen:**
- Database opslag ipv JSON file (consistenter met rest van applicatie)
- Per gebruiker ipv globaal (elke gebruiker eigen voorkeur)
- Login scherm altijd light (geen verwarring, standaard look)

**User Experience:**
- Jan kiest dark mode → opgeslagen in database
- Jan logt uit → login scherm wordt light
- Piet logt in met light voorkeur → ziet light mode
- Elke gebruiker behoudt eigen theme tussen sessies

**Testing:**
- ✅ Theme opslaan per gebruiker
- ✅ Theme laden bij login
- ✅ Theme resetten bij logout
- ✅ Login scherm altijd light
- ✅ Migratie van oude globale voorkeur
- ✅ Meerdere gebruikers met verschillende themes

**Nieuwe Bestanden:**
- `migratie_theme_per_gebruiker.py` - Database migratie script

**Aangepaste Bestanden:**
- `main.py` - Theme loading/saving per gebruiker + logout fix
- `database/connection.py` - theme_voorkeur kolom in schema
- `CLAUDE.md` - Versie 0.6.12, migratie lijst
- `DEV_NOTES.md` - Deze sessie

**Known Issues:**
Geen bekende issues.

---

### Sessie 21 Oktober 2025 (Deel 1) - Shift Voorkeuren Systeem (v0.6.11)
**Duur:** ~1.5 uur
**Focus:** Shift voorkeuren voor gebruikers - input voor toekomstige automatische planning

**Voltooid:**
- ✅ **Database Migratie v0.6.10 → v0.6.11**
  - Nieuwe kolom: `gebruikers.shift_voorkeuren` (TEXT, JSON format)
  - Opslag voor prioriteit mapping van shift types
  - Migratie script: `migratie_shift_voorkeuren.py`
  - Idempotent en veilig herhaalbaar

- ✅ **VoorkeurenScreen Implementatie**
  - Dashboard → Persoonlijk → Mijn Voorkeuren
  - 4 ComboBoxes voor shift types: Vroeg, Laat, Nacht, Typetabel
  - Prioriteit selectie: 1 (hoogste) tot 4 (laagste), of geen voorkeur
  - Live preview van gekozen volgorde tijdens invoer
  - Validatie: voorkomt dubbele prioriteiten
  - Reset functionaliteit naar standaard (leeg)

- ✅ **JSON Data Model**
  - Format: `{"1": "vroeg", "2": "typetabel", "3": "laat"}`
  - Reverse mapping voor UI display (van value→key naar key→value)
  - NULL = geen voorkeuren ingesteld
  - Flexibel: 1-4 voorkeuren mogelijk, rest mag leeg

- ✅ **UI/UX Features**
  - Info box met duidelijke uitleg hoe systeem werkt
  - Live preview: "1. Vroeg > 2. Typetabel > 3. Laat"
  - Kleurcodering: groen = voorkeuren actief, grijs = geen voorkeuren
  - Beschrijvingen per shift type
  - "Opslaan" en "Reset" knoppen

- ✅ **Main.py Handler**
  - `on_voorkeuren_clicked()` geïmplementeerd
  - Navigation: dashboard → voorkeuren → terug
  - User data meegegeven aan scherm

- ✅ **Database Connection Update**
  - `create_tables()` aangepast met shift_voorkeuren kolom
  - Seed functie up-to-date voor schone installs

**Technische Beslissingen:**
- JSON storage ipv aparte tabel (simpeler, flexibeler)
- ComboBox UI ipv drag-and-drop (duidelijker, minder complex)
- Geen verplichting alle opties in te vullen (gebruiksvriendelijk)
- Validatie op duplicaten (voorkomt fouten)
- Live preview voor directe feedback

**Use Cases:**
1. Teamlid met voorkeur voor vroege diensten: Vroeg=1, Typetabel=2, rest leeg
2. Teamlid die alleen nachtdiensten wil: Nacht=1, rest leeg
3. Teamlid die typetabel volgt: Typetabel=1, rest leeg
4. Teamlid zonder voorkeuren: alles leeg (default gedrag)

**Toekomstig Gebruik:**
- Input voor automatische planning generatie (volgende sprint)
- Planning algoritme respecteert voorkeuren waar mogelijk
- Balans tussen voorkeuren en bedrijfsbehoeften
- Rekening houden met HR regels

**Testing:**
- ✅ Voorkeuren opslaan en laden
- ✅ Live preview updates
- ✅ Validatie duplicaten
- ✅ Reset functionaliteit
- ✅ Database migratie
- ✅ UI layout en styling
- ✅ Navigation flow

**Nieuwe Bestanden:**
- `migratie_shift_voorkeuren.py` - Database migratie script
- `gui/screens/voorkeuren_screen.py` - Voorkeuren scherm (300+ lines)
- `RELEASE_NOTES_v0.6.11.md` - Release notes

**Aangepaste Bestanden:**
- `database/connection.py` - shift_voorkeuren kolom in create_tables()
- `main.py` - on_voorkeuren_clicked() handler
- `CLAUDE.md` - Versie 0.6.11, migratie lijst
- `DEV_NOTES.md` - Deze sessie

**Known Issues:**
Geen bekende issues.

---

### Sessie 20 Oktober 2025 (Deel 2) - Verlof & KD Saldo Systeem (v0.6.10)
**Duur:** ~2 uur
**Focus:** Complete verlof en kompensatiedag saldo tracking systeem

**Voltooid:**
- ✅ **Database Migratie v0.6.9 → v0.6.10**
  - Nieuwe tabel: `verlof_saldo` voor tracking van VV en KD per gebruiker/jaar
  - Kolommen: verlof_totaal, verlof_overgedragen, verlof_opgenomen, kd_totaal, kd_overgedragen, kd_opgenomen
  - Nieuwe speciale code: KD met term 'kompensatiedag' (6e systeem term)
  - Nieuwe kolom: `verlof_aanvragen.toegekende_code_term` voor planner's type keuze
  - 3 nieuwe HR regels: vervaldatum overgedragen verlof (1 mei), max KD overdracht (35 dagen)
  - Bestand: `migratie_verlof_saldo.py`

- ✅ **Service Layer: VerlofSaldoService**
  - `get_saldo()`: Haalt saldo op met real-time berekening van opgenomen dagen
  - `bereken_opgenomen_uit_aanvragen()`: Term-based query op goedgekeurde aanvragen
  - `_bereken_werkdagen()`: Rekening met weekends en feestdagen
  - `check_voldoende_saldo()`: Validatie voor negatief saldo warning
  - `sync_saldo_naar_database()`: Auto-sync na goedkeuring
  - `get_alle_saldi()`: Admin overzicht alle gebruikers
  - `maak_jaar_saldi_aan()`: Bulk aanmaken voor nieuw jaar
  - Bestand: `services/verlof_saldo_service.py`

- ✅ **Admin Scherm: Verlof Saldo Beheer**
  - Overzicht alle gebruikers met VV en KD saldi per jaar
  - Jaar selector (vorig, huidig, volgend jaar)
  - Per gebruiker: totaal, overdracht, opgenomen, resterend (met rood voor negatief)
  - Bewerken dialog met validatie (KD max 35 overdracht)
  - "Nieuw Jaar Aanmaken" functie voor bulk setup
  - Opmerking veld voor notities (bijv. "80% deeltijd")
  - Bestanden: `gui/screens/verlof_saldo_beheer_screen.py`, `gui/dialogs/verlof_saldo_bewerken_dialog.py`

- ✅ **Teamlid Widget: VerlofSaldoWidget**
  - Read-only weergave van eigen saldo (VV en KD)
  - Toon jaarlijks contingent, overdracht, opgenomen, resterend
  - Specifieke labels: "Overdracht uit vorig jaar" (VV) vs "Overdracht uit voorgaande jaren" (KD)
  - Warning voor overgedragen verlof vervaldatum (1 mei) met countdown
  - Auto-refresh na nieuwe aanvraag
  - Bestand: `gui/widgets/verlof_saldo_widget.py`

- ✅ **Verlof Aanvragen Scherm Uitbreiding**
  - HBoxLayout: formulier (2/3) + saldo widget (1/3)
  - Verbeterde layout hiërarchie: SIZE_HEADING voor titel, SIZE_NORMAL voor labels
  - Label gewijzigd: "Tot:" → "t/m:" (duidelijkheid over inclusief einddatum)
  - Reden veld horizontaal naast label (compacter)
  - Saldo refresh na succesvol indienen
  - Bestand: `gui/screens/verlof_aanvragen_screen.py`

- ✅ **Planner Goedkeuring: Type Selectie Dialog**
  - VerlofTypeDialog bij goedkeuring: kies tussen VV of KD
  - Real-time saldo preview met kleurcodering (rood/geel/groen)
  - Toont resterend saldo en saldo na goedkeuring
  - Dynamische code weergave via TermCodeService
  - Planning records gegenereerd met gekozen code
  - `toegekende_code_term` opgeslagen in verlof_aanvragen
  - Auto-sync saldo na goedkeuring
  - Bestand: `gui/screens/verlof_goedkeuring_screen.py` (VerlofTypeDialog class)

- ✅ **Dashboard Integratie**
  - Nieuw menu item "Verlof & KD Saldo Beheer" in Beheer tab
  - Signal + handler in main.py

- ✅ **Database Connection Updates**
  - `seed_speciale_codes()`: KD code toegevoegd
  - `create_tables()`: verlof_saldo tabel en toegekende_code_term kolom

**Business Rules Geïmplementeerd:**
- Verlof overdracht vervalt 1 mei (handmatig cleanup door admin)
- KD overdracht max 35 dagen (validatie in dialog)
- Negatief saldo toegestaan (wordt schuld voor volgend jaar)
- Opgenomen dagen auto-berekend uit goedgekeurde aanvragen (niet handmatig)
- Planner beslist VV of KD (teamlid vraagt "verlof" zonder type)

**Technische Beslissingen:**
- Term-based systeem: queries op 'verlof' en 'kompensatiedag' terms ipv codes
- Real-time berekening van opgenomen dagen (niet cached in database)
- Sync functie update database na elke goedkeuring
- Manual input voor contingenten (ondersteunt deeltijders, verschillende regelingen)
- HBoxLayout voor compacte formulieren (label naast input)

**UI/UX Verbeteringen:**
- "t/m:" label ipv "Tot:" voor duidelijkheid
- Specifieke overdracht labels voor VV en KD
- Saldo preview met kleurcodering in goedkeuring dialog
- Compactere formulier layout met betere hiërarchie

**Testing:**
- Complete workflow getest: admin setup → teamlid aanvraag → planner goedkeuring → saldo sync
- Saldo widget updates correct na aanvraag
- Type dialog toont juiste saldi en kleuren
- Planning records gegenereerd met juiste code

**Migratie Script Iteraties:**
- 8 fixes voor database schema verschillen (naam vs volledige_naam, kleur_hex, etc.)
- Unicode/emoji verwijderd (Windows console compatibiliteit)
- Idempotent script: kan meerdere keren draaien zonder errors

**Known Issues:**
- Geen automatische cleanup overgedragen verlof op 1 mei (handmatig door admin)
- Geen notificatie systeem voor vervaldatum warnings

---

### Sessie 20 Oktober 2025 (Deel 1) - Dark Mode & Rode Lijnen Visualisatie (v0.6.9)
**Duur:** ~3 uur
**Focus:** Bug fixes, dark mode implementatie, en rode lijnen visualisatie

**Voltooid:**
- ✅ **Bug Fix: Calendar Widget Kolom Weergave**
  - Verlof aanvragen kalender: rechtse kolom (zondag) viel gedeeltelijk weg
  - Fix: `min-width: 36px` en `min-height: 28px` toegevoegd aan QAbstractItemView::item
  - `setMinimumWidth(300)` voor gehele kalender widget
  - Toegepast op beide start_datum en eind_datum kalenders
  - Bestand: `gui/screens/verlof_aanvragen_screen.py`

- ✅ **Bug Fix: Feestdagen Niet Herkend in Grid Kalender**
  - Feestdagen buiten huidig jaar werden niet geladen voor buffer dagen
  - Probleem: Buffer dagen (8 voor/na maand) vielen buiten feestdagen dataset
  - Fix: `load_feestdagen_extended()` methode toegevoegd
  - Laadt feestdagen voor 3 jaren: vorig, huidig, volgend jaar
  - Auto-generatie via `ensure_jaar_data()` service
  - Toegepast op beide PlannerGridKalender en TeamlidGridKalender
  - Bestand: `gui/widgets/planner_grid_kalender.py`

- ✅ **Feature: Dark Mode (Nachtmodus)**
  - ThemeManager singleton class voor theme state management
  - Colors class met _LIGHT_THEME en _DARK_THEME dictionaries
  - Visuele ThemeToggleWidget met zon/maan iconen
  - Dashboard rebuild strategie voor correcte theme switching
  - Theme persistence via `data/theme_preference.json`
  - MENU_BUTTON_BG/HOVER kleuren per theme (wit vs grijs)
  - QCheckBox styling toegevoegd aan global stylesheet
  - Alleen beschikbaar in dashboard (design choice)
  - Bestanden:
    - `gui/styles.py` - ThemeManager en Colors
    - `main.py` - Theme loading/saving en apply logic
    - `gui/screens/dashboard_screen.py` - Theme toggle integratie
    - `gui/widgets/theme_toggle_widget.py` - NIEUW bestand
    - `gui/dialogs/handleiding_dialog.py` - Theme info toegevoegd

- ✅ **Feature: Rode Lijnen Visualisatie**
  - Visuele weergave van 28-daagse HR cycli in grid kalenders
  - Dikke rode linker border (4px, #dc3545) markeert periode start
  - Doorlopende lijn van header tot data cellen
  - Tooltip met periode nummer: "Start Rode Lijn Periode X"
  - Timestamp stripping fix (2024-07-28T00:00:00 → 2024-07-28)
  - Dictionary lookup voor snelle O(1) performance
  - Toegepast op beide PlannerGridKalender en TeamlidGridKalender
  - Bestanden:
    - `gui/widgets/planner_grid_kalender.py` - load_rode_lijnen() methode
    - `gui/widgets/teamlid_grid_kalender.py` - load_rode_lijnen() methode

**Technische Beslissingen:**
- Dashboard rebuild voor theme switching ipv widget refresh (betrouwbaarder)
- Theme toggle alleen in dashboard (niet in andere schermen)
- Rode lijnen data wordt geladen bij kalender init (niet on-demand)
- Timestamp stripping via string split ipv datetime parsing (sneller)

**Testing:**
- Alle bugs getest en opgelost
- Dark mode werkt in light en dark theme
- Rode lijnen zichtbaar op correcte datums (19 okt, 16 nov 2025)
- Theme persistence werkt bij herstart

**Bekende Beperkingen:**
- Calendar widgets (QCalendarWidget) behouden light mode styling (Qt limitation)
- Theme toggle alleen in dashboard (andere schermen laden automatisch met gekozen theme)

---

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

## 🛠️ KNOWN ISSUES

### 🟢 KLEIN (Quality of Life)

**Geen openstaande issues!** ✅

---

## ✅ OPGELOSTE BUGS (Laatste Sessions)

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

## 📋 TODO LIST

### Voor Release 1.0 (December 2025)

**Typetabel Systeem** (Hoge Prioriteit) - IN PROGRESS
- [x] Database migratie naar versioned systeem
- [x] TypetabelBeheerScreen met overzicht
- [x] Nieuwe typetabel concept maken
- [x] Grid editor met dropdowns
- [x] Kopiëren functionaliteit
- [x] Verwijderen concept
- [ ] Activeren flow met datum picker
- [ ] Validatie (alle weken ingevuld, realistische patronen)
- [ ] Bulk operaties (kopieer week, vul reeks)
- [ ] Wijzig aantal weken functionaliteit
- [ ] GebruikersBeheer integratie (dynamische max startweek)

**HR Regels Beheer** (Hoge Prioriteit) ✅ KLAAR
- [x] HR regels tabel in database
- [x] CRUD scherm voor regels
- [x] Historiek bijhouden (actief_vanaf, actief_tot)
- [x] Per regel type: 12u_rust, max_uren_week, max_dagen_cyclus, etc.
- [x] UI voor beheer (planner only)
- [x] Historiek standaard zichtbaar
- [ ] Integratie met validatie systeem (volgende sessie)

**Rode Lijnen Beheer** (Medium Prioriteit) ✅ KLAAR
- [x] Config tabel in database
- [x] CRUD scherm voor config
- [x] Historiek bijhouden (actief_vanaf, actief_tot)
- [x] Data ensure service gebruikt config
- [x] Automatische uitbreiding naar toekomst
- [ ] Visuele timeline weergave (nice-to-have)

**Planning Editor** (HOOGSTE PRIORITEIT)
- [x] Grid kalender met editable cells (basis)
- [x] Shift codes invoer per cel
- [x] Save/delete functionaliteit
- [ ] Auto-generatie uit typetabel button
- [ ] Concept vs Gepubliceerd status toggle
- [ ] Bulk operations (copy week, paste, clear)
- [ ] Undo/Redo functionaliteit
- [ ] Validatie integratie (rood/geel/groen feedback)

**Validatie Systeem** (Hoge Prioriteit)
- [ ] PlanningValidator service class
- [ ] 12u rust check implementeren
- [ ] 50u per week check implementeren
- [ ] 19 dagen per 28d cyclus check
- [ ] Max 7 dagen tussen RX/CX check
- [ ] Max 7 werkdagen reeks check
- [ ] **BELANGRIJK: Feestdagen behandelen als zondag** (bijv. 7701 verwacht, niet 7101)
- [ ] Visuele feedback in planning grid
- [ ] Violation messages tooltip
- [ ] Blokkeer publicatie bij violations

**Verlof Beheer** (Medium Prioriteit)
- [x] Verlof aanvraag dialog (teamleden)
- [x] Verlof goedkeuring scherm (planners)
- [x] Status tracking (aangevraagd/goedgekeurd/geweigerd)
- [ ] Verlof saldo tracking
- [ ] Impact preview in planning
- [ ] Notificaties systeem

**Export Functionaliteit** (Medium Prioriteit)
- [ ] Publiceer naar HR (Excel format)
- [ ] Template voor HR export
- [ ] Maandelijks overzicht export (Excel/PDF)
- [ ] Archief export (volledige planning)

**Voorkeuren Systeem** (Lage Prioriteit)
- [ ] Shift voorkeuren per gebruiker
- [ ] Medische beperkingen veld
- [ ] Opmerkingen/notities

**Jaarovergang & Cleanup** (Voor Release)
- [ ] Jaarovergang wizard
- [ ] Preview van te verwijderen data
- [ ] Archivering oude planning (Excel/PDF)
- [ ] Cleanup gedeactiveerde gebruikers
- [ ] Database vacuum/optimize

**Build & Deployment** (Voor Release)
- [ ] .EXE build met PyInstaller
- [ ] Icon voor applicatie
- [ ] Netwerkschijf deployment guide
- [ ] Backup script/cronjob setup
- [ ] Multi-user testing
- [ ] Performance testing
- [ ] Training materiaal
- [ ] Gebruikers handleiding

---

## 💡 DESIGN BESLISSINGEN

### Typetabel Architectuur (v0.6.6)
**Beslissing:** Versioned systeem met status lifecycle  
**Reden:**
- Trial & error workflow: Meerdere concepten naast elkaar
- Harde cutover datum: Actief tot X, nieuwe vanaf X
- Geschiedenis bewaren: Archief voor audit trail
- Simpel: Geen complexe gebruiker ↔ typetabel koppeling

**Alternatieven overwogen:**
- Single typetabel met edit history (geen trial & error)
- Per gebruiker typetabel (te complex, niet nodig)

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

**Formaten:**
- `6-14` → `06:00` tot `14:00` (hele uren shortcut)
- `06:00-14:00` → Volledig formaat
- `06:30-14:30` → Halve uren
- `14:15-22:45` → Kwartieren

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

---

## 📊 DATABASE SCHEMA EVOLUTIE

### v0.6.6 - Typetabel Versioned Systeem
**Nieuwe tabellen:**
- `typetabel_versies` (id, versie_naam, aantal_weken, status, actief_vanaf, actief_tot, ...)
- `typetabel_data` (id, versie_id, week_nummer, dag_nummer, shift_type)

**Verwijderd:**
- `typetabel` (oude structuur, wordt `typetabel_old_backup` na migratie)

**Wijzigingen:**
- Seed functie `seed_typetabel()` volledig herschreven

### v0.6.4 - Shift Codes Systeem
**Nieuwe tabellen:**
- `werkposten`
- `shift_codes`
- `speciale_codes`
- `planning` (basis)

### v0.6.3 - Feestdagen Herwerking
**Wijzigingen:**
- `feestdagen`: Toegevoegd `is_variabel` flag

### v0.6.1 - Gebruikers UUID
**Wijzigingen:**
- `gebruikers`: Toegevoegd `gebruiker_uuid`, timestamps

### v0.6.0 - Database Redesign
**Nieuwe structuur:**
- Foreign keys enabled
- Row factory voor dict access
- Timestamps overal
- Soft delete pattern

---

## 🚀 RELEASE PLANNING

### Release 1.0 - December 2025
**Target:** Productie-klare versie voor eindgebruikers

**Must-Have Features:**
- ✅ Gebruikersbeheer (compleet)
- ✅ Feestdagen beheer (compleet)
- ✅ Shift Codes beheer (compleet)
- ✅ Typetabel Beheer basis (compleet)
- ✅ HR Regels beheer (compleet)
- ✅ Rode Lijnen config beheer (compleet)
- ✅ Handleiding systeem (compleet)
- ✅ UX verbeteringen (compleet)
- 🔨 Typetabel Activatie (volgende sessie)
- 🔨 Planning Editor compleet
- 🔨 Validatie systeem
- 🔨 Verlof beheer compleet
- 🔨 Export functionaliteit
- 🔨 Voorkeuren
- 🔨 Jaarovergang
- 🔨 .EXE build

**Definition of Done:**
- Alle features geïmplementeerd
- Testing compleet (unit + integration)
- Performance acceptable (<2s load tijd)
- Documentation compleet
- Training materiaal klaar
- Deployment guide klaar

### Q1 2026 - Testing & Refinement
**Focus:** Beta testing met echte gebruikers

**Activiteiten:**
- Beta deployment naar kleine groep
- Bug fixes o.b.v. feedback
- Performance optimalisatie
- UI/UX refinement
- Documentation updates
- Training sessies

### Q2 2026 - Production Roll-out
**Focus:** Officiële release

**Activiteiten:**
- Production deployment
- All-hands training
- Support setup
- Monitoring & maintenance
- Issue tracking
- Regular updates

---

## 📚 LESSEN GELEERD

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

---

## 🎯 VOLGENDE SESSIE VOORBEREIDING

**Prioriteit 1: Planning Editor Volledig Maken**

1. **Auto-generatie uit Typetabel:**
   - Button "Genereer uit Typetabel"
   - Dialog met datum range picker
   - Preview van te genereren shifts
   - Overschrijf waarschuwing indien data bestaat
   - Bereken shift per gebruiker/datum uit actieve typetabel

2. **Concept vs Gepubliceerd:**
   - Status toggle button in toolbar
   - Visual indicator (info box met status)
   - Publiceren met bevestiging
   - Blokkeer editing in gepubliceerd mode

3. **Bulk Operaties:**
   - Copy week functionaliteit
   - Paste week functionaliteit
   - Clear range functionaliteit
   - Undo/Redo overwegen

**Geschatte tijd:** 4-5 uur

---

**Prioriteit 2: Typetabel Activatie Flow**

1. **Activeren Dialog maken:**
   - Datum picker voor startdatum
   - Validatie checklist tonen
   - Gebruikers impact preview
   - Bevestiging met warnings

2. **Validatie implementeren:**
   - Check: Alle weken ingevuld?
   - Check: Realistische codes?
   - Check: Gebruikers startweek binnen bereik?

3. **Status transitie:**
   - Oud actief → archief (met actief_tot datum)
   - Nieuw concept → actief (met actief_vanaf datum)
   - Database transactie (rollback bij fout)

4. **GebruikersBeheer update:**
   - Toon max startweek uit actieve typetabel
   - Validatie bij startweek instellen
   - Warning bij gebruikers buiten bereik

**Geschatte tijd:** 3-4 uur

---

*Dit document wordt actief bijgehouden tijdens development*
*Laatste update: 19 Oktober 2025*
*Versie: 0.6.8*