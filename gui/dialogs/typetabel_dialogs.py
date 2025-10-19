#gui/dialogs/typetabel_dialogs.py

"""
Typetabel Dialogs
Dialogs voor typetabel beheer
"""
from typing import Dict, Any
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QSpinBox, QTextEdit, QMessageBox)
from PyQt6.QtGui import QFont
from gui.styles import Styles, Fonts, Dimensions


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
        weken_info.setStyleSheet(f"color: #666;")
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