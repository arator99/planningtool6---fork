# gui/dialogs/shift_codes_grid_dialog.py
"""
Shift Codes Grid Dialog
Grid editor voor shift codes van een werkpost
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QCheckBox, QGroupBox, QMessageBox, QLineEdit)
from PyQt6.QtGui import QFont
from database.connection import get_connection
from gui.styles import Styles, Colors, Fonts, Dimensions
import sqlite3


class ShiftCodesGridDialog(QDialog):
    """Grid editor voor shift codes van een werkpost"""

    def __init__(self, parent, werkpost_id: int, werkpost_naam: str):
        super().__init__(parent)
        self.werkpost_id = werkpost_id
        self.werkpost_naam = werkpost_naam

        self.setWindowTitle(f"Shift Codes - {werkpost_naam}")
        self.setModal(True)
        self.resize(1000, 700)

        # Instance attributes
        self.grid: QTableWidget = QTableWidget()
        self.naam_input: QLineEdit = QLineEdit()
        self.beschrijving_input: QLineEdit = QLineEdit()
        self.telt_werkdag: QCheckBox = QCheckBox("Shifts tellen als werkdag")
        self.reset_12u: QCheckBox = QCheckBox("Shifts resetten 12u rust regel")
        self.breekt_reeks: QCheckBox = QCheckBox("Shifts breken werkreeks")

        # Data structure voor grid
        self.shift_types = ['vroeg', 'laat', 'nacht', 'dag']
        self.dag_types = ['weekdag', 'zaterdag', 'zondag']

        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Title
        title = QLabel(f"Shift Codes voor {self.werkpost_naam}")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        layout.addWidget(title)

        # Werkpost info (editeerbaar)
        info_group = QGroupBox("Werkpost Informatie")
        info_layout = QVBoxLayout()

        naam_layout = QHBoxLayout()
        naam_layout.addWidget(QLabel("Naam:"))
        self.naam_input.setStyleSheet(Styles.input_field())
        naam_layout.addWidget(self.naam_input)
        info_layout.addLayout(naam_layout)

        beschr_layout = QHBoxLayout()
        beschr_layout.addWidget(QLabel("Beschrijving:"))
        self.beschrijving_input.setStyleSheet(Styles.input_field())
        beschr_layout.addWidget(self.beschrijving_input)
        info_layout.addLayout(beschr_layout)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Instructie - AANGEPAST
        info = QLabel(
            "Vul per shift type en dag type de code en tijden in\n"
            "Tijd formaat: HH:MM-HH:MM (bijv. 06:30-14:30) of HH-HH voor hele uren (bijv. 06-14)"
        )
        info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(info)

        # Grid tabel
        self.setup_grid()
        layout.addWidget(self.grid)

        # Eigenschappen
        props_group = QGroupBox("Eigenschappen (geldt voor ALLE shifts van deze werkpost)")
        props_layout = QVBoxLayout()
        props_layout.addWidget(self.telt_werkdag)
        props_layout.addWidget(self.reset_12u)
        props_layout.addWidget(self.breekt_reeks)
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)

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
        opslaan_btn.clicked.connect(self.save_data)  # type: ignore
        button_layout.addWidget(opslaan_btn)

        layout.addLayout(button_layout)

    def setup_grid(self):
        """Setup de grid tabel structuur"""
        # Kolommen: elke shift type heeft 2 sub-kolommen (Code, Tijd)
        self.grid.setColumnCount(len(self.shift_types) * 2)
        self.grid.setRowCount(len(self.dag_types))

        # Row headers (dag types)
        self.grid.setVerticalHeaderLabels([
            dt.upper() for dt in self.dag_types
        ])

        # Column headers (shift types)
        headers = []
        for shift in self.shift_types:
            headers.append(f"{shift.upper()}\nCode")
            headers.append("Tijd")  # Simpel, uitleg staat boven de tabel
        self.grid.setHorizontalHeaderLabels(headers)

        # Styling
        self.grid.setStyleSheet(Styles.table_widget())
        self.grid.verticalHeader().setDefaultSectionSize(60)

        # Kolom breedtes
        for col in range(self.grid.columnCount()):
            if col % 2 == 0:  # Code kolom
                self.grid.setColumnWidth(col, 80)
            else:  # Tijd kolom
                self.grid.setColumnWidth(col, 100)

        # Font groter voor headers
        # Alleen vertical header (dag types) bold maken
        vertical_header_font = QFont(Fonts.FAMILY, Fonts.SIZE_SMALL, QFont.Weight.Bold)
        self.grid.verticalHeader().setFont(vertical_header_font)

    def load_data(self):
        """Laad bestaande shift codes en eigenschappen"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Laad werkpost info
            cursor.execute("""
                SELECT naam, beschrijving, telt_als_werkdag, reset_12u_rust, breekt_werk_reeks
                FROM werkposten
                WHERE id = ?
            """, (self.werkpost_id,))

            werkpost = cursor.fetchone()
            if werkpost:
                self.naam_input.setText(werkpost['naam'])
                self.beschrijving_input.setText(werkpost['beschrijving'] or "")
                self.telt_werkdag.setChecked(bool(werkpost['telt_als_werkdag']))
                self.reset_12u.setChecked(bool(werkpost['reset_12u_rust']))
                self.breekt_reeks.setChecked(bool(werkpost['breekt_werk_reeks']))

            # Laad shift codes
            cursor.execute("""
                SELECT dag_type, shift_type, code, start_uur, eind_uur
                FROM shift_codes
                WHERE werkpost_id = ?
            """, (self.werkpost_id,))

            shifts = cursor.fetchall()
            conn.close()

            # Vul grid in
            for shift in shifts:
                row = self.dag_types.index(shift['dag_type'])
                col_base = self.shift_types.index(shift['shift_type']) * 2

                # Code cel
                code_item = QTableWidgetItem(shift['code'] or "")
                self.grid.setItem(row, col_base, code_item)

                # Tijd cel - AANGEPAST: toon volledige tijd
                if shift['start_uur'] and shift['eind_uur']:
                    # Toon als HH:MM-HH:MM (bijv. "06:00-14:00" of "06:30-14:30")
                    tijd_str = f"{shift['start_uur'][:5]}-{shift['eind_uur'][:5]}"
                    tijd_item = QTableWidgetItem(tijd_str)
                    self.grid.setItem(row, col_base + 1, tijd_item)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))

    def save_data(self):
        """Valideer en sla grid data op"""

        try:
            # Validatie
            shifts_data = []

            for row_idx, dag_type in enumerate(self.dag_types):

                for shift_idx, shift_type in enumerate(self.shift_types):
                    col_base = shift_idx * 2

                    # Haal code en tijd op
                    code_item = self.grid.item(row_idx, col_base)
                    tijd_item = self.grid.item(row_idx, col_base + 1)

                    code = code_item.text().strip() if code_item else ""
                    tijd = tijd_item.text().strip() if tijd_item else ""

                    # Als code ingevuld, tijd moet ook
                    if code and not tijd:
                        QMessageBox.warning(
                            self, "Validatie Fout",
                            f"Voor {dag_type} {shift_type}: Code ingevuld maar geen tijd!"
                        )
                        return

                    # Als tijd ingevuld, code moet ook
                    if tijd and not code:
                        QMessageBox.warning(
                            self, "Validatie Fout",
                            f"Voor {dag_type} {shift_type}: Tijd ingevuld maar geen code!"
                        )
                        return

                    # Parse tijd
                    start_uur = None
                    eind_uur = None

                    if tijd:
                        # Verwijder spaties
                        tijd_clean = tijd.replace(' ', '')

                        # Split op -
                        if '-' not in tijd_clean:
                            QMessageBox.warning(
                                self, "Validatie Fout",
                                f"Tijd formaat moet bevatten '-' (bijv. 06:00-14:00 of 06-14)\n"
                                f"Fout bij {dag_type} {shift_type}"
                            )
                            return

                        parts = tijd_clean.split('-')

                        if len(parts) != 2:
                            QMessageBox.warning(
                                self, "Validatie Fout",
                                f"Tijd formaat moet zijn HH:MM-HH:MM of HH-HH\n"
                                f"Fout bij {dag_type} {shift_type}"
                            )
                            return

                        # Parse start tijd
                        start_deel = parts[0]

                        if ':' in start_deel:
                            start_parts = start_deel.split(':')
                            start_uur = f"{start_parts[0].zfill(2)}:{start_parts[1].zfill(2)}"
                        else:
                            start_uur = f"{start_deel.zfill(2)}:00"

                        # Parse eind tijd
                        eind_deel = parts[1]

                        if ':' in eind_deel:
                            eind_parts = eind_deel.split(':')
                            eind_uur = f"{eind_parts[0].zfill(2)}:{eind_parts[1].zfill(2)}"
                        else:
                            eind_uur = f"{eind_deel.zfill(2)}:00"

                    # Sla op voor database insert (alleen als code ingevuld)
                    if code:
                        shifts_data.append({
                            'dag_type': dag_type,
                            'shift_type': shift_type,
                            'code': code,
                            'start_uur': start_uur,
                            'eind_uur': eind_uur
                        })

            # Sla op in database
            conn = get_connection()
            cursor = conn.cursor()

            # Update werkpost naam/beschrijving/eigenschappen
            cursor.execute("""
                UPDATE werkposten
                SET naam = ?,
                    beschrijving = ?,
                    telt_als_werkdag = ?,
                    reset_12u_rust = ?,
                    breekt_werk_reeks = ?
                WHERE id = ?
            """, (
                self.naam_input.text().strip(),
                self.beschrijving_input.text().strip(),
                1 if self.telt_werkdag.isChecked() else 0,
                1 if self.reset_12u.isChecked() else 0,
                1 if self.breekt_reeks.isChecked() else 0,
                self.werkpost_id
            ))

            # Verwijder oude shift codes
            cursor.execute("""
                DELETE FROM shift_codes WHERE werkpost_id = ?
            """, (self.werkpost_id,))

            # Insert nieuwe shift codes
            for shift in shifts_data:
                cursor.execute("""
                    INSERT INTO shift_codes 
                    (werkpost_id, dag_type, shift_type, code, start_uur, eind_uur)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.werkpost_id,
                    shift['dag_type'],
                    shift['shift_type'],
                    shift['code'],
                    shift['start_uur'],
                    shift['eind_uur']
                ))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Succes", "Shift codes opgeslagen!")
            self.accept()

        except sqlite3.IntegrityError as e:
            QMessageBox.warning(self, "Fout", f"Werkpost naam bestaat al of andere constraint fout: {e}")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Fout", str(e))