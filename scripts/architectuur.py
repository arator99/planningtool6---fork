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

    - detect_db_version.py
        Beschrijving: Database Versie Detectie Tool  Analyseert een database en bepaalt welke versie het waarschijnlijk is op basis van aanwezige tabellen en kolommen.  Gebruik:     python detect_db_version.py     python detect_db_version.py path/to/database.db  Auteur: Planning Tool Team Datum: 21 Oktober 2025
        Imports:
            import sqlite3
            import sys
            from pathlib import Path
            from datetime import datetime
        Functies:
            get_table_columns(cursor, table_name)
            get_all_tables(cursor)
            detect_version(db_path)
            main()

    - Feestdagen_migration.py
        Beschrijving: Database migratie: Voeg is_variabel kolom toe aan feestdagen tabel Run dit script één keer om je database te upgraden
        Imports:
            import sqlite3
            from pathlib import Path
        Functies:
            migrate_feestdagen_type()

    - main.py
        Beschrijving: Main entry point voor Planning Tool FIXED: Signal namen + type hints + instance attributes UPDATED: Dark mode support met theme toggle (v0.6.12: per gebruiker)
        Imports:
            import sys
            from typing import Dict, Any, Optional
            from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
            from PyQt6.QtGui import QKeySequence, QShortcut
            from database.connection import init_database, check_db_compatibility
            from gui.screens.login_screen import LoginScreen
            from gui.screens.dashboard_screen import DashboardScreen
            from gui.screens.feestdagen_screen import FeestdagenScherm
            from gui.screens.gebruikersbeheer_screen import GebruikersbeheerScreen
            from gui.screens.mijn_planning_screen import MijnPlanningScreen
            from gui.styles import ThemeManager, Colors
            from gui.screens.typetabel_beheer_screen import TypetabelBeheerScreen
            from gui.screens.voorkeuren_screen import VoorkeurenScreen
            from gui.screens.hr_regels_beheer_screen import HRRegelsBeheerScreen
            from gui.screens.shift_codes_screen import ShiftCodesScreen
            from types import SimpleNamespace
            from gui.screens.rode_lijnen_beheer_screen import RodeLijnenBeheerScreen
            from gui.screens.verlof_saldo_beheer_screen import VerlofSaldoBeheerScreen
            from gui.screens.werkpost_koppeling_screen import WerkpostKoppelingScreen
            from types import SimpleNamespace
            from gui.screens.planning_editor_screen import PlanningEditorScreen
            from gui.screens.verlof_aanvragen_screen import VerlofAanvragenScreen
            from gui.screens.verlof_goedkeuring_screen import VerlofGoedkeuringScreen
            from gui.dialogs.handleiding_dialog import HandleidingDialog
            from database.connection import get_connection
            from database.connection import get_connection
            from config import APP_VERSION
        Klassen & Methodes:
            class MainWindow:
                __init__(self)

    - migrate_v0_6_4_to_v0_6_13.py
        Beschrijving: Cumulatieve Database Migratie: v0.6.4/0.6.5 -> v0.6.13  Dit script voert ALLE tussenliggende migraties uit: - v0.6.5 -> v0.6.6: Typetabel versioned systeem - v0.6.6 -> v0.6.7: Term-based speciale codes - v0.6.7 -> v0.6.8: Rode lijnen config (OPTIONEEL - alleen structuur) - v0.6.8 -> v0.6.10: Verlof saldo systeem - v0.6.10 -> v0.6.11: Shift voorkeuren - v0.6.11 -> v0.6.12: Theme voorkeur - v0.6.12 -> v0.6.13: Database versie tracking  BELANGRIJK: Maak ALTIJD een backup voor je dit script draait!  Gebruik:     python migrate_v0_6_4_to_v0_6_13.py     python migrate_v0_6_4_to_v0_6_13.py path/to/database.db  Auteur: Planning Tool Team Datum: 21 Oktober 2025
        Imports:
            import sqlite3
            import sys
            from pathlib import Path
            from datetime import datetime
        Functies:
            get_table_columns(cursor, table_name)
            table_exists(cursor, table_name)
            migrate_to_v0_6_6(conn, cursor)
            migrate_to_v0_6_7(conn, cursor)
            migrate_to_v0_6_8(conn, cursor)
            migrate_to_v0_6_10(conn, cursor)
            migrate_to_v0_6_11(conn, cursor)
            migrate_to_v0_6_12(conn, cursor)
            migrate_to_v0_6_13(conn, cursor)
            main()

    - migratie_gebruiker_werkposten.py
        Beschrijving: Database Migratie: Gebruiker Werkposten Koppeling Versie: 0.6.13 -> 0.6.14  Voegt gebruiker_werkposten tabel toe voor many-to-many relatie tussen gebruikers en werkposten. Dit zorgt voor slimme auto-generatie van planning waarbij de juiste shift code wordt gebruikt op basis van gebruiker's werkpost.  VEILIG: Idempotent - kan meerdere keren worden uitgevoerd
        Imports:
            import sqlite3
            import sys
            from pathlib import Path
        Functies:
            main()

    - migratie_hr_regels_versioning.py
        Beschrijving: Database Migratie - HR Regels Versioning Voegt actief_tot en is_actief kolommen toe voor historiek bijhouden  ACHTERGROND: - HR regels kunnen wijzigen over tijd (bijv. 12u rust → 10u rust vanaf 1 mei) - Planning van voor de wijziging moet gevalideerd worden met oude regels - Planning van na de wijziging moet gevalideerd worden met nieuwe regels - Datum-specifieke historiek nodig voor correcte validatie  WIJZIGINGEN: - actief_tot kolom (TIMESTAMP, nullable) - wanneer regel vervangen wordt - is_actief kolom (BOOLEAN) - huidige actieve regel per naam
        Imports:
            import sqlite3
            from pathlib import Path
        Functies:
            migratie_hr_regels_versioning()

    - migratie_rode_lijnen_config.py
        Beschrijving: Database Migratie - Rode Lijnen Config Voegt rode_lijnen_config tabel toe voor configureerbare HR cycli  ACHTERGROND: - Rode lijnen worden gebruikt voor HR validatie (max werkdagen per cyclus) - Momenteel hardcoded interval van 28 dagen vanaf 28 juli 2024 - Moet configureerbaar worden met historiek voor wijzigingen - Validator moet juiste config gebruiken op basis van planning datum  WIJZIGINGEN: - Nieuwe tabel rode_lijnen_config met versioning (actief_vanaf, actief_tot, is_actief) - Start met default config (2024-07-28, 28 dagen interval) - Services moeten config raadplegen ipv hardcoded waardes
        Imports:
            import sqlite3
            from pathlib import Path
        Functies:
            migratie_rode_lijnen_config()

    - migratie_shift_voorkeuren.py
        Beschrijving: Database migratie script voor shift voorkeuren systeem v0.6.10 -> v0.6.11  Voegt shift_voorkeuren kolom toe aan gebruikers tabel Format: JSON string met prioriteit mapping Voorbeeld: {"1": "vroeg", "2": "typetabel", "3": "laat", "4": "nacht"}
        Imports:
            import sqlite3
            from pathlib import Path
        Functies:
            migreer_shift_voorkeuren()

    - migratie_systeem_termen.py
        Beschrijving: Database Migratie v0.6.6 → v0.6.7 - Systeem Termen Voegt term kolom toe aan speciale_codes tabel en markeert verplichte systeemcodes  ACHTERGROND: - Voorheen waren codes hardcoded (VV voor verlof, RX voor zondagrust, etc.) - Nu werken we met termen die flexibele codes kunnen hebben - Teams kunnen codes aanpassen (VV → VL), maar termen blijven beschermd  VERPLICHTE TERMEN: 1. verlof (standaard: VV) 2. zondagrust (standaard: RX) 3. zaterdagrust (standaard: CX) 4. ziek (standaard: Z) 5. arbeidsduurverkorting (standaard: DA)
        Imports:
            import sqlite3
            from pathlib import Path
        Functies:
            migratie_systeem_termen()

    - migratie_theme_per_gebruiker.py
        Beschrijving: Database migratie script voor theme voorkeur per gebruiker v0.6.11 -> v0.6.12  Voegt theme_voorkeur kolom toe aan gebruikers tabel Migreert bestaande globale theme voorkeur (indien aanwezig)
        Imports:
            import sqlite3
            import json
            from pathlib import Path
        Functies:
            migreer_theme_per_gebruiker()

    - migratie_typetabel_versioned.py
        Beschrijving: Database migratie: Typetabel naar Versioned Systeem Migreert oude typetabel naar nieuwe versioned structuur met concept/actief/archief status  Run dit script één keer om je database te upgraden naar v0.7.0
        Imports:
            import sqlite3
            from pathlib import Path
            from datetime import datetime
        Functies:
            migrate_typetabel_to_versioned()

    - migratie_verlof_saldo.py
        Beschrijving: Database Migratie Script - Verlof & KD Saldo Systeem Versie: 0.6.9 -> 0.6.10  Wijzigingen: 1. Nieuwe tabel: verlof_saldo (jaarlijks contingent + overdracht tracking) 2. Nieuwe speciale code: KD (Kompensatiedag) met term 'kompensatiedag' 3. Nieuwe kolom: verlof_aanvragen.toegekende_code_term (VV of KD bij goedkeuring) 4. HR regel: Max KD overdracht (35 dagen) 5. HR regel: Verlof vervaldatum (1 mei)  Run dit script VOOR het opstarten van de applicatie na update naar v0.6.10
        Imports:
            import sqlite3
            from datetime import datetime
            from pathlib import Path
        Functies:
            get_database_path()
            migrate()

    - test_migratie.py
        Beschrijving: test_migratie.py
        Imports:
            from pathlib import Path
            import sqlite3

    - upgrade_to_v0_6_13.py
        Beschrijving: Database Upgrade: v0.6.12 → v0.6.13 Doel: Toevoegen db_metadata tabel voor versie tracking  Gebruik:     python upgrade_to_v0_6_13.py  Dit script: 1. Controleert of db_metadata tabel al bestaat 2. Maakt tabel aan indien nodig 3. Initialiseert versienummer op 0.6.12 (laatste DB schema wijziging voor v0.6.13) 4. Idempotent: kan meerdere keren uitgevoerd worden zonder problemen  Auteur: Planning Tool Team Datum: 21 Oktober 2025
        Imports:
            import sqlite3
            from pathlib import Path
            from config import MIN_DB_VERSION
        Functies:
            upgrade_database()

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
            from config import MIN_DB_VERSION, APP_VERSION
            from config import MIN_DB_VERSION
        Functies:
            get_connection()
            get_db_version()
            check_db_compatibility()
            init_database()
            create_tables(cursor)
            seed_data(conn, cursor)
            seed_db_version(cursor)
            seed_admin_user(cursor)
            seed_interventie_werkpost(cursor)
            seed_speciale_codes(cursor)
            seed_hr_regels(cursor)
            seed_typetabel(cursor)
            seed_rode_lijnen(cursor)
            seed_rode_lijnen_config(cursor)

    - __init__.py

gui/
    - styles.py
        Beschrijving: Centrale styling configuratie voor Planning Tool UPDATED: Dark mode ondersteuning met ThemeManager Gebruik: from gui.styles import Styles, Colors, Fonts, ThemeManager
        Imports:
            from typing import Optional
        Klassen & Methodes:
            class ThemeManager:
                __new__(cls)
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
            from database.connection import get_db_version
            from config import APP_VERSION
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

    - auto_generatie_dialog.py
        Beschrijving: Auto-Generatie Dialog Dialog voor het genereren van planning uit actieve typetabel
        Imports:
            from typing import Dict, Any, Optional, List, Set
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import QDate, Qt
            from PyQt6.QtGui import QFont
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions
            from datetime import datetime, timedelta
            import sqlite3
        Klassen & Methodes:
            class AutoGeneratieDialog:
                __init__(self, parent, current_year: int, current_month: int)
                init_ui(self)
                load_data(self)
                on_datum_changed(self)
                update_preview(self)
                check_bestaande_data(self, start_date, eind_date)
                genereer(self)

    - handleiding_dialog.py
        Beschrijving: Handleiding Dialog Toont gebruikershandleiding voor Planning Tool
        Imports:
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextBrowser, QPushButton,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from gui.styles import Styles, Colors, Fonts, Dimensions
            import markdown
        Klassen & Methodes:
            class HandleidingDialog:
                __init__(self, parent)
                init_ui(self)

    - hr_regel_edit_dialog.py
        Beschrijving: HR Regel Edit Dialog Voor het wijzigen van HR regels met nieuwe versie + datum
        Imports:
            from typing import Dict, Any
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt, QDate
            from PyQt6.QtGui import QFont
            from datetime import datetime
            from gui.styles import Styles, Colors, Fonts, Dimensions
        Klassen & Methodes:
            class HRRegelEditDialog:
                __init__(self, parent, regel: Dict[str, Any])
                init_ui(self)
                valideer_en_accept(self)

    - rode_lijnen_config_dialog.py
        Beschrijving: Rode Lijnen Config Dialog Voor het wijzigen van rode lijnen configuratie met nieuwe versie + datum
        Imports:
            from typing import Dict, Any
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt, QDate
            from PyQt6.QtGui import QFont
            from datetime import datetime
            from gui.styles import Styles, Colors, Fonts, Dimensions
        Klassen & Methodes:
            class RodeLijnenConfigDialog:
                __init__(self, parent, config: Dict[str, Any])
                init_ui(self)
                valideer_en_accept(self)

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

    - typetabel_dialogs.py
        Beschrijving: Typetabel Dialogs Dialogs voor typetabel beheer
        Imports:
            from typing import Dict, Any
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import QDate
            from PyQt6.QtGui import QFont
            from gui.styles import Styles, Fonts, Dimensions, Colors
            from datetime import datetime
        Klassen & Methodes:
            class NieuweTypetabelDialog:
                __init__(self, parent)
                init_ui(self)
                valideer_en_accept(self)
            class ActiveerTypetabelDialog:
                __init__(self, parent, versie: Dict[str, Any], heeft_actieve: bool = False)
                init_ui(self)
                update_weekdag_info(self)

    - typetabel_editor_dialog.py
        Beschrijving: Typetabel Editor Dialog Grid editor voor het bewerken van typetabel patroon
        Imports:
            from typing import Dict, Any, List, Optional
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
            from datetime import datetime
            import sqlite3
        Klassen & Methodes:
            class TypetabelEditorDialog:
                __init__(self, parent, versie: Dict[str, Any], readonly: bool = False)
                init_ui(self)
                setup_tabel(self)
                load_data(self)
                display_data(self)
                on_cel_gewijzigd(self)
                annuleren(self)
                opslaan(self)

    - verlof_saldo_bewerken_dialog.py
        Beschrijving: Verlof Saldo Bewerken Dialog Versie: 0.6.10  Dialog voor bewerken van verlof en KD saldi per gebruiker.
        Imports:
            from PyQt6.QtWidgets import (
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from gui.styles import Styles, Colors, Fonts, Dimensions
            from services.verlof_saldo_service import VerlofSaldoService
            from services.term_code_service import TermCodeService
        Klassen & Methodes:
            class VerlofSaldoBewerkenDialog:
                init_ui(self)
                opslaan(self)

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
            from gui.widgets.theme_toggle_widget import ThemeToggleWidget
            import bcrypt
            from database.connection import get_connection
            import sqlite3
            from gui.dialogs.handleiding_dialog import HandleidingDialog
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

    - hr_regels_beheer_screen.py
        Beschrijving: HR Regels Beheer Scherm Beheer van HR validatie regels met versioning support
        Imports:
            from typing import List, Dict, Any, Callable
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from datetime import datetime
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
            import sqlite3
            from gui.dialogs.hr_regel_edit_dialog import HRRegelEditDialog
        Klassen & Methodes:
            class HRRegelsBeheerScreen:
                __init__(self, router: Callable)
                init_ui(self)
                toggle_historiek(self, state)
                load_data(self)
                load_historiek(self)
                display_actieve_regels(self)
                display_historiek(self)
                create_bewerk_callback(self, regel: Dict[str, Any])
                callback()
                bewerk_regel(self, regel: Dict[str, Any])
                save_nieuwe_versie(self, oude_regel: Dict[str, Any], nieuwe_data: Dict[str, Any])

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
            from database.connection import get_connection, get_db_version
            from gui.styles import Styles, Colors, Fonts, Dimensions
            from config import APP_VERSION
        Klassen & Methodes:
            class LoginScreen:
                __init__(self)

    - mijn_planning_screen.py
        Beschrijving: Mijn Planning Scherm Teamleden bekijken hun eigen rooster en kunnen collega's filteren
        Imports:
            from typing import Callable, Set, Dict
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from datetime import datetime
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
            from gui.widgets import TeamlidGridKalender
            from database.connection import get_connection
            from PyQt6.QtWidgets import QTextEdit, QScrollArea
            from PyQt6.QtWidgets import QScrollArea, QTextEdit
        Klassen & Methodes:
            class MijnPlanningScreen:
                __init__(self, router: Callable, gebruiker_id: int)
                load_valid_codes(self)

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
            from gui.dialogs.auto_generatie_dialog import AutoGeneratieDialog
        Klassen & Methodes:
            class PlanningEditorScreen:
                __init__(self, router: Callable)
                load_valid_codes(self)
                load_maand_status(self)
                update_status_ui(self)
                toggle_status(self)
                publiceer_planning(self)
                terug_naar_concept(self)
                on_maand_changed(self)
                eventFilter(self, obj, event)
                toon_codes_helper(self)
                populate_codes_help_table(self)
                show_auto_generatie_dialog(self)
                filter_codes_table(self, search_text: str)

    - rode_lijnen_beheer_screen.py
        Beschrijving: Rode Lijnen Beheer Scherm Beheer van rode lijnen configuratie met versioning support
        Imports:
            from typing import List, Dict, Any, Callable
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from datetime import datetime
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
            import sqlite3
            from gui.dialogs.rode_lijnen_config_dialog import RodeLijnenConfigDialog
            from services.data_ensure_service import regenereer_rode_lijnen_vanaf
        Klassen & Methodes:
            class RodeLijnenBeheerScreen:
                __init__(self, router: Callable)
                init_ui(self)
                toggle_historiek(self, state)
                load_data(self)
                load_historiek(self)
                display_actieve_config(self)
                display_historiek(self)
                create_bewerk_callback(self, config: Dict[str, Any])
                callback()
                bewerk_config(self, config: Dict[str, Any])
                save_nieuwe_versie(self, oude_config: Dict[str, Any], nieuwe_data: Dict[str, Any])

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
            from services.term_code_service import TermCodeService
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

    - typetabel_beheer_screen.py
        Beschrijving: Typetabel Beheer Scherm Beheer van typetabel versies (concept/actief/archief)
        Imports:
            from typing import Callable, List, Dict, Any, Optional
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions
            from datetime import datetime
            import sqlite3
            from gui.dialogs.typetabel_dialogs import NieuweTypetabelDialog
            from gui.dialogs.typetabel_editor_dialog import TypetabelEditorDialog
            from gui.dialogs.typetabel_editor_dialog import TypetabelEditorDialog
            from gui.dialogs.typetabel_dialogs import ActiveerTypetabelDialog
        Klassen & Methodes:
            class TypetabelBeheerScreen:
                __init__(self, router: Callable)
                init_ui(self)
                load_data(self)
                display_versies(self)
                nieuwe_typetabel(self)
                kopieer_actieve(self)
                kopieer_versie(self, versie: Dict[str, Any])
                bewerk_typetabel(self, versie: Dict[str, Any])
                bekijk_typetabel(self, versie: Dict[str, Any], readonly: bool = True)
                activeer_versie(self, versie: Dict[str, Any])
                verwijder_versie(self, versie: Dict[str, Any])

    - verlof_aanvragen_screen.py
        Beschrijving: Verlof Aanvragen Scherm Teamleden kunnen verlof aanvragen en hun aanvragen bekijken
        Imports:
            from typing import Callable, List, Dict, Any
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt, QDate
            from PyQt6.QtGui import QTextCharFormat
            from PyQt6.QtGui import QFont
            from datetime import datetime, timedelta
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
            import sqlite3
            from gui.widgets.verlof_saldo_widget import VerlofSaldoWidget
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
            from services.term_code_service import TermCodeService
            import sqlite3
            from services.verlof_saldo_service import VerlofSaldoService
            from services.verlof_saldo_service import VerlofSaldoService
            from datetime import datetime
        Klassen & Methodes:
            class VerlofGoedkeuringScreen:
                __init__(self, router: Callable, planner_id: int)
            class VerlofTypeDialog:
            class WeigeringRedenDialog:
                __init__(self, parent: QWidget, naam: str)

    - verlof_saldo_beheer_screen.py
        Beschrijving: Verlof & KD Saldo Beheer Scherm Versie: 0.6.10  Admin scherm voor beheer van verlof en kompensatiedagen saldi per gebruiker.
        Imports:
            from typing import Callable
            from PyQt6.QtWidgets import (
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from datetime import datetime
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
            from services.verlof_saldo_service import VerlofSaldoService
            from services.term_code_service import TermCodeService
            from gui.dialogs.verlof_saldo_bewerken_dialog import VerlofSaldoBewerkenDialog
            from PyQt6.QtWidgets import QInputDialog
        Klassen & Methodes:
            class VerlofSaldoBeheerScreen:
                __init__(self, router: Callable)
                init_ui(self)
                on_jaar_changed(self)
                load_data(self)
                update_table(self)
                bewerken_saldo(self, gebruiker_id: int)
                nieuw_jaar_aanmaken(self)

    - voorkeuren_screen.py
        Beschrijving: Voorkeuren Screen - Shift voorkeuren instellen voor gebruikers v0.6.11  Gebruikers kunnen hun shift voorkeuren instellen in volgorde van prioriteit. Dit wordt gebruikt bij automatische planning generatie.
        Imports:
            from typing import Callable, Dict, Any, Optional
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from gui.styles import Styles, Colors, Fonts, Dimensions
            from database.connection import get_connection
            import sqlite3
            import json
        Klassen & Methodes:
            class VoorkeurenScreen:
                __init__(self, router: Callable, user_data: Dict[str, Any])

    - werkpost_koppeling_screen.py
        Beschrijving: Werkpost Koppeling Beheer Scherm Grid met gebruikers (Y-as) x werkposten (X-as) Checkboxes om aan te geven welke werkposten elke gebruiker kent
        Imports:
            from typing import Callable, List, Dict, Any
            from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            from database.connection import get_connection
            from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
            import sqlite3
        Klassen & Methodes:
            class WerkpostKoppelingScreen:
                __init__(self, router: Callable)
                init_ui(self)
                setup_table(self)
                on_filter_changed(self)
                load_data(self)
                build_grid(self)
                save_data(self)

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
            from services.term_code_service import TermCodeService
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
            from services.data_ensure_service import ensure_jaar_data
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
            from database.connection import get_connection
        Klassen & Methodes:
            class TeamlidGridKalender:
                __init__(self, jaar: int, maand: int, huidige_gebruiker_id: int)
            class FilterDialog:

    - theme_toggle_widget.py
        Beschrijving: Theme Toggle Widget Visuele switch voor dark/light mode met zon/maan iconen
        Imports:
            from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
            from PyQt6.QtCore import Qt, pyqtSignal
            from PyQt6.QtGui import QFont
            from gui.styles import Colors, Fonts, Dimensions, ThemeManager
        Klassen & Methodes:
            class ThemeToggleWidget:
                __init__(self, parent=None)
                init_ui(self)
                update_button_state(self)
                on_toggle(self)
                refresh(self)

    - verlof_saldo_widget.py
        Beschrijving: Verlof Saldo Widget Versie: 0.6.10  Read-only widget voor weergave van verlof en KD saldo (teamlid view).
        Imports:
            from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
            from PyQt6.QtGui import QFont
            from PyQt6.QtCore import Qt
            from datetime import datetime
            from gui.styles import Styles, Colors, Fonts, Dimensions
            from services.verlof_saldo_service import VerlofSaldoService
            from services.term_code_service import TermCodeService
        Klassen & Methodes:
            class VerlofSaldoWidget:
                __init__(self, gebruiker_id: int, jaar: int = None, parent=None)
                init_ui(self)
                load_saldo(self)
                refresh(self)

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
            regenereer_rode_lijnen_vanaf(actief_vanaf_str: str)

    - term_code_service.py
        Beschrijving: Term Code Service Centrale service voor het ophalen van codes op basis van systeem-termen  GEBRUIK:     from services.term_code_service import TermCodeService      verlof_code = TermCodeService.get_code_for_term('verlof')     # Returns: 'VV' (of wat de gebruiker heeft ingesteld)  CACHE: - Bij eerste gebruik wordt de mapping geladen - Refresh automatisch na wijzigingen in ShiftCodesScreen - Bij ontbrekende term: fallback naar standaard codes  VERPLICHTE TERMEN: - verlof (standaard: VV) - kompensatiedag (standaard: KD) - zondagrust (standaard: RX) - zaterdagrust (standaard: CX) - ziek (standaard: Z) - arbeidsduurverkorting (standaard: DA)
        Imports:
            from services.term_code_service import TermCodeService
            from typing import Dict, Optional
            import sqlite3
            from database.connection import get_connection
        Klassen & Methodes:
            class TermCodeService:
                refresh(cls)
                reset(cls)

    - verlof_saldo_service.py
        Beschrijving: Verlof & KD Saldo Service Versie: 0.6.10  Beheert verlof en kompensatiedagen saldi voor gebruikers. Gebruikt term-based systeem voor code-onafhankelijke queries.
        Imports:
            from datetime import datetime, date, timedelta
            from typing import Optional
            from database.connection import get_connection
            from services.term_code_service import TermCodeService
        Klassen & Methodes:
            class VerlofSaldoService:
                sync_saldo_naar_database(gebruiker_id: int, jaar: int)

    - __init__.py

Beschrijving:
-------------
Voeg hier handmatig uitleg toe over modules, datastromen, en verantwoordelijkheden.
"""
