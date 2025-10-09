# gui/screens/dashboard_screen.py
"""
Dashboard scherm voor Planning Tool
FIXED: Instance attributes in __init__ + PyCharm type hints
UPDATED: Teamleden kunnen wachtwoord wijzigen + Feestdagen alleen voor planners
"""
from typing import Dict, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTabWidget, QScrollArea, QFrame,
                             QDialog, QLineEdit, QMessageBox, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from gui.styles import Styles, Colors, Fonts, Dimensions
from gui.dialogs.about_dialog import AboutDialog
import bcrypt
from database.connection import get_connection
import sqlite3


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
    kalender_test_clicked = pyqtSignal()
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

    def show_wachtwoord_dialog(self) -> None:
        """Toon wachtwoord wijzig dialog"""
        dialog = WachtwoordWijzigenDialog(self, self.user_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self,
                "Succes",
                "Je wachtwoord is succesvol gewijzigd!"
            )

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

        # FIXED: Alleen "Mijn Planning" tab voor teamleden (geen leeg Instellingen tab)
        self.tabs.addTab(self.create_persoonlijk_tab(), "Mijn Planning")

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

        # Kalender Test knop (development only)
        scroll_layout.addWidget(self.create_menu_button(
            "Kalender Test",
            "Test de kalender widgets (development)"
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

        # NIEUW: Voor iedereen - Wachtwoord wijzigen
        scroll_layout.addWidget(self.create_menu_button(
            "Wijzig Wachtwoord",
            "Wijzig je inlogwachtwoord"
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

        # FIXED: Alle instellingen alleen voor planners
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

            scroll_layout.addWidget(self.create_menu_button(
                "Rode Lijnen",
                "Bekijk 28-dagen arbeidsduurcycli"
            ))

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        return widget

    def create_menu_button(self, title: str, description: str) -> QPushButton:
        """Maak een menu knop met titel en beschrijving - CRASHPROOF zonder nested layout"""
        # Container widget ipv button met layout
        container = QWidget()
        container.setMinimumHeight(80)
        container.setCursor(Qt.CursorShape.PointingHandCursor)

        container.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.BG_WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Dimensions.RADIUS_LARGE}px;
            }}
            QWidget:hover {{
                background-color: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(
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

        container_layout.addWidget(title_label)
        container_layout.addWidget(desc_label)

        # Mouse event handler voor click
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.handle_menu_click(title)

        container.mousePressEvent = mousePressEvent

        return container

    def handle_menu_click(self, title: str) -> None:
        """Handle menu button clicks"""
        if title == "Gebruikersbeheer":
            self.gebruikers_clicked.emit()  # type: ignore
        elif title == "Feestdagen":
            self.feestdagen_clicked.emit()  # type: ignore
        elif title == "HR Regels":
            self.hr_regels_clicked.emit()  # type: ignore
        elif title == "Shift Codes & Posten":
            self.shift_codes_clicked.emit()  # type: ignore
        elif title == "Rode Lijnen":
            self.rode_lijnen_clicked.emit()  # type: ignore
        elif title == "Planning Editor":
            self.planning_clicked.emit()  # type: ignore
        elif title == "Verlof Aanvragen" or title == "Verlof Goedkeuring":
            self.verlof_clicked.emit()  # type: ignore
        elif title == "Mijn Voorkeuren":
            self.voorkeuren_clicked.emit()  # type: ignore
        elif title == "Mijn Planning":
            self.planning_clicked.emit()  # type: ignore
        elif title == "Kalender Test":
            self.kalender_test_clicked.emit()  # type: ignore
        elif title == "Wijzig Wachtwoord":
            self.show_wachtwoord_dialog()


class WachtwoordWijzigenDialog(QDialog):
    """Dialog voor het wijzigen van wachtwoord"""

    def __init__(self, parent: QWidget, user_data: Dict[str, Any]):
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle("Wijzig Wachtwoord")
        self.setModal(True)
        self.setMinimumWidth(400)

        # Instance attributes
        self.huidig_input: QLineEdit = QLineEdit()
        self.nieuw_input: QLineEdit = QLineEdit()
        self.bevestig_input: QLineEdit = QLineEdit()

        self.init_ui()

    def init_ui(self) -> None:
        """Initialiseer UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Titel
        titel = QLabel("Wijzig je wachtwoord")
        titel.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_LARGE, QFont.Weight.Bold))
        layout.addWidget(titel)

        # Huidig wachtwoord
        huidig_label = QLabel("Huidig wachtwoord:")
        layout.addWidget(huidig_label)

        self.huidig_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.huidig_input.setPlaceholderText("Voer je huidige wachtwoord in")
        self.huidig_input.setStyleSheet(Styles.input_field())
        self.huidig_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        layout.addWidget(self.huidig_input)

        # Nieuw wachtwoord
        nieuw_label = QLabel("Nieuw wachtwoord:")
        layout.addWidget(nieuw_label)

        self.nieuw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.nieuw_input.setPlaceholderText("Minimaal 4 karakters")
        self.nieuw_input.setStyleSheet(Styles.input_field())
        self.nieuw_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        layout.addWidget(self.nieuw_input)

        # Bevestig nieuw wachtwoord
        bevestig_label = QLabel("Bevestig nieuw wachtwoord:")
        layout.addWidget(bevestig_label)

        self.bevestig_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.bevestig_input.setPlaceholderText("Herhaal je nieuwe wachtwoord")
        self.bevestig_input.setStyleSheet(Styles.input_field())
        self.bevestig_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        layout.addWidget(self.bevestig_input)

        # Info tekst (ZONDER emoji - Windows compatibility)
        info = QLabel("Je wachtwoord moet minimaal 4 karakters lang zijn.")
        info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: {Fonts.SIZE_SMALL}px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Buttons
        buttons = QDialogButtonBox()
        buttons.addButton("Wijzigen", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Annuleren", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.valideer_en_wijzig)  # type: ignore
        buttons.rejected.connect(self.reject)  # type: ignore
        layout.addWidget(buttons)

    def valideer_en_wijzig(self) -> None:
        """Valideer input en wijzig wachtwoord"""
        huidig = self.huidig_input.text()
        nieuw = self.nieuw_input.text()
        bevestig = self.bevestig_input.text()

        # Validaties
        if not huidig or not nieuw or not bevestig:
            QMessageBox.warning(self, "Fout", "Vul alle velden in!")
            return

        if len(nieuw) < 4:
            QMessageBox.warning(self, "Fout", "Je nieuwe wachtwoord moet minimaal 4 karakters lang zijn!")
            return

        if nieuw != bevestig:
            QMessageBox.warning(self, "Fout", "De nieuwe wachtwoorden komen niet overeen!")
            return

        try:
            # Check huidig wachtwoord
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT wachtwoord_hash FROM gebruikers WHERE id = ?",
                (self.user_data['id'],)
            )
            result = cursor.fetchone()

            if not result:
                conn.close()
                QMessageBox.critical(self, "Fout", "Gebruiker niet gevonden!")
                return

            # Verifieer huidig wachtwoord
            if not bcrypt.checkpw(huidig.encode('utf-8'), result['wachtwoord_hash']):
                conn.close()
                QMessageBox.warning(self, "Fout", "Het huidige wachtwoord is onjuist!")
                return

            # Update naar nieuw wachtwoord
            nieuw_hash = bcrypt.hashpw(nieuw.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "UPDATE gebruikers SET wachtwoord_hash = ? WHERE id = ?",
                (nieuw_hash, self.user_data['id'])
            )
            conn.commit()
            conn.close()

            # Succes!
            self.accept()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Er is een fout opgetreden: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Er is een onverwachte fout opgetreden: {str(e)}")