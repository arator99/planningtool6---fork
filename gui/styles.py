#gui/styles.py
"""
Centrale styling configuratie voor Planning Tool
UPDATED: Dark mode ondersteuning met ThemeManager
Gebruik: from gui.styles import Styles, Colors, Fonts, ThemeManager
"""
from typing import Optional


class ThemeManager:
    """Beheer het huidige thema (light/dark)"""
    _instance: Optional['ThemeManager'] = None
    _current_theme: str = 'light'  # default

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def set_theme(cls, theme: str) -> None:
        """Stel thema in: 'light' of 'dark'"""
        if theme not in ['light', 'dark']:
            raise ValueError(f"Ongeldig thema: {theme}. Gebruik 'light' of 'dark'.")
        cls._current_theme = theme
        # Update Colors class
        Colors.apply_theme(theme)

    @classmethod
    def get_theme(cls) -> str:
        """Haal huidig thema op"""
        return cls._current_theme

    @classmethod
    def toggle_theme(cls) -> str:
        """Wissel tussen light en dark mode. Returns nieuwe thema."""
        new_theme = 'dark' if cls._current_theme == 'light' else 'light'
        cls.set_theme(new_theme)
        return new_theme


class Colors:
    """Kleur palette voor de applicatie (thema-bewust)"""
    # Light theme colors (default)
    _LIGHT_THEME = {
        # Primary colors
        'PRIMARY': "#007bff",
        'PRIMARY_HOVER': "#0056b3",

        # State colors
        'SUCCESS': "#28a745",
        'SUCCESS_HOVER': "#218838",
        'WARNING': "#ffc107",
        'WARNING_HOVER': "#e0a800",
        'WARNING_BG': "#fff3cd",
        'DANGER': "#dc3545",
        'DANGER_HOVER': "#c82333",
        'INFO': "#17a2b8",
        'INFO_HOVER': "#117a8b",

        # Neutral colors
        'SECONDARY': "#6c757d",
        'SECONDARY_HOVER': "#5a6268",
        'LIGHT': "#f8f9fa",
        'DARK': "#343a40",

        # Backgrounds
        'BG_WHITE': "#ffffff",
        'BG_LIGHT': "#f8f9fa",
        'BG_DARK': "#343a40",

        # Borders
        'BORDER_LIGHT': "#dee2e6",
        'BORDER_MEDIUM': "#ced4da",
        'BORDER_DARK': "#6c757d",

        # Text
        'TEXT_PRIMARY': "#212529",
        'TEXT_SECONDARY': "#6c757d",
        'TEXT_MUTED': "#999999",
        'TEXT_WHITE': "#ffffff",
        'TEXT_BLACK': "#000000",

        # Table
        'TABLE_GRID': "#dee2e6",
        'TABLE_HEADER_BG': "#f8f9fa",
        'TABLE_HOVER': "#e9ecef",

        # Menu buttons (dashboard)
        'MENU_BUTTON_BG': "#ffffff",
        'MENU_BUTTON_HOVER': "#e9ecef",
    }

    # Dark theme colors
    _DARK_THEME = {
        # Primary colors (iets lichter voor contrast)
        'PRIMARY': "#4a9eff",
        'PRIMARY_HOVER': "#3d8ae0",

        # State colors
        'SUCCESS': "#5cb85c",
        'SUCCESS_HOVER': "#4cae4c",
        'WARNING': "#f0ad4e",
        'WARNING_HOVER': "#ec971f",
        'WARNING_BG': "#664d03",
        'DANGER': "#d9534f",
        'DANGER_HOVER': "#c9302c",
        'INFO': "#5bc0de",
        'INFO_HOVER': "#46b8da",

        # Neutral colors
        'SECONDARY': "#7a8288",
        'SECONDARY_HOVER': "#62686d",
        'LIGHT': "#2b3035",
        'DARK': "#e0e0e0",

        # Backgrounds
        'BG_WHITE': "#1e1e1e",
        'BG_LIGHT': "#2b3035",
        'BG_DARK': "#141414",

        # Borders
        'BORDER_LIGHT': "#3d4349",
        'BORDER_MEDIUM': "#4a5159",
        'BORDER_DARK': "#6c757d",

        # Text
        'TEXT_PRIMARY': "#e0e0e0",
        'TEXT_SECONDARY': "#a0a0a0",
        'TEXT_MUTED': "#707070",
        'TEXT_WHITE': "#ffffff",
        'TEXT_BLACK': "#000000",

        # Table
        'TABLE_GRID': "#3d4349",
        'TABLE_HEADER_BG': "#2b3035",
        'TABLE_HOVER': "#353b41",

        # Menu buttons (dashboard) - lichter dan BG_WHITE voor zichtbaarheid
        'MENU_BUTTON_BG': "#2b3035",
        'MENU_BUTTON_HOVER': "#353b41",
    }

    # Active theme colors (wijst naar light of dark)
    PRIMARY = _LIGHT_THEME['PRIMARY']
    PRIMARY_HOVER = _LIGHT_THEME['PRIMARY_HOVER']
    SUCCESS = _LIGHT_THEME['SUCCESS']
    SUCCESS_HOVER = _LIGHT_THEME['SUCCESS_HOVER']
    WARNING = _LIGHT_THEME['WARNING']
    WARNING_HOVER = _LIGHT_THEME['WARNING_HOVER']
    WARNING_BG = _LIGHT_THEME['WARNING_BG']
    DANGER = _LIGHT_THEME['DANGER']
    DANGER_HOVER = _LIGHT_THEME['DANGER_HOVER']
    INFO = _LIGHT_THEME['INFO']
    INFO_HOVER = _LIGHT_THEME['INFO_HOVER']
    SECONDARY = _LIGHT_THEME['SECONDARY']
    SECONDARY_HOVER = _LIGHT_THEME['SECONDARY_HOVER']
    LIGHT = _LIGHT_THEME['LIGHT']
    DARK = _LIGHT_THEME['DARK']
    BG_WHITE = _LIGHT_THEME['BG_WHITE']
    BG_LIGHT = _LIGHT_THEME['BG_LIGHT']
    BG_DARK = _LIGHT_THEME['BG_DARK']
    BORDER_LIGHT = _LIGHT_THEME['BORDER_LIGHT']
    BORDER_MEDIUM = _LIGHT_THEME['BORDER_MEDIUM']
    BORDER_DARK = _LIGHT_THEME['BORDER_DARK']
    TEXT_PRIMARY = _LIGHT_THEME['TEXT_PRIMARY']
    TEXT_SECONDARY = _LIGHT_THEME['TEXT_SECONDARY']
    TEXT_MUTED = _LIGHT_THEME['TEXT_MUTED']
    TEXT_WHITE = _LIGHT_THEME['TEXT_WHITE']
    TEXT_BLACK = _LIGHT_THEME['TEXT_BLACK']
    TABLE_GRID = _LIGHT_THEME['TABLE_GRID']
    TABLE_HEADER_BG = _LIGHT_THEME['TABLE_HEADER_BG']
    TABLE_HOVER = _LIGHT_THEME['TABLE_HOVER']
    MENU_BUTTON_BG = _LIGHT_THEME['MENU_BUTTON_BG']
    MENU_BUTTON_HOVER = _LIGHT_THEME['MENU_BUTTON_HOVER']

    @classmethod
    def apply_theme(cls, theme: str) -> None:
        """Pas een thema toe door alle class attributes bij te werken"""
        theme_colors = cls._DARK_THEME if theme == 'dark' else cls._LIGHT_THEME

        for key, value in theme_colors.items():
            setattr(cls, key, value)


class Fonts:
    """Font configuratie"""
    FAMILY = "Arial"
    FAMILY_ALT = "Segoe UI"

    SIZE_LARGE = 24
    SIZE_TITLE = 18
    SIZE_HEADING = 16
    SIZE_NORMAL = 14
    SIZE_SMALL = 12
    SIZE_TINY = 9
    SIZE_BUTTON = 12  # Uniforme button font size

    WEIGHT_NORMAL = "normal"
    WEIGHT_BOLD = "bold"


class Dimensions:
    """Afmetingen en spacing"""
    # Button heights - aangepast voor betere table integratie
    BUTTON_HEIGHT_LARGE = 40
    BUTTON_HEIGHT_NORMAL = 32  # Was: 35 - nu kleiner voor 50px rows
    BUTTON_HEIGHT_SMALL = 28   # Was: 30
    BUTTON_HEIGHT_TINY = 20

    # Table
    TABLE_ROW_HEIGHT = 50
    TABLE_ROW_HEIGHT_COMPACT = 45

    # Spacing
    SPACING_SMALL = 5
    SPACING_MEDIUM = 10
    SPACING_LARGE = 20

    # Margins
    MARGIN_SMALL = 5
    MARGIN_MEDIUM = 20
    MARGIN_LARGE = 40

    # Border radius
    RADIUS_SMALL = 3
    RADIUS_MEDIUM = 4
    RADIUS_LARGE = 5
    RADIUS_XL = 8


class Styles:
    """Pre-built style strings voor widgets met UNIFORME button styling"""

    @staticmethod
    def button_primary(height=None):
        """Primary action button (blauw)"""
        h = height or Dimensions.BUTTON_HEIGHT_NORMAL
        return f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_WHITE};
                border: none;
                border-radius: {Dimensions.RADIUS_MEDIUM}px;
                padding: 6px 12px;
                font-weight: {Fonts.WEIGHT_BOLD};
                font-size: {Fonts.SIZE_BUTTON}px;
                font-family: {Fonts.FAMILY};
                min-height: {h}px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
                color: {Colors.TEXT_WHITE};
            }}
            QPushButton:disabled {{
                background-color: {Colors.BORDER_LIGHT};
                color: {Colors.TEXT_MUTED};
            }}
        """

    @staticmethod
    def button_success(height=None):
        """Success button (groen) - bijv. Activeren, Opslaan"""
        h = height or Dimensions.BUTTON_HEIGHT_NORMAL
        return f"""
            QPushButton {{
                background-color: {Colors.SUCCESS};
                color: {Colors.TEXT_WHITE};
                border: none;
                border-radius: {Dimensions.RADIUS_MEDIUM}px;
                padding: 6px 12px;
                font-weight: {Fonts.WEIGHT_BOLD};
                font-size: {Fonts.SIZE_BUTTON}px;
                font-family: {Fonts.FAMILY};
                min-height: {h}px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SUCCESS_HOVER};
                color: {Colors.TEXT_WHITE};
            }}
        """

    @staticmethod
    def button_warning(height=None):
        """Warning button (oranje/geel) - bijv. Bewerken, Deactiveren"""
        h = height or Dimensions.BUTTON_HEIGHT_NORMAL
        return f"""
            QPushButton {{
                background-color: {Colors.WARNING};
                color: {Colors.TEXT_BLACK};
                border: none;
                border-radius: {Dimensions.RADIUS_MEDIUM}px;
                padding: 6px 12px;
                font-weight: {Fonts.WEIGHT_BOLD};
                font-size: {Fonts.SIZE_BUTTON}px;
                font-family: {Fonts.FAMILY};
                min-height: {h}px;
            }}
            QPushButton:hover {{
                background-color: {Colors.WARNING_HOVER};
                color: {Colors.TEXT_BLACK};
            }}
        """

    @staticmethod
    def button_danger(height=None):
        """Danger button (rood) - bijv. Verwijderen, Uitloggen"""
        h = height or Dimensions.BUTTON_HEIGHT_NORMAL
        return f"""
            QPushButton {{
                background-color: {Colors.DANGER};
                color: {Colors.TEXT_WHITE};
                border: none;
                border-radius: {Dimensions.RADIUS_MEDIUM}px;
                padding: 6px 12px;
                font-weight: {Fonts.WEIGHT_BOLD};
                font-size: {Fonts.SIZE_BUTTON}px;
                font-family: {Fonts.FAMILY};
                min-height: {h}px;
            }}
            QPushButton:hover {{
                background-color: {Colors.DANGER_HOVER};
                color: {Colors.TEXT_WHITE};
            }}
        """

    @staticmethod
    def button_secondary(height=None):
        """Secondary button (grijs) - bijv. Terug, Annuleren"""
        h = height or Dimensions.BUTTON_HEIGHT_NORMAL
        return f"""
            QPushButton {{
                background-color: {Colors.SECONDARY};
                color: {Colors.TEXT_WHITE};
                border: none;
                border-radius: {Dimensions.RADIUS_MEDIUM}px;
                padding: 6px 12px;
                font-weight: {Fonts.WEIGHT_BOLD};
                font-size: {Fonts.SIZE_BUTTON}px;
                font-family: {Fonts.FAMILY};
                min-height: {h}px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SECONDARY_HOVER};
            }}
        """

    @staticmethod
    def button_large_action(bg_color, hover_color):
        """Grote actie button met custom kleuren"""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                border-radius: {Dimensions.RADIUS_LARGE}px;
                padding: 6px 12px;
                font-size: {Fonts.SIZE_BUTTON}px;
                font-weight: {Fonts.WEIGHT_BOLD};
                font-family: {Fonts.FAMILY};
                min-height: {Dimensions.BUTTON_HEIGHT_NORMAL}px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """

    @staticmethod
    def input_field():
        """Standard input field styling"""
        return f"""
            QLineEdit, QComboBox, QDateEdit {{
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: {Dimensions.RADIUS_MEDIUM}px;
                padding: 8px;
                font-size: {Fonts.SIZE_NORMAL}px;
                font-family: {Fonts.FAMILY};
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 2px solid {Colors.PRIMARY};
            }}
        """

    @staticmethod
    def table_widget():
        """Standard table styling"""
        return f"""
            QTableWidget {{
                border: 1px solid {Colors.TABLE_GRID};
                background-color: {Colors.BG_WHITE};
                gridline-color: {Colors.TABLE_GRID};
                border-radius: {Dimensions.RADIUS_LARGE}px;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background-color: {Colors.TABLE_HEADER_BG};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {Colors.TABLE_GRID};
                font-weight: {Fonts.WEIGHT_BOLD};
                font-family: {Fonts.FAMILY};
            }}
        """

    @staticmethod
    def info_box(bg_color="#e7f3ff", border_color="#b3d9ff", text_color="#004085"):
        """Info box / alert styling"""
        return f"""
            QLabel {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: {Dimensions.RADIUS_MEDIUM}px;
                padding: 10px;
                color: {text_color};
                font-family: {Fonts.FAMILY};
            }}
        """

    @staticmethod
    def menu_button():
        """Dashboard menu button styling (thema-bewust)"""
        return f"""
            QPushButton {{
                background-color: {Colors.MENU_BUTTON_BG};
                color: {Colors.TEXT_PRIMARY};
                border: 2px solid {Colors.BORDER_LIGHT};
                border-radius: {Dimensions.RADIUS_XL}px;
                text-align: left;
                padding: 15px;
                font-size: {Fonts.SIZE_NORMAL}px;
                font-family: {Fonts.FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Colors.MENU_BUTTON_HOVER};
                border-color: {Colors.PRIMARY};
                color: {Colors.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {Colors.MENU_BUTTON_HOVER};
                color: {Colors.TEXT_PRIMARY};
            }}
            QPushButton:disabled {{
                background-color: {Colors.LIGHT};
                color: {Colors.TEXT_MUTED};
                border-color: {Colors.BORDER_LIGHT};
            }}
        """


class TableConfig:
    """Helper functies voor table configuratie"""

    @staticmethod
    def setup_table_widget(table, row_height=None):
        """Configureer een QTableWidget met standaard settings"""
        if row_height is None:
            row_height = Dimensions.TABLE_ROW_HEIGHT

        table.setStyleSheet(Styles.table_widget())
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)
        table.verticalHeader().setDefaultSectionSize(row_height)