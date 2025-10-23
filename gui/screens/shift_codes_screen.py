# gui/screens/shift_codes_screen.py
"""
Shift Codes Beheer Scherm
Geïntegreerd scherm met speciale codes en werkposten
"""
from typing import List, Dict, Any, Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database.connection import get_connection
from gui.styles import Styles, Fonts, Dimensions, TableConfig
from gui.dialogs.speciale_code_dialog import SpecialeCodeDialog
from gui.dialogs.werkpost_naam_dialog import WerkpostNaamDialog
from gui.dialogs.shift_codes_grid_dialog import ShiftCodesGridDialog
from services.term_code_service import TermCodeService
import sqlite3


class ShiftCodesScreen(QWidget):
    """Shift Codes Beheer - Speciale codes + Werkposten"""

    def __init__(self, router: Callable):
        super().__init__()
        self.router = router

        # Instance attributes
        self.speciale_tabel: QTableWidget = QTableWidget()
        self.werkposten_tabel: QTableWidget = QTableWidget()
        self.speciale_codes: List[Dict[str, Any]] = []
        self.werkposten: List[Dict[str, Any]] = []

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

        title = QLabel("Shift Codes Beheer")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        terug_btn = QPushButton("Terug")
        terug_btn.setFixedSize(100, Dimensions.BUTTON_HEIGHT_NORMAL)
        terug_btn.setStyleSheet(Styles.button_secondary())
        terug_btn.clicked.connect(self.router)  # type: ignore
        header_layout.addWidget(terug_btn)

        layout.addLayout(header_layout)

        # ============ SPECIALE CODES SECTIE ============
        speciale_group = QGroupBox("SPECIALE CODES (Globaal - geldig voor alle werkposten)")
        speciale_layout = QVBoxLayout()

        # Toolbar speciale codes
        speciale_toolbar = QHBoxLayout()
        speciale_toolbar.addStretch()

        nieuwe_code_btn = QPushButton("+ Nieuwe Code")
        nieuwe_code_btn.setStyleSheet(Styles.button_success())
        nieuwe_code_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        nieuwe_code_btn.clicked.connect(self.nieuwe_speciale_code)  # type: ignore
        speciale_toolbar.addWidget(nieuwe_code_btn)

        speciale_layout.addLayout(speciale_toolbar)

        # Tabel speciale codes
        self.speciale_tabel.setColumnCount(6)
        self.speciale_tabel.setHorizontalHeaderLabels([
            "Code", "Naam", "Werkdag", "12u Reset", "Breekt", "Acties"
        ])

        TableConfig.setup_table_widget(self.speciale_tabel, row_height=50)

        header = self.speciale_tabel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.speciale_tabel.setColumnWidth(5, 180)

        speciale_layout.addWidget(self.speciale_tabel)
        speciale_group.setLayout(speciale_layout)
        layout.addWidget(speciale_group)

        # ============ WERKPOSTEN SECTIE ============
        werkposten_group = QGroupBox("WERKPOSTEN (Shift codes per team/post)")
        werkposten_layout = QVBoxLayout()

        # Toolbar werkposten
        werkposten_toolbar = QHBoxLayout()
        werkposten_toolbar.addStretch()

        nieuwe_werkpost_btn = QPushButton("+ Nieuwe Werkpost")
        nieuwe_werkpost_btn.setStyleSheet(Styles.button_success())
        nieuwe_werkpost_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        nieuwe_werkpost_btn.clicked.connect(self.nieuwe_werkpost)  # type: ignore
        werkposten_toolbar.addWidget(nieuwe_werkpost_btn)

        werkposten_layout.addLayout(werkposten_toolbar)

        # Tabel werkposten
        self.werkposten_tabel.setColumnCount(4)
        self.werkposten_tabel.setHorizontalHeaderLabels([
            "Werkpost", "Shift Codes Configuratie", "Status", "Acties"
        ])

        TableConfig.setup_table_widget(self.werkposten_tabel, row_height=80)

        header = self.werkposten_tabel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.werkposten_tabel.setColumnWidth(3, 200)

        werkposten_layout.addWidget(self.werkposten_tabel)
        werkposten_group.setLayout(werkposten_layout)
        layout.addWidget(werkposten_group)

    def load_data(self):
        """Laad beide tabellen"""
        self.load_speciale_codes()
        self.load_werkposten()

    def load_speciale_codes(self):
        """Laad speciale codes"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM speciale_codes ORDER BY code
            """)

            self.speciale_codes = cursor.fetchall()
            conn.close()

            self.display_speciale_codes()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))

    def display_speciale_codes(self):
        """Toon speciale codes in tabel"""
        self.speciale_tabel.setRowCount(len(self.speciale_codes))

        for row, code in enumerate(self.speciale_codes):
            # Code naam (met indicator voor systeemcode)
            code_text = code['code']
            if code['term']:  # sqlite3.Row heeft geen .get(), gebruik directe access
                code_text += " [SYSTEEM]"
            self.speciale_tabel.setItem(row, 0, QTableWidgetItem(code_text))

            self.speciale_tabel.setItem(row, 1, QTableWidgetItem(code['naam']))
            self.speciale_tabel.setItem(row, 2, QTableWidgetItem("✓" if code['telt_als_werkdag'] else "✗"))
            self.speciale_tabel.setItem(row, 3, QTableWidgetItem("✓" if code['reset_12u_rust'] else "✗"))
            self.speciale_tabel.setItem(row, 4, QTableWidgetItem("✓" if code['breekt_werk_reeks'] else "✗"))

            # Acties
            acties_widget = QWidget()
            acties_layout = QHBoxLayout()
            acties_layout.setContentsMargins(0, 0, 0, 0)
            acties_layout.setSpacing(Dimensions.SPACING_SMALL)
            acties_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            bewerk_btn = QPushButton("Bewerken")
            bewerk_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            bewerk_btn.setFixedWidth(80)
            bewerk_btn.setStyleSheet(Styles.button_primary(Dimensions.BUTTON_HEIGHT_TINY))
            bewerk_btn.clicked.connect(self.create_bewerk_code_callback(dict(code)))  # type: ignore
            acties_layout.addWidget(bewerk_btn)

            verwijder_btn = QPushButton("Verwijder")
            verwijder_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            verwijder_btn.setFixedWidth(80)

            # Disable verwijder-knop voor systeemcodes
            if code['term']:  # sqlite3.Row heeft geen .get()
                verwijder_btn.setEnabled(False)
                verwijder_btn.setStyleSheet(Styles.button_secondary(Dimensions.BUTTON_HEIGHT_TINY))
                verwijder_btn.setToolTip("Systeemcode kan niet verwijderd worden")
            else:
                verwijder_btn.setStyleSheet(Styles.button_danger(Dimensions.BUTTON_HEIGHT_TINY))
                verwijder_btn.clicked.connect(self.create_verwijder_code_callback(dict(code)))  # type: ignore

            acties_layout.addWidget(verwijder_btn)

            acties_widget.setLayout(acties_layout)
            self.speciale_tabel.setCellWidget(row, 5, acties_widget)

    def load_werkposten(self):
        """Laad werkposten met shift codes info"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT w.*,
                       (SELECT COUNT(*) FROM shift_codes WHERE werkpost_id = w.id) as shift_count
                FROM werkposten w
                ORDER BY w.is_actief DESC, w.naam
            """)

            self.werkposten = cursor.fetchall()
            conn.close()

            self.display_werkposten()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))

    def display_werkposten(self):
        """Toon werkposten in tabel"""
        self.werkposten_tabel.setRowCount(len(self.werkposten))

        for row, werkpost in enumerate(self.werkposten):
            # Naam + beschrijving
            naam_text = werkpost['naam']
            if werkpost['beschrijving']:
                naam_text += f"\n({werkpost['beschrijving']})"
            self.werkposten_tabel.setItem(row, 0, QTableWidgetItem(naam_text))

            # Shift codes overzicht
            shift_overzicht = self.format_shift_codes_overzicht(werkpost['id'])
            self.werkposten_tabel.setItem(row, 1, QTableWidgetItem(shift_overzicht))

            # Status
            status_text = "Actief" if werkpost['is_actief'] else "Inactief"
            self.werkposten_tabel.setItem(row, 2, QTableWidgetItem(status_text))

            # Acties
            acties_widget = QWidget()
            acties_layout = QHBoxLayout()
            acties_layout.setContentsMargins(0, 0, 0, 0)
            acties_layout.setSpacing(Dimensions.SPACING_SMALL)
            acties_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            bewerk_btn = QPushButton("Bewerken")
            bewerk_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            bewerk_btn.setFixedWidth(80)
            bewerk_btn.setStyleSheet(Styles.button_primary(Dimensions.BUTTON_HEIGHT_TINY))
            bewerk_btn.clicked.connect(self.create_bewerk_werkpost_callback(dict(werkpost)))  # type: ignore
            acties_layout.addWidget(bewerk_btn)

            # Toggle button
            if werkpost['is_actief']:
                toggle_btn = QPushButton("Deactiveren")
                toggle_style = Styles.button_warning(Dimensions.BUTTON_HEIGHT_TINY)
            else:
                toggle_btn = QPushButton("Activeren")
                toggle_style = Styles.button_success(Dimensions.BUTTON_HEIGHT_TINY)

            toggle_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            toggle_btn.setFixedWidth(96)  # ALTIJD 96, voor beide teksten
            toggle_btn.setStyleSheet(toggle_style)
            toggle_btn.clicked.connect(self.create_toggle_werkpost_callback(dict(werkpost)))  # type: ignore
            acties_layout.addWidget(toggle_btn)

            acties_widget.setLayout(acties_layout)
            self.werkposten_tabel.setCellWidget(row, 3, acties_widget)

    def format_shift_codes_overzicht(self, werkpost_id: int) -> str:
        """Formatteer shift codes overzicht - Weekdag: V=7101, L=7201"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT dag_type, shift_type, code
                FROM shift_codes
                WHERE werkpost_id = ?
                ORDER BY 
                    CASE dag_type
                        WHEN 'weekdag' THEN 1
                        WHEN 'zaterdag' THEN 2
                        WHEN 'zondag' THEN 3
                    END,
                    CASE shift_type
                        WHEN 'vroeg' THEN 1
                        WHEN 'laat' THEN 2
                        WHEN 'nacht' THEN 3
                        WHEN 'dag' THEN 4
                    END
            """, (werkpost_id,))

            shifts = cursor.fetchall()
            conn.close()

            if not shifts:
                return "(Geen shifts geconfigureerd)"

            # Groepeer per dag_type
            per_dag = {}
            for shift in shifts:
                dag = shift['dag_type']
                if dag not in per_dag:
                    per_dag[dag] = []

                # Afkorting
                afkorting = {
                    'vroeg': 'V',
                    'laat': 'L',
                    'nacht': 'N',
                    'dag': 'D'
                }.get(shift['shift_type'], shift['shift_type'][0].upper())

                per_dag[dag].append(f"{afkorting}={shift['code']}")

            # Formatteer per regel
            regels = []
            for dag in ['weekdag', 'zaterdag', 'zondag']:
                if dag in per_dag:
                    dag_naam = dag.capitalize()
                    codes_str = ", ".join(per_dag[dag])
                    regels.append(f"{dag_naam}: {codes_str}")

            return "\n".join(regels)

        except sqlite3.Error:
            return "(Fout bij laden)"

    # ========== SPECIALE CODES CALLBACKS ==========

    def nieuwe_speciale_code(self):
        """Nieuwe speciale code toevoegen"""
        dialog = SpecialeCodeDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.save_speciale_code(data)

    def create_bewerk_code_callback(self, code: Dict[str, Any]):
        def callback():
            self.bewerk_speciale_code(code)

        return callback

    def bewerk_speciale_code(self, code: Dict[str, Any]):
        """Bewerk speciale code"""
        dialog = SpecialeCodeDialog(self, code)
        if dialog.exec():
            data = dialog.get_data()
            self.update_speciale_code(code['id'], data)

    def create_verwijder_code_callback(self, code: Dict[str, Any]):
        def callback():
            self.verwijder_speciale_code(code)

        return callback

    def verwijder_speciale_code(self, code: Dict[str, Any]):
        """Verwijder speciale code (niet mogelijk voor systeemcodes)"""
        # Extra check: systeemcodes mogen niet verwijderd worden
        if code.get('term'):  # hier wel .get() want code is dict()
            QMessageBox.warning(
                self,
                "Niet toegestaan",
                f"Code '{code['code']}' is een systeemcode en kan niet verwijderd worden.\n\n"
                f"Deze code wordt gebruikt door het systeem voor automatische functies.\n"
                f"Je kunt wel de code zelf wijzigen (bijv. van VV naar VL)."
            )
            return

        reply = QMessageBox.question(
            self,
            "Bevestigen",
            f"Weet je zeker dat je code '{code['code']}' ({code['naam']}) wilt verwijderen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM speciale_codes WHERE id = ?", (code['id'],))
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Succes", "Code verwijderd!")

                # Refresh cache (niet nodig voor verwijderen, maar voor consistentie)
                TermCodeService.refresh()
                self.load_speciale_codes()

            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Fout", str(e))

    def save_speciale_code(self, data: Dict[str, Any]):
        """Sla nieuwe code op"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO speciale_codes 
                (code, naam, telt_als_werkdag, reset_12u_rust, breekt_werk_reeks)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data['code'],
                data['naam'],
                1 if data['telt_als_werkdag'] else 0,
                1 if data['reset_12u_rust'] else 0,
                1 if data['breekt_werk_reeks'] else 0
            ))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Succes", "Code toegevoegd!")

            # Refresh cache voor term-code mapping
            TermCodeService.refresh()
            self.load_speciale_codes()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Fout", "Deze code bestaat al!")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))

    def update_speciale_code(self, code_id: int, data: Dict[str, Any]):
        """Update bestaande code"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE speciale_codes
                SET code = ?, naam = ?,
                    telt_als_werkdag = ?,
                    reset_12u_rust = ?,
                    breekt_werk_reeks = ?
                WHERE id = ?
            """, (
                data['code'],
                data['naam'],
                1 if data['telt_als_werkdag'] else 0,
                1 if data['reset_12u_rust'] else 0,
                1 if data['breekt_werk_reeks'] else 0,
                code_id
            ))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Succes", "Code bijgewerkt!")

            # Refresh cache voor term-code mapping (belangrijk bij wijzigen code!)
            TermCodeService.refresh()
            self.load_speciale_codes()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Fout", "Deze code bestaat al!")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", str(e))

    # ========== WERKPOSTEN CALLBACKS ==========

    def nieuwe_werkpost(self):
        """Nieuwe werkpost aanmaken"""
        # Stap 1: Naam dialog
        naam_dialog = WerkpostNaamDialog(self)
        if naam_dialog.exec():
            data = naam_dialog.get_data()

            # Sla werkpost op
            try:
                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO werkposten (naam, beschrijving, telt_als_werkdag, reset_12u_rust, breekt_werk_reeks)
                    VALUES (?, ?, 1, 0, 0)
                """, (data['naam'], data['beschrijving']))

                werkpost_id = cursor.lastrowid
                conn.commit()
                conn.close()

                # Stap 2: Direct naar shift codes grid
                grid_dialog = ShiftCodesGridDialog(self, werkpost_id, data['naam'])
                grid_dialog.exec()

                self.load_werkposten()

            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Fout", "Deze werkpost naam bestaat al!")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Fout", str(e))

    def create_bewerk_werkpost_callback(self, werkpost: Dict[str, Any]):
        def callback():
            self.bewerk_werkpost(werkpost)

        return callback

    def bewerk_werkpost(self, werkpost: Dict[str, Any]):
        """Open shift codes grid editor"""
        dialog = ShiftCodesGridDialog(self, werkpost['id'], werkpost['naam'])
        dialog.exec()
        self.load_werkposten()

    def create_toggle_werkpost_callback(self, werkpost: Dict[str, Any]):
        def callback():
            self.toggle_werkpost(werkpost)

        return callback

    def toggle_werkpost(self, werkpost: Dict[str, Any]):
        """Activeer/deactiveer werkpost (soft delete)"""
        nieuwe_status = 0 if werkpost['is_actief'] else 1
        actie = "deactiveren" if werkpost['is_actief'] else "activeren"

        reply = QMessageBox.question(
            self,
            "Bevestigen",
            f"Weet je zeker dat je werkpost '{werkpost['naam']}' wilt {actie}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()

                if nieuwe_status == 0:
                    cursor.execute("""
                        UPDATE werkposten
                        SET is_actief = 0, gedeactiveerd_op = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (werkpost['id'],))
                else:
                    cursor.execute("""
                        UPDATE werkposten
                        SET is_actief = 1, gedeactiveerd_op = NULL
                        WHERE id = ?
                    """, (werkpost['id'],))

                conn.commit()
                conn.close()

                self.load_werkposten()

            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Fout", str(e))