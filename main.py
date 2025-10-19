#main.py
"""
Main entry point voor Planning Tool
FIXED: Signal namen + type hints + instance attributes
"""
import sys
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtGui import QKeySequence, QShortcut
from database.connection import init_database
from gui.screens.login_screen import LoginScreen
from gui.screens.dashboard_screen import DashboardScreen
from gui.screens.feestdagen_screen import FeestdagenScherm
from gui.screens.gebruikersbeheer_screen import GebruikersbeheerScreen
from gui.screens.mijn_planning_screen import MijnPlanningScreen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_user: Optional[Dict[str, Any]] = None
        self.login_screen: Optional[LoginScreen] = None

        # Stacked widget voor schermen wisselen
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.setWindowTitle("Planning Tool")
        self.resize(1000, 700)

        # Globale F1 shortcut voor handleiding
        self.help_shortcut = QShortcut(QKeySequence("F1"), self)
        self.help_shortcut.activated.connect(self.show_handleiding)  # type: ignore

        self.show_login()

    def show_login(self) -> None:
        """Toon login scherm"""
        self.login_screen = LoginScreen()
        self.login_screen.login_success.connect(self.on_login_success)  # type: ignore
        self.stack.addWidget(self.login_screen)
        self.stack.setCurrentWidget(self.login_screen)

    def on_login_success(self, user_data: Dict[str, Any]) -> None:
        """Na succesvolle login"""
        self.current_user = user_data
        self.showMaximized()  # Maximaliseer window na login
        self.show_dashboard()

    def terug(self) -> None:
        """Ga terug naar vorig scherm (dashboard)"""
        if self.stack.count() > 1:
            # Verwijder huidig scherm
            current = self.stack.currentWidget()
            self.stack.removeWidget(current)
            if current:
                current.deleteLater()

    def show_dashboard(self) -> None:
        """Toon dashboard"""
        if not self.current_user:
            return

        dashboard = DashboardScreen(self.current_user)

        # FIXED: Signal namen moeten matchen met DashboardScreen
        dashboard.logout_signal.connect(self.on_logout)  # type: ignore
        dashboard.planning_clicked.connect(self.on_planning_clicked)  # type: ignore
        dashboard.verlof_clicked.connect(self.on_verlof_clicked)  # type: ignore
        dashboard.gebruikers_clicked.connect(self.on_gebruikers_clicked)  # type: ignore
        dashboard.typedienst_clicked.connect(self.on_typedienst_clicked)  # type: ignore
        dashboard.voorkeuren_clicked.connect(self.on_voorkeuren_clicked)  # type: ignore
        dashboard.hr_regels_clicked.connect(self.on_hr_regels_clicked)  # type: ignore
        dashboard.shift_codes_clicked.connect(self.on_shift_codes_clicked)  # type: ignore
        dashboard.feestdagen_clicked.connect(self.on_feestdagen_clicked)  # type: ignore
        dashboard.rode_lijnen_clicked.connect(self.on_rode_lijnen_clicked)  # type: ignore
        dashboard.planning_editor_clicked.connect(self.on_planning_editor_clicked)  # type: ignore
        dashboard.verlof_aanvragen_clicked.connect(self.on_verlof_aanvragen_clicked)  # type: ignore
        dashboard.verlof_goedkeuring_clicked.connect(self.on_verlof_goedkeuring_clicked)  # type: ignore

        self.stack.addWidget(dashboard)
        self.stack.setCurrentWidget(dashboard)

    # Bestaande handlers
    def on_gebruikers_clicked(self) -> None:
        """Open gebruikersbeheer scherm"""
        scherm = GebruikersbeheerScreen(self.terug)
        self.stack.addWidget(scherm)
        self.stack.setCurrentWidget(scherm)

    def on_typedienst_clicked(self) -> None:
        """Open typetabel beheer scherm"""
        if not self.current_user:
            return

        from gui.screens.typetabel_beheer_screen import TypetabelBeheerScreen
        scherm = TypetabelBeheerScreen(self.terug)
        self.stack.addWidget(scherm)
        self.stack.setCurrentWidget(scherm)

    def on_voorkeuren_clicked(self) -> None:
        """Open voorkeuren scherm (TODO)"""
        if self.current_user:
            print(f"Voorkeuren clicked - User: {self.current_user['naam']}")
        # TODO: Implementeer

    # Handlers voor Instellingen tab
    def on_hr_regels_clicked(self) -> None:
        """Open HR regels beheer scherm"""
        from gui.screens.hr_regels_beheer_screen import HRRegelsBeheerScreen
        scherm = HRRegelsBeheerScreen(self.terug)
        self.stack.addWidget(scherm)
        self.stack.setCurrentWidget(scherm)

    def on_shift_codes_clicked(self) -> None:
        """Open shift codes & posten scherm"""
        if not self.current_user:
            return

        from gui.screens.shift_codes_screen import ShiftCodesScreen
        scherm = ShiftCodesScreen(self.terug)
        self.stack.addWidget(scherm)
        self.stack.setCurrentWidget(scherm)

    def on_feestdagen_clicked(self) -> None:
        """Feestdagen scherm openen"""
        # FeestdagenScherm roept router.terug() aan
        # Geef een object door met een terug attribute
        from types import SimpleNamespace
        router = SimpleNamespace(terug=self.terug)
        feestdagen_scherm = FeestdagenScherm(self, router)  # type: ignore[arg-type]
        self.stack.addWidget(feestdagen_scherm)
        self.stack.setCurrentWidget(feestdagen_scherm)

    def on_rode_lijnen_clicked(self) -> None:
        """Open rode lijnen beheer scherm"""
        if not self.current_user:
            return

        from gui.screens.rode_lijnen_beheer_screen import RodeLijnenBeheerScreen
        scherm = RodeLijnenBeheerScreen(self.terug)
        self.stack.addWidget(scherm)
        self.stack.setCurrentWidget(scherm)

    def on_logout(self) -> None:
        """Uitloggen"""
        self.current_user = None
        # Verwijder alle widgets behalve login
        while self.stack.count() > 1:
            widget = self.stack.widget(1)
            if widget:
                self.stack.removeWidget(widget)
                widget.deleteLater()

        if self.login_screen:
            self.stack.setCurrentWidget(self.login_screen)
            self.showNormal()  # Haal uit maximized state
            self.resize(1000, 700)  # Terug naar normale grootte bij logout

            # Centreer het window
            screen = self.screen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)

    def on_planning_clicked(self) -> None:
        """Planning scherm openen - Mijn Planning voor teamleden"""
        if not self.current_user:
            return

        from types import SimpleNamespace
        router = SimpleNamespace(terug=self.terug)
        scherm = MijnPlanningScreen(router, self.current_user['id'])  # type: ignore[arg-type]
        self.stack.addWidget(scherm)
        self.stack.setCurrentWidget(scherm)

    def on_verlof_clicked(self) -> None:
        """Verlof scherm openen (nog niet gebouwd)"""
        if self.current_user:
            print(f"Verlof clicked - Rol: {self.current_user['rol']}")
        # TODO: Implementeer verlof scherm

    def on_planning_editor_clicked(self) -> None:
        """Open planning editor scherm"""
        if not self.current_user:
            return

        from gui.screens.planning_editor_screen import PlanningEditorScreen
        scherm = PlanningEditorScreen(self.terug)
        self.stack.addWidget(scherm)
        self.stack.setCurrentWidget(scherm)

    def on_verlof_aanvragen_clicked(self) -> None:
        """Open verlof aanvragen scherm"""
        if not self.current_user:
            return

        from gui.screens.verlof_aanvragen_screen import VerlofAanvragenScreen
        scherm = VerlofAanvragenScreen(self.terug, self.current_user['id'])
        self.stack.addWidget(scherm)
        self.stack.setCurrentWidget(scherm)

    def on_verlof_goedkeuring_clicked(self) -> None:
        """Open verlof goedkeuring scherm"""
        if not self.current_user:
            return

        from gui.screens.verlof_goedkeuring_screen import VerlofGoedkeuringScreen
        scherm = VerlofGoedkeuringScreen(self.terug, self.current_user['id'])
        self.stack.addWidget(scherm)
        self.stack.setCurrentWidget(scherm)

    def show_handleiding(self) -> None:
        """Toon handleiding dialog (F1)"""
        from gui.dialogs.handleiding_dialog import HandleidingDialog
        dialog = HandleidingDialog(self)
        dialog.exec()


def main() -> None:
    """Main entry point"""
    # Initialiseer database
    init_database()

    # Start app
    app = QApplication(sys.argv)

    # Globale stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background-color: white;
        }
        QWidget {
            font-family: Arial, sans-serif;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()