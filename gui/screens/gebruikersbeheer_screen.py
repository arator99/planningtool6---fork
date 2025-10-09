#gui/screens/gebruikersbeheer_screen.py
"""
Gebruikersbeheer scherm voor Planning Tool
Toevoegen, bewerken en beheren van teamleden
FIXED: Instance attributes + exception handling + type hints
"""
from typing import List, Dict, Any, Optional, Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QDialog, QFormLayout,
                             QComboBox, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database.connection import get_connection
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
import bcrypt
import uuid
import re
import sqlite3
from datetime import datetime


class GebruikersbeheerScreen(QWidget):
    def __init__(self, router: Callable):
        super().__init__()
        self.router = router

        # Instance attributes declareren in __init__
        self.zoek_input: QLineEdit = QLineEdit()
        self.tabel: QTableWidget = QTableWidget()
        self.alle_gebruikers: List[Dict[str, Any]] = []

        self.init_ui()
        self.laad_gebruikers()

    def init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE
        )
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Gebruikersbeheer")
        title.setFont(QFont(Fonts.FAMILY_ALT, Fonts.SIZE_LARGE, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        terug_btn = QPushButton("Terug")
        terug_btn.setFixedSize(100, Dimensions.BUTTON_HEIGHT_LARGE)
        terug_btn.clicked.connect(self.router)  # type: ignore
        terug_btn.setStyleSheet(Styles.button_secondary())
        header_layout.addWidget(terug_btn)

        layout.addLayout(header_layout)

        # Info bar
        info_label = QLabel("Gebruikersnaam formaat: 3 hoofdletters + 4 cijfers (bijv. AZE3601)")
        info_label.setStyleSheet(Styles.info_box())
        layout.addWidget(info_label)

        # Zoekbalk en toevoegen knop
        toolbar_layout = QHBoxLayout()

        self.zoek_input.setPlaceholderText("Zoek op naam of gebruikersnaam...")
        self.zoek_input.setFixedHeight(Dimensions.BUTTON_HEIGHT_LARGE)
        self.zoek_input.textChanged.connect(self.filter_gebruikers)  # type: ignore
        self.zoek_input.setStyleSheet(Styles.input_field())
        toolbar_layout.addWidget(self.zoek_input, stretch=1)

        toevoegen_btn = QPushButton("Nieuwe Gebruiker")
        toevoegen_btn.setFixedSize(180, Dimensions.BUTTON_HEIGHT_LARGE)
        toevoegen_btn.clicked.connect(self.nieuwe_gebruiker)  # type: ignore
        toevoegen_btn.setStyleSheet(Styles.button_large_action(Colors.SUCCESS, Colors.SUCCESS_HOVER))
        toolbar_layout.addWidget(toevoegen_btn)

        layout.addLayout(toolbar_layout)

        # Tabel
        self.tabel.setColumnCount(8)
        self.tabel.setHorizontalHeaderLabels([
            "Gebruikersnaam", "Naam", "Rol", "Reserve",
            "Startweek", "Actief", "Aangemaakt", "Acties"
        ])

        # Tabel configuratie met centrale styling
        TableConfig.setup_table_widget(self.tabel, row_height=50)

        # Kolom breedtes
        header = self.tabel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.tabel.setColumnWidth(7, 200)

        layout.addWidget(self.tabel)

        self.setLayout(layout)

    def laad_gebruikers(self) -> None:
        """Laad alle gebruikers uit database"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, gebruiker_uuid, gebruikersnaam, volledige_naam, rol, 
                   is_reserve, startweek_typedienst, is_actief, aangemaakt_op
            FROM gebruikers
            ORDER BY volledige_naam
        """)

        self.alle_gebruikers = cursor.fetchall()
        conn.close()

        self.toon_gebruikers(self.alle_gebruikers)

    def toon_gebruikers(self, gebruikers: List[Dict[str, Any]]) -> None:
        """Toon gebruikers in tabel met gestileerde actieknoppen"""
        self.tabel.setRowCount(len(gebruikers))

        for row, gebruiker in enumerate(gebruikers):
            self.tabel.setItem(row, 0, QTableWidgetItem(gebruiker['gebruikersnaam']))
            self.tabel.setItem(row, 1, QTableWidgetItem(gebruiker['volledige_naam']))

            rol_text = "Planner" if gebruiker['rol'] == 'planner' else "Teamlid"
            self.tabel.setItem(row, 2, QTableWidgetItem(rol_text))

            reserve_text = "Ja" if gebruiker['is_reserve'] else "Nee"
            self.tabel.setItem(row, 3, QTableWidgetItem(reserve_text))

            startweek_text = f"Week {gebruiker['startweek_typedienst']}" if gebruiker['startweek_typedienst'] else "N/A"
            self.tabel.setItem(row, 4, QTableWidgetItem(startweek_text))

            actief_text = "Ja" if gebruiker['is_actief'] else "Nee"
            actief_item = QTableWidgetItem(actief_text)
            if not gebruiker['is_actief']:
                actief_item.setForeground(Qt.GlobalColor.red)
            self.tabel.setItem(row, 5, actief_item)

            if gebruiker['aangemaakt_op']:
                try:
                    datum = datetime.fromisoformat(gebruiker['aangemaakt_op'])
                    datum_text = datum.strftime("%d-%m-%Y")
                except ValueError:
                    datum_text = "N/A"
            else:
                datum_text = "N/A"
            self.tabel.setItem(row, 6, QTableWidgetItem(datum_text))

            # Acties
            acties_widget = QWidget()
            acties_layout = QHBoxLayout()
            acties_layout.setContentsMargins(0, 0, 0, 0)
            acties_layout.setSpacing(Dimensions.SPACING_SMALL)
            acties_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Bewerken
            bewerk_btn = QPushButton("Bewerken")
            bewerk_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            bewerk_btn.setFixedWidth(80)
            bewerk_btn.setStyleSheet(Styles.button_primary(Dimensions.BUTTON_HEIGHT_TINY))
            bewerk_btn.clicked.connect(self.genereer_bewerk_callback(dict(gebruiker)))
            acties_layout.addWidget(bewerk_btn)

            # Activeren/Deactiveren
            toggle_btn = QPushButton("Deactiveren" if gebruiker['is_actief'] else "Activeren")
            toggle_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            toggle_btn.setFixedWidth(96)
            toggle_btn.setStyleSheet(
                Styles.button_warning(Dimensions.BUTTON_HEIGHT_TINY) if gebruiker['is_actief']
                else Styles.button_success(Dimensions.BUTTON_HEIGHT_TINY)
            )
            toggle_btn.clicked.connect(self.genereer_toggle_callback(dict(gebruiker)))
            acties_layout.addWidget(toggle_btn)

            acties_widget.setLayout(acties_layout)
            self.tabel.setCellWidget(row, 7, acties_widget)

    def genereer_bewerk_callback(self, gebruiker: Dict[str, Any]):
        def callback():
            self.bewerk_gebruiker(gebruiker)

        return callback

    def genereer_toggle_callback(self, gebruiker: Dict[str, Any]):
        def callback():
            self.toggle_actief(gebruiker)

        return callback

    def filter_gebruikers(self) -> None:
        """Filter gebruikers op basis van zoekterm"""
        zoekterm = self.zoek_input.text().lower()

        if not zoekterm:
            self.toon_gebruikers(self.alle_gebruikers)
            return

        gefilterd = [
            g for g in self.alle_gebruikers
            if zoekterm in g['gebruikersnaam'].lower() or
               zoekterm in g['volledige_naam'].lower()
        ]

        self.toon_gebruikers(gefilterd)

    def nieuwe_gebruiker(self) -> None:
        """Open dialog voor nieuwe gebruiker"""
        dialog = GebruikerDialog(parent=self, gebruiker=None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.opslaan_gebruiker(data)

    def bewerk_gebruiker(self, gebruiker: Dict[str, Any]) -> None:
        """Open dialog om gebruiker te bewerken"""
        dialog = GebruikerDialog(parent=self, gebruiker=gebruiker)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.update_gebruiker(gebruiker['id'], data)

    def opslaan_gebruiker(self, data: Dict[str, Any]) -> None:
        """Sla nieuwe gebruiker op in database"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Check of gebruikersnaam al bestaat
            cursor.execute("""
                SELECT id FROM gebruikers WHERE gebruikersnaam = ?
            """, (data['gebruikersnaam'],))

            if cursor.fetchone():
                QMessageBox.warning(self, "Fout",
                                    "Deze gebruikersnaam bestaat al!")
                conn.close()
                return

            # Hash wachtwoord
            wachtwoord_hash = bcrypt.hashpw(
                data['wachtwoord'].encode('utf-8'),
                bcrypt.gensalt()
            )

            # Genereer UUID
            gebruiker_uuid = str(uuid.uuid4())

            cursor.execute("""
                INSERT INTO gebruikers 
                (gebruiker_uuid, gebruikersnaam, wachtwoord_hash, volledige_naam, rol,
                 is_reserve, startweek_typedienst, is_actief, aangemaakt_op)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                gebruiker_uuid,
                data['gebruikersnaam'],
                wachtwoord_hash,
                data['volledige_naam'],
                data['rol'],
                data['is_reserve'],
                data['startweek_typedienst'],
                1  # Standaard actief
            ))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Succes",
                                    "Gebruiker succesvol aangemaakt!")
            self.laad_gebruikers()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout",
                                 f"Fout bij opslaan: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Fout",
                                 f"Onverwachte fout: {str(e)}")

    def update_gebruiker(self, gebruiker_id: int, data: Dict[str, Any]) -> None:
        """Update bestaande gebruiker"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Check of gebruikersnaam al bestaat (bij andere gebruiker)
            cursor.execute("""
                SELECT id FROM gebruikers 
                WHERE gebruikersnaam = ? AND id != ?
            """, (data['gebruikersnaam'], gebruiker_id))

            if cursor.fetchone():
                QMessageBox.warning(self, "Fout",
                                    "Deze gebruikersnaam bestaat al!")
                conn.close()
                return

            # Update zonder wachtwoord als deze niet is ingevuld
            if data['wachtwoord']:
                wachtwoord_hash = bcrypt.hashpw(
                    data['wachtwoord'].encode('utf-8'),
                    bcrypt.gensalt()
                )
                cursor.execute("""
                    UPDATE gebruikers
                    SET gebruikersnaam = ?,
                        wachtwoord_hash = ?,
                        volledige_naam = ?,
                        rol = ?,
                        is_reserve = ?,
                        startweek_typedienst = ?
                    WHERE id = ?
                """, (
                    data['gebruikersnaam'],
                    wachtwoord_hash,
                    data['volledige_naam'],
                    data['rol'],
                    data['is_reserve'],
                    data['startweek_typedienst'],
                    gebruiker_id
                ))
            else:
                cursor.execute("""
                    UPDATE gebruikers
                    SET gebruikersnaam = ?,
                        volledige_naam = ?,
                        rol = ?,
                        is_reserve = ?,
                        startweek_typedienst = ?
                    WHERE id = ?
                """, (
                    data['gebruikersnaam'],
                    data['volledige_naam'],
                    data['rol'],
                    data['is_reserve'],
                    data['startweek_typedienst'],
                    gebruiker_id
                ))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Succes",
                                    "Gebruiker succesvol bijgewerkt!")
            self.laad_gebruikers()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout",
                                 f"Fout bij bijwerken: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Fout",
                                 f"Onverwachte fout: {str(e)}")

    def toggle_actief(self, gebruiker: Dict[str, Any]) -> None:
        """Toggle actief status van gebruiker"""
        nieuwe_status = 0 if gebruiker['is_actief'] else 1
        actie = "deactiveren" if gebruiker['is_actief'] else "activeren"

        reply = QMessageBox.question(
            self,
            "Bevestigen",
            f"Weet je zeker dat je {gebruiker['volledige_naam']} wilt {actie}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()

                # Update status en timestamp
                if nieuwe_status == 0:
                    # Deactiveren
                    cursor.execute("""
                        UPDATE gebruikers
                        SET is_actief = ?, gedeactiveerd_op = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (nieuwe_status, gebruiker['id']))
                else:
                    # Activeren
                    cursor.execute("""
                        UPDATE gebruikers
                        SET is_actief = ?, gedeactiveerd_op = NULL
                        WHERE id = ?
                    """, (nieuwe_status, gebruiker['id']))

                conn.commit()
                conn.close()

                self.laad_gebruikers()

            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Fout",
                                     f"Fout bij wijzigen status: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Fout",
                                     f"Onverwachte fout: {str(e)}")


class GebruikerDialog(QDialog):
    """Dialog voor toevoegen/bewerken van gebruiker"""

    def __init__(self, parent: Optional[QWidget] = None, gebruiker: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.gebruiker = gebruiker
        self.edit_mode = gebruiker is not None

        self.setWindowTitle("Gebruiker Bewerken" if self.edit_mode else "Nieuwe Gebruiker")
        self.setMinimumWidth(500)

        # Instance attributes declareren in __init__
        self.gebruikersnaam_input: QLineEdit = QLineEdit()
        self.naam_input: QLineEdit = QLineEdit()
        self.wachtwoord_input: QLineEdit = QLineEdit()
        self.rol_combo: QComboBox = QComboBox()
        self.reserve_check: QCheckBox = QCheckBox("Is reserve")
        self.startweek_combo: QComboBox = QComboBox()

        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(Dimensions.SPACING_MEDIUM + 5)

        form_layout = QFormLayout()
        form_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Gebruikersnaam
        self.gebruikersnaam_input.setPlaceholderText("ABC1234")
        self.gebruikersnaam_input.setMaxLength(7)
        self.gebruikersnaam_input.textChanged.connect(self.on_gebruikersnaam_changed)  # type: ignore
        if self.edit_mode and self.gebruiker:
            self.gebruikersnaam_input.setText(self.gebruiker['gebruikersnaam'])
        form_layout.addRow("Gebruikersnaam:", self.gebruikersnaam_input)

        # Volledige naam
        if self.edit_mode and self.gebruiker:
            self.naam_input.setText(self.gebruiker['volledige_naam'])
        form_layout.addRow("Volledige Naam:", self.naam_input)

        # Wachtwoord
        self.wachtwoord_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self.edit_mode:
            self.wachtwoord_input.setPlaceholderText("Laat leeg om ongewijzigd te laten")
        form_layout.addRow("Wachtwoord:", self.wachtwoord_input)

        # Rol
        self.rol_combo.addItems(["Teamlid", "Planner"])
        if self.edit_mode and self.gebruiker:
            index = 1 if self.gebruiker['rol'] == 'planner' else 0
            self.rol_combo.setCurrentIndex(index)
        form_layout.addRow("Rol:", self.rol_combo)

        # Reserve checkbox
        if self.edit_mode and self.gebruiker:
            self.reserve_check.setChecked(self.gebruiker['is_reserve'])
        self.reserve_check.stateChanged.connect(self.on_reserve_changed)  # type: ignore
        form_layout.addRow("", self.reserve_check)

        # Startweek typedienst
        self.startweek_combo.addItems(["Geen", "Week 1", "Week 2", "Week 3",
                                       "Week 4", "Week 5", "Week 6"])
        if self.edit_mode and self.gebruiker and self.gebruiker['startweek_typedienst']:
            self.startweek_combo.setCurrentIndex(self.gebruiker['startweek_typedienst'])

        # Disable startweek als reserve
        if self.reserve_check.isChecked():
            self.startweek_combo.setEnabled(False)

        form_layout.addRow("Startweek Typedienst:", self.startweek_combo)

        layout.addLayout(form_layout)

        # Info labels
        info_layout = QVBoxLayout()
        info_layout.setSpacing(Dimensions.SPACING_SMALL)

        format_label = QLabel(
            "Gebruikersnaam: 3 hoofdletters + 4 cijfers (bijv. AZE3601)"
        )
        format_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-style: italic; font-size: {Fonts.SIZE_SMALL}px;")
        info_layout.addWidget(format_label)

        reserve_label = QLabel(
            "Reserves volgen geen typetabel en worden handmatig gepland."
        )
        reserve_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-style: italic; font-size: {Fonts.SIZE_SMALL}px;")
        info_layout.addWidget(reserve_label)

        layout.addLayout(info_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        annuleer_btn = QPushButton("Annuleren")
        annuleer_btn.clicked.connect(self.reject)  # type: ignore
        annuleer_btn.setStyleSheet(Styles.button_secondary())
        button_layout.addWidget(annuleer_btn)

        opslaan_btn = QPushButton("Opslaan")
        opslaan_btn.clicked.connect(self.valideer_en_accept)  # type: ignore
        opslaan_btn.setStyleSheet(Styles.button_large_action(Colors.SUCCESS, Colors.SUCCESS_HOVER))
        button_layout.addWidget(opslaan_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Styling voor inputs
        self.setStyleSheet(Styles.input_field())

    def on_gebruikersnaam_changed(self, text: str) -> None:
        """Auto-uppercase gebruikersnaam"""
        cursor_pos = self.gebruikersnaam_input.cursorPosition()
        self.gebruikersnaam_input.setText(text.upper())
        self.gebruikersnaam_input.setCursorPosition(cursor_pos)

    def on_reserve_changed(self, state: int) -> None:
        """Disable/enable startweek afhankelijk van reserve status"""
        is_reserve = state == Qt.CheckState.Checked.value
        self.startweek_combo.setEnabled(not is_reserve)
        if is_reserve:
            self.startweek_combo.setCurrentIndex(0)  # Geen

    def valideer_en_accept(self) -> None:
        """Valideer input en sluit dialog"""
        gebruikersnaam = self.gebruikersnaam_input.text().strip()

        if not gebruikersnaam:
            QMessageBox.warning(self, "Fout", "Gebruikersnaam is verplicht!")
            return

        # Valideer formaat: 3 letters + 4 cijfers
        if not re.match(r'^[A-Z]{3}[0-9]{4}$', gebruikersnaam):
            QMessageBox.warning(self, "Fout",
                                "Gebruikersnaam moet 3 hoofdletters + 4 cijfers zijn (bijv. AZE3601)!")
            return

        if not self.naam_input.text().strip():
            QMessageBox.warning(self, "Fout", "Volledige naam is verplicht!")
            return

        if not self.edit_mode and not self.wachtwoord_input.text():
            QMessageBox.warning(self, "Fout", "Wachtwoord is verplicht!")
            return

        if self.wachtwoord_input.text() and len(self.wachtwoord_input.text()) < 4:
            QMessageBox.warning(self, "Fout",
                                "Wachtwoord moet minimaal 4 tekens zijn!")
            return

        self.accept()

    def get_data(self) -> Dict[str, Any]:
        """Haal data op uit dialog"""
        return {
            'gebruikersnaam': self.gebruikersnaam_input.text().strip(),
            'volledige_naam': self.naam_input.text().strip(),
            'wachtwoord': self.wachtwoord_input.text(),
            'rol': 'planner' if self.rol_combo.currentText() == 'Planner' else 'teamlid',
            'is_reserve': 1 if self.reserve_check.isChecked() else 0,
            'startweek_typedienst': self.startweek_combo.currentIndex() if self.startweek_combo.currentIndex() > 0 else None
        }