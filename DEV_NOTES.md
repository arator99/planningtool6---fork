# DEV NOTES
Persoonlijke Notities & Observaties

## INHOUDSOPGAVE
1. [Snelle Notities](#snelle-notities)
2. [Bugs & Issues](#bugs--issues)
3. [Verbeterpunten](#verbeterpunten)
4. [Ideeën](#ideeën)
5. [Vragen voor AI Sessie](#vragen-voor-ai-sessie)

---

## SNELLE NOTITIES

*Dump hier alles wat je opmerkt tijdens gebruik/testen. Sorteer later.*

**[08/10/2025] - Bugs opgelost**
- ✅ Teamleden kunnen geen feestdagen meer aanpassen (Instellingen tab verwijderd voor teamleden)
- ✅ Alle gebruikers kunnen nu hun wachtwoord wijzigen via "Mijn Planning" tab
- Wachtwoord wijzig functionaliteit volledig werkend met bcrypt encryption


---

## BUGS & ISSUES

*Dingen die niet werken zoals verwacht*

### 🔴 Kritiek
*Blokkeert gebruik of kan data corrumperen*



### 🟡 Belangrijk  
*Moet opgelost worden voor release*

**~~Teamleden kunnen feestdagen aanpassen~~** ✅ OPGELOST [08/10/2025]
- ~~Ze hebben toegang tot Instellingen → Feestdagen~~
- ~~Dit zou alleen voor planners moeten zijn~~
- Opgemerkt: [07/10/2025]
- **Oplossing:** Instellingen tab volledig verwijderd voor teamleden. Alleen planners zien: Beheer, Persoonlijk, Instellingen. Teamleden zien alleen: Mijn Planning.

**~~Gebruikers kunnen hun wachtwoord niet zelf resetten/wijzigen~~** ✅ OPGELOST [08/10/2025]
- ~~Gebruikers hebben op hun tabblad geen toegang/knop tot hun profiel~~
- ~~Dit zou wel nodig zijn om hun wachtwoord te kunnen wijzigen~~
- Opgemerkt: [08/10/2025]
- **Oplossing:** 
  - "Wijzig Wachtwoord" knop toegevoegd aan "Mijn Planning" tab voor ALLE gebruikers (planners + teamleden)
  - WachtwoordWijzigenDialog geïmplementeerd met volledige validatie
  - Verificatie van huidig wachtwoord met bcrypt
  - Minimaal 4 karakters voor nieuw wachtwoord
  - Bevestiging dat nieuwe wachtwoorden overeenkomen
  - Proper error handling voor database operaties

**Admin account verschijnt in kalender weergaves**
- Admin account (rol='planner') wordt getoond in gebruikerslijst van kalenders
- Dit is geen werknemer en moet uitgefilterd worden
- Opgemerkt: [09/10/2025]
- **Locatie:** `gui/widgets/grid_kalender_base.py` → `load_gebruikers()` methode
- **Oplossing:** Extra conditie `AND rol != 'planner'` toevoegen aan query

### 🟢 Klein
*Irritant maar niet urgent*
**Filter state wordt gereset bij maand navigatie**
- Wanneer gebruiker filtert op specifieke persoon en dan naar andere maand navigeert, verdwijnt de filter
- Filter selectie wordt niet onthouden tussen maand wijzigingen
- Opgemerkt: [09/10/2025]
- **Locatie:** `gui/screens/mijn_planning_screen.py` + `gui/widgets/teamlid_grid_kalender.py`
- **Oplossing:** 
  - Filter state opslaan in `MijnPlanningScreen` als instance attribute
  - Bij maand wijziging: oude filter doorgeven aan nieuwe kalender instance
  - FilterDialog moet huidige selectie pre-selecteren bij openen
- **Impact:** Quality of Life verbetering, niet kritiek voor functionaliteit


---

## VERBETERPUNTEN

*Dingen die werken, maar beter kunnen*

### UI/UX


### Performance


### Code Quality


---

## IDEEËN

*Features of verbeteringen voor de toekomst*

### Korte termijn (voor 1.0)
** logboek toevoegen om na te kijken wie er laatst zaak x heeft gewijzigd, of gebruiker Y heeft uitgeschakeld?"**

### Lange termijn (na 1.0)


---

## VRAGEN VOOR AI SESSIE

*Dingen om te bespreken/vragen tijdens volgende programmeer sessie*

- [ ] 
- [ ] 
- [ ] 

---

## RECENTE OPLOSSINGEN & LEARNINGS

**[08/10/2025] - Crash bij Wachtwoord Dialog**
- **Probleem:** AttributeError: `Dimensions.INPUT_HEIGHT` bestaat niet
- **Oorzaak:** Gebruik van niet-bestaande constante uit styles.py
- **Oplossing:** Gebruik `Dimensions.BUTTON_HEIGHT_NORMAL` voor input field heights
- **Learning:** Altijd styles.py referentie checken in DEVELOPMENT_GUIDE.md voordat je constanten gebruikt
- **Toegevoegd:** Complete styles.py referentie sectie aan DEVELOPMENT_GUIDE.md

**[08/10/2025] - Menu Button Structuur**
- **Probleem:** Oorspronkelijk design had QPushButton met nested VBox layout (known crash issue)
- **Oplossing:** QWidget container met mousePressEvent handler in plaats van QPushButton met layout
- **Learning:** Volg altijd de "Crashproof Patterns" uit DEVELOPMENT_GUIDE.md
- **Pattern:** Container widget → VBox layout → Labels, dan mousePressEvent handler toevoegen

---

## NOTATIE GUIDE

**Prioriteiten:**
- 🔴 Kritiek - moet direct opgelost
- 🟡 Belangrijk - voor release 
- 🟢 Klein - wanneer tijd is

**Checklist items:**
- `[ ]` = Nog te doen
- `[x]` = Afgehandeld
- `~~tekst~~` ✅ = Opgelost met datum

**Tip:** Dateer je notities, dan weet je later hoe lang iets al bekend is.

---

*Dit is JOUW document - de AI leest het, maar vult het niet aan.*
*Laatste update: 08/10/2025*