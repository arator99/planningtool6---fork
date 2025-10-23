# gui/dialogs/speciale_code_dialog.py
"""
Speciale Code Dialog
Voor toevoegen/bewerken van globale speciale codes
"""
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QCheckBox, QFormLayout,
                             QMessageBox)
from PyQt6.QtGui import QFont
from gui.styles import Styles, Colors, Fonts, Dimensions


class SpecialeCodeDialog(QDialog):
    """Dialog voor toevoegen/bewerken speciale code"""

    def __init__(self, parent, code: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.code = code
        self.edit_mode = code is not None

        self.setWindowTitle("Code Bewerken" if self.edit_mode else "Nieuwe Speciale Code")
        self.setModal(True)
        self.setMinimumWidth(450)

        # Instance attributes
        self.code_input: QLineEdit = QLineEdit()
        self.naam_input: QLineEdit = QLineEdit()
        self.werkdag_check: QCheckBox = QCheckBox("Telt als werkdag")
        self.reset_check: QCheckBox = QCheckBox("Reset 12u rust regel")
        self.breekt_check: QCheckBox = QCheckBox("Breekt werkreeks")

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Title
        if self.edit_mode:
            title = QLabel(f"Bewerken: {self.code['code']}")
        else:
            title = QLabel("Nieuwe Speciale Code")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(title)

        # Waarschuwing voor systeemcodes
        # code is dict() hier (komt van dict(code) in shift_codes_screen.py)
        if self.edit_mode and self.code and self.code.get('term'):
            systeem_info = QLabel(
                f"SYSTEEMCODE: Deze code wordt gebruikt voor '{self.code.get('term')}'.\n"
                f"Je kunt de code wijzigen (bijv. VV naar VL), maar de functionaliteit blijft behouden."
            )
            systeem_info.setStyleSheet(
                f"color: {Colors.WARNING}; "
                f"font-weight: bold; "
                f"padding: {Dimensions.SPACING_MEDIUM}px; "
                f"background-color: rgba(255, 193, 7, 0.1); "
                f"border: 1px solid {Colors.WARNING}; "
                f"border-radius: {Dimensions.RADIUS_MEDIUM}px;"
            )
            systeem_info.setWordWrap(True)
            layout.addWidget(systeem_info)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Code
        self.code_input.setMaxLength(5)
        self.code_input.setPlaceholderText("Bijv. VV, RX, DA")
        self.code_input.textChanged.connect(self.on_code_changed)  # type: ignore
        if self.edit_mode and self.code:
            self.code_input.setText(self.code['code'])
        self.code_input.setStyleSheet(Styles.input_field())
        form_layout.addRow("Code:", self.code_input)

        # Naam
        self.naam_input.setPlaceholderText("Bijv. Verlof, Zondagsrust")
        if self.edit_mode and self.code:
            self.naam_input.setText(self.code['naam'])
        self.naam_input.setStyleSheet(Styles.input_field())
        form_layout.addRow("Naam:", self.naam_input)

        layout.addLayout(form_layout)

        # Eigenschappen
        props_group = QVBoxLayout()
        props_group.setSpacing(Dimensions.SPACING_SMALL)

        props_label = QLabel("Eigenschappen:")
        props_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        props_group.addWidget(props_label)

        if self.edit_mode and self.code:
            self.werkdag_check.setChecked(bool(self.code['telt_als_werkdag']))
            self.reset_check.setChecked(bool(self.code['reset_12u_rust']))
            self.breekt_check.setChecked(bool(self.code['breekt_werk_reeks']))

        props_group.addWidget(self.werkdag_check)
        props_group.addWidget(self.reset_check)
        props_group.addWidget(self.breekt_check)

        layout.addLayout(props_group)

        # Info voorbeelden
        info = QLabel(
            "Voorbeelden:\n"
            "• VV (Verlof): Werkdag ✓, Reset ✓, Breekt ✗\n"
            "• RX (Zondagsrust): Werkdag ✗, Reset ✗, Breekt ✓\n"
            "• Z (Ziek): Werkdag ✗, Reset ✓, Breekt ✓"
        )
        info.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; "
            f"font-style: italic; "
            f"font-size: {Fonts.SIZE_SMALL}px; "
            f"padding: {Dimensions.SPACING_MEDIUM}px; "
            f"background-color: {Colors.BG_LIGHT}; "
            f"border-radius: {Dimensions.RADIUS_MEDIUM}px;"
        )
        layout.addWidget(info)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        annuleer_btn = QPushButton("Annuleren")
        annuleer_btn.setStyleSheet(Styles.button_secondary())
        annuleer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        annuleer_btn.clicked.connect(self.reject)  # type: ignore
        button_layout.addWidget(annuleer_btn)

        opslaan_btn = QPushButton("Opslaan")
        opslaan_btn.setStyleSheet(Styles.button_success())
        opslaan_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        opslaan_btn.clicked.connect(self.valideer_en_accept)  # type: ignore
        button_layout.addWidget(opslaan_btn)

        layout.addLayout(button_layout)

    def on_code_changed(self, text: str):
        """Auto-uppercase code"""
        cursor_pos = self.code_input.cursorPosition()
        self.code_input.setText(text.upper())
        self.code_input.setCursorPosition(cursor_pos)

    def valideer_en_accept(self):
        """Valideer input"""
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "Fout", "Code is verplicht!")
            return

        if not self.naam_input.text().strip():
            QMessageBox.warning(self, "Fout", "Naam is verplicht!")
            return

        self.accept()

    def get_data(self) -> Dict[str, Any]:
        """Haal data op"""
        return {
            'code': self.code_input.text().strip().upper(),
            'naam': self.naam_input.text().strip(),
            'telt_als_werkdag': self.werkdag_check.isChecked(),
            'reset_12u_rust': self.reset_check.isChecked(),
            'breekt_werk_reeks': self.breekt_check.isChecked()
        }