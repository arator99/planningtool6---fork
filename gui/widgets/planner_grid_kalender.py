#gui/widgets/planner_grid_kalender.py
"""
Planner Grid Kalender
Editable kalender voor planners met buffer dagen en scroll functionaliteit
"""
from typing import Dict, Any, List, Optional, Callable
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QComboBox, QScrollArea, QWidget, QGridLayout,
                             QCheckBox, QDialog, QDialogButtonBox, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from gui.widgets.grid_kalender_base import GridKalenderBase
from gui.styles import Styles, Colors, Fonts, Dimensions
from datetime import datetime


class PlannerGridKalender(GridKalenderBase):
    """
    Grid kalender voor planners
    - Volledige maand + 8 dagen buffer voor/na
    - Horizontaal scrollable
    - Alle teamleden (met filter)
    - Editable cellen
    - Verlof status overlays
    """

    # Signal voor cel click
    cel_clicked: pyqtSignal = pyqtSignal(str, int)  # (datum_str, gebruiker_id)

    def __init__(self, jaar: int, maand: int):
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
            "Toont 8 dagen voor en 8 dagen na de geselecteerde maand voor betere planning continuïteit"
        )

    def load_initial_data(self) -> None:
        """Laad initiële data"""
        # Laad gebruikers
        self.load_gebruikers(alleen_actief=True)

        # Standaard: iedereen zichtbaar (planner view)
        self.set_alle_gebruikers_filter(True)

        # Laad feestdagen
        self.load_feestdagen()

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

    def build_grid(self) -> None:
        """Bouw de grid met namen en datums"""
        # Clear bestaande layout
        if self.grid_container.layout():
            QWidget().setLayout(self.grid_container.layout())

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
        naam_header.setFixedWidth(200)
        grid_layout.addWidget(naam_header, 0, 0)

        # Datum headers
        for col, (datum_str, label) in enumerate(datum_lijst, start=1):
            datum_header = QLabel(label)
            datum_header.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY, QFont.Weight.Bold))

            # Achtergrond kleur voor header
            achtergrond = self.get_datum_achtergrond(datum_str)

            # Highlight huidige maand dagen
            datum_obj = datetime.strptime(datum_str, '%Y-%m-%d')
            if datum_obj.month == self.maand:
                # Huidige maand: donkerder border
                border_style = f"2px solid {Colors.PRIMARY}"
            else:
                # Buffer dagen: normale border
                border_style = f"1px solid {Colors.BORDER_LIGHT}"

            datum_header.setStyleSheet(f"""
                QLabel {{
                    background-color: {achtergrond};
                    color: {Colors.TEXT_PRIMARY};
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
            naam_label.setFixedWidth(200)
            grid_layout.addWidget(naam_label, row, 0)

            # Shift cellen
            for col, (datum_str, _) in enumerate(datum_lijst, start=1):
                cel = self.create_shift_cel(datum_str, gebruiker_id, mode='planner')
                cel.setFixedWidth(60)

                # Maak cel klikbaar
                cel.mousePressEvent = self.create_cel_click_handler(datum_str, gebruiker_id)
                cel.setCursor(Qt.CursorShape.PointingHandCursor)

                grid_layout.addWidget(cel, row, col)
        #for row in range(grid_layout.rowCount()):
        #    grid_layout.setRowMinimumHeight(row, Dimensions.TABLE_ROW_HEIGHT)
        #    grid_layout.setRowStretch(row, 0)
        self.grid_container.setMaximumHeight(grid_layout.rowCount() * Dimensions.TABLE_ROW_HEIGHT)

        self.grid_container.setLayout(grid_layout)

    def create_shift_cel(self, datum_str: str, gebruiker_id: int, mode: str) -> QLabel:
        """
        Maak cel voor shift weergave
        Editable voor planner view
        """

        # Haal shift code op
        shift_code = self.get_display_code(datum_str, gebruiker_id)

        # Bepaal achtergrond en overlay
        achtergrond = self.get_datum_achtergrond(datum_str)
        overlay = self.get_verlof_overlay(datum_str, gebruiker_id, mode)

        # Check of dit een buffer dag is (andere maand)
        datum_obj = datetime.strptime(datum_str, '%Y-%m-%d')
        is_buffer = datum_obj.month != self.maand

        # Maak label
        cel = QLabel(shift_code)
        cel.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL, QFont.Weight.Bold))

        # Stylesheet met optionele grijze tint voor buffer dagen
        if is_buffer:
            # Buffer dag: iets transparanter
            base_style = self.create_cel_stylesheet(achtergrond, overlay)
            cel.setStyleSheet(base_style + f" QLabel {{ opacity: 0.7; }}")
        else:
            cel.setStyleSheet(self.create_cel_stylesheet(achtergrond, overlay))

        # Tooltip
        tooltip = self.get_cel_tooltip(datum_str, gebruiker_id, mode)
        if tooltip:
            cel.setToolTip(tooltip)

        # hoogte beperken van de cel
        #cel.setFixedHeight(32)  # of zelfs 28
        #cel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        #cel.setStyleSheet("background-color: #ffeecc; border: 1px solid #ccc;")  # tijdelijk

        return cel

    def create_cel_click_handler(self, datum_str: str, gebruiker_id: int):
        """Factory voor cel click handler (voorkomt closure problemen)"""

        def handler(event):
            self.on_cel_clicked(datum_str, gebruiker_id)

        return handler

    def on_cel_clicked(self, datum_str: str, gebruiker_id: int) -> None:
        """Handle cel click - emit signal voor parent"""
        self.cel_clicked.emit(datum_str, gebruiker_id)  # type: ignore

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