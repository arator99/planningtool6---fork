"""
Automatisch gegenereerd architectuuroverzicht

Projectstructuur:
------------------

root/
    - architectuur.py

    - config.py
        Beschrijving: config.py

    - database_migration.py
        Beschrijving: Database migratie script Voegt UUID en timestamp kolommen toe aan bestaande database Run dit script één keer om je database te upgraden
        Imports:
            import sqlite3
            import uuid
            from pathlib import Path
            from datetime import datetime
        Functies:
            migrate_database()

    - Feestdagen_migration.py
        Beschrijving: UPDATE feestdagen              SET jaar = CAST(substr(datum, 1, 4) AS INTEGER)
        Imports:
            import sqlite3
            from pathlib import Path
        Functies:
            migrate_feestdagen()

    - main.py
        Beschrijving: Main entry point voor Planning Tool FIXED: Signal namen + type hints + instance attributes
        Imports:
            import sys
            from typing import Dict, Any, Optional
            from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
            from database.connection import init_database
            from gui.screens.login_screen import LoginScreen
            from gui.screens.dashboard_screen import DashboardScreen
            from gui.screens.feestdagen_screen import FeestdagenScherm
            from gui.screens.gebruikersbeheer_screen import GebruikersbeheerScreen
            from types import SimpleNamespace
        Klassen & Methodes:
            class MainWindow:
                __init__(self)

database/
    - connection.py
        Beschrijving: Database connectie en initialisatie voor Planning Tool UPDATED: Met UUID en timestamp ondersteuning
        Imports:
            import sqlite3
            import os
            from pathlib import Path
            import bcrypt
            from datetime import datetime, timedelta
            import uuid
        Functies:
            get_connection()
            init_database()
            create_tables(cursor)
            seed_data(conn, cursor)
            seed_admin_user(cursor)
            seed_interventie_post(cursor)
            seed_speciale_codes(cursor)
            seed_hr_regels(cursor)
            seed_typetabel(cursor)
            seed_rode_lijnen(cursor)

    - __init__.py

gui/
    - styles.py
        Beschrijving: Centrale styling configuratie voor Planning Tool UPDATED: Uniforme button styling (zelfde padding, font-size, height voor alle button types) Gebruik: from gui.styles import Styles, Colors, Fonts
        Klassen & Methodes:
            class Colors:
            class Fonts:
            class Dimensions:
            class Styles:
                button_primary(height=None)
                button_success(height=None)
                button_warning(height=None)
                button_danger(height=None)
                button_secondary(height=None)
                button_large_action(bg_color, hover_color)
                input_field()
                table_widget()
                info_box(bg_color="#e7f3ff", border_color="#b3d9ff", text_color="#004085")
                menu_button()
            class TableConfig:
                setup_table_widget(table, row_height=None)

    - __init__.py

gui\dialogs/
    - about_dialog.py
        Beschrijving: About Dialog voor Planning Tool Toont versie info, roadmap en credits Laadt project info uit PROJECT_INFO.md
        Imports:
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from gui.styles import Styles, Colors, Fonts, Dimensions
            from pathlib import Path
            import re
        Functies:
            load_project_info()
            parse_roadmap_sections(markdown_text)
        Klassen & Methodes:
            class AboutDialog:
                __init__(self, parent=None)
                init_ui(self)
                create_over_tab(self)
                create_roadmap_tab(self)
                create_credits_tab(self)

gui\screens/
    - dashboard_screen.py
        Beschrijving: Dashboard scherm voor Planning Tool FIXED: Instance attributes in __init__ + PyCharm type hints
        Imports:
            from typing import Dict, Any
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt, pyqtSignal
            from PyQt6.QtGui import QFont
            from gui.styles import Styles, Colors, Fonts, Dimensions
            from gui.dialogs.about_dialog import AboutDialog
        Klassen & Methodes:
            class DashboardScreen:
                __init__(self, user_data: Dict[str, Any])

    - feestdagen_screen.py
        Beschrijving: Feestdagen beheer scherm - Verbeterde versie Automatische generatie met Paasberekening FIXED: Instance attributes + QDialogButtonBox type hints
        Imports:
            from typing import Tuple, Optional, Callable
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt, QDate
            from PyQt6.QtGui import QFont
            from datetime import datetime
            from database.connection import get_connection
            from services.data_ensure_service import ensure_jaar_data
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
        Klassen & Methodes:
            class FeestdagenScherm:
                __init__(self, master: QWidget, router: Callable)
                genereer_bewerk_callback(self, datum, naam)
                callback()
                genereer_verwijder_callback(self, datum)
                callback()
            class DatumBewerkDialog:
                __init__(self, naam: str, oude_datum: str, jaar: int, parent: Optional[QWidget] = None)
            class FeestdagToevoegenDialog:
                __init__(self, jaar: int, parent: Optional[QWidget] = None)

    - gebruikersbeheer_screen.py
        Beschrijving: Gebruikersbeheer scherm voor Planning Tool Toevoegen, bewerken en beheren van teamleden FIXED: Instance attributes + exception handling + type hints
        Imports:
            from typing import List, Dict, Any, Optional, Callable
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
            import bcrypt
            import uuid
            import re
            import sqlite3
            from datetime import datetime
        Klassen & Methodes:
            class GebruikersbeheerScreen:
                __init__(self, router: Callable)
            class GebruikerDialog:
                __init__(self, parent: Optional[QWidget] = None, gebruiker: Optional[Dict[str, Any]] = None)

    - login_screen.py
        Beschrijving: Login scherm voor Planning Tool FIXED: Instance attributes + pyqtSignal + type hints
        Imports:
            from typing import Dict, Any
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
            from PyQt6.QtCore import Qt, pyqtSignal
            from PyQt6.QtGui import QFont
            import bcrypt
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions
        Klassen & Methodes:
            class LoginScreen:
                __init__(self)

    - __init__.py

models/
    - __init__.py

services/
    - data_ensure_service.py
        Beschrijving: Auto-generatie service voor ontbrekende data
        Imports:
            from datetime import datetime, timedelta
            from database.connection import get_connection
        Functies:
            bereken_pasen(jaar)
            ensure_jaar_data(jaar)
            feestdagen_bestaan(jaar)
            genereer_feestdagen_template(jaar)
            rode_lijnen_bestaan_tot(datum)
            extend_rode_lijnen_tot(doel_datum)

    - __init__.py

Beschrijving:
-------------
Voeg hier handmatig uitleg toe over modules, datastromen, en verantwoordelijkheden.
"""
