# gui/dialogs/werkpost_naam_dialog.py
"""
Werkpost Naam Dialog
Simpele dialog voor naam en beschrijving werkpost
"""
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QTextEdit, QFormLayout,
                             QMessageBox)
from PyQt6.QtGui import QFont
from gui.styles import Styles, Colors, Fonts, Dimensions


class WerkpostNaamDialog(QDialog):
    """Dialog voor naam en beschrijving werkpost"""

    def __init__(self, parent, werkpost: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.werkpost = werkpost
        self.edit_mode = werkpost is not None

        self.setWindowTitle("Werkpost Bewerken" if self.edit_mode else "Nieuwe Werkpost")
        self.setModal(True)
        self.setMinimumWidth(500)

        # Instance attributes
        self.naam_input: QLineEdit = QLineEdit()
        self.beschrijving_input: QTextEdit = QTextEdit()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Title
        title = QLabel("Werkpost Gegevens")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(title)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Naam
        self.naam_input.setPlaceholderText("Bijv. Interventie, Dispatching, Preventie")
        if self.edit_mode and self.werkpost:
            self.naam_input.setText(self.werkpost['naam'])
        self.naam_input.setStyleSheet(Styles.input_field())
        form_layout.addRow("Naam:", self.naam_input)

        # Beschrijving
        self.beschrijving_input.setPlaceholderText("Optionele beschrijving...")
        self.beschrijving_input.setMaximumHeight(100)
        if self.edit_mode and self.werkpost and self.werkpost['beschrijving']:
            self.beschrijving_input.setPlainText(self.werkpost['beschrijving'])
        self.beschrijving_input.setStyleSheet(Styles.input_field())
        form_layout.addRow("Beschrijving:", self.beschrijving_input)

        layout.addLayout(form_layout)

        # Info
        if not self.edit_mode:
            info = QLabel(
                "Na het opslaan kun je de shift codes configureren."
            )
            info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")
            layout.addWidget(info)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        annuleer_btn = QPushButton("Annuleren")
        annuleer_btn.setStyleSheet(Styles.button_secondary())
        annuleer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        annuleer_btn.clicked.connect(self.reject)  # type: ignore
        button_layout.addWidget(annuleer_btn)

        if self.edit_mode:
            opslaan_btn = QPushButton("Opslaan")
        else:
            opslaan_btn = QPushButton("Volgende")

        opslaan_btn.setStyleSheet(Styles.button_success())
        opslaan_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        opslaan_btn.clicked.connect(self.valideer_en_accept)  # type: ignore
        button_layout.addWidget(opslaan_btn)

        layout.addLayout(button_layout)

    def valideer_en_accept(self):
        """Valideer input"""
        if not self.naam_input.text().strip():
            QMessageBox.warning(self, "Fout", "Naam is verplicht!")
            return

        self.accept()

    def get_data(self) -> Dict[str, Any]:
        """Haal data op"""
        return {
            'naam': self.naam_input.text().strip(),
            'beschrijving': self.beschrijving_input.toPlainText().strip()
        }