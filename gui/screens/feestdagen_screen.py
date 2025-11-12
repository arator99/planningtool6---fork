#gui/screens/feestdagen_screens.py
"""
Feestdagen beheer scherm - Verbeterde versie
Automatische generatie met Paasberekening
FIXED: Aangepast aan werkelijk database schema (datum, naam, is_zondagsrust)
"""
from typing import Tuple, Optional, Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QComboBox, QDialog, QDialogButtonBox, QDateEdit,
                             QLineEdit, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime
from database.connection import get_connection
from services.data_ensure_service import ensure_jaar_data
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig


class FeestdagenScherm(QWidget):
    def __init__(self, master: QWidget, router: Callable):
        super().__init__()
        self.master = master
        self.router = router
        self.huidig_jaar = datetime.now().year

        # Instance attributes declareren in __init__
        self.jaar_combo: QComboBox = QComboBox()
        self.info_label: QLabel = QLabel()
        self.tabel: QTableWidget = QTableWidget()

        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(Dimensions.SPACING_LARGE)
        layout.setContentsMargins(
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE
        )

        # Header
        header = QHBoxLayout()

        title = QLabel("Feestdagen Beheer")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE))
        header.addWidget(title)

        header.addStretch()

        # Terug knop
        terug_btn = QPushButton("Terug")
        terug_btn.clicked.connect(self.router.terug)  # type: ignore
        terug_btn.setFixedSize(100, Dimensions.BUTTON_HEIGHT_NORMAL)
        terug_btn.setStyleSheet(Styles.button_secondary())
        header.addWidget(terug_btn)

        layout.addLayout(header)

        # Jaar selector met info
        jaar_layout = QHBoxLayout()

        jaar_label = QLabel("Jaar:")
        jaar_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        jaar_layout.addWidget(jaar_label)

        self.jaar_combo.setFixedWidth(100)
        # Vul jaren: 5 jaar terug tot 10 jaar vooruit
        jaren = [str(jaar) for jaar in range(self.huidig_jaar - 5, self.huidig_jaar + 11)]
        self.jaar_combo.addItems(jaren)
        self.jaar_combo.setCurrentText(str(self.huidig_jaar))
        self.jaar_combo.currentTextChanged.connect(self.jaar_gewijzigd)  # type: ignore
        jaar_layout.addWidget(self.jaar_combo)

        # Info label
        self.info_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY))
        self.info_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")
        jaar_layout.addWidget(self.info_label)

        jaar_layout.addStretch()

        layout.addLayout(jaar_layout)

        # Tabel
        self.tabel.setColumnCount(4)
        self.tabel.setHorizontalHeaderLabels(['Datum', 'Naam', 'Type', 'Acties'])

        # Tabel configuratie met centrale styling
        TableConfig.setup_table_widget(self.tabel, row_height=50)

        # Kolom breedtes
        header_view = self.tabel.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.tabel.setColumnWidth(3, 200)

        layout.addWidget(self.tabel)

        # Bottom acties
        bottom_layout = QHBoxLayout()

        # Info tekst
        info_text = QLabel("Variabele feestdagen worden automatisch berekend op basis van Pasen")
        info_text.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")
        bottom_layout.addWidget(info_text)

        bottom_layout.addStretch()

        # Toevoegen knop
        toevoegen_btn = QPushButton("Extra Feestdag Toevoegen")
        toevoegen_btn.setFixedSize(220, Dimensions.BUTTON_HEIGHT_NORMAL)
        toevoegen_btn.clicked.connect(self.feestdag_toevoegen)  # type: ignore
        toevoegen_btn.setStyleSheet(Styles.button_large_action(Colors.PRIMARY, Colors.PRIMARY_HOVER))
        bottom_layout.addWidget(toevoegen_btn)

        layout.addLayout(bottom_layout)

        self.setLayout(layout)

        # Laad initiële data
        self.laad_initieel()

    def laad_initieel(self) -> None:
        """Laad initiële data - zorg dat huidig jaar bestaat en laad het"""
        try:
            # Zorg dat data bestaat voor huidig jaar (database operatie VOOR GUI update)
            ensure_jaar_data(self.huidig_jaar)

            # Update info label
            self.info_label.setText("(huidig jaar)")

            # Laad feestdagen
            self.laad_feestdagen()
        except Exception:
            pass

    def jaar_gewijzigd(self, jaar_str: str) -> None:
        """Jaar selectie gewijzigd - genereert automatisch feestdagen indien nodig"""
        try:
            jaar = int(jaar_str)

            # Zorg automatisch dat data bestaat
            ensure_jaar_data(jaar)

            # Update info label
            if jaar == self.huidig_jaar:
                self.info_label.setText("(huidig jaar)")
            elif jaar < self.huidig_jaar:
                self.info_label.setText("(historisch)")
            else:
                self.info_label.setText("(toekomstig)")

            # Laad feestdagen
            self.laad_feestdagen()
        except Exception:
            pass

    def laad_feestdagen(self) -> None:
        """Laad feestdagen voor geselecteerd jaar met visueel gecentreerde actieknoppen"""
        jaar = int(self.jaar_combo.currentText())

        conn = None
        feestdagen = []

        try:
            conn = get_connection()
            cursor = conn.cursor()
            # Schema: datum, naam, is_zondagsrust, is_variabel
            cursor.execute("""
                SELECT datum, naam, is_zondagsrust, is_variabel
                FROM feestdagen
                WHERE datum LIKE ?
                ORDER BY datum
            """, (f"{jaar}-%",))

            feestdagen = cursor.fetchall()
        except Exception:
            pass
        finally:
            if conn:
                conn.close()

        # GUI updates BUITEN database context
        self.tabel.setRowCount(len(feestdagen))

        for row, (datum, naam, is_zondagsrust, is_variabel) in enumerate(feestdagen):
            # Datum - formatteer naar dd-mm-yyyy
            datum_obj = datetime.strptime(datum, '%Y-%m-%d')
            datum_formatted = datum_obj.strftime('%d-%m-%Y')
            datum_item = QTableWidgetItem(datum_formatted)
            datum_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabel.setItem(row, 0, datum_item)

            # Naam
            naam_item = QTableWidgetItem(naam)
            self.tabel.setItem(row, 1, naam_item)

            # Type - nu uit database
            if is_variabel:
                # Check of het een automatisch gegenereerde variabele is
                if naam in ['Paasmaandag', 'O.H. Hemelvaart', 'Pinkstermaandag']:
                    type_text = "Variabel"
                else:
                    type_text = "Extra"
            else:
                type_text = "Vast"

            type_item = QTableWidgetItem(type_text)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabel.setItem(row, 2, type_item)

            # Acties - simpele HBox met AlignCenter
            actie_widget = QWidget()
            actie_layout = QHBoxLayout()
            actie_layout.setContentsMargins(0, 0, 0, 0)
            actie_layout.setSpacing(Dimensions.SPACING_SMALL)
            actie_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Bewerk knop (alleen voor variabele en extra feestdagen)
            if is_variabel:
                bewerk_btn = QPushButton("Bewerk")
                bewerk_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
                bewerk_btn.setFixedWidth(80)
                bewerk_btn.clicked.connect(self.genereer_bewerk_callback(datum, naam))  # type: ignore
                bewerk_btn.setStyleSheet(Styles.button_warning(Dimensions.BUTTON_HEIGHT_TINY))
                actie_layout.addWidget(bewerk_btn)

            # Verwijder knop (alleen voor extra feestdagen)
            if is_variabel and naam not in ['Paasmaandag', 'O.H. Hemelvaart', 'Pinkstermaandag']:
                verwijder_btn = QPushButton("Verwijder")
                verwijder_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
                verwijder_btn.setFixedWidth(80)
                verwijder_btn.clicked.connect(self.genereer_verwijder_callback(datum))  # type: ignore
                verwijder_btn.setStyleSheet(Styles.button_danger(Dimensions.BUTTON_HEIGHT_TINY))
                actie_layout.addWidget(verwijder_btn)

            # Als geen buttons, toon "-"
            if actie_layout.count() == 0:
                geen_actie = QLabel("-")
                geen_actie.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
                geen_actie.setAlignment(Qt.AlignmentFlag.AlignCenter)
                actie_layout.addWidget(geen_actie)

            actie_widget.setLayout(actie_layout)
            self.tabel.setCellWidget(row, 3, actie_widget)

    def genereer_bewerk_callback(self, datum: str, naam: str):
        """Genereer callback voor bewerk knop (voorkomt lambda closure problemen)"""

        def callback():
            self.bewerk_datum(naam, datum)

        return callback

    def genereer_verwijder_callback(self, datum: str):
        """Genereer callback voor verwijder knop (voorkomt lambda closure problemen)"""

        def callback():
            self.verwijder(datum)

        return callback

    def bewerk_datum(self, naam: str, oude_datum: str) -> None:
        """Bewerk datum van een feestdag (voor correcties)"""
        jaar = int(self.jaar_combo.currentText())

        dialog = DatumBewerkDialog(naam, oude_datum, jaar, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nieuwe_datum = dialog.get_datum()

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE feestdagen
                SET datum = ?
                WHERE datum = ?
            """, (nieuwe_datum, oude_datum))
            conn.commit()
            conn.close()

            self.laad_feestdagen()

            QMessageBox.information(
                self,
                'Gewijzigd',
                f'{naam} gewijzigd naar {nieuwe_datum}'
            )

    def feestdag_toevoegen(self) -> None:
        """Voeg extra feestdag toe"""
        jaar = int(self.jaar_combo.currentText())

        dialog = FeestdagToevoegenDialog(jaar, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            datum, naam = dialog.get_data()

            conn = get_connection()
            cursor = conn.cursor()

            # Check of datum al bestaat
            cursor.execute("SELECT naam FROM feestdagen WHERE datum = ?", (datum,))
            bestaand = cursor.fetchone()

            if bestaand:
                conn.close()
                QMessageBox.warning(
                    self,
                    'Bestaat al',
                    f'Er bestaat al een feestdag op {datum}: {bestaand[0]}'
                )
                return

            # Schema: datum, naam, is_zondagsrust, is_variabel (extra = variabel)
            cursor.execute("""
                INSERT OR IGNORE INTO feestdagen (datum, naam, is_zondagsrust, is_variabel)
                VALUES (?, ?, 1, 1)
            """, (datum, naam))
            conn.commit()
            conn.close()

            self.laad_feestdagen()

            QMessageBox.information(
                self,
                'Toegevoegd',
                f'{naam} toegevoegd op {datum}'
            )

    def verwijder(self, datum: str) -> None:
        """Verwijder extra feestdag"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT naam FROM feestdagen WHERE datum = ?", (datum,))
        result = cursor.fetchone()
        naam = result[0] if result else "Onbekend"
        conn.close()

        reply = QMessageBox.question(
            self,
            'Verwijderen?',
            f'Weet je zeker dat je "{naam}" ({datum}) wilt verwijderen?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM feestdagen WHERE datum = ?", (datum,))
            conn.commit()
            conn.close()

            self.laad_feestdagen()


class DatumBewerkDialog(QDialog):
    """Dialog om datum van feestdag te bewerken"""

    def __init__(self, naam: str, oude_datum: str, jaar: int, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.naam = naam
        self.oude_datum = oude_datum
        self.jaar = jaar
        self.setWindowTitle(f"{naam} bewerken")
        self.setModal(True)

        # Instance attribute declareren in __init__
        self.datum_edit: QDateEdit = QDateEdit()

        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()

        # Info
        info = QLabel(f"Wijzig de datum van {self.naam}")
        info.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY))
        layout.addWidget(info)

        # Oude datum info
        oude_info = QLabel(f"Huidige datum: {self.oude_datum}")
        oude_info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")
        layout.addWidget(oude_info)

        layout.addSpacing(Dimensions.SPACING_MEDIUM)

        # Datum picker
        datum_layout = QHBoxLayout()
        datum_label = QLabel("Nieuwe datum:")
        datum_layout.addWidget(datum_label)

        self.datum_edit.setCalendarPopup(True)
        self.datum_edit.setDisplayFormat("dd-MM-yyyy")

        # Set huidige datum
        parts = self.oude_datum.split('-')
        self.datum_edit.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))

        # Limiteer tot geselecteerd jaar
        self.datum_edit.setMinimumDate(QDate(self.jaar, 1, 1))
        self.datum_edit.setMaximumDate(QDate(self.jaar, 12, 31))

        datum_layout.addWidget(self.datum_edit)
        layout.addLayout(datum_layout)

        # Buttons
        buttons = QDialogButtonBox()
        buttons.addButton(QDialogButtonBox.StandardButton.Ok)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)  # type: ignore
        buttons.rejected.connect(self.reject)  # type: ignore
        layout.addWidget(buttons)

        self.setLayout(layout)

        # Styling
        self.setStyleSheet(Styles.input_field())

    def get_datum(self) -> str:
        """Return nieuwe datum in YYYY-MM-DD formaat"""
        qdate = self.datum_edit.date()
        return f"{qdate.year()}-{qdate.month():02d}-{qdate.day():02d}"


class FeestdagToevoegenDialog(QDialog):
    """Dialog om extra feestdag toe te voegen"""

    def __init__(self, jaar: int, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.jaar = jaar
        self.setWindowTitle("Extra Feestdag Toevoegen")
        self.setModal(True)

        # Instance attributes declareren in __init__
        self.naam_input: QLineEdit = QLineEdit()
        self.datum_edit: QDateEdit = QDateEdit()

        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()

        # Info
        info = QLabel(f"Voeg een extra feestdag toe voor {self.jaar}")
        info.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY))
        layout.addWidget(info)

        layout.addSpacing(Dimensions.SPACING_MEDIUM)

        # Naam
        naam_layout = QHBoxLayout()
        naam_label = QLabel("Naam:")
        naam_label.setFixedWidth(80)
        naam_layout.addWidget(naam_label)

        self.naam_input.setPlaceholderText("Bijv. Lokale feestdag")
        naam_layout.addWidget(self.naam_input)
        layout.addLayout(naam_layout)

        # Datum
        datum_layout = QHBoxLayout()
        datum_label = QLabel("Datum:")
        datum_label.setFixedWidth(80)
        datum_layout.addWidget(datum_label)

        self.datum_edit.setCalendarPopup(True)
        self.datum_edit.setDisplayFormat("dd-MM-yyyy")
        self.datum_edit.setDate(QDate(self.jaar, 1, 1))

        # Limiteer tot geselecteerd jaar
        self.datum_edit.setMinimumDate(QDate(self.jaar, 1, 1))
        self.datum_edit.setMaximumDate(QDate(self.jaar, 12, 31))

        datum_layout.addWidget(self.datum_edit)
        layout.addLayout(datum_layout)

        # Buttons
        buttons = QDialogButtonBox()
        buttons.addButton(QDialogButtonBox.StandardButton.Ok)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.valideer_en_accept)  # type: ignore
        buttons.rejected.connect(self.reject)  # type: ignore
        layout.addWidget(buttons)

        self.setLayout(layout)

        # Styling
        self.setStyleSheet(Styles.input_field())

    def valideer_en_accept(self) -> None:
        """Valideer input voor accept"""
        if not self.naam_input.text().strip():
            QMessageBox.warning(self, 'Fout', 'Vul een naam in!')
            return
        self.accept()

    def get_data(self) -> Tuple[str, str]:
        """Return (datum, naam) tuple"""
        qdate = self.datum_edit.date()
        datum = f"{qdate.year()}-{qdate.month():02d}-{qdate.day():02d}"
        naam = self.naam_input.text().strip()
        return datum, naam