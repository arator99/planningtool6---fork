# PLANNING TOOL
Roostersysteem voor Self-Rostering Teams

## VERSIE INFORMATIE
**Huidige versie:** 0.6.3 (Beta)  
**Release datum:** Oktober 2025  
**Status:** In actieve ontwikkeling

---

## WAT IS NIEUW

### Versie 0.6.3 (Oktober 2025)
- ✅ Feestdagen beheer verbeterd met onderscheid vast/variabel/extra
- ✅ Automatische Paasberekening voor variabele feestdagen
- ✅ Vaste feestdagen beveiligd tegen ongewenste wijzigingen
- ✅ Database migratie systeem voor soepele updates
- ✅ Herbruikbare Grid Kalender widgets (planner & teamlid views)
- ✅ Kalender met verlof/DA/VD overlays en feestdagen markering

### Versie 0.6.2
- ✅ Centrale styling systeem geïmplementeerd
- ✅ Gebruikersbeheer stabiliteit verbeterd
- ✅ Table layouts crashproof gemaakt

### Versie 0.6.1
- ✅ Gebruikersbeheer met reserve-functionaliteit
- ✅ UUID systeem voor permanente gebruikers-ID's
- ✅ Timestamp tracking (aangemaakt, gedeactiveerd, laatste login)

### Versie 0.6.0
- ✅ Login systeem met rol-gebaseerde toegang
- ✅ Dashboard met planner/teamlid weergave
- ✅ Auto-generatie van feestdagen en rode lijnen
- ✅ Database volledig herontworpen

### Eerdere versies (0.1 - 0.5)
- Verschillende iteraties en leerprocessen
- Fundamentele architectuur beslissingen
- Proof of concepts en prototypes

---

## HUIDIGE FUNCTIONALITEIT

### ✅ VOLLEDIG OPERATIONEEL

**Inloggen & Beveiliging**
- Veilig login systeem met wachtwoord encryptie
- Rol-gebaseerde toegang (Planner vs Teamlid)
- Laatste login tracking
- Actief/inactief account beheer

**Dashboard**
- Overzichtelijk menu met 3 tabs: Beheer, Persoonlijk, Instellingen
- Verschillende menu opties voor planner en teamleden
- Snelle navigatie naar alle functionaliteiten
- About dialog met roadmap informatie

**Gebruikersbeheer** (Planners)
- Teamleden toevoegen en bewerken
- Gebruikersnaam systeem (ABC1234 formaat)
- Reserve medewerkers markeren
- Startweek typedienst instellen
- Accounts activeren/deactiveren
- Zoeken op naam of gebruikersnaam

**Feestdagen Beheer** (Planners)
- Automatische generatie Belgische feestdagen per jaar
- Slimme Paasberekening voor variabele datums
- Vaste feestdagen beschermd tegen wijzigingen
- Variabele feestdagen aanpasbaar voor correcties
- Extra feestdagen toevoegen (bijv. lokale feestdagen)
- Overzicht per jaar met type indicatie

**Automatische Data Generatie**
- Feestdagen automatisch aangemaakt bij jaar selectie
- Rode lijnen cycli automatisch uitgebreid wanneer nodig
- "Lazy loading" principe: genereer alleen wat nodig is

**Grid Kalender Widgets** (Development)
- Herbruikbare kalender componenten voor planner en teamlid views
- Filter functionaliteit per gebruiker
- Verlof/DA/VD status overlays (gekleurde achtergronden)
- Feestdagen markering (gele achtergrond)
- Shift codes weergave (7101, 7201, VV, RX, etc.)
- Test scherm beschikbaar voor ontwikkeling

---

## IN ONTWIKKELING

### 🔨 VOOR RELEASE 1.0 (December 2025)

**HR Regels Beheer**
- Configureerbare waardes (12u rust, 50u/week, etc.)
- Historisch bijhouden van wijzigingen
- Actieve regel per type tracken

**Shift Codes & Speciale Codes Beheer**
- Posten toevoegen en beheren
- Shift codes per post configureren
- Speciale codes beheren (VV, RX, TCR/SCR, etc.)
- Nieuwe speciale codes toevoegen
- Code eigenschappen instellen (telt als werkdag, reset 12u rust, breekt reeks)
- Uitbreidbaar naar meerdere teams

**Rode Lijnen Overzicht**
- Visuele weergave 28-dagen cycli
- Timeline van komende periodes
- Huidige periode gemarkeerd

**Planning Editor** ⭐ (Kern functionaliteit)
- Kalender weergave per maand
- Shift codes invoeren per persoon/dag
- Automatisch genereren uit typetabel
- Concept vs Gepubliceerd status
- Validatie met visuele feedback

**Validatie & Controles**
- Realtime HR regels checking
- Visuele indicatoren (rood/geel/groen)
- 12u rust tussen shifts
- 50u per week maximum
- 19 dagen per 28-dagen cyclus
- Maximum dagen tussen rustdagen

**Verlof Beheer**
- Teamleden: verlof aanvragen
- Planners: goedkeuren/weigeren
- Overzicht eigen verlof
- Impact op planning zichtbaar

**Export Functionaliteit**
- Publiceren naar HR (Excel)
- Archief exports (Excel/PDF)
- Maandelijkse overzichten

**Voorkeuren**
- Shift voorkeuren per medewerker
- Medische beperkingen
- Opmerkingen veld

**Jaarovergang & Cleanup**
- Preview van te verwijderen data
- Archivering planning naar Excel/PDF
- Opruimen oude gedeactiveerde gebruikers

---

## SYSTEEM VEREISTEN

**Besturingssysteem:**
- Windows 10 of nieuwer
- Netwerkschijf toegang (voor multi-user gebruik)

**Schermresolutie:**
- Minimaal 1366x768
- Aanbevolen 1920x1080 of hoger

**Geheugen:**
- Minimaal 4GB RAM
- Aanbevolen 8GB RAM

**Opslag:**
- Minimaal 100MB vrije ruimte
- Database groeit geleidelijk (±1MB per jaar data)

---

## BEKENDE ISSUES

### ✅ OPGELOST
- **Unicode karakters**: Probleem met speciale tekens in buttons is opgelost
- **Table layout crashes**: Stabiliteit van tabel weergaves verbeterd
- **Button weergave**: Tekst in buttons wordt nu correct getoond
- **Feestdagen bewerken**: Vaste feestdagen nu beschermd tegen wijzigingen
- **Database migraties**: Soepel upgrade systeem geïmplementeerd

### ⚠️ BEKEND
- **Netwerklatency**: Bij gebruik vanaf netwerkschijf kan er lichte vertraging zijn bij opstarten
- **Grote datasets**: Planning overzichten met veel data kunnen traag laden (optimalisatie gepland)

### 🔍 IN ONDERZOEK
- **Gebruikers kunnen aan het tabblad instellingen**: Zij kunnen daar de feestdagen aanpassen.

**Probleem melden?** Neem contact op met je planner of leidinggevende.

---

## GEBRUIKERSINSTRUCTIES

### Eerste Keer Inloggen
1. Start de applicatie
2. Log in met:
   - **Gebruikersnaam:** `admin`
   - **Wachtwoord:** `admin`
3. ⚠️ **Belangrijk:** Wijzig het admin wachtwoord direct na eerste login!

### Voor Planners
1. **Teamleden beheren:** Dashboard → Beheer → Gebruikersbeheer
2. **Feestdagen instellen:** Dashboard → Instellingen → Feestdagen
3. **Planning maken:** (In ontwikkeling)

### Voor Teamleden
1. **Eigen rooster bekijken:** (In ontwikkeling)
2. **Verlof aanvragen:** (In ontwikkeling)
3. **Voorkeuren instellen:** (In ontwikkeling)

---

## SHIFT CODES

### Interventie Post (Voorbeeld)

**Weekdag Diensten:**
- 7101 - Vroege dienst (V): 06:00-14:00
- 7201 - Late dienst (L): 14:00-22:00
- 7301 - Nachtdienst (N): 22:00-06:00

**Zaterdag Diensten:**
- 7401 - Vroege dienst (V): 06:00-14:00
- 7501 - Late dienst (L): 14:00-22:00
- 7601 - Nachtdienst (N): 22:00-06:00

**Zondag/Feestdag Diensten:**
- 7701 - Vroege dienst (V): 06:00-14:00
- 7801 - Late dienst (L): 14:00-22:00
- 7901 - Nachtdienst (N): 22:00-06:00

*Deze codes zijn configureerbaar per team via Shift Codes beheer*

### Speciale Codes

- **VV** - Verlof (Betaald verlof)
- **VD** - Vrij van dienst (ADV/compensatieverlof)
- **DA** - Arbeidsduurverkorting
- **RX** - Zondagsrust
- **CX** - Zaterdagsrust
- **Z** - Ziek
- **RDS** - Roadshow/Meeting
- **TCR/SCR** - Opleiding (Postkennis/Servicecentrum)
- **T** - Reserve/Thuis (wordt vervangen bij definitieve planning)

*Speciale codes zijn configureerbaar per organisatie via Speciale Codes beheer*

---

## HR REGELS

Het systeem controleert automatisch op:

1. **Minimale rust:** 12 uur tussen diensten
2. **Maximum werkuren:** 50 uur per week
3. **Maximum werkdagen:** 19 dagen per 28-dagen cyclus
4. **Rustdagen:** Maximum 7 dagen tussen RX/CX
5. **Werkdagen reeks:** Maximum 7 werkdagen achter elkaar

⚠️ Planningen die deze regels schenden worden gemarkeerd en kunnen niet gepubliceerd worden.

---

## TYPEDIENSTTABEL

Het systeem werkt met een **6-weken roterend patroon**:

- Elke medewerker heeft een startweek (1-6)
- Het patroon herhaalt zich elke 6 weken
- Automatische generatie van basis planning mogelijk
- Reserves volgen GEEN typetabel (handmatig in te plannen)

**Voorbeeld Week 1:**
- Ma: Vroeg, Di: Vroeg, Wo: Rust, Do: Laat, Vr: Laat, Za: Rust, Zo: Rust

---

## RODE LIJNEN

**Wat zijn rode lijnen?**
Rode lijnen zijn 28-dagen cycli voor het bijhouden van de arbeidsduur. Het systeem controleert automatisch dat medewerkers niet meer dan 19 gewerkte dagen per cyclus hebben.

**Werking:**
- Eerste cyclus start: 28 juli 2024
- Elke periode duurt 28 dagen
- Automatisch uitgebreid naar de toekomst
- Zichtbaar in planning overzicht (in ontwikkeling)

---

## DATA & PRIVACY

**Data opslag:**
- Alle data wordt lokaal opgeslagen in SQLite database
- Locatie: `data/planning.db`
- Automatische backup aanbevolen

**Beveiliging:**
- Wachtwoorden zijn versleuteld (bcrypt)
- Geen wachtwoorden in plain text opgeslagen
- Toegang via rol-gebaseerd systeem

**Data retentie:**
- Planning: Minimaal 2 jaar bewaren
- Oude planning: Archiveren naar Excel/PDF
- Gedeactiveerde gebruikers: Cleanup na 2 maanden inactiviteit

---

## SUPPORT & CONTACT

**Bugs of problemen melden:**
- Neem contact op met je planner of de ontwikkelaar
- Vermeld versienummer en beschrijving probleem
- Screenshots zijn welkom

**Feature requests:**
- Suggesties zijn welkom
- Bespreek met de ontwikkelaar of planner
- Roadmap wordt regelmatig bijgewerkt

**Technische documentatie:**
- Voor ontwikkelaars: zie DEVELOPMENT_GUIDE.md
- Voor eindgebruikers: dit document volstaat

---

## ROADMAP

### Release 1.0 - December 2025
**🎯 Productie-klare versie**
- ✅ Gebruikersbeheer (voltooid)
- ✅ Feestdagen beheer (voltooid)
- ✅ Grid Kalender widgets (voltooid)
- 🔨 HR Regels scherm
- 🔨 Shift Codes beheer
- 🔨 Rode Lijnen overzicht
- 🔨 Planning Editor (kern!)
- 🔨 Validatie systeem
- 🔨 Auto-generatie planning
- 🔨 Verlof aanvragen & goedkeuring
- 🔨 Voorkeuren systeem
- 🔨 Export functionaliteit
- 🔨 Jaarovergang & cleanup
- 🔨 .EXE build voor netwerkschijf

### Q1 2026 - Test & Refinement
**🧪 Beta testing met eindgebruikers**
- Uitgebreide testing met planners
- Uitgebreide testing met teamleden
- Bug fixes en stabiliteit
- Performance optimalisatie
- Gebruikersfeedback verwerken
- Training materiaal ontwikkelen
- Documentatie finaliseren

### Q2 2026 - Roll-out
**🚀 Productie release**
- Officiële release versie 1.0
- Training voor planners
- Introductie voor teamleden
- Monitoring & support
- Kleine bug fixes indien nodig

### Toekomst (Post 1.0)
**🔮 Mogelijke uitbreidingen**
- Multi-team ondersteuning uitbreiden
- Rapportages & statistieken
- AI planning suggesties (onderzoek fase)
- Notificaties systeem
- Verbeterde export opties
- Dashboard uitbreidingen

**❌ Niet gepland**
- Mobile app (zou hosting vereisen)
- Cloud-based oplossing (blijft lokaal/netwerkschijf)
- Integratie met externe HR systemen (voorlopig)

---

## CREDITS

**Ontwikkeling:**
- Project architectuur & ontwerp
- Database implementatie
- GUI ontwikkeling
- Paasberekening algoritme (Computus)
- Validatie logica

**Testing:**
- Beta testers (Q1 2026)
- Gebruikers feedback (Q1 2026)

**Gebruikte technologieën:**
- Python 3.11+
- PyQt6 (GUI framework)
- SQLite (Database)
- bcrypt (Wachtwoord encryptie)

---

## LICENTIE & COPYRIGHT

**Copyright © 2024-2025**

Dit is een tool ontwikkeld voor self-rostering teams.

**Gebruiksvoorwaarden:**
- Alleen voor intern gebruik binnen organisatie
- Geen distributie buiten organisatie
- Wijzigingen alleen door geautoriseerd personeel
- Geen garantie op functionaliteit (gebruik op eigen risico)

---

## TOEPASSINGSGEBIED

Deze tool is ontwikkeld voor **alle teams die aan self-rostering doen**, niet enkel interventie teams. Het shift codes systeem is volledig configureerbaar zodat elk team zijn eigen roostersysteem kan opzetten volgens de specifieke noden.

**Geschikt voor:**
- Elk team met self-rostering principes

**Vereisten:**
- Roterend rooster systeem (bijv. 6-weken patroon)
- HR regels voor arbeidsduur
- Shift-based werkomgeving
- Need voor verlof beheer

---

*Voor technische details en ontwikkelaar informatie, zie DEVELOPMENT_GUIDE.md*

*Laatste update: Oktober 2025*  
*Versie: 0.6.3*