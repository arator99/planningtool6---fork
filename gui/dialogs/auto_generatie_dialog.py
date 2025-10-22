# gui/dialogs/auto_generatie_dialog.py
"""
Auto-Generatie Dialog
Dialog voor het genereren van planning uit actieve typetabel
"""
from typing import Dict, Any, Optional, List, Set
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QDateEdit, QMessageBox, QTextEdit,
                             QCheckBox, QGroupBox)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont
from database.connection import get_connection
from gui.styles import Styles, Colors, Fonts, Dimensions
from datetime import datetime, timedelta
import sqlite3


class AutoGeneratieDialog(QDialog):
    """Dialog voor auto-generatie uit typetabel"""

    def __init__(self, parent, current_year: int, current_month: int):
        super().__init__(parent)
        self.current_year = current_year
        self.current_month = current_month

        self.setWindowTitle("Auto-Genereren uit Typetabel")
        self.setModal(True)
        self.resize(700, 650)

        # Instance attributes
        self.start_datum: QDateEdit = QDateEdit()
        self.eind_datum: QDateEdit = QDateEdit()
        self.preview_text: QTextEdit = QTextEdit()

        # Data
        self.actieve_typetabel: Optional[Dict[str, Any]] = None
        self.gebruikers: List[Dict[str, Any]] = []
        self.bestaande_data_count: int = 0
        self.beschermd_count: int = 0
        self.speciale_codes: Set[str] = set()
        self.feestdagen: Dict[str, bool] = {}  # {datum_str: is_zondagsrust}

        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Title
        title = QLabel("Auto-Generatie uit Typetabel")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(title)

        # Info box
        info = QLabel(
            "Genereer planning automatisch op basis van de actieve typetabel.\n"
            "FEESTDAGEN: Worden behandeld als zondag (bijv. V → 7701).\n"
            "BESCHERMD: Verlof, ziekte, rust en handmatig aangepaste shifts worden NIET overschreven."
        )
        info.setStyleSheet(Styles.info_box())
        info.setWordWrap(True)
        layout.addWidget(info)

        # Datum range group
        datum_group = QGroupBox("Datum Bereik")
        datum_layout = QVBoxLayout()

        # Start datum
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Van:"))
        self.start_datum.setCalendarPopup(True)
        self.start_datum.setDisplayFormat("dd-MM-yyyy")
        self.start_datum.setDate(QDate(self.current_year, self.current_month, 1))
        self.start_datum.setStyleSheet(Styles.input_field())
        self.start_datum.dateChanged.connect(self.on_datum_changed)  # type: ignore
        start_layout.addWidget(self.start_datum)
        datum_layout.addLayout(start_layout)

        # Eind datum
        eind_layout = QHBoxLayout()
        eind_layout.addWidget(QLabel("Tot:"))
        self.eind_datum.setCalendarPopup(True)
        self.eind_datum.setDisplayFormat("dd-MM-yyyy")
        # Default: laatste dag van huidige maand
        laatste_dag = QDate(self.current_year, self.current_month, 1).addMonths(1).addDays(-1)
        self.eind_datum.setDate(laatste_dag)
        self.eind_datum.setStyleSheet(Styles.input_field())
        self.eind_datum.dateChanged.connect(self.on_datum_changed)  # type: ignore
        eind_layout.addWidget(self.eind_datum)
        datum_layout.addLayout(eind_layout)

        datum_group.setLayout(datum_layout)
        layout.addWidget(datum_group)

        # Preview group
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()

        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(280)
        self.preview_text.setStyleSheet(Styles.input_field())
        preview_layout.addWidget(self.preview_text)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        annuleer_btn = QPushButton("Annuleren")
        annuleer_btn.setStyleSheet(Styles.button_secondary())
        annuleer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        annuleer_btn.clicked.connect(self.reject)  # type: ignore
        button_layout.addWidget(annuleer_btn)

        genereer_btn = QPushButton("Genereren")
        genereer_btn.setStyleSheet(Styles.button_success())
        genereer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        genereer_btn.clicked.connect(self.genereer)  # type: ignore
        button_layout.addWidget(genereer_btn)

        layout.addLayout(button_layout)

    def load_data(self):
        """Laad actieve typetabel, gebruikers en speciale codes"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Haal actieve typetabel op
            cursor.execute("""
                SELECT id, versie_naam, aantal_weken, actief_vanaf
                FROM typetabel_versies
                WHERE status = 'actief'
            """)
            self.actieve_typetabel = cursor.fetchone()

            if not self.actieve_typetabel:
                conn.close()
                QMessageBox.warning(
                    self,
                    "Geen Actieve Typetabel",
                    "Er is geen actieve typetabel beschikbaar.\n\n"
                    "Ga naar Instellingen → Typetabel Beheer om een typetabel te activeren."
                )
                self.reject()
                return

            # Haal actieve gebruikers op (niet admin, niet reserve)
            cursor.execute("""
                SELECT id, volledige_naam, startweek_typedienst
                FROM gebruikers
                WHERE is_actief = 1
                  AND gebruikersnaam != 'admin'
                  AND is_reserve = 0
                ORDER BY volledige_naam
            """)
            self.gebruikers = cursor.fetchall()

            # Haal speciale codes op (voor bescherming)
            cursor.execute("""
                SELECT code
                FROM speciale_codes
            """)
            for row in cursor.fetchall():
                self.speciale_codes.add(row['code'])

            # Haal feestdagen op (voor correcte code toekenning)
            cursor.execute("""
                SELECT datum, is_zondagsrust
                FROM feestdagen
            """)
            for row in cursor.fetchall():
                self.feestdagen[row['datum']] = bool(row['is_zondagsrust'])

            conn.close()

            # Update preview
            self.update_preview()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))
            self.reject()

    def on_datum_changed(self):
        """Update preview bij datum wijziging"""
        self.update_preview()

    def update_preview(self):
        """Update preview tekst"""
        if not self.actieve_typetabel:
            return

        start_date = self.start_datum.date().toPyDate()
        eind_date = self.eind_datum.date().toPyDate()

        # Validatie
        if start_date > eind_date:
            self.preview_text.setPlainText("⚠️ Start datum moet voor eind datum liggen!")
            return

        # Bereken aantal dagen
        dagen = (eind_date - start_date).days + 1

        # Check bestaande data
        self.check_bestaande_data(start_date, eind_date)

        # Bouw preview tekst
        lines = []
        lines.append(f"TYPETABEL: {self.actieve_typetabel['versie_naam']}")
        lines.append(f"Cyclus: {self.actieve_typetabel['aantal_weken']} weken")
        lines.append(f"Actief vanaf: {self.actieve_typetabel['actief_vanaf']}")
        lines.append("")
        lines.append(f"PERIODE: {start_date.strftime('%d-%m-%Y')} t/m {eind_date.strftime('%d-%m-%Y')}")
        lines.append(f"Aantal dagen: {dagen}")
        lines.append("")
        lines.append(f"GEBRUIKERS: {len(self.gebruikers)}")

        # Toon eerste 5 gebruikers met startweek
        for i, gebruiker in enumerate(self.gebruikers[:5]):
            startweek = gebruiker['startweek_typedienst'] or 1
            lines.append(f"  - {gebruiker['volledige_naam']} (startweek {startweek})")

        if len(self.gebruikers) > 5:
            lines.append(f"  ... en {len(self.gebruikers) - 5} anderen")

        lines.append("")
        lines.append(f"TOTAAL TE GENEREREN: {len(self.gebruikers) * dagen} planning records")
        lines.append("")
        lines.append("FEESTDAGEN:")
        lines.append(f"  - {len(self.feestdagen)} feestdagen gevonden")
        lines.append("  - Worden behandeld als zondag (V → 7701, L → 7801, etc.)")
        lines.append("")
        lines.append("BESCHERMING:")
        lines.append(f"  - Speciale codes: {', '.join(sorted(self.speciale_codes)) if self.speciale_codes else 'Geen'}")
        lines.append("  - Handmatig aangepaste shifts")

        if self.bestaande_data_count > 0:
            lines.append("")
            lines.append(f"ℹ️ BESTAAND: {self.bestaande_data_count} records")
            if self.beschermd_count > 0:
                lines.append(f"🔒 BESCHERMD: {self.beschermd_count} records (worden overgeslagen)")
            lines.append(f"✓ WORDT INGEVULD: Lege cellen en typetabel-shifts")

        self.preview_text.setPlainText("\n".join(lines))

    def check_bestaande_data(self, start_date, eind_date):
        """Check hoeveel planning records al bestaan en hoeveel beschermd zijn"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Totaal bestaande records
            cursor.execute("""
                SELECT COUNT(*)
                FROM planning
                WHERE datum >= ? AND datum <= ?
                  AND shift_code IS NOT NULL
            """, (start_date.isoformat(), eind_date.isoformat()))

            result = cursor.fetchone()
            self.bestaande_data_count = result[0] if result else 0

            # Beschermde records (speciale codes)
            if self.speciale_codes:
                placeholders = ','.join(['?' for _ in self.speciale_codes])
                query = f"""
                    SELECT COUNT(*)
                    FROM planning
                    WHERE datum >= ? AND datum <= ?
                      AND shift_code IN ({placeholders})
                """
                params = [start_date.isoformat(), eind_date.isoformat()] + list(self.speciale_codes)
                cursor.execute(query, params)

                result = cursor.fetchone()
                self.beschermd_count = result[0] if result else 0
            else:
                self.beschermd_count = 0

            conn.close()

        except sqlite3.Error:
            self.bestaande_data_count = 0
            self.beschermd_count = 0

    def genereer(self):
        """Voer auto-generatie uit"""
        if not self.actieve_typetabel:
            QMessageBox.warning(self, "Fout", "Geen actieve typetabel beschikbaar!")
            return

        start_date = self.start_datum.date().toPyDate()
        eind_date = self.eind_datum.date().toPyDate()

        if start_date > eind_date:
            QMessageBox.warning(self, "Validatie Fout", "Start datum moet voor eind datum liggen!")
            return

        # Bevestiging
        reply = QMessageBox.question(
            self,
            "Bevestig Genereren",
            f"Planning genereren voor {len(self.gebruikers)} gebruikers van "
            f"{start_date.strftime('%d-%m-%Y')} t/m {eind_date.strftime('%d-%m-%Y')}?\n\n"
            f"Lege cellen en typetabel-shifts worden ingevuld.\n"
            f"Verlof, ziekte en handmatige wijzigingen blijven behouden.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Genereer planning
        try:
            records_toegevoegd, records_beschermd = self.genereer_planning(start_date, eind_date)

            QMessageBox.information(
                self,
                "Succes",
                f"✓ {records_toegevoegd} planning records gegenereerd\n"
                f"🔒 {records_beschermd} records beschermd (niet overschreven)"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Fout bij genereren:\n{str(e)}")

    def genereer_planning(self, start_date, eind_date) -> tuple:
        """
        Genereer planning records uit typetabel
        Returns: (records_toegevoegd, records_beschermd)
        """
        conn = get_connection()
        cursor = conn.cursor()

        records_toegevoegd = 0
        records_beschermd = 0
        versie_id = self.actieve_typetabel['id']
        aantal_weken = self.actieve_typetabel['aantal_weken']
        actief_vanaf_str = self.actieve_typetabel['actief_vanaf']

        # Parse actief_vanaf datum
        try:
            actief_vanaf = datetime.strptime(actief_vanaf_str, "%Y-%m-%d").date()
        except:
            # Fallback als format anders is
            actief_vanaf = datetime.fromisoformat(actief_vanaf_str).date()

        # Laad alle typetabel data in memory (sneller)
        cursor.execute("""
            SELECT week_nummer, dag_nummer, shift_type
            FROM typetabel_data
            WHERE versie_id = ?
        """, (versie_id,))

        typetabel_data = {}
        for row in cursor.fetchall():
            key = (row['week_nummer'], row['dag_nummer'])
            typetabel_data[key] = row['shift_type']

        # Laad gebruiker werkposten mapping (NIEUW - v0.6.14)
        cursor.execute("""
            SELECT gebruiker_id, werkpost_id, prioriteit
            FROM gebruiker_werkposten
            ORDER BY gebruiker_id, prioriteit
        """)

        gebruiker_werkposten = {}  # {gebruiker_id: [(werkpost_id, prioriteit), ...]}
        for row in cursor.fetchall():
            gebruiker_id = row['gebruiker_id']
            if gebruiker_id not in gebruiker_werkposten:
                gebruiker_werkposten[gebruiker_id] = []
            gebruiker_werkposten[gebruiker_id].append((row['werkpost_id'], row['prioriteit']))

        # Laad shift_codes mapping (NIEUW - v0.6.14)
        cursor.execute("""
            SELECT werkpost_id, dag_type, shift_type, code
            FROM shift_codes
        """)

        shift_codes_map = {}  # {(werkpost_id, dag_type, shift_type): code}
        for row in cursor.fetchall():
            key = (row['werkpost_id'], row['dag_type'], row['shift_type'])
            shift_codes_map[key] = row['code']

        # Laad alle bestaande planning in memory (sneller dan per query)
        cursor.execute("""
            SELECT gebruiker_id, datum, shift_code
            FROM planning
            WHERE datum >= ? AND datum <= ?
        """, (start_date.isoformat(), eind_date.isoformat()))

        bestaande_planning = {}
        for row in cursor.fetchall():
            key = (row['gebruiker_id'], row['datum'])
            bestaande_planning[key] = row['shift_code']

        # Loop door elke gebruiker
        for gebruiker in self.gebruikers:
            gebruiker_id = gebruiker['id']
            startweek = gebruiker['startweek_typedienst'] or 1

            # Haal werkposten van gebruiker op
            werkposten = gebruiker_werkposten.get(gebruiker_id, [])
            if not werkposten:
                # Gebruiker heeft geen werkposten - skip
                continue

            # Loop door elke datum
            current_date = start_date
            while current_date <= eind_date:
                # Bereken shift voor deze datum (SLIMME VERSIE)
                shift_code_typetabel = self.bereken_shift_slim(
                    current_date,
                    actief_vanaf,
                    aantal_weken,
                    startweek,
                    typetabel_data,
                    werkposten,
                    shift_codes_map,
                    self.feestdagen  # NIEUW: feestdagen meegeven
                )

                # Check bestaande planning
                key = (gebruiker_id, current_date.isoformat())
                bestaande_code = bestaande_planning.get(key)

                # Beslissingslogica
                if bestaande_code is None:
                    # Lege cel - altijd invullen
                    cursor.execute("""
                        INSERT OR REPLACE INTO planning
                        (gebruiker_id, datum, shift_code, status)
                        VALUES (?, ?, ?, 'concept')
                    """, (gebruiker_id, current_date.isoformat(), shift_code_typetabel))
                    records_toegevoegd += 1

                elif bestaande_code in self.speciale_codes:
                    # Speciale code (VV, KD, RX, etc.) - BESCHERMD
                    records_beschermd += 1

                elif bestaande_code == shift_code_typetabel:
                    # Zelfde als typetabel - refresh (update timestamp)
                    cursor.execute("""
                        INSERT OR REPLACE INTO planning
                        (gebruiker_id, datum, shift_code, status)
                        VALUES (?, ?, ?, 'concept')
                    """, (gebruiker_id, current_date.isoformat(), shift_code_typetabel))
                    # Niet tellen als nieuw toegevoegd (is refresh)

                else:
                    # Handmatig aangepaste shift - BESCHERMD
                    records_beschermd += 1

                current_date += timedelta(days=1)

        conn.commit()
        conn.close()

        return records_toegevoegd, records_beschermd

    def bereken_shift_slim(self, datum, actief_vanaf, aantal_weken, startweek,
                           typetabel_data, werkposten, shift_codes_map,
                           feestdagen) -> Optional[str]:
        """
        Bereken shift code voor een specifieke datum en gebruiker (SLIM - v0.6.14)

        Args:
            datum: Datum waarvoor shift berekend wordt
            actief_vanaf: Start datum typetabel
            aantal_weken: Aantal weken in typetabel cyclus
            startweek: Gebruiker's startweek in cyclus
            typetabel_data: {(week, dag): shift_type} - bijv. "V", "L", "N"
            werkposten: [(werkpost_id, prioriteit), ...] voor deze gebruiker
            shift_codes_map: {(werkpost_id, dag_type, shift_type): code}
            feestdagen: {datum_str: is_zondagsrust} - feestdagen mapping

        Returns:
            Concrete shift code (bijv. "7101") of None
        """
        # Bereken aantal dagen sinds actief_vanaf
        dagen_verschil = (datum - actief_vanaf).days

        # Bereken week in cyclus (0-based, dan +1 voor 1-based)
        # Met startweek offset
        week_in_cyclus = ((dagen_verschil // 7 + startweek - 1) % aantal_weken) + 1

        # Dag nummer (1=maandag, 7=zondag)
        dag_nummer = datum.isoweekday()

        # Haal shift_type op uit typetabel (bijv. "V", "L", "N", "dag")
        key = (week_in_cyclus, dag_nummer)
        shift_type = typetabel_data.get(key)

        if not shift_type:
            return None

        # CHECK FEESTDAG: Feestdagen worden behandeld als zondag voor shift codes
        datum_str = datum.isoformat()
        is_feestdag = datum_str in feestdagen

        # Bereken dag_type op basis van dag nummer (of feestdag!)
        if is_feestdag:
            # Feestdag = altijd zondag shift codes gebruiken (bijv. V → 7701)
            dag_type = 'zondag'
        elif dag_nummer == 6:  # Zaterdag
            dag_type = 'zaterdag'
        elif dag_nummer == 7:  # Zondag
            dag_type = 'zondag'
        else:  # Ma-Vr
            dag_type = 'weekdag'

        # Check of dit een directe code is (RX, CX, T)
        # Deze codes moeten niet gemapt worden maar direct overgenomen
        shift_type_upper = shift_type.upper()
        if shift_type_upper in ['RX', 'CX', 'T']:
            # Directe code - return as-is
            return shift_type_upper

        # Normaliseer shift_type naar shift_codes formaat (V, L, N, D)
        # Typetabel kan "V", "v", "vroeg" bevatten
        shift_type_lower = shift_type.lower()
        if shift_type_lower in ['v', 'vroeg']:
            shift_type_normalized = 'vroeg'
        elif shift_type_lower in ['l', 'laat']:
            shift_type_normalized = 'laat'
        elif shift_type_lower in ['n', 'nacht']:
            shift_type_normalized = 'nacht'
        elif shift_type_lower in ['d', 'dag']:
            shift_type_normalized = 'dag'
        else:
            # Onbekend shift type - return None
            return None

        # Loop door werkposten (op prioriteit) om match te vinden
        for werkpost_id, _ in sorted(werkposten, key=lambda x: x[1]):
            lookup_key = (werkpost_id, dag_type, shift_type_normalized)
            shift_code = shift_codes_map.get(lookup_key)

            if shift_code:
                # Match gevonden!
                return shift_code

        # Geen match gevonden in shift_codes - return None
        return None
