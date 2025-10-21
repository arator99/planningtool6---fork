# Release Notes v0.6.9

**Datum:** 20 oktober 2025
**Status:** Bug fixes en nieuwe features

## Bugs Opgelost

### Bug 1: Feestdagen worden niet herkend als zondag in grid-kalender

**Probleem:**
Feestdagen werden niet correct herkend als "zondag" voor shift code validatie. Hierdoor konden planner verkeerde shift codes toewijzen op feestdagen (weekdag/zaterdag codes in plaats van zondag codes).

**Oorzaak:**
De `load_feestdagen()` methode in de grid kalender laadde alleen feestdagen voor het huidige jaar. Bij maanden aan het begin/einde van het jaar (januari/december) met 8 dagen buffer, vielen feestdagen van het vorige/volgende jaar buiten de geladen dataset.

**Oplossing:**
- Nieuwe methode `load_feestdagen_extended()` toegevoegd aan `planner_grid_kalender.py`
- Laadt nu feestdagen voor 3 jaren: vorig jaar, huidig jaar, en volgend jaar
- Buffer dagen worden nu correct gevalideerd met feestdagen check
- Fix toegepast op beide `PlannerGridKalender` en `TeamlidGridKalender`

**Bestanden aangepast:**
- `gui/widgets/planner_grid_kalender.py` - regel 307-335

---

### Bug 2: Verlof kalender rechtse kolom valt gedeeltelijk weg

**Probleem:**
Bij het openen van de kalender widget (QCalendarWidget) in het verlof aanvragen scherm, werd de rechtse kolom met datums gedeeltelijk afgesneden. De 7e dag van de week (zondag) was moeilijk leesbaar.

**Oorzaak:**
PyQt6 QCalendarWidget heeft standaard geen minimum breedte ingesteld voor tabel items, waardoor kolommen kunnen worden samengedrukt.

**Oplossing:**
- `min-width: 32px` en `min-height: 24px` toegevoegd aan `QAbstractItemView::item` styling
- `QTableView` styling toegevoegd voor betere selectie weergave
- Fix toegepast op beide start_datum en eind_datum kalender widgets

**Bestanden aangepast:**
- `gui/screens/verlof_aanvragen_screen.py` - regel 152-169 en 210-227

---

## Nieuwe Features

### Feature: Dark Mode (Nachtmodus)

**Beschrijving:**
Volledige dark mode ondersteuning voor de hele applicatie met visuele theme toggle functionaliteit.

**Functionaliteit:**
- **Light Mode** (standaard): Heldere achtergronden, donkere tekst
- **Dark Mode**: Donkere achtergronden (#1e1e1e), lichte tekst (#e0e0e0)
- **Visuele Toggle**: Schuifknop in dashboard header met zon/maan iconen
  - ☀ (zon) aan de linkerkant voor Light Mode (oranje #FFB000 met gele badge)
  - ☾ (maan) aan de rechterkant voor Dark Mode (blauw #5BC0DE met blauwe badge)
  - Knop verschuift van links naar rechts bij toggle
  - Icons hebben ronde achtergronden voor betere zichtbaarheid
  - Actieve mode heeft highlighted icon met bold font
- **Toggle locatie**: Alleen beschikbaar in dashboard (niet in andere schermen)
- **Dashboard Rebuild**: Bij toggle wordt dashboard opnieuw opgebouwd voor correcte styling
- **Persistent**: Theme voorkeur wordt opgeslagen in `data/theme_preference.json`
- **Automatisch laden**: Bij opstarten wordt de laatst gebruikte theme geladen
- **Dashboard buttons**: Menu buttons hebben aparte kleuren per theme
  - Light mode: Wit (#ffffff) met donkere tekst
  - Dark mode: Lichtgrijs (#2b3035) met lichte tekst

**Thema kleuren:**

| Element | Light Mode | Dark Mode |
|---------|-----------|-----------|
| Achtergrond | #ffffff | #1e1e1e |
| Tekst | #212529 | #e0e0e0 |
| Primary | #007bff | #4a9eff |
| Borders | #dee2e6 | #3d4349 |
| Table header | #f8f9fa | #2b3035 |

**Implementatie details:**
- **ThemeManager class**: Singleton pattern voor theme state management
- **Colors class**: Dynamische kleur palette met `_LIGHT_THEME` en `_DARK_THEME` dictionaries
- **MENU_BUTTON_BG/HOVER**: Aparte kleuren voor dashboard menu buttons per theme
- **Dashboard rebuild**: Bij toggle wordt dashboard opnieuw opgebouwd voor correcte styling
- **ThemeToggleWidget**: Visuele component met zon/maan icons en schuifknop

**Bestanden aangepast:**
- `gui/styles.py`: ThemeManager, Colors classes, MENU_BUTTON_BG/HOVER kleuren
- `main.py`: Theme loading, saving, apply met dashboard rebuild
- `gui/dialogs/handleiding_dialog.py`: Theme toggle info toegevoegd
- `gui/screens/dashboard_screen.py`: Theme toggle widget integratie
- `gui/widgets/theme_toggle_widget.py`: NIEUW - Visuele theme toggle component

**Gebruik:**
1. Start de applicatie (light mode is standaard)
2. Login → Dashboard verschijnt met theme toggle in header
3. Klik op de schuifknop (☀ ● ☾) om te wisselen
4. Dashboard wordt opnieuw opgebouwd met nieuwe theme
5. Theme wordt automatisch opgeslagen
6. Bij volgende opstart wordt de laatst gebruikte theme geladen
7. Toggle knop toont altijd huidige theme (oranje = light, blauw = dark)

**Note:** Theme toggle is alleen beschikbaar in dashboard. Andere schermen gebruiken de geselecteerde theme automatisch bij (her)laden.

---

### Feature: Rode Lijnen Visualisatie in Grid Kalenders

**Beschrijving:**
Rode lijnen (28-daagse HR cycli) worden nu visueel weergegeven in beide grid kalenders (planner en teamlid view). Dit helpt planners en teamleden om snel te zien waar een nieuwe HR periode begint.

**Functionaliteit:**
- **Visuele rode lijn**: Dikke rode linker border (4px, kleur #dc3545) markeert het begin van elke nieuwe 28-daagse periode
- **Doorlopende lijn**: De rode lijn loopt door van datum header tot aan alle shift cellen in die kolom
- **Tooltip**: Bij hover toont "Start Rode Lijn Periode X" met het periode nummer
- **Beide kalenders**: Geïmplementeerd in zowel PlannerGridKalender als TeamlidGridKalender
- **Automatisch laden**: Rode lijnen data wordt automatisch geladen bij kalender initialisatie

**Voorbeeld:**
```
| Teamlid | 17 Vr | 18 Za | │ 19 Zo | 20 Ma | 21 Di |
|---------|-------|-------|─┼--------|-------|-------|
| Jan     |   V   |  RX   | │   L    |   L   |   N   |
| Piet    |   L   |  RX   | │   N    |   V   |   V   |
                            └─ Rode lijn: Start Periode 17
```

**Use case:**
- HR regel: "Max 19 werkdagen per 28-daagse cyclus"
- Planner kan nu visueel zien waar elke cyclus begint
- Teamleden kunnen hun eigen werkdagen per periode tellen

**Implementatie details:**
- **Data loading**: Nieuwe methode `load_rode_lijnen()` in beide kalender widgets
- **Dictionary lookup**: `{datum_str: periode_nummer}` voor snelle O(1) lookup
- **Timestamp handling**: Database datums met timestamps worden gestripped naar date-only format
- **Styling**: Rode border wordt toegevoegd via CSS in zowel headers als data cellen

**Bestanden aangepast:**
- `gui/widgets/planner_grid_kalender.py`:
  - `load_rode_lijnen()` methode (regel 347-369)
  - `load_initial_data()` aanroep toegevoegd (regel 312)
  - `build_grid()` datum headers met rode lijn check (regel 414-453)
  - `create_editable_cel()` data cellen met rode lijn styling (regel 499-516)

- `gui/widgets/teamlid_grid_kalender.py`:
  - Import `get_connection` toegevoegd (regel 15)
  - `load_rode_lijnen()` methode (regel 139-161)
  - `load_initial_data()` aanroep toegevoegd (regel 124)
  - `build_grid()` datum headers met rode lijn check (regel 203-231)
  - `create_shift_cel()` data cellen met rode lijn styling (regel 270-284)

**Database query:**
```sql
SELECT start_datum, eind_datum, periode_nummer
FROM rode_lijnen
ORDER BY start_datum
```

**Gebruik:**
1. Open Planning Editor of Mijn Planning scherm
2. Navigeer naar een maand (bv. oktober 2025)
3. Zie de rode lijn op 19 oktober (Start Periode 17)
4. Hover over de kolom om periode nummer te zien
5. Gebruik de rode lijnen als visuele guide voor HR planning

---

## Technische Details

### Database Migraties
Geen database wijzigingen in deze release.

### Backwards Compatibility
Volledig backwards compatible met v0.6.8. Geen breaking changes.

### Bekende Beperkingen
- Theme toggle alleen beschikbaar in dashboard (design choice voor betrouwbaarheid)
- Andere schermen laden met geselecteerde theme, maar kunnen niet zelf wisselen
- Calendar widgets (QCalendarWidget) behouden light mode styling (Qt limitation)
- Bij navigatie tussen schermen blijft geselecteerde theme behouden

---

## Testing Checklist

**Bug Fixes:**
- [x] Bug 1: Feestdag op 1 januari 2026 wordt herkend als zondag in december 2025 buffer
- [x] Bug 2: Verlof kalender toont alle 7 kolommen volledig (min-width: 36px)

**Dark Mode:**
- [x] Feature: Dark mode toggle werkt in dashboard
- [x] Feature: Dashboard rebuild geeft correcte button kleuren
- [x] Feature: Zon/maan icons goed zichtbaar met badges
- [x] Feature: Theme voorkeur wordt persistent opgeslagen
- [x] Feature: Theme laadt automatisch bij herstart
- [x] Feature: Light mode - witte buttons, Dark mode - grijze buttons
- [x] Feature: Toggle werkt consistent bij meerdere switches

**Rode Lijnen:**
- [x] Feature: Rode lijnen zichtbaar in Planning Editor
- [x] Feature: Rode lijnen zichtbaar in Mijn Planning
- [x] Feature: Rode lijn op 19 oktober 2025 (Periode 17)
- [x] Feature: Rode lijn op 16 november 2025 (Periode 18)
- [x] Feature: Tooltip toont periode nummer
- [x] Feature: Timestamp stripping werkt correct (2024-07-28T00:00:00 → 2024-07-28)

---

## Upgrade Instructies

### Van v0.6.8 naar v0.6.9

1. **Backup**: Maak een backup van `data/planning.db`
2. **Kopieer files**: Vervang alle aangepaste bestanden
3. **Test**: Start applicatie en test theme toggle in dashboard
4. **Geen migratie nodig**: Database schema is ongewijzigd

### Nieuwe bestanden
- `data/theme_preference.json` (wordt automatisch aangemaakt bij eerste theme toggle)
- `gui/widgets/theme_toggle_widget.py` (visuele theme toggle component)

### Gewijzigde bestanden
- `gui/styles.py` - ThemeManager en Colors classes
- `main.py` - Theme loading/saving en QCheckBox styling
- `gui/screens/dashboard_screen.py` - Theme toggle widget integratie
- `gui/screens/verlof_aanvragen_screen.py` - Calendar widget styling fix
- `gui/widgets/planner_grid_kalender.py` - Feestdagen extended + rode lijnen
- `gui/widgets/teamlid_grid_kalender.py` - Rode lijnen visualisatie
- `gui/dialogs/handleiding_dialog.py` - Theme toggle info

---

## Volgende Stappen (Roadmap)

**Voor v0.7.0:**
- HR Regels validatie in planning editor
- Export functionaliteit naar Excel
- Typetabel activatie flow
- Bulk shift operations

**Voor v1.0:**
- Network database support verbeteren
- .EXE build optimalisatie
- Volledige documentatie update
