# gui/dialogs/handleiding_dialog.py
"""
Handleiding Dialog
Toont gebruikershandleiding voor Planning Tool
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextBrowser, QPushButton,
                             QHBoxLayout, QTabWidget)
from PyQt6.QtGui import QFont
from gui.styles import Styles, Colors, Fonts, Dimensions
import markdown


class HandleidingDialog(QDialog):
    """Dialog met handleiding informatie in tabs"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Planning Tool - Handleiding")
        self.setModal(True)
        self.resize(1000, 750)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Tab widget voor verschillende secties
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER_LIGHT};
                background-color: white;
            }}
            QTabBar::tab {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_PRIMARY};
                padding: 10px 20px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.PRIMARY};
                color: white;
            }}
        """)

        # Tab 1: Eerste Gebruik
        eerste_gebruik = self.create_text_browser()
        eerste_gebruik.setHtml(self.load_eerste_gebruik())
        tabs.addTab(eerste_gebruik, "Eerste Gebruik")

        # Tab 2: Voor Planners
        planner = self.create_text_browser()
        planner.setHtml(self.load_planner_handleiding())
        tabs.addTab(planner, "Voor Planners")

        # Tab 3: Voor Teamleden
        teamlid = self.create_text_browser()
        teamlid.setHtml(self.load_teamlid_handleiding())
        tabs.addTab(teamlid, "Voor Teamleden")

        layout.addWidget(tabs)

        # Sluit knop
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Sluiten")
        close_btn.setStyleSheet(Styles.button_primary())
        close_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)  # type: ignore
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def create_text_browser(self) -> QTextBrowser:
        """Maak een geconfigureerde text browser"""
        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setOpenLinks(True)  # Enable internal links
        browser.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        return browser

    def load_eerste_gebruik(self) -> str:
        """Laad Eerste Gebruik sectie"""
        md_content = """
# Welkom bij de Planning Tool

**Versie:** 0.6.16

Deze Planning Tool helpt teams met het plannen van diensten, beheren van verlofaanvragen,
en valideren van roosters volgens HR-regels.

---

## Sneltoetsen

| Toets | Functie |
|-------|---------|
| **F1** | Deze handleiding openen (werkt in alle schermen) |

**Tip:** Gebruik de theme toggle (☀ ● ☾) in het dashboard header om te wisselen tussen Light en Dark Mode.

---

## Rollen en Rechten

### Planner

**Volledige controle over planning:**
- Planning maken en wijzigen voor alle teamleden
- Verlofaanvragen goedkeuren of afwijzen
- Gebruikers beheren (toevoegen, bewerken, deactiveren)
- Shift codes en werkposten configureren
- HR-regels en instellingen aanpassen
- Typetabellen beheren

### Teamlid

**Persoonlijke planning beheer:**
- Eigen planning bekijken
- Verlof aanvragen
- Notities naar planner sturen (bijv. "Afspraak 14u - liefst late shift")
- Voorkeuren instellen
- Wachtwoord wijzigen

---

## Belangrijke Concepten

### Typetabel (Diensttabel)

Een **typetabel** is een herhalend patroon van diensten dat zich automatisch herhaalt.

**Kenmerken:**
- Lengte: 1 tot 52 weken
- Elke gebruiker heeft een **startweek** (1 t/m N)
- Startweek bepaalt waar iemand in het patroon begint
- Gebruikt voor automatische roostergeneratie

**Statussen:**
- **CONCEPT** - In bewerking, nog niet actief
- **ACTIEF** - Wordt gebruikt voor roostering (slechts 1 kan actief zijn)
- **ARCHIEF** - Oude versie, alleen-lezen

### Shift Codes

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
- `6-14` wordt automatisch `06:00-14:00`
- `06:00-14:00` volledige notatie
- `14:15-22:45` met kwartieren

#### 2. Speciale Codes (Globaal)
Codes die voor iedereen gelden.

**Systeem codes** (beschermd):
- `VV` - Verlof (code aanpasbaar, functie niet)
- `RX` - Zondagsrust
- `CX` - Zaterdagrust
- `Z` - Ziek
- `DA` - Arbeidsduurverkorting

Deze codes hebben een `[SYSTEEM]` label en kunnen niet verwijderd worden.

### HR Regels

Het systeem controleert **automatisch** of roosters voldoen aan HR-afspraken:

| Regel | Beschrijving | Default |
|-------|--------------|---------|
| **Rust tussen diensten** | Minimum aantal uren rust | 12 uur |
| **Max uren per week** | Maximum werkuren | 50 uur |
| **Max werkdagen cyclus** | Max werkdagen per rode lijn | 19 dagen |
| **Max dagen tussen rust** | Max dagen tussen RX/CX | 7 dagen |
| **Max opeenvolgende werkdagen** | Max aantal dagen achter elkaar | 7 dagen |

**Let op:** Default regels zijn VOORBEELDEN. Stem deze af met HR!

### Rode Lijnen

**Rode lijnen** zijn HR-cycli (standaard 28 dagen) die gebruikt worden om werkdagen te tellen.
Het systeem genereert deze automatisch.

### Feestdagen

Belgische feestdagen worden automatisch gegenereerd per jaar:
- Vaste feestdagen (Nieuwjaar, Nationale feestdag, Kerstmis)
- Variabele feestdagen (Pasen, Hemelvaart, Pinksteren)

---

## Tips voor Starters

- Druk op **F1** in elk scherm voor deze handleiding
- Gebruik de tabs hierboven voor specifieke instructies (Planner/Teamlid)
- Filter op werkpost in kalenderschermen voor overzicht
- Planning status: Concept > Gepubliceerd > Gesloten
        """

        return self.convert_markdown_to_html(md_content)

    def load_planner_handleiding(self) -> str:
        """Laad Planner handleiding"""
        md_content = """
# Handleiding voor Planners

Deze sectie bevat instructies voor planners en beheerders.

---

## Planning Maken

1. Ga naar **Planning → Planning Editor**
2. Selecteer een werkpost in het filter
3. Klik op een cel in de kalender
4. Selecteer een shift code uit de lijst
5. Planning verschijnt met kleur van de shift

**Planning status:**
- **CONCEPT** - Nog niet zichtbaar voor teamleden
- **GEPUBLICEERD** - Zichtbaar en definitief

**Notities bekijken:**

Teamleden kunnen notities achterlaten voor specifieke datums.
Je kunt deze bekijken en beantwoorden:

1. **Notitie herkennen:**
   - **Groen hoekje** rechtsboven in cel = notitie aanwezig
   - Hover voor tooltip met notitie tekst

2. **Notitie bekijken/bewerken:**
   - Rechtermuisklik op cel → "Notitie toevoegen/bewerken"
   - Lees, beantwoord of verwijder notitie
   - Notities krijgen automatisch prefix `[Planner]:`

3. **Notitie van teamlid:**
   - Prefix toont wie notitie maakte (bijv. `[Peter]: Afspraak om 14u`)
   - Je kunt hierop reageren of planning aanpassen

---

## Verlof Goedkeuren

1. Ga naar **Planning → Verlof Goedkeuring**
2. Zie lijst met openstaande aanvragen
3. Klik **Goedkeuren** of **Afwijzen**
4. Bij goedkeuring wordt automatisch verlofcode in planning gezet
5. Medewerker krijgt bericht van beslissing

---

## Gebruikers Beheren

### Nieuwe gebruiker toevoegen

1. Ga naar **Beheer → Gebruikersbeheer**
2. Klik **Nieuwe Gebruiker**
3. Vul gegevens in:
   - Naam en gebruikersnaam
   - Rol (Planner of Teamlid)
   - Is reserve? (voor flexpool)
   - Startweek typedienst (1 t/m N)
4. Klik **Opslaan**

### Gebruiker bewerken

- Klik op gebruiker in lijst
- Pas gegevens aan
- Klik **Wijzigingen Opslaan**

### Gebruiker deactiveren

- Klik **Deactiveer** (wordt niet verwijderd, alleen inactief)
- Kan later weer geactiveerd worden

---

## Shift Codes Beheren

1. Ga naar **Beheer → Shift Codes & Werkposten**

### Werkpost toevoegen

1. Klik **Nieuwe Werkpost**
2. Geef naam (bijv. "Interventie")
3. Vul 3x4 grid in (Vroeg/Laat/Nacht × Ma-Zo/Weekend/Feestdag)
4. Gebruik flexibele tijd notatie: `6-14`, `06:00-14:00`, `14:15-22:45`

### Speciale code aanpassen

- Codes met `[SYSTEEM]` label kunnen niet verwijderd
- Wel de code zelf aanpassen (VV naar VL)
- Beschrijving en kleur wijzigen

---

## Typetabel Beheren

1. Ga naar **Beheer → Typetabel Beheer**

### Nieuwe typetabel maken

1. Klik **Nieuw Concept**
2. Geef naam en beschrijving
3. Kies aantal weken (1-52)
4. Klik **Aanmaken**

### Typetabel bewerken

1. Klik **Bewerk** bij concept
2. Vul grid in met shift codes
3. Wijzig cellen naar wens
4. Klik **Opslaan**

### Typetabel kopiëren

1. Klik **Kopieer** om variant te maken
2. Geef nieuwe naam
3. Pas aan naar behoefte

### Typetabel activeren

1. Klik **Activeer** bij concept
2. Oude actieve typetabel wordt gearchiveerd
3. Nieuwe wordt actief voor roostering

---

## HR Regels Aanpassen

1. Ga naar **Instellingen → HR Regels Beheer**
2. Zie actieve regels + historiek
3. Klik **Wijzig** bij een regel
4. Pas waarde aan
5. Kies **Actief vanaf** datum
6. Klik **Nieuwe Versie Opslaan**

**Let op:** Als je een datum in het verleden kiest, moet planning opnieuw gevalideerd worden!

**Historiek:**
- Bij wijzigen wordt nieuwe versie aangemaakt
- Oude regel wordt gearchiveerd met einddatum
- Planning gebruikt correcte regel op basis van datum

---

## Rode Lijnen Configureren

1. Ga naar **Instellingen → Rode Lijnen Beheer**
2. Zie huidige configuratie
3. Klik **Wijzig**
4. Pas start datum of interval aan
5. Kies **Actief vanaf** datum
6. Klik **Nieuwe Versie Opslaan**

**Gebruik:**
- Interval van 28 dagen is standaard Nederlandse HR-cyclus
- Kan aangepast naar andere intervallen (bijv. 21 dagen)
- Start datum bepaalt wanneer eerste rode lijn begint

---

## Feestdagen Beheren

1. Ga naar **Instellingen → Feestdagen**
2. Feestdagen worden automatisch gegenereerd per jaar
3. **Nieuwe feestdag toevoegen:**
   - Klik **Nieuwe Feestdag**
   - Selecteer datum
   - Geef naam
   - Markeer als zondagsrust indien nodig
4. **Feestdag bewerken:**
   - Klik op feestdag in lijst
   - Pas gegevens aan
   - Klik **Opslaan**

---

## Tips voor Planners

- Gebruik historiek in HR Regels en Rode Lijnen voor audit trail
- Check feestdagen elk jaar of ze kloppen
- Kopieer typetabellen voor varianten (winter/zomer)
- Filter op werkpost in kalenders voor overzicht
- Planning automatisch gesloten na einddatum
        """

        return self.convert_markdown_to_html(md_content)

    def load_teamlid_handleiding(self) -> str:
        """Laad Teamlid handleiding"""
        md_content = """
# Handleiding voor Teamleden

Deze sectie bevat instructies voor teamleden.

---

## Eigen Planning Bekijken

1. Ga naar **Planning → Mijn Planning**
2. Zie je rooster per maand
3. Gebruik knoppen om door maanden te navigeren
4. Kleuren tonen verschillende shift types

**Planning lezen:**
- Elke kleur is een ander type dienst
- Klik op een dienst om details te zien
- Check regelmatig voor wijzigingen

---

## Verlof Aanvragen

1. Ga naar **Planning → Verlof Aanvragen**
2. Klik **Nieuwe Aanvraag**
3. Selecteer datum met kalender
4. Kies type:
   - **Verlof (VV)** - Regulier verlof
   - **Zondagsrust (RX)** - Extra rustdag
   - **Zaterdagrust (CX)** - Extra rustdag
   - Andere types afhankelijk van configuratie
5. Voeg eventueel opmerking toe
6. Klik **Aanvraag Indienen**
7. Wacht op goedkeuring van planner

**Status:**
- **IN_BEHANDELING** - Wachten op planner
- **GOEDGEKEURD** - Geaccepteerd
- **AFGEKEURD** - Niet goedgekeurd

**Tips:**
- Vraag verlof zo vroeg mogelijk aan
- Voeg context toe in opmerkingen
- Check status regelmatig

---

## Notitie naar Planner Sturen

**Wanneer te gebruiken:**
- Je hebt een afspraak en wil een bepaalde shift
- Je hebt een voorkeur voor een specifieke datum
- Je wil de planner informeren over een bijzondere situatie

**Hoe te gebruiken:**
1. Ga naar **Mijn Planning → Notitie naar Planner**
2. Selecteer de **datum** waar je notitie over gaat
3. Schrijf je **notitie** in het tekstveld
4. Klik **Opslaan**

**Voorbeelden:**
- "Afspraak om 14u, kan niet voor late shift"
- "Verzoek voor vroege shift ivm vervoer"
- "Arts afspraak 10u - liefst vrij of late dienst"

**Wat gebeurt er:**
- Je notitie wordt opgeslagen met jouw naam
- Een **groen hoekje** verschijnt in de planning bij jouw naam
- De planner ziet je notitie en kan hierop reageren

**Let op:**
- Houd notities kort en duidelijk
- Dit is geen garantie voor een specifieke shift
- Voor officiële verlofaanvragen: gebruik "Verlof Aanvragen"

---

## Wachtwoord Wijzigen

1. Ga naar **Persoonlijk → Wijzig Wachtwoord**
2. Voer oud wachtwoord in
3. Voer nieuw wachtwoord in (2x)
4. Klik **Wijzig Wachtwoord**

**Wachtwoord tips:**
- Kies een sterk wachtwoord
- Verander regelmatig
- Deel nooit met anderen

---

## Veelgestelde Vragen

**Q: Mijn verlof is niet goedgekeurd, waarom niet?**
A: Neem contact op met je planner voor uitleg. Mogelijk conflicteert het met andere planning.

**Q: Kan ik mijn eigen planning wijzigen?**
A: Nee, alleen planners kunnen planning wijzigen. Je kunt wel verlof aanvragen.

**Q: Hoe ver vooruit kan ik planning zien?**
A: Afhankelijk van wat je planner heeft gepubliceerd. Meestal enkele maanden vooruit.

**Q: Mijn wachtwoord werkt niet meer**
A: Neem contact op met je planner. Alleen planners kunnen wachtwoorden resetten.

**Q: Ik zie mijn nieuwe verlof niet in planning**
A: Verlof verschijnt pas in planning nadat de planner het heeft goedgekeurd.

---

## Tips voor Teamleden

- Check je planning wekelijks
- Vraag verlof vroeg aan
- Voeg context toe bij verlofaanvragen
- Wijzig je wachtwoord regelmatig
- Gebruik F1 voor hulp
        """

        return self.convert_markdown_to_html(md_content)

    def convert_markdown_to_html(self, md_content: str) -> str:
        """Converteer markdown naar HTML met styling"""
        # Converteer markdown naar HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code']
        )

        # Wrap in HTML met styling
        full_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    padding: 20px;
                    max-width: 900px;
                }}
                h1 {{
                    color: #2C3E50;
                    border-bottom: 3px solid #3498DB;
                    padding-bottom: 10px;
                    margin-top: 20px;
                }}
                h2 {{
                    color: #34495E;
                    border-bottom: 2px solid #BDC3C7;
                    padding-bottom: 8px;
                    margin-top: 30px;
                }}
                h3 {{
                    color: #7F8C8D;
                    margin-top: 20px;
                }}
                h4 {{
                    color: #95A5A6;
                    margin-top: 15px;
                }}
                p {{
                    margin: 10px 0;
                }}
                ul, ol {{
                    margin: 10px 0 10px 25px;
                }}
                li {{
                    margin-bottom: 8px;
                }}
                code {{
                    background-color: #ECF0F1;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                    color: #C0392B;
                }}
                pre {{
                    background-color: #ECF0F1;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                    color: #2C3E50;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 15px 0;
                }}
                th {{
                    background-color: #3498DB;
                    color: white;
                    padding: 10px;
                    text-align: left;
                    border: 1px solid #2980B9;
                }}
                td {{
                    padding: 8px;
                    border: 1px solid #BDC3C7;
                }}
                tr:nth-child(even) {{
                    background-color: #ECF0F1;
                }}
                blockquote {{
                    border-left: 4px solid #3498DB;
                    padding-left: 15px;
                    margin: 15px 0;
                    color: #7F8C8D;
                    font-style: italic;
                }}
                hr {{
                    border: none;
                    border-top: 2px solid #BDC3C7;
                    margin: 30px 0;
                }}
                strong {{
                    color: #2C3E50;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        return full_html
