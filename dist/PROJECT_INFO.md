# PLANNING TOOL
Roostersysteem voor Self-Rostering Teams

## VERSIE INFORMATIE
**Huidige versie:** 0.6.8 (Beta)
**Release datum:** Oktober 2025
**Status:** In actieve ontwikkeling - Rode Lijnen Config & UX verbeteringen

---

## WAT IS NIEUW

### Versie 0.6.8 (Oktober 2025) ⭐ NIEUW
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

### Voor bestaande databases (v0.6.5 → v0.6.6)

```bash
python migrate_typetabel_versioned.py
```

**Wat doet dit:**
- Maakt nieuwe typetabel_versies tabel
- Maakt nieuwe typetabel_data tabel
- Converteert oude data
- Behoudt backup als typetabel_old_backup

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
- 🔨 Typetabel Activatie
- 🔨 Planning Editor volledig
- 🔨 Validatie systeem
- 🔨 Export functionaliteit
- 🔨 .EXE build

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
*Laatste update: 19 Oktober 2025*
*Versie: 0.6.8*