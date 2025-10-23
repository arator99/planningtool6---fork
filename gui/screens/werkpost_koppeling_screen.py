# gui/screens/werkpost_koppeling_screen.py
"""
Werkpost Koppeling Beheer Scherm
Grid met gebruikers (Y-as) x werkposten (X-as)
Checkboxes om aan te geven welke werkposten elke gebruiker kent
"""
from typing import Callable, List, Dict, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QCheckBox, QMessageBox, QHeaderView, QSpinBox, QLineEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database.connection import get_connection
from gui.styles import Styles, Fonts, Dimensions
import sqlite3


class WerkpostKoppelingScreen(QWidget):
    """Werkpost Koppeling Beheer - Grid met checkboxes"""

    def __init__(self, router: Callable):
        super().__init__()
        self.router = router

        # Instance attributes
        self.tabel: QTableWidget = QTableWidget()
        self.gebruikers: List[Dict[str, Any]] = []
        self.werkposten: List[Dict[str, Any]] = []
        self.koppelingen: Dict[tuple, Dict[str, Any]] = {}  # {(gebruiker_id, werkpost_id): {prioriteit, id}}
        self.toon_reserves_checkbox: QCheckBox = QCheckBox("Toon reserves")
        self.naam_filter: QLineEdit = QLineEdit()

        self.init_ui()
        self.load_data()

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

        title = QLabel("Werkpost Koppeling Beheer")
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
            "Configureer welke werkposten elke gebruiker kent.\n"
            "Bij multi-post: prioriteit 1 = eerste keuze, 2 = fallback, etc.\n"
            "Auto-generatie gebruikt automatisch de juiste shift code op basis van deze koppelingen."
        )
        info.setStyleSheet(Styles.info_box())
        info.setWordWrap(True)
        layout.addWidget(info)

        # Filter section
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filters:")
        filter_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        filter_layout.addWidget(filter_label)

        # Naam filter
        self.naam_filter.setPlaceholderText("Zoek op naam...")
        self.naam_filter.setStyleSheet(Styles.input_field())
        self.naam_filter.setMaximumWidth(250)
        self.naam_filter.textChanged.connect(self.on_filter_changed)  # type: ignore
        filter_layout.addWidget(self.naam_filter)

        # Reserve checkbox
        self.toon_reserves_checkbox.setChecked(False)
        self.toon_reserves_checkbox.stateChanged.connect(self.on_filter_changed)  # type: ignore
        filter_layout.addWidget(self.toon_reserves_checkbox)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Tabel
        self.setup_table()
        layout.addWidget(self.tabel)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        opslaan_btn = QPushButton("Opslaan")
        opslaan_btn.setStyleSheet(Styles.button_success())
        opslaan_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        opslaan_btn.clicked.connect(self.save_data)  # type: ignore
        button_layout.addWidget(opslaan_btn)

        layout.addLayout(button_layout)

    def setup_table(self):
        """Setup tabel structuur"""
        # Dit wordt ingevuld na load_data
        self.tabel.setStyleSheet(Styles.table_widget())
        self.tabel.verticalHeader().setDefaultSectionSize(60)

    def on_filter_changed(self):
        """Filter is gewijzigd - rebuild grid"""
        self.build_grid()

    def load_data(self):
        """Laad gebruikers, werkposten en bestaande koppelingen"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Haal actieve gebruikers op (niet admin, inclusief reserves)
            cursor.execute("""
                SELECT id, volledige_naam, is_reserve
                FROM gebruikers
                WHERE is_actief = 1
                  AND gebruikersnaam != 'admin'
                ORDER BY is_reserve, volledige_naam
            """)
            self.gebruikers = cursor.fetchall()

            # Haal actieve werkposten op
            cursor.execute("""
                SELECT id, naam, beschrijving
                FROM werkposten
                WHERE is_actief = 1
                ORDER BY naam
            """)
            self.werkposten = cursor.fetchall()

            # Haal bestaande koppelingen op
            cursor.execute("""
                SELECT id, gebruiker_id, werkpost_id, prioriteit
                FROM gebruiker_werkposten
            """)

            for row in cursor.fetchall():
                key = (row['gebruiker_id'], row['werkpost_id'])
                self.koppelingen[key] = {
                    'id': row['id'],
                    'prioriteit': row['prioriteit']
                }

            conn.close()

            self.build_grid()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))

    def build_grid(self):
        """Bouw de grid met checkboxes en prioriteiten"""
        if not self.gebruikers or not self.werkposten:
            info = QLabel("Geen gebruikers of werkposten beschikbaar")
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return

        # Filter gebruikers op basis van reserves checkbox en naam
        toon_reserves = self.toon_reserves_checkbox.isChecked()
        naam_filter_text = self.naam_filter.text().lower().strip()

        gefilterde_gebruikers = [
            g for g in self.gebruikers
            if (toon_reserves or not g['is_reserve']) and
               (not naam_filter_text or naam_filter_text in g['volledige_naam'].lower())
        ]

        # Kolommen: Naam + (Checkbox + Prioriteit) per werkpost
        num_cols = 1 + (len(self.werkposten) * 2)  # 1 voor naam, 2 per werkpost (checkbox + prioriteit)
        self.tabel.setColumnCount(num_cols)
        self.tabel.setRowCount(len(gefilterde_gebruikers))

        # Headers
        headers = ["Gebruiker"]
        for werkpost in self.werkposten:
            werkpost_label = werkpost['naam']
            if werkpost['beschrijving']:
                werkpost_label += f"\n({werkpost['beschrijving']})"
            headers.append(werkpost_label)
            headers.append("Prio")

        self.tabel.setHorizontalHeaderLabels(headers)

        # Vul grid in
        for row_idx, gebruiker in enumerate(gefilterde_gebruikers):
            # Naam kolom (met [RESERVE] label indien van toepassing)
            naam_text = gebruiker['volledige_naam']
            if gebruiker['is_reserve']:
                naam_text += " [RESERVE]"

            naam_item = QTableWidgetItem(naam_text)
            naam_item.setFlags(naam_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Maak reserves visueel anders (grijze achtergrond)
            if gebruiker['is_reserve']:
                naam_item.setBackground(Qt.GlobalColor.lightGray)

            self.tabel.setItem(row_idx, 0, naam_item)

            col_idx = 1
            for werkpost in self.werkposten:
                key = (gebruiker['id'], werkpost['id'])
                koppeling = self.koppelingen.get(key)

                # Checkbox widget
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                checkbox = QCheckBox()
                checkbox.setChecked(koppeling is not None)
                checkbox.setProperty("gebruiker_id", gebruiker['id'])
                checkbox.setProperty("werkpost_id", werkpost['id'])
                checkbox_layout.addWidget(checkbox)

                checkbox_widget.setLayout(checkbox_layout)
                self.tabel.setCellWidget(row_idx, col_idx, checkbox_widget)
                col_idx += 1

                # Prioriteit spinbox
                prio_widget = QWidget()
                prio_layout = QHBoxLayout(prio_widget)
                prio_layout.setContentsMargins(0, 0, 0, 0)
                prio_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                spinbox = QSpinBox()
                spinbox.setMinimum(1)
                spinbox.setMaximum(99)
                spinbox.setValue(koppeling['prioriteit'] if koppeling else 1)
                spinbox.setEnabled(koppeling is not None)
                spinbox.setProperty("gebruiker_id", gebruiker['id'])
                spinbox.setProperty("werkpost_id", werkpost['id'])
                spinbox.setStyleSheet(Styles.input_field())
                spinbox.setFixedWidth(60)
                prio_layout.addWidget(spinbox)

                # Enable/disable spinbox bij checkbox change
                checkbox.stateChanged.connect(  # type: ignore
                    lambda state, sb=spinbox: sb.setEnabled(state == Qt.CheckState.Checked.value)
                )

                prio_widget.setLayout(prio_layout)
                self.tabel.setCellWidget(row_idx, col_idx, prio_widget)
                col_idx += 1

        # Column widths
        header = self.tabel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, num_cols, 2):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(i + 1, QHeaderView.ResizeMode.Fixed)
            self.tabel.setColumnWidth(i + 1, 80)

    def save_data(self):
        """Sla koppelingen op in database"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Verzamel alle koppelingen uit de grid
            nieuwe_koppelingen = []

            for row_idx in range(self.tabel.rowCount()):
                col_idx = 1
                for werkpost in self.werkposten:
                    # Haal checkbox en spinbox widgets op
                    checkbox_widget = self.tabel.cellWidget(row_idx, col_idx)
                    checkbox = checkbox_widget.findChild(QCheckBox)

                    prio_widget = self.tabel.cellWidget(row_idx, col_idx + 1)
                    spinbox = prio_widget.findChild(QSpinBox)

                    if checkbox and checkbox.isChecked():
                        gebruiker_id = checkbox.property("gebruiker_id")
                        werkpost_id = checkbox.property("werkpost_id")
                        prioriteit = spinbox.value()

                        nieuwe_koppelingen.append({
                            'gebruiker_id': gebruiker_id,
                            'werkpost_id': werkpost_id,
                            'prioriteit': prioriteit
                        })

                    col_idx += 2

            # Validatie: elke gebruiker moet minimaal 1 werkpost hebben
            gebruikers_met_werkpost = set(k['gebruiker_id'] for k in nieuwe_koppelingen)
            gebruikers_zonder_werkpost = []

            for gebruiker in self.gebruikers:
                if gebruiker['id'] not in gebruikers_met_werkpost:
                    gebruikers_zonder_werkpost.append(gebruiker['volledige_naam'])

            if gebruikers_zonder_werkpost:
                reply = QMessageBox.question(
                    self,
                    "Waarschuwing",
                    f"De volgende gebruikers hebben GEEN werkpost:\n\n"
                    f"{', '.join(gebruikers_zonder_werkpost)}\n\n"
                    f"Deze gebruikers kunnen niet worden gebruikt bij auto-generatie.\n\n"
                    f"Toch opslaan?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Delete alle oude koppelingen
            cursor.execute("DELETE FROM gebruiker_werkposten")

            # Insert nieuwe koppelingen
            for koppeling in nieuwe_koppelingen:
                cursor.execute("""
                    INSERT INTO gebruiker_werkposten
                    (gebruiker_id, werkpost_id, prioriteit)
                    VALUES (?, ?, ?)
                """, (
                    koppeling['gebruiker_id'],
                    koppeling['werkpost_id'],
                    koppeling['prioriteit']
                ))

            conn.commit()
            conn.close()

            QMessageBox.information(
                self,
                "Succes",
                f"{len(nieuwe_koppelingen)} koppelingen opgeslagen!"
            )

            # Reload data
            self.load_data()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))
