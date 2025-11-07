# gui/dialogs/periode_definitie_edit_dialog.py
"""
Periode Definitie Edit Dialog
Generieke dialog voor week/weekend definitie met dag + uur selectie
"""
from typing import Dict, Any
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QLineEdit, QMessageBox, QFormLayout)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime
from gui.styles import Styles, Colors, Fonts, Dimensions


class PeriodeDefinitieEditDialog(QDialog):
    """Dialog voor bewerken week/weekend definitie met dag/uur selectie"""

    def __init__(self, parent, huidige_regel: Dict[str, Any]):
        super().__init__(parent)
        self.huidige_regel = huidige_regel

        # Parse huidige waarde: "ma-00:00|zo-23:59"
        self.parse_periode_waarde()

        # Instance attributes
        self.start_dag_combo: QComboBox = QComboBox()
        self.start_uur_input: QLineEdit = QLineEdit()
        self.eind_dag_combo: QComboBox = QComboBox()
        self.eind_uur_input: QLineEdit = QLineEdit()

        # Title bepalen obv regel naam
        titel = "Week Definitie" if "week" in huidige_regel['naam'].lower() else "Weekend Definitie"
        self.setWindowTitle(f"{titel} Wijzigen")
        self.setModal(True)
        self.setMinimumWidth(500)

        self.init_ui()

    def parse_periode_waarde(self):
        """Parse 'ma-00:00|zo-23:59' naar dict"""
        waarde = str(self.huidige_regel['waarde'])

        try:
            start, eind = waarde.split('|')

            # Parse start
            start_dag, start_uur = start.split('-', 1)
            self.start_dag = start_dag.strip()
            self.start_uur = start_uur.strip()

            # Parse eind
            eind_dag, eind_uur = eind.split('-', 1)
            self.eind_dag = eind_dag.strip()
            self.eind_uur = eind_uur.strip()

        except (ValueError, IndexError):
            # Fallback defaults
            self.start_dag = 'ma'
            self.start_uur = '00:00'
            self.eind_dag = 'zo'
            self.eind_uur = '23:59'

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Title
        is_week = "week" in self.huidige_regel['naam'].lower()
        title_text = "Wijzig Week Definitie" if is_week else "Wijzig Weekend Definitie"
        title = QLabel(title_text)
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_LARGE, QFont.Weight.Bold))
        layout.addWidget(title)

        # Info
        if is_week:
            info_text = (
                "Definieer wanneer een werkweek start en eindigt.\n"
                "Dit wordt gebruikt voor HR regels zoals 'Maximum 50 uur per week'."
            )
        else:
            info_text = (
                "Definieer wanneer een weekend start en eindigt.\n"
                "Dit kan per CAO verschillen (bijv. vrijdagmiddag tot zondagavond)."
            )

        info = QLabel(info_text)
        info.setStyleSheet(Styles.info_box())
        info.setWordWrap(True)
        layout.addWidget(info)

        # Form
        form = QFormLayout()
        form.setSpacing(Dimensions.SPACING_MEDIUM)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Dagen mapping (kort -> lang)
        dag_mapping = {
            'ma': 'Maandag', 'di': 'Dinsdag', 'wo': 'Woensdag', 'do': 'Donderdag',
            'vr': 'Vrijdag', 'za': 'Zaterdag', 'zo': 'Zondag'
        }
        dagen_kort = list(dag_mapping.keys())
        dagen_lang = list(dag_mapping.values())

        # Start dag
        self.start_dag_combo.addItems(dagen_lang)
        self.start_dag_combo.setStyleSheet(Styles.input_field())
        self.start_dag_combo.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        if self.start_dag in dagen_kort:
            self.start_dag_combo.setCurrentIndex(dagen_kort.index(self.start_dag))
        form.addRow("Start dag:", self.start_dag_combo)

        # Start uur
        self.start_uur_input.setText(self.start_uur)
        self.start_uur_input.setStyleSheet(Styles.input_field())
        self.start_uur_input.setPlaceholderText("HH:MM (bijv. 00:00)")
        self.start_uur_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        form.addRow("Start uur:", self.start_uur_input)

        # Eind dag
        self.eind_dag_combo.addItems(dagen_lang)
        self.eind_dag_combo.setStyleSheet(Styles.input_field())
        self.eind_dag_combo.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        if self.eind_dag in dagen_kort:
            self.eind_dag_combo.setCurrentIndex(dagen_kort.index(self.eind_dag))
        form.addRow("Eind dag:", self.eind_dag_combo)

        # Eind uur
        self.eind_uur_input.setText(self.eind_uur)
        self.eind_uur_input.setStyleSheet(Styles.input_field())
        self.eind_uur_input.setPlaceholderText("HH:MM (bijv. 23:59)")
        self.eind_uur_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        form.addRow("Eind uur:", self.eind_uur_input)

        layout.addLayout(form)

        # Actief vanaf (altijd vandaag voor nieuwe versie)
        actief_label = QLabel(f"Actief vanaf: {QDate.currentDate().toString('dd-MM-yyyy')}")
        actief_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")
        layout.addWidget(actief_label)

        # Voorbeelden
        if is_week:
            voorbeelden_text = (
                "<b>Voorbeelden:</b><br>"
                "• Standaard: Maandag 00:00 - Zondag 23:59<br>"
                "• CAO variant: Zondag 14:00 - Zondag 13:59<br>"
                "• Nachtdienst: Zondag 22:00 - Zondag 21:59"
            )
        else:
            voorbeelden_text = (
                "<b>Voorbeelden:</b><br>"
                "• Standaard: Zaterdag 00:00 - Zondag 23:59<br>"
                "• Vrijdagmiddag: Vrijdag 14:00 - Zondag 23:59<br>"
                "• Zaterdagochtend: Zaterdag 06:00 - Maandag 05:59"
            )

        voorbeelden = QLabel(voorbeelden_text)
        voorbeelden.setStyleSheet(
            f"background-color: {Colors.BG_LIGHT}; "
            f"padding: {Dimensions.SPACING_MEDIUM}px; "
            f"border-radius: {Dimensions.RADIUS_MEDIUM}px; "
            f"color: {Colors.TEXT_SECONDARY};"
        )
        voorbeelden.setWordWrap(True)
        layout.addWidget(voorbeelden)

        layout.addStretch()

        # Buttons
        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_btn = QPushButton("Annuleren")
        cancel_btn.setFixedSize(120, Dimensions.BUTTON_HEIGHT_NORMAL)
        cancel_btn.setStyleSheet(Styles.button_secondary())
        cancel_btn.clicked.connect(self.reject)  # type: ignore
        buttons.addWidget(cancel_btn)

        save_btn = QPushButton("Opslaan")
        save_btn.setFixedSize(120, Dimensions.BUTTON_HEIGHT_NORMAL)
        save_btn.setStyleSheet(Styles.button_primary())
        save_btn.clicked.connect(self.save)  # type: ignore
        buttons.addWidget(save_btn)

        layout.addLayout(buttons)

    def validate_tijd(self, tijd_str: str) -> bool:
        """Valideer HH:MM formaat"""
        try:
            parts = tijd_str.split(':')
            if len(parts) != 2:
                return False

            uur = int(parts[0])
            minuut = int(parts[1])

            return 0 <= uur <= 23 and 0 <= minuut <= 59

        except (ValueError, AttributeError):
            return False

    def save(self):
        """Valideer en save data"""
        start_uur = self.start_uur_input.text().strip()
        eind_uur = self.eind_uur_input.text().strip()

        # Validatie
        if not self.validate_tijd(start_uur):
            QMessageBox.warning(
                self,
                "Validatie Fout",
                "Start uur moet formaat HH:MM hebben (bijv. 00:00, 14:30)"
            )
            return

        if not self.validate_tijd(eind_uur):
            QMessageBox.warning(
                self,
                "Validatie Fout",
                "Eind uur moet formaat HH:MM hebben (bijv. 23:59, 13:59)"
            )
            return

        # Dagen mapping
        dagen_kort = ['ma', 'di', 'wo', 'do', 'vr', 'za', 'zo']
        start_dag = dagen_kort[self.start_dag_combo.currentIndex()]
        eind_dag = dagen_kort[self.eind_dag_combo.currentIndex()]

        # Bouw nieuwe waarde
        nieuwe_waarde = f"{start_dag}-{start_uur}|{eind_dag}-{eind_uur}"

        # Check of er wijziging is
        if nieuwe_waarde == self.huidige_regel['waarde']:
            QMessageBox.information(
                self,
                "Geen Wijziging",
                "Er zijn geen wijzigingen doorgevoerd."
            )
            return

        # Bevestiging
        dagen_lang = {
            'ma': 'Maandag', 'di': 'Dinsdag', 'wo': 'Woensdag', 'do': 'Donderdag',
            'vr': 'Vrijdag', 'za': 'Zaterdag', 'zo': 'Zondag'
        }

        reply = QMessageBox.question(
            self,
            "Bevestig Wijziging",
            f"Nieuwe definitie:\n\n"
            f"Start: {dagen_lang[start_dag]} {start_uur}\n"
            f"Eind: {dagen_lang[eind_dag]} {eind_uur}\n\n"
            f"Actief vanaf: {QDate.currentDate().toString('dd-MM-yyyy')}\n\n"
            f"De oude definitie wordt gearchiveerd.\n"
            f"Doorgaan?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.accept()

    def get_data(self) -> Dict[str, Any]:
        """Haal data op uit form"""
        dagen_kort = ['ma', 'di', 'wo', 'do', 'vr', 'za', 'zo']
        start_dag = dagen_kort[self.start_dag_combo.currentIndex()]
        eind_dag = dagen_kort[self.eind_dag_combo.currentIndex()]

        start_uur = self.start_uur_input.text().strip()
        eind_uur = self.eind_uur_input.text().strip()

        return {
            'waarde': f"{start_dag}-{start_uur}|{eind_dag}-{eind_uur}",
            'actief_vanaf': datetime.now().isoformat()
        }
