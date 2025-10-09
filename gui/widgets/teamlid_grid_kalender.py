#gui/widgets/teamlid_grid_kalender.py
"""
Teamlid Grid Kalender
Read-only kalender voor teamleden om eigen/collega shifts te bekijken
"""
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QComboBox, QScrollArea, QWidget, QGridLayout,
                             QCheckBox, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from gui.widgets.grid_kalender_base import GridKalenderBase
from gui.styles import Styles, Colors, Fonts, Dimensions
from datetime import datetime


class TeamlidGridKalender(GridKalenderBase):
    """
    Grid kalender voor teamleden
    - Volledige maand weergave (geen buffer)
    - Filter op gebruikers
    - Read-only (alleen bekijken)
    - Verlof/DA/VD overlays
    """

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

        # Grid container (wordt gevuld door build_grid)
        self.grid_container = QWidget()
        layout.addWidget(self.grid_container)

        layout.addStretch()

    def create_header(self) -> QHBoxLayout:
        """Maak header met jaar/maand selectie en filter"""
        header = QHBoxLayout()

        # Titel
        self.title_label = QLabel()
        self.title_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_LARGE))
        self.update_title()
        header.addWidget(self.title_label)

        header.addStretch()

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

    def load_initial_data(self) -> None:
        """Laad initiële data"""
        # Laad gebruikers
        self.load_gebruikers(alleen_actief=True)

        # Standaard: alleen huidige gebruiker zichtbaar
        self.set_alle_gebruikers_filter(False)
        self.filter_gebruikers[self.huidige_gebruiker_id] = True

        # Laad feestdagen
        self.load_feestdagen()

        # Datum range: alleen deze maand
        datum_lijst = self.get_datum_lijst(start_offset=0, eind_offset=0)
        if datum_lijst:
            start_datum = datum_lijst[0][0]
            eind_datum = datum_lijst[-1][0]

            # Laad planning en verlof
            self.load_planning_data(start_datum, eind_datum)
            self.load_verlof_data(start_datum, eind_datum)

        # Bouw grid
        self.build_grid()

    def build_grid(self) -> None:
        """Bouw de grid met namen en datums"""
        # Clear bestaande layout
        if self.grid_container.layout():
            QWidget().setLayout(self.grid_container.layout())

        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Haal datum lijst en zichtbare gebruikers
        datum_lijst = self.get_datum_lijst(start_offset=0, eind_offset=0)
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
        naam_header.setFixedWidth(200)
        grid_layout.addWidget(naam_header, 0, 0)

        # Datum headers
        for col, (datum_str, label) in enumerate(datum_lijst, start=1):
            datum_header = QLabel(label)
            datum_header.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY, QFont.Weight.Bold))

            # Achtergrond kleur voor header (geel voor zondag/feestdag, grijs voor zaterdag)
            achtergrond = self.get_datum_achtergrond(datum_str)
            datum_header.setStyleSheet(f"""
                QLabel {{
                    background-color: {achtergrond};
                    color: {Colors.TEXT_PRIMARY};
                    padding: 4px;
                    border: 1px solid {Colors.BORDER_LIGHT};
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
            naam_label.setFixedWidth(200)
            grid_layout.addWidget(naam_label, row, 0)

            # Shift cellen
            for col, (datum_str, _) in enumerate(datum_lijst, start=1):
                cel = self.create_shift_cel(datum_str, gebruiker_id, mode='teamlid')
                cel.setFixedWidth(60)
                grid_layout.addWidget(cel, row, col)

        self.grid_container.setLayout(grid_layout)

    def create_shift_cel(self, datum_str: str, gebruiker_id: int, mode: str) -> QLabel:
        """
        Maak cel voor shift weergave
        Read-only voor teamlid view
        """
        # Haal shift code op
        shift_code = self.get_display_code(datum_str, gebruiker_id)

        # Bepaal achtergrond en overlay
        achtergrond = self.get_datum_achtergrond(datum_str)
        overlay = self.get_verlof_overlay(datum_str, gebruiker_id, mode)

        # Maak label
        cel = QLabel(shift_code)
        cel.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL, QFont.Weight.Bold))
        cel.setStyleSheet(self.create_cel_stylesheet(achtergrond, overlay))

        # Tooltip
        tooltip = self.get_cel_tooltip(datum_str, gebruiker_id, mode)
        if tooltip:
            cel.setToolTip(tooltip)

        return cel

    def open_filter_dialog(self) -> None:
        """Open dialog om gebruikers te filteren"""
        dialog = FilterDialog(self.gebruikers_data, self.filter_gebruikers, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.filter_gebruikers = dialog.get_filter()
            self.build_grid()

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


class FilterDialog(QDialog):
    """Dialog om teamleden te selecteren voor weergave"""

    def __init__(self, gebruikers_data: List[Dict[str, Any]],
                 huidige_filter: Dict[int, bool],
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.gebruikers_data = gebruikers_data
        self.huidige_filter = huidige_filter.copy()
        self.checkboxes: Dict[int, QCheckBox] = {}

        self.setWindowTitle("Filter Teamleden")
        self.setModal(True)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()

        # Info
        info = QLabel("Selecteer welke teamleden je wilt zien in de planning:")
        info.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        layout.addWidget(info)

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

        layout.addLayout(quick_layout)

        # Scroll area met checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Checkbox per gebruiker
        for gebruiker in self.gebruikers_data:
            checkbox = QCheckBox(f"{gebruiker['volledige_naam']} ({gebruiker['gebruikersnaam']})")
            checkbox.setChecked(self.huidige_filter.get(gebruiker['id'], True))
            checkbox.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
            self.checkboxes[gebruiker['id']] = checkbox
            scroll_layout.addWidget(checkbox)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

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

    def get_filter(self) -> Dict[int, bool]:
        """Return filter dict"""
        return {
            gebruiker_id: checkbox.isChecked()
            for gebruiker_id, checkbox in self.checkboxes.items()
        }