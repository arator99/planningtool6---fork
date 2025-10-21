# gui/screens/verlof_aanvragen_screen.py
"""
Verlof Aanvragen Scherm
Teamleden kunnen verlof aanvragen en hun aanvragen bekijken
"""
from typing import Callable, List, Dict, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QDateEdit, QTextEdit, QMessageBox,
                             QDialog, QDialogButtonBox, QCalendarWidget)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QTextCharFormat
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
from database.connection import get_connection
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
import sqlite3


class VerlofAanvragenScreen(QWidget):
    """
    Verlof aanvragen scherm voor teamleden
    - Aanvragen indienen
    - Eigen aanvragen bekijken
    - Pending aanvragen intrekken
    """

    def __init__(self, router: Callable, gebruiker_id: int):
        super().__init__()
        self.router = router
        self.gebruiker_id = gebruiker_id

        # Instance attributes
        self.tabel: QTableWidget = QTableWidget()
        self.start_datum: QDateEdit = QDateEdit()
        self.eind_datum: QDateEdit = QDateEdit()
        self.reden_input: QTextEdit = QTextEdit()
        self.saldo_widget = None  # Will be set in init_ui

        self.init_ui()
        self.load_aanvragen()

    def init_ui(self) -> None:
        """Bouw UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_LARGE)
        layout.setContentsMargins(
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE
        )

        # Header
        header = QHBoxLayout()

        title = QLabel("Verlof Aanvragen")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        header.addWidget(title)

        header.addStretch()

        terug_btn = QPushButton("Terug")
        terug_btn.setFixedSize(100, Dimensions.BUTTON_HEIGHT_NORMAL)
        terug_btn.clicked.connect(self.router)  # type: ignore
        terug_btn.setStyleSheet(Styles.button_secondary())
        header.addWidget(terug_btn)

        layout.addLayout(header)

        # Info box
        info = QLabel(
            "Vraag hier verlof aan. Let op: je kunt geen verlof aanvragen in "
            "gepubliceerde maanden."
        )
        info.setStyleSheet(Styles.info_box())
        info.setWordWrap(True)
        layout.addWidget(info)

        # HBox: Formulier + Saldo Widget
        content_layout = QHBoxLayout()

        # Formulier (links)
        form_widget = self.create_form()
        content_layout.addWidget(form_widget, stretch=2)

        # Saldo Widget (rechts)
        from gui.widgets.verlof_saldo_widget import VerlofSaldoWidget
        self.saldo_widget = VerlofSaldoWidget(self.gebruiker_id)
        content_layout.addWidget(self.saldo_widget, stretch=1)

        layout.addLayout(content_layout)

        # Tabel met aanvragen
        tabel_label = QLabel("Mijn Verlof Aanvragen")
        tabel_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(tabel_label)

        self.setup_table()
        layout.addWidget(self.tabel)

    def create_form(self) -> QWidget:
        """Maak aanvraag formulier"""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.BG_WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Dimensions.RADIUS_LARGE}px;
                padding: {Dimensions.SPACING_SMALL}px;
            }}
        """)

        layout = QVBoxLayout(widget)
        layout.setSpacing(Dimensions.SPACING_SMALL)

        # Titel
        form_title = QLabel("Nieuwe Verlofaanvraag")
        form_title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        form_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(form_title)

        # Datums layout (compacter - horizontaal)
        datums_layout = QHBoxLayout()
        datums_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Start datum
        start_label = QLabel("Van:")
        start_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        start_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        datums_layout.addWidget(start_label)

        self.start_datum.setCalendarPopup(True)
        self.start_datum.setDisplayFormat("dd-MM-yyyy")  # Nederlandse format
        self.start_datum.setDate(QDate.currentDate().addDays(14))
        self.start_datum.setMinimumHeight(32)
        self.start_datum.setMinimumWidth(120)
        self.start_datum.setStyleSheet(Styles.input_field())
        calendar_start = self.start_datum.calendarWidget()
        calendar_start.setMinimumWidth(300)  # Zorg voor voldoende breedte
        calendar_start.setStyleSheet("""
            QCalendarWidget QToolButton {
                color: black;
                background-color: white;
                min-width: 80px;
            }
            QCalendarWidget QMenu {
                background-color: white;
                color: black;
            }
            QCalendarWidget QSpinBox {
                color: black;
                background-color: white;
                min-width: 60px;
            }
            QCalendarWidget QComboBox {
                color: black;
                background-color: white;
                min-width: 100px;
            }
            QCalendarWidget QComboBox::drop-down {
                background-color: white;
            }
            QCalendarWidget QAbstractItemView {
                color: black;
                background-color: white;
                selection-background-color: #d0d0d0;
                selection-color: black;
            }
            QCalendarWidget QAbstractItemView::item {
                color: black;
                background-color: white;
                min-width: 36px;
                max-width: 36px;
                min-height: 28px;
            }
            QCalendarWidget QAbstractItemView::item:hover {
                color: black;
                background-color: #e0e0e0;
            }
            QCalendarWidget QAbstractItemView::item:selected {
                color: black;
                background-color: #d0d0d0;
            }
            QCalendarWidget QTableView {
                selection-background-color: #d0d0d0;
            }
            QCalendarWidget QWidget {
                alternate-background-color: white;
            }
            /* Dagen buiten huidige maand - lichtgrijs en disabled */
            QCalendarWidget QAbstractItemView:disabled {
                color: #cccccc;
                background-color: #f5f5f5;
            }
        """)
        datums_layout.addWidget(self.start_datum)

        # Eind datum
        eind_label = QLabel("t/m:")
        eind_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        eind_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        datums_layout.addWidget(eind_label)

        self.eind_datum.setCalendarPopup(True)
        self.eind_datum.setDisplayFormat("dd-MM-yyyy")  # Nederlandse format
        self.eind_datum.setDate(QDate.currentDate().addDays(21))
        self.eind_datum.setMinimumHeight(32)
        self.eind_datum.setMinimumWidth(120)
        self.eind_datum.setStyleSheet(Styles.input_field())
        calendar_eind = self.eind_datum.calendarWidget()
        calendar_eind.setMinimumWidth(300)  # Zorg voor voldoende breedte
        calendar_eind.setStyleSheet("""
            QCalendarWidget QToolButton {
                color: black;
                background-color: white;
                min-width: 80px;
            }
            QCalendarWidget QMenu {
                background-color: white;
                color: black;
            }
            QCalendarWidget QSpinBox {
                color: black;
                background-color: white;
                min-width: 60px;
            }
            QCalendarWidget QComboBox {
                color: black;
                background-color: white;
                min-width: 100px;
            }
            QCalendarWidget QComboBox::drop-down {
                background-color: white;
            }
            QCalendarWidget QAbstractItemView {
                color: black;
                background-color: white;
                selection-background-color: #d0d0d0;
                selection-color: black;
            }
            QCalendarWidget QAbstractItemView::item {
                color: black;
                background-color: white;
                min-width: 36px;
                max-width: 36px;
                min-height: 28px;
            }
            QCalendarWidget QAbstractItemView::item:hover {
                color: black;
                background-color: #e0e0e0;
            }
            QCalendarWidget QAbstractItemView::item:selected {
                color: black;
                background-color: #d0d0d0;
            }
            QCalendarWidget QTableView {
                selection-background-color: #d0d0d0;
            }
            QCalendarWidget QWidget {
                alternate-background-color: white;
            }
            /* Dagen buiten huidige maand - lichtgrijs en disabled */
            QCalendarWidget QAbstractItemView:disabled {
                color: #cccccc;
                background-color: #f5f5f5;
            }
        """)
        datums_layout.addWidget(self.eind_datum)

        datums_layout.addStretch()

        layout.addLayout(datums_layout)

        # Reden (horizontaal - compacter)
        reden_layout = QHBoxLayout()
        reden_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        reden_label = QLabel("Reden (optioneel):")
        reden_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        reden_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        reden_layout.addWidget(reden_label)

        self.reden_input.setPlaceholderText("Bijv. Familievakantie, persoonlijke redenen...")
        self.reden_input.setMaximumHeight(60)
        self.reden_input.setStyleSheet(Styles.input_field())
        reden_layout.addWidget(self.reden_input, stretch=1)

        layout.addLayout(reden_layout)

        # Submit button (kleiner)
        submit_btn = QPushButton("Verlof Aanvragen")
        submit_btn.setStyleSheet(Styles.button_success())
        submit_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        submit_btn.setMaximumWidth(200)
        submit_btn.clicked.connect(self.aanvragen_verlof)  # type: ignore
        layout.addWidget(submit_btn)

        return widget

    def setup_table(self) -> None:
        """Setup aanvragen tabel"""
        self.tabel.setColumnCount(6)
        self.tabel.setHorizontalHeaderLabels([
            "Start Datum", "Eind Datum", "Dagen", "Status", "Reden", "Acties"
        ])

        TableConfig.setup_table_widget(self.tabel, row_height=50)

        # Column widths
        header = self.tabel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tabel.setColumnWidth(5, 120)

    def load_aanvragen(self) -> None:
        """Laad eigen verlof aanvragen"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, start_datum, eind_datum, aantal_dagen, status, 
                       opmerking, aangevraagd_op, reden_weigering
                FROM verlof_aanvragen
                WHERE gebruiker_id = ?
                ORDER BY start_datum DESC
            """, (self.gebruiker_id,))

            aanvragen = cursor.fetchall()
            conn.close()

            self.display_aanvragen(aanvragen)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon aanvragen niet laden:\n{e}")

    def display_aanvragen(self, aanvragen: List[Dict[str, Any]]) -> None:
        """Toon aanvragen in tabel"""
        self.tabel.setRowCount(0)

        for aanvraag in aanvragen:
            row = self.tabel.rowCount()
            self.tabel.insertRow(row)

            # Start datum
            start = datetime.strptime(aanvraag['start_datum'], '%Y-%m-%d')
            self.tabel.setItem(row, 0, QTableWidgetItem(start.strftime('%d-%m-%Y')))

            # Eind datum
            eind = datetime.strptime(aanvraag['eind_datum'], '%Y-%m-%d')
            self.tabel.setItem(row, 1, QTableWidgetItem(eind.strftime('%d-%m-%Y')))

            # Aantal dagen
            self.tabel.setItem(row, 2, QTableWidgetItem(str(aanvraag['aantal_dagen'])))

            # Status met emoji
            status = aanvraag['status']
            status_text = {
                'pending': '🕐 In behandeling',
                'goedgekeurd': '✅ Goedgekeurd',
                'geweigerd': '❌ Geweigerd'
            }.get(status, status)

            status_item = QTableWidgetItem(status_text)
            if status == 'goedgekeurd':
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif status == 'geweigerd':
                status_item.setForeground(Qt.GlobalColor.darkRed)

            self.tabel.setItem(row, 3, status_item)

            # Reden (of weigering reden)
            if status == 'geweigerd' and aanvraag['reden_weigering']:
                reden_text = f"Geweigerd: {aanvraag['reden_weigering']}"
            else:
                reden_text = aanvraag['opmerking'] or "-"

            self.tabel.setItem(row, 4, QTableWidgetItem(reden_text))

            # Acties (alleen intrekken bij pending)
            if status == 'pending':
                acties_widget = self.create_acties_widget(aanvraag['id'])
                self.tabel.setCellWidget(row, 5, acties_widget)
            else:
                self.tabel.setItem(row, 5, QTableWidgetItem("-"))

    def create_acties_widget(self, aanvraag_id: int) -> QWidget:
        """Maak acties widget met intrekken button"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Dimensions.SPACING_SMALL)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        intrekken_btn = QPushButton("Intrekken")
        intrekken_btn.setFixedWidth(100)
        intrekken_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
        intrekken_btn.setStyleSheet(Styles.button_warning(Dimensions.BUTTON_HEIGHT_TINY))
        intrekken_btn.clicked.connect(  # type: ignore
            lambda: self.intrekken_aanvraag(aanvraag_id)
        )
        layout.addWidget(intrekken_btn)

        widget.setLayout(layout)
        return widget

    def aanvragen_verlof(self) -> None:
        """Verwerk verlof aanvraag"""
        # Haal datums op
        start = self.start_datum.date().toPyDate()
        eind = self.eind_datum.date().toPyDate()
        reden = self.reden_input.toPlainText().strip()

        # Validaties
        if eind < start:
            QMessageBox.warning(
                self,
                "Ongeldige Periode",
                "Eind datum moet na start datum liggen!"
            )
            return

        # Check gepubliceerde maanden
        if self.check_gepubliceerde_maanden(start, eind):
            QMessageBox.warning(
                self,
                "Gepubliceerde Maand",
                "Je kunt geen verlof aanvragen in gepubliceerde maanden.\n\n"
                "Neem contact op met je planner."
            )
            return

        # Check overlappende aanvragen
        overlappend = self.check_overlap(start, eind)
        if overlappend:
            # Vraag of aansluitend maken
            overlappend_start_str = datetime.strptime(overlappend['start'], '%Y-%m-%d').strftime('%d-%m-%Y')
            overlappend_eind_str = datetime.strptime(overlappend['eind'], '%Y-%m-%d').strftime('%d-%m-%Y')

            reply = QMessageBox.question(
                self,
                "Overlappende Periode",
                f"Je hebt al verlof van {overlappend_start_str} tot {overlappend_eind_str}.\n\n"
                f"Wil je de periodes aan elkaar laten aansluiten?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Pas datums aan om aan te sluiten
                overlappend_start = datetime.strptime(overlappend['start'], '%Y-%m-%d').date()
                overlappend_eind = datetime.strptime(overlappend['eind'], '%Y-%m-%d').date()

                # Bepaal welke kant we op moeten schuiven
                if start <= overlappend_start and eind >= overlappend_eind:
                    # Nieuwe periode omvat bestaande volledig
                    QMessageBox.warning(
                        self,
                        "Volledige Overlap",
                        "De nieuwe periode omvat je bestaande verlof volledig.\n"
                        "Kies een andere periode of trek eerst je bestaande aanvraag in."
                    )
                    return
                elif start >= overlappend_start and eind <= overlappend_eind:
                    # Nieuwe periode zit volledig binnen bestaande
                    QMessageBox.warning(
                        self,
                        "Volledige Overlap",
                        "Deze periode valt volledig binnen je bestaande verlof.\n"
                        "Kies een andere periode."
                    )
                    return
                elif overlappend_eind >= start:
                    # Bestaande periode loopt door in nieuwe: start nieuwe na bestaande
                    start = overlappend_eind + timedelta(days=1)
                else:
                    # Nieuwe periode loopt door in bestaande: eindig nieuwe voor bestaande
                    eind = overlappend_start - timedelta(days=1)

                if eind < start:
                    QMessageBox.warning(
                        self,
                        "Ongeldige Aanpassing",
                        "Na aansluiting blijft er geen geldige periode over."
                    )
                    return
            else:
                return

        # Bereken aantal dagen
        aantal_dagen = (eind - start).days + 1

        # Bevestiging
        reply = QMessageBox.question(
            self,
            "Verlof Aanvragen",
            f"Verlof aanvragen van {start.strftime('%d-%m-%Y')} "
            f"tot {eind.strftime('%d-%m-%Y')}?\n\n"
            f"Aantal dagen: {aantal_dagen}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Opslaan
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO verlof_aanvragen 
                (gebruiker_id, start_datum, eind_datum, aantal_dagen, 
                 status, opmerking, aangevraagd_op)
                VALUES (?, ?, ?, ?, 'pending', ?, CURRENT_TIMESTAMP)
            """, (
                self.gebruiker_id,
                start.isoformat(),
                eind.isoformat(),
                aantal_dagen,
                reden if reden else None
            ))

            conn.commit()
            conn.close()

            QMessageBox.information(
                self,
                "Succes",
                "Je verlofaanvraag is ingediend!\n\n"
                "Je ontvangt bericht zodra deze is behandeld."
            )

            # Reset formulier
            self.start_datum.setDate(QDate.currentDate().addDays(14))
            self.eind_datum.setDate(QDate.currentDate().addDays(21))
            self.reden_input.clear()

            # Herlaad tabel
            self.load_aanvragen()

            # Refresh saldo widget
            if self.saldo_widget:
                self.saldo_widget.refresh()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon aanvraag niet opslaan:\n{e}")

    def check_gepubliceerde_maanden(self, start: datetime.date, eind: datetime.date) -> bool:
        """Check of periode gepubliceerde maanden bevat"""
        # TODO: Implementeren wanneer planning.status wordt gebruikt
        # Voor nu: return False (alles is concept)
        return False

    def check_overlap(self, start: datetime.date, eind: datetime.date) -> Dict[str, str]:
        """
        Check overlappende verlof aanvragen
        Returns: Dict met start/eind als er overlap is, anders None
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT start_datum, eind_datum
                FROM verlof_aanvragen
                WHERE gebruiker_id = ?
                  AND status IN ('pending', 'goedgekeurd')
                  AND (
                    (start_datum <= ? AND eind_datum >= ?) OR
                    (start_datum <= ? AND eind_datum >= ?) OR
                    (start_datum >= ? AND eind_datum <= ?)
                  )
                LIMIT 1
            """, (
                self.gebruiker_id,
                eind.isoformat(), start.isoformat(),
                start.isoformat(), start.isoformat(),
                start.isoformat(), eind.isoformat()
            ))

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'start': result['start_datum'],
                    'eind': result['eind_datum']
                }

            return None

        except sqlite3.Error as e:
            print(f"Error checking overlap: {e}")
            return None

    def intrekken_aanvraag(self, aanvraag_id: int) -> None:
        """Trek verlof aanvraag in"""
        reply = QMessageBox.question(
            self,
            "Aanvraag Intrekken",
            "Weet je zeker dat je deze aanvraag wilt intrekken?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM verlof_aanvragen
                WHERE id = ? AND status = 'pending'
            """, (aanvraag_id,))

            if cursor.rowcount == 0:
                QMessageBox.warning(
                    self,
                    "Kan Niet Intrekken",
                    "Deze aanvraag kan niet meer worden ingetrokken."
                )
                conn.close()
                return

            conn.commit()
            conn.close()

            QMessageBox.information(
                self,
                "Succes",
                "Je aanvraag is ingetrokken."
            )

            # Herlaad tabel
            self.load_aanvragen()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon aanvraag niet intrekken:\n{e}")