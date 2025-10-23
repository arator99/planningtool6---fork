#gui/screens/mijn_planning_screen.py

"""
Mijn Planning Scherm
Teamleden bekijken hun eigen rooster en kunnen collega's filteren
"""
from typing import Callable, Set
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime
from gui.styles import Styles, Colors, Fonts, Dimensions
from gui.widgets import TeamlidGridKalender
from database.connection import get_connection


class MijnPlanningScreen(QWidget):
    """
    Mijn Planning scherm voor teamleden
    Toont TeamlidGridKalender met eigen rooster
    """

    def __init__(self, router: Callable, gebruiker_id: int):
        super().__init__()
        self.router = router
        self.gebruiker_id = gebruiker_id

        # State
        self.valid_codes: Set[str] = set()
        self.speciale_codes: Set[str] = set()

        # Instance attributes
        self.kalender: TeamlidGridKalender = TeamlidGridKalender(
            datetime.now().year,
            datetime.now().month,
            self.gebruiker_id
        )
        self.codes_help_table: QTableWidget = QTableWidget()

        self.init_ui()
        self.load_valid_codes()

    def init_ui(self) -> None:
        """Bouw UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(Dimensions.SPACING_LARGE)
        main_layout.setContentsMargins(
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE
        )

        # Linker deel: Header + Kalender
        left_layout = QVBoxLayout()
        left_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Header
        header = QHBoxLayout()

        title = QLabel("Mijn Planning")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE))
        header.addWidget(title)

        header.addStretch()

        # Terug knop
        terug_btn = QPushButton("Terug")
        terug_btn.setFixedSize(100, Dimensions.BUTTON_HEIGHT_NORMAL)
        terug_btn.clicked.connect(self.router.terug)  # type: ignore
        terug_btn.setStyleSheet(Styles.button_secondary())
        header.addWidget(terug_btn)

        left_layout.addLayout(header)

        # Info box
        info_box = QLabel(
            "Bekijk hier je eigen rooster. "
            "Gebruik de filter knop rechtsboven om collega's te bekijken."
        )
        info_box.setStyleSheet(Styles.info_box())
        info_box.setWordWrap(True)
        left_layout.addWidget(info_box)

        # Kalender widget
        left_layout.addWidget(self.kalender)

        main_layout.addLayout(left_layout, stretch=3)

        # Rechter deel: Codes legend
        right_widget = self.create_codes_sidebar()
        main_layout.addWidget(right_widget, stretch=1)

    def create_codes_sidebar(self) -> QWidget:
        """Maak sidebar met beschikbare codes"""
        from PyQt6.QtWidgets import QTextEdit, QScrollArea

        widget = QWidget()
        widget.setMaximumWidth(300)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Title
        title = QLabel("Beschikbare Codes")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(title)

        # Info
        info = QLabel("Overzicht shift codes")
        info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")
        layout.addWidget(info)

        # Scroll area

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # SHIFTS sectie
        shifts_label = QLabel("SHIFTS:")
        shifts_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        scroll_layout.addWidget(shifts_label)

        shifts_text = QTextEdit()
        shifts_text.setReadOnly(True)
        shifts_text.setMaximumHeight(350)
        shifts_text.setText(self.get_shift_codes_text())
        shifts_text.setStyleSheet(Styles.input_field())
        scroll_layout.addWidget(shifts_text)

        # SPECIAAL sectie
        special_label = QLabel("SPECIAAL:")
        special_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        scroll_layout.addWidget(special_label)

        special_text = QTextEdit()
        special_text.setReadOnly(True)
        special_text.setMaximumHeight(200)
        special_text.setText(self.get_special_codes_text())
        special_text.setStyleSheet(Styles.input_field())
        scroll_layout.addWidget(special_text)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        widget.setLayout(layout)
        return widget

    def load_valid_codes(self):
        """Laad alle geldige codes uit database"""
        conn = get_connection()
        cursor = conn.cursor()

        # Shift codes (alleen actieve werkposten)
        cursor.execute("""
            SELECT DISTINCT sc.code
            FROM shift_codes sc
            JOIN werkposten w ON sc.werkpost_id = w.id
            WHERE w.is_actief = 1
        """)

        for row in cursor.fetchall():
            self.valid_codes.add(row['code'])

        # Speciale codes
        cursor.execute("SELECT code FROM speciale_codes")

        for row in cursor.fetchall():
            code = row['code']
            self.valid_codes.add(code)
            self.speciale_codes.add(code)

        conn.close()

    def get_shift_codes_text(self) -> str:
        """Haal shift codes tekst voor sidebar"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT w.naam as werkpost, sc.code, sc.dag_type, sc.shift_type,
                   sc.start_uur, sc.eind_uur
            FROM shift_codes sc
            JOIN werkposten w ON sc.werkpost_id = w.id
            WHERE w.is_actief = 1
            ORDER BY w.naam, sc.code
        """)

        lines = []
        current_werkpost = None

        for row in cursor.fetchall():
            if row['werkpost'] != current_werkpost:
                if current_werkpost:
                    lines.append("")
                lines.append(f"=== {row['werkpost']} ===")
                current_werkpost = row['werkpost']

            # Format: CODE - Type (dag) tijd-tijd
            dag_short = {'weekdag': 'we', 'zaterdag': 'za', 'zondag': 'zo'}.get(row['dag_type'], row['dag_type'][:2])
            shift_short = row['shift_type'][:1].upper()

            lines.append(
                f"{row['code']} - {shift_short} ({dag_short}) "
                f"{row['start_uur']}-{row['eind_uur']}"
            )

        conn.close()
        return "\n".join(lines) if lines else "Geen shift codes beschikbaar"

    def get_special_codes_text(self) -> str:
        """Haal speciale codes tekst voor sidebar"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT code, naam FROM speciale_codes ORDER BY code")

        lines = [f"{row['code']} - {row['naam']}" for row in cursor.fetchall()]

        conn.close()
        return "\n".join(lines) if lines else "Geen speciale codes beschikbaar"