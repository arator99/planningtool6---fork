# PLANNING TOOL
Roostersysteem voor Self-Rostering Teams

## VERSIE INFORMATIE
**Huidige versie:** 0.6.15 (Beta)
**Release datum:** 22 Oktober 2025
**Status:** In actieve ontwikkeling - Planning Editor Priority 1 Compleet

---

## WAT IS NIEUW

### Versie 0.6.15 (22 Oktober 2025) ⭐ NIEUW
- ✅ **Concept vs Gepubliceerd Toggle**
  - Planning status management per maand
  - Concept modus: planning nog niet zichtbaar voor teamleden (geel info box)
  - Gepubliceerd modus: planning zichtbaar voor teamleden (groen info box)
  - Planners kunnen altijd wijzigen, ook na publicatie (voor zieken, last-minute)
  - Teamleden zien ALLEEN gepubliceerde planning
  - Bevestiging dialogs bij status wijziging
  - Locatie: Planning Editor (bovenaan scherm)

- ✅ **Bug Fixes & Verbeteringen**
  - Feestdag specifieke error messages ("Op feestdagen moeten zondagdiensten worden gebruikt")
  - Filter blijft behouden bij maand navigatie in kalenders
  - Rode lijnen automatisch hertekend na config wijziging
  - Naam kolom verbreed naar 280px voor lange namen (28+ karakters)
  - Multiscreen setup fix: window blijft nu op primair scherm (niet meer over 2 monitors)

**Workflow:**
1. Planner maakt planning → automatisch concept status
2. Teamleden zien NIETS (verborgen)
3. Planner klikt "Publiceren" → bevestiging
4. Status = gepubliceerd → teamleden zien planning
5. Planner kan altijd nog wijzigen (zieken, etc.)
6. Optioneel: "Terug naar Concept" verbergt planning weer

### Versie 0.6.14 (22 Oktober 2025)
- ✅ **Werkpost Koppeling Systeem**
  - Nieuwe beheer functie: koppel gebruikers aan werkposten
  - Grid interface met checkboxes (gebruikers × werkposten)
  - Multi-post support met prioriteit (1 = eerste keuze, 2 = fallback, etc.)
  - Filters: zoek op naam + toon reserves optie
  - Reserves visueel onderscheiden met [RESERVE] label
  - Locatie: Beheer tab → "Werkpost Koppeling"

- ✅ **Slimme Auto-Generatie uit Typetabel**
  - Planning Editor: knop "Auto-Genereren uit Typetabel" nu actief
  - Intelligente code lookup: typetabel "V" → werkpost → shift_code "7101"
  - Multi-post fallback: zoekt door werkposten tot match gevonden
  - Beschermt verlof, ziekte en handmatig aangepaste shifts
  - Preview met statistieken voor generatie
  - Datum range selectie (standaard: huidige maand)

- ✅ **Bug Fixes**
  - Nieuwe werkpost: "Shifts resetten 12u rust regel" staat nu standaard UIT
  - Speciale codes query error opgelost
  - Kalender refresh na auto-generatie werkt correct

**Workflow:**
1. Configureer werkpost koppelingen (Beheer → Werkpost Koppeling)
2. Vul typetabel in met shift types (V, L, N, dag)
3. Ga naar Planning Editor → Auto-Genereren
4. Selecteer datum bereik → Genereren
5. Planning wordt automatisch ingevuld met juiste shift codes!

### Versie 0.6.13 (21 Oktober 2025)
- ✅ **Database Versie Beheer Systeem**
  - Centrale versie configuratie in `config.py` (APP_VERSION en MIN_DB_VERSION)
  - Automatische compatibiliteit check bij app start
  - Database versie tracking via nieuwe `db_metadata` tabel
  - Versie weergave op loginscherm (app + database versie)
  - Versie weergave in About dialog
  - Bij incompatibele database: duidelijke error met upgrade instructies
  - Upgrade script: `upgrade_to_v0_6_13.py`

- ✅ **UI Verbetering: Verlof Saldo Beheer Scherm**
  - Terug knop verplaatst naar rechtsboven (consistent met andere schermen)
  - Jaar selector verplaatst naar toolbar (logischere plaatsing bij acties)
  - Uniformere gebruikerservaring door hele applicatie

**Waarom belangrijk voor testers:**
- Als je een oude database hebt, krijg je een duidelijke melding
- Je weet altijd welke versie je draait (zie loginscherm)
- Database upgrades zijn nu gecontroleerd en veilig
- Bij problemen: app geeft aan dat je contact moet opnemen
- Consistentere interface: alle schermen hebben terug knop rechtsboven

### Versie 0.6.12 (21 Oktober 2025)
- ✅ **Theme Voorkeur Per Gebruiker**
  - Elke gebruiker kiest eigen light/dark mode voorkeur
  - Opgeslagen in database (niet meer globaal JSON bestand)
  - Login scherm blijft altijd light mode
  - Theme wordt onthouden tussen sessies
  - Database migratie: `migratie_theme_per_gebruiker.py`

### Versie 0.6.11 (21 Oktober 2025)
- ✅ **Shift Voorkeuren Systeem**
  - Dashboard → Persoonlijk → Mijn Voorkeuren
  - Stel prioriteit in voor shift types (Vroeg, Laat, Nacht, Typetabel)
  - Auto-save functionaliteit (geen opslaan knop)
  - Real-time validatie: voorkomt dubbele prioriteiten
  - Input voor toekomstige automatische planning generatie
  - Database migratie: `migratie_shift_voorkeuren.py`

### Versie 0.6.10 (20 Oktober 2025)
- ✅ **Verlof & KD Saldo Systeem - Volledig operationeel**
  - Admin: Verlof & KD Saldo Beheer scherm (Dashboard > Beheer tab)
  - Jaarlijks contingent per gebruiker (handmatig input voor deeltijders)
  - Overdracht management: VV vervalt 1 mei, KD max 35 dagen
  - "Nieuw Jaar Aanmaken" functie voor bulk setup
  - Opmerking veld voor notities (bijv. "80% deeltijd", "65+ regime")
  - Database migratie: `migratie_verlof_saldo.py`

- ✅ **Teamlid: Saldo Widget**
  - VerlofSaldoWidget in verlof aanvragen scherm (rechts naast formulier)
  - Read-only weergave eigen VV en KD saldo
  - Specifieke labels: "Overdracht uit vorig jaar" (VV) vs "Overdracht uit voorgaande jaren" (KD)
  - Warning countdown voor vervaldatum overgedragen verlof (1 mei)
  - Auto-refresh na nieuwe aanvraag

- ✅ **Planner: Type Selectie bij Goedkeuring**
  - VerlofTypeDialog: kies VV of KD bij goedkeuren
  - Real-time saldo preview met kleurcodering (groen/geel/rood)
  - Planning records gegenereerd met gekozen code
  - Auto-sync saldo na goedkeuring
  - Workflow: teamlid vraagt "verlof" → planner beslist VV of KD

- ✅ **UI/UX Verbeteringen**
  - Label gewijzigd: "Tot:" → "t/m:" (duidelijkheid over inclusief einddatum)
  - Compactere formulier layout (reden veld horizontaal naast label)
  - Betere font hiërarchie (SIZE_HEADING voor titels, SIZE_NORMAL voor labels)

- ✅ **Term-based Systeem Uitbreiding**
  - Nieuwe speciale code: KD met term 'kompensatiedag' (6e systeem term)
  - Queries gebruiken terms ipv hardcoded codes
  - Codes kunnen hernoemd worden zonder functionaliteit te breken

### Versie 0.6.9 (20 Oktober 2025)
- ✅ **Dark Mode (Nachtmodus)** - Later verbeterd in v0.6.12
  - ThemeToggleWidget in dashboard met zon/maan iconen
  - Dashboard rebuild strategie voor correcte styling
  - Alleen beschikbaar in dashboard (design choice)

- ✅ **Rode Lijnen Visualisatie**
  - Visuele weergave 28-daagse HR cycli in grid kalenders
  - Dikke rode linker border markeert periode start
  - Tooltip met periode nummer
  - Toegepast op Planner en Teamlid kalenders

- ✅ **Bug Fixes**
  - Calendar widget kolom weergave (zondag gedeeltelijk afgesneden)
  - Feestdagen laden voor 3 jaren (vorig, huidig, volgend)
  - Extended loading voor buffer dagen in kalenders

### Versie 0.6.8 (Oktober 2025)
- ✅ **Rode Lijnen Config Beheer**
  - Versioned configuratie systeem (actief_vanaf, actief_tot)
  - UI scherm voor beheer rode lijnen configuratie
  - Historiek bijhouden van configuratie wijzigingen
  - Database migratie: `migratie_rode_lijnen_config.py`
  - Data ensure service gebruikt nu config ipv hardcoded waarden

- ✅ **UX Verbeteringen**
  - Auto-maximize venster na login voor optimaal schermgebruik
  - Window centreren bij logout
  - Tab-based handleiding met F1 shortcut (Eerste Gebruik, Voor Planners, Voor Teamleden)
  - Filter state behouden bij maand navigatie in kalenders
  - Codes sidebar toegevoegd aan Mijn Planning scherm
  - Grid stretching probleem opgelost met betere layout

- ✅ **Keyboard Shortcuts**
  - F1: Globale handleiding (alle schermen)
  - F2: Shift codes helper in Planning Editor (was F1)

- ✅ **Historiek Standaard Zichtbaar**
  - HR Regels beheer toont historiek standaard
  - Rode Lijnen beheer toont historiek standaard

### Versie 0.6.7 (Oktober 2025)
- ✅ **Term-based Systeem voor Speciale Codes**
  - Systeemcodes beschermd tegen verwijdering (verlof, zondagrust, zaterdagrust, ziek, arbeidsduurverkorting)
  - Codes zelf blijven aanpasbaar (bijv. VV → VL voor verlof)
  - Automatische functies gebruiken termen ipv hardcoded codes
  - Visual indicators voor systeemcodes in UI
  - Database migratie: `migratie_systeem_termen.py`
  - TermCodeService met cache voor performance
  - **Bugfix:** Verlofcode kan niet meer per ongeluk verwijderd worden

### Versie 0.6.6 (Oktober 2025)
- ✅ **Typetabel Beheer Systeem - Volledig operationeel**
  - Versioned systeem (Concept/Actief/Archief status)
  - TypetabelBeheerScreen met overzicht alle versies
  - Nieuwe typetabel concept maken (1-52 weken)
  - Grid editor voor patronen bewerken
  - Kopiëren van typetabellen voor varianten
  - Verwijderen van concept versies
  - Bekijken actieve typetabel (read-only)
  - Database migratie voor bestaande databases
  - Aangepaste seed functie voor schone start

### Versie 0.6.5 (Oktober 2025)
- ✅ Planning Editor eerste iteratie
- ✅ Verlof aanvragen (teamleden)
- ✅ Verlof goedkeuring (planners)

### Versie 0.6.4 (Oktober 2025)
- ✅ Shift Codes Beheer compleet
- ✅ Werkposten systeem
- ✅ Speciale codes beheer
- ✅ Flexibele tijd notatie

---

## HUIDIGE FUNCTIONALITEIT

### ✅ VOLLEDIG OPERATIONEEL

**Inloggen & Beveiliging**
- Veilig login systeem met wachtwoord encryptie
- Rol-gebaseerde toegang (Planner vs Teamlid)
- Wachtwoord wijzigen voor alle gebruikers

**Dashboard**
- Overzichtelijk menu met tabs
- Verschillende opties voor planner en teamleden
- Snelle navigatie
- Tab-based handleiding (F1)
- Auto-maximize na login

**Gebruikersbeheer** (Planners)
- Teamleden toevoegen en bewerken
- Reserve medewerkers markeren
- Startweek typedienst instellen
- Accounts activeren/deactiveren

**Feestdagen Beheer** (Planners)
- Automatische generatie per jaar
- Slimme Paasberekening
- Extra feestdagen toevoegen

**Shift Codes Beheer** (Planners)
- Werkposten configureren per team
- Grid editor voor shift codes
- Flexibele tijd notatie
- Speciale codes (VV, RX, DA, Z, etc.)

**Typetabel Beheer** (Planners) ⭐ NIEUW
- Versioned systeem (Concept/Actief/Archief)
- Flexibel patroon (1-52 weken)
- Grid editor voor patronen
- Nieuwe typetabel maken
- Kopiëren functionaliteit
- Multi-post support (V1, V2, L1, etc.)

**Planning & Verlof**
- Planning Editor basis
- Verlof aanvragen (teamleden)
- Verlof goedkeuring (planners)

**Grid Kalender Widgets**
- Herbruikbare kalender componenten
- Filter functionaliteit
- Status overlays

---

## IN ONTWIKKELING

### 🔨 VOOR RELEASE 1.0 (December 2025)

**Typetabel Features:**
- Activeren met datum picker
- Validatie checks
- Bulk operaties

**Planning Editor:**
- Auto-generatie uit typetabel
- Concept vs Gepubliceerd
- Validatie feedback

**Validatie Systeem:**
- HR regels checking
- Visuele indicatoren
- 12u rust, 50u/week, 19 dagen/28d

**Export:**
- Excel export naar HR
- Archief exports

---

## EERSTE KEER INLOGGEN

1. Start de applicatie
2. Log in met:
   - **Gebruikersnaam:** `admin`
   - **Wachtwoord:** `admin`
3. ⚠️ **Belangrijk:** Wijzig het admin wachtwoord direct!

---

## GEBRUIKERSINSTRUCTIES

### Voor Planners
1. **Teamleden beheren:** Dashboard → Beheer → Gebruikersbeheer
2. **Feestdagen instellen:** Dashboard → Instellingen → Feestdagen
3. **Shift codes configureren:** Dashboard → Instellingen → Shift Codes & Posten
4. **Typetabel beheren:** Dashboard → Instellingen → Typetabel ⭐ NIEUW
5. **Planning maken:** Dashboard → Beheer → Planning Editor

### Voor Teamleden
1. **Eigen rooster bekijken:** Dashboard → Mijn Planning
2. **Verlof aanvragen:** Dashboard → Mijn Planning → Verlof Aanvragen
3. **Wachtwoord wijzigen:** Dashboard → Mijn Planning → Wijzig Wachtwoord

---

## TYPETABEL SYSTEEM ⭐ NIEUW

### Wat is een Typetabel?

Een typetabel is een **herhalend patroon** dat gebruikt wordt om automatisch planning te genereren. Het patroon kan variëren van 1 tot 52 weken.

**Voorbeeld 6-weken patroon:**
```
Week 1: V, V, RX, L, L, CX, RX
Week 2: L, L, RX, N, N, CX, RX
Week 3: N, N, RX, V, V, CX, RX
Week 4: V, V, RX, L, L, CX, RX
Week 5: L, L, RX, N, N, CX, RX
Week 6: N, N, RX, V, V, CX, RX

Dan herhaalt: Week 7 = Week 1, Week 8 = Week 2, etc.
```

### Versioned Systeem

**Status Types:**
- **CONCEPT**: Voor trial & error met nieuwe patronen
- **ACTIEF**: De huidige typetabel in gebruik (altijd maar 1)
- **ARCHIEF**: Oude typetabellen voor geschiedenis

### Multi-Post Support

Wanneer je meerdere posten hebt, gebruik je codes met post nummers:

**Voorbeeld Officieren (2 posten):**
```
Week 1: V1, V1, RX, L2, L2, CX, RX
Week 2: L1, L1, RX, N1, N1, CX, RX

Codes betekenis:
- V1 = Vroege dienst Post 1
- V2 = Vroege dienst Post 2  
- L1 = Late dienst Post 1
- L2 = Late dienst Post 2
- N1 = Nachtdienst Post 1
- RX = Zondagsrust
- CX = Zaterdagsrust
```

### Hoe werkt het?

1. **Startweek**: Elke medewerker krijgt een startweek (bijv. 1-6)
2. **Herhaling**: Het patroon herhaalt automatisch
3. **Automatisch**: Planning kan gegenereerd worden uit typetabel

### Typetabel Beheren

**Nieuwe Typetabel Maken:**
1. Dashboard → Instellingen → Typetabel
2. Klik "+ Nieuwe Typetabel"
3. Vul naam in (bijv. "Interventie 18 weken Winter 2026")
4. Kies aantal weken (1-52)
5. Grid editor opent automatisch
6. Vul patronen in per week
7. Klik "Opslaan"

**Typetabel Kopiëren:**
1. Klik "Kopiëren" bij een versie
2. Nieuwe concept wordt aangemaakt
3. Pas aan naar wens
4. Activeer wanneer klaar

**Typetabel Activeren:**
*(Komt in volgende update)*

---

## SHIFT CODES SYSTEEM

### Werkposten

**Voorbeeld Interventie:**
- Weekdag: 7101 (V 06:00-14:00), 7201 (L 14:00-22:00), 7301 (N 22:00-06:00)
- Zaterdag: 7401 (V), 7501 (L), 7601 (N)
- Zondag: 7701 (V), 7801 (L), 7901 (N)

**Tijd Formaten:**
- `6-14` → 06:00 tot 14:00
- `06:00-14:00` → Volledig formaat
- `06:30-14:30` → Halve uren
- `14:15-22:45` → Kwartieren

### Speciale Codes

- **VV** - Verlof
- **VD** - Vrij van dienst
- **DA** - Arbeidsduurverkorting
- **RX** - Zondagsrust
- **CX** - Zaterdagsrust
- **Z** - Ziek
- **T** - Reserve/Thuis

---

## HR REGELS

Het systeem controleert op:
1. Minimale rust: 12 uur tussen diensten
2. Maximum werkuren: 50 uur per week
3. Maximum werkdagen: 19 dagen per 28-dagen cyclus
4. Maximum 7 dagen tussen RX/CX
5. Maximum 7 werkdagen achter elkaar

---

## DATABASE MIGRATIE

### Meest Recente Migraties

**v0.6.14 → v0.6.15: Rode Lijnen Seed Datum Fix** ⭐ NIEUW
```bash
python fix_rode_lijnen_seed_datum.py
```
- Herstelt rode lijnen van 28 juli 2024 → 29 juli 2024 (correcte cyclus)
- Update rode_lijnen_config indien nodig
- Idempotent: veilig om meerdere keren te draaien
- **LET OP:** Alleen nodig voor databases met oude seed datum

**v0.6.13 → v0.6.14: Werkpost Koppeling**
```bash
python migratie_gebruiker_werkposten.py
```
- Maakt `gebruiker_werkposten` tabel voor many-to-many relatie
- Koppelt gebruikers aan werkposten met prioriteit
- Nodig voor slimme auto-generatie functionaliteit

**v0.6.12 → v0.6.13: Database Versie Tracking**
```bash
python upgrade_to_v0_6_13.py
```
- Maakt `db_metadata` tabel voor versie tracking
- Initialiseert database versie op 0.6.13
- Vanaf nu wordt database versie automatisch gecontroleerd bij app start

**LET OP:** Vanaf v0.6.13 heeft de app een versiebeheersysteem. Bij het starten wordt automatisch gecontroleerd of je database compatibel is. Als dat niet zo is, krijg je een duidelijke melding.

**v0.6.11 → v0.6.12: Theme Per Gebruiker**
```bash
python migratie_theme_per_gebruiker.py
```
- Voegt `theme_voorkeur` kolom toe aan gebruikers tabel
- Migreert oude globale theme naar alle gebruikers
- Verwijdert oude `theme_preference.json` bestand

**v0.6.10 → v0.6.11: Shift Voorkeuren**
```bash
python migratie_shift_voorkeuren.py
```
- Voegt `shift_voorkeuren` kolom toe aan gebruikers tabel
- JSON format voor prioriteit mapping

**v0.6.9 → v0.6.10: Verlof & KD Saldo**
```bash
python migratie_verlof_saldo.py
```
- Maakt `verlof_saldo` tabel voor VV en KD tracking
- Voegt KD speciale code toe met term 'kompensatiedag'
- Voegt `toegekende_code_term` kolom toe aan verlof_aanvragen

### Eerdere Migraties

**v0.6.7 → v0.6.8:** `python migratie_rode_lijnen_config.py`
**v0.6.6 → v0.6.7:** `python migratie_systeem_termen.py`
**v0.6.5 → v0.6.6:** `python migratie_typetabel_versioned.py`

**Voor schone start:**
Geen migratie nodig - automatisch correct aangemaakt.

---

## SYSTEEM VEREISTEN

- Windows 10 of nieuwer
- Schermresolutie: minimaal 1366x768
- RAM: minimaal 4GB
- Opslag: minimaal 100MB

---

## BEKENDE ISSUES

### ✅ OPGELOST
- Unicode karakters in buttons
- Table layout crashes
- Feestdagen bewerken
- Typetabel seed conflict
- Filter reset bij maand navigatie (v0.6.8)
- Grid stretching op full-screen (v0.6.8)
- F1 conflict met shift codes helper (v0.6.8)
- Rode lijnen verkeerde seed datum (v0.6.15)
- Multiscreen setup: window over 2 monitors (v0.6.15)
- Dark mode: grid tekst niet leesbaar (v0.6.15)
- About dialog: PROJECT_INFO niet gevonden in .exe (v0.6.15)

### ⚠️ BEKEND
- Netwerklatency bij gebruik vanaf netwerkschijf
- Grote datasets kunnen traag laden

---

## ROADMAP

### Release 1.0 - December 2025
**Productie-klare versie**
- ✅ Gebruikersbeheer
- ✅ Feestdagen beheer
- ✅ Shift Codes beheer
- ✅ Typetabel Beheer basis ⭐
- ✅ HR Regels beheer ⭐
- ✅ Rode Lijnen config beheer ⭐
- ✅ Handleiding systeem ⭐
- ✅ .EXE build ⭐
- ✅ Werkpost Koppeling (v0.6.14) ⭐
- ✅ Auto-Generatie uit Typetabel (v0.6.14) ⭐
- ✅ Concept vs Gepubliceerd Toggle (v0.6.15) ⭐
- 🔨 Typetabel Activatie
- 🔨 Planning Editor bulk operaties (copy week, paste, clear)
- 🔨 Validatie systeem met visuele feedback
- 🔨 Export functionaliteit naar Excel

### Q1 2026 - Testing
**Beta testing met eindgebruikers**

### Q2 2026 - Roll-out
**Productie release**

---

## SUPPORT

**Bugs of problemen:**
- Neem contact op met je planner
- Vermeld versienummer en beschrijving

**Technische documentatie:**
- Ontwikkelaars: zie DEVELOPMENT_GUIDE.md
- Eindgebruikers: dit document

---

## TOEPASSINGSGEBIED

Deze tool is voor **alle teams met self-rostering**, niet alleen interventie. Het shift codes systeem is volledig configureerbaar per team.

**Geschikt voor:**
- Teams met roterend rooster
- Shift-based werkomgeving
- Variabele rooster lengtes (6, 12, 18, 52 weken)
- Multi-post organisaties

---

*Voor technische details: zie DEVELOPMENT_GUIDE.md*
*Laatste update: 22 Oktober 2025*
*Versie: 0.6.15*