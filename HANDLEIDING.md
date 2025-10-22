# Planning Tool - Gebruikershandleiding

**Versie:** 0.6.15
**Laatst bijgewerkt:** 22 Oktober 2025

---

## Inhoud

1. [Welkom](#welkom)
2. [Aan de slag](#aan-de-slag)
3. [Sneltoetsen](#sneltoetsen)
4. [Rollen en rechten](#rollen-en-rechten)
5. [Belangrijke concepten](#belangrijke-concepten)
6. [Veelgebruikte taken](#veelgebruikte-taken)
7. [Tips & Tricks](#tips--tricks)
8. [Veelgestelde vragen](#veelgestelde-vragen)

---

## Welkom

Welkom bij de **Planning Tool**, een roosterapplicatie speciaal ontwikkeld voor self-rostering teams. Deze tool helpt je met:

- 📅 Efficiënt plannen van diensten
- 🏖️ Beheren van verlofaanvragen
- ✅ Automatische validatie volgens HR-regels
- 📊 Overzichtelijk beheer van shift codes en werkposten
- 🔄 Historiek van planning wijzigingen

---

## Aan de slag

### Eerste keer inloggen

**Standaard login:**
- Gebruikersnaam: `admin`
- Wachtwoord: `admin`

⚠️ **Belangrijk:** Wijzig het admin wachtwoord direct na eerste login via *Persoonlijk → Wijzig Wachtwoord*

### Interface navigatie

Na inloggen zie je het **Dashboard** met verschillende tabs:

#### Voor Planners:
- **Beheer** - Typetabellen, Shift codes, Gebruikers, Verlof & KD Saldo Beheer
- **Planning** - Planning editor, Verlof goedkeuring (met VV/KD type selectie)
- **Instellingen** - HR regels, Feestdagen, Rode lijnen
- **Persoonlijk** - **Mijn Voorkeuren** (shift voorkeuren, nieuw v0.6.11), Wachtwoord wijzigen, **Dark Mode** (nieuw v0.6.12)

#### Voor Teamleden:
- **Planning** - Mijn planning bekijken, Verlof aanvragen (met saldo weergave)
- **Persoonlijk** - **Mijn Voorkeuren** (shift voorkeuren, nieuw v0.6.11), Wachtwoord wijzigen, **Dark Mode** (nieuw v0.6.12)

---

## Sneltoetsen

| Toets | Functie |
|-------|---------|
| **F1** | Deze handleiding openen (werkt in alle schermen) |

---

## Rollen en rechten

### 👨‍💼 Planner

**Volledige controle over planning:**
- Planning maken en wijzigen voor alle teamleden
- Verlofaanvragen goedkeuren of afwijzen
- Gebruikers beheren (toevoegen, bewerken, deactiveren)
- Shift codes en werkposten configureren
- HR-regels en instellingen aanpassen
- Typetabellen beheren

### 👤 Teamlid

**Persoonlijke planning beheer:**
- Eigen planning bekijken
- Verlof aanvragen (met saldo weergave)
- Shift voorkeuren instellen (v0.6.11)
- Dark mode kiezen (v0.6.12)
- Wachtwoord wijzigen

---

## Belangrijke concepten

### 🗓️ Typetabel (Diensttabel)

Een **typetabel** is een herhalend patroon van diensten dat zich automatisch herhaalt.

**Kenmerken:**
- Lengte: 1 tot 52 weken
- Elke gebruiker heeft een **startweek** (1 t/m N)
- Startweek bepaalt waar iemand in het patroon begint
- Gebruikt voor automatische roostergeneratie

**Voorbeeld:**
```
Week 1: V1, V2, V1, V2, L1, RX, RX
Week 2: V2, V1, V2, V1, L2, RX, RX
Week 3: L1, L1, L2, L2, V1, RX, RX
```

Als persoon A startweek 1 heeft en persoon B startweek 2, dan beginnen ze op een andere plek in het patroon.

**Statussen:**
- 🟡 **CONCEPT** - In bewerking, nog niet actief
- 🟢 **ACTIEF** - Wordt gebruikt voor roostering (slechts 1 kan actief zijn)
- ⚫ **ARCHIEF** - Oude versie, alleen-lezen

### 🏷️ Shift Codes

Er zijn **twee soorten** codes:

#### 1. Werkposten (Team-specifiek)
Diensten die specifiek zijn voor jouw werkpost/team.

**Voorbeelden:**
- `V1` - Vroege dienst werkpost 1 (06:00-14:00)
- `V2` - Vroege dienst werkpost 2 (06:00-14:00)
- `L1` - Late dienst werkpost 1 (14:00-22:00)
- `L2` - Late dienst werkpost 2 (14:00-22:00)

**Tijd notatie:**
Je kunt tijden flexibel invoeren:
- `6-14` → wordt automatisch `06:00-14:00`
- `06:00-14:00` → volledige notatie
- `14:15-22:45` → met kwartieren

#### 2. Speciale Codes (Globaal)
Codes die voor iedereen gelden.

**Systeem codes** (beschermd, niet verwijderbaar):
- `VV` - Verlof (code zelf kan wel aangepast, bijv. naar VL)
- `RX` - Zondagsrust
- `CX` - Zaterdagsrust
- `Z` - Ziek
- `DA` - Arbeidsduurverkorting

Deze codes hebben een `[SYSTEEM]` label en kunnen niet verwijderd worden. Je **kunt** wel de code zelf aanpassen (bijv. VV naar VL), maar de functionaliteit blijft behouden.

**Andere codes:**
- `T` - Training
- `N1`, `N2` - Nachtdiensten
- Eigen codes toevoegen naar behoefte

### ⚖️ HR Regels

Het systeem controleert **automatisch** of roosters voldoen aan HR-afspraken:

| Regel | Beschrijving | Default |
|-------|--------------|---------|
| **Rust tussen diensten** | Minimum aantal uren rust | 12 uur |
| **Max uren per week** | Maximum werkuren | 50 uur |
| **Max werkdagen cyclus** | Max werkdagen per rode lijn | 19 dagen |
| **Max dagen tussen rust** | Max dagen tussen RX/CX | 7 dagen |
| **Max opeenvolgende werkdagen** | Max aantal dagen achter elkaar | 7 dagen |

⚠️ **LET OP:** Default regels zijn **VOORBEELDEN**. Stem deze af met HR voordat je ze gebruikt!

**Historiek:**
- Bij wijzigen wordt een nieuwe versie aangemaakt
- Oude regel wordt gearchiveerd met einddatum
- Planning van voor de wijziging gebruikt oude regels
- Planning van na de wijziging gebruikt nieuwe regels

### 🔴 Rode Lijnen

**Rode lijnen** zijn HR-cycli die gebruikt worden om werkdagen te tellen.

**Configuratie:**
- **Start datum** - Eerste rode lijn datum (bijv. 28 juli 2024)
- **Interval** - Aantal dagen per cyclus (standaard 28 dagen)
- Automatische generatie van nieuwe rode lijnen
- Configureerbaar via *Instellingen → Rode Lijnen*

**Gebruik:**
Het systeem controleert hoeveel dagen je hebt gewerkt binnen een rode lijn periode en waarschuwt als je het maximum nadert.

### 🎄 Feestdagen

**Automatische generatie:**
- Belgische feestdagen worden automatisch aangemaakt per jaar
- Vaste feestdagen (Nieuwjaar, Nationale feestdag, Kerstmis, etc.)
- Variabele feestdagen (Pasen, Hemelvaart, Pinksteren - automatisch berekend)

**Beheer:**
- Planners kunnen feestdagen handmatig toevoegen of aanpassen
- Markeren als zondagsrust (dubbele betaling)

---

## Veelgebruikte taken

### Voor Planners

#### 📝 Planning maken

1. Ga naar **Planning → Planning Editor**
2. Selecteer een werkpost in het filter (bijv. "Interventie")
3. Klik op een cel in de kalender
4. Selecteer een shift code uit de lijst
5. Planning verschijnt met kleur van de shift
6. Wijzigingen opslaan

**Planning status: Concept vs Gepubliceerd**

De planning heeft twee statussen per maand:

- 🟡 **CONCEPT** (gele waarschuwing bovenaan)
  - Planning is nog in bewerking
  - Teamleden kunnen deze planning NIET zien
  - Je kunt vrijelijk experimenteren en wijzigen
  - Knop "Publiceren" verschijnt

- 🟢 **GEPUBLICEERD** (groene bevestiging bovenaan)
  - Planning is definitief en zichtbaar
  - Teamleden kunnen deze planning WEL zien
  - Je kunt ALTIJD nog wijzigen (voor zieken, last-minute wijzigingen)
  - Knop "Terug naar Concept" beschikbaar (verbergt planning weer)

**Planning publiceren:**
1. Maak planning voor een maand
2. Status is automatisch "CONCEPT"
3. Klik op **"Publiceren"** knop bovenaan
4. Bevestig in de dialog
5. Status wordt "GEPUBLICEERD" voor hele maand
6. Teamleden kunnen planning nu bekijken

**Waarom concept status?**
- Je kunt eerst plannen zonder dat teamleden alles zien
- Experimenteer met verschillende roosters
- Publiceer pas wanneer je tevreden bent
- Voorkom verwarring bij teamleden

#### ✅ Verlof goedkeuren

1. Ga naar **Planning → Verlof Goedkeuring**
2. Zie lijst met openstaande aanvragen
3. Klik **Goedkeuren** of **Afwijzen**
4. Bij goedkeuring wordt automatisch de verlofcode (VV) in planning gezet
5. Medewerker krijgt bericht van beslissing

#### 👥 Gebruikers beheren

1. Ga naar **Beheer → Gebruikersbeheer**
2. Klik **Nieuwe Gebruiker** om iemand toe te voegen
3. Vul gegevens in:
   - Naam en gebruikersnaam
   - Rol (Planner of Teamlid)
   - Is reserve? (voor flexpool)
   - Startweek typedienst (1 t/m N)
4. Klik **Opslaan**

**Gebruiker bewerken:**
- Klik op gebruiker in lijst
- Pas gegevens aan
- Klik **Wijzigingen Opslaan**

**Gebruiker deactiveren:**
- Klik **Deactiveer** (wordt niet verwijderd, alleen inactief)
- Kan later weer geactiveerd worden

#### 🏷️ Shift codes beheren

1. Ga naar **Beheer → Shift Codes & Werkposten**
2. **Werkpost toevoegen:**
   - Klik **Nieuwe Werkpost**
   - Geef naam (bijv. "Interventie")
   - Vul 3x4 grid in (Vroeg/Laat/Nacht × Ma-Zo/Weekend/Feestdag)
3. **Speciale code aanpassen:**
   - Codes met `[SYSTEEM]` label kunnen niet verwijderd
   - Wel de code zelf aanpassen (VV → VL)
   - Beschrijving en kleur wijzigen

**Tijd notatie tips:**
- Gebruik `6-14` voor snelle invoer
- Systeem vult automatisch aan naar `06:00-14:00`
- Kan ook met kwartieren: `06:15-14:30`

#### 📋 Typetabel beheren

1. Ga naar **Beheer → Typetabel Beheer**
2. **Nieuwe maken:**
   - Klik **Nieuw Concept**
   - Kies aantal weken (1-52)
   - Vul grid in met shift codes
3. **Bewerken:**
   - Klik **Bewerk** bij concept
   - Wijzig cellen naar wens
4. **Kopiëren:**
   - Klik **Kopieer** om variant te maken
   - Geef nieuwe naam
5. **Activeren:**
   - Klik **Activeer** bij concept
   - Oude actieve typetabel wordt gearchiveerd

#### ⚖️ HR Regels aanpassen

1. Ga naar **Instellingen → HR Regels Beheer**
2. Zie actieve regels + historiek
3. Klik **Wijzig** bij een regel
4. Pas waarde aan
5. Kies **Actief vanaf** datum
6. Klik **Nieuwe Versie Opslaan**

⚠️ **Let op:** Als je een datum in het verleden kiest, moet planning opnieuw gevalideerd worden!

#### 🔴 Rode Lijnen configureren

1. Ga naar **Instellingen → Rode Lijnen Beheer**
2. Zie huidige configuratie
3. Klik **Wijzig**
4. Pas start datum of interval aan
5. Kies **Actief vanaf** datum
6. Klik **Nieuwe Versie Opslaan**

**Gebruik:**
- Interval van 28 dagen is standaard Nederlandse HR-cyclus
- Kan aangepast naar andere intervallen (bijv. 21 dagen)
- Start datum bepaalt wanneer de eerste rode lijn begint

---

### Voor Teamleden

#### 📅 Eigen planning bekijken

1. Ga naar **Planning → Mijn Planning**
2. Zie je rooster per maand
3. Gebruik knoppen om door maanden te navigeren
4. Kleuren tonen verschillende shift types

**Let op:**
- Je ziet alleen **gepubliceerde** planning
- Planning in concept status (nog in bewerking) is verborgen
- Als je geen planning ziet voor een maand, is deze waarschijnlijk nog niet gepubliceerd
- Neem contact op met je planner als je denkt dat planning wel gepubliceerd zou moeten zijn

#### 🏖️ Verlof aanvragen

1. Ga naar **Planning → Verlof Aanvragen**
2. Klik **Nieuwe Aanvraag**
3. Selecteer datum met kalender
4. Kies type (Verlof, Zondagsrust, etc.)
5. Voeg eventueel opmerking toe
6. Klik **Aanvraag Indienen**
7. Wacht op goedkeuring van planner

**Status:**
- 🟡 **IN_BEHANDELING** - Wachten op planner
- 🟢 **GOEDGEKEURD** - Geaccepteerd
- 🔴 **AFGEKEURD** - Niet goedgekeurd

#### 🔐 Wachtwoord wijzigen

1. Ga naar **Persoonlijk → Wijzig Wachtwoord**
2. Voer oud wachtwoord in
3. Voer nieuw wachtwoord in (2x)
4. Klik **Wijzig Wachtwoord**

---

## Tips & Tricks

### Voor Planners

✅ **Gebruik historiek**
- HR Regels en Rode Lijnen tonen volledig historiek
- Handig voor audit trail en compliance

✅ **Planning status**
- Concept → zichtbaar alleen voor planners
- Gepubliceerd → teamleden kunnen zien
- Gesloten → automatisch na einddatum

✅ **Feestdagen automatisch**
- Systeem genereert Belgische feestdagen automatisch
- Check wel of ze kloppen voor jouw regio

✅ **Filter op werkpost**
- In kalenders: gebruik werkpost filter voor overzicht
- Voorkomt chaos bij meerdere werkposten

✅ **Kopieer typetabellen**
- Maak eerst een basis typetabel
- Kopieer voor varianten (winter/zomer)
- Scheelt veel handmatig werk

### Voor Teamleden

✅ **Verlof vroeg aanvragen**
- Hoe eerder, hoe groter de kans op goedkeuring
- Planner heeft meer tijd om te plannen

✅ **Opmerkingen toevoegen**
- Geef context bij verlofaanvraag
- Helpt planner bij beslissing

✅ **Planning regelmatig checken**
- Check je rooster wekelijks
- Let op wijzigingen

---

## Veelgestelde vragen

### Algemeen

**Q: Hoe open ik de handleiding?**
A: Druk op **F1** in elk scherm, of klik op **Handleiding** knop in dashboard.

**Q: Mijn wachtwoord werkt niet meer**
A: Neem contact op met je planner. Alleen planners kunnen wachtwoorden resetten.

**Q: Waarom zie ik bepaalde menu's niet?**
A: Menu's zijn afhankelijk van je rol. Teamleden zien minder opties dan planners.

### Voor Planners

**Q: Kan ik meerdere typetabellen actief hebben?**
A: Nee, slechts 1 typetabel kan actief zijn. Bij activeren wordt de oude gearchiveerd.

**Q: Hoe verwijder ik een shift code?**
A: Codes met `[SYSTEEM]` label kunnen niet verwijderd. Andere codes: klik **Verwijder** in Shift Codes scherm.

**Q: Verlofcode per ongeluk verwijderd, wat nu?**
A: Sinds v0.6.7 kan dit niet meer - systeemcodes zijn beschermd. Bij oudere versies: run migratie script.

**Q: HR regels wijzigen voor oude planning?**
A: Oude planning gebruikt oude regels. Kies "Actief vanaf" datum in toekomst om alleen nieuwe planning te beïnvloeden.

**Q: Hoe genereer ik feestdagen voor volgend jaar?**
A: Gebeurt automatisch zodra je dat jaar opent in een kalender scherm.

### Voor Teamleden

**Q: Mijn verlof is niet goedgekeurd, waarom niet?**
A: Neem contact op met je planner voor uitleg. Mogelijk conflicteert het met andere planning.

**Q: Kan ik mijn eigen planning wijzigen?**
A: Nee, alleen planners kunnen planning wijzigen. Je kunt wel verlof aanvragen.

**Q: Hoe ver vooruit kan ik planning zien?**
A: Afhankelijk van wat je planner heeft gepubliceerd. Meestal enkele maanden vooruit.

---

## Problemen of vragen?

Bij technische problemen of vragen over de applicatie:
- Neem contact op met je planner
- Of met je IT/systeembeheerder

**Planning Tool versie 0.6.7**
*Druk op F1 om deze handleiding te openen*
