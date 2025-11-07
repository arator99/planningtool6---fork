"""
Verlof Saldo Widget
Versie: 0.6.23

Read-only widget voor weergave van verlof en KD saldo (teamlid view).
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtGui import QFont
from datetime import datetime

from gui.styles import Colors, Fonts, Dimensions
from services.verlof_saldo_service import VerlofSaldoService
from services.term_code_service import TermCodeService
from services.hr_regels_service import HRRegelsService


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

        # Check voor overgedragen verlof vervaldatum (uit HR regels)
        # FIFO principe: overgedragen verlof wordt eerst opgenomen
        overgedragen = saldo['vv_overgedragen']
        opgenomen = saldo['vv_opgenomen']

        # Bereken restant overgedragen verlof (wat nog niet ingepland/opgenomen is)
        restant_overgedragen = max(0, overgedragen - opgenomen)

        if restant_overgedragen > 0:
            today = datetime.now().date()
            current_year = today.year
            vervaldatum = HRRegelsService.get_verlof_vervaldatum(current_year)

            # Warning window: 1 januari t/m vervaldatum (niet het hele jaar)
            warning_start = datetime(current_year, 1, 1).date()

            if warning_start <= today < vervaldatum:
                dagen_tot_verval = (vervaldatum - today).days
                # Format vervaldatum leesbaar (1 mei, 15 juni, etc.)
                maand_naam = vervaldatum.strftime("%B").lower()
                dag = vervaldatum.day
                vervaldatum_str = f"{dag} {maand_naam}"

                self.warning_label.setText(
                    f"Let op: Overgedragen verlof ({restant_overgedragen} dagen) "
                    f"vervalt op {vervaldatum_str} {current_year} (nog {dagen_tot_verval} dagen)"
                )
                self.warning_label.setVisible(True)
            # Als voor 1 januari of na vervaldatum: geen warning

    def refresh(self):
        """Ververs saldo (na wijziging)"""
        self.load_saldo()
