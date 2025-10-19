"""
Automatisch gegenereerd architectuuroverzicht

Projectstructuur:
------------------

root/
    - architectuur.py

    - config.py
        Beschrijving: config.py

    - create_planning_table.py
        Beschrijving: Maak planning tabel aan (tijdelijk, tot Planning Editor gemaakt is)
        Imports:
            import sqlite3
            from pathlib import Path

    - database_migration.py
        Beschrijving: Database migratie script Voegt UUID en timestamp kolommen toe aan bestaande database Run dit script één keer om je database te upgraden
        Imports:
            import sqlite3
            import uuid
            from pathlib import Path
            from datetime import datetime
        Functies:
            migrate_database()

    - database_shift_codes_migration.py
        Beschrijving: Database migratie voor Shift Codes systeem FIXED: Herstructureer shift_codes tabel als schema niet klopt
        Imports:
            import sqlite3
            from pathlib import Path
        Functies:
            migrate_shift_codes()

    - Feestdagen_migration.py
        Beschrijving: Database migratie: Voeg is_variabel kolom toe aan feestdagen tabel Run dit script één keer om je database te upgraden
        Imports:
            import sqlite3
            from pathlib import Path
        Functies:
            migrate_feestdagen_type()

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
            from gui.screens.kalender_test_screen import KalenderTestScreen
            from gui.screens.mijn_planning_screen import MijnPlanningScreen
            from gui.screens.shift_codes_screen import ShiftCodesScreen
            from types import SimpleNamespace
            from types import SimpleNamespace
            from types import SimpleNamespace
            from gui.screens.planning_editor_screen import PlanningEditorScreen
            from gui.screens.verlof_aanvragen_screen import VerlofAanvragenScreen
            from gui.screens.verlof_goedkeuring_screen import VerlofGoedkeuringScreen
        Klassen & Methodes:
            class MainWindow:
                __init__(self)

    - test_migratie.py
        Beschrijving: test_migratie.py
        Imports:
            from pathlib import Path
            import sqlite3

    - verify_planning_editor_readiness.py
        Beschrijving: Verificatie script: Check of alles klaar is voor Planning Editor
        Imports:
            import sqlite3
            from pathlib import Path
            from datetime import datetime

database/
    - connection.py
        Beschrijving: Database connectie en initialisatie voor Planning Tool UPDATED: v0.6.4+ structuur met werkposten en simpele planning tabel
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
            seed_interventie_werkpost(cursor)
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

    - shift_codes_grid_dialog.py
        Beschrijving: Shift Codes Grid Dialog Grid editor voor shift codes van een werkpost
        Imports:
            from typing import Dict, Any, Optional
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions
            import sqlite3
        Klassen & Methodes:
            class ShiftCodesGridDialog:
                __init__(self, parent, werkpost_id: int, werkpost_naam: str)
                init_ui(self)
                setup_grid(self)
                load_data(self)
                save_data(self)

    - speciale_code_dialog.py
        Beschrijving: Speciale Code Dialog Voor toevoegen/bewerken van globale speciale codes
        Imports:
            from typing import Dict, Any, Optional
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from gui.styles import Styles, Colors, Fonts, Dimensions
        Klassen & Methodes:
            class SpecialeCodeDialog:
                __init__(self, parent, code: Optional[Dict[str, Any]] = None)
                init_ui(self)
                on_code_changed(self, text: str)
                valideer_en_accept(self)

    - werkpost_naam_dialog.py
        Beschrijving: Werkpost Naam Dialog Simpele dialog voor naam en beschrijving werkpost
        Imports:
            from typing import Dict, Any, Optional
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtGui import QFont
            from gui.styles import Styles, Colors, Fonts, Dimensions
        Klassen & Methodes:
            class WerkpostNaamDialog:
                __init__(self, parent, werkpost: Optional[Dict[str, Any]] = None)
                init_ui(self)
                valideer_en_accept(self)

gui\screens/
    - dashboard_screen.py
        Beschrijving: Dashboard scherm voor Planning Tool FIXED: Instance attributes in __init__ + PyCharm type hints UPDATED: Teamleden kunnen wachtwoord wijzigen + Feestdagen alleen voor planners
        Imports:
            from typing import Dict, Any
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt, pyqtSignal
            from PyQt6.QtGui import QFont
            from gui.styles import Styles, Colors, Fonts, Dimensions
            from gui.dialogs.about_dialog import AboutDialog
            import bcrypt
            from database.connection import get_connection
            import sqlite3
        Klassen & Methodes:
            class DashboardScreen:
                __init__(self, user_data: Dict[str, Any])
                mousePressEvent(event)
            class WachtwoordWijzigenDialog:
                __init__(self, parent: QWidget, user_data: Dict[str, Any])

    - feestdagen_screen.py
        Beschrijving: Feestdagen beheer scherm - Verbeterde versie Automatische generatie met Paasberekening FIXED: Aangepast aan werkelijk database schema (datum, naam, is_zondagsrust)
        Imports:
            from typing import Tuple, Optional, Callable
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt, QDate
            from PyQt6.QtGui import QFont
            from datetime import datetime
            from database.connection import get_connection
            from services.data_ensure_service import ensure_jaar_data
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
            import traceback
            import traceback
            import traceback
        Klassen & Methodes:
            class FeestdagenScherm:
                __init__(self, master: QWidget, router: Callable)
                genereer_bewerk_callback(self, datum: str, naam: str)
                callback()
                genereer_verwijder_callback(self, datum: str)
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
                genereer_bewerk_callback(self, gebruiker: Dict[str, Any])
                callback()
                genereer_toggle_callback(self, gebruiker: Dict[str, Any])
                callback()
            class GebruikerDialog:
                __init__(self, parent: Optional[QWidget] = None, gebruiker: Optional[Dict[str, Any]] = None)

    - kalender_test_screen.py
        Beschrijving: Kalender Test Scherm - DEBUG VERSION Voor het testen van beide grid kalender widgets
        Imports:
            from typing import Callable
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from datetime import datetime
            from gui.styles import Styles, Colors, Fonts, Dimensions
            import traceback
            from gui.widgets.grid_kalender_base import GridKalenderBase
            import traceback
            from PyQt6.QtWidgets import QGridLayout, QDialog
            import traceback
            from gui.widgets import TeamlidGridKalender
            from PyQt6.QtWidgets import QDialog
            import traceback
            from gui.widgets import PlannerGridKalender
            from PyQt6.QtWidgets import QDialog
            import traceback
        Klassen & Methodes:
            class KalenderTestScreen:
                __init__(self, router: Callable, gebruiker_id: int = 1)

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

    - mijn_planning_screen.py
        Beschrijving: Mijn Planning Scherm Teamleden bekijken hun eigen rooster en kunnen collega's filteren
        Imports:
            from typing import Callable
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from datetime import datetime
            from gui.styles import Styles, Colors, Fonts, Dimensions
            from gui.widgets import TeamlidGridKalender
        Klassen & Methodes:
            class MijnPlanningScreen:
                __init__(self, router: Callable, gebruiker_id: int)

    - planning_editor_screen.py
        Beschrijving: Planning Editor Scherm Gebruikt PlannerGridKalender widget met codes sidebar en toolbar
        Imports:
            from typing import Callable, Set, Dict, Any, List
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from gui.widgets.planner_grid_kalender import PlannerGridKalender
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
            from database.connection import get_connection
            from datetime import datetime
        Klassen & Methodes:
            class PlanningEditorScreen:
                __init__(self, router: Callable)
                load_valid_codes(self)
                eventFilter(self, obj, event)
                toon_codes_helper(self)
                populate_codes_help_table(self)
                filter_codes_table(self, search_text: str)

    - shift_codes_screen.py
        Beschrijving: Shift Codes Beheer Scherm Geïntegreerd scherm met speciale codes en werkposten
        Imports:
            from typing import List, Dict, Any, Callable
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
            from gui.dialogs.speciale_code_dialog import SpecialeCodeDialog
            from gui.dialogs.werkpost_naam_dialog import WerkpostNaamDialog
            from gui.dialogs.shift_codes_grid_dialog import ShiftCodesGridDialog
            import sqlite3
        Klassen & Methodes:
            class ShiftCodesScreen:
                __init__(self, router: Callable)
                init_ui(self)
                load_data(self)
                load_speciale_codes(self)
                display_speciale_codes(self)
                load_werkposten(self)
                display_werkposten(self)
                nieuwe_speciale_code(self)
                create_bewerk_code_callback(self, code: Dict[str, Any])
                callback()
                bewerk_speciale_code(self, code: Dict[str, Any])
                create_verwijder_code_callback(self, code: Dict[str, Any])
                callback()
                verwijder_speciale_code(self, code: Dict[str, Any])
                save_speciale_code(self, data: Dict[str, Any])
                update_speciale_code(self, code_id: int, data: Dict[str, Any])
                nieuwe_werkpost(self)
                create_bewerk_werkpost_callback(self, werkpost: Dict[str, Any])
                callback()
                bewerk_werkpost(self, werkpost: Dict[str, Any])
                create_toggle_werkpost_callback(self, werkpost: Dict[str, Any])
                callback()
                toggle_werkpost(self, werkpost: Dict[str, Any])

    - verlof_aanvragen_screen.py
        Beschrijving: Verlof Aanvragen Scherm Teamleden kunnen verlof aanvragen en hun aanvragen bekijken
        Imports:
            from typing import Callable, List, Dict, Any
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt, QDate
            from PyQt6.QtGui import QFont
            from datetime import datetime, timedelta
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
            import sqlite3
        Klassen & Methodes:
            class VerlofAanvragenScreen:
                __init__(self, router: Callable, gebruiker_id: int)

    - verlof_goedkeuring_screen.py
        Beschrijving: Verlof Goedkeuring Scherm Planners kunnen verlofaanvragen goedkeuren of weigeren
        Imports:
            from typing import Callable, List, Dict, Any
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from datetime import datetime, timedelta
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
            import sqlite3
        Klassen & Methodes:
            class VerlofGoedkeuringScreen:
                __init__(self, router: Callable, planner_id: int)
            class WeigeringRedenDialog:
                __init__(self, parent: QWidget, naam: str)

    - __init__.py

gui\widgets/
    - grid_kalender_base.py
        Beschrijving: Grid Kalender Base Class Gemeenschappelijke functionaliteit voor planner en teamlid kalenders UPDATED: Database compatibiliteit met nieuwe planning tabel structuur
        Imports:
            from typing import Dict, Any, List, Optional, Tuple
            from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
            from PyQt6.QtCore import Qt, QDate
            from PyQt6.QtGui import QFont
            from datetime import datetime, timedelta
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions
            import calendar
        Klassen & Methodes:
            class GridKalenderBase:
                __init__(self, jaar: int, maand: int)

    - planner_grid_kalender.py
        Beschrijving: Planner Grid Kalender Editable kalender voor planners met buffer dagen en scroll functionaliteit UPDATED: Editable cellen met keyboard navigatie en save functionaliteit
        Imports:
            from typing import Dict, Any, List, Optional, Callable, Set
            from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
            from PyQt6.QtCore import Qt, pyqtSignal
            from PyQt6.QtGui import QFont, QCursor
            from gui.widgets.grid_kalender_base import GridKalenderBase
            from gui.styles import Styles, Colors, Fonts, Dimensions
            from datetime import datetime, timedelta
            from database.connection import get_connection
            import sqlite3
            from gui.widgets.teamlid_grid_kalender import FilterDialog
        Klassen & Methodes:
            class EditableLabel:
                __init__(self, text: str, datum_str: str, gebruiker_id: int, parent_grid)
                mousePressEvent(self, event)
                start_edit(self)
                to_upper()
                finish_edit(self)
                eventFilter(self, obj, event)
            class PlannerGridKalender:
                __init__(self, jaar: int, maand: int)
                set_valid_codes(self, codes: Set[str], codes_per_dag: Dict[str, Set[str]], speciale: Set[str])
                on_cel_edited(self, datum_str: str, gebruiker_id: int, code: str)
                save_shift(self, datum_str: str, gebruiker_id: int, shift_code: str)
                delete_shift(self, datum_str: str, gebruiker_id: int)
                navigate_to_cell(self, huidige_datum: str, huidige_gebruiker_id: int, richting: str)
                show_context_menu(self, cel: EditableLabel, datum_str: str, gebruiker_id: int)
                vul_week(self, start_datum: str, gebruiker_id: int, code: str)

    - teamlid_grid_kalender.py
        Beschrijving: Teamlid Grid Kalender Read-only kalender voor teamleden om eigen/collega shifts te bekijken
        Imports:
            from typing import Dict, Any, List, Optional
            from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from gui.widgets.grid_kalender_base import GridKalenderBase
            from gui.styles import Styles, Colors, Fonts, Dimensions
            from datetime import datetime
        Klassen & Methodes:
            class TeamlidGridKalender:
                __init__(self, jaar: int, maand: int, huidige_gebruiker_id: int)
            class FilterDialog:

    - __init__.py
        Beschrijving: GUI Widgets Package Herbruikbare widgets voor de planning tool
        Imports:
            from gui.widgets.grid_kalender_base import GridKalenderBase
            from gui.widgets.planner_grid_kalender import PlannerGridKalender
            from gui.widgets.teamlid_grid_kalender import TeamlidGridKalender

models/
    - __init__.py

services/
    - data_ensure_service.py
        Beschrijving: Auto-generatie service voor ontbrekende data Lazy initialization pattern: genereer alleen wat nodig is, wanneer het nodig is
        Imports:
            from datetime import datetime, timedelta
            from database.connection import get_connection
        Functies:
            bereken_pasen(jaar)
            ensure_jaar_data(jaar)
            ensure_rode_lijnen_tot(datum)
            feestdagen_bestaan(jaar)
            genereer_feestdagen_template(jaar)
            rode_lijnen_bestaan_tot(datum)
            extend_rode_lijnen_tot(doel_datum)

    - __init__.py

Beschrijving:
-------------
Voeg hier handmatig uitleg toe over modules, datastromen, en verantwoordelijkheden.
"""
