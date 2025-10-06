PROJECT STATUS & ROADMAP
========================

VOLTOOID:
---------
✅ Project structuur opgezet (MVC patroon)
✅ Database volledig ontworpen en geïmplementeerd
   - Alle tabellen: gebruikers, posten, shifts, verlof, HR regels, etc.
   - Seed functie met initiële data (admin, interventie post, typetabel)
   - UUID systeem voor gebruikers (unieke permanente identificatie)
   - Timestamps: aangemaakt_op, gedeactiveerd_op, laatste_login
   - Planning maanden tabel voor publicatie tracking
   - Speciale codes: VV, VD, DA, RX, CX, Z, RDS, TCR, T
   - HR regels: 12u rust, 50u/week, 19 dagen/28d, 7 dagen tussen RX
   - Typediensttabel: 6-weken patroon voor roterend rooster
   - Rode lijnen: 28-dagen cycli voor arbeidsduur validatie (100 periodes)
   - Database migratie systeem opgezet

✅ Centrale styling systeem (gui/styles.py)
   - Colors, Fonts, Dimensions classes
   - Pre-built Styles voor alle widget types
   - TableConfig helper voor consistente tabellen
   - Alle schermen gebruiken centrale styling
   - Makkelijk aanpasbaar vanaf 1 locatie

✅ Login systeem
   - Wachtwoord hashing (bcrypt)
   - Rol-gebaseerde toegang (planner/teamlid)
   - Gecentreerde interface met centrale styling
   - Laatste login timestamp tracking
   - Actief/inactief account validatie
   - Admin credentials: gebruikersnaam 'admin', wachtwoord 'admin'

✅ Dashboard
   - 3 tabs: Beheer, Persoonlijk, Instellingen
   - Verschillende menu voor planner vs teamlid
   - Signal/slot navigatie systeem
   - Centrale styling toegepast

✅ Gebruikersbeheer scherm (gui/screens/gebruikersbeheer_screen.py)
   - Teamleden toevoegen/bewerken met UUID generatie
   - Gebruikersnaam formaat: ABC1234 (3 letters + 4 cijfers, auto-uppercase)
   - Startweek typedienst instellen (week 1-6)
   - Reserve checkbox (disable automatisch startweek)
   - Wachtwoord beheer (optioneel bij bewerken)
   - Actief/inactief toggle met timestamps
   - Zoekfunctionaliteit op naam/gebruikersnaam
   - Validatie: unieke gebruikersnaam, min 4 chars wachtwoord
   - Aanmaakdatum tracking

✅ Feestdagen beheer scherm (Instellingen)
   - Overzicht per jaar met dd-mm-yyyy formaat
   - Automatische Paasberekening (Computus algoritme)
   - Variabele feestdagen automatisch gegenereerd
   - Extra feestdagen toevoegen/bewerken/verwijderen
   - Auto-generatie bij jaar selectie
   - Geen handmatige invoer meer nodig
   - Centrale styling toegepast

✅ Auto-generatie service (services/data_ensure_service.py)
   - Automatische feestdagen genereren bij nieuw jaar
   - Paasberekening voor variabele datums
   - Automatisch rode lijnen uitbreiden wanneer nodig
   - "Lazy initialization" patroon

TODO - PRIORITEIT HOOG:
-----------------------
📋 HR Regels scherm (gui/screens/hr_regels_screen.py)
   - Configureerbare waardes (12u rust, 50u/week, etc.)
   - Historisch bijhouden van wijzigingen met timestamps
   - Actieve regel per type tracken

📋 Shift Codes & Posten scherm (gui/screens/shift_codes_screen.py)
   - Posten toevoegen/beheren
   - Shift codes per post configureren
   - Voor uitbreiding naar andere teams
   - Start/eind tijden, duur uren
   - Weekdag/zaterdag/zondag flags

📋 Rode Lijnen scherm (gui/screens/rode_lijnen_screen.py)
   - Overzicht komende periodes (28-dagen cycli)
   - Readonly weergave (automatisch gegenereerd)
   - Visuele timeline van periodes
   - Huidige periode highlighten

📋 Jaarovergang & Cleanup scherm (gui/screens/jaarovergang_screen.py)
   - Handmatige cleanup knop in Instellingen
   - Toon gebruikers inactief > huidige datum - 2 maanden
   - Preview wat verwijderd wordt
   - Archiveer planning ouder dan N-2 jaar naar Excel/PDF
   - Hard delete functie voor oude data
   - Bevestigingsdialoog met overzicht

TODO - PRIORITEIT MIDDEL:
-------------------------
📋 Planning Editor (gui/screens/planning_editor_screen.py)
   - Kalender grid per maand
   - Multi-maand view (vorige/huidige/volgende)
   - Shift codes invoeren per persoon/dag
   - Rode lijnen visualisatie in kalender
   - Genereer uit typetabel functionaliteit
   - T (reserve) vervangen door echte shifts
   - Concept vs Gepubliceerd status
   - Bewerkbaar check: max 2 maanden terug
   - Read-only voor oudere maanden

📋 Validatie Service (services/validation_service.py)
   - 12u rust check (met reset voor VV/DA/VD)
   - 50u/week limiet
   - 19 gewerkte dagen/28d (rode lijn)
   - Max 7 dagen tussen RX
   - Max 7 werkdagen achter elkaar
   - Realtime validatie feedback in grid
   - Visuele indicatoren (rood/geel/groen)

📋 Planning Service (services/planning_service.py)
   - Genereer planning uit typetabel
   - Vertaal V/L/N naar juiste shift codes (7101-7901)
   - Datum → shift code logika (weekdag/zaterdag/RX detectie)
   - RX/CX detectie via feestdagen tabel
   - Startweek offset berekening per gebruiker

📋 Export Service (services/export_service.py)
   - Publiceer naar HR: Excel export per maand
   - Status change: concept → gepubliceerd
   - Archief functie: Excel/PDF per jaar
   - Template-based exports
   - Opslaan in /exports/ folder

📋 Verlof Aanvraag scherm (gui/screens/verlof_aanvraag_screen.py)
   - Teamlid: verlof aanvragen/intrekken
   - Overzicht eigen verlof (status: pending/goedgekeurd/geweigerd)
   - Kalender interface voor datum selectie
   - Aantal dagen berekening

📋 Verlof Goedkeuring scherm (gui/screens/verlof_goedkeuring_screen.py)
   - Planner: overzicht alle aanvragen
   - Goedkeuren/weigeren functionaliteit
   - Impact op planning zichtbaar
   - Filter per status/gebruiker

📋 Voorkeuren scherm (gui/screens/voorkeuren_screen.py)
   - Shift voorkeuren (1e/2e/3e keuze: vroeg/laat/nacht/mix)
   - Medische beperkingen (geen nachten, geen weekends)
   - Opmerkingen veld
   - Per gebruiker opslaan

TODO - PRIORITEIT LAAG:
-----------------------
📋 Team Planning Overzicht (read-only voor teamleden)
📋 Typediensttabel beheer scherm (voor wijzigingen aan 6-weken patroon)
📋 Rapportage/Statistieken (aantal nachten, weekends, verdeling)
📋 AI Planning Suggesties (toekomst)

OPTIMALISATIE BIJ CONVERSIE NAAR .EXE:
--------------------------------------
Bij de finale oplevering van dit project voorzien we een conversie van de Python-code 
naar een uitvoerbaar .exe-bestand. Gezien het feit dat deze .exe zal worden uitgevoerd 
vanaf een netwerkschijf, streven we ernaar om de bestandsgrootte zo klein mogelijk te 
houden om latency en laadtijden te minimaliseren.

Om dit te bereiken zullen we:
- PyInstaller gebruiken met optimale settings (--onefile, --windowed)
- Overbodige modules en packages excluden via exclude-list
- UPX compressie toepassen voor kleinere executable
- Alleen essentiële PyQt6 modules bundelen
- Virtual environment met minimale dependencies
- Database en exports folder relatief aan .exe locatie
- Mogelijk werken met externe .dll-bestanden om functionaliteit modulair te laden
- De build configureren met focus op minimale footprint en maximale efficiëntie
- Testing op netwerkschijf voor latency en performance validatie

Deze optimalisatie is essentieel om de performantie van het programma te garanderen 
in een netwerkomgeving.

TECHNISCHE ARCHITECTUUR:
------------------------
Database: SQLite
   - Locatie: data/planning.db
   - Foreign keys enabled
   - Row factory voor dict access
   - UUID voor gebruikers als permanente ID
   - Timestamps voor audit trails
   - Migratie systeem voor schema updates

GUI Framework: PyQt6
   - Signal/Slot voor navigatie
   - QStackedWidget voor scherm wisseling
   - Centrale styling via gui/styles.py (Colors, Fonts, Dimensions, Styles)
   - Consistente UI across alle schermen
   - Unicode emoji's vermeden (Windows compatibility)
   - TableConfig helper voor tabellen

Services Laag:
   - Scheiding business logic van GUI
   - Herbruikbare validatie/planning functies
   - Database abstractie
   - Auto-generatie services voor feestdagen en rode lijnen
   - Export/archivering services

Models:
   - Dataclasses voor entities (toekomstig)
   - Type safety

Styling Systeem:
   - Centrale kleuren palette (Colors class)
   - Font configuratie (Fonts class)
   - Dimensies en spacing (Dimensions class)
   - Pre-built styles (Styles class met methods)
   - Herbruikbare componenten (TableConfig)

SHIFT CODES SYSTEEM:
-------------------
Interventie Post:
- Weekdag: 7101 (V), 7201 (L), 7301 (N)
- Zaterdag: 7401 (V), 7501 (L), 7601 (N)
- RX: 7701 (V), 7801 (L), 7901 (N)

Speciale Codes:
- VV: Verlof (telt als gewerkte dag, reset 12u)
- VD: Vrij van dienst (telt als gewerkte dag, reset 12u)
- DA: Arbeidsduurverkorting (telt als gewerkte dag, reset 12u)
- RX: Zondagsrust (telt NIET als gewerkte dag, breekt reeks)
- CX: Zaterdagsrust (telt NIET als gewerkte dag, breekt reeks)
- Z: Ziek (telt NIET als gewerkte dag, reset 12u, breekt reeks)
- RDS: Roadshow/Meeting (10:00-18:00, telt als gewerkte dag)
- TCR: Postkennis opleiding (variabele tijden, telt als gewerkte dag)
- T: Reserve/Thuis (in typetabel, vervangen bij planning)

TYPEDIENSTTABEL:
---------------
- 6-weken roterend patroon
- Medewerkers starten bij verschillende weken (verschoven via startweek_typedienst)
- Bevat V/L/N/RX/CX/T codes
- Dient als template voor planning generatie
- Reserves volgen GEEN typetabel (handmatig plannen)

HR REGELS:
---------
1. Min 12u rust tussen shifts (VV/DA/VD reset deze regel)
2. Max 50u per week (zondag 00:00 - zondag 23:59)
3. Max 19 gewerkte dagen per 28-dagen cyclus (rode lijn)
4. Max 7 kalenderdagen tussen RX/CX
5. Max 7 werkdagen achter elkaar (RX/CX breken reeks)

RESERVES SYSTEEM:
----------------
- is_reserve flag in gebruikers tabel
- Volgen GEEN typetabel (handmatig plannen)
- startweek_typedienst = NULL voor reserves
- Wel HR regels van toepassing
- Kunnen inloggen en verlof vragen
- Planner ziet hun verlof voor beschikbaarheid

DATA RETENTIE & CLEANUP:
------------------------
- Bewerkbaar: Huidige maand + 2 maanden terug
- Read-only: Oudere maanden (kunnen wel bekeken worden)
- Cleanup: Per jaar, handmatig via Jaarovergang scherm
- Archivering: N-2 jaar (bijv. in 2026: archiveer 2024)
- Export: Excel/PDF voor gearchiveerde jaren
- Gebruikers: Hard delete als > 2 maanden inactief bij cleanup

TEAM SETUP:
-----------
Huidige config: 1 team (Interventie)
Toekomst: Uitbreidbaar naar meerdere teams met eigen shift codes

BEKENDE ISSUES & OPLOSSINGEN:
-----------------------------
- PyQt6 6.9.1 op Windows: Unicode arrows/emoji's in QPushButton veroorzaken crashes
  Oplossing: Gebruik gewone tekst in buttons (gedaan in centrale styling)
- Database connecties: Gebruik context managers voor proper cleanup
- Router pattern: Geef method door (self.terug) niet object (self)
- Schema mismatches: Altijd migratie scripts maken bij database wijzigingen
- SQLite crashes: Memory violation bij ontbrekende kolommen → graceful error handling toevoegen

BELANGRIJKE CREDENTIALS:
------------------------
- Admin login: gebruikersnaam 'admin', wachtwoord 'admin'
- Eerste keer inloggen: database wordt automatisch aangemaakt met seed data