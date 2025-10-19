# gui/dialogs/rode_lijnen_config_dialog.py
"""
Rode Lijnen Config Dialog
Voor het wijzigen van rode lijnen configuratie met nieuwe versie + datum
"""
from typing import Dict, Any
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSpinBox, QDateEdit,
                             QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime
from gui.styles import Styles, Colors, Fonts, Dimensions


class RodeLijnenConfigDialog(QDialog):
    """Dialog voor het wijzigen van rode lijnen configuratie"""

    def __init__(self, parent, config: Dict[str, Any]):
        super().__init__(parent)
        self.config = config

        self.setWindowTitle("Rode Lijnen Configuratie Wijzigen")
        self.setModal(True)
        self.setMinimumWidth(550)

        # Instance attributes
        self.start_datum_input: QDateEdit = QDateEdit()
        self.interval_input: QSpinBox = QSpinBox()
        self.actief_vanaf_input: QDateEdit = QDateEdit()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Title
        title = QLabel("Wijzig Rode Lijnen Configuratie")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(title)

        # Info box
        info = QLabel(
            "Bij wijzigen wordt een nieuwe versie aangemaakt.\n"
            "De oude configuratie wordt gearchiveerd met einddatum = nieuwe startdatum."
        )
        info.setStyleSheet(Styles.info_box())
        info.setWordWrap(True)
        layout.addWidget(info)

        # Huidige config
        huidig_group = QVBoxLayout()
        huidig_label = QLabel("HUIDIGE CONFIGURATIE:")
        huidig_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        huidig_group.addWidget(huidig_label)

        # Start datum
        start_datum = datetime.fromisoformat(self.config['start_datum'])
        start_str = start_datum.strftime('%d-%m-%Y')
        start_label = QLabel(f"Start datum: {start_str}")
        start_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: {Fonts.SIZE_NORMAL}px;")
        huidig_group.addWidget(start_label)

        # Interval
        interval_label = QLabel(f"Interval: {self.config['interval_dagen']} dagen")
        interval_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_LARGE))
        interval_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        huidig_group.addWidget(interval_label)

        # Actief vanaf
        if self.config.get('actief_vanaf'):
            datum = datetime.fromisoformat(self.config['actief_vanaf'])
            datum_str = datum.strftime('%d-%m-%Y')
            vanaf_label = QLabel(f"Actief vanaf: {datum_str}")
            vanaf_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: {Fonts.SIZE_SMALL}px;")
            huidig_group.addWidget(vanaf_label)

        layout.addLayout(huidig_group)

        # Nieuwe config form
        form_layout = QFormLayout()
        form_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Start datum input
        self.start_datum_input.setCalendarPopup(True)
        self.start_datum_input.setDisplayFormat("dd-MM-yyyy")
        start_datum_qdate = QDate(start_datum.year, start_datum.month, start_datum.day)
        self.start_datum_input.setDate(start_datum_qdate)
        self.start_datum_input.setStyleSheet(Styles.input_field())
        self.start_datum_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        form_layout.addRow("Nieuwe start datum:", self.start_datum_input)

        # Interval input
        self.interval_input.setMinimum(1)
        self.interval_input.setMaximum(365)
        self.interval_input.setValue(self.config['interval_dagen'])
        self.interval_input.setSuffix(" dagen")
        self.interval_input.setStyleSheet(Styles.input_field())
        self.interval_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        form_layout.addRow("Nieuw interval:", self.interval_input)

        # Actief vanaf datum
        self.actief_vanaf_input.setCalendarPopup(True)
        self.actief_vanaf_input.setDisplayFormat("dd-MM-yyyy")
        self.actief_vanaf_input.setDate(QDate.currentDate())
        self.actief_vanaf_input.setStyleSheet(Styles.input_field())
        self.actief_vanaf_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        form_layout.addRow("Actief vanaf:", self.actief_vanaf_input)

        layout.addLayout(form_layout)

        # Uitleg
        uitleg = QLabel(
            "LET OP:\n"
            "- Start datum bepaalt de eerste rode lijn datum\n"
            "- Interval bepaalt elke X dagen een nieuwe rode lijn\n"
            "- Actief vanaf bepaalt wanneer deze config gebruikt wordt voor validatie"
        )
        uitleg.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; "
            f"font-style: italic; "
            f"font-size: {Fonts.SIZE_SMALL}px; "
            f"padding: {Dimensions.SPACING_MEDIUM}px; "
            f"background-color: {Colors.BG_LIGHT}; "
            f"border-radius: {Dimensions.RADIUS_MEDIUM}px;"
        )
        uitleg.setWordWrap(True)
        layout.addWidget(uitleg)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        annuleer_btn = QPushButton("Annuleren")
        annuleer_btn.setStyleSheet(Styles.button_secondary())
        annuleer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        annuleer_btn.clicked.connect(self.reject)  # type: ignore
        button_layout.addWidget(annuleer_btn)

        opslaan_btn = QPushButton("Nieuwe Versie Opslaan")
        opslaan_btn.setStyleSheet(Styles.button_success())
        opslaan_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        opslaan_btn.clicked.connect(self.valideer_en_accept)  # type: ignore
        button_layout.addWidget(opslaan_btn)

        layout.addLayout(button_layout)

    def valideer_en_accept(self):
        """Valideer input voordat we accepteren"""
        nieuwe_start_datum = self.start_datum_input.date().toPyDate()
        oude_start_datum = datetime.fromisoformat(self.config['start_datum']).date()
        nieuwe_interval = self.interval_input.value()
        oude_interval = self.config['interval_dagen']

        # Check of er iets is gewijzigd
        if nieuwe_start_datum == oude_start_datum and nieuwe_interval == oude_interval:
            QMessageBox.warning(
                self,
                "Geen wijziging",
                "Er zijn geen wijzigingen doorgevoerd.\n"
                "Wijzig de start datum of interval, of annuleer."
            )
            return

        # Check datum in verleden
        gekozen_actief_vanaf = self.actief_vanaf_input.date().toPyDate()
        vandaag = datetime.now().date()

        if gekozen_actief_vanaf < vandaag:
            reply = QMessageBox.question(
                self,
                "Datum in verleden",
                f"De gekozen datum ({gekozen_actief_vanaf.strftime('%d-%m-%Y')}) ligt in het verleden.\n\n"
                "Dit betekent dat rode lijnen opnieuw gegenereerd moeten worden.\n"
                "Weet je zeker dat je wilt doorgaan?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.accept()

    def get_data(self) -> Dict[str, Any]:
        """Haal nieuwe data op"""
        start_datum = self.start_datum_input.date().toPyDate()
        actief_vanaf = self.actief_vanaf_input.date().toPyDate()

        return {
            'start_datum': start_datum.isoformat(),
            'interval_dagen': self.interval_input.value(),
            'actief_vanaf': actief_vanaf.isoformat()
        }
