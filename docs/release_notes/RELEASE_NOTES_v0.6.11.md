# Release Notes v0.6.11

**Release Datum:** 21 Oktober 2025
**Status:** Beta - Shift Voorkeuren Systeem

---

## 🎯 NIEUWE FEATURES

### Shift Voorkeuren Systeem
Teamleden kunnen nu hun shift voorkeuren instellen voor toekomstige automatische planning generatie.

**Functionaliteit:**
- ✅ **Persoonlijke Voorkeuren Scherm**
  - Dashboard → Persoonlijk → Mijn Voorkeuren
  - Stel prioriteit in voor shift types (1 = hoogste, 4 = laagste)
  - Opties: Vroege dienst, Late dienst, Nachtdienst, Typetabel
  - Live preview van gekozen volgorde
  - Validatie: geen dubbele prioriteiten

- ✅ **Flexible Prioriteit System**
  - Niet verplicht om alle opties in te vullen
  - Gebruikers kunnen 1, 2, 3 of 4 voorkeuren instellen
  - Leeg = geen voorkeur (standaard: typetabel of vrije invulling)
  - Meerdere opties mogen leeg blijven

- ✅ **Database Storage**
  - Voorkeuren opgeslagen als JSON in `gebruikers.shift_voorkeuren`
  - Format: `{"1": "vroeg", "2": "typetabel", "3": "laat"}`
  - Migratie script: `migratie_shift_voorkeuren.py`

**Gebruik voor Teamleden:**
1. Dashboard → Persoonlijk → Mijn Voorkeuren
2. Kies prioriteit (1-4) voor elk shift type
3. Preview toont gekozen volgorde
4. Klik "Opslaan"

**Hoe het werkt:**
- Bij toekomstige automatische planning generatie krijgen je voorkeuren voorrang
- Prioriteit 1 = hoogste voorkeur
- Je kunt opties leeg laten als je geen voorkeur hebt
- "Typetabel" = volg het standaard rooster patroon
- Als geen voorkeuren ingesteld: automatisch typetabel of vrije invulling

**Voorbeeld Scenario's:**
```
Scenario 1: Voorkeur voor vroege diensten
- Vroege Dienst: 1 (Hoogste)
- Typetabel: 2
- Rest: (Geen voorkeur)

Scenario 2: Nacht voorkeur met fallback
- Nachtdienst: 1 (Hoogste)
- Typetabel: 2
- Vroege Dienst: 3
- Late Dienst: 4 (Laagste)

Scenario 3: Alleen typetabel volgen
- Typetabel: 1 (Hoogste)
- Rest: (Geen voorkeur)

Scenario 4: Geen voorkeuren
- Alles: (Geen voorkeur)
→ Systeem gebruikt typetabel of vult vrij in
```

---

## 🔧 TECHNISCHE DETAILS

### Database Wijzigingen

**Nieuwe Kolom: `gebruikers.shift_voorkeuren`**
```sql
ALTER TABLE gebruikers
ADD COLUMN shift_voorkeuren TEXT;
```

**JSON Format:**
```json
{
  "1": "vroeg",
  "2": "typetabel",
  "3": "laat",
  "4": "nacht"
}
```

**Mapping:**
- `"vroeg"` = Voorkeur voor vroege diensten
- `"laat"` = Voorkeur voor late diensten
- `"nacht"` = Voorkeur voor nachtdiensten
- `"typetabel"` = Volg het standaard rooster patroon

### Nieuwe Bestanden

**Migratie:**
- `migratie_shift_voorkeuren.py` - Database migratie script

**GUI:**
- `gui/screens/voorkeuren_screen.py` - Voorkeuren scherm voor teamleden

**Modified:**
- `database/connection.py` - `shift_voorkeuren` kolom toegevoegd aan create_tables()
- `main.py` - Handler voor voorkeuren scherm geïmplementeerd

---

## 📋 MIGRATIE INSTRUCTIES

### Voor Bestaande Databases (v0.6.10 → v0.6.11)

```bash
python migratie_shift_voorkeuren.py
```

**Wat doet dit:**
1. Voegt `shift_voorkeuren` kolom toe aan `gebruikers` tabel
2. Standaard waarde: NULL (geen voorkeuren)
3. Idempotent: kan veilig meerdere keren draaien

**Voor Schone Database:**
Geen migratie nodig - kolom wordt automatisch aangemaakt.

---

## 🎨 UI/UX FEATURES

**Info Box:**
- Duidelijke uitleg hoe voorkeuren werken
- Voorbeelden van gebruik
- Tips voor gebruikers

**Live Preview:**
- Real-time weergave van gekozen volgorde
- Kleuren: groen = voorkeuren ingesteld, grijs = geen voorkeuren
- Format: "1. Vroeg > 2. Typetabel > 3. Laat"

**Validatie:**
- Voorkomt dubbele prioriteiten
- Duidelijke foutmeldingen
- Suggesties bij fouten

**Reset Functie:**
- "Reset naar Standaard" knop
- Zet alles terug naar "Geen voorkeur"
- Bevestiging vereist

---

## 🔮 TOEKOMSTIG GEBRUIK

Dit voorkeuren systeem wordt gebruikt bij:

1. **Automatische Planning Generatie** (toekomstige feature)
   - Systeem respecteert shift voorkeuren bij auto-generatie
   - Prioriteit 1 voorkeuren krijgen voorrang
   - Fallback naar lagere prioriteiten indien nodig

2. **Planning Optimalisatie**
   - Betere match tussen voorkeuren en werkelijkheid
   - Minder handmatige aanpassingen nodig
   - Hogere tevredenheid teamleden

3. **Planning Algoritme**
   - Input voor smart scheduling
   - Balans tussen voorkeuren en bedrijfsbehoeften
   - Rekening houden met HR regels

---

## 🧪 TESTING

**Getest:**
- ✅ Voorkeuren opslaan en laden
- ✅ Live preview updates
- ✅ Validatie van duplicaten
- ✅ Reset functionaliteit
- ✅ Database migratie (bestaand → nieuw)
- ✅ Schone database setup
- ✅ UI layout en styling
- ✅ Navigation (dashboard → voorkeuren → terug)

**Browser Support:**
N/A (Desktop applicatie)

---

## 🐛 BEKENDE ISSUES

Geen bekende issues in deze release.

---

## 📝 NOTITIES VOOR ONTWIKKELAARS

**Data Model:**
- Voorkeuren opgeslagen als JSON string
- NULL = geen voorkeuren ingesteld
- Parsing: `json.loads()` met error handling
- Reverse mapping nodig voor UI display

**UI Pattern:**
- ComboBox met 5 opties: "(Geen voorkeur)", "1 (Hoogste)", "2", "3", "4 (Laagste)"
- Index 0 = geen voorkeur
- Index 1-4 = prioriteit 1-4

**Future Considerations:**
- Bij meer shift types: systeem uitbreiden met extra opties
- Bij wijziging shift codes: mapping blijft hetzelfde (vroeg/laat/nacht)
- Voorkeuren zijn suggesties, geen garanties

---

## 🔄 UPGRADE PATH

**Van v0.6.10:**
1. Run migratie script: `python migratie_shift_voorkeuren.py`
2. Restart applicatie
3. Teamleden kunnen voorkeuren instellen via Dashboard → Persoonlijk → Mijn Voorkeuren

**Van eerdere versies:**
Eerst upgraden naar v0.6.10, dan naar v0.6.11.

---

## 📚 DOCUMENTATIE UPDATES

- `DEV_NOTES.md` - Sessie 21 Oktober 2025 toegevoegd
- `DEVELOPMENT_GUIDE.md` - Voorkeuren systeem gedocumenteerd
- `PROJECT_INFO.md` - Gebruikersinstructies voor voorkeuren toegevoegd
- `CLAUDE.md` - Workflow en versie informatie bijgewerkt

---

**Vorige versie:** v0.6.10 (Verlof & KD Saldo Systeem)
**Volgende versie:** v0.6.12 (TBD)

*Laatste update: 21 Oktober 2025*
