#gui/dialogs/typetabel_editor_dialog.py

"""
Typetabel Editor Dialog
Grid editor voor het bewerken van typetabel patroon
"""
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QComboBox, QMessageBox, QTextEdit,
                             QScrollArea, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database.connection import get_connection
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
from datetime import datetime
import sqlite3


class TypetabelEditorDialog(QDialog):
    """Dialog voor bewerken typetabel grid"""

    def __init__(self, parent, versie: Dict[str, Any], readonly: bool = False):
        super().__init__(parent)

        self.versie = versie
        self.readonly = readonly
        self.data: List[Dict[str, Any]] = []
        self.heeft_wijzigingen = False

        self.setWindowTitle(f"{'Bekijk' if readonly else 'Bewerk'} Typetabel: {versie['versie_naam']}")
        self.setModal(True)
        self.setMinimumSize(1000, 700)

        # Instance attributes
        self.tabel = QTableWidget()
        self.opmerking_input: Optional[QTextEdit] = None

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialiseer UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel(self.versie['versie_naam'])
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        header_layout.addWidget(title)

        if self.versie['status'] == 'actief':
            status_badge = QLabel("✓ ACTIEF")
            status_badge.setStyleSheet(f"color: {Colors.SUCCESS}; font-weight: bold; padding: 5px;")
            header_layout.addWidget(status_badge)
        elif self.versie['status'] == 'concept':
            status_badge = QLabel("⚙ CONCEPT")
            status_badge.setStyleSheet(f"color: {Colors.WARNING}; font-weight: bold; padding: 5px;")
            header_layout.addWidget(status_badge)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Info lijn
        info_text = f"Weken: {self.versie['aantal_weken']}"
        if self.versie['laatste_wijziging']:
            try:
                dt = datetime.fromisoformat(self.versie['laatste_wijziging'])
                info_text += f"  |  Laatst gewijzigd: {dt.strftime('%Y-%m-%d %H:%M')}"
            except:
                pass

        info_label = QLabel(info_text)
        info_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(info_label)

        # Uitleg
        if not self.readonly:
            uitleg = QLabel(
                "Vul hieronder het patroon in. Gebruik codes zoals V1, V2, L1, L2, N1, RX, CX, etc. "
                "Dit patroon herhaalt zich voor alle personen op basis van hun startweek."
            )
            uitleg.setWordWrap(True)
            uitleg.setStyleSheet(Styles.info_box())
            layout.addWidget(uitleg)

        # Grid tabel
        self.setup_tabel()
        layout.addWidget(self.tabel, 1)

        # Opmerking (alleen bij niet readonly)
        if not self.readonly:
            layout.addWidget(QLabel("Opmerking:"))
            self.opmerking_input = QTextEdit()
            self.opmerking_input.setMaximumHeight(60)
            self.opmerking_input.setPlaceholderText("Optionele opmerking...")
            self.opmerking_input.setStyleSheet(Styles.input_field())
            if self.versie['opmerking']:
                self.opmerking_input.setPlainText(self.versie['opmerking'])
            layout.addWidget(self.opmerking_input)

        # Buttons
        button_layout = QHBoxLayout()

        if not self.readonly:
            button_layout.addStretch()

            annuleer_btn = QPushButton("Annuleren")
            annuleer_btn.setStyleSheet(Styles.button_secondary())
            annuleer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
            annuleer_btn.clicked.connect(self.annuleren)  # type: ignore
            button_layout.addWidget(annuleer_btn)

            opslaan_btn = QPushButton("Opslaan")
            opslaan_btn.setStyleSheet(Styles.button_success())
            opslaan_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
            opslaan_btn.clicked.connect(self.opslaan)  # type: ignore
            button_layout.addWidget(opslaan_btn)
        else:
            button_layout.addStretch()

            sluiten_btn = QPushButton("Sluiten")
            sluiten_btn.setStyleSheet(Styles.button_secondary())
            sluiten_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
            sluiten_btn.clicked.connect(self.accept)  # type: ignore
            button_layout.addWidget(sluiten_btn)

        layout.addLayout(button_layout)

    def setup_tabel(self):
        """Setup grid tabel"""
        aantal_weken = self.versie['aantal_weken']

        # 7 kolommen (Ma-Zo)
        self.tabel.setColumnCount(7)
        self.tabel.setRowCount(aantal_weken)

        # Headers
        dagen = ['Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag', 'Zondag']
        self.tabel.setHorizontalHeaderLabels(dagen)

        # Vertical headers (Week 1, Week 2, ...)
        week_labels = [f"Week {i + 1}" for i in range(aantal_weken)]
        self.tabel.setVerticalHeaderLabels(week_labels)

        # Styling
        TableConfig.setup_table_widget(self.tabel, row_height=50)

        # Column width
        header = self.tabel.horizontalHeader()
        for i in range(7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        # Vertical header width
        self.tabel.verticalHeader().setFixedWidth(80)

    def load_data(self):
        """Laad typetabel data uit database"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM typetabel_data
                WHERE versie_id = ?
                ORDER BY week_nummer, dag_nummer
            """, (self.versie['id'],))

            self.data = cursor.fetchall()
            conn.close()

            self.display_data()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon data niet laden:\n{e}")

    def display_data(self):
        """Vul grid met data"""
        # Maak lookup dict
        data_dict = {}
        for row in self.data:
            key = (row['week_nummer'], row['dag_nummer'])
            data_dict[key] = row['shift_type']

        # Vul tabel
        for week in range(1, self.versie['aantal_weken'] + 1):
            for dag in range(1, 8):
                shift_type = data_dict.get((week, dag), '')

                row_idx = week - 1
                col_idx = dag - 1

                if self.readonly:
                    # Read-only: gewone item
                    item = QTableWidgetItem(shift_type if shift_type else '-')
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if not shift_type:
                        item.setForeground(Qt.GlobalColor.gray)
                    self.tabel.setItem(row_idx, col_idx, item)
                else:
                    # Editable: combobox
                    combo = QComboBox()
                    combo.setEditable(True)
                    combo.setStyleSheet(Styles.input_field())

                    # Vul met veelgebruikte codes
                    standaard_codes = [
                        '', 'V', 'L', 'N', 'RX', 'CX',
                        'V1', 'V2', 'V3', 'V4',
                        'L1', 'L2', 'L3', 'L4',
                        'N1', 'N2', 'N3', 'N4',
                        'VV', 'VD', 'DA', 'Z'
                    ]
                    combo.addItems(standaard_codes)

                    # Set huidige waarde
                    if shift_type:
                        combo.setCurrentText(shift_type)
                    else:
                        combo.setCurrentText('')

                    # Track wijzigingen
                    combo.currentTextChanged.connect(self.on_cel_gewijzigd)  # type: ignore

                    self.tabel.setCellWidget(row_idx, col_idx, combo)

    def on_cel_gewijzigd(self):
        """Track dat er wijzigingen zijn"""
        self.heeft_wijzigingen = True

    def annuleren(self):
        """Annuleer met check voor wijzigingen"""
        if self.heeft_wijzigingen:
            reply = QMessageBox.question(
                self,
                "Onopgeslagen wijzigingen",
                "Je hebt onopgeslagen wijzigingen. Weet je zeker dat je wilt annuleren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

        self.reject()

    def opslaan(self):
        """Sla wijzigingen op naar database"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Update alle cellen
            for week in range(1, self.versie['aantal_weken'] + 1):
                for dag in range(1, 8):
                    row_idx = week - 1
                    col_idx = dag - 1

                    combo = self.tabel.cellWidget(row_idx, col_idx)
                    if isinstance(combo, QComboBox):
                        shift_type = combo.currentText().strip().upper()

                        # Update in database
                        cursor.execute("""
                            UPDATE typetabel_data
                            SET shift_type = ?
                            WHERE versie_id = ? AND week_nummer = ? AND dag_nummer = ?
                        """, (
                            shift_type if shift_type else None,
                            self.versie['id'],
                            week,
                            dag
                        ))

            # Update laatste_wijziging en opmerking
            nieuwe_opmerking = self.opmerking_input.toPlainText().strip() if self.opmerking_input else ''
            cursor.execute("""
                UPDATE typetabel_versies
                SET laatste_wijziging = ?, opmerking = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), nieuwe_opmerking, self.versie['id']))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Opgeslagen", "Typetabel is opgeslagen!")
            self.heeft_wijzigingen = False
            self.accept()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon niet opslaan:\n{e}")