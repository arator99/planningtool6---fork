#gui/dialogs/about_diolog.py

"""
About Dialog voor Planning Tool
Toont versie info, roadmap en credits
Laadt project info uit PROJECT_INFO.md
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTabWidget, QWidget, QTextEdit, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from gui.styles import Styles, Colors, Fonts, Dimensions
from pathlib import Path
import re

VERSION = "0.6.0"
BUILD_DATE = "oktober 2025"
DEVELOPERS = "Ontwikkeld door:\n• Aerts Bob (Lead Developer - I-O.112)\n• Claude (AI Assistant - Anthropic)"


def load_project_info():
    """Laad project info uit PROJECT_INFO.md"""
    info_file = Path(__file__).parent.parent.parent / "PROJECT_INFO.md"
    try:
        if info_file.exists():
            return info_file.read_text(encoding='utf-8')
        else:
            return "PROJECT_INFO.md niet gevonden in root folder."
    except Exception as e:
        return f"Fout bij laden van project info: {str(e)}"


def parse_roadmap_sections(markdown_text):
    """Parse markdown text naar HTML voor roadmap tab"""
    # Basis cleanup
    html = markdown_text.replace('\n\n', '<br><br>')
    html = html.replace('\n', '<br>')

    # Headers met kleuren
    html = re.sub(r'VOLTOOID:', '<h3 style="color: #28a745;">VOLTOOID:</h3>', html)
    html = re.sub(r'TODO - PRIORITEIT HOOG:', '<h3 style="color: #ffc107;">TODO - PRIORITEIT HOOG:</h3>', html)
    html = re.sub(r'TODO - PRIORITEIT MIDDEL:', '<h3 style="color: #007bff;">TODO - PRIORITEIT MIDDEL:</h3>', html)
    html = re.sub(r'TODO - PRIORITEIT LAAG:', '<h3 style="color: #6c757d;">TODO - PRIORITEIT LAAG:</h3>', html)

    # Vervang checkmarks en bullets
    html = html.replace('✅', '<span style="color: #28a745;">✓</span>')
    html = html.replace('📋', '<span style="color: #007bff;">•</span>')

    # Bold text (eenvoudige implementatie voor headers)
    html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)

    return html


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Over Planning Tool")
        self.setMinimumSize(700, 600)
        self.project_info = load_project_info()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Header met logo/titel
        header_layout = QVBoxLayout()
        header_layout.setSpacing(Dimensions.SPACING_SMALL)

        title = QLabel("Planning Tool")
        title.setFont(QFont(Fonts.FAMILY_ALT, Fonts.SIZE_LARGE, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {Colors.PRIMARY};")
        header_layout.addWidget(title)

        version_label = QLabel(f"Versie {VERSION}")
        version_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        header_layout.addWidget(version_label)

        build_label = QLabel(f"Build: {BUILD_DATE}")
        build_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        build_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        build_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        header_layout.addWidget(build_label)

        layout.addLayout(header_layout)

        # Tabs voor verschillende info
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Dimensions.RADIUS_MEDIUM}px;
                background: {Colors.BG_WHITE};
            }}
            QTabBar::tab {{
                background: {Colors.LIGHT};
                border: 1px solid {Colors.BORDER_LIGHT};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: {Dimensions.RADIUS_MEDIUM}px;
                border-top-right-radius: {Dimensions.RADIUS_MEDIUM}px;
            }}
            QTabBar::tab:selected {{
                background: {Colors.BG_WHITE};
                border-bottom-color: {Colors.BG_WHITE};
            }}
        """)

        # Tab 1: Over
        over_widget = self.create_over_tab()
        tabs.addTab(over_widget, "Over")

        # Tab 2: Status & Roadmap
        roadmap_widget = self.create_roadmap_tab()
        tabs.addTab(roadmap_widget, "Status & Roadmap")

        # Tab 3: Credits
        credits_widget = self.create_credits_tab()
        tabs.addTab(credits_widget, "Credits")

        layout.addWidget(tabs)

        # Sluit knop
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Sluiten")
        close_btn.setFixedSize(100, Dimensions.BUTTON_HEIGHT_NORMAL)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(Styles.button_secondary())
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def create_over_tab(self):
        """Over tab met beschrijving"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(
            Dimensions.MARGIN_MEDIUM,
            Dimensions.MARGIN_MEDIUM,
            Dimensions.MARGIN_MEDIUM,
            Dimensions.MARGIN_MEDIUM
        )
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        beschrijving = QLabel(
            "Planning Tool is een applicatie voor het beheren van shift planning "
            "voor diensten die aan self-rostering doen. De tool ondersteunt roterend rooster planning, "
            "verlofbeheer, HR regels validatie en automatische feestdagen berekening."
        )
        beschrijving.setWordWrap(True)
        beschrijving.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        layout.addWidget(beschrijving)

        layout.addSpacing(Dimensions.SPACING_MEDIUM)

        # Features lijst
        features_label = QLabel("Belangrijkste functies:")
        features_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        layout.addWidget(features_label)

        features = [
            "Gebruikersbeheer met rol-gebaseerde toegang",
            "6-weken roterend typedienst rooster",
            "Automatische feestdagen generatie met Paasberekening",
            "HR regels validatie (12u rust, max uren, werkdagen)",
            "Verlof aanvraag en goedkeuring systeem",
            "Planning export naar Excel voor HR administratie",
            "28-dagen cyclus tracking (rode lijnen)",
            "Reserve medewerkers ondersteuning"
        ]

        for feature in features:
            feature_label = QLabel(f"  • {feature}")
            feature_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
            feature_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
            layout.addWidget(feature_label)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_roadmap_tab(self):
        """Roadmap tab met scroll - laadt uit PROJECT_INFO.md"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area voor roadmap
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"border: none; background: {Colors.BG_WHITE};")

        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(
            Dimensions.MARGIN_MEDIUM,
            Dimensions.MARGIN_MEDIUM,
            Dimensions.MARGIN_MEDIUM,
            Dimensions.MARGIN_MEDIUM
        )
        content_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        roadmap_text = QTextEdit()
        roadmap_text.setReadOnly(True)
        roadmap_text.setStyleSheet(f"""
            QTextEdit {{
                border: none;
                background: {Colors.BG_WHITE};
                font-family: {Fonts.FAMILY};
                font-size: {Fonts.SIZE_SMALL}px;
            }}
        """)

        # Parse en laad project info
        html_content = parse_roadmap_sections(self.project_info)
        roadmap_text.setHtml(html_content)

        content_layout.addWidget(roadmap_text)

        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)

        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget

    def create_credits_tab(self):
        """Credits tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE
        )
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Developers
        dev_label = QLabel("Ontwikkeling")
        dev_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(dev_label)

        dev_text = QLabel(DEVELOPERS)
        dev_text.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        dev_text.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(dev_text)

        layout.addSpacing(Dimensions.SPACING_MEDIUM)

        # Technologie
        tech_label = QLabel("Technologie")
        tech_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(tech_label)

        tech_items = [
            "Python 3.x",
            "PyQt6 - GUI Framework",
            "SQLite - Database",
            "bcrypt - Password Hashing",
            "Papaparse - CSV Processing (toekomstig)",
            "SheetJS - Excel Export (toekomstig)"
        ]

        for tech in tech_items:
            tech_item = QLabel(f"  • {tech}")
            tech_item.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
            layout.addWidget(tech_item)

        layout.addSpacing(Dimensions.SPACING_MEDIUM)

        # Copyright
        copyright_label = QLabel(f"© 2025 - Planning Tool v{VERSION}")
        copyright_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TINY))
        copyright_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)

        layout.addStretch()

        widget.setLayout(layout)
        return widget