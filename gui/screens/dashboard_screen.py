#gui/screens/dashboard_screen.py

"""
Dashboard scherm voor Planning Tool
FIXED: Instance attributes in __init__ + PyCharm type hints
"""
from typing import Dict, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTabWidget, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from gui.styles import Styles, Colors, Fonts, Dimensions
from gui.dialogs.about_dialog import AboutDialog


class DashboardScreen(QWidget):
    """Dashboard met tabs voor Beheer, Persoonlijk en Instellingen"""

    # SIGNALS - Class-level declaratie
    gebruikers_clicked = pyqtSignal()
    typedienst_clicked = pyqtSignal()
    voorkeuren_clicked = pyqtSignal()
    hr_regels_clicked = pyqtSignal()
    shift_codes_clicked = pyqtSignal()
    feestdagen_clicked = pyqtSignal()
    rode_lijnen_clicked = pyqtSignal()
    planning_clicked = pyqtSignal()
    verlof_clicked = pyqtSignal()
    logout_signal = pyqtSignal()

    def __init__(self, user_data: Dict[str, Any]):
        super().__init__()
        self.user_data = user_data

        # Instance attributes declareren in __init__
        self.header_frame: QFrame = QFrame()
        self.tabs: QTabWidget = QTabWidget()

        # UI initialiseren
        self.init_ui()

    def init_ui(self) -> None:
        """Initialiseer de user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.create_header()
        layout.addWidget(self.header_frame)

        # Tabs gebaseerd op rol
        if self.user_data['rol'] == 'planner':
            self.create_planner_tabs()
        else:
            self.create_teamlid_tabs()

        layout.addWidget(self.tabs)

    def create_header(self) -> None:
        """Maak header met welkom en logout"""
        self.header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.PRIMARY};
                padding: {Dimensions.SPACING_LARGE}px;
            }}
        """)

        header_layout = QHBoxLayout(self.header_frame)

        # Welkom tekst
        welkom_label = QLabel(f"Welkom, {self.user_data['naam']}")
        welkom_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        welkom_label.setStyleSheet(f"color: {Colors.TEXT_WHITE};")
        header_layout.addWidget(welkom_label)

        header_layout.addStretch()

        # About knop
        about_btn = QPushButton("Over")
        about_btn.setStyleSheet(Styles.button_secondary())
        about_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        about_btn.clicked.connect(self.show_about_dialog)
        header_layout.addWidget(about_btn)

        # Logout knop
        logout_btn = QPushButton("Uitloggen")
        logout_btn.setStyleSheet(Styles.button_danger())
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self.logout_signal.emit)  # type: ignore
        header_layout.addWidget(logout_btn)

    def show_about_dialog(self) -> None:
        """Toon About dialog"""
        dialog = AboutDialog(self)
        dialog.exec()

    def create_planner_tabs(self) -> None:
        """Maak tabs voor planner rol"""
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {Colors.BG_LIGHT};
            }}
            QTabBar::tab {{
                background-color: {Colors.BG_WHITE};
                color: {Colors.TEXT_PRIMARY};
                padding: {Dimensions.SPACING_MEDIUM}px {Dimensions.SPACING_LARGE}px;
                margin-right: 2px;
                border-top-left-radius: {Dimensions.RADIUS_MEDIUM}px;
                border-top-right-radius: {Dimensions.RADIUS_MEDIUM}px;
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_WHITE};
            }}
            QTabBar::tab:hover {{
                background-color: {Colors.PRIMARY_HOVER};
                color: {Colors.TEXT_WHITE};
            }}
        """)

        self.tabs.addTab(self.create_beheer_tab(), "Beheer")
        self.tabs.addTab(self.create_persoonlijk_tab(), "Persoonlijk")
        self.tabs.addTab(self.create_instellingen_tab(), "Instellingen")

    def create_teamlid_tabs(self) -> None:
        """Maak tabs voor teamlid rol"""
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {Colors.BG_LIGHT};
            }}
            QTabBar::tab {{
                background-color: {Colors.BG_WHITE};
                color: {Colors.TEXT_PRIMARY};
                padding: {Dimensions.SPACING_MEDIUM}px {Dimensions.SPACING_LARGE}px;
                margin-right: 2px;
                border-top-left-radius: {Dimensions.RADIUS_MEDIUM}px;
                border-top-right-radius: {Dimensions.RADIUS_MEDIUM}px;
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_WHITE};
            }}
        """)

        self.tabs.addTab(self.create_persoonlijk_tab(), "Mijn Planning")
        self.tabs.addTab(self.create_instellingen_tab(), "Instellingen")

    def create_beheer_tab(self) -> QWidget:
        """Maak Beheer tab (alleen voor planner)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE
        )
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        title = QLabel("Beheer")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(title)

        # Scroll area voor menu items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Menu items
        scroll_layout.addWidget(self.create_menu_button(
            "Planning Editor",
            "Maak en beheer de maandplanning"
        ))

        scroll_layout.addWidget(self.create_menu_button(
            "Verlof Goedkeuring",
            "Beheer verlofaanvragen van teamleden"
        ))

        scroll_layout.addWidget(self.create_menu_button(
            "Gebruikersbeheer",
            "Beheer teamleden en hun toegang"
        ))

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        return widget

    def create_persoonlijk_tab(self) -> QWidget:
        """Maak Persoonlijk tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE
        )
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        title = QLabel("Persoonlijk")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        scroll_layout.addWidget(self.create_menu_button(
            "Mijn Planning",
            "Bekijk je eigen planning"
        ))

        scroll_layout.addWidget(self.create_menu_button(
            "Verlof Aanvragen",
            "Vraag verlof aan of bekijk je aanvragen"
        ))

        scroll_layout.addWidget(self.create_menu_button(
            "Mijn Voorkeuren",
            "Stel je shift voorkeuren in"
        ))

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        return widget

    def create_instellingen_tab(self) -> QWidget:
        """Maak Instellingen tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE
        )
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        title = QLabel("Instellingen")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        if self.user_data['rol'] == 'planner':
            scroll_layout.addWidget(self.create_menu_button(
                "HR Regels",
                "Configureer arbeidsregels en rusttijden"
            ))

            scroll_layout.addWidget(self.create_menu_button(
                "Shift Codes & Posten",
                "Beheer shift codes per post"
            ))

        scroll_layout.addWidget(self.create_menu_button(
            "Feestdagen",
            "Beheer feestdagen per jaar"
        ))

        if self.user_data['rol'] == 'planner':
            scroll_layout.addWidget(self.create_menu_button(
                "Rode Lijnen",
                "Bekijk 28-dagen arbeidsduurcycli"
            ))

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        return widget

    def create_menu_button(self, title: str, description: str) -> QPushButton:
        """Maak een menu knop met titel en beschrijving"""
        btn = QPushButton()
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(80)

        # Styling
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Dimensions.RADIUS_LARGE}px;
                text-align: left;
                padding: {Dimensions.SPACING_MEDIUM}px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
            }}
        """)

        # Layout binnen button
        btn_layout = QVBoxLayout(btn)
        btn_layout.setContentsMargins(
            Dimensions.SPACING_MEDIUM,
            Dimensions.SPACING_SMALL,
            Dimensions.SPACING_MEDIUM,
            Dimensions.SPACING_SMALL
        )

        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent; border: none;")

        desc_label = QLabel(description)
        desc_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        desc_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent; border: none;")

        btn_layout.addWidget(title_label)
        btn_layout.addWidget(desc_label)

        # Connect signals gebaseerd op titel
        if title == "Gebruikersbeheer":
            btn.clicked.connect(self.gebruikers_clicked.emit)  # type: ignore
        elif title == "Feestdagen":
            btn.clicked.connect(self.feestdagen_clicked.emit)  # type: ignore
        elif title == "HR Regels":
            btn.clicked.connect(self.hr_regels_clicked.emit)  # type: ignore
        elif title == "Shift Codes & Posten":
            btn.clicked.connect(self.shift_codes_clicked.emit)  # type: ignore
        elif title == "Rode Lijnen":
            btn.clicked.connect(self.rode_lijnen_clicked.emit)  # type: ignore
        elif title == "Planning Editor":
            btn.clicked.connect(self.planning_clicked.emit)  # type: ignore
        elif title == "Verlof Aanvragen" or title == "Verlof Goedkeuring":
            btn.clicked.connect(self.verlof_clicked.emit)  # type: ignore
        elif title == "Mijn Voorkeuren":
            btn.clicked.connect(self.voorkeuren_clicked.emit)  # type: ignore

        return btn