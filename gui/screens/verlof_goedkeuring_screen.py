# gui/screens/verlof_goedkeuring_screen.py
"""
Verlof Goedkeuring Scherm
Planners kunnen verlofaanvragen goedkeuren of weigeren
"""
from typing import Callable, List, Dict, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QComboBox, QDialog, QTextEdit,
                             QMessageBox, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
from database.connection import get_connection
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
from services.term_code_service import TermCodeService
import sqlite3


class VerlofGoedkeuringScreen(QWidget):
    """
    Verlof goedkeuring scherm voor planners
    - Overzicht van alle aanvragen
    - Goedkeuren/Weigeren
    - Filter per teamlid
    - Impact op planning zien
    """

    #signal om notificatie terug te laten tellen
    verlofGoedgekeurd = pyqtSignal()

    def __init__(self, router: Callable, planner_id: int):
        super().__init__()
        self.router = router
        self.planner_id = planner_id

        # Instance attributes
        self.tabel: QTableWidget = QTableWidget()
        self.filter_combo: QComboBox = QComboBox()
        self.alle_aanvragen: List[Dict[str, Any]] = []

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

        title = QLabel("Verlof Goedkeuring")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        header.addWidget(title)

        header.addStretch()

        # Filter
        filter_label = QLabel("Filter:")
        filter_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        header.addWidget(filter_label)

        self.filter_combo.setFixedWidth(200)
        self.filter_combo.addItem("Alle aanvragen", None)
        self.filter_combo.addItem("🕐 Pending", "pending")
        self.filter_combo.addItem("✅ Goedgekeurd", "goedgekeurd")
        self.filter_combo.addItem("❌ Geweigerd", "geweigerd")
        self.filter_combo.currentIndexChanged.connect(self.on_filter_changed)  # type: ignore
        header.addWidget(self.filter_combo)

        terug_btn = QPushButton("Terug")
        terug_btn.setFixedSize(100, Dimensions.BUTTON_HEIGHT_NORMAL)
        terug_btn.clicked.connect(self.router)  # type: ignore
        terug_btn.setStyleSheet(Styles.button_secondary())
        header.addWidget(terug_btn)

        layout.addLayout(header)

        # Info box
        info = QLabel(
            "Behandel hier verlofaanvragen van teamleden. Bij goedkeuring wordt "
            "automatisch VV in de planning gezet voor de verlofperiode."
        )
        info.setStyleSheet(Styles.info_box())
        info.setWordWrap(True)
        layout.addWidget(info)

        # Tabel
        self.setup_table()
        layout.addWidget(self.tabel)

    def setup_table(self) -> None:
        """Setup aanvragen tabel"""
        self.tabel.setColumnCount(8)
        self.tabel.setHorizontalHeaderLabels([
            "Teamlid", "Start", "Eind", "Dagen", "Status",
            "Aangevraagd op", "Reden", "Acties"
        ])

        TableConfig.setup_table_widget(self.tabel, row_height=50)

        # Column widths
        header = self.tabel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.tabel.setColumnWidth(7, 220)

    def load_aanvragen(self) -> None:
        """Laad alle verlof aanvragen"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 
                    va.id, va.gebruiker_id, va.start_datum, va.eind_datum,
                    va.aantal_dagen, va.status, va.opmerking, va.aangevraagd_op,
                    va.reden_weigering,
                    g.volledige_naam
                FROM verlof_aanvragen va
                JOIN gebruikers g ON va.gebruiker_id = g.id
                ORDER BY 
                    CASE va.status 
                        WHEN 'pending' THEN 1
                        WHEN 'goedgekeurd' THEN 2
                        WHEN 'geweigerd' THEN 3
                    END,
                    va.start_datum ASC
            """)

            self.alle_aanvragen = cursor.fetchall()
            conn.close()

            self.display_aanvragen()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon aanvragen niet laden:\n{e}")

    def on_filter_changed(self) -> None:
        """Filter gewijzigd"""
        self.display_aanvragen()

    def display_aanvragen(self) -> None:
        """Toon aanvragen in tabel (met filter)"""
        self.tabel.setRowCount(0)

        # Haal filter op
        filter_status = self.filter_combo.currentData()

        # Filter aanvragen
        gefilterde_aanvragen = [
            a for a in self.alle_aanvragen
            if filter_status is None or a['status'] == filter_status
        ]

        for aanvraag in gefilterde_aanvragen:
            row = self.tabel.rowCount()
            self.tabel.insertRow(row)

            # Teamlid
            naam_item = QTableWidgetItem(aanvraag['volledige_naam'])
            naam_item.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
            self.tabel.setItem(row, 0, naam_item)

            # Start datum
            start = datetime.strptime(aanvraag['start_datum'], '%Y-%m-%d')
            self.tabel.setItem(row, 1, QTableWidgetItem(start.strftime('%d-%m-%Y')))

            # Eind datum
            eind = datetime.strptime(aanvraag['eind_datum'], '%Y-%m-%d')
            self.tabel.setItem(row, 2, QTableWidgetItem(eind.strftime('%d-%m-%Y')))

            # Aantal dagen
            self.tabel.setItem(row, 3, QTableWidgetItem(str(aanvraag['aantal_dagen'])))

            # Status
            status = aanvraag['status']
            status_text = {
                'pending': '🕐 Pending',
                'goedgekeurd': '✅ Goedgekeurd',
                'geweigerd': '❌ Geweigerd'
            }.get(status, status)

            status_item = QTableWidgetItem(status_text)
            if status == 'goedgekeurd':
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif status == 'geweigerd':
                status_item.setForeground(Qt.GlobalColor.darkRed)

            self.tabel.setItem(row, 4, status_item)

            # Aangevraagd op
            aangevraagd = datetime.strptime(aanvraag['aangevraagd_op'], '%Y-%m-%d %H:%M:%S')
            self.tabel.setItem(row, 5, QTableWidgetItem(aangevraagd.strftime('%d-%m-%Y %H:%M')))

            # Reden
            if status == 'geweigerd' and aanvraag['reden_weigering']:
                reden_text = f"Geweigerd: {aanvraag['reden_weigering']}"
            else:
                reden_text = aanvraag['opmerking'] or "-"

            self.tabel.setItem(row, 6, QTableWidgetItem(reden_text))

            # Acties (alleen voor pending)
            if status == 'pending':
                acties_widget = self.create_acties_widget(aanvraag)
                self.tabel.setCellWidget(row, 7, acties_widget)
            else:
                self.tabel.setItem(row, 7, QTableWidgetItem("-"))

            # Tooltip met extra info (wie is er nog meer vrij?)
            tooltip = self.get_impact_tooltip(aanvraag)
            for col in range(self.tabel.columnCount()):
                item = self.tabel.item(row, col)
                if item:
                    item.setToolTip(tooltip)

    def create_acties_widget(self, aanvraag: Dict[str, Any]) -> QWidget:
        """Maak acties widget met goedkeuren/weigeren buttons"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Dimensions.SPACING_SMALL)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Goedkeuren
        goedkeuren_btn = QPushButton("Goedkeuren")
        goedkeuren_btn.setFixedWidth(100)
        goedkeuren_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
        goedkeuren_btn.setStyleSheet(Styles.button_success(Dimensions.BUTTON_HEIGHT_TINY))
        goedkeuren_btn.clicked.connect(  # type: ignore
            lambda: self.goedkeuren_aanvraag(aanvraag)
        )
        layout.addWidget(goedkeuren_btn)

        # Weigeren
        weigeren_btn = QPushButton("Weigeren")
        weigeren_btn.setFixedWidth(100)
        weigeren_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
        weigeren_btn.setStyleSheet(Styles.button_danger(Dimensions.BUTTON_HEIGHT_TINY))
        weigeren_btn.clicked.connect(  # type: ignore
            lambda: self.weigeren_aanvraag(aanvraag)
        )
        layout.addWidget(weigeren_btn)

        widget.setLayout(layout)
        return widget

    def get_impact_tooltip(self, aanvraag: Dict[str, Any]) -> str:
        """Genereer tooltip met impact info"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Zoek andere mensen die vrij zijn in deze periode
            cursor.execute("""
                SELECT DISTINCT g.volledige_naam
                FROM verlof_aanvragen va
                JOIN gebruikers g ON va.gebruiker_id = g.id
                WHERE va.status = 'goedgekeurd'
                  AND va.gebruiker_id != ?
                  AND (
                    (va.start_datum <= ? AND va.eind_datum >= ?) OR
                    (va.start_datum <= ? AND va.eind_datum >= ?) OR
                    (va.start_datum >= ? AND va.eind_datum <= ?)
                  )
            """, (
                aanvraag['gebruiker_id'],
                aanvraag['eind_datum'], aanvraag['start_datum'],
                aanvraag['start_datum'], aanvraag['start_datum'],
                aanvraag['start_datum'], aanvraag['eind_datum']
            ))

            anderen_vrij = cursor.fetchall()
            conn.close()

            tooltip_lines = [
                f"Verlofaanvraag: {aanvraag['volledige_naam']}",
                f"Periode: {aanvraag['start_datum']} t/m {aanvraag['eind_datum']}",
                f"Dagen: {aanvraag['aantal_dagen']}"
            ]

            if anderen_vrij:
                tooltip_lines.append("")
                tooltip_lines.append("⚠️ Ook vrij in deze periode:")
                for row in anderen_vrij:
                    tooltip_lines.append(f"  • {row['volledige_naam']}")
            else:
                tooltip_lines.append("")
                tooltip_lines.append("✓ Geen andere teamleden vrij in deze periode")

            return "\n".join(tooltip_lines)

        except sqlite3.Error as e:
            return f"Kon impact niet berekenen: {e}"

    def goedkeuren_aanvraag(self, aanvraag: Dict[str, Any]) -> None:
        """Keur verlof aanvraag goed"""
        # Format datums
        start_datum = datetime.strptime(aanvraag['start_datum'], '%Y-%m-%d').strftime('%d-%m-%Y')
        eind_datum = datetime.strptime(aanvraag['eind_datum'], '%Y-%m-%d').strftime('%d-%m-%Y')

        # Vraag planner om type te kiezen (VV of KD)
        type_dialog = VerlofTypeDialog(
            self,
            aanvraag['volledige_naam'],
            start_datum,
            eind_datum,
            aanvraag['aantal_dagen'],
            aanvraag['gebruiker_id']
        )

        if type_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # Haal gekozen type op (term)
        code_term = type_dialog.get_code_term()

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Update aanvraag status + toegekende_code_term
            cursor.execute("""
                UPDATE verlof_aanvragen
                SET status = 'goedgekeurd',
                    behandeld_door = ?,
                    behandeld_op = CURRENT_TIMESTAMP,
                    toegekende_code_term = ?
                WHERE id = ?
            """, (self.planner_id, code_term, aanvraag['id']))

            # Haal code op basis van gekozen term
            toegekende_code = TermCodeService.get_code_for_term(code_term)

            # Vul planning voor elke dag met gekozen code
            start = datetime.strptime(aanvraag['start_datum'], '%Y-%m-%d')
            eind = datetime.strptime(aanvraag['eind_datum'], '%Y-%m-%d')

            huidige = start
            while huidige <= eind:
                datum_str = huidige.strftime('%Y-%m-%d')

                cursor.execute("""
                    INSERT INTO planning (gebruiker_id, datum, shift_code, status)
                    VALUES (?, ?, ?, 'concept')
                    ON CONFLICT(gebruiker_id, datum)
                    DO UPDATE SET shift_code = ?
                    WHERE status = 'concept'
                """, (aanvraag['gebruiker_id'], datum_str, toegekende_code, toegekende_code))

                huidige += timedelta(days=1)

            conn.commit()

            # Sync saldo
            from services.verlof_saldo_service import VerlofSaldoService
            jaar = start.year
            VerlofSaldoService.sync_saldo_naar_database(aanvraag['gebruiker_id'], jaar)

            conn.close()

            type_naam = "Verlof (VV)" if code_term == "verlof" else "Kompensatiedag (KD)"
            QMessageBox.information(
                self,
                "Succes",
                f"{type_naam} goedgekeurd voor {aanvraag['volledige_naam']}!\n\n"
                f"{toegekende_code} is toegevoegd aan de planning."
            )
            self.verlofGoedgekeurd.emit()
            # Herlaad tabel
            self.load_aanvragen()


        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon aanvraag niet goedkeuren:\n{e}")

    def weigeren_aanvraag(self, aanvraag: Dict[str, Any]) -> None:
        """Weiger verlof aanvraag"""
        # Dialog voor reden
        dialog = WeigeringRedenDialog(self, aanvraag['volledige_naam'])

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        reden = dialog.get_reden()

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE verlof_aanvragen
                SET status = 'geweigerd',
                    behandeld_door = ?,
                    behandeld_op = CURRENT_TIMESTAMP,
                    reden_weigering = ?
                WHERE id = ?
            """, (self.planner_id, reden, aanvraag['id']))

            conn.commit()
            conn.close()

            QMessageBox.information(
                self,
                "Succes",
                f"Verlof geweigerd voor {aanvraag['volledige_naam']}."
            )

            # Herlaad tabel
            self.load_aanvragen()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon aanvraag niet weigeren:\n{e}")


class VerlofTypeDialog(QDialog):
    """Dialog voor kiezen verlof type (VV of KD)"""

    def __init__(self, parent: QWidget, naam: str, start_datum: str,
                 eind_datum: str, dagen: int, gebruiker_id: int):
        super().__init__(parent)
        self.naam = naam
        self.start_datum = start_datum
        self.eind_datum = eind_datum
        self.dagen = dagen
        self.gebruiker_id = gebruiker_id

        self.setWindowTitle("Type Verlof Kiezen")
        self.setModal(True)
        self.setMinimumWidth(550)

        # Instance attributes
        self.type_combo: QComboBox = QComboBox()
        self.saldo_label: QLabel = QLabel()

        self.init_ui()
        self.load_saldo()

    def init_ui(self) -> None:
        """Initialiseer UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Titel
        titel = QLabel(f"Verlof goedkeuren voor {self.naam}")
        titel.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_LARGE, QFont.Weight.Bold))
        titel.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(titel)

        # Info
        info_text = (
            f"Periode: {self.start_datum} t/m {self.eind_datum}\n"
            f"Aantal dagen: {self.dagen}"
        )
        info = QLabel(info_text)
        info.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(info)

        # Kies type
        type_layout = QHBoxLayout()
        type_label = QLabel("Toekennen als:")
        type_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        type_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        type_layout.addWidget(type_label)

        # Type combobox met codes
        verlof_code = TermCodeService.get_code_for_term('verlof')
        kd_code = TermCodeService.get_code_for_term('kompensatiedag')

        self.type_combo.addItem(f"Verlof ({verlof_code})", 'verlof')
        self.type_combo.addItem(f"Kompensatiedag ({kd_code})", 'kompensatiedag')
        self.type_combo.setStyleSheet(Styles.input_field())
        self.type_combo.setMinimumWidth(200)
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)  # type: ignore
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()

        layout.addLayout(type_layout)

        # Saldo info
        self.saldo_label.setWordWrap(True)
        self.saldo_label.setStyleSheet(f"""
            background-color: {Colors.BG_LIGHT};
            border: 1px solid {Colors.BORDER_LIGHT};
            border-radius: 4px;
            padding: {Dimensions.SPACING_MEDIUM}px;
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(self.saldo_label)

        # Buttons
        buttons = QDialogButtonBox()
        buttons.addButton("Goedkeuren", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Annuleren", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)  # type: ignore
        buttons.rejected.connect(self.reject)  # type: ignore
        layout.addWidget(buttons)

    def load_saldo(self) -> None:
        """Laad en toon saldo voor gekozen type"""
        from services.verlof_saldo_service import VerlofSaldoService
        from datetime import datetime

        jaar = datetime.now().year
        saldo = VerlofSaldoService.get_saldo(self.gebruiker_id, jaar)

        code_term = self.type_combo.currentData()

        if code_term == 'verlof':
            resterend = saldo['vv_resterend']
            type_naam = "Verlof"
        else:
            resterend = saldo['kd_resterend']
            type_naam = "KD"

        # Bepaal kleur
        nieuw_resterend = resterend - self.dagen
        if nieuw_resterend < 0:
            kleur = Colors.DANGER
            status = "LET OP: Tekort!"
        elif nieuw_resterend < 5:
            kleur = Colors.WARNING
            status = "Laag saldo"
        else:
            kleur = Colors.SUCCESS
            status = "OK"

        saldo_text = (
            f"<b>{type_naam} saldo ({jaar}):</b><br>"
            f"Resterend: {resterend} dagen<br>"
            f"Na goedkeuring: {nieuw_resterend} dagen<br>"
            f"<span style='color: {kleur};'><b>{status}</b></span>"
        )

        self.saldo_label.setText(saldo_text)

    def on_type_changed(self) -> None:
        """Type combobox gewijzigd"""
        self.load_saldo()

    def get_code_term(self) -> str:
        """Haal gekozen term op"""
        return self.type_combo.currentData()


class WeigeringRedenDialog(QDialog):
    """Dialog voor reden van weigering"""

    def __init__(self, parent: QWidget, naam: str):
        super().__init__(parent)
        self.naam = naam

        self.setWindowTitle("Reden van Weigering")
        self.setModal(True)
        self.setMinimumWidth(500)

        # Instance attributes
        self.reden_input: QTextEdit = QTextEdit()

        self.init_ui()

    def init_ui(self) -> None:
        """Initialiseer UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Titel
        titel = QLabel(f"Verlof weigeren voor {self.naam}")
        titel.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_LARGE, QFont.Weight.Bold))
        layout.addWidget(titel)

        # Info
        info = QLabel("Geef een reden voor de weigering (verplicht):")
        info.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        layout.addWidget(info)

        # Reden input
        self.reden_input.setPlaceholderText(
            "Bijv. Te weinig bezetting in deze periode, "
            "overlapping met andere verloven..."
        )
        self.reden_input.setMinimumHeight(100)
        self.reden_input.setStyleSheet(Styles.input_field())
        layout.addWidget(self.reden_input)

        # Buttons
        buttons = QDialogButtonBox()
        buttons.addButton("Weigeren", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Annuleren", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.valideer_en_accept)  # type: ignore
        buttons.rejected.connect(self.reject)  # type: ignore
        layout.addWidget(buttons)

    def valideer_en_accept(self) -> None:
        """Valideer input"""
        if not self.reden_input.toPlainText().strip():
            QMessageBox.warning(
                self,
                "Reden Verplicht",
                "Je moet een reden opgeven voor de weigering."
            )
            return

        self.accept()

    def get_reden(self) -> str:
        """Haal reden op"""
        return self.reden_input.toPlainText().strip()