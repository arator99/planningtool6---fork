# gui/screens/dashboard_screen.py
"""
Dashboard scherm voor Planning Tool
FIXED: Instance attributes in __init__ + PyCharm type hints
UPDATED: Teamleden kunnen wachtwoord wijzigen + Feestdagen alleen voor planners
"""
from typing import Dict, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTabWidget, QScrollArea, QFrame,
                             QDialog, QLineEdit, QMessageBox, QDialogButtonBox,
                             QDateEdit, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont
from gui.styles import Styles, Colors, Fonts, Dimensions
from gui.dialogs.about_dialog import AboutDialog
from gui.widgets.theme_toggle_widget import ThemeToggleWidget
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
    logout_signal = pyqtSignal()
    planning_editor_clicked: pyqtSignal = pyqtSignal()  # NIEUW
    verlof_aanvragen_clicked: pyqtSignal = pyqtSignal()  # Voor teamleden
    verlof_goedkeuring_clicked: pyqtSignal = pyqtSignal()  # Voor planners
    verlof_saldo_beheer_clicked: pyqtSignal = pyqtSignal()  # Voor admin - v0.6.10
    werkpost_koppeling_clicked: pyqtSignal = pyqtSignal()  # Voor admin - v0.6.14



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

    def get_pending_leave_count(self) -> int:
        """Haal het aantal openstaande (pending) verlofaanvragen op uit de verlof_aanvragen tabel."""
        count = 0

        # --- CORRECTIE HIER: De status in de DB is 'pending' ---
        pending_status_name = 'pending'
        # ----------------------------------------------------

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Telt het aantal rijen in de CORRECTE tabel: verlof_aanvragen
            cursor.execute(f"""
                SELECT COUNT(*) FROM verlof_aanvragen
                WHERE status = ?
            """, (pending_status_name,))

            count = cursor.fetchone()[0]
            conn.close()

            # U kunt deze prints nu verwijderen, maar ter controle:
            print(f"Aantal gevonden '{pending_status_name}' aanvragen:", count)

        except sqlite3.Error as e:
            print(f"Databasefout bij ophalen verloftelling: {e}")

        return count

    def create_verlof_button_with_badge(self, count: int) -> QWidget:
        """Maakt de 'Verlof Goedkeuring' knop (QWidget) met de rode notificatiebol helemaal rechts, inclusief hover-effect."""

        widget = QWidget()
        # Gebruik objectName voor QSS en geef een PointingHandCursor voor UX
        widget.setObjectName("VerlofMenuItem")
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        widget.setMinimumHeight(80)

        # --- GECORRIGEERDE STYLING MET HOVER ---
        widget.setStyleSheet(f"""
            #VerlofMenuItem {{
                background-color: {Colors.BG_WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Dimensions.RADIUS_LARGE}px;
            }}
            #VerlofMenuItem:hover {{
                /* Gebruik de door de gebruiker opgegeven styling */
                background-color: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
            }}
        """)

        # Hoofd layout (Vertical)
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(
            Dimensions.SPACING_MEDIUM,
            Dimensions.SPACING_SMALL,
            Dimensions.SPACING_MEDIUM,
            Dimensions.SPACING_SMALL
        )

        # Bovenste rij (Horizontaal: Titel + Spacer + Badge)
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Titel Label
        title_label = QLabel("Verlof Goedkeuring")
        title_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent; border: none;")
        top_layout.addWidget(title_label)

        # De stretch dwingt de Badge naar de rechterrand.
        top_layout.addStretch()

        # Notificatie Badge (Alleen tonen als count > 0)
        if count > 0:
            notification_label = QLabel(str(count))
            notification_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL, QFont.Weight.Bold))
            notification_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            notification_label.setFixedSize(50, 50)

            # Styling voor de rode bol (cirkel)
            notification_label.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_WHITE};
                    background-color: {Colors.DANGER}; 
                    border-radius: 25px;
                    padding: 0px;
                    background-clip: padding-box;
                   
                }}
            """)
            #top_layout.addWidget(notification_label)
            badge_wrapper = QWidget()
            badge_layout = QVBoxLayout(badge_wrapper)
            badge_layout.setContentsMargins(0, 20, 15, 0)  # ← Laat de bol zakken
            badge_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Of AlignVCenter voor subtieler effect
            badge_layout.addWidget(notification_label)
            badge_wrapper.setStyleSheet("background: transparent;")

            top_layout.addWidget(badge_wrapper)

        main_layout.addLayout(top_layout)

        # Beschrijving Label
        description_label = QLabel("Beheer verlofaanvragen van teamleden")
        description_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        description_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent; border: none;")
        main_layout.addWidget(description_label)

        # Koppel de klikactie
        widget.mousePressEvent = lambda event: self.handle_menu_click("Verlof Goedkeuring")

        return widget

    def refresh_verlof_badge(self):
        """Refresh verlof badge (na goedkeuring/weigering)"""
        # Herlaad de hele Planning tab om de badge te updaten
        if self.user_data['rol'] == 'planner':
            # Vind de Planning tab index (normaal is het tab 1 voor planners)
            planning_tab_index = 1

            # Onthoud huidige tab selectie
            current_tab_index = self.tabs.currentIndex()

            # Verwijder oude Planning tab
            old_widget = self.tabs.widget(planning_tab_index)
            if old_widget:
                self.tabs.removeTab(planning_tab_index)
                old_widget.deleteLater()

            # Maak nieuwe Planning tab met updated badge
            new_planning_tab = self.create_planning_tab()
            self.tabs.insertTab(planning_tab_index, new_planning_tab, "Planning")

            # Herstel tab selectie
            self.tabs.setCurrentIndex(current_tab_index)

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

        # Theme toggle widget
        self.theme_toggle = ThemeToggleWidget()
        self.theme_toggle.theme_changed.connect(self.on_theme_changed)  # type: ignore
        header_layout.addWidget(self.theme_toggle)

        # Handleiding knop
        handleiding_btn = QPushButton("Handleiding (F1)")
        handleiding_btn.setStyleSheet(Styles.button_secondary())
        handleiding_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        handleiding_btn.clicked.connect(self.show_handleiding)  # type: ignore
        header_layout.addWidget(handleiding_btn)

        # About knop
        about_btn = QPushButton("Over")
        about_btn.setStyleSheet(Styles.button_secondary())
        about_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        about_btn.clicked.connect(self.show_about_dialog) # type: ignore
        header_layout.addWidget(about_btn)

        # Logout knop
        logout_btn = QPushButton("Uitloggen")
        logout_btn.setStyleSheet(Styles.button_danger())
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self.logout_signal.emit)  # type: ignore
        header_layout.addWidget(logout_btn)

    def on_theme_changed(self, nieuwe_theme: str) -> None:
        """Handle theme change van toggle widget"""
        # Save theme preference via main window method
        main_window = self.window()
        if hasattr(main_window, 'save_theme_preference'):
            main_window.save_theme_preference(nieuwe_theme)

        # Apply theme via main window (rebuilds dashboard)
        if hasattr(main_window, 'apply_theme'):
            main_window.apply_theme()

    def show_about_dialog(self) -> None:
        """Toon About dialog"""
        dialog = AboutDialog(self)
        dialog.exec()

    def show_handleiding(self) -> None:
        """Toon handleiding dialog"""
        from gui.dialogs.handleiding_dialog import HandleidingDialog
        dialog = HandleidingDialog(self)
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

    def show_notitie_naar_planner_dialog(self) -> None:
        """Toon notitie naar planner dialog"""
        dialog = NotitieNaarPlannerDialog(self, self.user_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self,
                "Notitie Verstuurd",
                "Je notitie is opgeslagen en zichtbaar voor de planner."
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

        self.tabs.addTab(self.create_persoonlijk_tab(), "Persoonlijk")
        self.tabs.addTab(self.create_planning_tab(), "Planning")
        self.tabs.addTab(self.create_beheer_tab(), "Beheer")
        self.tabs.addTab(self.create_instellingen_tab(), "HR-instellingen")

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
        self.tabs.addTab(self.create_persoonlijk_tab(), "Persoonlijk")

    def create_planning_tab(self) -> QWidget:
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

        title = QLabel("Planning")
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

        # --- Verlof Goedkeuring: Gebruik de nieuwe functie met badge ---
        pending_count = self.get_pending_leave_count()
        verlof_btn = self.create_verlof_button_with_badge(pending_count)

        scroll_layout.addWidget(verlof_btn)

        #scroll_layout.addWidget(self.create_menu_button(
        #    "Verlof Goedkeuring",
        #    "Beheer verlofaanvragen van teamleden"
        #))

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        return widget

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
            "Gebruikersbeheer",
            "Beheer teamleden en hun toegang"
        ))

        scroll_layout.addWidget(self.create_menu_button(
            "Shift Codes & Posten",
            "Beheer shift codes per post"
        ))

        scroll_layout.addWidget(self.create_menu_button(
            "Werkpost Koppeling (Postkennis)",
            "Koppel gebruikers aan werkposten voor auto-generatie"
        ))

        scroll_layout.addWidget(self.create_menu_button(
            "Verlof & KD Saldo",
            "Beheer verlof en kompensatiedagen saldi"
        ))

        scroll_layout.addWidget(self.create_menu_button(
            "Typetabel",
            "Beheer het roterend typedienstpatroon"
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

        # NIEUW v0.6.16: Notitie naar planner
        scroll_layout.addWidget(self.create_menu_button(
            "Notitie naar Planner",
            "Laat een notitie achter voor de planner"
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
                "Rode Lijnen",
                "Bekijk 28-dagen arbeidsduurcycli"
            ))

            scroll_layout.addWidget(self.create_menu_button(
                "Feestdagen",
                "Beheer feestdagen per jaar"
            ))

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        return widget

    def create_menu_button(self, title: str, description: str) -> QWidget:
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
        elif title == "Werkpost Koppeling (Postkennis)":
            self.werkpost_koppeling_clicked.emit()  # type: ignore
        elif title == "Typetabel":
            self.typedienst_clicked.emit()  # type: ignore
        elif title == "Rode Lijnen":
            self.rode_lijnen_clicked.emit()  # type: ignore
        elif title == "Planning Editor":
            self.planning_editor_clicked.emit()  # type: ignore
        #elif title == "Verlof Aanvragen" or title == "Verlof Goedkeuring":
        #    self.verlof_clicked.emit()  # type: ignore
        elif title == "Mijn Voorkeuren":
            self.voorkeuren_clicked.emit()  # type: ignore
        elif title == "Mijn Planning":
            self.planning_clicked.emit()  # type: ignore
        elif title == "Wijzig Wachtwoord":
            self.show_wachtwoord_dialog()
        elif title == "Notitie naar Planner":
            self.show_notitie_naar_planner_dialog()
        elif title == "Verlof Aanvragen":
            self.verlof_aanvragen_clicked.emit()  # type: ignore
        elif title == "Verlof Goedkeuring":
            self.verlof_goedkeuring_clicked.emit()  # type: ignore
        elif title == "Verlof & KD Saldo":
            self.verlof_saldo_beheer_clicked.emit()  # type: ignore


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


class NotitieNaarPlannerDialog(QDialog):
    """Dialog voor teamleden om notitie naar planner te sturen"""

    def __init__(self, parent: QWidget, user_data: Dict[str, Any]):
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle("Notitie naar Planner")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Instance attributes
        self.datum_edit: QDateEdit = QDateEdit()
        self.notitie_edit: QTextEdit = QTextEdit()

        self.init_ui()

    def init_ui(self) -> None:
        """Initialiseer UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Uitleg
        uitleg = QLabel(
            "Laat een notitie achter voor de planner. Dit verschijnt in de planning "
            "op de door jou gekozen datum bij jouw naam."
        )
        uitleg.setWordWrap(True)
        uitleg.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: {Dimensions.SPACING_SMALL}px;")
        layout.addWidget(uitleg)

        # Datum selectie
        datum_label = QLabel("Selecteer datum:")
        datum_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        layout.addWidget(datum_label)

        self.datum_edit.setCalendarPopup(True)
        self.datum_edit.setDate(QDate.currentDate())
        self.datum_edit.setStyleSheet(Styles.input_field())
        self.datum_edit.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        layout.addWidget(self.datum_edit)

        # Notitie tekst
        notitie_label = QLabel("Jouw notitie:")
        notitie_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        layout.addWidget(notitie_label)

        self.notitie_edit.setPlaceholderText(
            "Bijv: Heb een afspraak om 15u, kan niet voor late shift. "
            "Of: Verzoek voor vroege shift ivm vervoer."
        )
        self.notitie_edit.setStyleSheet(Styles.input_field())
        layout.addWidget(self.notitie_edit)

        # Info tekst
        info = QLabel(
            "Tip: Houd de notitie kort en duidelijk. De planner ziet dit als "
            "een groen hoekje in de planning grid."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-style: italic; padding: {Dimensions.SPACING_SMALL}px;")
        layout.addWidget(info)

        # Buttons - gebruik type: ignore voor de hele constructie
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel  # type: ignore
        )

        # Haal buttons op en check of ze bestaan
        save_button = button_box.button(QDialogButtonBox.StandardButton.Save)
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)

        if save_button:
            save_button.setText("Opslaan")
        if cancel_button:
            cancel_button.setText("Annuleren")

        button_box.accepted.connect(self.save_notitie)  # type: ignore
        button_box.rejected.connect(self.reject)  # type: ignore
        layout.addWidget(button_box)

    def save_notitie(self) -> None:
        """Sla notitie op in planning tabel"""
        notitie_tekst = self.notitie_edit.toPlainText().strip()

        if not notitie_tekst:
            QMessageBox.warning(
                self,
                "Notitie Leeg",
                "Je moet een notitie invoeren voordat je kunt opslaan."
            )
            return

        # Voeg naam prefix toe voor duidelijkheid
        gebruiker_naam = self.user_data.get('naam', 'Onbekend')
        notitie_met_prefix = f"[{gebruiker_naam}]: {notitie_tekst}"

        datum_str = self.datum_edit.date().toString("yyyy-MM-dd")
        gebruiker_id = self.user_data['id']

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Check of er al een planning record bestaat voor deze datum + gebruiker
            cursor.execute("""
                SELECT id, notitie FROM planning
                WHERE gebruiker_id = ? AND datum = ?
            """, (gebruiker_id, datum_str))
            bestaand = cursor.fetchone()

            if bestaand:
                # Update bestaande notitie
                cursor.execute("""
                    UPDATE planning
                    SET notitie = ?
                    WHERE gebruiker_id = ? AND datum = ?
                """, (notitie_met_prefix, gebruiker_id, datum_str))
            else:
                # Maak nieuw record (alleen met notitie, geen shift_code)
                cursor.execute("""
                    INSERT INTO planning (gebruiker_id, datum, notitie, status)
                    VALUES (?, ?, ?, 'concept')
                """, (gebruiker_id, datum_str, notitie_met_prefix))

            conn.commit()
            conn.close()

            # Succes!
            self.accept()

        except sqlite3.Error as e:
            QMessageBox.critical(
                self,
                "Database Fout",
                f"Kon notitie niet opslaan:\n{str(e)}"
            )