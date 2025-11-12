# PLANNING TOOL
Roostersysteem voor Self-Rostering Teams

## VERSIE INFORMATIE
**Huidige versie:** 0.6.29 (Beta)
**Release datum:** 12 November 2025
**Status:** Notitie Gelezen/Ongelezen Tracking + Badge Systeem

---

## WAT IS NIEUW

### Versie 0.6.29 (12 November 2025)
- ✅ **Database Schema Uitbreiding** - Notitie Gelezen/Ongelezen Tracking
  - **Nieuwe kolom:** notitie_gelezen (BOOLEAN DEFAULT 0) in planning tabel
  - **Migratie script:** upgrade_to_v0_6_29.py voor safe upgrade
  - **Standaard waarde:** 0 (alles ongelezen bij eerste migratie)
- ✅ **Rode Badge Systeem** - Visuele notificatie voor ongelezen notities
  - **Dashboard Planning tab:** Rode bol met cijfer bij "Notities Overzicht" knop
  - **Pattern:** Analoog aan verlof goedkeuring badge (50x50px cirkel, rechts in knop)
  - **Query:** Tel notities met `[Naam]:` prefix (niet `[Planner]:`) en `notitie_gelezen = 0`
  - **Real-time update:** Badge refresht na markeren als gelezen
- ✅ **Notities Overzicht Scherm** - Centrale notitie management voor planners
  - **Tabel met 5 kolommen:** ID (verborgen), Datum, Teamlid, Notitie, Status (Ongelezen/Gelezen)
  - **Filter opties:** Alle notities / Alleen ongelezen (dropdown)
  - **Multi-selectie:** Selecteer meerdere notities tegelijk
  - **Markeer als gelezen:** Knop onderaan voor bulk operatie
  - **Visual feedback:** Ongelezen notities in bold, kleuren per status (rood/groen)
  - **Sortering:** Nieuwste eerst (datum DESC)
- ✅ **Navigation Integratie**
  - **Signal:** notities_overzicht_clicked in dashboard_screen.py
  - **Handler:** on_notities_overzicht_clicked() in main.py
  - **Dashboard reference:** Doorgegeven voor badge refresh functionaliteit
- ✅ **Planning Editor Ongewijzigd**
  - **Groen hoekje blijft altijd zichtbaar:** Geen onderscheid gelezen/ongelezen in grid
  - **User feedback:** Planner wilde alle notities zichtbaar, ongeacht status

### Versie 0.6.28 (11-12 November 2025)
- ✅ **Database Schema Uitbreiding** - Voornaam/Achternaam Split
  - **Nieuwe kolommen:** voornaam, achternaam (volledige_naam behouden voor compatibility)
  - **Intelligente parsing:** Belgische naam heuristiek (laatste woord = voornaam, rest = achternaam)
  - **Samengestelde achternamen:** "Van Den Ackerveken Stef" correct gesplitst
  - **Migratie script:** upgrade_to_v0_6_28.py voor safe upgrade
- ✅ **ISSUE-002 Fix: Sortering op Achternaam** - Intuïtievere gebruikerslijsten
  - **Oude sortering:** Alfabetisch op eerste letter van volledige naam
  - **Nieuwe sortering:** is_reserve, achternaam, voornaam (vaste mensen eerst, dan reserves)
  - **Impact:** Planners zien teamleden logischer gesorteerd in alle grids
- ✅ **Werkpost Validatie UI Integratie** - Visuele feedback in planning grid
  - **Backend:** Was al compleet (check_werkpost_koppeling in constraint_checker.py)
  - **Fix:** Violation constructor kreeg ontbrekende velden (gebruiker_id, datum_range)
  - **Friendly names:** 'werkpost_onbekend' -> 'Onbekende werkpost koppeling'
  - **Visual feedback:** Gele overlay (WARNING) + tooltip + HR Summary box
  - **Testing:** test_werkpost_validation.py (all tests passed)
- ✅ **ISSUE-005 Fix: HR Overlay Persistence** - Constant visual feedback
  - **Probleem:** Rode/gele HR overlay verdween bij cel klik (QLineEdit had hard-coded white background)
  - **Root cause:** Editor stylesheet verborg onderliggende overlay
  - **Fix:** EditableLabel.overlay_kleur attribute tracking + conditional stylesheet (8 code changes)
  - **Result:** HR/verlof overlays blijven zichtbaar tijdens edit (planner heeft constante feedback)
- ✅ **Unicode Cleanup** - Windows Encoding Compatibility
  - **Probleem:** Unicode pijltjes (→) kunnen encoding problemen geven op Windows cmd/PowerShell
  - **Fix:** 13 voorkomens vervangen met ASCII -> in actieve Python code
  - **Impact:** Veiliger voor Windows console output
- ✅ **Code Documentatie** - Section-level Comments
  - **constraint_checker.py:** 4 major section headers (1600+ lines navigeerbaar)
  - **planning_validator_service.py:** 2 major section headers (540 lines)
  - **Voordeel:** Makkelijker navigeren voor developers, quick reference
- ✅ **Typetabel Pre-Validatie Improvements** - Theoretical Pattern Validation
  - **Standalone "Valideer" knop:** Pre-activatie check zonder activeren
  - **Theoretische modus:** 1 dummy gebruiker, geen feestdagen, start op maandag
  - **2.5 cycli simulatie:** Week alignment fix (Week 1 Dag 1 = maandag)
  - **Detailed report:** Exact locaties (Week X, Dagnaam) met max 10 violations per type

### Versie 0.6.27 (11 November 2025) ⭐ HR VALIDATIE v1.0 COMPLEET
- ✅ **FASE 5: Typetabel Pre-Activatie HR Validatie** - Last piece of HR validation roadmap
  - **Pre-activatie check:** HR validatie draait VOOR typetabel activatie
  - **Simulatie:** 2.5 cycli van typetabel (bijv. 6 weken → 105 dagen)
  - **Cross-boundary detectie:** Violations aan begin/eind van cyclus gedetecteerd
  - **Soft warning:** Gebruiker ziet violations maar mag doorgaan (niet blokkerend)
  - **Rich dialog:** Breakdown per violation type (errors/warnings)
  - **Intelligent feedback:** "10 dagen te veel opeenvolgende werkdagen" ipv 10 aparte meldingen
- ✅ **Excel HR Layout Migration** - HR-conforme export layout
  - **New row structure:** Empty row 1, header row 2 met "mmm/jj" datum, column headers row 3
  - **HR color scheme:** Feestdagen geel, weekends oranje, werkdagen grijs
  - **Priority coloring:** Feestdag > Weekend > Werkdag in data cellen
  - **Professional format:** Merged cells, borders, consistent widths
- 🎉 **HR VALIDATIE SYSTEEM 100% COMPLEET (38/38 uur):**
  - FASE 1-4: Core logic, DB integration, UI integration, pre-publicatie (28u - v0.6.26)
  - FASE 5: Typetabel pre-validatie (10u - v0.6.27)
  - **7 HR regels:** 12u rust, 50u/week, 19 dagen/cyclus, 7 dagen tussen RX, 7 werkdagen reeks, max weekends, nacht→vroeg
  - **Real-time feedback:** Rode/gele overlays in planning grid
  - **On-demand validatie:** "Valideer Planning" knop voor batch check
  - **Pre-publicatie warning:** Soft warning voor publiceren
  - **Pre-activatie warning:** Soft warning voor typetabel activatie
  - **13 automated tests:** All passed

### Versie 0.6.26.2 (10 November 2025)
- ✅ **HR Violations Deduplicatie** - Accurate counting in summary box
  - **Fix:** 10-daagse reeks toont nu 1 item ipv 10 aparte items
  - **Smart formatting:** "Te veel werkdagen: 10 dagen (1 jan - 10 jan)"
  - **Object ID deduplicatie:** Gebruikt Python object ID voor accurate counts
- ✅ **Cache Toggle Feature** - Performance testing configuratie
  - **Toggle:** `ENABLE_VALIDATION_CACHE` in config.py
  - **Purpose:** Test batch vs direct queries op netwerk database

### Versie 0.6.26.1 (8 November 2025)
- ✅ **Alle realtime validatie uitgeschakeld**
  - **Latency problemen:** Live testen toonden latency problemen aan 
  - **Nieuwe nummering:** Fork gemaakt naar 0.6.26.1
  - **Design change:** Alle realtime validatie uitgeschakeld, validatie op aanroepcl

### Versie 0.6.26 (4 November 2025)
- ✅ **HR Validatie Waarschuwing bij Publicatie** - Informed decision making
  - **Pre-validatie:** Alle gebruikers worden gevalideerd (alle 6 HR checks)
  - **Waarschuwing:** Bij violations verschijnt dialoog met alle gebruikers + counts
  - **Gebruiker keuze:** "Bent u zeker dat u wil publiceren met planningsfouten?"
  - **Flexibiliteit:** Kan toch publiceren (bijv. bij bugs in validatie systeem)
  - **Workflow:** Vul in → Valideer → Bekijk violations → Publiceer (met of zonder fixes)
- ✅ **HR Validatie UX Verbeteringen** - Workflow optimalisatie
  - **ISSUE-007:** Real-time validation DISABLED (te irritant + ghost violations)
    - **Was:** Popup bij elke cel edit + violations op verkeerde datums
    - **Nu:** Alleen batch validatie via "Valideer Planning" knop
    - **Impact:** Rustig kunnen werken zonder interruptions
  - **ISSUE-006:** HR Summary Box altijd zichtbaar met scroll + ALLE violations
    - **Was:** Box verborgen bij geen violations, tekst afgeknipt, max 5 per gebruiker
    - **Nu:** Altijd zichtbaar met "Geen HR violations gevonden" message
    - **Scroll:** QScrollArea wrapper (max 200px hoogte) voor lange lijsten
    - **Volledig:** Toont ALLE violations van ALLE gebruikers (geen limits)
  - **Tooltip fix:** HTML tags verwijderd (plain text rendering)
- ✅ **HR Validatie Bug Fixes** - Core logica verbeteringen
  - **BUG-005 & BUG-005b:** Segmented planning validatie met datum gap detection
    - **Probleem:** Weekend-only planning (za/zo) triggerde valse RX violations
    - **Oplossing:** Planning gesplitst in continue segmenten bij lege cellen/datum gaps
    - **Impact:** Partial planning invulling mogelijk zonder valse violations
- ✅ **Automated Testing Suite** - 16 constraint scenario tests (100% pass rate)
  - **Test coverage:** RX/CX gaps, werkdagen reeks, 12u rust, 50u week, 19 dagen cyclus
  - **Edge cases:** Cross-month, cross-year, boundary tests (7 vs 8 dagen)
  - **Segmented tests:** Weekend-only, complete planning, datum gap scenarios
  - **Files:** `test_constraint_scenarios.py`, `test_segmented_rx_check.py`, `test_datum_gap_segmentation.py`

### Versie 0.6.25 (3 November 2025)
- ✅ **HTML Handleiding** - Statisch HTML bestand voor betere onderhoudbaarheid
  - **Nieuw bestand:** `Handleiding.html` in root directory (geen hardcoded Python meer)
  - **Rendering:** QWebEngineView voor HTML weergave met lokale screenshots
  - **Voordelen:** Makkelijker te updaten, betere opmaak, sneller te laden
  - **Bug fix:** Typo in error message gerepareerd (`<boy>` → `<body>`)
- ✅ **Dashboard Reorganisatie** - Nieuwe tab indeling voor betere UX
  - **Voor planners:** 4 tabs (was: 3)
    - **Persoonlijk:** Eigen planning, verlof aanvragen, notities, wachtwoord
    - **Planning (NIEUW):** Planning Editor + Verlof Goedkeuring (met badge)
    - **Beheer:** Gebruikers, Shift Codes, Werkpost Koppeling, Verlof Saldo, Typetabel
    - **HR-instellingen:** HR Regels, Rode Lijnen, Feestdagen
  - **Voor teamleden:** Blijft 1 tab (Persoonlijk)
  - **Voordeel:** Duidelijkere scheiding tussen planning, beheer en instellingen
- ✅ **Notificatie Badge** - Visuele indicator voor openstaande verlofaanvragen
  - **Rode bol met cijfer:** Toont aantal pending verlofaanvragen in Verlof Goedkeuring knop
  - **Real-time update:** Badge cijfer updatet automatisch bij statuswijziging
  - **Refresh mechanisme:** Hele Planning tab wordt herladen na goedkeuring/weigering
  - **Voor planners:** Direct zichtbaar hoeveel aanvragen op behandeling wachten
  - **Custom widget:** Professionele styling met hover effect en juiste positionering
- ✅ **Performance Verbetering - ValidationCache** - Dramatisch sneller laden over netwerk 🚀
  - **Probleem opgelost:** Planning Editor laden duurde 30-60 seconden over netwerk drive
  - **Root cause:** Te veel database queries (900+ queries per maand)
  - **Oplossing:** Slimme cache met batch loading
  - **Resultaat:** Planning Editor laadt nu in **minder dan 1 seconde** (2000x sneller!)
  - **Technisch:** 5 queries ipv 900+ (batch preloading van bemannings validatie)
  - **Voor gebruikers:** Geen wachttijd meer bij openen Planning Editor of maand navigatie
  - **Smart update:** Cache wordt automatisch bijgewerkt na shift wijziging
  - **Transparant:** Werkt automatisch op achtergrond, geen gebruikersactie nodig

### Versie 0.6.23 (30 Oktober 2025)
- ✅ **HR Regels Vervaldatum Vereenvoudigd** - Planner-vriendelijke interface
  - **Probleem opgelost:** Twee aparte regels (dag + maand) was verwarrend
  - **Nieuwe weergave:** "Vervaldatum overgedragen verlof: 1 mei" (één regel, leesbaar)
  - **Intuïtieve edit:** Dag/maand dropdowns (1-31, januari-december) in plaats van technische nummers
  - **Database format:** "DD-MM" (bijv. "01-05" voor 1 mei)
  - **Dynamische lookup:** Code gebruikt HR regels uit database (niet meer hardcoded)
  - **Flexibiliteit:** Vervaldatum aanpasbaar per organisatie via UI
  - **Default waarde:** 1 mei (Nederlandse standaard) voor nieuwe installaties
  - **Migratie:** upgrade_to_v0_6_23.py converteert oude dag+maand regels automatisch
- ✅ **Nieuwe HR Regels Service** - Herbruikbare helper functies
  - **get_verlof_vervaldatum():** Haal vervaldatum op uit database
  - **get_actieve_regel():** Generic helper voor alle HR regels
  - **Fallback strategie:** Robuust bij parse errors
- ✅ **Datum Type Support** - Schaalbaar voor toekomstige datum regels
  - **Eenheid "datum":** Nieuw type naast uur, dagen, etc.
  - **Automatische UI:** Edit dialog detecteert type en toont juiste widget
  - **Versioning:** Historiek van regel wijzigingen behouden

### Versie 0.6.22 (30 Oktober 2025)
- ✅ **Verlof Saldo Berekening Fixes** - Twee belangrijke correcties
  - **Fix #1: Kalenderdagen i.p.v. werkdagen** - Verlof wordt nu geteld in kalenderdagen (inclusief weekends)
    - **Probleem opgelost:** 13-22 november = 10 dagen (was: 7 werkdagen zonder weekends)
    - **Consistent:** Saldo telling komt overeen met aanvraag scherm
  - **Fix #2: Planning als source of truth** - Saldo berekening gebruikt daadwerkelijke planning records
    - **Probleem opgelost:** Handmatige wijzigingen (VV → CX/RX) worden nu correct meegenomen
    - **Voorbeeld:** 10 dagen aangevraagd, 2 handmatig gewijzigd → saldo toont 8 dagen opgenomen ✓
  - **Gedragswijziging:** Saldo telt alle planning (concept + gepubliceerd) - feedback gebruikers gevraagd
  - **Technisch:** Kalenderdagen berekening: `(eind - start).days + 1` (simpeler en correcter)

### Versie 0.6.21 (29 Oktober 2025)
- ✅ **Kritische Shift Codes** - Selectieve bemanningscontrole voor belangrijke shifts
  - **Flexibele markering:** Planner bepaalt zelf welke shifts kritisch zijn (bijv. vroege dienst = kritisch, late dienst = niet)
  - **Grid editor:** Nieuwe "Kritisch" kolom met checkbox per shift (12 checkboxes: 3 dag types × 4 shift types)
  - **Visual indicator:** ⚠ symbool toont kritische shifts in overzicht (Weekdag: V=7101 ⚠, L=7201)
  - **Slimme validatie:** Bemanningscontrole overlay (rood/groen/oranje) valideert ALLEEN kritische shifts
  - **Excel rapport:** Labels aangepast naar "Bemannings Validatie (Kritische Shifts)"
  - **Database upgrade:** Nieuwe kolom shift_codes.is_kritisch (run upgrade_to_v0_6_21.py)
  - **Praktisch voorbeeld:** Interventie vroeg = kritisch (moet ingevuld), Interventie laat = niet kritisch (mag leeg)
- ✅ **UX Verbetering** - Oranje overlay voor dubbele shifts (was geel)
  - **Betere contrast:** Oranje overlay (#FFA726) onderscheidbaar van gele zon-/feestdag achtergrond
  - **Visuele duidelijkheid:** Geen verwarring meer tussen dubbele shifts en weekend kleuren
  - **Excel consistent:** Oranje achtergrond (#FFCC80) ook in validatie rapport
- ✅ **Kritische Bugfix** - Atomic publicatie (Excel export + database update)
  - **Probleem opgelost:** Planning blijft op concept als Excel export faalt (was: gepubliceerd zonder Excel)
  - **Data integriteit:** Planning status en Excel export blijven altijd synchroon
  - **Duidelijke errors:** Specifieke foutmelding bij open Excel bestand of permission issues
  - **User-friendly:** Concrete actiestappen in foutmeldingen (sluit Excel, check permissions)

### Versie 0.6.20 (28 Oktober 2025)
- ✅ **Bemannings Controle Systeem** - Automatische validatie shift bemanning
  - **Status overlay:** Groen (volledig), oranje (dubbel), rood (onvolledig) op datum headers
  - **Intelligente detectie:** Gebruikt shift_codes tabel als configuratie (1 code = 1 persoon)
  - **Dubbele code warning:** Waarschuwing bij dubbele toewijzing met override optie
  - **Excel validatie rapport:** Nieuwe sheet met dag-per-dag status overzicht
  - **Publicatie validatie:** Samenvatting in publicatie dialog voor final check
  - **Real-time updates:** Overlay en tooltips updaten direct na wijziging
  - **Qt CSS techniek:** `qlineargradient()` voor semi-transparante overlays

### Versie 0.6.19 (28 Oktober 2025)
- ✅ **HR Rules Visualisatie** - Rode Lijnen Werkdagen Tracking in Planning Editor
  - **2 nieuwe kolommen:** "Voor RL" en "Na RL" (vóór/na de rode lijn periode)
  - **Rode scheiding:** 3px rode border tussen beide kolommen visualiseert de rode lijn
  - **Werkdagen telling:** Toont aantal gewerkte dagen per 28-daagse cyclus periode
  - **Visuele waarschuwing:** Rode overlay als individuele periode > 19 dagen
  - **Real-time updates:** HR cijfers updaten direct na shift wijziging (geen refresh nodig)
  - **Tooltips:** "X/19 dagen" + periode nummer + datumbereik voor context

- ✅ **Slimme Periode Detectie** - Intelligente rode lijn herkenning
  - **2-stappen logica:** Zoekt eerst rode lijn die start in huidige maand (meest relevant)
  - **Fallback:** Als geen start in maand, gebruik periode waar maand in valt
  - **Voorbeeld:** September 2025 → rode lijn op 22 sept → toont periode 15 (voor) en 16 (na)
  - **Correcte data:** Gebruikt exact start/eind datums uit database (geen berekeningen)

- ✅ **Performance Optimalisatie** - Geen grid rebuild nodig
  - **Targeted updates:** Alleen HR cijfers updaten (3 labels vs 1500+ cellen)
  - **Cache systeem:** `hr_werkdagen_cache` en `hr_cel_widgets` voor snelle lookups
  - **Crash preventie:** Direct setText pattern ipv volledige rebuild
  - **Instant feedback:** Shifts en HR cijfers direct zichtbaar zonder wachten

- ✅ **Business Rules Implementatie** - HR regels correct toegepast
  - **Max 19 dagen regel:** Per 28-dagen cyclus (rode lijn periode)
  - **Werkdag definitie:** Alleen shifts met `telt_als_werkdag=1`
  - **Beide bronnen:** Werkposten EN speciale codes ondersteund
  - **Lege cellen:** Tellen NIET als werkdag (alleen ingevulde shifts)
  - **Alle status:** Concept EN gepubliceerd beide meegeteld

**Waarom dit belangrijk is:**
- **Compliance:** Real-time inzicht in HR regels tijdens roosteren
- **Preventie:** Waarschuwing VOORDAT planning gepubliceerd wordt
- **Efficiency:** Planner ziet direct impact van wijzigingen
- **Transparantie:** Duidelijke feedback over werkdagen per periode

**Voor Planners:**
1. Open Planning Editor → zie 2 nieuwe kolommen naast teamlid namen
2. Vul shifts in → cijfers updaten automatisch
3. Rode cel? → die specifieke periode heeft > 19 werkdagen
4. Hover over cijfer → zie details (periode nummer, datums, X/19 dagen)

**Technische Details:**
- Locatie: `gui/widgets/planner_grid_kalender.py`
- Nieuwe methodes: `get_relevante_rode_lijn_periodes()`, `tel_gewerkte_dagen()`, `update_hr_cijfers_voor_gebruiker()`
- Grid shift: Datum kolommen nu vanaf kolom 3 (was kolom 1)
- Query: LEFT JOIN met beide werkposten + speciale_codes voor werkdag check

### Versie 0.6.18 (27 Oktober 2025)
- ✅ **Grid Kalender Refactoring** - Code quality verbetering via DRY principe
  - **170 regels duplicatie** tussen Planner en Teamlid kalenders geëlimineerd
  - **Template Method Pattern:** Base class met override hooks voor customisatie
  - **7 Methods naar base class:** `load_rode_lijnen()`, `update_title()`, `on_jaar_changed()`, `on_maand_changed()`, `open_filter_dialog()`, `create_header()`
  - **Code reductie:** -54 regels netto (-2.3% van codebase)
  - **Maintainability:** Bug fixes in 1 plek = beide widgets automatisch gefixed
  - **Extensibility:** Nieuwe grid widget maken? Gewoon inheriten van base class!
  - Bestanden: `grid_kalender_base.py`, `planner_grid_kalender.py`, `teamlid_grid_kalender.py`

- ✅ **Teamlid Navigatie Knoppen** - Consistent UX met Planning Editor
  - **"← Vorige Maand" en "Volgende Maand →"** buttons toegevoegd aan Mijn Planning
  - Kwam **automatisch uit refactoring** via template method pattern
  - Voorheen: alleen dropdowns (minder handig voor snelle navigatie)
  - Nu: dropdowns + navigatie buttons (consistent met Planner view)
  - Locatie: Dashboard → Mijn Planning (bovenaan kalender)

- ✅ **Mijn Planning Status Indicator** - Transparantie voor teamleden
  - **Visual feedback** over planning status per maand
  - **Geel waarschuwing:** "Planning voor [maand] is nog niet gepubliceerd" (concept)
  - **Groen bevestiging:** "Planning voor [maand]" (gepubliceerd)
  - Auto-update bij maand navigatie via PyQt signals
  - Database query: check status in planning tabel per maand
  - **Duidelijke communicatie:** Teamlid weet of lege kalender = concept of echt leeg

- ✅ **Filter Architecture Improvement** - Clean code via required overrides
  - **Template Method:** `get_initial_filter_state(user_id)` in base class
  - **Required override pattern** met `NotImplementedError` (fail-fast design)
  - **Planner view:** alle gebruikers initieel zichtbaar (return True)
  - **Teamlid view:** alleen eigen planning zichtbaar (return user_id == huidige_gebruiker_id)
  - Expliciete gedragsdefinitie per view type
  - Crash bij development time als override vergeten (niet in productie!)

**Workflow Voorbeeld - Teamlid Planning Bekijken:**
1. Teamlid: Login → Dashboard → Mijn Planning
2. **Status indicator** toont: "Planning voor november is nog niet gepubliceerd" (geel)
3. Filter: **alleen eigen rooster zichtbaar** (geen afleiding van collega's)
4. Klik "Volgende Maand →" voor december
5. **Status indicator** update automatisch: "Planning voor december" (groen)
6. Snel navigeren met nieuwe **navigatie buttons**

**Technische Highlights:**
- **Template Method Pattern** voor clean inheritance en code reuse
- **Required override pattern** voor fail-fast development
- **PyQt signals** voor gedecoupelde inter-component communicatie
- **DRY principle:** Single source of truth voor shared logic
- **Separation of concerns:** Base class vs subclass responsibilities duidelijk gescheiden

**Bug Fixes:**
- Missing import: `List` toegevoegd aan planner_grid_kalender.py
- Month navigation: Index berekening gecorrigeerd (self.maand - 1)
- Filter behavior: Meerdere iteraties naar clean architecture

**Impact:**
- **Code Quality:** -54 regels, betere maintainability, DRY principe
- **UX:** Consistent navigatie, transparantie over planning status
- **Development:** Sneller nieuwe features door template methods
- **Stability:** Fail-fast design voorkomt productie bugs

### Versie 0.6.17 (24 Oktober 2025)
- ✅ **Multi-Cell Selectie Systeem** - Bulk operaties voor efficiënt roosteren
  - **Selecteren:** Ctrl+Click voor individuele cellen, Shift+Click voor rechthoek selectie
  - **Visuele feedback:** Lichtblauwe overlay toont geselecteerde cellen
  - **Bulk Wissen:** Context menu "Wis Selectie" - verwijder meerdere shifts tegelijk
  - **Bulk Invullen:** Context menu "Vul Selectie In..." - vul meerdere cellen met zelfde code
  - **Bescherming:** Speciale codes (VV, Z, RX, KD) blijven behouden tenzij expliciet
  - **Notities:** Notities blijven ALTIJD behouden bij bulk operaties
  - **Status label:** "X cellen geselecteerd (ESC om te wissen)" - druk ESC om selectie te wissen
  - **Tijdsbesparing:** 80% minder clicks voor repetitieve taken!

- ✅ **Gepubliceerde Maand Bescherming** - Voorkom onbedoelde wijzigingen
  - Planning kan niet gewijzigd worden wanneer maand gepubliceerd is
  - Duidelijke waarschuwing: "Deze maand is gepubliceerd en kan niet worden bewerkt"
  - Instructie: "Zet de maand eerst terug naar concept via de Planning Editor"
  - Bescherming voor: cel bewerken, bulk wissen, bulk invullen, week vullen, notitie bewerken

- ✅ **Status Visualisatie Verbeteringen** - Altijd zichtbare status indicator
  - **8px gekleurde rand** rond hele Planning Editor scherm
  - **Geel** (#FFE082) voor concept modus - planning nog niet zichtbaar voor teamleden
  - **Groen** (#81C784) voor gepubliceerd modus - planning zichtbaar voor teamleden
  - Altijd zichtbaar, zelfs bij scrollen

- ✅ **Planning Editor Layout Optimalisatie** - Meer ruimte voor toekomstige features
  - Info box (concept/gepubliceerd) naast maandnaam op 1 rij
  - Knoppen compacter: Auto-Genereren, Wis Maand, Publiceren op 1 rij
  - Dubbele tooltip verwijderd (staat nu alleen onderaan)
  - **2 rijen verticale ruimte gewonnen** voor toekomstige HR validatie features

**Workflow Voorbeeld - Bulk Invullen:**
1. Planner: Open Planning Editor
2. Ctrl+Click op vrijdag voor 10 medewerkers (of Shift+Click voor groot gebied)
3. Rechtsklik → "Vul Selectie In..."
4. Typ "V" (vroege dienst) → Invullen
5. Klaar! 10 shifts ingevuld in 5 seconden (voorheen 10x handmatig invoeren)

**Workflow Voorbeeld - Bulk Wissen:**
1. Selecteer weekend cellen voor meerdere medewerkers
2. Rechtsklik → "Wis Selectie (20 cellen)"
3. Bevestig (checkbox "Ook speciale codes verwijderen?" blijft UIT)
4. Klaar! Alleen shift codes verwijderd, verlof/ziekte behouden, notities intact

### Versie 0.6.16 (23 Oktober 2025)
- ✅ **Notitie naar Planner Feature**
  - Teamleden kunnen nu notities sturen naar planner
  - Menu knop "Notitie naar Planner" in Mijn Planning tab
  - Datum selectie + tekst editor voor notitie
  - Automatisch zichtbaar in planning grid bij juiste persoon
  - Groen hoekje indicator toont aanwezigheid van notitie
  - Locatie: Dashboard → Mijn Planning → "Notitie naar Planner"

- ✅ **Naam Prefix voor Notities**
  - Teamlid notities: `[Naam]: tekst` (bijv. "[Peter]: Afspraak om 14u")
  - Planner notities: `[Planner]: tekst`
  - Altijd duidelijk wie notitie heeft aangemaakt
  - Slimme logica: bestaande prefix niet overschrijven

- ✅ **Notitie Indicator Verbetering**
  - Kleur verbeterd: #17a2b8 (teal) → #00E676 (helder groen)
  - 70% beter zichtbaar voor gebruikers
  - Material Design kleur voor optimale UX

- ✅ **Database Versie Fix**
  - Upgrade script `upgrade_to_v0_6_16.py` voor versie synchronisatie
  - Documentatie over migratie best practices toegevoegd
  - Test script uitgebreid voor diagnose

**Workflow:**
1. Teamlid: Dashboard → "Notitie naar Planner"
2. Selecteer datum + schrijf notitie (bijv. "Afspraak om 14u, kan niet voor late shift")
3. Notitie wordt opgeslagen met naam prefix: `[Peter]: Afspraak om 14u, kan niet voor late shift`
4. Groen hoekje verschijnt in planning grid bij Peter op gekozen datum
5. Planner ziet notitie en kan hierop reageren

### Versie 0.6.15 (22 Oktober 2025)
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

### 🔨 HOGE PRIORITEIT (Volgende Updates)

**Code Quality Refactoring (Gepland: v0.6.18)** 🚨
- **Grid Kalender Code Cleanup** - Elimineer 170 regels code duplicatie
  - Probleem: Duplicatie tussen Planner en Teamlid kalenders
  - Oplossing: Verplaats naar base class met template method pattern
  - Impact: Betere maintainability, minder bugs, toekomstbestendig
  - Geschatte tijd: 1-1.5 uur

**Mijn Planning Verbeteringen (Gepland: v0.6.18)** 🎯
- **Navigatie Knoppen** - "← Vorige Maand" en "Volgende Maand →" buttons
  - Huidige situatie: alleen dropdowns (minder handig voor teamleden)
  - Nieuwe situatie: gelijke UX als Planning Editor
  - Komt automatisch uit code cleanup refactoring!

- **Status Indicator voor Teamleden** - Duidelijkheid over planning status
  - Probleem: Lege maand → onduidelijk of planning nog niet gepubliceerd is
  - Oplossing: Info box toont "Planning is nog niet gepubliceerd" of "Planning gepubliceerd"
  - Voorkomt: Verwarring en onnodige vragen aan planner

**Waarom deze volgorde?**
- Code cleanup eerst = nieuwe features komen gratis!
- Voorkomt nieuwe code duplicatie
- Clean code approach = toekomstbestendig

---

### 🔨 VOOR RELEASE 1.0 (December 2025)

**Typetabel Features:**
- Activeren met datum picker
- Validatie checks
- Bulk operaties

**Planning Editor:**
- ✅ Auto-generatie uit typetabel (v0.6.14)
- ✅ Concept vs Gepubliceerd (v0.6.15)
- ✅ Multi-cell selectie & bulk operaties (v0.6.17)
- Bulk operaties (copy week, paste)
- Validatie feedback met visuele indicatoren

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

## VOLLEDIGE VERSIE GESCHIEDENIS

### v0.6.29 (12 November 2025) - Notitie Indicator Teamlid View
**ISSUE-004 fix: Groene hoekje indicator voor notities in "Mijn Planning"**

**Bug Fixes:**
- **ISSUE-004: Notitie Indicator Teamlid View**
  - Probleem: Teamleden zagen geen visuele indicator voor notities (alleen tooltips)
  - Planner view had wel indicator sinds v0.6.16 (groen hoekje rechts boven)
  - Oplossing: Groene border indicator toegevoegd aan teamlid view
  - Privacy: Alleen eigen notities krijgen indicator (collega notities verborgen)
  - Implementatie: `teamlid_grid_kalender.py:create_shift_cel()`
  - Check: `gebruiker_id == huidige_gebruiker_id` voor privacy filtering
  - Styling: `border-top: 3px solid #00E676` + `border-right: 3px solid #00E676`
  - Kleur: #00E676 (Material Design bright green - consistent met planner view)

**UX Observatie - Badge Refresh (NOT A BUG):**
- Planner schrijft notitie via "Notitie naar Planner" → badge refresht niet direct
- Badge query werkt correct, dashboard refresht alleen niet automatisch
- Beslissing: GEEN FIX NODIG
- Redenering: Auteur weet wat hij schreef, badge is voor "een week later" of collega-planners
- Status: Working as intended - badge refresht bij login

**Technisch:**
- `gui/widgets/teamlid_grid_kalender.py`: Notitie indicator logic
- Geen database wijzigingen (gebruikt bestaande notitie veld)

**Impact:**
- ✓ Teamleden zien groene hoekje op dagen met eigen notities
- ✓ Consistent met planner view indicator
- ✓ Privacy behouden (alleen eigen notities zichtbaar)

---

### v0.6.28 (12 November 2025) - Werkpost Validatie UI + ISSUE-005 Fix
**Werkpost validation user feedback + HR overlay persistence fix**

**Nieuwe Features:**
- **Werkpost Validatie - UI Integratie**
  - Backend was al compleet (constraint_checker.py), UI integration ontbrak
  - Probleem: Violation constructor kreeg niet alle vereiste velden
  - Fix: gebruiker_id en datum_range parameters toegevoegd (constraint_checker.py:1622-1629)
  - Friendly name: 'werkpost_onbekend' → 'Onbekende werkpost koppeling'
  - Visual feedback: Gele overlay (WARNING severity), tooltip, HR Summary box
  - Testing: test_werkpost_validation.py met 2 scenarios (positief + negatief)
  - Result: Planners zien waarschuwing bij verkeerde werkpost toewijzing

**Bug Fixes:**
- **ISSUE-005: HR Overlay Verdwijnt Bij Cel Klik**
  - Probleem: HR violation overlay (rood/geel) verdween bij cel klik voor edit
  - Root cause: QLineEdit editor had hard-coded `background-color: white`
  - Oplossing (8 code changes):
    - Added `overlay_kleur: Optional[str]` attribute to EditableLabel (line 55)
    - Modified editor stylesheet to use overlay color if present (lines 84-96)
    - Updated overlay in 4 methods: create_editable_cel(), update_bemannings_status_voor_datum(), refresh_data(), apply_selection_styling()
  - Discovered: HR overlay ontbrak in update flows (alleen verlof overlay was applied)
  - Result: HR overlay blijft zichtbaar tijdens cel edit, verlof overlays ook behouden

- **ISSUE-002: Kolom Sortering op Achternaam**
  - Probleem: Kolommen gesorteerd op volledige_naam (voornaam eerst)
  - Database uitbreiding: voornaam + achternaam kolommen toegevoegd
  - Parse logica: laatste woord = voornaam, rest = achternaam
  - SQL sortering: `ORDER BY is_reserve, achternaam, voornaam`
  - Migratie: upgrade_to_v0_6_28.py
  - Impact: Vaste mensen eerst (op achternaam), dan reserves (op achternaam)

**Code Quality:**
- **Unicode Cleanup:** 13x → vervangen met -> in Python code (ASCII safe voor Windows)
- **Code Documentatie:** Section comments in constraint_checker.py en planning_validator_service.py

**Technisch:**
- `services/constraint_checker.py`: Werkpost validation fix
- `gui/widgets/planner_grid_kalender.py`: HR overlay persistence (8 changes)
- `database/connection.py`: voornaam + achternaam kolommen
- `migrations/upgrade_to_v0_6_28.py`: Database schema update

**Database:**
- Schema wijziging: voornaam TEXT, achternaam TEXT kolommen in gebruikers tabel
- Migratie vereist: upgrade_to_v0_6_28.py

**Impact:**
- ✓ Werkpost validatie volledig geïntegreerd (backend + UI)
- ✓ HR overlay blijft zichtbaar tijdens edit (constante feedback)
- ✓ Teamleden correct gesorteerd (achternaam alfabetisch)
- ✓ Vaste mensen en reserves gescheiden in lijst

---

### v0.6.26 (4 November 2025) - HR Validatie Systeem Compleet
**Pre-publicatie validatie + UX fixes + segmented validation + automated testing**

**Nieuwe Features:**
- **HR Validatie Waarschuwing bij Publicatie**
  - Pre-publicatie validatie check in `planning_editor_screen.py:publiceer_planning()`
  - Alle gebruikers worden gevalideerd (alle 6 HR checks)
  - Bij violations: QMessageBox.warning met samenvatting (ALLE gebruikers)
  - Message: "Bent u zeker dat u wil publiceren met planningsfouten?"
  - Gebruiker kan kiezen: Annuleren (No) of Toch publiceren (Yes)
  - Flexibiliteit: Kan publiceren ondanks violations (bijv. bij bugs in validatie)
  - Workflow: Valideer → Bekijk violations → Publiceer (met of zonder fixes)

**UX Verbeteringen:**
- **ISSUE-007: Real-time Validation Disabled**
  - Probleem 1: Popup bij elke cel edit (zeer irritant bij meerdere edits)
  - Probleem 2: Ghost violations op verkeerde datums (week ervoor)
  - Root cause: `validate_shift()` datum mapping probleem
  - Oplossing: Real-time validation volledig uitgeschakeld
  - Workflow: Gebruiker vult rustig in → klikt "Valideer Planning" → bekijkt summary
  - Impact: Geen interruptions meer, accurate validation via knop

- **Tooltip Fix: HTML Tags Verwijderd**
  - Probleem: `<b>`, `<br>` tags zichtbaar in hover tooltips
  - Oplossing: `get_hr_tooltip()` gebruikt plain text met `\n`
  - Impact: Tooltips correct leesbaar

**Bug Fixes:**
- **BUG-005: Segmented RX Check**
  - Probleem: Weekend-only planning (za/zo ingevuld) triggerde valse RX violations
  - User scenario: "ik vul enkel zaterdag en zondag in voor een ganse maand, en ik krijg al violations"
  - Oplossing: `_segment_planning_op_lege_cellen()` in constraint_checker
  - Gedrag: Planning wordt gesplitst in continue segmenten bij lege cellen
  - Impact: Partial planning mogelijk tijdens invullen (geen valse violations meer)

- **BUG-005b: Datum Gap Detection**
  - Probleem: Database heeft geen records voor lege dagen (ma-vr), alleen za/zo leek continu
  - User scenario: "RX op 27/09, weekends t/m 21/10, violations op RX en werkdagen"
  - Oplossing: Detectie van datum gaps `(p.datum - vorige_datum).days > 1`
  - Impact: Lege werkdagen tussen weekends triggeren geen violations meer
  - Toegepast op: RX check + werkdagen reeks check

- **ISSUE-006: HR Summary Box Always Visible + ALLE Violations**
  - Probleem: Box verborgen bij geen violations, tekst afgeknipt, max 5 per gebruiker
  - User feedback: "mag die er altijd staan. summary box moet alle fouten geven, dus niet enkel de top 5"
  - Oplossing: QLabel wrapped in QScrollArea (200px max hoogte)
  - Gedrag: Altijd zichtbaar met "Geen HR violations gevonden" message
  - Volledig: Toont ALLE violations van ALLE gebruikers (geen limits meer)
  - Scroll: Automatisch bij lange violation lijsten

**Automated Testing Suite:**
- **test_constraint_scenarios.py** (13 tests) ✅ 100% PASSED
  - RX/CX gap distinction (alleen RX telt, niet CX)
  - 7 vs 8 werkdagen reeks (boundary test)
  - RX breekt werkdagen reeks (reset_12u_rust flag)
  - VV telt als werkdag (telt in cyclus, breekt reeks NIET)
  - 48u vs 56u week (boundary test)
  - 12u rust cross-month (nacht 31/10 → vroeg 1/11)
  - RX gap cross-year (dec 2024 → jan 2025)
  - 19 vs 20 dagen cyclus (boundary test)

- **test_segmented_rx_check.py** (3 tests) ✅ 100% PASSED
  - Weekend only → 0 violations
  - Complete planning → correct validation
  - Gap > 7 within segment → correct violation

- **test_datum_gap_segmentation.py** (1 test) ✅ 100% PASSED
  - User scenario: RX 27/09, weekends only, RX 21/10
  - Geen valse violations op lege werkdagen

**Technisch:**
- `services/constraint_checker.py`: Segmented validation logic
  - `_segment_planning_op_lege_cellen()` - Split planning in segmenten
  - `_check_rx_gap_in_segment()` - Check per segment
  - Datum gap detection in werkdagen reeks check
- `gui/widgets/planner_grid_kalender.py`: HR summary box QScrollArea wrapper
- Test scripts: 900+ lines test code, 16 scenarios

**Database:**
- Geen schema wijzigingen

**Impact:**
- ✓ Informed decision: Waarschuwing bij publicatie met violations (geen blokkering)
- ✓ Flexibiliteit: Kan publiceren ondanks violations (bijv. bij bugs in validatie)
- ✓ Transparantie: Toont ALLE violations van ALLE gebruikers (geen limits)
- ✓ Geen irritante popups meer bij cel edits (rustig kunnen werken)
- ✓ Accurate validation zonder ghost violations (alleen via knop)
- ✓ Partial planning invulling mogelijk (weekend/weekday eerst)
- ✓ Geen valse violations meer bij geleidelijke planning invoer
- ✓ HR summary altijd zichtbaar met scroll (consistent UI feedback)
- ✓ 16 automated tests voor regression detection

### v0.6.23 (30 Oktober 2025) - HR Regels Vervaldatum Vereenvoudigd
**Planner-vriendelijke interface: dag + maand → één datum veld**

**Nieuwe Features:**
- **HR Regels Service** (`services/hr_regels_service.py`)
  - `get_verlof_vervaldatum(jaar)` - Dynamic lookup vervaldatum uit database
  - `get_actieve_regel(naam)` - Generic helper voor alle HR regels
  - Format: "DD-MM" string → date object
  - Fallback: 1 mei (Nederlandse standaard)

- **Vereenvoudigde HR Regel**
  - Was: 2 aparte regels ("dag" + "maand")
  - Nu: 1 regel "Vervaldatum overgedragen verlof"
  - Weergave: "1 mei" (leesbaar, niet "dag=1 maand=5")
  - Eenheid: "datum" (nieuw type)

- **Intuïtieve Edit Dialog**
  - Conditionale UI: detecteert eenheid type
  - Datum type: dag/maand dropdowns (1-31, januari-december)
  - Numeriek type: spinbox (bestaand gedrag)
  - Parse/format helpers bidirectioneel

- **Dynamische Code Lookup**
  - Vervang hardcoded `datetime(year, 5, 1)`
  - Gebruik HRRegelsService in verlof_saldo_widget
  - Warning text dynamisch: "vervalt op {datum} {jaar}"

**Migratie:**
- `upgrade_to_v0_6_23.py` - Automatische conversie oude regels
- Zoekt dag/maand regels, combineert tot "DD-MM" format
- Archiveert oude regels (is_actief=0)
- Default: 1 mei voor nieuwe/ontbrekende regels

**UI Verbeteringen:**
- HR Regels Beheer: leesbare datums ("1 mei" vs "01-05")
- Nederlandse maandnamen in edit dialog
- Historiek toont ook geformateerde datums

**Database:**
- Schema wijziging: nieuwe datum format voor HR regels
- MIN_DB_VERSION = 0.6.23

**Voordelen:**
- ✓ Planner-vriendelijk: duidelijke datum weergave
- ✓ Flexibel: vervaldatum aanpasbaar per organisatie
- ✓ Consistent: code gebruikt database (niet hardcoded)
- ✓ Schaalbaar: datum type herbruikbaar voor andere regels

### v0.6.22 (30 Oktober 2025) - Verlof Saldo Berekening Fixes
**Twee belangrijke correcties in verlof saldo berekening**

**Bug Fixes:**
- **Fix #1: Kalenderdagen i.p.v. werkdagen**
  - Probleem: 13-22 november telde als 7 dagen (alleen ma-vr)
  - Oplossing: Nu 10 dagen (inclusief weekends)
  - Consistent met aanvraag scherm
  - Berekening: `(eind - start).days + 1`

- **Fix #2: Planning als source of truth**
  - Probleem: Handmatige wijzigingen (VV → CX/RX) niet meegenomen in saldo
  - Oplossing: Saldo berekening nu uit planning tabel ipv verlof_aanvragen
  - Voorbeeld: 10 dagen aangevraagd, 2 handmatig gewijzigd → saldo toont 8 dagen ✓

**Gedragswijziging:**
- Saldo telt alle planning records (concept + gepubliceerd)
- Planner ziet direct saldo impact bij concept wijzigingen
- Gedocumenteerd in DESIGN DECISIONS voor gebruikersfeedback

**Technisch:**
- `services/verlof_saldo_service.py`: `_bereken_werkdagen()` vereenvoudigd
- 3 functies aangepast: `get_saldo()`, `sync_saldo_naar_database()`, `get_alle_saldi()`
- Test scripts: `test_verlof_berekening.py`, `test_planning_saldo.py`

**Database:**
- Geen schema wijzigingen

### v0.6.21 (29 Oktober 2025) - Kritische Shift Codes Systeem
**Selectieve bemanningscontrole - planner bepaalt welke shifts kritiek zijn**

**Nieuwe Features:**
- **Kritische Shifts Markering**
  - Nieuwe kolom in shift_codes tabel: is_kritisch (BOOLEAN)
  - Grid editor: "Kritisch" kolom met 12 checkboxes per werkpost
  - Visual indicator: ⚠ symbool in overzicht bij kritische shifts
  - Planner controle: zelf bepalen welke shifts validatie nodig hebben

- **Selectieve Bemanningscontrole**
  - Alleen kritische shifts worden gevalideerd in overlay
  - Praktisch: vroege dienst kritisch, late dienst niet kritisch mogelijk
  - Excel rapport labels: "Bemannings Validatie (Kritische Shifts)"

- **UX Verbeteringen**
  - Oranje overlay voor dubbele shifts (was geel)
  - Betere contrast vs weekend kleuren (#FFA726)
  - Atomic publicatie bugfix (Excel + database synchroon)

**Technisch:**
- Database kolom: `shift_codes.is_kritisch` BOOLEAN DEFAULT 0
- Migration script: `upgrade_to_v0_6_21.py`
- Service filter: `bemannings_controle_service.py` (WHERE is_kritisch = 1)
- Dialog update: `shift_codes_grid_dialog.py` (nieuwe kolom)
- Excel labels: `export_service.py` (kritische shifts vermelding)

**Database:**
- Schema wijziging: shift_codes.is_kritisch kolom
- MIN_DB_VERSION = 0.6.21

### v0.6.20 (28 Oktober 2025) - Bemannings Controle System
**Intelligente shift staffing validatie met real-time feedback**

**Nieuwe Features:**
- **Bemannings Controle Service**
  - Automatische detectie verwachte bemanning via shift_codes tabel
  - Status systeem: groen (volledig), geel (dubbel), rood (onvolledig)
  - Geen database wijzigingen nodig (gebruikt bestaande structuur)

- **Datum Header Overlay Visualisatie**
  - Lichtgroene overlay: volledig bemand (40% opacity #81C784)
  - Gele overlay: dubbele code gebruikt (40% opacity #FFE082)
  - Rode overlay: ontbrekende code(s) (40% opacity #E57373)
  - Overlay ALLEEN op datum headers (cellen vrij voor toekomstige HR fout indicators)
  - Tooltips per dag: toon welke codes wel/niet ingevuld met gebruikersnamen
  - Real-time updates: overlay updatet direct na cel wijziging
  - Weekend/feestdag kleuren blijven behouden onder overlay

- **Dubbele Code Waarschuwing**
  - Warning dialog bij dubbele shift_code toewijzing
  - Keuze: Annuleren of Toch opslaan
  - Context aware: correct voor opleidingen/dubbele bemanning

- **Excel Validatie Rapport**
  - Tweede sheet: "Validatie Rapport" tab in Excel export
  - Dag-per-dag overzicht: Datum, Dag, Status, Ontbrekende Shifts
  - Kleurcodering: groen/geel/rood backgrounds
  - Samenvatting sectie met totaal cijfers

- **Publicatie Flow met Validatie**
  - Samenvatting dialog toont bemannings status voor publiceren
  - Preview cijfers: "✓ Volledig: X dagen, ⚠ Dubbel: Y dagen, ✗ Onvolledig: Z dagen"
  - Validatie rapport automatisch toegevoegd aan Excel

**Technisch:**
- Nieuwe service: `services/bemannings_controle_service.py`
- Grid updates: `gui/widgets/planner_grid_kalender.py` (overlay + tooltips)
- Excel uitbreiding: `services/export_service.py` (validatie rapport sheet)
- Planning editor: `gui/screens/planning_editor_screen.py` (validatie in publicatie flow)
- Qt CSS overlay techniek: `qlineargradient()` syntax voor semi-transparante achtergronden

**Database:**
- Geen schema wijzigingen (hergebruikt shift_codes voor configuratie)

### v0.6.15 (22 Oktober 2025) - Planning Editor Priority 1 Compleet
**Planning Status Management + Bug Fixes**

**Nieuwe Features:**
- **Concept vs Gepubliceerd Toggle**
  - Planning status management per maand
  - Concept: verborgen voor teamleden (geel info box)
  - Gepubliceerd: zichtbaar voor teamleden (groen info box)
  - Planners kunnen altijd wijzigen (ook na publicatie)
  - Bevestiging dialogs bij status wijziging

**Verbeteringen:**
- Feestdag specifieke error messages
- Filter blijft behouden bij maand navigatie
- Rode lijnen auto-regeneratie na config wijziging
- Naam kolom verbreed naar 280px (28+ karakters)
- Multiscreen setup fix: window blijft op primair scherm
- Dark mode: grid tekst leesbaarheid fix (zwart op licht)
- About dialog fix voor .exe builds

**Database:**
- Geen schema wijzigingen (gebruikt bestaande planning.status kolom)

### v0.6.14 (22 Oktober 2025) - Werkpost Koppeling & Slimme Auto-Generatie
**Many-to-many werkpost systeem met intelligente planning generatie**

**Nieuwe Features:**
- **Werkpost Koppeling**
  - Grid interface: gebruikers × werkposten met checkboxes
  - Multi-post support met prioriteit (1 = eerste keuze, 2 = fallback)
  - Filters: zoek op naam + toon reserves
  - Locatie: Beheer → Werkpost Koppeling

- **Slimme Auto-Generatie uit Typetabel**
  - Typetabel "V" → werkpost → shift_code "7101" lookup
  - Multi-post fallback mechanisme
  - Beschermt verlof, ziekte en handmatige wijzigingen
  - Preview met statistieken

**Database:**
- Nieuwe tabel: `gebruiker_werkposten` (many-to-many met prioriteit)
- Index: `idx_gebruiker_werkposten_gebruiker`
- Migratie: `migratie_gebruiker_werkposten.py`

**Bug Fixes:**
- Nieuwe werkpost: reset_12u standaard UIT

### v0.6.13 (21 Oktober 2025) - Database Versie Beheer Systeem
**Centrale versie configuratie en compatibiliteit checks**

**Nieuwe Features:**
- **Database Versie Tracking**
  - Centrale versie in `config.py` (APP_VERSION + MIN_DB_VERSION)
  - Automatische compatibiliteit check bij app start
  - Versie weergave op loginscherm en About dialog
  - Bij incompatibiliteit: duidelijke error met upgrade instructies

- **UI Verbetering**
  - Verlof Saldo Beheer: terug knop rechtsboven (consistent)
  - Jaar selector in toolbar (logischer)

**Database:**
- Nieuwe tabel: `db_metadata` (version tracking)
- Upgrade script: `upgrade_to_v0_6_13.py`

### v0.6.12 (21 Oktober 2025) - Theme Per Gebruiker
**Individuele theme voorkeuren**

**Nieuwe Features:**
- Theme voorkeur per gebruiker (ipv globaal)
- Opgeslagen in database (niet JSON bestand)
- Login scherm blijft altijd light mode
- Theme onthouden tussen sessies

**Database:**
- Nieuwe kolom: `gebruikers.theme_voorkeur` (TEXT, default 'light')
- Migratie: `migratie_theme_per_gebruiker.py`
- Oude `theme_preference.json` verwijderd

### v0.6.11 (21 Oktober 2025) - Shift Voorkeuren Systeem
**Individuele shift prioriteiten per gebruiker**

**Nieuwe Features:**
- Shift voorkeuren scherm (Dashboard → Persoonlijk → Mijn Voorkeuren)
- Prioriteit selectie: Vroeg, Laat, Nacht, Typetabel (1-4)
- Auto-save functionaliteit
- Real-time validatie (voorkomt dubbele prioriteiten)
- Live preview van volgorde

**Database:**
- Nieuwe kolom: `gebruikers.shift_voorkeuren` (TEXT, JSON format)
- Migratie: `migratie_shift_voorkeuren.py`

**Toekomstig Gebruik:**
- Input voor automatische planning generatie

### v0.6.10 (20 Oktober 2025) - Verlof & KD Saldo Systeem
**Complete saldo tracking voor verlof en kompensatiedagen**

**Nieuwe Features:**
- **Admin: Verlof & KD Saldo Beheer**
  - Jaarlijks contingent per gebruiker
  - Overdracht management (VV vervalt 1 mei, KD max 35 dagen)
  - "Nieuw Jaar Aanmaken" bulk functie
  - Opmerking veld voor notities

- **Teamlid: Saldo Widget**
  - Read-only weergave eigen saldo (VV en KD)
  - Specifieke overdracht labels
  - Warning countdown voor vervaldatum (1 mei)
  - Auto-refresh na aanvraag

- **Planner: Type Selectie**
  - VerlofTypeDialog: kies VV of KD bij goedkeuren
  - Real-time saldo preview (rood/geel/groen)
  - Auto-sync saldo na goedkeuring

**Database:**
- Nieuwe tabel: `verlof_saldo` (per gebruiker/jaar)
- Nieuwe kolom: `verlof_aanvragen.toegekende_code_term`
- Nieuwe speciale code: KD met term 'kompensatiedag'
- Migratie: `migratie_verlof_saldo.py`

**UI/UX:**
- Label: "Tot:" → "t/m:" (duidelijkheid)
- Compactere formulier layouts

### v0.6.9 (20 Oktober 2025) - Dark Mode & Rode Lijnen Visualisatie
**Theme systeem en HR cyclus visualisatie**

**Nieuwe Features:**
- **Dark Mode (Nachtmodus)**
  - ThemeToggleWidget in dashboard (zon/maan iconen)
  - Dashboard rebuild strategie
  - Theme persistence via JSON
  - Alleen beschikbaar in dashboard

- **Rode Lijnen Visualisatie**
  - Visuele weergave 28-daagse HR cycli in grid kalenders
  - Rode linker border (4px) markeert periode start
  - Tooltip met periode nummer
  - Beide Planner en Teamlid kalenders

**Bug Fixes:**
- Calendar widget kolom weergave (zondag afgesneden)
- Feestdagen laden voor 3 jaren (vorig, huidig, volgend)
- Extended loading voor buffer dagen

**Bekende Beperkingen:**
- QCalendarWidget behouden light mode styling (Qt limitation)

### v0.6.8 (19 Oktober 2025) - Rode Lijnen Config & UX Verbeteringen
**Versioned configuratie systeem en gebruiksvriendelijkheid**

**Nieuwe Features:**
- **Rode Lijnen Config Beheer**
  - Versioned configuratie (actief_vanaf, actief_tot)
  - UI scherm voor beheer
  - Historiek bijhouden
  - Data ensure service gebruikt config

- **UX Verbeteringen**
  - Auto-maximize na login
  - Window centreren bij logout
  - Tab-based handleiding (F1 shortcut)
  - Filter state preservation bij maand navigatie
  - Codes sidebar in Mijn Planning scherm

- **Keyboard Shortcuts**
  - F1: Globale handleiding
  - F2: Shift codes helper (was F1)

- **Historiek Standaard Zichtbaar**
  - HR Regels beheer
  - Rode Lijnen beheer

**Database:**
- Nieuwe tabel: `rode_lijnen_config`
- Migratie: `migratie_rode_lijnen_config.py`

### v0.6.7 (19 Oktober 2025) - Term-based Systeem voor Speciale Codes
**Bescherming systeemcodes tegen verwijdering**

**Nieuwe Features:**
- **Term-based Systeem**
  - Systeemcodes beschermd via termen
  - Codes hernoembaar (VV → VL), termen blijven
  - TermCodeService met cache
  - Visual indicators voor systeemcodes

- **Verplichte Termen:**
  - verlof, zondagrust, zaterdagrust, ziek, arbeidsduurverkorting

**Database:**
- Nieuwe kolom: `speciale_codes.term` (TEXT, nullable)
- UNIQUE index op term
- Migratie: `migratie_systeem_termen.py`

**Bugfix:**
- Verlofcode kan niet meer per ongeluk verwijderd worden

### v0.6.6 (18 Oktober 2025) - Typetabel Beheer Systeem
**Versioned typetabel systeem met volledige CRUD**

**Nieuwe Features:**
- **Versioned Systeem**
  - Status lifecycle: Concept → Actief → Archief
  - TypetabelBeheerScreen met overzicht
  - Grid editor voor patronen (Weken × 7 dagen)
  - Nieuwe typetabel concept maken (1-52 weken)
  - Kopiëren functionaliteit
  - Verwijderen concept
  - Bekijken actieve typetabel (read-only)

- **Multi-post Support**
  - Shift codes met post nummers (V1, V2, L1, L2, etc.)

**Database:**
- Nieuwe tabellen: `typetabel_versies`, `typetabel_data`
- Oude tabel: `typetabel_old_backup` (na migratie)
- Migratie: `migrate_typetabel_versioned.py`

**Openstaande:**
- Activatie flow (volgende versie)

### v0.6.5 (16 Oktober 2025) - Planning Editor & Verlof Beheer
**Kernschermen voor planning en verlof**

**Nieuwe Features:**
- PlanningEditorScreen met editable grid
- Cel editing met keyboard navigatie
- Context menu voor snelle acties
- VerlofAanvragenScreen (teamleden)
- VerlofGoedkeuringScreen (planners)

**Nieuwe Bestanden:**
- `gui/screens/planning_editor_screen.py`
- `gui/screens/verlof_aanvragen_screen.py`
- `gui/screens/verlof_goedkeuring_screen.py`

### v0.6.4 (15 Oktober 2025) - Shift Codes Systeem
**Complete shift codes implementatie met multi-team support**

**Nieuwe Features:**
- **Werkposten Systeem**
  - Team-specifieke shift codes
  - 3×4 grid editor (dag_type × shift_type)
  - Eigenschappen op werkpost niveau
  - Soft delete

- **Speciale Codes**
  - Globale codes (VV, RX, DA, Z, etc.)
  - CRUD dialogs

- **Tijd Parsing**
  - Flexibele formaten: 6-14, 06:00-14:00, 06:30-14:30
  - Halve uren en kwartieren support
  - Over middernacht support

**Database:**
- Nieuwe tabellen: `werkposten`, `shift_codes`, `speciale_codes`, `planning`
- Migratie: `migrate_shift_codes.py`

**Bug Fixes:**
- Admin in kalenders gefilterd
- Button width uniform (96px)

### v0.6.3 (14 Oktober 2025) - Feestdagen Verbetering & Grid Kalenders
**Feestdagen systeem herwerking en herbruikbare kalender widgets**

**Nieuwe Features:**
- **Feestdagen Systeem**
  - `is_variabel` flag (0=vast, 1=variabel/extra)
  - Paasberekening algoritme (Computus)
  - Beveiliging vaste feestdagen (niet bewerkbaar)
  - Variabele feestdagen correctie mogelijk

- **Grid Kalender Widgets**
  - GridKalenderBase (base class)
  - PlannerGridKalender (planner view)
  - TeamlidGridKalender (teamlid view met filter)
  - FilterDialog voor gebruiker selectie
  - Verlof/DA/VD overlays
  - Feestdagen markering

**Database:**
- Nieuwe kolom: `feestdagen.is_variabel`
- Migratie check: PRAGMA table_info

### v0.6.2 (12 Oktober 2025) - Gebruikersbeheer & Centrale Styling
**Styling systeem en gebruikersbeheer stabiliteit**

**Nieuwe Features:**
- **Centrale Styling** (`gui/styles.py`)
  - Colors, Fonts, Dimensions classes
  - Styles class met pre-built methods
  - TableConfig helper
  - Consistent over hele applicatie

- **Gebruikersbeheer Stabiliteit**
  - Crashproof
  - Table layouts stabiel

**Bug Fixes:**
- Unicode karakters → Plain tekst
- Table layout crashes opgelost
- Button tekst overlap gefixt

### v0.6.1 (11 Oktober 2025) - Gebruikersbeheer Complete
**Volledige gebruikersbeheer implementatie**

**Nieuwe Features:**
- UUID systeem voor permanente gebruikers-ID's
- Timestamp tracking (aangemaakt, gedeactiveerd, laatste login)
- Reserve functionaliteit
- Startweek typedienst instellen
- Wachtwoord reset
- Zoeken op naam/gebruikersnaam
- Soft delete (deactiveren ipv verwijderen)

**Database:**
- Nieuwe kolommen: `gebruiker_uuid`, timestamps, `is_reserve`

### v0.6.0 (10 Oktober 2025) - Dashboard & Login
**Basis applicatie framework**

**Nieuwe Features:**
- Login systeem met bcrypt encryptie
- Rol-gebaseerde toegang (planner/teamlid)
- Dashboard met tabs
- Menu systeem
- About dialog
- Wachtwoord wijzigen functionaliteit
- Auto-generatie feestdagen
- Auto-generatie rode lijnen

**Database Redesign:**
- Volledige schema herwerking
- Foreign keys enabled
- Row factory voor dict access
- Seed data functions

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
- 📋 **HR Validatie Systeem** - Design compleet (zie `HR_VALIDATIE_SYSTEEM_DESIGN.md`)
  - 6 HR regels: 12u rust, 50u/week, 19 dagen/cyclus, 7 dagen tussen RX/CX, 7 werkdagen reeks, max weekends
  - Real-time rode overlay + tooltips
  - Pre-publicatie validatie rapport
  - Typetabel pre-activatie check
  - Target: v0.6.25 (34-46 uur implementatie)
- 🔨 Export functionaliteit naar Excel

### Q1 2026 - Testing
**Beta testing met eindgebruikers**

### Q2 2026 - Roll-out
**Productie release**

---

## BEKENDE BEPERKINGEN & TOEKOMSTIGE FEATURES

### Emergency Access (Lage Prioriteit)
**Probleem:** Als de enige planner zijn wachtwoord vergeet EN het admin account is inactief of wachtwoord vergeten, is er geen toegang meer tot het systeem.

**Geplande oplossing:**
- Emergency reset script (`emergency_reset.py`) voor wachtwoord reset
- Kan uitgevoerd worden met directe database toegang
- Logging van alle reset acties (audit trail)
- Gebruik: `python emergency_reset.py --user admin --reset-password`

**Huidige workaround:**
- Direct database wijzigen via SQLite browser
- Contact IT support voor database toegang

### Overige Beperkingen (v0.6.17)
- Geen automatische backup functionaliteit (handmatig data/ folder backuppen aanbevolen)
- Geen multi-tenant support (één database per organisatie)
- Thema wijzigingen alleen in dashboard (niet in alle schermen)

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
*Voor recente development sessies: zie DEV_NOTES.md*
*Voor historische sessies: zie DEV_NOTES_ARCHIVE.md*

*Laatste update: 10 November 2025*
*Versie: 0.6.26.2*