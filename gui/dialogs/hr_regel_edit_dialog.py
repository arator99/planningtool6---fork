# gui/dialogs/hr_regel_edit_dialog.py
"""
HR Regel Edit Dialog
Voor het wijzigen van HR regels met nieuwe versie + datum
"""
from typing import Dict, Any
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QDoubleSpinBox, QDateEdit,
                             QFormLayout, QMessageBox)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QFont
from datetime import datetime
from gui.styles import Styles, Colors, Fonts, Dimensions


class HRRegelEditDialog(QDialog):
    """Dialog voor het wijzigen van een HR regel"""

    def __init__(self, parent, regel: Dict[str, Any]):
        super().__init__(parent)
        self.regel = regel

        self.setWindowTitle(f"HR Regel Wijzigen: {regel['naam']}")
        self.setModal(True)
        self.setMinimumWidth(500)

        # Instance attributes
        self.waarde_input: QDoubleSpinBox = QDoubleSpinBox()
        self.datum_input: QDateEdit = QDateEdit()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Title
        naam_display = self.regel['naam'].replace('_', ' ').title()
        title = QLabel(f"Wijzig: {naam_display}")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(title)

        # Info box
        info = QLabel(
            "Bij wijzigen wordt een nieuwe versie aangemaakt.\n"
            "De oude regel wordt gearchiveerd met einddatum = nieuwe startdatum."
        )
        info.setStyleSheet(Styles.info_box())
        info.setWordWrap(True)
        layout.addWidget(info)

        # Huidige waarde
        huidig_group = QVBoxLayout()
        huidig_label = QLabel("HUIDIGE WAARDE:")
        huidig_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        huidig_group.addWidget(huidig_label)

        huidige_waarde = QLabel(
            f"{self.regel['waarde']} {self.regel['eenheid']}"
        )
        huidige_waarde.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_LARGE))
        huidige_waarde.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        huidig_group.addWidget(huidige_waarde)

        # Actief vanaf
        if self.regel.get('actief_vanaf'):
            datum = datetime.fromisoformat(self.regel['actief_vanaf'])
            datum_str = datum.strftime('%d-%m-%Y')
            vanaf_label = QLabel(f"Actief vanaf: {datum_str}")
            vanaf_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: {Fonts.SIZE_SMALL}px;")
            huidig_group.addWidget(vanaf_label)

        layout.addLayout(huidig_group)

        # Nieuwe waarde form
        form_layout = QFormLayout()
        form_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Nieuwe waarde input
        self.waarde_input.setMinimum(0.0)
        self.waarde_input.setMaximum(9999.0)
        self.waarde_input.setDecimals(1)
        self.waarde_input.setValue(self.regel['waarde'])
        self.waarde_input.setSuffix(f" {self.regel['eenheid']}")
        self.waarde_input.setStyleSheet(Styles.input_field())
        self.waarde_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        form_layout.addRow("Nieuwe waarde:", self.waarde_input)

        # Actief vanaf datum
        self.datum_input.setCalendarPopup(True)
        self.datum_input.setDisplayFormat("dd-MM-yyyy")
        self.datum_input.setDate(QDate.currentDate())
        self.datum_input.setStyleSheet(Styles.input_field())
        self.datum_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        form_layout.addRow("Actief vanaf:", self.datum_input)

        layout.addLayout(form_layout)

        # Beschrijving tonen
        if self.regel.get('beschrijving'):
            beschrijving_clean = self.regel['beschrijving'].replace('VOORBEELD - ', '')
            beschrijving = QLabel(f"Beschrijving: {beschrijving_clean}")
            beschrijving.setStyleSheet(
                f"color: {Colors.TEXT_SECONDARY}; "
                f"font-style: italic; "
                f"font-size: {Fonts.SIZE_SMALL}px; "
                f"padding: {Dimensions.SPACING_MEDIUM}px; "
                f"background-color: {Colors.BG_LIGHT}; "
                f"border-radius: {Dimensions.RADIUS_MEDIUM}px;"
            )
            beschrijving.setWordWrap(True)
            layout.addWidget(beschrijving)

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
        nieuwe_waarde = self.waarde_input.value()
        oude_waarde = self.regel['waarde']

        # Check of waarde is gewijzigd
        if nieuwe_waarde == oude_waarde:
            QMessageBox.warning(
                self,
                "Geen wijziging",
                "De nieuwe waarde is hetzelfde als de huidige waarde.\n"
                "Wijzig de waarde of annuleer."
            )
            return

        # Check datum in verleden
        gekozen_datum = self.datum_input.date().toPyDate()
        vandaag = datetime.now().date()

        if gekozen_datum < vandaag:
            reply = QMessageBox.question(
                self,
                "Datum in verleden",
                f"De gekozen datum ({gekozen_datum.strftime('%d-%m-%Y')}) ligt in het verleden.\n\n"
                "Dit betekent dat planning vanaf die datum opnieuw gevalideerd moet worden.\n"
                "Weet je zeker dat je wilt doorgaan?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.accept()

    def get_data(self) -> Dict[str, Any]:
        """Haal nieuwe data op"""
        datum = self.datum_input.date().toPyDate()

        return {
            'waarde': self.waarde_input.value(),
            'actief_vanaf': datum.isoformat()
        }
