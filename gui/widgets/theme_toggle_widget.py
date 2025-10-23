# gui/widgets/theme_toggle_widget.py
"""
Theme Toggle Widget
Visuele switch voor dark/light mode met zon/maan iconen
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from gui.styles import Fonts, ThemeManager


class ThemeToggleWidget(QWidget):
    """
    Toggle widget voor dark/light mode switching
    Bevat: Zon icon | Toggle button | Maan icon
    """

    theme_changed = pyqtSignal(str)  # Emit nieuwe theme ('light' of 'dark')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.update_button_state()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Zon icon (light mode) - met achtergrond voor betere zichtbaarheid
        self.sun_label = QLabel("☀")
        self.sun_label.setFont(QFont(Fonts.FAMILY, 18, QFont.Weight.Bold))
        self.sun_label.setFixedSize(28, 28)
        self.sun_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sun_label.setStyleSheet("""
            color: #FFB000;
            background-color: rgba(255, 193, 7, 0.2);
            border-radius: 14px;
            padding: 2px;
        """)
        self.sun_label.setToolTip("Light Mode")
        layout.addWidget(self.sun_label)

        # Toggle button (schuifknop effect)
        self.toggle_btn = QPushButton()
        self.toggle_btn.setFixedSize(50, 24)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.on_toggle)  # type: ignore
        layout.addWidget(self.toggle_btn)

        # Maan icon (dark mode) - met achtergrond voor betere zichtbaarheid
        self.moon_label = QLabel("☾")
        self.moon_label.setFont(QFont(Fonts.FAMILY, 18, QFont.Weight.Bold))
        self.moon_label.setFixedSize(28, 28)
        self.moon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.moon_label.setStyleSheet("""
            color: #5BC0DE;
            background-color: rgba(91, 192, 222, 0.2);
            border-radius: 14px;
            padding: 2px;
        """)
        self.moon_label.setToolTip("Dark Mode")
        layout.addWidget(self.moon_label)

    def update_button_state(self):
        """Update button styling gebaseerd op huidig thema"""
        current_theme = ThemeManager.get_theme()

        if current_theme == 'dark':
            # Dark mode actief - knop naar rechts (maan kant)
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #5BC0DE;
                    border: 2px solid #5BC0DE;
                    border-radius: 12px;
                    text-align: right;
                    padding-right: 4px;
                    font-weight: bold;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #46B8DA;
                    border-color: #46B8DA;
                }
            """)
            self.toggle_btn.setText("●")
            self.toggle_btn.setToolTip("Schakel naar Light Mode")

            # Icon highlighting - actief (maan) vs inactief (zon)
            self.sun_label.setStyleSheet("""
                color: #999999;
                background-color: rgba(200, 200, 200, 0.1);
                border-radius: 14px;
                padding: 2px;
            """)
            self.moon_label.setStyleSheet("""
                color: #5BC0DE;
                background-color: rgba(91, 192, 222, 0.3);
                border-radius: 14px;
                padding: 2px;
                font-weight: bold;
            """)
        else:
            # Light mode actief - knop naar links (zon kant)
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFB000;
                    border: 2px solid #FFB000;
                    border-radius: 12px;
                    text-align: left;
                    padding-left: 4px;
                    font-weight: bold;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #E0A800;
                    border-color: #E0A800;
                }
            """)
            self.toggle_btn.setText("●")
            self.toggle_btn.setToolTip("Schakel naar Dark Mode")

            # Icon highlighting - actief (zon) vs inactief (maan)
            self.sun_label.setStyleSheet("""
                color: #FFB000;
                background-color: rgba(255, 193, 7, 0.3);
                border-radius: 14px;
                padding: 2px;
                font-weight: bold;
            """)
            self.moon_label.setStyleSheet("""
                color: #999999;
                background-color: rgba(200, 200, 200, 0.1);
                border-radius: 14px;
                padding: 2px;
            """)

    def on_toggle(self):
        """Handle toggle click"""
        nieuwe_theme = ThemeManager.toggle_theme()
        self.update_button_state()
        self.theme_changed.emit(nieuwe_theme)  # type: ignore

    def refresh(self):
        """Refresh button state (useful when theme changed externally via F9)"""
        self.update_button_state()
