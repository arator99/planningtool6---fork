# gui/widgets/planner_grid_kalender.py
"""
Planner Grid Kalender
Editable kalender voor planners met buffer dagen en scroll functionaliteit
UPDATED: Editable cellen met keyboard navigatie en save functionaliteit
"""
from typing import Dict, Optional, Set
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QComboBox, QScrollArea, QWidget, QGridLayout,
                             QDialog, QLineEdit, QMessageBox, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from gui.widgets.grid_kalender_base import GridKalenderBase
from gui.styles import Styles, Colors, Fonts, Dimensions
from datetime import datetime, timedelta
from database.connection import get_connection
from services.data_ensure_service import ensure_jaar_data
import sqlite3


class EditableLabel(QLabel):
    """
    Label die editable wordt bij klik
    """
    edit_started: pyqtSignal = pyqtSignal()
    edit_finished: pyqtSignal = pyqtSignal(str)  # nieuwe waarde

    def __init__(self, text: str, datum_str: str, gebruiker_id: int, parent_grid):
        super().__init__(text)
        self.datum_str = datum_str
        self.gebruiker_id = gebruiker_id
        self.parent_grid = parent_grid
        self.editor: Optional[QLineEdit] = None
        self.is_editing = False

    def mousePressEvent(self, event):
        """Start edit mode bij klik"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_edit()
        super().mousePressEvent(event)

    def start_edit(self):
        """Start edit mode"""
        if self.is_editing:
            return

        self.is_editing = True
        self.edit_started.emit()  # type: ignore

        # Maak editor
        self.editor = QLineEdit(self)
        self.editor.setText(self.text())
        self.editor.setMaxLength(5)
        self.editor.setGeometry(self.rect())
        self.editor.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #2196F3;
                padding: 2px;
                font-weight: bold;
            }
        """)

        # Uppercase automatisch
        def to_upper():
            pos = self.editor.cursorPosition()
            self.editor.setText(self.editor.text().upper())
            self.editor.setCursorPosition(pos)

        self.editor.textChanged.connect(to_upper)  # type: ignore
        self.editor.editingFinished.connect(self.finish_edit)  # type: ignore

        # Focus en selecteer alles
        self.editor.show()
        self.editor.setFocus()
        self.editor.selectAll()

        # Install event filter voor keyboard
        self.editor.installEventFilter(self)

    def finish_edit(self):
        """Beëindig edit mode"""
        if not self.is_editing or not self.editor:
            return

        nieuwe_waarde = self.editor.text().strip().upper()
        self.editor.deleteLater()
        self.editor = None
        self.is_editing = False

        # Emit signal met nieuwe waarde
        self.edit_finished.emit(nieuwe_waarde)  # type: ignore

    def eventFilter(self, obj, event):
        """Handle keyboard events in editor"""
        if obj == self.editor and event.type() == event.Type.KeyPress:
            key = event.key()

            if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                # ENTER = finish en ga naar cel eronder
                self.finish_edit()
                self.parent_grid.navigate_to_cell(self.datum_str, self.gebruiker_id, 'down')
                return True

            elif key == Qt.Key.Key_Tab:
                # TAB = finish en ga naar volgende cel
                self.finish_edit()
                self.parent_grid.navigate_to_cell(self.datum_str, self.gebruiker_id, 'next')
                return True

            elif key == Qt.Key.Key_Backtab:  # SHIFT+TAB
                # SHIFT+TAB = finish en ga naar vorige cel
                self.finish_edit()
                self.parent_grid.navigate_to_cell(self.datum_str, self.gebruiker_id, 'prev')
                return True

            elif key == Qt.Key.Key_Escape:
                # ESC = cancel
                if self.editor:
                    self.editor.setText(self.text())  # Reset to original
                self.finish_edit()
                return True

            # NIEUW: Arrow keys
            elif key == Qt.Key.Key_Up:
                # Arrow UP = finish en ga naar cel erboven
                self.finish_edit()
                self.parent_grid.navigate_to_cell(self.datum_str, self.gebruiker_id, 'up')
                return True

            elif key == Qt.Key.Key_Down:
                # Arrow DOWN = finish en ga naar cel eronder
                self.finish_edit()
                self.parent_grid.navigate_to_cell(self.datum_str, self.gebruiker_id, 'down')
                return True

            elif key == Qt.Key.Key_Left:
                # Arrow LEFT = finish en ga naar vorige cel (links)
                self.finish_edit()
                self.parent_grid.navigate_to_cell(self.datum_str, self.gebruiker_id, 'left')
                return True

            elif key == Qt.Key.Key_Right:
                # Arrow RIGHT = finish en ga naar volgende cel (rechts)
                self.finish_edit()
                self.parent_grid.navigate_to_cell(self.datum_str, self.gebruiker_id, 'right')
                return True

        return super().eventFilter(obj, event)


class PlannerGridKalender(GridKalenderBase):
    """
    Grid kalender voor planners
    - Volledige maand + 8 dagen buffer voor/na
    - Horizontaal scrollable
    - Alle teamleden (met filter)
    - Editable cellen met keyboard navigatie
    - Verlof status overlays
    """

    # Signals
    cel_clicked: pyqtSignal = pyqtSignal(str, int)  # (datum_str, gebruiker_id)
    data_changed: pyqtSignal = pyqtSignal()  # Planning gewijzigd
    maand_changed: pyqtSignal = pyqtSignal()  # Maand gewijzigd (navigatie)

    def __init__(self, jaar: int, maand: int):
        super().__init__(jaar, maand)

        # Editable state
        self.valid_codes: Set[str] = set()  # Alle codes (voor algemene check)
        self.valid_codes_per_dag: Dict[str, Set[str]] = {
            'weekdag': set(),
            'zaterdag': set(),
            'zondag': set()
        }  # Codes per dag_type
        self.speciale_codes: Set[str] = set()  # Speciale codes (altijd geldig)
        self.cel_widgets: Dict[str, Dict[int, EditableLabel]] = {}  # {datum: {user_id: widget}}
        self.feestdag_namen: Dict[str, str] = {}  # {datum_str: naam} - feestdag namen

        self.init_ui()
        self.load_initial_data()

    def set_valid_codes(self, codes: Set[str], codes_per_dag: Dict[str, Set[str]], speciale: Set[str]):
        """Set valid codes voor validatie (called by parent screen)"""
        self.valid_codes = codes
        self.valid_codes_per_dag = codes_per_dag
        self.speciale_codes = speciale

    def init_ui(self) -> None:
        """Bouw UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)
        layout.setContentsMargins(
            Dimensions.MARGIN_MEDIUM,
            Dimensions.MARGIN_MEDIUM,
            Dimensions.MARGIN_MEDIUM,
            Dimensions.MARGIN_MEDIUM
        )

        # Header met controls
        header = self.create_header()
        layout.addLayout(header)

        # Info label
        self.info_label = QLabel()
        self.info_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY))
        self.info_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")
        self.update_info_label()
        layout.addWidget(self.info_label)

        # Scroll area met grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Grid container (wordt gevuld door build_grid)
        self.grid_container = QWidget()
        self.scroll_area.setWidget(self.grid_container)

        layout.addWidget(self.scroll_area)

    def create_header(self) -> QHBoxLayout:
        """Maak header met jaar/maand selectie en filter"""
        header = QHBoxLayout()

        # Titel
        self.title_label = QLabel()
        self.title_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_LARGE))
        self.update_title()
        header.addWidget(self.title_label)

        header.addStretch()

        # Navigatie knoppen
        vorige_btn = QPushButton("← Vorige Maand")
        vorige_btn.setFixedSize(130, Dimensions.BUTTON_HEIGHT_NORMAL)
        vorige_btn.clicked.connect(self.vorige_maand)  # type: ignore
        vorige_btn.setStyleSheet(Styles.button_secondary())
        header.addWidget(vorige_btn)

        volgende_btn = QPushButton("Volgende Maand →")
        volgende_btn.setFixedSize(150, Dimensions.BUTTON_HEIGHT_NORMAL)
        volgende_btn.clicked.connect(self.volgende_maand)  # type: ignore
        volgende_btn.setStyleSheet(Styles.button_secondary())
        header.addWidget(volgende_btn)

        # Filter knop
        filter_btn = QPushButton("Filter Teamleden")
        filter_btn.setFixedSize(150, Dimensions.BUTTON_HEIGHT_NORMAL)
        filter_btn.clicked.connect(self.open_filter_dialog)  # type: ignore
        filter_btn.setStyleSheet(Styles.button_secondary())
        header.addWidget(filter_btn)

        # Jaar selector
        jaar_label = QLabel("Jaar:")
        jaar_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        header.addWidget(jaar_label)

        self.jaar_combo = QComboBox()
        self.jaar_combo.setFixedWidth(100)
        jaren = [str(jaar) for jaar in range(datetime.now().year - 1, datetime.now().year + 3)]
        self.jaar_combo.addItems(jaren)
        self.jaar_combo.setCurrentText(str(self.jaar))
        self.jaar_combo.currentTextChanged.connect(self.on_jaar_changed)  # type: ignore
        header.addWidget(self.jaar_combo)

        # Maand selector
        maand_label = QLabel("Maand:")
        maand_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        header.addWidget(maand_label)

        self.maand_combo = QComboBox()
        self.maand_combo.setFixedWidth(120)
        maanden = ['Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni',
                   'Juli', 'Augustus', 'September', 'Oktober', 'November', 'December']
        self.maand_combo.addItems(maanden)
        self.maand_combo.setCurrentIndex(self.maand - 1)
        self.maand_combo.currentIndexChanged.connect(self.on_maand_changed)  # type: ignore
        header.addWidget(self.maand_combo)

        return header

    def update_title(self) -> None:
        """Update titel met maand/jaar"""
        maanden = ['Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni',
                   'Juli', 'Augustus', 'September', 'Oktober', 'November', 'December']
        self.title_label.setText(f"Planning {maanden[self.maand - 1]} {self.jaar}")

    def update_info_label(self) -> None:
        """Update info label met buffer info"""
        self.info_label.setText(
            "Klik op cel om shift te bewerken • TAB=volgende • ENTER=eronder • ESC=annuleer • "
            "Rechtsklik voor opties"
        )

    def load_initial_data(self) -> None:
        """Laad initiële data"""
        # Laad gebruikers (filter wordt automatisch behouden door base class)
        self.load_gebruikers(alleen_actief=True)

        # Laad feestdagen voor huidig jaar EN aangrenzende jaren (voor buffer dagen)
        self.load_feestdagen_extended()

        # Laad rode lijnen (28-daagse HR-cycli)
        self.load_rode_lijnen()

        # Datum range: maand + 8 dagen buffer
        datum_lijst = self.get_datum_lijst(start_offset=8, eind_offset=8)
        if datum_lijst:
            start_datum = datum_lijst[0][0]
            eind_datum = datum_lijst[-1][0]

            # Laad planning en verlof
            self.load_planning_data(start_datum, eind_datum)
            self.load_verlof_data(start_datum, eind_datum)

        # Bouw grid
        self.build_grid()

    def load_feestdagen_extended(self) -> None:
        """Laad feestdagen voor huidig jaar + vorig/volgend jaar (voor buffer dagen)"""
        jaren = [self.jaar - 1, self.jaar, self.jaar + 1]

        # Zorg dat feestdagen bestaan voor alle jaren
        for jaar in jaren:
            ensure_jaar_data(jaar)

        # Laad feestdagen met namen
        conn = get_connection()
        cursor = conn.cursor()
        self.feestdagen = []
        self.feestdag_namen = {}  # Reset dictionary
        for jaar in jaren:
            cursor.execute("""
                SELECT datum, naam FROM feestdagen
                WHERE datum LIKE ?
            """, (f"{jaar}-%",))
            for row in cursor.fetchall():
                datum_str = row['datum']
                self.feestdagen.append(datum_str)
                self.feestdag_namen[datum_str] = row['naam']
        conn.close()

    def load_rode_lijnen(self) -> None:
        """Laad rode lijnen (28-daagse HR-cycli) voor huidige periode"""
        conn = get_connection()
        cursor = conn.cursor()

        # Laad alle rode lijnen start datums (deze markeren begin van een nieuwe periode)
        cursor.execute("""
            SELECT start_datum, eind_datum, periode_nummer
            FROM rode_lijnen
            ORDER BY start_datum
        """)

        # Dictionary met start_datum als key voor snelle lookup
        # Converteer datetime naar date string (YYYY-MM-DD)
        self.rode_lijnen_starts: Dict[str, int] = {}
        for row in cursor.fetchall():
            datum_str = row['start_datum']
            # Strip timestamp als die er is (2024-07-28T00:00:00 -> 2024-07-28)
            if 'T' in datum_str:
                datum_str = datum_str.split('T')[0]
            self.rode_lijnen_starts[datum_str] = row['periode_nummer']

        conn.close()

    def build_grid(self) -> None:
        """Bouw de grid met namen en datums"""
        # Clear bestaande layout
        if self.grid_container.layout():
            QWidget().setLayout(self.grid_container.layout())

        # Reset cel widgets
        self.cel_widgets.clear()

        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Haal datum lijst en zichtbare gebruikers
        datum_lijst = self.get_datum_lijst(start_offset=8, eind_offset=8)
        zichtbare_gebruikers = self.get_zichtbare_gebruikers()

        if not zichtbare_gebruikers:
            # Geen gebruikers geselecteerd
            info = QLabel("Geen teamleden geselecteerd. Gebruik de filter knop.")
            info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: 20px;")
            grid_layout.addWidget(info, 0, 0)
            self.grid_container.setLayout(grid_layout)
            return

        # Header rij: namen kolom + datums
        naam_header = QLabel("Teamlid")
        naam_header.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL, QFont.Weight.Bold))
        naam_header.setStyleSheet(f"""
            QLabel {{
                background-color: {Colors.PRIMARY};
                color: white;
                padding: 8px;
                border: 1px solid {Colors.BORDER_LIGHT};
                qproperty-alignment: AlignCenter;
            }}
        """)
        naam_header.setFixedWidth(280)  # Verhoogd van 200 naar 280 voor lange namen
        grid_layout.addWidget(naam_header, 0, 0)

        # Datum headers
        for col, (datum_str, label) in enumerate(datum_lijst, start=1):
            datum_header = QLabel(label)
            datum_header.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY, QFont.Weight.Bold))

            # Achtergrond kleur voor header
            achtergrond = self.get_datum_achtergrond(datum_str)

            # Check of dit het begin van een rode lijn periode is
            is_rode_lijn_start = datum_str in self.rode_lijnen_starts

            # Highlight huidige maand dagen
            datum_obj = datetime.strptime(datum_str, '%Y-%m-%d')
            if datum_obj.month == self.maand:
                # Huidige maand: donkerder border
                border_style = f"2px solid {Colors.PRIMARY}"
            else:
                # Buffer dagen: normale border
                border_style = f"1px solid {Colors.BORDER_LIGHT}"

            # Rode lijn: dikke rode linker border
            if is_rode_lijn_start:
                periode_nr = self.rode_lijnen_starts[datum_str]
                datum_header.setStyleSheet(f"""
                    QLabel {{
                        background-color: {achtergrond};
                        color: #000000;
                        padding: 4px;
                        border: {border_style};
                        border-left: 4px solid #dc3545;
                        qproperty-alignment: AlignCenter;
                    }}
                """)
                # Tooltip met periode nummer
                datum_header.setToolTip(f"Start Rode Lijn Periode {periode_nr}")
            else:
                datum_header.setStyleSheet(f"""
                    QLabel {{
                        background-color: {achtergrond};
                        color: #000000;
                        padding: 4px;
                        border: {border_style};
                        qproperty-alignment: AlignCenter;
                    }}
                """)

            datum_header.setFixedWidth(60)
            grid_layout.addWidget(datum_header, 0, col)

        # Data rijen: per gebruiker
        for row, gebruiker in enumerate(zichtbare_gebruikers, start=1):
            gebruiker_id = gebruiker['id']

            # Naam kolom
            naam_label = QLabel(gebruiker['volledige_naam'])
            naam_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
            naam_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {Colors.BG_LIGHT};
                    padding: 8px;
                    border: 1px solid {Colors.BORDER_LIGHT};
                }}
            """)
            naam_label.setFixedWidth(280)  # Verhoogd van 200 naar 280 voor lange namen
            grid_layout.addWidget(naam_label, row, 0)

            # Shift cellen (editable)
            for col, (datum_str, _) in enumerate(datum_lijst, start=1):
                cel = self.create_editable_cel(datum_str, gebruiker_id)
                cel.setFixedWidth(60)
                grid_layout.addWidget(cel, row, col)

                # Track widget
                if datum_str not in self.cel_widgets:
                    self.cel_widgets[datum_str] = {}
                self.cel_widgets[datum_str][gebruiker_id] = cel

        self.grid_container.setMaximumHeight(grid_layout.rowCount() * Dimensions.TABLE_ROW_HEIGHT)
        self.grid_container.setLayout(grid_layout)

    def create_editable_cel(self, datum_str: str, gebruiker_id: int) -> EditableLabel:
        """Maak editable cel voor shift weergave"""
        # Haal shift code op
        shift_code = self.get_display_code(datum_str, gebruiker_id)

        # Check of er een notitie is
        heeft_notitie = False
        if datum_str in self.planning_data and gebruiker_id in self.planning_data[datum_str]:
            notitie = self.planning_data[datum_str][gebruiker_id].get('notitie', '')
            heeft_notitie = bool(notitie and notitie.strip())

        # Display text (zonder notitie indicator - die komt via CSS)
        display_text = shift_code

        # Bepaal achtergrond en overlay
        achtergrond = self.get_datum_achtergrond(datum_str)
        overlay = self.get_verlof_overlay(datum_str, gebruiker_id, 'planner')

        # Check of dit een buffer dag is
        datum_obj = datetime.strptime(datum_str, '%Y-%m-%d')
        is_buffer = datum_obj.month != self.maand

        # Check of dit het begin van een rode lijn periode is
        is_rode_lijn_start = datum_str in self.rode_lijnen_starts


        # Maak editable label (met display_text ipv shift_code)
        cel = EditableLabel(display_text, datum_str, gebruiker_id, self)
        cel.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL, QFont.Weight.Bold))

        # Stylesheet met optionele rode lijn en notitie indicator
        base_style = self.create_cel_stylesheet(achtergrond, overlay)

        # Rode lijn indicator (linker border)
        if is_rode_lijn_start:
            base_style = base_style.replace(
                "border: 1px solid",
                "border: 1px solid"
            ).replace(
                "qproperty-alignment: AlignCenter;",
                "border-left: 4px solid #dc3545;\n                    qproperty-alignment: AlignCenter;"
            )

        # Notitie indicator (rechter boven corner accent)
        if heeft_notitie:
            base_style = base_style.replace(
                "border: 1px solid",
                "border: 1px solid"
            ).replace(
                "qproperty-alignment: AlignCenter;",
                "border-top: 3px solid #17a2b8;\n                    border-right: 3px solid #17a2b8;\n                    qproperty-alignment: AlignCenter;"
            )

        if is_buffer:
            cel.setStyleSheet(base_style + " QLabel { opacity: 0.7; }")
        else:
            cel.setStyleSheet(base_style)

        # Tooltip
        tooltip = self.get_cel_tooltip(datum_str, gebruiker_id, 'planner')
        if is_rode_lijn_start:
            periode_nr = self.rode_lijnen_starts[datum_str]
            rode_lijn_tooltip = f"Start Rode Lijn Periode {periode_nr}"
            tooltip = f"{tooltip}\n{rode_lijn_tooltip}" if tooltip else rode_lijn_tooltip
        if heeft_notitie:
            notitie_tooltip = "Heeft notitie (klik rechts -> Notitie bewerken)"
            tooltip = f"{tooltip}\n{notitie_tooltip}" if tooltip else notitie_tooltip
        if tooltip:
            cel.setToolTip(tooltip)

        # Connect signals
        cel.edit_finished.connect(lambda code: self.on_cel_edited(datum_str, gebruiker_id, code))  # type: ignore

        # Context menu
        cel.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        cel.customContextMenuRequested.connect(  # type: ignore
            lambda pos: self.show_context_menu(cel, datum_str, gebruiker_id)
        )

        # Cursor
        cel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        return cel

    def on_cel_edited(self, datum_str: str, gebruiker_id: int, code: str):
        """Handle cel edit"""
        if not code:
            # Lege cel = delete
            self.delete_shift(datum_str, gebruiker_id)
            return

        # Check of code überhaupt bestaat
        if code not in self.valid_codes:
            QMessageBox.warning(
                self,
                "Ongeldige Code",
                f"'{code}' is geen geldige shift code.\n\n"
                f"Check de codes lijst in het scherm."
            )
            # Reset cel
            if datum_str in self.cel_widgets and gebruiker_id in self.cel_widgets[datum_str]:
                oude_code = self.get_display_code(datum_str, gebruiker_id)
                self.cel_widgets[datum_str][gebruiker_id].setText(oude_code)
            return

        # Check of het een speciale code is (altijd geldig)
        if code in self.speciale_codes:
            self.save_shift(datum_str, gebruiker_id, code)
            return

        # Voor shift codes: check dag_type
        dag_type = self.bepaal_dag_type(datum_str)

        if code not in self.valid_codes_per_dag[dag_type]:
            # Bepaal welke dag_types deze code WEL heeft
            gevonden_types = [dt for dt, codes in self.valid_codes_per_dag.items() if code in codes]

            if gevonden_types:
                types_str = ', '.join(gevonden_types)

                # Check of het een feestdag is voor specifieke melding
                is_feestdag = datum_str in self.feestdagen
                if is_feestdag:
                    # Haal feestdag naam op
                    feestdag_naam = self.get_feestdag_naam(datum_str)
                    dag_beschrijving = f"een feestdag ({feestdag_naam})"
                    extra_info = "Op feestdagen moeten zondagdiensten worden gebruikt."
                else:
                    # Gewone zondag/zaterdag/weekdag
                    dag_beschrijving = f"een {dag_type}"
                    extra_info = f"Gebruik een shift code voor {dag_type}."

                QMessageBox.warning(
                    self,
                    "Verkeerde Dag Type",
                    f"'{code}' is een {types_str} shift.\n\n"
                    f"Deze datum is {dag_beschrijving}.\n"
                    f"{extra_info}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Ongeldige Code",
                    f"'{code}' is geen geldige shift code."
                )

            # Reset cel
            if datum_str in self.cel_widgets and gebruiker_id in self.cel_widgets[datum_str]:
                oude_code = self.get_display_code(datum_str, gebruiker_id)
                self.cel_widgets[datum_str][gebruiker_id].setText(oude_code)
            return

        # Alles OK - save
        self.save_shift(datum_str, gebruiker_id, code)

    def bepaal_dag_type(self, datum_str: str) -> str:
        """
        Bepaal dag_type voor een datum
        Returns: 'weekdag', 'zaterdag', of 'zondag'
        """
        datum = datetime.strptime(datum_str, '%Y-%m-%d')
        weekdag = datum.weekday()  # 0=Ma, 6=Zo

        # Zondag of feestdag
        if weekdag == 6 or datum_str in self.feestdagen:
            return 'zondag'
        # Zaterdag
        elif weekdag == 5:
            return 'zaterdag'
        # Weekdag (ma-vr)
        else:
            return 'weekdag'

    def get_feestdag_naam(self, datum_str: str) -> str:
        """Haal feestdag naam op voor een datum"""
        return self.feestdag_namen.get(datum_str, "Feestdag")

    def save_shift(self, datum_str: str, gebruiker_id: int, shift_code: str):
        """Sla shift op in database"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO planning (gebruiker_id, datum, shift_code, status)
                VALUES (?, ?, ?, 'concept')
                ON CONFLICT(gebruiker_id, datum) 
                DO UPDATE SET shift_code = ?
                WHERE status = 'concept'
            """, (gebruiker_id, datum_str, shift_code, shift_code))

            conn.commit()
            conn.close()

            # Update cel display
            if datum_str in self.cel_widgets and gebruiker_id in self.cel_widgets[datum_str]:
                self.cel_widgets[datum_str][gebruiker_id].setText(shift_code)

            # Emit signal
            self.data_changed.emit()  # type: ignore

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon shift niet opslaan:\n{e}")

    def delete_shift(self, datum_str: str, gebruiker_id: int):
        """Verwijder shift uit database"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM planning
                WHERE gebruiker_id = ? AND datum = ?
                  AND status = 'concept'
            """, (gebruiker_id, datum_str))

            conn.commit()
            conn.close()

            # Update cel display
            if datum_str in self.cel_widgets and gebruiker_id in self.cel_widgets[datum_str]:
                self.cel_widgets[datum_str][gebruiker_id].setText("")

            # Emit signal
            self.data_changed.emit()  # type: ignore

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon shift niet verwijderen:\n{e}")

    def edit_notitie(self, datum_str: str, gebruiker_id: int):
        """Bewerk of verwijder notitie voor cel"""
        from PyQt6.QtWidgets import QTextEdit, QDialog, QVBoxLayout, QPushButton, QHBoxLayout
        from datetime import datetime

        # Haal huidige notitie op (uit planning_data of database)
        huidige_notitie = ""
        if datum_str in self.planning_data and gebruiker_id in self.planning_data[datum_str]:
            huidige_notitie = self.planning_data[datum_str][gebruiker_id].get('notitie', '') or ""

        # Haal gebruikersnaam op
        gebruiker_naam = "Onbekend"
        for user in self.gebruikers_data:
            if user['id'] == gebruiker_id:
                gebruiker_naam = user['volledige_naam']
                break

        # Format datum voor display
        try:
            datum_obj = datetime.strptime(datum_str, '%Y-%m-%d')
            datum_display = datum_obj.strftime('%d-%m-%Y')
        except (ValueError, TypeError):
            datum_display = datum_str

        # Maak dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Notitie: {gebruiker_naam} - {datum_display}")
        dialog.setModal(True)
        dialog.resize(500, 300)

        layout = QVBoxLayout(dialog)

        # Text editor
        text_edit = QTextEdit()
        text_edit.setPlainText(huidige_notitie)
        text_edit.setPlaceholderText("Bijv: Afspraak arbeidsgeneesheer 15u - late shift nodig")
        layout.addWidget(text_edit)

        # Buttons
        button_layout = QHBoxLayout()

        verwijder_btn = QPushButton("Verwijder Notitie")
        verwijder_btn.setStyleSheet(Styles.button_warning())
        verwijder_btn.clicked.connect(lambda: text_edit.setPlainText(""))  # type: ignore
        button_layout.addWidget(verwijder_btn)

        button_layout.addStretch()

        annuleer_btn = QPushButton("Annuleren")
        annuleer_btn.clicked.connect(dialog.reject)  # type: ignore
        button_layout.addWidget(annuleer_btn)

        opslaan_btn = QPushButton("Opslaan")
        opslaan_btn.setStyleSheet(Styles.button_primary())
        opslaan_btn.clicked.connect(dialog.accept)  # type: ignore
        button_layout.addWidget(opslaan_btn)

        layout.addLayout(button_layout)

        # Toon dialog
        if dialog.exec():
            nieuwe_notitie = text_edit.toPlainText().strip()

            # Opslaan in database
            try:
                conn = get_connection()
                cursor = conn.cursor()

                # Check of record bestaat
                cursor.execute("""
                    SELECT id FROM planning
                    WHERE gebruiker_id = ? AND datum = ?
                """, (gebruiker_id, datum_str))

                row = cursor.fetchone()

                if row:
                    # Update bestaand record
                    cursor.execute("""
                        UPDATE planning
                        SET notitie = ?
                        WHERE gebruiker_id = ? AND datum = ?
                    """, (nieuwe_notitie if nieuwe_notitie else None, gebruiker_id, datum_str))
                else:
                    # Maak nieuw record (alleen met notitie, geen shift_code)
                    cursor.execute("""
                        INSERT INTO planning (gebruiker_id, datum, notitie, status)
                        VALUES (?, ?, ?, 'concept')
                    """, (gebruiker_id, datum_str, nieuwe_notitie))

                conn.commit()
                conn.close()

                # Refresh grid
                self.load_initial_data()

                # Success feedback
                if nieuwe_notitie:
                    QMessageBox.information(self, "Notitie Opgeslagen", "✓ Notitie is opgeslagen.")
                else:
                    QMessageBox.information(self, "Notitie Verwijderd", "✓ Notitie is verwijderd.")

            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Fout", f"Kon notitie niet opslaan:\n{e}")

    def navigate_to_cell(self, huidige_datum: str, huidige_gebruiker_id: int, richting: str):
        """Navigeer naar andere cel"""
        datum_lijst = self.get_datum_lijst(start_offset=8, eind_offset=8)
        gebruikers = self.get_zichtbare_gebruikers()

        # Vind huidige positie
        datum_index = next((i for i, (d, _) in enumerate(datum_lijst) if d == huidige_datum), None)
        gebruiker_index = next((i for i, u in enumerate(gebruikers) if u['id'] == huidige_gebruiker_id), None)

        if datum_index is None or gebruiker_index is None:
            return

        # Bepaal nieuwe positie
        nieuwe_datum_index = datum_index
        nieuwe_gebruiker_index = gebruiker_index

        if richting == 'next' or richting == 'right':
            # TAB of Arrow Right - volgende kolom, wrap to next row
            nieuwe_datum_index += 1
            if nieuwe_datum_index >= len(datum_lijst):
                nieuwe_datum_index = 0
                nieuwe_gebruiker_index += 1

        elif richting == 'prev' or richting == 'left':
            # SHIFT+TAB of Arrow Left - vorige kolom
            nieuwe_datum_index -= 1
            if nieuwe_datum_index < 0:
                nieuwe_datum_index = len(datum_lijst) - 1
                nieuwe_gebruiker_index -= 1

        elif richting == 'down':
            # ENTER of Arrow Down - volgende rij
            nieuwe_gebruiker_index += 1

        elif richting == 'up':
            # Arrow Up - vorige rij
            nieuwe_gebruiker_index -= 1

        # Check bounds
        if nieuwe_datum_index < 0 or nieuwe_datum_index >= len(datum_lijst):
            return
        if nieuwe_gebruiker_index < 0 or nieuwe_gebruiker_index >= len(gebruikers):
            return

        # Activeer nieuwe cel
        nieuwe_datum = datum_lijst[nieuwe_datum_index][0]
        nieuwe_gebruiker_id = gebruikers[nieuwe_gebruiker_index]['id']

        if nieuwe_datum in self.cel_widgets and nieuwe_gebruiker_id in self.cel_widgets[nieuwe_datum]:
            self.cel_widgets[nieuwe_datum][nieuwe_gebruiker_id].start_edit()

    def show_context_menu(self, cel: EditableLabel, datum_str: str, gebruiker_id: int):
        """Toon context menu bij rechtsklik"""
        menu = QMenu(self)

        # Notitie toevoegen/bewerken
        notitie_action = menu.addAction("Notitie toevoegen/bewerken")
        notitie_action.triggered.connect(lambda: self.edit_notitie(datum_str, gebruiker_id))  # type: ignore

        menu.addSeparator()

        # Verwijder
        delete_action = menu.addAction("Verwijder shift")
        delete_action.triggered.connect(lambda: self.delete_shift(datum_str, gebruiker_id))  # type: ignore

        # Vul week (als cel niet leeg)
        if cel.text():
            menu.addSeparator()
            vul_week_action = menu.addAction(f"Vul hele week met '{cel.text()}'")
            vul_week_action.triggered.connect(  # type: ignore
                lambda: self.vul_week(datum_str, gebruiker_id, cel.text())
            )

        menu.exec(QCursor.pos())

    def vul_week(self, start_datum: str, gebruiker_id: int, code: str):
        """Vul 7 dagen met zelfde code"""
        reply = QMessageBox.question(
            self,
            "Vul Week",
            f"7 dagen vullen met '{code}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Vul 7 dagen
        datum = datetime.strptime(start_datum, '%Y-%m-%d')
        for i in range(7):
            nieuwe_datum = (datum + timedelta(days=i)).strftime('%Y-%m-%d')
            self.save_shift(nieuwe_datum, gebruiker_id, code)

    def open_filter_dialog(self) -> None:
        """Open dialog om gebruikers te filteren"""
        from gui.widgets.teamlid_grid_kalender import FilterDialog
        dialog = FilterDialog(self.gebruikers_data, self.filter_gebruikers, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.filter_gebruikers = dialog.get_filter()
            self.build_grid()

    def vorige_maand(self) -> None:
        """Navigeer naar vorige maand"""
        if self.maand == 1:
            self.refresh_data(self.jaar - 1, 12)
            self.jaar_combo.setCurrentText(str(self.jaar))
            self.maand_combo.setCurrentIndex(11)
        else:
            self.refresh_data(self.jaar, self.maand - 1)
            self.maand_combo.setCurrentIndex(self.maand - 1)

    def volgende_maand(self) -> None:
        """Navigeer naar volgende maand"""
        if self.maand == 12:
            self.refresh_data(self.jaar + 1, 1)
            self.jaar_combo.setCurrentText(str(self.jaar))
            self.maand_combo.setCurrentIndex(0)
        else:
            self.refresh_data(self.jaar, self.maand + 1)
            self.maand_combo.setCurrentIndex(self.maand - 1)

    def on_jaar_changed(self, jaar_str: str) -> None:
        """Jaar gewijzigd"""
        self.refresh_data(int(jaar_str), self.maand)

    def on_maand_changed(self, index: int) -> None:
        """Maand gewijzigd"""
        self.refresh_data(self.jaar, index + 1)

    def refresh_data(self, jaar: int, maand: int) -> None:
        """Herlaad data voor nieuwe jaar/maand"""
        self.jaar = jaar
        self.maand = maand
        self.update_title()
        self.load_initial_data()
        # Emit signal zodat parent screen kan reageren (bijv. status reload)
        self.maand_changed.emit()  # type: ignore