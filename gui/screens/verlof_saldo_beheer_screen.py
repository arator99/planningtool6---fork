"""
Verlof & KD Saldo Beheer Scherm
Versie: 0.6.10

Admin scherm voor beheer van verlof en kompensatiedagen saldi per gebruiker.
"""

from typing import Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime

from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
from services.verlof_saldo_service import VerlofSaldoService
from services.term_code_service import TermCodeService


class VerlofSaldoBeheerScreen(QWidget):
    """Scherm voor beheer van verlof en KD saldi"""

    def __init__(self, router: Callable):
        super().__init__()
        self.router: Callable = router
        self.current_jaar: int = datetime.now().year
        self.saldi_data: list[dict] = []

        self.jaar_combo: QComboBox
        self.table: QTableWidget
        self.status_label: QLabel

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialiseer UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)
        layout.setContentsMargins(
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE
        )

        # Header met titel en terug knop
        header_layout = QHBoxLayout()

        title = QLabel("Verlof & KD Saldo Beheer")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Terug knop rechtsboven (consistent met andere schermen)
        terug_btn = QPushButton("Terug")
        terug_btn.setFixedWidth(120)
        terug_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        terug_btn.setStyleSheet(Styles.button_secondary())
        terug_btn.clicked.connect(self.router)  # type: ignore
        header_layout.addWidget(terug_btn)

        layout.addLayout(header_layout)

        # Info text
        info_text = QLabel(
            "Beheer verlof en kompensatiedagen saldi per gebruiker. "
            "Opgenomen dagen worden automatisch berekend uit goedgekeurde aanvragen."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: 8px;")
        layout.addWidget(info_text)

        # Toolbar met jaar selector
        toolbar = QHBoxLayout()

        # Jaar selector
        jaar_label = QLabel("Jaar:")
        jaar_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: bold;")
        toolbar.addWidget(jaar_label)

        self.jaar_combo = QComboBox()
        self.jaar_combo.setStyleSheet(Styles.input_field())
        self.jaar_combo.setMinimumWidth(100)

        # Vullen jaren: vorig, huidig, volgend
        current_year = datetime.now().year
        for jaar in range(current_year - 1, current_year + 2):
            self.jaar_combo.addItem(str(jaar), jaar)
            if jaar == current_year:
                self.jaar_combo.setCurrentIndex(self.jaar_combo.count() - 1)

        self.jaar_combo.currentIndexChanged.connect(self.on_jaar_changed)  # type: ignore
        toolbar.addWidget(self.jaar_combo)

        toolbar.addSpacing(Dimensions.SPACING_LARGE)

        nieuw_jaar_btn = QPushButton("Nieuw Jaar Aanmaken")
        nieuw_jaar_btn.setStyleSheet(Styles.button_primary())
        nieuw_jaar_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        nieuw_jaar_btn.clicked.connect(self.nieuw_jaar_aanmaken)  # type: ignore
        toolbar.addWidget(nieuw_jaar_btn)

        toolbar.addStretch()

        refresh_btn = QPushButton("Vernieuwen")
        refresh_btn.setStyleSheet(Styles.button_secondary())
        refresh_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        refresh_btn.clicked.connect(self.load_data)  # type: ignore
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # Tabel
        self.table = QTableWidget()
        TableConfig.setup_table_widget(self.table, row_height=80)

        # Kolommen
        columns = [
            "Gebruiker",
            f"Verlof ({TermCodeService.get_code_for_term('verlof')})",
            f"KD ({TermCodeService.get_code_for_term('kompensatiedag')})",
            "Opmerking",
            "Acties"
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        # Kolom breedtes
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(0, 200)  # Gebruiker
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Verlof
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # KD
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(3, 150)  # Opmerking
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(4, 120)  # Acties

        layout.addWidget(self.table)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(self.status_label)

    def on_jaar_changed(self):
        """Jaar geselecteerd gewijzigd"""
        self.current_jaar = self.jaar_combo.currentData()
        self.load_data()

    def load_data(self):
        """Laad saldi data voor huidige jaar"""
        self.saldi_data = VerlofSaldoService.get_alle_saldi(self.current_jaar)
        self.update_table()

        # Update status
        self.status_label.setText(
            f"{len(self.saldi_data)} gebruikers - "
            f"Laatste update: {datetime.now().strftime('%H:%M:%S')}"
        )

    def update_table(self):
        """Update tabel met saldi data"""
        self.table.setRowCount(len(self.saldi_data))

        for row_idx, saldo in enumerate(self.saldi_data):
            # Kolom 0: Gebruiker info
            gebruiker_text = f"{saldo['naam']}\n{saldo['gebruikersnaam']}"
            if saldo['is_reserve']:
                gebruiker_text += "\n(Reserve)"

            gebruiker_item = QTableWidgetItem(gebruiker_text)
            gebruiker_item.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
            self.table.setItem(row_idx, 0, gebruiker_item)

            # Kolom 1: Verlof info
            vv_text = self._format_saldo_text(
                saldo['vv_totaal'],
                saldo['vv_overgedragen'],
                saldo['vv_opgenomen'],
                saldo['vv_resterend']
            )
            vv_item = QTableWidgetItem(vv_text)
            vv_item.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
            if saldo['vv_resterend'] < 0:
                vv_item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row_idx, 1, vv_item)

            # Kolom 2: KD info
            kd_text = self._format_saldo_text(
                saldo['kd_totaal'],
                saldo['kd_overgedragen'],
                saldo['kd_opgenomen'],
                saldo['kd_resterend']
            )
            kd_item = QTableWidgetItem(kd_text)
            kd_item.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
            if saldo['kd_resterend'] < 0:
                kd_item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row_idx, 2, kd_item)

            # Kolom 3: Opmerking
            opmerking_item = QTableWidgetItem(saldo['opmerking'])
            opmerking_item.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
            self.table.setItem(row_idx, 3, opmerking_item)

            # Kolom 4: Acties
            bewerken_btn = QPushButton("Bewerken")
            bewerken_btn.setStyleSheet(Styles.button_primary(Dimensions.BUTTON_HEIGHT_TINY))
            bewerken_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            bewerken_btn.clicked.connect(  # type: ignore
                lambda checked, g_id=saldo['gebruiker_id']: self.bewerken_saldo(g_id)
            )
            self.table.setCellWidget(row_idx, 4, bewerken_btn)

    def _format_saldo_text(self, totaal: int, overgedragen: int,
                          opgenomen: int, resterend: int) -> str:
        """Formatteer saldo tekst voor tabel cel"""
        return (
            f"Totaal: {totaal}  |  Overdracht: {overgedragen}\n"
            f"Opgenomen: {opgenomen}  |  Resterend: {resterend}"
        )

    def bewerken_saldo(self, gebruiker_id: int):
        """Open bewerken dialog voor gebruiker"""
        from gui.dialogs.verlof_saldo_bewerken_dialog import VerlofSaldoBewerkenDialog

        # Zoek gebruiker data
        gebruiker_data = None
        for saldo in self.saldi_data:
            if saldo['gebruiker_id'] == gebruiker_id:
                gebruiker_data = saldo
                break

        if not gebruiker_data:
            return

        dialog = VerlofSaldoBewerkenDialog(
            gebruiker_id=gebruiker_id,
            naam=gebruiker_data['naam'],
            jaar=self.current_jaar,
            vv_totaal=gebruiker_data['vv_totaal'],
            vv_overgedragen=gebruiker_data['vv_overgedragen'],
            kd_totaal=gebruiker_data['kd_totaal'],
            kd_overgedragen=gebruiker_data['kd_overgedragen'],
            opmerking=gebruiker_data['opmerking'],
            parent=self
        )

        if dialog.exec():
            # Herlaad data na opslaan
            self.load_data()

    def nieuw_jaar_aanmaken(self):
        """Maak saldo records aan voor een nieuw jaar"""
        # Vraag welk jaar
        current_year = datetime.now().year
        jaren = [str(y) for y in range(current_year, current_year + 3)]

        from PyQt6.QtWidgets import QInputDialog
        jaar_str, ok = QInputDialog.getItem(
            self,
            "Nieuw Jaar Aanmaken",
            "Voor welk jaar wil je saldo records aanmaken?",
            jaren,
            0,
            False
        )

        if not ok:
            return

        jaar = int(jaar_str)

        # Bevestig
        reply = QMessageBox.question(
            self,
            "Bevestigen",
            f"Saldo records aanmaken voor {jaar}?\n\n"
            f"Dit maakt nieuwe records aan voor alle actieve gebruikers "
            f"met standaard waarden (0). Je moet de contingenten handmatig invullen.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Maak aan
        try:
            aangemaakt = VerlofSaldoService.maak_jaar_saldi_aan(jaar)

            QMessageBox.information(
                self,
                "Succes",
                f"{aangemaakt} saldo records aangemaakt voor {jaar}.\n\n"
                f"Vul nu de contingenten in via de Bewerken knop."
            )

            # Selecteer het nieuwe jaar
            for i in range(self.jaar_combo.count()):
                if self.jaar_combo.itemData(i) == jaar:
                    self.jaar_combo.setCurrentIndex(i)
                    break

            self.load_data()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Fout",
                f"Fout bij aanmaken saldo records:\n{str(e)}"
            )
