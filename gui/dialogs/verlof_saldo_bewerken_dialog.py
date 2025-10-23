"""
Verlof Saldo Bewerken Dialog
Versie: 0.6.10

Dialog voor bewerken van verlof en KD saldi per gebruiker.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QTextEdit, QGroupBox, QMessageBox
)
from PyQt6.QtGui import QFont

from gui.styles import Styles, Colors, Fonts, Dimensions
from services.verlof_saldo_service import VerlofSaldoService
from services.term_code_service import TermCodeService


class VerlofSaldoBewerkenDialog(QDialog):
    """Dialog voor bewerken van verlof en KD saldo"""

    def __init__(self, gebruiker_id: int, naam: str, jaar: int,
                 vv_totaal: int, vv_overgedragen: int,
                 kd_totaal: int, kd_overgedragen: int,
                 opmerking: str, parent=None):
        super().__init__(parent)

        self.gebruiker_id: int = gebruiker_id
        self.naam: str = naam
        self.jaar: int = jaar

        # Spinboxes
        self.vv_totaal_spin: QSpinBox
        self.vv_overgedragen_spin: QSpinBox
        self.kd_totaal_spin: QSpinBox
        self.kd_overgedragen_spin: QSpinBox
        self.opmerking_edit: QTextEdit

        self.init_ui()

        # Vul waarden in
        self.vv_totaal_spin.setValue(vv_totaal)
        self.vv_overgedragen_spin.setValue(vv_overgedragen)
        self.kd_totaal_spin.setValue(kd_totaal)
        self.kd_overgedragen_spin.setValue(kd_overgedragen)
        self.opmerking_edit.setPlainText(opmerking)

    def init_ui(self):
        """Initialiseer UI"""
        self.setWindowTitle(f"Saldo Bewerken - {self.naam} - {self.jaar}")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Title
        title = QLabel(f"Saldo Bewerken: {self.naam}")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(title)

        subtitle = QLabel(f"Jaar: {self.jaar}")
        subtitle.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(subtitle)

        # Verlof groep
        verlof_code = TermCodeService.get_code_for_term('verlof')
        verlof_group = QGroupBox(f"Verlof ({verlof_code})")
        verlof_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        verlof_layout = QVBoxLayout()

        # VV Totaal
        vv_totaal_layout = QHBoxLayout()
        vv_totaal_label = QLabel("Jaarlijks contingent:")
        vv_totaal_label.setMinimumWidth(180)
        vv_totaal_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: normal;")
        vv_totaal_layout.addWidget(vv_totaal_label)

        self.vv_totaal_spin = QSpinBox()
        self.vv_totaal_spin.setMinimum(0)
        self.vv_totaal_spin.setMaximum(100)
        self.vv_totaal_spin.setSuffix(" dagen")
        self.vv_totaal_spin.setStyleSheet(Styles.input_field())
        vv_totaal_layout.addWidget(self.vv_totaal_spin)
        vv_totaal_layout.addStretch()
        verlof_layout.addLayout(vv_totaal_layout)

        # VV Overgedragen
        vv_overgedragen_layout = QHBoxLayout()
        vv_overgedragen_label = QLabel("Overgedragen van vorig jaar:")
        vv_overgedragen_label.setMinimumWidth(180)
        vv_overgedragen_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: normal;")
        vv_overgedragen_layout.addWidget(vv_overgedragen_label)

        self.vv_overgedragen_spin = QSpinBox()
        self.vv_overgedragen_spin.setMinimum(0)
        self.vv_overgedragen_spin.setMaximum(100)
        self.vv_overgedragen_spin.setSuffix(" dagen")
        self.vv_overgedragen_spin.setStyleSheet(Styles.input_field())
        vv_overgedragen_layout.addWidget(self.vv_overgedragen_spin)
        vv_overgedragen_layout.addStretch()
        verlof_layout.addLayout(vv_overgedragen_layout)

        # Info
        vv_info = QLabel("Vervalt op 1 mei (HR-regel)")
        vv_info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px; font-weight: normal;")
        verlof_layout.addWidget(vv_info)

        verlof_group.setLayout(verlof_layout)
        layout.addWidget(verlof_group)

        # KD groep
        kd_code = TermCodeService.get_code_for_term('kompensatiedag')
        kd_group = QGroupBox(f"Kompensatiedagen ({kd_code})")
        kd_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        kd_layout = QVBoxLayout()

        # KD Totaal
        kd_totaal_layout = QHBoxLayout()
        kd_totaal_label = QLabel("Jaarlijks contingent:")
        kd_totaal_label.setMinimumWidth(180)
        kd_totaal_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: normal;")
        kd_totaal_layout.addWidget(kd_totaal_label)

        self.kd_totaal_spin = QSpinBox()
        self.kd_totaal_spin.setMinimum(0)
        self.kd_totaal_spin.setMaximum(50)
        self.kd_totaal_spin.setSuffix(" dagen")
        self.kd_totaal_spin.setStyleSheet(Styles.input_field())
        kd_totaal_layout.addWidget(self.kd_totaal_spin)
        kd_totaal_layout.addStretch()
        kd_layout.addLayout(kd_totaal_layout)

        # KD Overgedragen
        kd_overgedragen_layout = QHBoxLayout()
        kd_overgedragen_label = QLabel("Overgedragen van vorig jaar:")
        kd_overgedragen_label.setMinimumWidth(180)
        kd_overgedragen_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: normal;")
        kd_overgedragen_layout.addWidget(kd_overgedragen_label)

        self.kd_overgedragen_spin = QSpinBox()
        self.kd_overgedragen_spin.setMinimum(0)
        self.kd_overgedragen_spin.setMaximum(35)
        self.kd_overgedragen_spin.setSuffix(" dagen")
        self.kd_overgedragen_spin.setStyleSheet(Styles.input_field())
        kd_overgedragen_layout.addWidget(self.kd_overgedragen_spin)
        kd_overgedragen_layout.addStretch()
        kd_layout.addLayout(kd_overgedragen_layout)

        # Info
        kd_info = QLabel("Max 35 dagen overdraagbaar (HR-regel)")
        kd_info.setStyleSheet(f"color: {Colors.WARNING}; font-size: 11px; font-weight: normal;")
        kd_layout.addWidget(kd_info)

        kd_group.setLayout(kd_layout)
        layout.addWidget(kd_group)

        # Opmerking
        opmerking_label = QLabel("Opmerking (optioneel):")
        opmerking_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(opmerking_label)

        self.opmerking_edit = QTextEdit()
        self.opmerking_edit.setMaximumHeight(60)
        self.opmerking_edit.setPlaceholderText("Bv. '80% deeltijd' of '65+ regime'")
        self.opmerking_edit.setStyleSheet(Styles.input_field())
        layout.addWidget(self.opmerking_edit)

        # Info label
        info = QLabel(
            "Opgenomen dagen worden automatisch berekend uit goedgekeurde verlof aanvragen."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px; padding: 8px;")
        layout.addWidget(info)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        annuleren_btn = QPushButton("Annuleren")
        annuleren_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        annuleren_btn.setStyleSheet(Styles.button_secondary())
        annuleren_btn.clicked.connect(self.reject)  # type: ignore
        button_layout.addWidget(annuleren_btn)

        opslaan_btn = QPushButton("Opslaan")
        opslaan_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        opslaan_btn.setStyleSheet(Styles.button_primary())
        opslaan_btn.clicked.connect(self.opslaan)  # type: ignore
        button_layout.addWidget(opslaan_btn)

        layout.addLayout(button_layout)

    def opslaan(self):
        """Sla saldo op"""
        # Validatie: KD overdracht max 35
        kd_overgedragen = self.kd_overgedragen_spin.value()
        if kd_overgedragen > 35:
            QMessageBox.warning(
                self,
                "Validatie Fout",
                "Maximaal 35 KD dagen kunnen worden overgedragen (HR-regel)."
            )
            return

        # Haal waarden op
        vv_totaal = self.vv_totaal_spin.value()
        vv_overgedragen = self.vv_overgedragen_spin.value()
        kd_totaal = self.kd_totaal_spin.value()
        opmerking = self.opmerking_edit.toPlainText().strip()

        # Opslaan via service
        success = VerlofSaldoService.update_saldo(
            gebruiker_id=self.gebruiker_id,
            jaar=self.jaar,
            vv_totaal=vv_totaal,
            vv_overgedragen=vv_overgedragen,
            kd_totaal=kd_totaal,
            kd_overgedragen=kd_overgedragen,
            opmerking=opmerking
        )

        if success:
            QMessageBox.information(
                self,
                "Succes",
                f"Saldo voor {self.naam} ({self.jaar}) is opgeslagen."
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Fout",
                "Fout bij opslaan van saldo. Probeer opnieuw."
            )
