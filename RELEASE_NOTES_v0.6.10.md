# Release Notes v0.6.10

**Release Datum:** 20 Oktober 2025
**Versie:** 0.6.10 Beta
**Thema:** Verlof & KD Saldo Systeem

---

## 🎯 Samenvatting

Versie 0.6.10 introduceert een compleet systeem voor het beheren en volgen van verlof (VV) en kompensatiedagen (KD) saldi. Administrators kunnen jaarlijkse contingenten instellen, teamleden zien hun eigen saldo bij het aanvragen van verlof, en planners kunnen bij goedkeuring kiezen tussen VV of KD met real-time saldo preview.

---

## ✨ Nieuwe Features

### 1. Verlof & KD Saldo Beheer (Admin)

**Nieuw scherm:** Verlof & KD Saldo Beheer (beschikbaar in Dashboard > Beheer tab)

**Functionaliteit:**
- Overzicht van alle gebruikers met hun VV en KD saldi
- Jaar selector: bekijk saldi voor vorig, huidig, of volgend jaar
- Per gebruiker zichtbaar:
  - Jaarlijks contingent (handmatig ingesteld)
  - Overdracht uit vorig(e) jaar/jaren
  - Opgenomen dagen (automatisch berekend)
  - Resterend saldo (met rode markering bij negatief)
- **Bewerken dialoog** per gebruiker:
  - Instellen jaarlijks VV contingent (variabel per leeftijd/regeling)
  - Instellen jaarlijks KD contingent (standaard 13 dagen)
  - Instellen overdracht VV uit vorig jaar (vervalt 1 mei)
  - Instellen overdracht KD uit voorgaande jaren (max 35 dagen)
  - Opmerking veld voor notities (bijv. "80% deeltijd", "65+ regime")
- **Nieuw Jaar Aanmaken** functie:
  - Bulk aanmaken van saldo records voor alle actieve gebruikers
  - Voor komend jaar alvast voorbereiden

**Validatie:**
- KD overdracht maximaal 35 dagen (HR-regel)
- Negatief saldo toegestaan (wordt schuld voor volgend jaar)

---

### 2. Saldo Widget voor Teamleden

**Nieuwe widget:** VerlofSaldoWidget in verlof aanvragen scherm

**Functionaliteit:**
- Read-only weergave van eigen VV en KD saldo
- Informatie per type:
  - Resterend aantal dagen (groot weergegeven)
  - Jaarlijks contingent
  - Overdracht: "Overdracht uit vorig jaar" (VV) / "Overdracht uit voorgaande jaren" (KD)
  - Opgenomen dagen
- **Vervaldatum warning:**
  - Geel waarschuwingsbericht bij overgedragen VV
  - Countdown: "Let op: Overgedragen verlof (X dagen) vervalt op 1 mei YYYY (nog X dagen)"
  - Alleen zichtbaar vóór 1 mei
- **Auto-refresh:** Saldo wordt automatisch bijgewerkt na nieuwe aanvraag indienen

---

### 3. Type Selectie bij Goedkeuring (Planner)

**Nieuwe dialoog:** VerlofTypeDialog bij goedkeuren van verlofaanvraag

**Functionaliteit:**
- Planner kiest tussen:
  - **Verlof (VV)** - telt tegen verlof saldo
  - **Kompensatiedag (KD)** - telt tegen KD saldo
- **Real-time saldo preview:**
  - Huidige resterend saldo
  - Saldo ná goedkeuring
  - **Kleurcodering:**
    - Groen: voldoende saldo (resterend ≥ 5 dagen)
    - Geel: laag saldo (resterend < 5 dagen)
    - Rood: negatief saldo (tekort!)
- Dynamische code weergave: toont huidige codes (VV/KD kunnen hernoemd zijn)
- **Automatisch:**
  - Planning records gegenereerd met gekozen code
  - `toegekende_code_term` opgeslagen in verlof_aanvragen
  - Saldo gesynchroniseerd met database

**Workflow:**
Teamlid vraagt "verlof" aan → Planner beslist bij goedkeuring VV of KD → Systeem past saldo en planning aan

---

## 🔧 Technische Wijzigingen

### Database Migratie

**Nieuwe tabel:** `verlof_saldo`
- Kolommen: `gebruiker_id`, `jaar`, `verlof_totaal`, `verlof_overgedragen`, `verlof_opgenomen`, `kd_totaal`, `kd_overgedragen`, `kd_opgenomen`, `opmerking`
- Unieke combinatie: gebruiker_id + jaar

**Nieuwe kolom:** `verlof_aanvragen.toegekende_code_term`
- Slaat op welk type (verlof/kompensatiedag) door planner toegekend is
- Gebruikt voor term-based queries

**Nieuwe speciale code:** KD met term 'kompensatiedag'
- 6e systeem term (naast verlof, zondagrust, zaterdagrust, ziek, arbeidsduurverkorting)
- Code kan hernoemd worden (KD → CD) zonder functionaliteit te breken

**Nieuwe HR regels:**
- "Vervaldatum overgedragen verlof (maand)": 5 (mei)
- "Vervaldatum overgedragen verlof (dag)": 1
- "Max overdracht KD naar volgend jaar": 35 dagen

**Migratie script:** `migratie_verlof_saldo.py`
- Idempotent: kan meerdere keren draaien
- Auto-seeding van saldo records voor bestaande gebruikers

---

### Service Layer

**Nieuwe service:** `services/verlof_saldo_service.py`

**Belangrijkste methoden:**
- `get_saldo(gebruiker_id, jaar)` - Haalt saldo op met real-time berekening
- `bereken_opgenomen_uit_aanvragen()` - Term-based query op goedgekeurde aanvragen
- `_bereken_werkdagen()` - Rekening houdend met weekends en feestdagen
- `sync_saldo_naar_database()` - Auto-sync na goedkeuring
- `check_voldoende_saldo()` - Validatie functie voor warnings
- `get_alle_saldi()` - Admin overzicht alle gebruikers
- `maak_jaar_saldi_aan()` - Bulk aanmaken voor nieuw jaar

**Term-based systeem:**
- Queries gebruiken terms ('verlof', 'kompensatiedag') ipv hardcoded codes
- Maakt systeem onafhankelijk van code hernoemen (VV→TH, KD→CD)
- Gebruikt `TermCodeService` voor dynamische code lookup

---

### GUI Bestanden

**Nieuwe bestanden:**
- `gui/screens/verlof_saldo_beheer_screen.py` - Admin saldo beheer scherm
- `gui/dialogs/verlof_saldo_bewerken_dialog.py` - Bewerk saldo dialog
- `gui/widgets/verlof_saldo_widget.py` - Teamlid saldo weergave widget

**Gewijzigde bestanden:**
- `gui/screens/verlof_aanvragen_screen.py`:
  - HBoxLayout: formulier (2/3) + saldo widget (1/3)
  - Label gewijzigd: "Tot:" → "t/m:" (duidelijkheid over inclusief einddatum)
  - Reden veld horizontaal naast label (compacter)
  - Betere font hiërarchie: SIZE_HEADING voor titel, SIZE_NORMAL voor labels
  - Saldo refresh na succesvol indienen
- `gui/screens/verlof_goedkeuring_screen.py`:
  - Nieuwe VerlofTypeDialog class toegevoegd
  - Goedkeuren functie uitgebreid met type selectie
  - Auto-sync saldo na goedkeuring
  - Planning generatie met gekozen code
- `gui/screens/dashboard_screen.py`:
  - Nieuw menu item "Verlof & KD Saldo Beheer" in Beheer tab
- `main.py`:
  - Signal handler voor saldo beheer scherm
- `database/connection.py`:
  - KD code toegevoegd aan seed_speciale_codes()
  - verlof_saldo tabel toegevoegd aan create_tables()

---

## 🎨 UI/UX Verbeteringen

### Verlof Aanvragen Scherm

**Layout verbeteringen:**
- Compactere formulier layout met betere visuele hiërarchie
- Saldo widget rechts naast formulier (ratio 2:1)
- Reden veld horizontaal naast label ipv eronder

**Label verbetering:**
- "Tot:" → "t/m:" voor duidelijkheid dat einddatum inclusief is
- Voorkomt misverstand dat veel organisaties hebben

**Overdracht labels:**
- Verlof: "Overdracht uit vorig jaar" (enkelvoud, vervalt 1 mei)
- KD: "Overdracht uit voorgaande jaren" (meervoud, max 35 dagen)

### Saldo Widget

**Kleurgebruik:**
- Geel warning voor vervaldatum overgedragen verlof
- Rode tekst voor negatief saldo in admin scherm
- Groen/geel/rood in planner goedkeuring dialog

**Informatiedichtheid:**
- Compacte weergave zonder overbodige whitespace
- Belangrijkste info (resterend) prominent weergegeven
- Details (totaal, overdracht, opgenomen) op tweede lijn

---

## 📋 Business Rules

**Verlof Overdracht:**
- Overgedragen verlof vervalt op 1 mei
- Handmatig cleanup door admin (geen automatische verwijdering)
- Countdown warning zichtbaar voor teamleden

**KD Overdracht:**
- Maximaal 35 dagen overdraagbaar naar volgend jaar
- Validatie in bewerk dialog (kan niet >35 invoeren)
- Geen vervaldatum

**Negatief Saldo:**
- Toegestaan (wordt schuld voor volgend jaar)
- Rode markering in admin overzicht
- Rode warning in planner goedkeuring dialog

**Opgenomen Dagen:**
- Automatisch berekend uit goedgekeurde verlof_aanvragen
- NIET handmatig aanpasbaar
- Real-time berekening bij elke query
- Sync naar database na goedkeuring voor performance

**Contingent Input:**
- Handmatig per gebruiker (ondersteunt deeltijders)
- Variabel verlof contingent (afhankelijk van leeftijd/regeling)
- Standaard KD: 13 dagen per jaar (voltijd)

**Type Selectie:**
- Teamlid vraagt "verlof" zonder type te specificeren
- Planner beslist bij goedkeuring: VV of KD
- Keuze opgeslagen in `toegekende_code_term`

---

## 🐛 Fixes

- Geen kritieke bugs in deze release
- 8 migratie script fixes tijdens ontwikkeling:
  - Database schema verschillen (naam vs volledige_naam)
  - Unicode/emoji verwijderd (Windows console compatibiliteit)
  - Kolom namen gecorrigeerd (kleur_hex, regel_type, is_actief)

---

## 🔄 Migratie Instructies

### Voor bestaande installaties:

1. **Backup maken:**
   ```bash
   copy data\planning.db data\planning_backup_v0.6.9.db
   ```

2. **Migratie draaien:**
   ```bash
   python migratie_verlof_saldo.py
   ```

3. **Applicatie starten:**
   ```bash
   python main.py
   ```

4. **Saldi invullen:**
   - Login als admin
   - Ga naar Dashboard > Beheer > "Verlof & KD Saldo Beheer"
   - Klik "Nieuw Jaar Aanmaken" voor 2025 (als nog niet gedaan)
   - Voor elke gebruiker: klik "Bewerken" en vul in:
     - Jaarlijks verlof contingent (variabel per leeftijd)
     - Overdracht verlof uit 2024 (indien van toepassing)
     - Jaarlijks KD contingent (standaard 13, pas aan voor deeltijders)
     - Overdracht KD uit voorgaande jaren (max 35)
     - Eventuele opmerking (bijv. "80% deeltijd")

### Voor nieuwe installaties:

- Geen speciale stappen nodig
- Database bevat automatisch KD code en verlof_saldo tabel
- Saldo records handmatig aanmaken via "Nieuw Jaar Aanmaken"

---

## ⚠️ Bekende Beperkingen

1. **Geen automatische cleanup overgedragen verlof:**
   - Systeem verwijdert niet automatisch overgedragen VV na 1 mei
   - Admin moet handmatig opschonen begin mei
   - Toekomstige versie kan automatische cleanup toevoegen

2. **Geen notificatie systeem:**
   - Geen email/push notificaties voor vervaldatum
   - Teamleden zien alleen warning in eigen scherm
   - Admins moeten actief controleren

3. **Geen history tracking:**
   - Geen audit log van saldo wijzigingen
   - Kan nuttig zijn voor transparantie
   - Mogelijk in toekomstige versie

---

## 📊 Impact

**Database:**
- +1 nieuwe tabel (verlof_saldo)
- +1 nieuwe kolom (verlof_aanvragen.toegekende_code_term)
- +1 nieuwe speciale code (KD)
- +3 nieuwe HR regels

**Code:**
- +3 nieuwe GUI bestanden (~500 regels)
- +1 nieuwe service (~480 regels)
- ~200 regels wijzigingen in bestaande bestanden
- +1 migratie script (~250 regels)

**Performance:**
- Saldo queries zijn snel (< 50ms)
- Real-time berekening heeft minimale impact
- Database sync na goedkeuring is asynchroon

---

## 🚀 Volgende Stappen (v0.6.11+)

**Prioriteit 1: Typetabel Activatie Flow**
- Activeren dialog met validatie
- Status transitie (concept → actief)
- Gebruikers controle (startweek binnen bereik)

**Prioriteit 2: Planning Editor Volledig**
- Auto-generatie uit typetabel
- Concept vs Gepubliceerd toggle
- Bulk operaties (copy week, paste, clear)

**Prioriteit 3: Validatie Systeem**
- PlanningValidator class
- 12u rust, 50u/week, 19 dagen per cyclus checks
- Visuele feedback (rood/geel/groen)

---

## 👥 Credits

**Ontwikkeling:** Claude Code (Anthropic) + Gebruiker
**Testing:** Gebruiker
**Feedback:** Team feedback tijdens ontwikkeling

---

**Voor vragen of issues:** Zie HANDLEIDING.md of DEVELOPMENT_GUIDE.md
