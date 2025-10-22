#gui/screens/login_screen.py
"""
Login scherm voor Planning Tool
FIXED: Instance attributes + pyqtSignal + type hints
"""
from typing import Dict, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import bcrypt
from database.connection import get_connection, get_db_version
from gui.styles import Styles, Colors, Fonts, Dimensions
from config import APP_VERSION


class LoginScreen(QWidget):
    """Login scherm met authenticatie"""

    # Signal als class-level attribute
    login_success = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        # Instance attributes declareren in __init__
        self.username_input: QLineEdit = QLineEdit()
        self.password_input: QLineEdit = QLineEdit()

        self.init_ui()

    def init_ui(self) -> None:
        """Initialiseer de user interface"""
        # Hoofd layout met centering
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Centered container
        container = QWidget()
        container.setMaximumWidth(400)
        container.setStyleSheet(f"background-color: {Colors.BG_WHITE}; border-radius: 10px;")

        layout = QVBoxLayout()
        layout.setSpacing(Dimensions.SPACING_LARGE)
        layout.setContentsMargins(50, 50, 50, 50)

        # Title
        title = QLabel("Planning Tool")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_LARGE, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Username
        self.username_input.setPlaceholderText("Gebruikersnaam")
        self.username_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_LARGE)
        self.username_input.setStyleSheet(Styles.input_field())
        layout.addWidget(self.username_input)

        # Password
        self.password_input.setPlaceholderText("Wachtwoord")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_LARGE)
        self.password_input.returnPressed.connect(self.login)  # type: ignore
        self.password_input.setStyleSheet(Styles.input_field())
        layout.addWidget(self.password_input)

        # Login button
        login_btn = QPushButton("Inloggen")
        login_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_LARGE)
        login_btn.clicked.connect(self.login)  # type: ignore
        login_btn.setStyleSheet(Styles.button_large_action(Colors.PRIMARY, Colors.PRIMARY_HOVER))
        layout.addWidget(login_btn)

        container.setLayout(layout)

        # Center container in main layout
        main_layout.addStretch()

        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(container)
        h_layout.addStretch()

        main_layout.addLayout(h_layout)
        main_layout.addStretch()

        # Versie informatie onderaan (v0.6.13)
        versie_layout = QHBoxLayout()
        versie_layout.setContentsMargins(20, 0, 20, 20)

        app_versie_label = QLabel(f"Versie {APP_VERSION}")
        app_versie_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: {Fonts.SIZE_SMALL}px;")
        versie_layout.addWidget(app_versie_label)

        versie_layout.addStretch()

        # Database versie (indien beschikbaar)
        db_versie = get_db_version()
        if db_versie:
            db_versie_label = QLabel(f"Database: {db_versie}")
            db_versie_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: {Fonts.SIZE_SMALL}px;")
            versie_layout.addWidget(db_versie_label)

        main_layout.addLayout(versie_layout)

        self.setLayout(main_layout)

    def login(self) -> None:
        """Verwerk login poging"""
        gebruikersnaam = self.username_input.text().strip()
        wachtwoord = self.password_input.text()

        if not gebruikersnaam or not wachtwoord:
            QMessageBox.warning(self, "Fout", "Vul alle velden in!")
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, gebruiker_uuid, gebruikersnaam, wachtwoord_hash, 
                   volledige_naam, rol, is_actief
            FROM gebruikers 
            WHERE gebruikersnaam = ?
        """, (gebruikersnaam,))

        user = cursor.fetchone()

        if not user:
            QMessageBox.warning(self, "Fout", "Ongeldige gebruikersnaam of wachtwoord!")
            conn.close()
            return

        if not user['is_actief']:
            QMessageBox.warning(self, "Fout", "Dit account is gedeactiveerd!")
            conn.close()
            return

        if bcrypt.checkpw(wachtwoord.encode('utf-8'), user['wachtwoord_hash']):
            # Update laatste_login timestamp
            cursor.execute("""
                UPDATE gebruikers 
                SET laatste_login = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (user['id'],))
            conn.commit()
            conn.close()

            # Emit success signal met user data
            user_data: Dict[str, Any] = {
                'id': user['id'],
                'uuid': user['gebruiker_uuid'],
                'gebruikersnaam': user['gebruikersnaam'],
                'naam': user['volledige_naam'],
                'rol': user['rol']
            }
            self.login_success.emit(user_data)  # type: ignore
        else:
            QMessageBox.warning(self, "Fout", "Ongeldige gebruikersnaam of wachtwoord!")
            conn.close()