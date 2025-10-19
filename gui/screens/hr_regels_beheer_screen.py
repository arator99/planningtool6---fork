# gui/screens/hr_regels_beheer_screen.py
"""
HR Regels Beheer Scherm
Beheer van HR validatie regels met versioning support
"""
from typing import List, Dict, Any, Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime
from database.connection import get_connection
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
import sqlite3


class HRRegelsBeheerScreen(QWidget):
    """HR Regels Beheer - Configuratie validatie regels met historiek"""

    def __init__(self, router: Callable):
        super().__init__()
        self.router = router

        # Instance attributes
        self.actieve_tabel: QTableWidget = QTableWidget()
        self.historiek_tabel: QTableWidget = QTableWidget()
        self.toon_historiek_check: QCheckBox = QCheckBox("Toon historiek")
        self.actieve_regels: List[Dict[str, Any]] = []
        self.historiek_regels: List[Dict[str, Any]] = []

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

        title = QLabel("HR Regels Beheer")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        terug_btn = QPushButton("Terug")
        terug_btn.setFixedSize(100, Dimensions.BUTTON_HEIGHT_NORMAL)
        terug_btn.setStyleSheet(Styles.button_secondary())
        terug_btn.clicked.connect(self.router)  # type: ignore
        header_layout.addWidget(terug_btn)

        layout.addLayout(header_layout)

        # Waarschuwing voor voorbeeld regels
        warning = QLabel(
            "LET OP: Standaard regels zijn VOORBEELDEN. "
            "Controleer en wijzig deze volgens afspraken met HR!"
        )
        warning.setStyleSheet(
            f"color: {Colors.WARNING}; "
            f"font-weight: bold; "
            f"padding: {Dimensions.SPACING_MEDIUM}px; "
            f"background-color: rgba(255, 193, 7, 0.1); "
            f"border: 1px solid {Colors.WARNING}; "
            f"border-radius: {Dimensions.RADIUS_MEDIUM}px;"
        )
        warning.setWordWrap(True)
        layout.addWidget(warning)

        # Actieve regels groep
        actieve_group = QGroupBox("ACTIEVE HR REGELS")
        actieve_layout = QVBoxLayout()

        # Info
        info = QLabel(
            "Deze regels worden gebruikt voor planning validatie. "
            "Bij wijzigen wordt een nieuwe versie aangemaakt en de oude gearchiveerd."
        )
        info.setStyleSheet(Styles.info_box())
        info.setWordWrap(True)
        actieve_layout.addWidget(info)

        # Tabel actieve regels
        self.actieve_tabel.setColumnCount(5)
        self.actieve_tabel.setHorizontalHeaderLabels([
            "Regel", "Waarde", "Eenheid", "Actief Vanaf", "Acties"
        ])

        TableConfig.setup_table_widget(self.actieve_tabel, row_height=60)

        header = self.actieve_tabel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.actieve_tabel.setColumnWidth(4, 100)

        actieve_layout.addWidget(self.actieve_tabel)
        actieve_group.setLayout(actieve_layout)
        layout.addWidget(actieve_group)

        # Historiek toggle
        historiek_header = QHBoxLayout()

        self.toon_historiek_check.setChecked(True)
        self.toon_historiek_check.stateChanged.connect(self.toggle_historiek)  # type: ignore
        historiek_header.addWidget(self.toon_historiek_check)

        historiek_label = QLabel("Gearchiveerde regels (alleen-lezen)")
        historiek_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        historiek_header.addWidget(historiek_label)

        historiek_header.addStretch()
        layout.addLayout(historiek_header)

        # Historiek tabel
        self.historiek_tabel.setColumnCount(5)
        self.historiek_tabel.setHorizontalHeaderLabels([
            "Regel", "Waarde", "Eenheid", "Actief Van - Tot", "Vervangen Door"
        ])

        TableConfig.setup_table_widget(self.historiek_tabel, row_height=50)

        header = self.historiek_tabel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.historiek_tabel.setVisible(True)
        layout.addWidget(self.historiek_tabel)

    def toggle_historiek(self, state):
        """Toggle historiek tabel visibility"""
        self.historiek_tabel.setVisible(state == Qt.CheckState.Checked.value)
        if state == Qt.CheckState.Checked.value:
            self.load_historiek()

    def load_data(self):
        """Laad actieve regels"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, naam, waarde, eenheid, beschrijving, actief_vanaf
                FROM hr_regels
                WHERE is_actief = 1
                ORDER BY naam
            """)

            self.actieve_regels = cursor.fetchall()
            conn.close()

            self.display_actieve_regels()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))

    def load_historiek(self):
        """Laad gearchiveerde regels"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, naam, waarde, eenheid, beschrijving,
                       actief_vanaf, actief_tot
                FROM hr_regels
                WHERE is_actief = 0
                ORDER BY naam, actief_vanaf DESC
            """)

            self.historiek_regels = cursor.fetchall()
            conn.close()

            self.display_historiek()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))

    def display_actieve_regels(self):
        """Toon actieve regels in tabel"""
        self.actieve_tabel.setRowCount(len(self.actieve_regels))

        for row, regel in enumerate(self.actieve_regels):
            # Regel naam + beschrijving (kleinere font voor beschrijving)
            naam_text = regel['naam'].replace('_', ' ').title()
            naam_item = QTableWidgetItem()

            if regel['beschrijving']:
                # Verwijder VOORBEELD prefix voor display
                beschrijving = regel['beschrijving'].replace('VOORBEELD - ', '')
                # Naam in bold, beschrijving in klein
                naam_item.setText(f"{naam_text}\n{beschrijving}")
                naam_item.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
            else:
                naam_item.setText(naam_text)
                naam_item.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))

            self.actieve_tabel.setItem(row, 0, naam_item)

            # Waarde
            waarde_item = QTableWidgetItem(str(regel['waarde']))
            waarde_item.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
            waarde_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.actieve_tabel.setItem(row, 1, waarde_item)

            # Eenheid
            eenheid_item = QTableWidgetItem(regel['eenheid'])
            eenheid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.actieve_tabel.setItem(row, 2, eenheid_item)

            # Actief vanaf
            if regel['actief_vanaf']:
                datum = datetime.fromisoformat(regel['actief_vanaf'])
                datum_str = datum.strftime('%d-%m-%Y')
            else:
                datum_str = '-'
            self.actieve_tabel.setItem(row, 3, QTableWidgetItem(datum_str))

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
            bewerk_btn.clicked.connect(self.create_bewerk_callback(dict(regel)))  # type: ignore
            acties_layout.addWidget(bewerk_btn)

            acties_widget.setLayout(acties_layout)
            self.actieve_tabel.setCellWidget(row, 4, acties_widget)

    def display_historiek(self):
        """Toon gearchiveerde regels in tabel"""
        self.historiek_tabel.setRowCount(len(self.historiek_regels))

        for row, regel in enumerate(self.historiek_regels):
            # Regel naam
            naam_text = regel['naam'].replace('_', ' ').title()
            self.historiek_tabel.setItem(row, 0, QTableWidgetItem(naam_text))

            # Waarde
            self.historiek_tabel.setItem(row, 1, QTableWidgetItem(str(regel['waarde'])))

            # Eenheid
            self.historiek_tabel.setItem(row, 2, QTableWidgetItem(regel['eenheid']))

            # Periode
            van = datetime.fromisoformat(regel['actief_vanaf']).strftime('%d-%m-%Y') if regel['actief_vanaf'] else 'N/A'
            tot = datetime.fromisoformat(regel['actief_tot']).strftime('%d-%m-%Y') if regel['actief_tot'] else 'heden'
            periode_item = QTableWidgetItem(f"{van} - {tot}")
            self.historiek_tabel.setItem(row, 3, periode_item)

            # Vervangen door (link naar nieuwe regel)
            if regel['actief_tot']:
                vervangen_item = QTableWidgetItem("Nieuwe versie actief")
            else:
                vervangen_item = QTableWidgetItem("-")
            self.historiek_tabel.setItem(row, 4, vervangen_item)

    def create_bewerk_callback(self, regel: Dict[str, Any]):
        def callback():
            self.bewerk_regel(regel)
        return callback

    def bewerk_regel(self, regel: Dict[str, Any]):
        """Bewerk regel - maak nieuwe versie aan"""
        from gui.dialogs.hr_regel_edit_dialog import HRRegelEditDialog

        dialog = HRRegelEditDialog(self, regel)
        if dialog.exec():
            data = dialog.get_data()
            self.save_nieuwe_versie(regel, data)

    def save_nieuwe_versie(self, oude_regel: Dict[str, Any], nieuwe_data: Dict[str, Any]):
        """
        Sla nieuwe versie op en archiveer oude regel

        Flow:
        1. Oude regel: set actief_tot + is_actief=0
        2. Nieuwe regel: insert met is_actief=1
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Stap 1: Archiveer oude regel
            cursor.execute("""
                UPDATE hr_regels
                SET actief_tot = ?,
                    is_actief = 0
                WHERE id = ?
            """, (nieuwe_data['actief_vanaf'], oude_regel['id']))

            # Stap 2: Insert nieuwe regel
            cursor.execute("""
                INSERT INTO hr_regels
                (naam, waarde, eenheid, beschrijving, actief_vanaf, is_actief)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (
                oude_regel['naam'],
                nieuwe_data['waarde'],
                oude_regel['eenheid'],
                oude_regel['beschrijving'],
                nieuwe_data['actief_vanaf']
            ))

            conn.commit()
            conn.close()

            # Format datum voor display
            datum_obj = datetime.fromisoformat(nieuwe_data['actief_vanaf'])
            datum_display = datum_obj.strftime('%d-%m-%Y')

            QMessageBox.information(
                self,
                "Succes",
                f"Nieuwe versie aangemaakt!\n\n"
                f"Regel: {oude_regel['naam']}\n"
                f"Nieuwe waarde: {nieuwe_data['waarde']} {oude_regel['eenheid']}\n"
                f"Actief vanaf: {datum_display}"
            )

            # Herlaad data
            self.load_data()
            if self.toon_historiek_check.isChecked():
                self.load_historiek()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))
