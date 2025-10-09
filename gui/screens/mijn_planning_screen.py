#gui/screens/mijn_planning_screen.py

"""
Mijn Planning Scherm
Teamleden bekijken hun eigen rooster en kunnen collega's filteren
"""
from typing import Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime
from gui.styles import Styles, Colors, Fonts, Dimensions
from gui.widgets import TeamlidGridKalender


class MijnPlanningScreen(QWidget):
    """
    Mijn Planning scherm voor teamleden
    Toont TeamlidGridKalender met eigen rooster
    """

    def __init__(self, router: Callable, gebruiker_id: int):
        super().__init__()
        self.router = router
        self.gebruiker_id = gebruiker_id

        # Instance attributes
        self.kalender: TeamlidGridKalender = TeamlidGridKalender(
            datetime.now().year,
            datetime.now().month,
            self.gebruiker_id
        )

        self.init_ui()

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

        layout.addLayout(header)

        # Info box
        info_box = QLabel(
            "Bekijk hier je eigen rooster. "
            "Gebruik de filter knop rechtsboven om collega's te bekijken."
        )
        info_box.setStyleSheet(Styles.info_box())
        info_box.setWordWrap(True)
        layout.addWidget(info_box)

        # Kalender widget
        layout.addWidget(self.kalender)