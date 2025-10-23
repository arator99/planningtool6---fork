"""
Verlof Saldo Widget
Versie: 0.6.10

Read-only widget voor weergave van verlof en KD saldo (teamlid view).
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtGui import QFont
from datetime import datetime

from gui.styles import Colors, Fonts, Dimensions
from services.verlof_saldo_service import VerlofSaldoService
from services.term_code_service import TermCodeService


class VerlofSaldoWidget(QWidget):
    """Widget voor weergave van verlof en KD saldo"""

    def __init__(self, gebruiker_id: int, jaar: int = None, parent=None):
        super().__init__(parent)
        self.gebruiker_id: int = gebruiker_id
        self.jaar: int = jaar or datetime.now().year

        self.init_ui()
        self.load_saldo()

    def init_ui(self):
        """Initialiseer UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Dimensions.SPACING_MEDIUM,
            Dimensions.SPACING_MEDIUM,
            Dimensions.SPACING_MEDIUM,
            Dimensions.SPACING_MEDIUM
        )
        layout.setSpacing(Dimensions.SPACING_SMALL)

        # Container frame
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_LIGHT};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 4px;
                padding: {Dimensions.SPACING_MEDIUM}px;
            }}
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setSpacing(Dimensions.SPACING_SMALL)

        # Title
        title = QLabel(f"Mijn Saldo - {self.jaar}")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        frame_layout.addWidget(title)

        # Verlof section
        self.verlof_label = QLabel()
        self.verlof_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        self.verlof_label.setWordWrap(True)
        self.verlof_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        frame_layout.addWidget(self.verlof_label)

        # KD section
        self.kd_label = QLabel()
        self.kd_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        self.kd_label.setWordWrap(True)
        self.kd_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        frame_layout.addWidget(self.kd_label)

        # Warning label (voor overgedragen verlof vervaldatum)
        self.warning_label = QLabel()
        self.warning_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY))
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet(f"color: {Colors.WARNING};")
        self.warning_label.setVisible(False)
        frame_layout.addWidget(self.warning_label)

        layout.addWidget(frame)

    def load_saldo(self):
        """Laad en toon saldo"""
        saldo = VerlofSaldoService.get_saldo(self.gebruiker_id, self.jaar)

        verlof_code = TermCodeService.get_code_for_term('verlof')
        kd_code = TermCodeService.get_code_for_term('kompensatiedag')

        # Verlof text
        verlof_text = (
            f"<b>VERLOF ({verlof_code}):</b> {saldo['vv_resterend']} dagen resterend<br>"
            f"Jaarlijks: {saldo['vv_totaal']} | Overdracht uit vorig jaar: {saldo['vv_overgedragen']}<br>"
            f"Opgenomen: {saldo['vv_opgenomen']}"
        )
        self.verlof_label.setText(verlof_text)

        # KD text
        kd_text = (
            f"<b>KD ({kd_code}):</b> {saldo['kd_resterend']} dagen resterend<br>"
            f"Jaarlijks: {saldo['kd_totaal']} | Overdracht uit voorgaande jaren: {saldo['kd_overgedragen']}<br>"
            f"Opgenomen: {saldo['kd_opgenomen']}"
        )
        self.kd_label.setText(kd_text)

        # Check voor overgedragen verlof vervaldatum (1 mei)
        if saldo['vv_overgedragen'] > 0:
            today = datetime.now().date()
            current_year = today.year
            vervaldatum = datetime(current_year, 5, 1).date()  # 1 mei

            if today < vervaldatum:
                dagen_tot_verval = (vervaldatum - today).days
                self.warning_label.setText(
                    f"Let op: Overgedragen verlof ({saldo['vv_overgedragen']} dagen) "
                    f"vervalt op 1 mei {current_year} (nog {dagen_tot_verval} dagen)"
                )
                self.warning_label.setVisible(True)
            # Als na 1 mei, toon geen warning (zou al vervallen moeten zijn)

    def refresh(self):
        """Ververs saldo (na wijziging)"""
        self.load_saldo()
