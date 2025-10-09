#gui/styles.py
"""
Centrale styling configuratie voor Planning Tool
UPDATED: Uniforme button styling (zelfde padding, font-size, height voor alle button types)
Gebruik: from gui.styles import Styles, Colors, Fonts
"""


class Colors:
    """Kleur palette voor de applicatie"""
    # Primary colors
    PRIMARY = "#007bff"
    PRIMARY_HOVER = "#0056b3"

    # State colors
    SUCCESS = "#28a745"
    SUCCESS_HOVER = "#218838"
    WARNING = "#ffc107"
    WARNING_HOVER = "#e0a800"
    DANGER = "#dc3545"
    DANGER_HOVER = "#c82333"
    INFO = "#17a2b8"
    INFO_HOVER = "#117a8b"

    # Neutral colors
    SECONDARY = "#6c757d"
    SECONDARY_HOVER = "#5a6268"
    LIGHT = "#f8f9fa"
    DARK = "#343a40"

    # Backgrounds
    BG_WHITE = "#ffffff"
    BG_LIGHT = "#f8f9fa"
    BG_DARK = "#343a40"

    # Borders
    BORDER_LIGHT = "#dee2e6"
    BORDER_MEDIUM = "#ced4da"
    BORDER_DARK = "#6c757d"

    # Text
    TEXT_PRIMARY = "#212529"
    TEXT_SECONDARY = "#6c757d"
    TEXT_MUTED = "#999999"
    TEXT_WHITE = "#ffffff"
    TEXT_BLACK = "#000000"

    # Table
    TABLE_GRID = "#dee2e6"
    TABLE_HEADER_BG = "#f8f9fa"
    TABLE_HOVER = "#e9ecef"


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
        """Dashboard menu button styling"""
        return f"""
            QPushButton {{
                background-color: {Colors.BG_WHITE};
                border: 2px solid {Colors.BORDER_LIGHT};
                border-radius: {Dimensions.RADIUS_XL}px;
                text-align: left;
                padding: 15px;
                font-size: {Fonts.SIZE_NORMAL}px;
                font-family: {Fonts.FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Colors.TABLE_HOVER};
                border-color: {Colors.PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {Colors.BORDER_LIGHT};
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