# gui/widgets/planner_grid_kalender.py
"""
Planner Grid Kalender
Editable kalender voor planners met buffer dagen en scroll functionaliteit

VERSION HISTORY:
- v0.6.17: Multi-cell selectie met Ctrl+Click en Shift+Click
- v0.6.19: HR rules visualisatie (rode lijnen werkdagen tracking)
- v0.6.20: Bemannings controle overlay met kleurcodering
- v0.6.25: PERFORMANCE - Gebruiker filtering en ValidationCache integratie
  * Accepteert optional gebruiker_ids parameter voor filtering
  * Filters gebruikers_data na load (alleen relevante users)
  * ValidationCache batch preload (900+ queries → 5 queries)
  * Speedup: 30-60s → 0.01-0.03s (2000x sneller)
- v0.6.26: VALIDATIE SYSTEEM - On-demand validation only (UX verbetering)
  * HR Violations: Rode/gele overlay op cellen (ALLEEN na "Valideer Planning" klik)
  * Bemannings Controle: Rood/oranje/groen overlay op datum headers (ALLEEN na knopklik)
  * Tooltips met violation en bemannings details per cel
  * Real-time validation VOLLEDIG DISABLED (validatie alleen op knopklik)
  * HR Summary Box toont instructie: "Klik op 'Valideer Planning' om HR regels te controleren"
  * Batch validatie via "Valideer Planning" knop (alle 6 HR checks + bemannings controle on-demand)
  * Scroll functionaliteit in summary box (max 200px)
"""
from typing import Dict, Optional, Set, List
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QComboBox, QScrollArea, QWidget, QGridLayout,
                             QDialog, QLineEdit, QMessageBox, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from gui.widgets.grid_kalender_base import GridKalenderBase
from gui.styles import Styles, Colors, Fonts, Dimensions
from datetime import datetime, timedelta, date
from database.connection import get_connection
from services.data_ensure_service import ensure_jaar_data
from services.bemannings_controle_service import controleer_bemanning
from services.planning_validator_service import PlanningValidator
from services.constraint_checker import Violation
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
        self.overlay_kleur: Optional[str] = None  # Track HR/verlof overlay (v0.6.28 - ISSUE-005 fix)

    def mousePressEvent(self, event):
        """Start edit mode bij klik (of toggle selectie met Ctrl/Shift)"""
        if event.button() == Qt.MouseButton.LeftButton:
            modifiers = event.modifiers()

            # Ctrl/Shift = toggle selectie (niet editeren)
            if modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
                self.parent_grid.toggle_cell_selection(self.datum_str, self.gebruiker_id, modifiers)
            else:
                # Normale klik = start edit
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

        # Bepaal achtergrond kleur (gebruik overlay als die er is - v0.6.28 ISSUE-005 fix)
        if self.overlay_kleur:
            background = self.overlay_kleur  # Behoud HR/verlof overlay tijdens edit
        else:
            background = "white"  # Default wit voor normale cellen

        self.editor.setStyleSheet(f"""
            QLineEdit {{
                background-color: {background};
                border: 2px solid #2196F3;
                padding: 2px;
                font-weight: bold;
            }}
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

    def __init__(self, jaar: int, maand: int, gebruiker_ids: Optional[List[int]] = None):
        super().__init__(jaar, maand)

        # PERFORMANCE (v0.6.25): Filter gebruikers - alleen laden wat nodig is
        self.filtered_gebruiker_ids = gebruiker_ids  # Optionele filter op gebruiker IDs

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

        # Multi-cell selection state
        self.selected_cells: Set[tuple] = set()  # Set van (datum_str, gebruiker_id) tuples
        self.last_clicked: Optional[tuple] = None  # (datum_str, gebruiker_id) voor range selectie
        self.selection_label: Optional[QLabel] = None  # Label om aantal geselecteerde cellen te tonen

        # HR rules state (rode lijnen werkdagen tracking)
        self.rode_lijn_periodes: Optional[Dict[str, Dict[str, str]]] = None  # {periode_type: {start, eind, nummer}}
        self.hr_werkdagen_cache: Dict[int, Dict[str, int]] = {}  # {gebruiker_id: {voor: X, na: Y}}
        self.hr_cel_widgets: Dict[int, Dict[str, QLabel]] = {}  # {gebruiker_id: {voor: QLabel, na: QLabel}}

        # Bemannings controle state (v0.6.20)
        self.bemannings_status: Dict[str, Dict] = {}  # {datum_str: {status, ontbrekende_codes, dubbele_codes, ...}}
        self.datum_header_widgets: Dict[str, QLabel] = {}  # {datum_str: QLabel} - voor real-time overlay updates

        # HR violations state (v0.6.26 - Fase 3)
        self.hr_violations: Dict[str, Dict[int, List]] = {}  # {datum_str: {gebruiker_id: [Violation, ...]}}

        self.init_ui()
        self.load_initial_data()

        # Focus policy zodat ESC key events werken
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_valid_codes(self, codes: Set[str], codes_per_dag: Dict[str, Set[str]], speciale: Set[str]):
        """Set valid codes voor validatie (called by parent screen)"""
        self.valid_codes = codes
        self.valid_codes_per_dag = codes_per_dag
        self.speciale_codes = speciale

    def get_laatste_dag_van_maand(self) -> int:
        """Get laatste dag nummer van huidige maand"""
        from calendar import monthrange
        _, laatste_dag = monthrange(self.jaar, self.maand)
        return laatste_dag

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

        # Header wordt nu extern toegevoegd door parent screen (zie planning_editor_screen.py)
        # header = self.create_header()
        # layout.addLayout(header)

        # Info label (verborgen - staat nu onderaan in planning editor als instructies)
        # self.info_label = QLabel()
        # self.info_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY))
        # self.info_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")
        # self.update_info_label()
        # layout.addWidget(self.info_label)

        # Selection label (altijd zichtbaar om layout verspringen te voorkomen)
        self.selection_label = QLabel(" ")  # Spatie als placeholder
        self.selection_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        self.selection_label.setStyleSheet(f"""
            QLabel {{
                background-color: white;
                color: {Colors.TEXT_PRIMARY};
                padding: 8px;
                border-radius: 4px;
                min-height: 20px;
            }}
        """)
        # ALTIJD zichtbaar (met spatie of tekst), nooit hide()
        layout.addWidget(self.selection_label)

        # FROZEN COLUMNS (v0.6.25) - Dual scroll area pattern
        # Splits grid in frozen deel (naam + HR) en scrollable deel (datums)
        h_layout = QHBoxLayout()
        h_layout.setSpacing(0)
        h_layout.setContentsMargins(0, 0, 0, 0)

        # LINKER deel: Frozen kolommen (naam + Voor RL + Na RL)
        self.frozen_scroll = QScrollArea()
        self.frozen_scroll.setWidgetResizable(True)
        self.frozen_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.frozen_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Sync met rechts
        self.frozen_container = QWidget()
        self.frozen_scroll.setWidget(self.frozen_container)
        # Width wordt dynamisch gezet in build_grid() (afhankelijk van HR kolommen)

        # RECHTER deel: Scrollable kolommen (datums)
        self.scrollable_scroll = QScrollArea()
        self.scrollable_scroll.setWidgetResizable(True)
        self.scrollable_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollable_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollable_container = QWidget()
        self.scrollable_scroll.setWidget(self.scrollable_container)

        # Synchroniseer vertical scrollbars (frozen volgt scrollable)
        self.scrollable_scroll.verticalScrollBar().valueChanged.connect(  # type: ignore
            self.frozen_scroll.verticalScrollBar().setValue
        )

        h_layout.addWidget(self.frozen_scroll)
        h_layout.addWidget(self.scrollable_scroll)

        layout.addLayout(h_layout)

        # HR Violations Summary Box (v0.6.26 - Fase 3 UX + ISSUE-006 fix)
        # Altijd zichtbaar met scroll functionaliteit
        self.hr_summary_scroll = QScrollArea()
        self.hr_summary_scroll.setWidgetResizable(True)
        self.hr_summary_scroll.setMaximumHeight(200)  # Max hoogte voor scroll
        self.hr_summary_scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.hr_summary_label = QLabel()
        self.hr_summary_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        self.hr_summary_label.setStyleSheet(f"""
            QLabel {{
                background-color: #FFF3CD;
                color: #856404;
                padding: 12px;
                border: 1px solid #FFEAA7;
                border-radius: 4px;
            }}
        """)
        self.hr_summary_label.setWordWrap(True)
        self.hr_summary_label.setTextFormat(Qt.TextFormat.RichText)
        self.hr_summary_label.setText(
            "<b>💡 Klik op 'Valideer Planning' om alle controles uit te voeren</b><br>"
            "<i>Validatie controleert:<br>"
            "• HR Regels: 12u rust, max 50u/week, max 19 werkdagen/cyclus, "
            "max 7 dagen tussen rustdagen, max 7 opeenvolgende werkdagen, max 6 weekends achter elkaar<br>"
            "• Bemannings Controle: volledig/dubbel/onvolledig bemand per dag (kritische shifts)</i>"
        )  # Default tekst (geen validatie uitgevoerd)

        self.hr_summary_scroll.setWidget(self.hr_summary_label)
        layout.addWidget(self.hr_summary_scroll)

    def get_header_extra_buttons(self) -> List[QPushButton]:
        """Voeg vorige/volgende maand buttons toe (planner-specifiek)"""
        buttons = []

        vorige_btn = QPushButton("← Vorige Maand")
        vorige_btn.setFixedSize(130, Dimensions.BUTTON_HEIGHT_NORMAL)
        vorige_btn.clicked.connect(self.vorige_maand)  # type: ignore
        vorige_btn.setStyleSheet(Styles.button_secondary())
        buttons.append(vorige_btn)

        volgende_btn = QPushButton("Volgende Maand →")
        volgende_btn.setFixedSize(150, Dimensions.BUTTON_HEIGHT_NORMAL)
        volgende_btn.clicked.connect(self.volgende_maand)  # type: ignore
        volgende_btn.setStyleSheet(Styles.button_secondary())
        buttons.append(volgende_btn)

        # Valideer Planning knop (v0.6.26 - BUG FIX voor batch validatie)
        valideer_btn = QPushButton("Valideer Planning")
        valideer_btn.setFixedSize(140, Dimensions.BUTTON_HEIGHT_NORMAL)
        valideer_btn.clicked.connect(self.on_valideer_planning_clicked)  # type: ignore
        valideer_btn.setStyleSheet(Styles.button_primary())
        valideer_btn.setToolTip(
            "Controleer alle HR regels en bemannings status voor deze maand\n"
            "- HR violations: 12u rust, 50u/week, 19 werkdagen, etc.\n"
            "- Bemannings controle: volledig/dubbel/onvolledig per dag\n"
            "Dit kan enkele seconden duren voor grote teams"
        )
        buttons.append(valideer_btn)

        return buttons

    def get_initial_filter_state(self, user_id: int) -> bool:
        """
        Planner-specifieke filter: alle gebruikers initieel zichtbaar
        Planner moet overzicht hebben van het hele team
        """
        return True

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

        # PERFORMANCE (v0.6.25): Filter gebruikers als filtered_gebruiker_ids opgegeven
        if self.filtered_gebruiker_ids:
            self.gebruikers_data = [
                user for user in self.gebruikers_data
                if user['id'] in self.filtered_gebruiker_ids
            ]

        # Laad feestdagen voor huidig jaar EN aangrenzende jaren (voor buffer dagen)
        self.load_feestdagen_extended()

        # Laad rode lijnen (28-daagse HR-cycli)
        self.load_rode_lijnen()

        # Laad relevante rode lijn periodes voor HR columns
        self.get_relevante_rode_lijn_periodes()

        # Reset HR cache (data is ververst)
        self.hr_werkdagen_cache.clear()

        # Datum range: maand + 8 dagen buffer
        datum_lijst = self.get_datum_lijst(start_offset=8, eind_offset=8)
        if datum_lijst:
            start_datum = datum_lijst[0][0]
            eind_datum = datum_lijst[-1][0]

            # Laad planning en verlof
            self.load_planning_data(start_datum, eind_datum)
            self.load_verlof_data(start_datum, eind_datum)

        # PERFORMANCE FIX (v0.6.25): Preload ValidationCache VOOR bemannings status
        # Dit voorkomt N+1 query probleem (900+ queries → 5 queries)
        # v0.6.26.2: Conditioneel obv config.ENABLE_VALIDATION_CACHE flag
        from config import ENABLE_VALIDATION_CACHE
        if ENABLE_VALIDATION_CACHE:
            from services.validation_cache import ValidationCache
            cache = ValidationCache.get_instance()

            # Haal gebruiker IDs op voor preload
            gebruiker_ids = [user['id'] for user in self.gebruikers_data] if self.gebruikers_data else None

            # Preload cache voor deze maand (batch loading)
            cache.preload_month(self.jaar, self.maand, gebruiker_ids)

        # Clear bemannings controle status (v0.6.26: REAL-TIME DISABLED)
        # Bemannings status wordt alleen geladen bij "Valideer Planning" knop
        self.bemannings_status.clear()

        # Clear HR violations (v0.6.26 - Fase 3: REAL-TIME DISABLED)
        # Violations worden alleen geladen bij "Valideer Planning" knop
        self.hr_violations.clear()

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

    def get_relevante_rode_lijn_periodes(self) -> None:
        """
        Haal relevante rode lijn periodes op voor huidige maand
        - Zoek EERST rode lijn die START binnen deze maand (meest zichtbaar)
        - Als die er niet is, gebruik de rode lijn waar de maand in valt
        - Vorige periode: periode_nummer - 1
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Eerste dag van maand
        maand_start = f"{self.jaar}-{self.maand:02d}-01"

        # STAP 1: Zoek rode lijn die START binnen deze maand
        cursor.execute("""
            SELECT periode_nummer, start_datum, eind_datum
            FROM rode_lijnen
            WHERE start_datum LIKE ?
            ORDER BY start_datum ASC
            LIMIT 1
        """, (f"{self.jaar}-{self.maand:02d}-%",))

        huidige = cursor.fetchone()

        # STAP 2: Als geen rode lijn start in deze maand, gebruik de periode waar maand in valt
        if not huidige:
            cursor.execute("""
                SELECT periode_nummer, start_datum, eind_datum
                FROM rode_lijnen
                WHERE start_datum <= ? AND eind_datum >= ?
                ORDER BY start_datum DESC
                LIMIT 1
            """, (maand_start, maand_start))

            huidige = cursor.fetchone()

        if not huidige:
            # Geen rode lijn gevonden - skip HR columns
            self.rode_lijn_periodes = None
            conn.close()
            return

        huidige_periode_nr = huidige['periode_nummer']
        huidige_start = huidige['start_datum']
        huidige_eind = huidige['eind_datum']

        # Haal vorige periode op (periode_nummer - 1)
        vorig_periode_nr = huidige_periode_nr - 1
        cursor.execute("""
            SELECT periode_nummer, start_datum, eind_datum
            FROM rode_lijnen
            WHERE periode_nummer = ?
        """, (vorig_periode_nr,))

        vorige = cursor.fetchone()

        if not vorige:
            # Geen vorige periode - skip HR columns
            self.rode_lijn_periodes = None
            conn.close()
            return

        vorige_start = vorige['start_datum']
        vorige_eind = vorige['eind_datum']

        # Sla op
        self.rode_lijn_periodes = {
            'vorig': {
                'nummer': str(vorig_periode_nr),
                'start': vorige_start,
                'eind': vorige_eind
            },
            'huidig': {
                'nummer': str(huidige_periode_nr),
                'start': huidige_start,
                'eind': huidige_eind
            }
        }

        conn.close()

    def tel_gewerkte_dagen(self, gebruiker_id: int, start_datum: str, eind_datum: str) -> int:
        """
        Tel aantal gewerkte dagen in periode voor gebruiker
        Alleen tellen als telt_als_werkdag = 1 (uit werkposten of speciale_codes)
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Query beide concept EN gepubliceerde planning (status niet filteren)
        # Empty cells (shift_code IS NULL or '') tellen NIET mee
        cursor.execute("""
            SELECT COUNT(*) as werkdagen
            FROM planning p
            LEFT JOIN shift_codes sc ON p.shift_code = sc.code
            LEFT JOIN werkposten w ON sc.werkpost_id = w.id
            LEFT JOIN speciale_codes spc ON p.shift_code = spc.code
            WHERE p.gebruiker_id = ?
              AND p.datum BETWEEN ? AND ?
              AND p.shift_code IS NOT NULL
              AND p.shift_code != ''
              AND (
                  (sc.code IS NOT NULL AND w.telt_als_werkdag = 1)
                  OR
                  (spc.code IS NOT NULL AND spc.telt_als_werkdag = 1)
              )
        """, (gebruiker_id, start_datum, eind_datum))

        row = cursor.fetchone()
        conn.close()

        return row['werkdagen'] if row else 0

    def load_bemannings_status(self) -> None:
        """
        Laad bemannings controle status voor alle datums in datum lijst

        PERFORMANCE OPTIMALISATIE (v0.6.25):
        Gebruikt ValidationCache ipv database queries (15-30x sneller)
        Cache moet vooraf geladen zijn via preload_month()
        """
        from services.validation_cache import ValidationCache

        self.bemannings_status.clear()
        cache = ValidationCache.get_instance()

        # Haal datum lijst op (met buffer)
        datum_lijst = self.get_datum_lijst(start_offset=8, eind_offset=8)

        for datum_str, _ in datum_lijst:
            # Converteer naar date object
            datum_obj = datetime.strptime(datum_str, '%Y-%m-%d').date()

            # Haal status uit cache (instant, geen database query!)
            status = cache.get_bemannings_status(datum_obj)

            if status:
                # Cache hit - gebruik cached data
                self.bemannings_status[datum_str] = {
                    'status': status,
                    'details': f"Status: {status}",
                    'verwachte_codes': [],
                    'werkelijke_codes': [],
                    'ontbrekende_codes': [],
                    'dubbele_codes': []
                }
            else:
                # Cache miss - fallback naar oude methode
                # (Dit zou niet moeten gebeuren als preload_month() correct werd aangeroepen)
                resultaat = controleer_bemanning(datum_obj)
                self.bemannings_status[datum_str] = resultaat

    def get_bemannings_overlay_kleur(self, datum_str: str) -> Optional[str]:
        """
        Bepaal overlay kleur voor bemannings status
        Returns: qlineargradient CSS syntax of None
        """
        if datum_str not in self.bemannings_status:
            return None

        status = self.bemannings_status[datum_str]['status']

        if status == 'groen':
            # Lichtgroen overlay (40% opacity - verhoogd voor betere zichtbaarheid)
            return "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(129, 199, 132, 0.4), stop:1 rgba(129, 199, 132, 0.4))"
        elif status == 'geel':
            # Oranje overlay voor dubbele shifts (55% opacity - Material Orange 600 voor meer intensiteit)
            # Onderscheidbaar van gele zon-/feestdag achtergrond
            return "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(251, 140, 0, 0.55), stop:1 rgba(251, 140, 0, 0.55))"
        elif status == 'rood':
            # Lichtrood overlay (40% opacity)
            return "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(229, 115, 115, 0.4), stop:1 rgba(229, 115, 115, 0.4))"
        else:
            return None

    def get_bemannings_tooltip(self, datum_str: str) -> str:
        """
        Genereer tooltip text voor bemannings status
        Returns: HTML formatted tooltip string
        """
        if datum_str not in self.bemannings_status:
            return ""

        resultaat = self.bemannings_status[datum_str]
        status = resultaat['status']
        datum_obj = datetime.strptime(datum_str, '%Y-%m-%d')
        datum_label = datum_obj.strftime('%d %B')

        # Status emoji
        if status == 'groen':
            status_text = f"{datum_label} - Volledig bemand"
            icon = "✓"
        elif status == 'geel':
            status_text = f"{datum_label} - Dubbele code(s)"
            icon = "⚠"
        else:  # rood
            status_text = f"{datum_label} - ONVOLLEDIG"
            icon = "✗"

        tooltip_parts = [status_text]

        # Toon verwachte codes met status
        verwachte = resultaat.get('verwachte_codes', [])
        werkelijke = resultaat.get('werkelijke_codes', [])
        ontbrekende = resultaat.get('ontbrekende_codes', [])
        dubbele = resultaat.get('dubbele_codes', [])

        # Groepeer werkelijke codes
        werkelijk_dict = {}
        for item in werkelijke:
            code = item['code']
            naam = item['gebruiker_naam']
            if code not in werkelijk_dict:
                werkelijk_dict[code] = []
            werkelijk_dict[code].append(naam)

        # Toon elke verwachte code
        if verwachte:
            tooltip_parts.append("")  # Lege regel
            for verwacht_item in verwachte:
                code = verwacht_item['code']
                werkpost = verwacht_item['werkpost_naam']
                shift_type = verwacht_item['shift_type']

                if code in werkelijk_dict:
                    # Code is ingevuld
                    namen = werkelijk_dict[code]
                    if len(namen) == 1:
                        tooltip_parts.append(f"✓ {werkpost} {shift_type} ({code}): {namen[0]}")
                    else:
                        # Dubbel
                        tooltip_parts.append(f"⚠ {werkpost} {shift_type} ({code}): {', '.join(namen)}")
                else:
                    # Code ontbreekt
                    tooltip_parts.append(f"✗ {werkpost} {shift_type} ({code}): NIET INGEVULD")

        return "\n".join(tooltip_parts)

    def load_hr_violations(self) -> None:
        """
        Laad HR violations voor alle gebruikers in huidige maand

        BATCH VALIDATIE (v0.6.26):
        - Loop door alle gefilterde gebruikers
        - Create PlanningValidator per gebruiker
        - Call validate_all() voor batch check
        - Map violations naar self.hr_violations dict

        Performance: Max 30 gebruikers, ~1-2 sec per gebruiker
        """
        self.hr_violations.clear()

        if not self.gebruikers_data:
            return

        # Loop door alle zichtbare gebruikers
        for user in self.gebruikers_data:
            gebruiker_id = user['id']

            try:
                # Create validator voor deze gebruiker + maand
                validator = PlanningValidator(
                    gebruiker_id=gebruiker_id,
                    jaar=self.jaar,
                    maand=self.maand
                )

                # Run batch validatie (alle 6 HR checks)
                violations_dict = validator.validate_all()

                # Flatten violations en map naar datum
                for regel_naam, violations_list in violations_dict.items():
                    for violation in violations_list:
                        # Violation kan exacte datum of datum_range hebben
                        if violation.datum:
                            # Filter: alleen violations in huidige maand (ISSUE-009 fix)
                            if violation.datum.year != self.jaar or violation.datum.month != self.maand:
                                continue  # Skip violations buiten huidige maand

                            datum_str = violation.datum.strftime('%Y-%m-%d')

                            # Initialiseer datum entry als nodig
                            if datum_str not in self.hr_violations:
                                self.hr_violations[datum_str] = {}

                            # Initialiseer gebruiker entry als nodig
                            if gebruiker_id not in self.hr_violations[datum_str]:
                                self.hr_violations[datum_str][gebruiker_id] = []

                            # Add violation
                            self.hr_violations[datum_str][gebruiker_id].append(violation)

                        # Als violation een datum_range heeft, map naar alle dagen in range
                        if violation.datum_range:
                            start_datum, eind_datum = violation.datum_range
                            huidige_datum = start_datum

                            while huidige_datum <= eind_datum:
                                # Filter: alleen datums in huidige maand (ISSUE-009 fix)
                                if huidige_datum.year != self.jaar or huidige_datum.month != self.maand:
                                    huidige_datum += timedelta(days=1)
                                    continue  # Skip datums buiten huidige maand

                                datum_str = huidige_datum.strftime('%Y-%m-%d')

                                # Initialiseer entries
                                if datum_str not in self.hr_violations:
                                    self.hr_violations[datum_str] = {}

                                if gebruiker_id not in self.hr_violations[datum_str]:
                                    self.hr_violations[datum_str][gebruiker_id] = []

                                # Add violation (alleen als niet al toegevoegd)
                                if violation not in self.hr_violations[datum_str][gebruiker_id]:
                                    self.hr_violations[datum_str][gebruiker_id].append(violation)

                                huidige_datum += timedelta(days=1)

            except Exception:
                # Silently skip errors, continue with other users
                pass

        # Update summary box na laden
        self.update_hr_summary()

    def on_valideer_planning_clicked(self) -> None:
        """
        Handler voor "Valideer Planning" knop (v0.6.26 - UX verbetering)

        Probleem: Real-time validatie tijdens plannen was te irritant.
        Oplossing: Batch validatie on-demand (alleen op knopklik).

        Process:
        1. Show progress cursor (kan 1-2 sec duren)
        2. Run load_hr_violations() (batch check HR regels voor alle gebruikers)
        3. Run load_bemannings_status() (batch check bemannings controle alle dagen)
        4. Rebuild grid om violations en bemannings status te tonen
        5. Show samenvatting dialog met alle violations
        """
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QApplication

        # Show busy cursor
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        try:
            # Run batch validatie - HR violations
            self.load_hr_violations()

            # Run batch validatie - Bemannings controle
            self.load_bemannings_status()

            # Rebuild grid om violations en bemannings status te tonen
            self.build_grid()

            # Tel violations
            totaal_violations = 0
            violations_per_type = {}

            for datum_violations in self.hr_violations.values():
                for gebruiker_violations in datum_violations.values():
                    for v in gebruiker_violations:
                        totaal_violations += 1
                        type_str = v.type.value
                        violations_per_type[type_str] = violations_per_type.get(type_str, 0) + 1

            # Show samenvatting
            if totaal_violations == 0:
                QMessageBox.information(
                    self,
                    "Validatie Compleet",
                    f"Geen HR violations gevonden voor {self.get_maand_naam()} {self.jaar}!\n\n"
                    "Alle gebruikers voldoen aan de HR regels."
                )
            else:
                # Build detailed message
                details = []
                for type_str, count in sorted(violations_per_type.items()):
                    # Friendly names
                    type_names = {
                        'min_rust_12u': '12u rust tussen shifts',
                        'max_uren_week': 'Max 50u per week',
                        'max_werkdagen_cyclus': 'Max 19 werkdagen per cyclus',
                        'max_dagen_tussen_rx': 'Max 7 dagen tussen rustdagen',
                        'max_werkdagen_reeks': 'Max 7 opeenvolgende werkdagen',
                        'max_weekends_achter_elkaar': 'Max 6 weekends achter elkaar',
                        'werkpost_onbekend': 'Onbekende werkpost koppeling'
                    }
                    naam = type_names.get(type_str, type_str)
                    details.append(f"• {naam}: {count}x")

                details_str = "\n".join(details)

                QMessageBox.warning(
                    self,
                    "HR Violations Gevonden",
                    f"Gevonden: {totaal_violations} violation(s) voor {self.get_maand_naam()} {self.jaar}\n\n"
                    f"{details_str}\n\n"
                    f"Violations zijn nu zichtbaar in de grid met rode overlays.\n"
                    f"Hover over cellen voor details."
                )

        finally:
            # Restore cursor
            QApplication.restoreOverrideCursor()

    def get_maand_naam(self) -> str:
        """Helper: Get maand naam in Nederlands"""
        maanden = ['Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni',
                   'Juli', 'Augustus', 'September', 'Oktober', 'November', 'December']
        return maanden[self.maand - 1]

    def update_hr_summary(self) -> None:
        """
        Update HR violations summary box onderaan grid (v0.6.26 - Fase 3 UX)

        Toont overzicht van alle violations voor zichtbare gebruikers:
        - Gegroepeerd per gebruiker
        - Error count + warning count
        - GEDEPLICEERDE violations (1x per periode, niet 1x per datum)
        - Datum range formatting voor periode-violations

        v0.6.26.2: Deduplicatie op basis van object ID voor periode-violations
        """
        # Verzamel alle violations voor zichtbare gebruikers
        # Structure: {gebruiker_id: {datum_str: [violations]}}
        violations_per_gebruiker: Dict[int, Dict[str, List[Violation]]] = {}

        for datum_str, gebruikers_dict in self.hr_violations.items():
            for gebruiker_id, violations_list in gebruikers_dict.items():
                if gebruiker_id not in violations_per_gebruiker:
                    violations_per_gebruiker[gebruiker_id] = {}

                if datum_str not in violations_per_gebruiker[gebruiker_id]:
                    violations_per_gebruiker[gebruiker_id][datum_str] = []

                violations_per_gebruiker[gebruiker_id][datum_str].extend(violations_list)

        # Check of er violations zijn (ISSUE-006: altijd tonen, niet verbergen)
        if not violations_per_gebruiker:
            self.hr_summary_label.setText(
                "<b>💡 Klik op 'Valideer Planning' om alle controles uit te voeren</b><br>"
                "<i>Validatie controleert:<br>"
                "• HR Regels: 12u rust, max 50u/week, max 19 werkdagen/cyclus, "
                "max 7 dagen tussen rustdagen, max 7 opeenvolgende werkdagen, max 6 weekends achter elkaar<br>"
                "• Bemannings Controle: volledig/dubbel/onvolledig bemand per dag (kritische shifts)</i>"
            )
            return

        # DEDUPLICATIE: Tel unieke violations (niet per datum)
        # Violations met datum_range worden meerdere keren opgeslagen (1x per datum in range)
        # → Tel op basis van object ID voor accurate counts
        total_errors = 0
        total_warnings = 0
        seen_violation_ids: set = set()

        for datums_dict in violations_per_gebruiker.values():
            for violations_list in datums_dict.values():
                for v in violations_list:
                    violation_id = id(v)
                    if violation_id not in seen_violation_ids:
                        seen_violation_ids.add(violation_id)
                        if v.severity.value == 'error':
                            total_errors += 1
                        else:
                            total_warnings += 1

        # Format HTML summary
        html_parts = [
            "<b>HR Regel Overtredingen Gevonden:</b><br>",
            f"<span style='color: #dc3545;'>✗ {total_errors} errors</span> | ",
            f"<span style='color: #ffc107;'>⚠ {total_warnings} warnings</span><br><br>"
        ]

        # Group violations per gebruiker (ALLE gebruikers, geen limit)
        for gebruiker_id, datums_dict in sorted(violations_per_gebruiker.items()):
            # Haal gebruiker naam op
            gebruiker_naam = "Onbekend"
            for user in self.gebruikers_data:
                if user['id'] == gebruiker_id:
                    gebruiker_naam = user['volledige_naam']
                    break

            # DEDUPLICATIE: Collect unieke violations voor deze gebruiker
            unieke_violations = []
            seen_ids: set = set()

            for violations_list in datums_dict.values():
                for v in violations_list:
                    violation_id = id(v)
                    if violation_id not in seen_ids:
                        seen_ids.add(violation_id)
                        unieke_violations.append(v)

            # Count per severity (nu correct - unieke violations)
            errors = [v for v in unieke_violations if v.severity.value == 'error']
            warnings = [v for v in unieke_violations if v.severity.value == 'warning']

            # Toon naam met totaal counts
            html_parts.append(f"<b>{gebruiker_naam}</b>: ")

            if errors:
                html_parts.append(f"<span style='color: #dc3545;'>{len(errors)} errors</span>")
            if warnings:
                if errors:
                    html_parts.append(", ")
                html_parts.append(f"<span style='color: #ffc107;'>{len(warnings)} warnings</span>")

            html_parts.append("<br>")

            # Toon unieke violations met correcte datum formatting
            for v in unieke_violations:
                icon = "✗" if v.severity.value == 'error' else "⚠"
                color = "#dc3545" if v.severity.value == 'error' else "#ffc107"

                # Beschrijving (volledige tekst)
                desc = v.beschrijving

                # DATUM FORMATTING: periode vs point-in-time
                if v.datum_range:
                    # Periode violation (bijv. werkdagen reeks, week, cyclus)
                    start_datum, eind_datum = v.datum_range
                    start_formatted = start_datum.strftime('%d %B')  # "1 januari"
                    eind_formatted = eind_datum.strftime('%d %B')    # "10 januari"
                    datum_text = f"{start_formatted} - {eind_formatted}"
                elif v.datum:
                    # Point-in-time violation (bijv. 12u rust)
                    datum_formatted = v.datum.strftime('%d %B')
                    datum_text = f"op {datum_formatted}"
                else:
                    # Geen datum info (rare case)
                    datum_text = ""

                html_parts.append(
                    f"&nbsp;&nbsp;<span style='color: {color};'>{icon}</span> {desc} "
                    f"<i>({datum_text})</i><br>"
                )

            html_parts.append("<br>")

        html_parts.append("<i>Controleer de planning voordat je publiceert (cellen met rode/gele overlay)</i>")

        # Update label (ISSUE-006: altijd zichtbaar, geen show() nodig)
        self.hr_summary_label.setText("".join(html_parts))

    def get_hr_overlay_kleur(self, datum_str: str, gebruiker_id: int) -> Optional[str]:
        """
        Bepaal HR violation overlay kleur voor cel

        Returns:
            qlineargradient CSS syntax voor overlay (40% opacity)
            - Rood voor errors
            - Geel voor warnings
            - None voor geen violations
        """
        # Check of er violations zijn voor deze datum + gebruiker
        if datum_str not in self.hr_violations:
            return None

        if gebruiker_id not in self.hr_violations[datum_str]:
            return None

        violations = self.hr_violations[datum_str][gebruiker_id]
        if not violations:
            return None

        # Check severity: errors = rood, warnings = geel
        heeft_error = any(v.severity.value == 'error' for v in violations)

        if heeft_error:
            # Rood overlay (70% opacity voor betere zichtbaarheid)
            # #E57373 = Material Red 300
            return "rgba(229, 115, 115, 0.7)"
        else:
            # Geel overlay (70% opacity voor betere zichtbaarheid)
            # #FFD54F = Material Amber 300
            return "rgba(255, 213, 79, 0.7)"

    def get_hr_tooltip(self, datum_str: str, gebruiker_id: int) -> str:
        """
        Genereer tooltip tekst met HR violation details

        Returns:
            Plain text string met violations lijst (geen HTML)
            - ⚠ voor warnings
            - ✗ voor errors
        """
        # Check of er violations zijn
        if datum_str not in self.hr_violations:
            return ""

        if gebruiker_id not in self.hr_violations[datum_str]:
            return ""

        violations = self.hr_violations[datum_str][gebruiker_id]
        if not violations:
            return ""

        # Format datum
        datum_obj = datetime.strptime(datum_str, '%Y-%m-%d')
        datum_label = datum_obj.strftime('%d %B')

        tooltip_parts = [f"HR Regel Overtredingen ({datum_label}):"]

        # Group violations by type
        for violation in violations:
            # Icon based on severity
            if violation.severity.value == 'error':
                icon = "✗"
            else:
                icon = "⚠"

            # Add violation description
            tooltip_parts.append(f"{icon} {violation.beschrijving}")

        return "\n".join(tooltip_parts)

    def build_grid(self) -> None:
        """Bouw de grid met namen en datums - SPLIT in frozen + scrollable (v0.6.25)"""
        # Clear bestaande layouts
        if self.frozen_container.layout():
            QWidget().setLayout(self.frozen_container.layout())
        if self.scrollable_container.layout():
            QWidget().setLayout(self.scrollable_container.layout())

        # Reset cel widgets
        self.cel_widgets.clear()
        self.hr_cel_widgets.clear()
        self.datum_header_widgets.clear()

        # Maak twee aparte layouts
        frozen_layout = QGridLayout()
        frozen_layout.setSpacing(0)
        frozen_layout.setContentsMargins(0, 0, 0, 0)

        scrollable_layout = QGridLayout()
        scrollable_layout.setSpacing(0)
        scrollable_layout.setContentsMargins(0, 0, 0, 0)

        # Haal datum lijst en zichtbare gebruikers
        datum_lijst = self.get_datum_lijst(start_offset=8, eind_offset=8)
        zichtbare_gebruikers = self.get_zichtbare_gebruikers()

        if not zichtbare_gebruikers:
            # Geen gebruikers geselecteerd
            info = QLabel("Geen teamleden geselecteerd. Gebruik de filter knop.")
            info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: 20px;")
            frozen_layout.addWidget(info, 0, 0)
            self.frozen_container.setLayout(frozen_layout)
            self.scrollable_container.setLayout(scrollable_layout)
            return

        # ============== FROZEN HEADERS (naam + HR kolommen) ==============
        # Dynamische frozen width: 280px (naam) of 380px (naam + HR)
        frozen_width = 280
        if self.rode_lijn_periodes:
            frozen_width = 380  # 280 + 50 + 50
        self.frozen_scroll.setFixedWidth(frozen_width)

        # Naam header → frozen kolom 0
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
        naam_header.setFixedWidth(280)
        frozen_layout.addWidget(naam_header, 0, 0)

        # HR kolom headers (alleen als rode lijn periodes beschikbaar zijn)
        frozen_col_offset = 1  # Start positie voor HR kolommen in frozen layout
        if self.rode_lijn_periodes:
            # Voor RL header → frozen kolom 1
            hr_voor_header = QLabel("Voor\nRL")
            hr_voor_header.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY, QFont.Weight.Bold))
            hr_voor_header.setStyleSheet(f"""
                QLabel {{
                    background-color: {Colors.PRIMARY};
                    color: white;
                    padding: 4px;
                    border: 1px solid {Colors.BORDER_LIGHT};
                    qproperty-alignment: AlignCenter;
                }}
            """)
            hr_voor_header.setFixedWidth(50)
            vorig_periode = self.rode_lijn_periodes['vorig']
            hr_voor_header.setToolTip(
                f"Gewerkte dagen vóór rode lijn\n"
                f"Periode {vorig_periode['nummer']}: {vorig_periode['start']} t/m {vorig_periode['eind']}"
            )
            frozen_layout.addWidget(hr_voor_header, 0, 1)

            # Na RL header → frozen kolom 2
            hr_na_header = QLabel("Na\nRL")
            hr_na_header.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY, QFont.Weight.Bold))
            hr_na_header.setStyleSheet(f"""
                QLabel {{
                    background-color: {Colors.PRIMARY};
                    color: white;
                    padding: 4px;
                    border: 1px solid {Colors.BORDER_LIGHT};
                    border-left: 3px solid #dc3545;
                    qproperty-alignment: AlignCenter;
                }}
            """)
            hr_na_header.setFixedWidth(50)
            huidig_periode = self.rode_lijn_periodes['huidig']
            hr_na_header.setToolTip(
                f"Gewerkte dagen ná rode lijn\n"
                f"Periode {huidig_periode['nummer']}: {huidig_periode['start']} t/m {huidig_periode['eind']}"
            )
            frozen_layout.addWidget(hr_na_header, 0, 2)

        # ============== SCROLLABLE HEADERS (datum kolommen) ==============
        # Datum headers starten bij scrollable kolom 0
        for col, (datum_str, label) in enumerate(datum_lijst):
            datum_header = QLabel(label)
            datum_header.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY, QFont.Weight.Bold))

            # Achtergrond kleur voor header (weekend/feestdag basis)
            achtergrond = self.get_datum_achtergrond(datum_str)

            # Bemannings overlay (v0.6.20 - qlineargradient zoals cell selection)
            bemannings_overlay = self.get_bemannings_overlay_kleur(datum_str)

            # Check of dit het begin van een rode lijn periode is
            is_rode_lijn_start = datum_str in self.rode_lijnen_starts

            # Blauwe kader ROND de hele huidige maand (v0.6.25)
            datum_obj = datetime.strptime(datum_str, '%Y-%m-%d')
            is_huidige_maand = datum_obj.month == self.maand
            is_eerste_dag_maand = is_huidige_maand and datum_obj.day == 1
            is_laatste_dag_maand = is_huidige_maand and datum_obj.day == self.get_laatste_dag_van_maand()

            # Base border
            border_style = f"1px solid {Colors.BORDER_LIGHT}"

            # Blauwe kader rondom hele maand
            extra_borders = []
            if is_huidige_maand:
                extra_borders.append("border-top: 3px solid #2196F3")  # Boven border voor alle maand dagen
            if is_eerste_dag_maand:
                extra_borders.append("border-left: 3px solid #2196F3")  # Linker border voor eerste dag
            if is_laatste_dag_maand:
                extra_borders.append("border-right: 3px solid #2196F3")  # Rechter border voor laatste dag

            # Tooltip met bemanningsstatus (v0.6.20)
            bemannings_tooltip = self.get_bemannings_tooltip(datum_str)
            base_tooltip = ""
            if is_rode_lijn_start:
                periode_nr = self.rode_lijnen_starts[datum_str]
                base_tooltip = f"Start Rode Lijn Periode {periode_nr}"

            # Combineer tooltips
            if bemannings_tooltip and base_tooltip:
                full_tooltip = f"{bemannings_tooltip}\n\n{base_tooltip}"
            elif bemannings_tooltip:
                full_tooltip = bemannings_tooltip
            else:
                full_tooltip = base_tooltip

            # Build style met borders
            border_parts = [f"border: {border_style}"]

            # Rode lijn: dikke rode linker border (kan combineren met blauwe maand border)
            if is_rode_lijn_start:
                border_parts.append("border-left: 4px solid #dc3545")

            # Blauwe maand borders (kunnen rode lijn overschrijven als beide aanwezig)
            border_parts.extend(extra_borders)

            base_style = f"""
                QLabel {{
                    background-color: {achtergrond};
                    color: #000000;
                    padding: 4px;
                    {'; '.join(border_parts)};
                    qproperty-alignment: AlignCenter;
                }}
            """

            # Bemannings overlay toepassen (replace background-color met background + qlineargradient)
            if bemannings_overlay:
                base_style = base_style.replace(
                    f"background-color: {achtergrond}",
                    f"background: {bemannings_overlay}"
                )

            datum_header.setStyleSheet(base_style)

            if full_tooltip:
                datum_header.setToolTip(full_tooltip)

            datum_header.setFixedWidth(60)
            scrollable_layout.addWidget(datum_header, 0, col)  # Scrollable headers

            # Sla datum header op voor later updaten (v0.6.20)
            self.datum_header_widgets[datum_str] = datum_header

        # ============== DATA RIJEN (split in frozen + scrollable) ==============
        for row, gebruiker in enumerate(zichtbare_gebruikers, start=1):
            gebruiker_id = gebruiker['id']
            is_laatste_rij = (row == len(zichtbare_gebruikers))

            # ---- FROZEN: Naam kolom → frozen kolom 0 ----
            naam_label = QLabel(gebruiker['volledige_naam'])
            naam_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
            naam_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {Colors.BG_LIGHT};
                    padding: 8px;
                    border: 1px solid {Colors.BORDER_LIGHT};
                }}
            """)
            naam_label.setFixedWidth(280)
            frozen_layout.addWidget(naam_label, row, 0)

            # ---- FROZEN: HR kolom cellen → frozen kolom 1, 2 ----
            if self.rode_lijn_periodes:
                # Bereken werkdagen (gebruik cache)
                if gebruiker_id not in self.hr_werkdagen_cache:
                    vorig_periode = self.rode_lijn_periodes['vorig']
                    huidig_periode = self.rode_lijn_periodes['huidig']

                    voor_dagen = self.tel_gewerkte_dagen(
                        gebruiker_id,
                        vorig_periode['start'],
                        vorig_periode['eind']
                    )
                    na_dagen = self.tel_gewerkte_dagen(
                        gebruiker_id,
                        huidig_periode['start'],
                        huidig_periode['eind']
                    )

                    self.hr_werkdagen_cache[gebruiker_id] = {
                        'voor': voor_dagen,
                        'na': na_dagen
                    }

                voor_dagen = self.hr_werkdagen_cache[gebruiker_id]['voor']
                na_dagen = self.hr_werkdagen_cache[gebruiker_id]['na']
                totaal_dagen = voor_dagen + na_dagen

                # Check ELKE periode apart (niet het totaal!)
                is_voor_overschrijding = voor_dagen > 19
                is_na_overschrijding = na_dagen > 19

                # Kolom 1: "Voor RL" aantal (rood als deze periode > 19)
                voor_achtergrond = "rgba(255, 0, 0, 0.3)" if is_voor_overschrijding else Colors.BG_LIGHT
                hr_voor_cel = QLabel(str(voor_dagen))
                hr_voor_cel.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL, QFont.Weight.Bold))
                hr_voor_cel.setStyleSheet(f"""
                    QLabel {{
                        background-color: {voor_achtergrond};
                        padding: 8px;
                        border: 1px solid {Colors.BORDER_LIGHT};
                        qproperty-alignment: AlignCenter;
                    }}
                """)
                hr_voor_cel.setFixedWidth(50)
                vorig_periode = self.rode_lijn_periodes['vorig']
                hr_voor_cel.setToolTip(
                    f"Gewerkte dagen: {voor_dagen}/19\n"
                    f"Periode {vorig_periode['nummer']}: {vorig_periode['start']} t/m {vorig_periode['eind']}"
                )
                frozen_layout.addWidget(hr_voor_cel, row, 1)  # Frozen kolom 1

                # Kolom 2: "Na RL" aantal met rode linker border (rood als deze periode > 19)
                na_achtergrond = "rgba(255, 0, 0, 0.3)" if is_na_overschrijding else Colors.BG_LIGHT
                hr_na_cel = QLabel(str(na_dagen))
                hr_na_cel.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL, QFont.Weight.Bold))
                hr_na_cel.setStyleSheet(f"""
                    QLabel {{
                        background-color: {na_achtergrond};
                        padding: 8px;
                        border: 1px solid {Colors.BORDER_LIGHT};
                        border-left: 3px solid #dc3545;
                        qproperty-alignment: AlignCenter;
                    }}
                """)
                hr_na_cel.setFixedWidth(50)
                huidig_periode = self.rode_lijn_periodes['huidig']
                hr_na_cel.setToolTip(
                    f"Gewerkte dagen: {na_dagen}/19\n"
                    f"Periode {huidig_periode['nummer']}: {huidig_periode['start']} t/m {huidig_periode['eind']}"
                )
                frozen_layout.addWidget(hr_na_cel, row, 2)  # Frozen kolom 2

                # Sla HR cellen op voor latere updates
                self.hr_cel_widgets[gebruiker_id] = {
                    'voor': hr_voor_cel,
                    'na': hr_na_cel
                }

            # ---- SCROLLABLE: Datum cellen → scrollable kolom 0+ ----
            for col, (datum_str, _) in enumerate(datum_lijst):  # Start bij kolom 0 in scrollable
                cel = self.create_editable_cel(datum_str, gebruiker_id, is_laatste_rij)
                cel.setFixedWidth(60)
                scrollable_layout.addWidget(cel, row, col)  # Scrollable layout

                # Track widget
                if datum_str not in self.cel_widgets:
                    self.cel_widgets[datum_str] = {}
                self.cel_widgets[datum_str][gebruiker_id] = cel

        # Set layouts op containers
        self.frozen_container.setMaximumHeight(frozen_layout.rowCount() * Dimensions.TABLE_ROW_HEIGHT)
        self.frozen_container.setLayout(frozen_layout)

        self.scrollable_container.setMaximumHeight(scrollable_layout.rowCount() * Dimensions.TABLE_ROW_HEIGHT)
        self.scrollable_container.setLayout(scrollable_layout)

    def create_editable_cel(self, datum_str: str, gebruiker_id: int, is_laatste_rij: bool = False) -> EditableLabel:
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

        # Bepaal achtergrond (weekend kleurtjes blijven behouden)
        achtergrond = self.get_datum_achtergrond(datum_str)

        # Bepaal overlay (verlof + HR violations, bemannings overlay alleen op datum headers)
        verlof_overlay = self.get_verlof_overlay(datum_str, gebruiker_id, 'planner')
        hr_overlay = self.get_hr_overlay_kleur(datum_str, gebruiker_id)

        # Prioriteit: verlof overlay eerst, dan HR overlay
        overlay = verlof_overlay if verlof_overlay else hr_overlay

        # Check of dit een buffer dag is
        datum_obj = datetime.strptime(datum_str, '%Y-%m-%d')
        is_buffer = datum_obj.month != self.maand

        # Check of dit het begin van een rode lijn periode is
        is_rode_lijn_start = datum_str in self.rode_lijnen_starts

        # Blauwe kader ROND de hele huidige maand (v0.6.25) - onderste border voor data cellen
        is_huidige_maand = datum_obj.month == self.maand
        is_eerste_dag_maand = is_huidige_maand and datum_obj.day == 1
        is_laatste_dag_maand = is_huidige_maand and datum_obj.day == self.get_laatste_dag_van_maand()

        # Maak editable label (met display_text ipv shift_code)
        cel = EditableLabel(display_text, datum_str, gebruiker_id, self)
        cel.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL, QFont.Weight.Bold))

        # Sla overlay kleur op voor editor styling (v0.6.28 - ISSUE-005 fix)
        if overlay:
            cel.overlay_kleur = overlay

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
                "border-top: 3px solid #00E676;\n                    border-right: 3px solid #00E676;\n                    qproperty-alignment: AlignCenter;"
            )

        # Blauwe maand kader - onder border voor ALLEEN de laatste rij (v0.6.25)
        if is_huidige_maand and is_laatste_rij:
            base_style = base_style.replace(
                "qproperty-alignment: AlignCenter;",
                "border-bottom: 3px solid #2196F3;\n                    qproperty-alignment: AlignCenter;"
            )

        # Blauwe maand kader - linker border voor eerste dag
        if is_eerste_dag_maand:
            base_style = base_style.replace(
                "qproperty-alignment: AlignCenter;",
                "border-left: 3px solid #2196F3;\n                    qproperty-alignment: AlignCenter;"
            )

        # Blauwe maand kader - rechter border voor laatste dag
        if is_laatste_dag_maand:
            base_style = base_style.replace(
                "qproperty-alignment: AlignCenter;",
                "border-right: 3px solid #2196F3;\n                    qproperty-alignment: AlignCenter;"
            )

        if is_buffer:
            cel.setStyleSheet(base_style + " QLabel { opacity: 0.7; }")
        else:
            cel.setStyleSheet(base_style)

        # Tooltip (combineer alle tooltip components)
        tooltip = self.get_cel_tooltip(datum_str, gebruiker_id, 'planner')

        # Add HR violations tooltip (v0.6.26)
        hr_tooltip = self.get_hr_tooltip(datum_str, gebruiker_id)
        if hr_tooltip:
            tooltip = f"{tooltip}\n\n{hr_tooltip}" if tooltip else hr_tooltip

        # Add rode lijn tooltip
        if is_rode_lijn_start:
            periode_nr = self.rode_lijnen_starts[datum_str]
            rode_lijn_tooltip = f"Start Rode Lijn Periode {periode_nr}"
            tooltip = f"{tooltip}\n{rode_lijn_tooltip}" if tooltip else rode_lijn_tooltip

        # Add notitie tooltip
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
        # Check of maand in concept is (niet gepubliceerd)
        if not self.check_maand_is_concept():
            QMessageBox.warning(
                self,
                "Gepubliceerde Maand",
                "Deze maand is gepubliceerd en kan niet worden bewerkt.\n\n"
                "Zet de maand eerst terug naar concept via de Planning Editor."
            )
            # Reset cel naar oude waarde met stylesheet rebuild (v0.6.25)
            if datum_str in self.cel_widgets and gebruiker_id in self.cel_widgets[datum_str]:
                zichtbare_gebruikers = self.get_zichtbare_gebruikers()
                is_laatste_rij = False
                if zichtbare_gebruikers:
                    laatste_gebruiker_id = zichtbare_gebruikers[-1]['id']
                    is_laatste_rij = (gebruiker_id == laatste_gebruiker_id)
                self.rebuild_cel_style(datum_str, gebruiker_id, is_laatste_rij)
            return

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
            # Reset cel met stylesheet rebuild (v0.6.25)
            if datum_str in self.cel_widgets and gebruiker_id in self.cel_widgets[datum_str]:
                zichtbare_gebruikers = self.get_zichtbare_gebruikers()
                is_laatste_rij = False
                if zichtbare_gebruikers:
                    laatste_gebruiker_id = zichtbare_gebruikers[-1]['id']
                    is_laatste_rij = (gebruiker_id == laatste_gebruiker_id)
                self.rebuild_cel_style(datum_str, gebruiker_id, is_laatste_rij)
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

            # Reset cel met stylesheet rebuild (v0.6.25)
            if datum_str in self.cel_widgets and gebruiker_id in self.cel_widgets[datum_str]:
                zichtbare_gebruikers = self.get_zichtbare_gebruikers()
                is_laatste_rij = False
                if zichtbare_gebruikers:
                    laatste_gebruiker_id = zichtbare_gebruikers[-1]['id']
                    is_laatste_rij = (gebruiker_id == laatste_gebruiker_id)
                self.rebuild_cel_style(datum_str, gebruiker_id, is_laatste_rij)
            return

        # Check voor dubbele shift_code (v0.6.20 - waarschuwing, maar kan doorgaan)
        if code not in self.speciale_codes:
            # Check of deze code al gebruikt wordt door andere gebruiker op deze datum
            dubbel_gebruiker = self.check_dubbele_shift_code(datum_str, code, gebruiker_id)
            if dubbel_gebruiker:
                # Toon waarschuwing dialog met keuze
                antwoord = QMessageBox.question(
                    self,
                    "Dubbele Shift Code",
                    f"Code '{code}' wordt al gebruikt door {dubbel_gebruiker} op deze datum.\n\n"
                    f"Dit kan correct zijn bij opleidingen of dubbele bemanning.\n\n"
                    f"Weet je zeker dat je dit wilt?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if antwoord == QMessageBox.StandardButton.No:
                    # Annuleren - reset cel met stylesheet rebuild (v0.6.25)
                    if datum_str in self.cel_widgets and gebruiker_id in self.cel_widgets[datum_str]:
                        zichtbare_gebruikers = self.get_zichtbare_gebruikers()
                        is_laatste_rij = False
                        if zichtbare_gebruikers:
                            laatste_gebruiker_id = zichtbare_gebruikers[-1]['id']
                            is_laatste_rij = (gebruiker_id == laatste_gebruiker_id)
                        self.rebuild_cel_style(datum_str, gebruiker_id, is_laatste_rij)
                    return
                # Anders: gebruiker heeft "Yes" gekozen, ga door met opslaan

        # Alles OK - save
        self.save_shift(datum_str, gebruiker_id, code)

    def check_dubbele_shift_code(self, datum_str: str, code: str, huidige_gebruiker_id: int) -> Optional[str]:
        """
        Check of een shift_code al gebruikt wordt door een andere gebruiker op deze datum.

        Args:
            datum_str: Datum string (YYYY-MM-DD)
            code: Shift code om te checken
            huidige_gebruiker_id: ID van gebruiker die de code wil gebruiken (excludeer deze)

        Returns:
            Naam van gebruiker die code al gebruikt, of None als code niet dubbel is
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT g.volledige_naam
            FROM planning p
            JOIN gebruikers g ON p.gebruiker_id = g.id
            WHERE p.datum = ?
            AND p.shift_code = ?
            AND p.gebruiker_id != ?
            LIMIT 1
        """, (datum_str, code, huidige_gebruiker_id))

        row = cursor.fetchone()
        conn.close()

        return row['volledige_naam'] if row else None

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

    def update_hr_cijfers_voor_gebruiker(self, gebruiker_id: int) -> None:
        """Update HR cijfers voor specifieke gebruiker zonder volledige rebuild"""
        # Check of HR kolommen beschikbaar zijn
        if not self.rode_lijn_periodes:
            return

        # Check of deze gebruiker HR cellen heeft
        if gebruiker_id not in self.hr_cel_widgets:
            return

        # Bereken nieuwe werkdagen
        vorig_periode = self.rode_lijn_periodes['vorig']
        huidig_periode = self.rode_lijn_periodes['huidig']

        voor_dagen = self.tel_gewerkte_dagen(
            gebruiker_id,
            vorig_periode['start'],
            vorig_periode['eind']
        )
        na_dagen = self.tel_gewerkte_dagen(
            gebruiker_id,
            huidig_periode['start'],
            huidig_periode['eind']
        )

        # Update cache
        self.hr_werkdagen_cache[gebruiker_id] = {
            'voor': voor_dagen,
            'na': na_dagen
        }

        # Check overschrijdingen per cel
        is_voor_overschrijding = voor_dagen > 19
        is_na_overschrijding = na_dagen > 19

        # Update "Voor RL" cel
        voor_cel = self.hr_cel_widgets[gebruiker_id]['voor']
        voor_cel.setText(str(voor_dagen))
        voor_achtergrond = "rgba(255, 0, 0, 0.3)" if is_voor_overschrijding else Colors.BG_LIGHT
        voor_cel.setStyleSheet(f"""
            QLabel {{
                background-color: {voor_achtergrond};
                padding: 8px;
                border: 1px solid {Colors.BORDER_LIGHT};
                qproperty-alignment: AlignCenter;
            }}
        """)
        voor_cel.setToolTip(
            f"Gewerkte dagen: {voor_dagen}/19\n"
            f"Periode {vorig_periode['nummer']}: {vorig_periode['start']} t/m {vorig_periode['eind']}"
        )

        # Update "Na RL" cel
        na_cel = self.hr_cel_widgets[gebruiker_id]['na']
        na_cel.setText(str(na_dagen))
        na_achtergrond = "rgba(255, 0, 0, 0.3)" if is_na_overschrijding else Colors.BG_LIGHT
        na_cel.setStyleSheet(f"""
            QLabel {{
                background-color: {na_achtergrond};
                padding: 8px;
                border: 1px solid {Colors.BORDER_LIGHT};
                border-left: 3px solid #dc3545;
                qproperty-alignment: AlignCenter;
            }}
        """)
        na_cel.setToolTip(
            f"Gewerkte dagen: {na_dagen}/19\n"
            f"Periode {huidig_periode['nummer']}: {huidig_periode['start']} t/m {huidig_periode['eind']}"
        )

    def update_bemannings_status_voor_datum(self, datum_str: str) -> None:
        """
        Update bemannings controle status voor specifieke datum zonder volledige rebuild.
        Herberekent alleen de status voor deze datum en update de overlay kleuren.

        PERFORMANCE OPTIMALISATIE (v0.6.25):
        Invalideerd cache na wijziging en haalt nieuwe status op

        v0.6.26.2: Conditioneel obv config.ENABLE_VALIDATION_CACHE flag
        """
        from config import ENABLE_VALIDATION_CACHE

        # Converteer naar date object
        datum_obj = datetime.strptime(datum_str, '%Y-%m-%d').date()

        # PERFORMANCE FIX: Gebruik cache indien ingeschakeld
        if ENABLE_VALIDATION_CACHE:
            from services.validation_cache import ValidationCache

            cache = ValidationCache.get_instance()
            cache.invalidate_date(datum_obj)

            # Re-preload cache voor deze maand (snel - gebruikt batch queries)
            gebruiker_ids = [user['id'] for user in self.gebruikers_data] if self.gebruikers_data else None
            cache.preload_month(self.jaar, self.maand, gebruiker_ids)

            # Haal nieuwe status uit cache
            status = cache.get_bemannings_status(datum_obj)
        else:
            # Fallback: Direct query (v0.6.26.2)
            from services.bemannings_controle_service import controleer_bemanning
            status_dict = controleer_bemanning(datum_obj)
            status = status_dict.get('status', 'groen')

        if status:
            # Update status dictionary (minimale data voor UI)
            self.bemannings_status[datum_str] = {
                'status': status,
                'details': f"Status: {status}",
                'verwachte_codes': [],
                'werkelijke_codes': [],
                'ontbrekende_codes': [],
                'dubbele_codes': []
            }
        else:
            # Fallback naar oude methode
            resultaat = controleer_bemanning(datum_obj)
            self.bemannings_status[datum_str] = resultaat

        # Update alle cellen voor deze datum (alleen tooltips, geen overlay wijziging)
        if datum_str in self.cel_widgets:
            # Haal basis achtergrond op (weekend kleurtjes blijven behouden)
            nieuwe_achtergrond = self.get_datum_achtergrond(datum_str)

            for gebruiker_id, cel in self.cel_widgets[datum_str].items():
                # Bepaal overlay (verlof + HR, bemannings overlay alleen op datum headers)
                verlof_overlay = self.get_verlof_overlay(datum_str, gebruiker_id, 'planner')
                hr_overlay = self.get_hr_overlay_kleur(datum_str, gebruiker_id)

                # Prioriteit: verlof overlay eerst, dan HR overlay (v0.6.28 - ISSUE-005 fix)
                overlay = verlof_overlay if verlof_overlay else hr_overlay

                # Bepaal of het een buffer dag is
                datum_obj_check = datetime.strptime(datum_str, '%Y-%m-%d')
                is_buffer = datum_obj_check.month != self.maand

                # Check rode lijn
                is_rode_lijn_start = datum_str in self.rode_lijnen_starts

                # Check notitie
                heeft_notitie = False
                if datum_str in self.planning_data and gebruiker_id in self.planning_data[datum_str]:
                    notitie = self.planning_data[datum_str][gebruiker_id].get('notitie', '')
                    heeft_notitie = bool(notitie and notitie.strip())

                # Maak stylesheet (geen bemannings overlay op cellen)
                base_style = self.create_cel_stylesheet(nieuwe_achtergrond, overlay)

                # Rode lijn indicator
                if is_rode_lijn_start:
                    base_style = base_style.replace(
                        "border: 1px solid",
                        "border: 1px solid"
                    ).replace(
                        "qproperty-alignment: AlignCenter;",
                        "border-left: 4px solid #dc3545;\n                    qproperty-alignment: AlignCenter;"
                    )

                # Notitie indicator
                if heeft_notitie:
                    base_style = base_style.replace(
                        "border: 1px solid",
                        "border: 1px solid"
                    ).replace(
                        "qproperty-alignment: AlignCenter;",
                        "border-top: 3px solid #00E676;\n                    border-right: 3px solid #00E676;\n                    qproperty-alignment: AlignCenter;"
                    )

                if is_buffer:
                    cel.setStyleSheet(base_style + " QLabel { opacity: 0.7; }")
                else:
                    cel.setStyleSheet(base_style)

                # Update overlay kleur voor editor styling (v0.6.28 - ISSUE-005 fix)
                cel.overlay_kleur = overlay if overlay else None

        # Update ook de datum header (v0.6.20 - real-time overlay update)
        if datum_str in self.datum_header_widgets:
            header = self.datum_header_widgets[datum_str]

            # Haal basis achtergrond op
            achtergrond = self.get_datum_achtergrond(datum_str)

            # Haal bemannings overlay op (v0.6.20)
            bemannings_overlay = self.get_bemannings_overlay_kleur(datum_str)

            # Check rode lijn
            is_rode_lijn_start = datum_str in self.rode_lijnen_starts

            # Highlight huidige maand
            datum_obj_check = datetime.strptime(datum_str, '%Y-%m-%d')
            if datum_obj_check.month == self.maand:
                border_style = f"2px solid {Colors.PRIMARY}"
            else:
                border_style = f"1px solid {Colors.BORDER_LIGHT}"

            # Update tooltip
            bemannings_tooltip = self.get_bemannings_tooltip(datum_str)
            base_tooltip = ""
            if is_rode_lijn_start:
                periode_nr = self.rode_lijnen_starts[datum_str]
                base_tooltip = f"Start Rode Lijn Periode {periode_nr}"

            if bemannings_tooltip and base_tooltip:
                full_tooltip = f"{bemannings_tooltip}\n\n{base_tooltip}"
            elif bemannings_tooltip:
                full_tooltip = bemannings_tooltip
            else:
                full_tooltip = base_tooltip

            # Build base stylesheet
            if is_rode_lijn_start:
                base_style = f"""
                    QLabel {{
                        background-color: {achtergrond};
                        color: #000000;
                        padding: 4px;
                        border: {border_style};
                        border-left: 4px solid #dc3545;
                        qproperty-alignment: AlignCenter;
                    }}
                """
            else:
                base_style = f"""
                    QLabel {{
                        background-color: {achtergrond};
                        color: #000000;
                        padding: 4px;
                        border: {border_style};
                        qproperty-alignment: AlignCenter;
                    }}
                """

            # Bemannings overlay toepassen (replace background-color met background + qlineargradient)
            if bemannings_overlay:
                base_style = base_style.replace(
                    f"background-color: {achtergrond}",
                    f"background: {bemannings_overlay}"
                )

            header.setStyleSheet(base_style)

            if full_tooltip:
                header.setToolTip(full_tooltip)

    def rebuild_cel_style(self, datum_str: str, gebruiker_id: int, is_laatste_rij: bool = False) -> None:
        """
        Rebuild cel stylesheet na wijziging (v0.6.25)
        Herstelt alle custom borders: blauwe maand kader, rode lijn, notitie indicator
        """
        if datum_str not in self.cel_widgets or gebruiker_id not in self.cel_widgets[datum_str]:
            return

        cel = self.cel_widgets[datum_str][gebruiker_id]

        # Haal shift code en notitie op
        shift_code = self.get_display_code(datum_str, gebruiker_id)

        heeft_notitie = False
        if datum_str in self.planning_data and gebruiker_id in self.planning_data[datum_str]:
            notitie = self.planning_data[datum_str][gebruiker_id].get('notitie', '')
            heeft_notitie = bool(notitie and notitie.strip())

        # Bepaal achtergrond en overlay
        achtergrond = self.get_datum_achtergrond(datum_str)
        verlof_overlay = self.get_verlof_overlay(datum_str, gebruiker_id, 'planner')
        hr_overlay = self.get_hr_overlay_kleur(datum_str, gebruiker_id)

        # Prioriteit: verlof overlay eerst, dan HR overlay (v0.6.28 - ISSUE-005 fix)
        overlay = verlof_overlay if verlof_overlay else hr_overlay

        # Check flags
        datum_obj = datetime.strptime(datum_str, '%Y-%m-%d')
        is_buffer = datum_obj.month != self.maand
        is_rode_lijn_start = datum_str in self.rode_lijnen_starts
        is_huidige_maand = datum_obj.month == self.maand
        is_eerste_dag_maand = is_huidige_maand and datum_obj.day == 1
        is_laatste_dag_maand = is_huidige_maand and datum_obj.day == self.get_laatste_dag_van_maand()

        # Rebuild stylesheet (same logic as create_editable_cel)
        base_style = self.create_cel_stylesheet(achtergrond, overlay)

        # Rode lijn indicator
        if is_rode_lijn_start:
            base_style = base_style.replace(
                "qproperty-alignment: AlignCenter;",
                "border-left: 4px solid #dc3545;\n                    qproperty-alignment: AlignCenter;"
            )

        # Notitie indicator
        if heeft_notitie:
            base_style = base_style.replace(
                "qproperty-alignment: AlignCenter;",
                "border-top: 3px solid #00E676;\n                    border-right: 3px solid #00E676;\n                    qproperty-alignment: AlignCenter;"
            )

        # Blauwe maand kader - onder border voor laatste rij
        if is_huidige_maand and is_laatste_rij:
            base_style = base_style.replace(
                "qproperty-alignment: AlignCenter;",
                "border-bottom: 3px solid #2196F3;\n                    qproperty-alignment: AlignCenter;"
            )

        # Blauwe maand kader - linker border voor eerste dag
        if is_eerste_dag_maand:
            base_style = base_style.replace(
                "qproperty-alignment: AlignCenter;",
                "border-left: 3px solid #2196F3;\n                    qproperty-alignment: AlignCenter;"
            )

        # Blauwe maand kader - rechter border voor laatste dag
        if is_laatste_dag_maand:
            base_style = base_style.replace(
                "qproperty-alignment: AlignCenter;",
                "border-right: 3px solid #2196F3;\n                    qproperty-alignment: AlignCenter;"
            )

        # Apply stylesheet
        if is_buffer:
            cel.setStyleSheet(base_style + " QLabel { opacity: 0.7; }")
        else:
            cel.setStyleSheet(base_style)

        # Update overlay kleur voor editor styling (v0.6.28 - ISSUE-005 fix)
        cel.overlay_kleur = overlay if overlay else None

        # Update text
        cel.setText(shift_code)

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

            # UPDATE PLANNING DATA CACHE (v0.6.26 - CRITICAL FIX)
            # Anders verschijnen nieuwe shifts niet in de grid tot herstart
            if datum_str not in self.planning_data:
                self.planning_data[datum_str] = {}

            # Behoud bestaande notitie als die er is
            bestaande_notitie = ""
            if gebruiker_id in self.planning_data.get(datum_str, {}):
                bestaande_notitie = self.planning_data[datum_str][gebruiker_id].get('notitie', '')

            self.planning_data[datum_str][gebruiker_id] = {
                'shift_code': shift_code,
                'notitie': bestaande_notitie,
                'status': 'concept'
            }

            # Update cel display met volledige stylesheet rebuild (v0.6.25 fix)
            if datum_str in self.cel_widgets and gebruiker_id in self.cel_widgets[datum_str]:
                # Bepaal of dit de laatste rij is voor blauwe border
                is_laatste_rij = False
                zichtbare_gebruikers = self.get_zichtbare_gebruikers()
                if zichtbare_gebruikers:
                    laatste_gebruiker_id = zichtbare_gebruikers[-1]['id']
                    is_laatste_rij = (gebruiker_id == laatste_gebruiker_id)

                self.rebuild_cel_style(datum_str, gebruiker_id, is_laatste_rij)

            # Clear HR cache voor deze gebruiker
            if gebruiker_id in self.hr_werkdagen_cache:
                del self.hr_werkdagen_cache[gebruiker_id]

            # Update alleen HR cijfers (geen volledige rebuild)
            self.update_hr_cijfers_voor_gebruiker(gebruiker_id)

            # DISABLED (v0.6.26 - USER FEEDBACK): Real-time bemannings controle uitgeschakeld
            # Update bemannings status voor deze datum (v0.6.20)
            # self.update_bemannings_status_voor_datum(datum_str)

            # DISABLED (v0.6.26 - USER FEEDBACK):
            # Real-time validation is te irritant (popup bij elke edit)
            # Ghost violations door verkeerde datum mapping
            # Gebruiker moet "Valideer Planning" knop gebruiken
            # Update HR violations voor deze gebruiker (v0.6.26 - Fase 3.4)
            # violations = self.update_hr_violations_voor_gebruiker(datum_str, gebruiker_id, shift_code)
            # Toon warning dialog als er violations zijn (non-blocking)
            # if violations:
            #     self.show_hr_violation_warning(violations)

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

            # UPDATE PLANNING DATA CACHE (v0.6.26 - CRITICAL FIX)
            # Anders blijven verwijderde shifts zichtbaar in de grid tot herstart
            if datum_str in self.planning_data:
                if gebruiker_id in self.planning_data[datum_str]:
                    del self.planning_data[datum_str][gebruiker_id]

                # Verwijder datum entry als geen gebruikers meer shifts hebben
                if not self.planning_data[datum_str]:
                    del self.planning_data[datum_str]

            # Update cel display met volledige stylesheet rebuild (v0.6.25 fix)
            if datum_str in self.cel_widgets and gebruiker_id in self.cel_widgets[datum_str]:
                # Bepaal of dit de laatste rij is voor blauwe border
                is_laatste_rij = False
                zichtbare_gebruikers = self.get_zichtbare_gebruikers()
                if zichtbare_gebruikers:
                    laatste_gebruiker_id = zichtbare_gebruikers[-1]['id']
                    is_laatste_rij = (gebruiker_id == laatste_gebruiker_id)

                self.rebuild_cel_style(datum_str, gebruiker_id, is_laatste_rij)

            # Clear HR cache voor deze gebruiker
            if gebruiker_id in self.hr_werkdagen_cache:
                del self.hr_werkdagen_cache[gebruiker_id]

            # Update alleen HR cijfers (geen volledige rebuild)
            self.update_hr_cijfers_voor_gebruiker(gebruiker_id)

            # DISABLED (v0.6.26 - USER FEEDBACK): Real-time bemannings controle uitgeschakeld
            # Update bemannings status voor deze datum (v0.6.20)
            # self.update_bemannings_status_voor_datum(datum_str)

            # DISABLED (v0.6.26 - USER FEEDBACK):
            # Real-time validation uitgeschakeld, gebruiker moet "Valideer Planning" knop gebruiken
            # Update HR violations voor deze gebruiker (v0.6.26 - BUG FIX)
            # CRITICAL: Clear violations na delete, anders blijft oude "te veel uren" warning zichtbaar
            # self.clear_hr_violations_voor_gebruiker(datum_str, gebruiker_id)

            # Emit signal
            self.data_changed.emit()  # type: ignore

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon shift niet verwijderen:\n{e}")

    def edit_notitie(self, datum_str: str, gebruiker_id: int):
        """Bewerk of verwijder notitie voor cel"""
        from PyQt6.QtWidgets import QTextEdit, QDialog, QVBoxLayout, QPushButton, QHBoxLayout
        from datetime import datetime

        # Check of maand in concept is (niet gepubliceerd)
        if not self.check_maand_is_concept():
            QMessageBox.warning(
                self,
                "Gepubliceerde Maand",
                "Deze maand is gepubliceerd en kan niet worden bewerkt.\n\n"
                "Zet de maand eerst terug naar concept via de Planning Editor."
            )
            return

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
        text_edit.setPlaceholderText("Bijv: Afspraak arbeidsgeneesheer 15u - late shift nodig\n(Wordt automatisch opgeslagen als '[Planner]: ...')")
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

            # Voeg [Planner] prefix toe als notitie niet al een prefix heeft
            if nieuwe_notitie and not nieuwe_notitie.startswith('['):
                nieuwe_notitie = f"[Planner]: {nieuwe_notitie}"

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

    def clear_hr_violations_voor_gebruiker(self, datum_str: str, gebruiker_id: int) -> None:
        """
        Clear HR violations cache voor gebruiker op datum (v0.6.26 - BUG FIX)

        Aangeroepen na delete_shift() om oude violations te verwijderen.
        Zonder deze clear blijft de oude "te veel uren" warning zichtbaar na shift verwijdering.

        Args:
            datum_str: Datum (YYYY-MM-DD)
            gebruiker_id: Gebruiker ID
        """
        if datum_str in self.hr_violations:
            if gebruiker_id in self.hr_violations[datum_str]:
                del self.hr_violations[datum_str][gebruiker_id]

            # Verwijder datum entry als geen gebruikers meer violations hebben
            if not self.hr_violations[datum_str]:
                del self.hr_violations[datum_str]

        # Update cel styling om overlay te verwijderen
        if datum_str in self.cel_widgets and gebruiker_id in self.cel_widgets[datum_str]:
            zichtbare_gebruikers = self.get_zichtbare_gebruikers()
            is_laatste_rij = False
            if zichtbare_gebruikers:
                laatste_gebruiker_id = zichtbare_gebruikers[-1]['id']
                is_laatste_rij = (gebruiker_id == laatste_gebruiker_id)

            self.rebuild_cel_style(datum_str, gebruiker_id, is_laatste_rij)

    def update_hr_violations_voor_gebruiker(self, datum_str: str, gebruiker_id: int, shift_code: str) -> List[Violation]:
        """
        Re-valideer HR violations voor gebruiker na shift wijziging (v0.6.26 - Fase 3.4)

        Args:
            datum_str: Datum die gewijzigd is
            gebruiker_id: Gebruiker ID
            shift_code: Nieuwe shift code

        Returns:
            List van nieuwe violations (voor warning dialog)
        """
        try:
            # Convert datum_str naar date object
            datum_obj = datetime.strptime(datum_str, '%Y-%m-%d').date()

            # Create validator voor deze gebruiker
            validator = PlanningValidator(
                gebruiker_id=gebruiker_id,
                jaar=self.jaar,
                maand=self.maand
            )

            # Run real-time validatie (alleen snelle checks: 12u rust + 50u week)
            violations = validator.validate_shift(datum_obj, shift_code)

            # Update cache voor deze datum + gebruiker
            if violations:
                # Initialiseer entries als nodig
                if datum_str not in self.hr_violations:
                    self.hr_violations[datum_str] = {}

                # Update violations voor deze gebruiker
                self.hr_violations[datum_str][gebruiker_id] = violations
            else:
                # Geen violations - clear cache voor deze gebruiker op deze datum
                if datum_str in self.hr_violations:
                    if gebruiker_id in self.hr_violations[datum_str]:
                        del self.hr_violations[datum_str][gebruiker_id]

                    # Verwijder datum entry als geen gebruikers meer violations hebben
                    if not self.hr_violations[datum_str]:
                        del self.hr_violations[datum_str]

            # Update cel styling om overlay te reflecteren
            if datum_str in self.cel_widgets and gebruiker_id in self.cel_widgets[datum_str]:
                zichtbare_gebruikers = self.get_zichtbare_gebruikers()
                is_laatste_rij = False
                if zichtbare_gebruikers:
                    laatste_gebruiker_id = zichtbare_gebruikers[-1]['id']
                    is_laatste_rij = (gebruiker_id == laatste_gebruiker_id)

                self.rebuild_cel_style(datum_str, gebruiker_id, is_laatste_rij)

            # Update summary box (real-time)
            self.update_hr_summary()

            return violations

        except Exception:
            return []

    def show_hr_violation_warning(self, violations: List[Violation]) -> None:
        """
        Toon non-blocking warning dialog met HR violations (v0.6.26 - Fase 3.5)

        Args:
            violations: List van Violation objects
        """
        if not violations:
            return

        # Format violations voor display
        violations_text = []
        for v in violations:
            # Icon based on severity
            icon = "✗" if v.severity.value == 'error' else "⚠"
            violations_text.append(f"{icon} {v.beschrijving}")

        message = (
            "De wijziging is opgeslagen, maar er zijn HR regel overtredingen:\n\n"
            + "\n".join(violations_text) +
            "\n\nControleer de planning voordat je publiceert."
        )

        QMessageBox.warning(
            self,
            "HR Regel Overtredingen",
            message
        )

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

    def toggle_cell_selection(self, datum_str: str, gebruiker_id: int, modifiers):
        """Toggle cel selectie met Ctrl/Shift support"""
        cel_key = (datum_str, gebruiker_id)

        # Zorg dat widget focus heeft voor ESC key events
        self.setFocus()

        if modifiers & Qt.KeyboardModifier.ShiftModifier and self.last_clicked:
            # SHIFT = range selectie
            self.select_range(self.last_clicked, cel_key)
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            # CTRL = toggle individuele cel
            if cel_key in self.selected_cells:
                self.selected_cells.remove(cel_key)
            else:
                self.selected_cells.add(cel_key)
            self.last_clicked = cel_key
        else:
            # Gewone klik zonder modifier - clear selectie
            self.clear_selection()

        self.update_selection_display()

    def select_range(self, start: tuple, end: tuple):
        """Selecteer range tussen twee cellen (Shift+Click)"""
        start_datum, start_user = start
        end_datum, end_user = end

        # Haal datum lijst en gebruikers op
        datum_lijst = self.get_datum_lijst(start_offset=8, eind_offset=8)
        gebruikers = self.get_zichtbare_gebruikers()

        # Vind indices
        datum_strs = [d for d, _ in datum_lijst]
        user_ids = [u['id'] for u in gebruikers]

        try:
            start_datum_idx = datum_strs.index(start_datum)
            end_datum_idx = datum_strs.index(end_datum)
            start_user_idx = user_ids.index(start_user)
            end_user_idx = user_ids.index(end_user)
        except ValueError:
            # Een van de cellen niet gevonden
            return

        # Zorg dat start < end
        if start_datum_idx > end_datum_idx:
            start_datum_idx, end_datum_idx = end_datum_idx, start_datum_idx
        if start_user_idx > end_user_idx:
            start_user_idx, end_user_idx = end_user_idx, start_user_idx

        # Selecteer alle cellen in rectangle
        for d_idx in range(start_datum_idx, end_datum_idx + 1):
            for u_idx in range(start_user_idx, end_user_idx + 1):
                cel_key = (datum_strs[d_idx], user_ids[u_idx])
                self.selected_cells.add(cel_key)

    def clear_selection(self):
        """Wis alle selectie"""
        self.selected_cells.clear()
        self.last_clicked = None
        self.update_selection_display()

    def update_selection_display(self):
        """Update visuele feedback van selectie"""
        # Update label (altijd zichtbaar, nooit hide)
        num_selected = len(self.selected_cells)
        if num_selected > 0:
            self.selection_label.setText(f"{num_selected} cellen geselecteerd (ESC om te wissen)")
        else:
            self.selection_label.setText(" ")  # Spatie als placeholder

        # Update cel styling
        for datum_str in self.cel_widgets:
            for gebruiker_id in self.cel_widgets[datum_str]:
                cel = self.cel_widgets[datum_str][gebruiker_id]
                cel_key = (datum_str, gebruiker_id)
                self.apply_selection_styling(cel, datum_str, gebruiker_id, cel_key in self.selected_cells)

    def apply_selection_styling(self, cel: EditableLabel, datum_str: str, gebruiker_id: int, is_selected: bool):
        """Pas selectie styling toe op cel"""
        # Haal basis styling op
        shift_code = self.get_display_code(datum_str, gebruiker_id)
        achtergrond = self.get_datum_achtergrond(datum_str)
        verlof_overlay = self.get_verlof_overlay(datum_str, gebruiker_id, 'planner')
        hr_overlay = self.get_hr_overlay_kleur(datum_str, gebruiker_id)

        # Prioriteit: verlof overlay eerst, dan HR overlay (v0.6.28 - ISSUE-005 fix)
        overlay = verlof_overlay if verlof_overlay else hr_overlay

        # Check buffer dag
        datum_obj = datetime.strptime(datum_str, '%Y-%m-%d')
        is_buffer = datum_obj.month != self.maand

        # Check rode lijn en notitie
        is_rode_lijn_start = datum_str in self.rode_lijnen_starts
        heeft_notitie = False
        if datum_str in self.planning_data and gebruiker_id in self.planning_data[datum_str]:
            notitie = self.planning_data[datum_str][gebruiker_id].get('notitie', '')
            heeft_notitie = bool(notitie and notitie.strip())

        # Bouw stylesheet
        base_style = self.create_cel_stylesheet(achtergrond, overlay)

        # Rode lijn indicator
        if is_rode_lijn_start:
            base_style = base_style.replace(
                "border: 1px solid",
                "border: 1px solid"
            ).replace(
                "qproperty-alignment: AlignCenter;",
                "border-left: 4px solid #dc3545;\n                    qproperty-alignment: AlignCenter;"
            )

        # Notitie indicator
        if heeft_notitie:
            base_style = base_style.replace(
                "border: 1px solid",
                "border: 1px solid"
            ).replace(
                "qproperty-alignment: AlignCenter;",
                "border-top: 3px solid #00E676;\n                    border-right: 3px solid #00E676;\n                    qproperty-alignment: AlignCenter;"
            )

        # SELECTIE OVERLAY (lichtblauw semi-transparant)
        if is_selected:
            # Extract de achtergrondkleur en mix met blauw
            base_style = base_style.replace(
                f"background-color: {achtergrond}",
                f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(33, 150, 243, 0.3), stop:1 rgba(33, 150, 243, 0.2))"
            )

        # Buffer opacity
        if is_buffer:
            cel.setStyleSheet(base_style + " QLabel { opacity: 0.7; }")
        else:
            cel.setStyleSheet(base_style)

        # Update overlay kleur voor editor styling (v0.6.28 - ISSUE-005 fix)
        cel.overlay_kleur = overlay if overlay else None

    def keyPressEvent(self, event):
        """Handle keyboard events (ESC voor selectie wissen)"""
        if event.key() == Qt.Key.Key_Escape:
            if self.selected_cells:
                self.clear_selection()
                event.accept()
                return
        super().keyPressEvent(event)

    def check_maand_is_concept(self) -> bool:
        """
        Check of huidige maand in concept status is.
        Returns True als concept (editable), False als gepubliceerd (read-only).
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Haal eerste dag van maand
            eerste_dag = f"{self.jaar}-{self.maand:02d}-01"

            # Check of er gepubliceerde records zijn voor deze maand
            cursor.execute("""
                SELECT COUNT(*) as aantal
                FROM planning
                WHERE datum LIKE ?
                  AND status = 'gepubliceerd'
            """, (f"{self.jaar}-{self.maand:02d}-%",))

            row = cursor.fetchone()
            conn.close()

            # Als er gepubliceerde records zijn, is maand gepubliceerd
            if row and row['aantal'] > 0:
                return False  # Gepubliceerd = niet editable

            return True  # Concept of leeg = editable

        except sqlite3.Error:
            # Bij fout: assume concept (veiliger)
            return True

    def show_context_menu(self, cel: EditableLabel, datum_str: str, gebruiker_id: int):
        """Toon context menu bij rechtsklik"""
        menu = QMenu(self)

        # Check of er selectie is
        has_selection = len(self.selected_cells) > 0

        # BULK OPERATIES (als er selectie is)
        if has_selection:
            menu.addAction("BULK OPERATIES").setEnabled(False)  # Header

            wis_selectie_action = menu.addAction(f"Wis Selectie ({len(self.selected_cells)} cellen)")
            wis_selectie_action.triggered.connect(self.bulk_delete_selected)  # type: ignore

            vul_selectie_action = menu.addAction(f"Vul Selectie In... ({len(self.selected_cells)} cellen)")
            vul_selectie_action.triggered.connect(self.bulk_fill_selected)  # type: ignore

            menu.addSeparator()

        # Notitie toevoegen/bewerken
        notitie_action = menu.addAction("Notitie toevoegen/bewerken")
        notitie_action.triggered.connect(lambda: self.edit_notitie(datum_str, gebruiker_id))  # type: ignore

        menu.addSeparator()

        # Verwijder enkele cel
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

    def bulk_delete_selected(self):
        """Verwijder alle geselecteerde cellen"""
        from PyQt6.QtWidgets import QCheckBox

        if not self.selected_cells:
            return

        # Check of maand in concept is (niet gepubliceerd)
        if not self.check_maand_is_concept():
            QMessageBox.warning(
                self,
                "Gepubliceerde Maand",
                "Deze maand is gepubliceerd en kan niet worden bewerkt.\n\n"
                "Zet de maand eerst terug naar concept via de Planning Editor."
            )
            return

        # Maak bevestiging dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Wis Selectie")
        dialog.setModal(True)
        dialog.resize(450, 200)

        layout = QVBoxLayout(dialog)

        # Info label
        info_label = QLabel(f"Weet je zeker dat je {len(self.selected_cells)} shifts wilt verwijderen?")
        info_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        layout.addWidget(info_label)

        # Checkbox: ook speciale codes verwijderen?
        checkbox = QCheckBox("Ook speciale codes verwijderen (VV, Z, RX, etc.)")
        checkbox.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        checkbox.setChecked(False)  # Standaard UIT (bescherm speciale codes)
        layout.addWidget(checkbox)

        # Warning
        warning = QLabel("Let op: Notities blijven altijd behouden.")
        warning.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY))
        warning.setStyleSheet(f"color: {Colors.WARNING}; font-style: italic;")
        layout.addWidget(warning)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        annuleer_btn = QPushButton("Annuleren")
        annuleer_btn.clicked.connect(dialog.reject)  # type: ignore
        button_layout.addWidget(annuleer_btn)

        wis_btn = QPushButton("Verwijderen")
        wis_btn.setStyleSheet(Styles.button_warning())
        wis_btn.clicked.connect(dialog.accept)  # type: ignore
        button_layout.addWidget(wis_btn)

        layout.addLayout(button_layout)

        # Toon dialog
        if dialog.exec():
            verwijder_speciale_codes = checkbox.isChecked()

            try:
                conn = get_connection()
                cursor = conn.cursor()
                verwijderd_count = 0

                for datum_str, gebruiker_id in self.selected_cells:
                    # Haal huidige shift code op
                    shift_code = self.get_display_code(datum_str, gebruiker_id)

                    # Skip als speciale code EN bescherming aan staat
                    if not verwijder_speciale_codes and shift_code in self.speciale_codes:
                        continue

                    # Verwijder shift (maar NIET notitie!)
                    cursor.execute("""
                        UPDATE planning
                        SET shift_code = NULL
                        WHERE gebruiker_id = ? AND datum = ?
                          AND status = 'concept'
                    """, (gebruiker_id, datum_str))

                    verwijderd_count += 1

                conn.commit()
                conn.close()

                # Refresh grid
                self.load_initial_data()

                # Clear selectie
                self.clear_selection()

                # Success feedback
                QMessageBox.information(
                    self,
                    "Shifts Verwijderd",
                    f"{verwijderd_count} shifts verwijderd.\nNotities zijn behouden."
                )

            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Fout", f"Kon shifts niet verwijderen:\n{e}")

    def bulk_fill_selected(self):
        """Vul alle geselecteerde cellen in met zelfde code"""
        from PyQt6.QtWidgets import QCheckBox

        if not self.selected_cells:
            return

        # Check of maand in concept is (niet gepubliceerd)
        if not self.check_maand_is_concept():
            QMessageBox.warning(
                self,
                "Gepubliceerde Maand",
                "Deze maand is gepubliceerd en kan niet worden bewerkt.\n\n"
                "Zet de maand eerst terug naar concept via de Planning Editor."
            )
            return

        # Maak dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Vul Selectie In")
        dialog.setModal(True)
        dialog.resize(500, 250)

        layout = QVBoxLayout(dialog)

        # Info label
        info_label = QLabel(f"Vul {len(self.selected_cells)} cellen in met shift code:")
        info_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        layout.addWidget(info_label)

        # Input field voor code
        code_label = QLabel("Shift code:")
        code_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        layout.addWidget(code_label)

        code_input = QLineEdit()
        code_input.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        code_input.setMaxLength(5)
        code_input.setPlaceholderText("Bijv: V, L, N, RX, VV, etc.")
        code_input.setStyleSheet(Styles.input_field())

        # Uppercase automatisch
        def to_upper():
            pos = code_input.cursorPosition()
            code_input.setText(code_input.text().upper())
            code_input.setCursorPosition(pos)

        code_input.textChanged.connect(to_upper)  # type: ignore
        layout.addWidget(code_input)

        # Checkbox: ook speciale codes overschrijven?
        checkbox = QCheckBox("Ook speciale codes overschrijven (VV, Z, RX, etc.)")
        checkbox.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        checkbox.setChecked(False)  # Standaard UIT (bescherm speciale codes)
        layout.addWidget(checkbox)

        # Warning
        warning = QLabel("Let op: Notities blijven altijd behouden.")
        warning.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY))
        warning.setStyleSheet(f"color: {Colors.WARNING}; font-style: italic;")
        layout.addWidget(warning)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        annuleer_btn = QPushButton("Annuleren")
        annuleer_btn.clicked.connect(dialog.reject)  # type: ignore
        button_layout.addWidget(annuleer_btn)

        vul_btn = QPushButton("Invullen")
        vul_btn.setStyleSheet(Styles.button_primary())
        vul_btn.clicked.connect(dialog.accept)  # type: ignore
        button_layout.addWidget(vul_btn)

        layout.addLayout(button_layout)

        # Focus op input
        code_input.setFocus()

        # Toon dialog
        if dialog.exec():
            nieuwe_code = code_input.text().strip().upper()

            if not nieuwe_code:
                QMessageBox.warning(self, "Geen Code", "Vul een shift code in.")
                return

            # Validatie: bestaat de code?
            if nieuwe_code not in self.valid_codes:
                QMessageBox.warning(
                    self,
                    "Ongeldige Code",
                    f"'{nieuwe_code}' is geen geldige shift code.\n\n"
                    f"Check de codes lijst in het scherm."
                )
                return

            overschrijf_speciale_codes = checkbox.isChecked()

            try:
                conn = get_connection()
                cursor = conn.cursor()
                ingevuld_count = 0

                for datum_str, gebruiker_id in self.selected_cells:
                    # Haal huidige shift code op
                    oude_code = self.get_display_code(datum_str, gebruiker_id)

                    # Skip als speciale code EN bescherming aan staat
                    if not overschrijf_speciale_codes and oude_code in self.speciale_codes:
                        continue

                    # Save shift (notitie blijft behouden)
                    cursor.execute("""
                        INSERT INTO planning (gebruiker_id, datum, shift_code, status)
                        VALUES (?, ?, ?, 'concept')
                        ON CONFLICT(gebruiker_id, datum)
                        DO UPDATE SET shift_code = ?
                        WHERE status = 'concept'
                    """, (gebruiker_id, datum_str, nieuwe_code, nieuwe_code))

                    ingevuld_count += 1

                conn.commit()
                conn.close()

                # Refresh grid
                self.load_initial_data()

                # Clear selectie
                self.clear_selection()

                # Success feedback
                QMessageBox.information(
                    self,
                    "Cellen Ingevuld",
                    f"{ingevuld_count} cellen ingevuld met '{nieuwe_code}'.\nNotities zijn behouden."
                )

            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Fout", f"Kon cellen niet invullen:\n{e}")

    def vul_week(self, start_datum: str, gebruiker_id: int, code: str):
        """Vul 7 dagen met zelfde code"""
        # Check of maand in concept is (niet gepubliceerd)
        if not self.check_maand_is_concept():
            QMessageBox.warning(
                self,
                "Gepubliceerde Maand",
                "Deze maand is gepubliceerd en kan niet worden bewerkt.\n\n"
                "Zet de maand eerst terug naar concept via de Planning Editor."
            )
            return

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
        """
        Open dialog om gebruikers te filteren

        BELANGRIJK: Laadt ALLE actieve gebruikers uit database, niet alleen
        de huidige gefilterde lijst. Dit maakt dynamische filter uitbreiding mogelijk.
        """
        from gui.widgets.teamlid_grid_kalender import FilterDialog

        # Laad ALLE actieve gebruikers uit database (niet alleen huidige gefilterde lijst)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, volledige_naam, gebruikersnaam, is_reserve, is_actief
            FROM gebruikers
            WHERE gebruikersnaam != 'admin' AND is_actief = 1
            ORDER BY is_reserve, achternaam, voornaam
        """)
        alle_gebruikers = cursor.fetchall()
        conn.close()

        # Open dialog met ALLE gebruikers
        dialog = FilterDialog(alle_gebruikers, self.filter_gebruikers, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.filter_gebruikers = dialog.get_filter()

            # KRITIEK: Update filtered_gebruiker_ids met nieuwe selectie
            # Zodat load_initial_data() de juiste gebruikers laadt
            geselecteerde_ids = [
                user_id for user_id, is_visible in self.filter_gebruikers.items()
                if is_visible
            ]

            if geselecteerde_ids:
                # Update naar nieuwe gefilterde lijst
                self.filtered_gebruiker_ids = geselecteerde_ids
            else:
                # Geen gebruikers geselecteerd - toon waarschuwing
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Geen gebruikers geselecteerd",
                    "Selecteer minstens één gebruiker om weer te geven."
                )
                return

            # BELANGRIJK: Herlaad data met nieuwe filter
            # Dit zorgt dat nieuwe gebruikers die nu zichtbaar zijn ook geladen worden
            # Plus: clear ValidationCache voor nieuwe gebruikers
            from config import ENABLE_VALIDATION_CACHE
            if ENABLE_VALIDATION_CACHE:
                from services.validation_cache import ValidationCache
                cache = ValidationCache.get_instance()
                cache.clear()  # Clear cache voor nieuwe gebruikers set

            self.load_initial_data()
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

    def refresh_data(self, jaar: int, maand: int) -> None:
        """Herlaad data voor nieuwe jaar/maand"""
        self.jaar = jaar
        self.maand = maand
        self.update_title()
        self.load_initial_data()
        # Emit signal zodat parent screen kan reageren (bijv. status reload)
        self.maand_changed.emit()  # type: ignore