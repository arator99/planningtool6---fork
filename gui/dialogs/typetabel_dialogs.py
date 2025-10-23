#gui/dialogs/typetabel_dialogs.py

"""
Typetabel Dialogs
Dialogs voor typetabel beheer
"""
from typing import Dict, Any
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QSpinBox, QTextEdit,
                             QMessageBox, QDateEdit)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QFont
from gui.styles import Styles, Fonts, Dimensions, Colors


class NieuweTypetabelDialog(QDialog):
    """Dialog voor nieuwe typetabel aanmaken"""

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Nieuwe Typetabel")
        self.setModal(True)
        self.setMinimumWidth(500)

        # Instance attributes
        self.naam_input = QLineEdit()
        self.weken_spin = QSpinBox()
        self.opmerking_input = QTextEdit()

        self.init_ui()

    def init_ui(self):
        """Initialiseer UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Title
        title = QLabel("Nieuwe Typetabel")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(title)

        # Info
        info = QLabel(
            "Een typetabel is een herhalend patroon dat gebruikt wordt "
            "voor automatische planning generatie."
        )
        info.setWordWrap(True)
        info.setStyleSheet(Styles.info_box())
        layout.addWidget(info)

        # Naam
        layout.addWidget(QLabel("Naam:"))
        self.naam_input.setPlaceholderText("Bijv. 'Interventie 18 weken Winter 2026'")
        self.naam_input.setStyleSheet(Styles.input_field())
        layout.addWidget(self.naam_input)

        # Aantal weken
        layout.addWidget(QLabel("Aantal weken in patroon:"))

        weken_layout = QHBoxLayout()
        self.weken_spin.setMinimum(1)
        self.weken_spin.setMaximum(52)
        self.weken_spin.setValue(6)
        self.weken_spin.setStyleSheet(Styles.input_field())
        weken_layout.addWidget(self.weken_spin)

        weken_info = QLabel("(1-52 weken)")
        weken_info.setStyleSheet("color: #666;")
        weken_layout.addWidget(weken_info)
        weken_layout.addStretch()

        layout.addLayout(weken_layout)

        # Info over herhalend patroon
        herhaald_info = QLabel(
            "ℹ️ Het patroon herhaalt na dit aantal weken. Personen kunnen "
            "startweek 1 tot {} krijgen.".format(self.weken_spin.value())
        )
        herhaald_info.setWordWrap(True)
        herhaald_info.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        layout.addWidget(herhaald_info)

        # Update info bij wijziging
        self.weken_spin.valueChanged.connect(
            lambda val: herhaald_info.setText(
                f"ℹ️ Het patroon herhaalt na dit aantal weken. Personen kunnen "
                f"startweek 1 tot {val} krijgen."
            )
        )  # type: ignore

        # Opmerking
        layout.addWidget(QLabel("Opmerking (optioneel):"))
        self.opmerking_input.setPlaceholderText("Bijv. 'Voor winter periode 2026'")
        self.opmerking_input.setMaximumHeight(80)
        self.opmerking_input.setStyleSheet(Styles.input_field())
        layout.addWidget(self.opmerking_input)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        annuleer_btn = QPushButton("Annuleren")
        annuleer_btn.setStyleSheet(Styles.button_secondary())
        annuleer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        annuleer_btn.clicked.connect(self.reject)  # type: ignore
        button_layout.addWidget(annuleer_btn)

        aanmaken_btn = QPushButton("Aanmaken")
        aanmaken_btn.setStyleSheet(Styles.button_success())
        aanmaken_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        aanmaken_btn.clicked.connect(self.valideer_en_accept)  # type: ignore
        button_layout.addWidget(aanmaken_btn)

        layout.addLayout(button_layout)

    def valideer_en_accept(self):
        """Valideer input en sluit dialog"""
        if not self.naam_input.text().strip():
            QMessageBox.warning(self, "Fout", "Naam is verplicht!")
            return

        self.accept()

    def get_data(self) -> Dict[str, Any]:
        """Haal data op uit dialog"""
        return {
            'naam': self.naam_input.text().strip(),
            'aantal_weken': self.weken_spin.value(),
            'opmerking': self.opmerking_input.toPlainText().strip()
        }


class ActiveerTypetabelDialog(QDialog):
    """Dialog voor activatie van concept typetabel"""

    def __init__(self, parent, versie: Dict[str, Any], heeft_actieve: bool = False):
        super().__init__(parent)

        self.versie = versie
        self.heeft_actieve = heeft_actieve

        self.setWindowTitle("Typetabel Activeren")
        self.setModal(True)
        self.setMinimumWidth(600)

        # Instance attributes
        self.datum_input = QDateEdit()

        self.init_ui()

    def init_ui(self):
        """Initialiseer UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Title
        title = QLabel(f"Activeren: {self.versie['versie_naam']}")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(title)

        # Waarschuwing als er al een actieve is
        if self.heeft_actieve:
            waarschuwing = QLabel(
                "LET OP: Er is al een actieve typetabel!\n\n"
                "Bij activatie wordt de huidige actieve typetabel gearchiveerd.\n"
                "De nieuwe typetabel wordt vanaf de gekozen datum actief."
            )
            waarschuwing.setWordWrap(True)
            waarschuwing.setStyleSheet(f"""
                background-color: {Colors.WARNING_BG};
                border: 2px solid {Colors.WARNING};
                border-radius: 4px;
                padding: 12px;
                color: #000;
            """)
            layout.addWidget(waarschuwing)

        # Info
        info = QLabel(
            f"Activeer deze typetabel om deze te gebruiken voor auto-generatie.\n\n"
            f"Patroon: {self.versie['aantal_weken']} weken cyclus"
        )
        info.setWordWrap(True)
        info.setStyleSheet(Styles.info_box())
        layout.addWidget(info)

        # Datum picker
        layout.addWidget(QLabel("Actief vanaf datum:"))

        datum_layout = QHBoxLayout()

        self.datum_input.setCalendarPopup(True)
        self.datum_input.setDisplayFormat("dd-MM-yyyy")
        self.datum_input.setDate(QDate.currentDate())
        self.datum_input.setStyleSheet(Styles.input_field())
        datum_layout.addWidget(self.datum_input)

        datum_info = QLabel("(Meestal een maandag)")
        datum_info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        datum_layout.addWidget(datum_info)
        datum_layout.addStretch()

        layout.addLayout(datum_layout)

        # Weekdag waarschuwing
        self.weekdag_label = QLabel()
        self.weekdag_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: {Fonts.SIZE_SMALL}px;")
        layout.addWidget(self.weekdag_label)
        self.update_weekdag_info()

        # Connect datum change
        self.datum_input.dateChanged.connect(self.update_weekdag_info)  # type: ignore

        # Spacer
        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        annuleer_btn = QPushButton("Annuleren")
        annuleer_btn.setStyleSheet(Styles.button_secondary())
        annuleer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        annuleer_btn.clicked.connect(self.reject)  # type: ignore
        button_layout.addWidget(annuleer_btn)

        activeer_btn = QPushButton("Activeren")
        activeer_btn.setStyleSheet(Styles.button_success())
        activeer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        activeer_btn.clicked.connect(self.accept)  # type: ignore
        button_layout.addWidget(activeer_btn)

        layout.addLayout(button_layout)

    def update_weekdag_info(self):
        """Update weekdag informatie"""
        datum = self.datum_input.date()
        weekdag_nr = datum.dayOfWeek()  # 1=maandag, 7=zondag

        dagen = ['Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag', 'Zondag']
        weekdag_naam = dagen[weekdag_nr - 1]

        if weekdag_nr == 1:
            self.weekdag_label.setText(f"✓ {weekdag_naam} - Ideaal voor start typetabel!")
        else:
            self.weekdag_label.setText(f"ℹ️ {weekdag_naam} - Let op: meestal start je op maandag")

    def get_datum(self) -> str:
        """Haal gekozen datum op (ISO format)"""
        qdate = self.datum_input.date()
        return qdate.toString("yyyy-MM-dd")