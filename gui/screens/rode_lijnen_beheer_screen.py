# gui/screens/rode_lijnen_beheer_screen.py
"""
Rode Lijnen Beheer Scherm
Beheer van rode lijnen configuratie met versioning support
"""
from typing import List, Dict, Any, Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime
from database.connection import get_connection
from gui.styles import Styles, Fonts, Dimensions, TableConfig
import sqlite3


class RodeLijnenBeheerScreen(QWidget):
    """Rode Lijnen Beheer - Configuratie HR cycli met historiek"""

    def __init__(self, router: Callable):
        super().__init__()
        self.router = router

        # Instance attributes
        self.actieve_tabel: QTableWidget = QTableWidget()
        self.historiek_tabel: QTableWidget = QTableWidget()
        self.toon_historiek_check: QCheckBox = QCheckBox("Toon historiek")
        self.actieve_config: List[Dict[str, Any]] = []
        self.historiek_config: List[Dict[str, Any]] = []

        self.init_ui()
        self.load_data()
        self.load_historiek()  # Laad historiek direct bij start

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE
        )
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Rode Lijnen Beheer")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        terug_btn = QPushButton("Terug")
        terug_btn.setFixedSize(100, Dimensions.BUTTON_HEIGHT_NORMAL)
        terug_btn.setStyleSheet(Styles.button_secondary())
        terug_btn.clicked.connect(self.router)  # type: ignore
        header_layout.addWidget(terug_btn)

        layout.addLayout(header_layout)

        # Info box
        info = QLabel(
            "Rode lijnen zijn HR cycli van X dagen voor validatie. "
            "De validator controleert max werkdagen per cyclus op basis van deze configuratie."
        )
        info.setStyleSheet(Styles.info_box())
        info.setWordWrap(True)
        layout.addWidget(info)

        # Actieve config groep
        actieve_group = QGroupBox("ACTIEVE CONFIGURATIE")
        actieve_layout = QVBoxLayout()

        # Tabel actieve config
        self.actieve_tabel.setColumnCount(4)
        self.actieve_tabel.setHorizontalHeaderLabels([
            "Start Datum", "Interval", "Actief Vanaf", "Acties"
        ])

        TableConfig.setup_table_widget(self.actieve_tabel, row_height=60)

        header = self.actieve_tabel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.actieve_tabel.setColumnWidth(3, 100)

        actieve_layout.addWidget(self.actieve_tabel)
        actieve_group.setLayout(actieve_layout)
        layout.addWidget(actieve_group)

        # Historiek toggle
        historiek_header = QHBoxLayout()

        self.toon_historiek_check.setChecked(True)
        self.toon_historiek_check.stateChanged.connect(self.toggle_historiek)  # type: ignore
        historiek_header.addWidget(self.toon_historiek_check)

        historiek_label = QLabel("Gearchiveerde configuraties (alleen-lezen)")
        historiek_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        historiek_header.addWidget(historiek_label)

        historiek_header.addStretch()
        layout.addLayout(historiek_header)

        # Historiek tabel
        self.historiek_tabel.setColumnCount(4)
        self.historiek_tabel.setHorizontalHeaderLabels([
            "Start Datum", "Interval", "Actief Van - Tot", "Status"
        ])

        TableConfig.setup_table_widget(self.historiek_tabel, row_height=50)

        header = self.historiek_tabel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.historiek_tabel.setVisible(True)
        layout.addWidget(self.historiek_tabel)

    def toggle_historiek(self, state):
        """Toggle historiek tabel visibility"""
        self.historiek_tabel.setVisible(state == Qt.CheckState.Checked.value)
        if state == Qt.CheckState.Checked.value:
            self.load_historiek()

    def load_data(self):
        """Laad actieve configuratie"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, start_datum, interval_dagen, actief_vanaf
                FROM rode_lijnen_config
                WHERE is_actief = 1
                ORDER BY actief_vanaf DESC
            """)

            self.actieve_config = cursor.fetchall()
            conn.close()

            self.display_actieve_config()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))

    def load_historiek(self):
        """Laad gearchiveerde configuraties"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, start_datum, interval_dagen, actief_vanaf, actief_tot
                FROM rode_lijnen_config
                WHERE is_actief = 0
                ORDER BY actief_vanaf DESC
            """)

            self.historiek_config = cursor.fetchall()
            conn.close()

            self.display_historiek()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))

    def display_actieve_config(self):
        """Toon actieve configuratie in tabel"""
        self.actieve_tabel.setRowCount(len(self.actieve_config))

        for row, config in enumerate(self.actieve_config):
            # Start datum
            start_datum = datetime.fromisoformat(config['start_datum']).strftime('%d-%m-%Y')
            start_item = QTableWidgetItem(start_datum)
            start_item.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
            self.actieve_tabel.setItem(row, 0, start_item)

            # Interval
            interval_item = QTableWidgetItem(f"{config['interval_dagen']} dagen")
            interval_item.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
            interval_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.actieve_tabel.setItem(row, 1, interval_item)

            # Actief vanaf
            if config['actief_vanaf']:
                datum = datetime.fromisoformat(config['actief_vanaf'])
                datum_str = datum.strftime('%d-%m-%Y')
            else:
                datum_str = '-'
            self.actieve_tabel.setItem(row, 2, QTableWidgetItem(datum_str))

            # Acties
            acties_widget = QWidget()
            acties_layout = QHBoxLayout()
            acties_layout.setContentsMargins(0, 0, 0, 0)
            acties_layout.setSpacing(Dimensions.SPACING_SMALL)
            acties_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            bewerk_btn = QPushButton("Wijzig")
            bewerk_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            bewerk_btn.setFixedWidth(80)
            bewerk_btn.setStyleSheet(Styles.button_primary(Dimensions.BUTTON_HEIGHT_TINY))
            bewerk_btn.clicked.connect(self.create_bewerk_callback(dict(config)))  # type: ignore
            acties_layout.addWidget(bewerk_btn)

            acties_widget.setLayout(acties_layout)
            self.actieve_tabel.setCellWidget(row, 3, acties_widget)

    def display_historiek(self):
        """Toon gearchiveerde configuraties in tabel"""
        self.historiek_tabel.setRowCount(len(self.historiek_config))

        for row, config in enumerate(self.historiek_config):
            # Start datum
            start_datum = datetime.fromisoformat(config['start_datum']).strftime('%d-%m-%Y')
            self.historiek_tabel.setItem(row, 0, QTableWidgetItem(start_datum))

            # Interval
            interval_item = QTableWidgetItem(f"{config['interval_dagen']} dagen")
            self.historiek_tabel.setItem(row, 1, interval_item)

            # Periode
            van = datetime.fromisoformat(config['actief_vanaf']).strftime('%d-%m-%Y') if config['actief_vanaf'] else 'N/A'
            tot = datetime.fromisoformat(config['actief_tot']).strftime('%d-%m-%Y') if config['actief_tot'] else 'heden'
            periode_item = QTableWidgetItem(f"{van} - {tot}")
            self.historiek_tabel.setItem(row, 2, periode_item)

            # Status
            status_item = QTableWidgetItem("Gearchiveerd")
            self.historiek_tabel.setItem(row, 3, status_item)

    def create_bewerk_callback(self, config: Dict[str, Any]):
        def callback():
            self.bewerk_config(config)
        return callback

    def bewerk_config(self, config: Dict[str, Any]):
        """Bewerk configuratie - maak nieuwe versie aan"""
        from gui.dialogs.rode_lijnen_config_dialog import RodeLijnenConfigDialog

        dialog = RodeLijnenConfigDialog(self, config)
        if dialog.exec():
            data = dialog.get_data()
            self.save_nieuwe_versie(config, data)

    def save_nieuwe_versie(self, oude_config: Dict[str, Any], nieuwe_data: Dict[str, Any]):
        """
        Sla nieuwe versie op en archiveer oude configuratie

        Flow:
        1. Oude config: set actief_tot + is_actief=0
        2. Nieuwe config: insert met is_actief=1
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Stap 1: Archiveer oude config
            cursor.execute("""
                UPDATE rode_lijnen_config
                SET actief_tot = ?,
                    is_actief = 0
                WHERE id = ?
            """, (nieuwe_data['actief_vanaf'], oude_config['id']))

            # Stap 2: Insert nieuwe config
            cursor.execute("""
                INSERT INTO rode_lijnen_config
                (start_datum, interval_dagen, actief_vanaf, is_actief)
                VALUES (?, ?, ?, 1)
            """, (
                nieuwe_data['start_datum'],
                nieuwe_data['interval_dagen'],
                nieuwe_data['actief_vanaf']
            ))

            conn.commit()
            conn.close()

            # BELANGRIJK: Regenereer rode lijnen met nieuwe configuratie
            from services.data_ensure_service import regenereer_rode_lijnen_vanaf
            try:
                toegevoegd = regenereer_rode_lijnen_vanaf(nieuwe_data['actief_vanaf'])
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Waarschuwing",
                    f"Configuratie opgeslagen, maar fout bij regenereren rode lijnen:\n{str(e)}\n\n"
                    f"Herstart de applicatie om rode lijnen te vernieuwen."
                )

            # Format data voor display
            datum_obj = datetime.fromisoformat(nieuwe_data['actief_vanaf'])
            datum_display = datum_obj.strftime('%d-%m-%Y')
            start_obj = datetime.fromisoformat(nieuwe_data['start_datum'])
            start_display = start_obj.strftime('%d-%m-%Y')

            QMessageBox.information(
                self,
                "Succes",
                f"Nieuwe configuratie aangemaakt!\n\n"
                f"Start datum: {start_display}\n"
                f"Interval: {nieuwe_data['interval_dagen']} dagen\n"
                f"Actief vanaf: {datum_display}\n\n"
                f"Rode lijnen zijn geregenereerd.\n"
                f"Sluit en heropen planning schermen om vernieuwde rode lijnen te zien."
            )

            # Herlaad data
            self.load_data()
            if self.toon_historiek_check.isChecked():
                self.load_historiek()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))
