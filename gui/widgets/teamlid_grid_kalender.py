#gui/widgets/teamlid_grid_kalender.py
"""
Teamlid Grid Kalender
Read-only kalender voor teamleden om eigen/collega shifts te bekijken
"""
from typing import Dict, Any, List, Optional, Set
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QComboBox, QScrollArea, QWidget, QGridLayout,
                             QCheckBox, QDialog, QDialogButtonBox)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from gui.widgets.grid_kalender_base import GridKalenderBase
from gui.styles import Styles, Colors, Fonts, Dimensions
from datetime import datetime
from database.connection import get_connection


class TeamlidGridKalender(GridKalenderBase):
    """
    Grid kalender voor teamleden
    - Volledige maand weergave (geen buffer)
    - Filter op gebruikers
    - Read-only (alleen bekijken)
    - Verlof/DA/VD overlays
    """

    # Signal voor maand wijziging
    maand_changed: pyqtSignal = pyqtSignal()

    def __init__(self, jaar: int, maand: int, huidige_gebruiker_id: int):
        self.huidige_gebruiker_id = huidige_gebruiker_id
        super().__init__(jaar, maand)
        self.init_ui()
        self.load_initial_data()

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

        # FROZEN COLUMNS (v0.6.25) - Dual scroll area pattern
        # Splits grid in frozen deel (naam) en scrollable deel (datums)
        h_layout = QHBoxLayout()
        h_layout.setSpacing(0)
        h_layout.setContentsMargins(0, 0, 0, 0)

        # LINKER deel: Frozen kolom (naam)
        self.frozen_scroll = QScrollArea()
        self.frozen_scroll.setWidgetResizable(True)
        self.frozen_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.frozen_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Sync met rechts
        self.frozen_container = QWidget()
        self.frozen_scroll.setWidget(self.frozen_container)
        self.frozen_scroll.setFixedWidth(280)  # Alleen naam kolom

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

        layout.addStretch()

    def get_header_extra_buttons(self) -> List[QPushButton]:
        """Voeg vorige/volgende maand buttons toe (teamlid view)"""
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

        return buttons

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
            self.maand_combo.setCurrentIndex(self.maand - 1)  # BUG FIX: index is 0-based

    def get_initial_filter_state(self, user_id: int) -> bool:
        """
        Teamlid-specifieke filter: alleen eigen planning initieel zichtbaar
        Teamlid moet focussen op eigen rooster, niet afgeleid door collega's
        """
        return user_id == self.huidige_gebruiker_id

    def load_initial_data(self) -> None:
        """Laad initiële data"""
        # Laad gebruikers (filter wordt behouden bij refresh, geforceerd bij init)
        self.load_gebruikers(alleen_actief=True)

        # Laad feestdagen
        self.load_feestdagen()

        # Laad rode lijnen (28-daagse HR cycli)
        self.load_rode_lijnen()

        # Datum range: alleen deze maand
        datum_lijst = self.get_datum_lijst(start_offset=0, eind_offset=0)
        if datum_lijst:
            start_datum = datum_lijst[0][0]
            eind_datum = datum_lijst[-1][0]

            # Laad planning en verlof (alleen gepubliceerde planning voor teamleden)
            self.load_planning_data(start_datum, eind_datum, alleen_gepubliceerd=True)
            self.load_verlof_data(start_datum, eind_datum)

        # Bouw grid
        self.build_grid()

    def build_grid(self) -> None:
        """Bouw de grid met namen en datums - SPLIT in frozen + scrollable (v0.6.25)"""
        # Clear bestaande layouts
        if self.frozen_container.layout():
            QWidget().setLayout(self.frozen_container.layout())
        if self.scrollable_container.layout():
            QWidget().setLayout(self.scrollable_container.layout())

        # Maak twee aparte layouts
        frozen_layout = QGridLayout()
        frozen_layout.setSpacing(0)
        frozen_layout.setContentsMargins(0, 0, 0, 0)

        scrollable_layout = QGridLayout()
        scrollable_layout.setSpacing(0)
        scrollable_layout.setContentsMargins(0, 0, 0, 0)

        # Haal datum lijst en zichtbare gebruikers
        datum_lijst = self.get_datum_lijst(start_offset=0, eind_offset=0)
        zichtbare_gebruikers = self.get_zichtbare_gebruikers()

        if not zichtbare_gebruikers:
            # Geen gebruikers geselecteerd
            info = QLabel("Geen teamleden geselecteerd. Gebruik de filter knop.")
            info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: 20px;")
            frozen_layout.addWidget(info, 0, 0)
            self.frozen_container.setLayout(frozen_layout)
            self.scrollable_container.setLayout(scrollable_layout)
            return

        # ============== FROZEN HEADER (naam kolom) ==============
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

        # ============== SCROLLABLE HEADERS (datum kolommen) ==============
        # Datum headers starten bij scrollable kolom 0
        for col, (datum_str, label) in enumerate(datum_lijst):
            datum_header = QLabel(label)
            datum_header.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY, QFont.Weight.Bold))

            # Achtergrond kleur voor header (geel voor zondag/feestdag, grijs voor zaterdag)
            achtergrond = self.get_datum_achtergrond(datum_str)

            # Check of dit het begin van een rode lijn periode is
            is_rode_lijn_start = datum_str in self.rode_lijnen_starts

            if is_rode_lijn_start:
                periode_nr = self.rode_lijnen_starts[datum_str]
                datum_header.setStyleSheet(f"""
                    QLabel {{
                        background-color: {achtergrond};
                        color: #000000;
                        padding: 4px;
                        border: 1px solid {Colors.BORDER_LIGHT};
                        border-left: 4px solid #dc3545;
                        qproperty-alignment: AlignCenter;
                    }}
                """)
                datum_header.setToolTip(f"Start Rode Lijn Periode {periode_nr}")
            else:
                datum_header.setStyleSheet(f"""
                    QLabel {{
                        background-color: {achtergrond};
                        color: #000000;
                        padding: 4px;
                        border: 1px solid {Colors.BORDER_LIGHT};
                        qproperty-alignment: AlignCenter;
                    }}
                """)

            datum_header.setFixedWidth(60)
            scrollable_layout.addWidget(datum_header, 0, col)  # Scrollable headers

        # ============== DATA RIJEN (split in frozen + scrollable) ==============
        for row, gebruiker in enumerate(zichtbare_gebruikers, start=1):
            gebruiker_id = gebruiker['id']

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

            # ---- SCROLLABLE: Datum cellen → scrollable kolom 0+ ----
            for col, (datum_str, _) in enumerate(datum_lijst):  # Start bij kolom 0 in scrollable
                cel = self.create_shift_cel(datum_str, gebruiker_id, mode='teamlid')
                cel.setFixedWidth(60)
                scrollable_layout.addWidget(cel, row, col)  # Scrollable layout

        # Set layouts op containers
        self.frozen_container.setLayout(frozen_layout)
        self.scrollable_container.setLayout(scrollable_layout)

    def create_shift_cel(self, datum_str: str, gebruiker_id: int, mode: str) -> QLabel:
        """
        Maak cel voor shift weergave
        Read-only voor teamlid view

        ISSUE-004 FIX: Notitie indicator (groen hoekje) toegevoegd
        - Alleen voor ingelogde gebruiker's eigen notities
        """
        # Haal shift code op
        shift_code = self.get_display_code(datum_str, gebruiker_id)

        # Bepaal achtergrond en overlay
        achtergrond = self.get_datum_achtergrond(datum_str)
        overlay = self.get_verlof_overlay(datum_str, gebruiker_id, mode)

        # Check of dit het begin van een rode lijn periode is
        is_rode_lijn_start = datum_str in self.rode_lijnen_starts

        # ISSUE-004 FIX: Check of er een notitie is (alleen voor ingelogde gebruiker)
        heeft_notitie = False
        if gebruiker_id == self.huidige_gebruiker_id:  # Alleen eigen notities tonen
            if datum_str in self.planning_data and gebruiker_id in self.planning_data[datum_str]:
                notitie = self.planning_data[datum_str][gebruiker_id].get('notitie', '')
                heeft_notitie = bool(notitie and notitie.strip())

        # Maak label
        cel = QLabel(shift_code)
        cel.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL, QFont.Weight.Bold))

        # Stylesheet met optionele rode lijn
        base_style = self.create_cel_stylesheet(achtergrond, overlay)
        if is_rode_lijn_start:
            # Voeg rode linker border toe
            base_style = base_style.replace(
                "qproperty-alignment: AlignCenter;",
                "border-left: 4px solid #dc3545;\n                    qproperty-alignment: AlignCenter;"
            )

        # ISSUE-004 FIX: Notitie indicator (rechter boven corner accent)
        if heeft_notitie:
            base_style = base_style.replace(
                "border: 1px solid",
                "border: 1px solid"
            ).replace(
                "qproperty-alignment: AlignCenter;",
                "border-top: 3px solid #00E676;\n                    border-right: 3px solid #00E676;\n                    qproperty-alignment: AlignCenter;"
            )

        cel.setStyleSheet(base_style)

        # Tooltip
        tooltip = self.get_cel_tooltip(datum_str, gebruiker_id, mode)
        if is_rode_lijn_start:
            periode_nr = self.rode_lijnen_starts[datum_str]
            rode_lijn_tooltip = f"Start Rode Lijn Periode {periode_nr}"
            tooltip = f"{tooltip}\n{rode_lijn_tooltip}" if tooltip else rode_lijn_tooltip
        if tooltip:
            cel.setToolTip(tooltip)

        return cel

    def refresh_data(self, jaar: int, maand: int) -> None:
        """Herlaad data voor nieuwe jaar/maand"""
        self.jaar = jaar
        self.maand = maand
        self.update_title()
        self.load_initial_data()
        self.maand_changed.emit()  # Emit signal voor status update


class FilterDialog(QDialog):
    """
    Dialog om teamleden te selecteren voor weergave

    v0.6.28+ (ISSUE-011): Uitgebreid met werkpost filtering
    - Selecteer werkposten om te plannen
    - Filter gebruikers op werkpost kennis
    """

    def __init__(self, gebruikers_data: List[Dict[str, Any]],
                 huidige_filter: Dict[int, bool],
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.gebruikers_data = gebruikers_data
        self.huidige_filter = huidige_filter.copy()
        self.checkboxes: Dict[int, QCheckBox] = {}

        # NIEUW (ISSUE-011): Werkpost filtering
        self.werkpost_checkboxes: Dict[int, QCheckBox] = {}
        self.check_filter_op_werkpost: QCheckBox
        self.check_toon_reserves: QCheckBox  # NIEUW: reserves filter
        self.all_gebruiker_ids: Set[int] = {u['id'] for u in gebruikers_data}  # Alle beschikbare IDs
        # Reserve IDs (sqlite3.Row heeft geen .get(), gebruik try/except of check keys)
        self.reserve_gebruiker_ids: Set[int] = {
            u['id'] for u in gebruikers_data
            if 'is_reserve' in u.keys() and u['is_reserve']
        }
        # Onthoud originele checked state van reserves (voor restore bij toggle)
        self.reserves_checked_state: Dict[int, bool] = {}
        # Onthoud originele checked state van ALLE gebruikers (voor werkpost filter restore)
        self.all_users_checked_state: Dict[int, bool] = {}

        self.setWindowTitle("Filter Teamleden & Werkposten")
        self.setModal(True)
        self.resize(650, 700)  # Groter voor werkpost sectie
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()

        # NIEUW (ISSUE-011): Werkpost sectie bovenaan
        from PyQt6.QtWidgets import QGroupBox
        werkpost_group = QGroupBox("🏢 WERKPOST FILTER")
        werkpost_layout = QVBoxLayout()

        # Info
        info_werkpost = QLabel("Selecteer werkposten om te zien:")
        info_werkpost.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        werkpost_layout.addWidget(info_werkpost)

        # Scroll area voor werkposten
        werkpost_scroll = QScrollArea()
        werkpost_scroll.setWidgetResizable(True)
        werkpost_scroll.setMaximumHeight(120)
        werkpost_scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        werkpost_container = QWidget()
        werkpost_container_layout = QVBoxLayout(werkpost_container)
        werkpost_container_layout.setContentsMargins(5, 5, 5, 5)
        werkpost_container_layout.setSpacing(3)

        # Laad werkposten uit database
        from database.connection import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, naam
            FROM werkposten
            WHERE is_actief = 1
            ORDER BY naam
        """)
        werkposten = cursor.fetchall()
        conn.close()

        # Maak checkbox per werkpost
        for werkpost in werkposten:
            werkpost_id = werkpost['id']
            werkpost_naam = werkpost['naam']

            checkbox = QCheckBox(werkpost_naam)
            checkbox.setChecked(True)  # Default: alle werkposten geselecteerd
            checkbox.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
            checkbox.toggled.connect(self._on_werkpost_changed)  # type: ignore

            self.werkpost_checkboxes[werkpost_id] = checkbox
            werkpost_container_layout.addWidget(checkbox)

        werkpost_scroll.setWidget(werkpost_container)
        werkpost_layout.addWidget(werkpost_scroll)

        # Filter op werkpost kennis checkbox
        self.check_filter_op_werkpost = QCheckBox("Alleen teamleden die geselecteerde werkposten kennen")
        self.check_filter_op_werkpost.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        self.check_filter_op_werkpost.setChecked(False)  # Default uit
        self.check_filter_op_werkpost.toggled.connect(self._on_werkpost_filter_changed)  # type: ignore
        werkpost_layout.addWidget(self.check_filter_op_werkpost)

        werkpost_group.setLayout(werkpost_layout)
        layout.addWidget(werkpost_group)

        # Teamleden sectie
        from PyQt6.QtWidgets import QGroupBox
        teamleden_group = QGroupBox("👥 TEAMLEDEN FILTER")
        teamleden_layout = QVBoxLayout()

        # Info
        info = QLabel("Selecteer welke teamleden je wilt zien:")
        info.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        teamleden_layout.addWidget(info)

        # NIEUW: Toon reserves checkbox
        self.check_toon_reserves = QCheckBox("Toon reserves")
        self.check_toon_reserves.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        self.check_toon_reserves.setChecked(True)  # Default: reserves tonen
        self.check_toon_reserves.toggled.connect(self._on_reserves_filter_changed)  # type: ignore
        teamleden_layout.addWidget(self.check_toon_reserves)

        # Quick filters
        quick_layout = QHBoxLayout()

        alle_btn = QPushButton("Selecteer Alles")
        alle_btn.clicked.connect(self.selecteer_alles)  # type: ignore
        alle_btn.setStyleSheet(Styles.button_secondary())
        quick_layout.addWidget(alle_btn)

        geen_btn = QPushButton("Deselecteer Alles")
        geen_btn.clicked.connect(self.deselecteer_alles)  # type: ignore
        geen_btn.setStyleSheet(Styles.button_secondary())
        quick_layout.addWidget(geen_btn)

        teamleden_layout.addLayout(quick_layout)

        # Scroll area met checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(250)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Checkbox per gebruiker
        for gebruiker in self.gebruikers_data:
            checkbox = QCheckBox(f"{gebruiker['volledige_naam']} ({gebruiker['gebruikersnaam']})")
            initial_checked = self.huidige_filter.get(gebruiker['id'], True)
            checkbox.setChecked(initial_checked)
            checkbox.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
            self.checkboxes[gebruiker['id']] = checkbox

            # Onthoud initiële state voor alle gebruikers
            self.all_users_checked_state[gebruiker['id']] = initial_checked

            scroll_layout.addWidget(checkbox)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        teamleden_layout.addWidget(scroll)

        teamleden_group.setLayout(teamleden_layout)
        layout.addWidget(teamleden_group)

        # Buttons
        buttons = QDialogButtonBox()
        buttons.addButton(QDialogButtonBox.StandardButton.Ok)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)  # type: ignore
        buttons.rejected.connect(self.reject)  # type: ignore
        layout.addWidget(buttons)

        self.setLayout(layout)

    def selecteer_alles(self) -> None:
        """Selecteer alle checkboxes"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)

    def deselecteer_alles(self) -> None:
        """Deselecteer alle checkboxes"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)

    def _on_werkpost_changed(self) -> None:
        """
        Handle werkpost checkbox wijziging (ISSUE-011)

        Update gebruiker checkboxes op basis van werkpost filter
        """
        # Alleen update doen als werkpost filter actief is
        if self.check_filter_op_werkpost.isChecked():
            self._update_gebruiker_checkboxes()

    def _on_werkpost_filter_changed(self) -> None:
        """
        Handle werkpost filter checkbox wijziging (ISSUE-011)

        Enable/disable gebruiker filtering op basis van werkpost kennis
        """
        self._update_gebruiker_checkboxes()

    def _on_reserves_filter_changed(self) -> None:
        """
        Handle reserves filter checkbox wijziging

        Toon/verberg reserve gebruikers
        Bug fix: Herstel originele checked state bij tonen
        """
        toon_reserves = self.check_toon_reserves.isChecked()

        for gebruiker_id, checkbox in self.checkboxes.items():
            if gebruiker_id in self.reserve_gebruiker_ids:
                # Dit is een reserve
                if toon_reserves:
                    # Toon reserve: enable en HERSTEL checked state
                    # Check of werkpost filter actief is en deze gebruiker zou disablen
                    if self.check_filter_op_werkpost.isChecked():
                        # Laat werkpost filter de enabled state bepalen
                        self._update_gebruiker_checkboxes()
                    else:
                        checkbox.setEnabled(True)

                    # KRITIEK: Herstel originele checked state
                    # Probeer eerst all_users_checked_state, dan reserves_checked_state
                    if gebruiker_id in self.all_users_checked_state:
                        checkbox.setChecked(self.all_users_checked_state[gebruiker_id])
                    elif gebruiker_id in self.reserves_checked_state:
                        checkbox.setChecked(self.reserves_checked_state[gebruiker_id])
                    else:
                        # Default: reserves zijn checked (standaard aan bij opstarten)
                        checkbox.setChecked(True)
                else:
                    # Verberg reserve: sla huidige state op, dan disable en uncheck
                    # Sla state op VOORDAT we unchecken (in beide dictionaries)
                    self.all_users_checked_state[gebruiker_id] = checkbox.isChecked()
                    self.reserves_checked_state[gebruiker_id] = checkbox.isChecked()

                    checkbox.setEnabled(False)
                    checkbox.setChecked(False)

    def _update_gebruiker_checkboxes(self) -> None:
        """
        Update welke gebruiker checkboxes enabled/disabled zijn (ISSUE-011)

        Als werkpost filter actief is, disable gebruikers die geen van de
        geselecteerde werkposten kennen.

        Ook rekening houden met reserves filter (verberg reserves optie).
        """
        # Check beide filters
        werkpost_filter_actief = self.check_filter_op_werkpost.isChecked()
        toon_reserves = self.check_toon_reserves.isChecked()

        if not werkpost_filter_actief:
            # Werkpost filter uit: enable gebruikers (maar respecteer reserves filter)
            for gebruiker_id, checkbox in self.checkboxes.items():
                is_reserve = gebruiker_id in self.reserve_gebruiker_ids

                if is_reserve and not toon_reserves:
                    # Reserve en reserves zijn verborgen: disable
                    # Sla state op voordat we disablen
                    self.all_users_checked_state[gebruiker_id] = checkbox.isChecked()
                    checkbox.setEnabled(False)
                    checkbox.setChecked(False)
                else:
                    # Enable en HERSTEL checked state
                    checkbox.setEnabled(True)
                    # Herstel opgeslagen state (of gebruik current state als die niet bestaat)
                    if gebruiker_id in self.all_users_checked_state:
                        checkbox.setChecked(self.all_users_checked_state[gebruiker_id])
            return

        # Werkpost filter aan: bepaal welke gebruikers geselecteerde werkposten kennen
        geselecteerde_werkpost_ids = [
            wp_id for wp_id, wp_checkbox in self.werkpost_checkboxes.items()
            if wp_checkbox.isChecked()
        ]

        if not geselecteerde_werkpost_ids:
            # Geen werkposten geselecteerd: disable alle gebruikers
            for checkbox in self.checkboxes.values():
                checkbox.setEnabled(False)
                checkbox.setChecked(False)
            return

        # Query: welke gebruikers kennen minstens 1 van de geselecteerde werkposten?
        from database.connection import get_connection
        conn = get_connection()
        cursor = conn.cursor()

        placeholders = ','.join(['?'] * len(geselecteerde_werkpost_ids))
        query = f"""
            SELECT DISTINCT gebruiker_id
            FROM gebruiker_werkposten
            WHERE werkpost_id IN ({placeholders})
        """
        cursor.execute(query, geselecteerde_werkpost_ids)
        results = cursor.fetchall()
        conn.close()

        # Set van gebruiker IDs die minstens 1 werkpost kennen
        toegestane_gebruiker_ids = {row['gebruiker_id'] for row in results}

        # Update checkboxes: enable/disable op basis van BEIDE filters
        for gebruiker_id, checkbox in self.checkboxes.items():
            is_reserve = gebruiker_id in self.reserve_gebruiker_ids
            kent_werkpost = gebruiker_id in toegestane_gebruiker_ids

            # Gebruiker is enabled ALS:
            # 1. Kent de werkpost (werkpost filter)
            # EN
            # 2. Is geen reserve OF reserves worden getoond (reserves filter)
            if kent_werkpost and (not is_reserve or toon_reserves):
                checkbox.setEnabled(True)
                # Bug fix: Herstel checked state (voor alle gebruikers, niet alleen reserves)
                if gebruiker_id in self.all_users_checked_state:
                    checkbox.setChecked(self.all_users_checked_state[gebruiker_id])
                # Extra: ook reserves state
                if is_reserve and gebruiker_id in self.reserves_checked_state:
                    checkbox.setChecked(self.reserves_checked_state[gebruiker_id])
            else:
                # Sla checked state op VOORDAT we disablen
                self.all_users_checked_state[gebruiker_id] = checkbox.isChecked()
                if is_reserve:
                    self.reserves_checked_state[gebruiker_id] = checkbox.isChecked()

                checkbox.setEnabled(False)
                checkbox.setChecked(False)  # Uncheck disabled users

    def get_filter(self) -> Dict[int, bool]:
        """Return filter dict"""
        return {
            gebruiker_id: checkbox.isChecked()
            for gebruiker_id, checkbox in self.checkboxes.items()
        }