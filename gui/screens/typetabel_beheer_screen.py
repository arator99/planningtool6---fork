#gui/screens/typetabel_beheer_screen.py

"""
Typetabel Beheer Scherm
Beheer van typetabel versies (concept/actief/archief)
"""
from typing import Callable, List, Dict, Any, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QMessageBox, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database.connection import get_connection
from gui.styles import Styles, Colors, Fonts, Dimensions
from datetime import datetime
import sqlite3


class TypetabelBeheerScreen(QWidget):
    """Scherm voor beheer van typetabel versies"""

    def __init__(self, router: Callable):
        super().__init__()
        self.router = router

        # Instance attributes
        self.actieve_versies: List[Dict[str, Any]] = []
        self.concept_versies: List[Dict[str, Any]] = []
        self.archief_versies: List[Dict[str, Any]] = []
        self.scroll_content: Optional[QWidget] = None

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialiseer UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE
        )
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Typetabel Beheer")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        terug_btn = QPushButton("Terug")
        terug_btn.setFixedSize(100, Dimensions.BUTTON_HEIGHT_NORMAL)
        terug_btn.setStyleSheet(Styles.button_secondary())
        terug_btn.clicked.connect(self.router)  # type: ignore
        header_layout.addWidget(terug_btn)

        layout.addLayout(header_layout)

        # Info box
        info = QLabel(
            "Beheer hier de typetabellen. Een typetabel is een herhalend patroon "
            "dat gebruikt wordt voor automatische planning generatie."
        )
        info.setWordWrap(True)
        info.setStyleSheet(Styles.info_box())
        layout.addWidget(info)

        # Scroll area voor versies
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(Dimensions.SPACING_LARGE)

        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll, 1)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        nieuwe_btn = QPushButton("+ Nieuwe Typetabel")
        nieuwe_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        nieuwe_btn.setStyleSheet(Styles.button_success())
        nieuwe_btn.clicked.connect(self.nieuwe_typetabel)  # type: ignore
        bottom_layout.addWidget(nieuwe_btn)

        kopieer_btn = QPushButton("+ Kopieer Actieve")
        kopieer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        kopieer_btn.setStyleSheet(Styles.button_primary())
        kopieer_btn.clicked.connect(self.kopieer_actieve)  # type: ignore
        bottom_layout.addWidget(kopieer_btn)

        layout.addLayout(bottom_layout)

    def load_data(self):
        """Laad alle typetabel versies"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Actieve versies
            cursor.execute("""
                SELECT * FROM typetabel_versies 
                WHERE status = 'actief'
                ORDER BY actief_vanaf DESC
            """)
            self.actieve_versies = cursor.fetchall()

            # Concept versies
            cursor.execute("""
                SELECT * FROM typetabel_versies 
                WHERE status = 'concept'
                ORDER BY laatste_wijziging DESC
            """)
            self.concept_versies = cursor.fetchall()

            # Archief versies
            cursor.execute("""
                SELECT * FROM typetabel_versies 
                WHERE status = 'archief'
                ORDER BY actief_tot DESC
                LIMIT 10
            """)
            self.archief_versies = cursor.fetchall()

            conn.close()

            self.display_versies()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon data niet laden:\n{e}")

    def display_versies(self):
        """Toon alle versies in scroll area"""
        # Clear bestaande content
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Actieve typetabellen
        if self.actieve_versies:
            actief_label = QLabel("Actieve Typetabel:")
            actief_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
            self.scroll_layout.addWidget(actief_label)

            for versie in self.actieve_versies:
                card = self.create_versie_card(versie, "actief")
                self.scroll_layout.addWidget(card)

        # Concept typetabellen
        if self.concept_versies:
            concept_label = QLabel("Concept Typetabellen:")
            concept_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
            self.scroll_layout.addWidget(concept_label)

            for versie in self.concept_versies:
                card = self.create_versie_card(versie, "concept")
                self.scroll_layout.addWidget(card)

        # Archief
        if self.archief_versies:
            archief_label = QLabel(f"Archief: ({len(self.archief_versies)} versies)")
            archief_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
            self.scroll_layout.addWidget(archief_label)

            for versie in self.archief_versies:
                card = self.create_versie_card(versie, "archief")
                self.scroll_layout.addWidget(card)

        # Als geen versies: info
        if not self.actieve_versies and not self.concept_versies:
            geen_data = QLabel("Nog geen typetabellen aangemaakt.\nKlik op '+ Nieuwe Typetabel' om te starten.")
            geen_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            geen_data.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: 40px;")
            self.scroll_layout.addWidget(geen_data)

        self.scroll_layout.addStretch()

    def create_versie_card(self, versie: Dict[str, Any], status_type: str) -> QFrame:
        """Maak card voor één typetabel versie"""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)

        # Styling op basis van status
        if status_type == "actief":
            bg_color = "#e8f5e9"
            border_color = "#4caf50"
        elif status_type == "concept":
            bg_color = "#fff3e0"
            border_color = "#ff9800"
        else:  # archief
            bg_color = "#f5f5f5"
            border_color = "#9e9e9e"

        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 15px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(Dimensions.SPACING_SMALL)

        # Header: Status badge + naam
        header = QHBoxLayout()

        if status_type == "actief":
            badge = QLabel("✓ ACTIEF")
            badge.setStyleSheet(f"color: {Colors.SUCCESS}; font-weight: bold;")
        elif status_type == "concept":
            badge = QLabel("⚙ CONCEPT")
            badge.setStyleSheet(f"color: {Colors.WARNING}; font-weight: bold;")
        else:
            badge = QLabel("📦 ARCHIEF")
            badge.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-weight: bold;")

        header.addWidget(badge)

        naam = QLabel(versie['versie_naam'])
        naam.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        header.addWidget(naam)

        header.addStretch()
        layout.addLayout(header)

        # Info lijn
        info_text = f"Weken: {versie['aantal_weken']}"

        if status_type == "actief" and versie['actief_vanaf']:
            info_text += f"  |  Actief sinds: {versie['actief_vanaf']}"
        elif status_type == "concept" and versie['laatste_wijziging']:
            # Parse ISO timestamp
            try:
                dt = datetime.fromisoformat(versie['laatste_wijziging'])
                dagen_geleden = (datetime.now() - dt).days
                if dagen_geleden == 0:
                    tijd_str = "vandaag"
                elif dagen_geleden == 1:
                    tijd_str = "gisteren"
                else:
                    tijd_str = f"{dagen_geleden} dagen geleden"
                info_text += f"  |  Gewijzigd: {tijd_str}"
            except (ValueError, TypeError):
                pass

        info_label = QLabel(info_text)
        info_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(info_label)

        # Tel gebruikers (alleen voor actief)
        if status_type == "actief":
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM gebruikers 
                    WHERE is_actief = 1 AND is_reserve = 0 AND gebruikersnaam != 'admin'
                """)
                gebruikers_cnt = cursor.fetchone()['cnt']
                conn.close()

                if gebruikers_cnt > 0:
                    users_label = QLabel(f"Gebruikers: {gebruikers_cnt} personen")
                    users_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: {Fonts.SIZE_SMALL}px;")
                    layout.addWidget(users_label)
            except Exception:
                pass  # Silently fail on DB errors

        # Opmerking (indien aanwezig)
        if versie['opmerking']:
            opmerking = QLabel(versie['opmerking'])
            opmerking.setWordWrap(True)
            opmerking.setStyleSheet(
                f"color: {Colors.TEXT_SECONDARY}; font-style: italic; font-size: {Fonts.SIZE_SMALL}px;")
            layout.addWidget(opmerking)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(Dimensions.SPACING_SMALL)

        if status_type == "actief":
            bekijk_btn = QPushButton("Bekijken")
            bekijk_btn.setStyleSheet(Styles.button_secondary(Dimensions.BUTTON_HEIGHT_TINY))
            bekijk_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            bekijk_btn.clicked.connect(
                lambda checked, v=versie: self.bekijk_typetabel(v, readonly=True))  # type: ignore
            buttons_layout.addWidget(bekijk_btn)

            kopieer_btn = QPushButton("Kopiëren")
            kopieer_btn.setStyleSheet(Styles.button_primary(Dimensions.BUTTON_HEIGHT_TINY))
            kopieer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            kopieer_btn.clicked.connect(lambda checked, v=versie: self.kopieer_versie(v))  # type: ignore
            buttons_layout.addWidget(kopieer_btn)

        elif status_type == "concept":
            bewerk_btn = QPushButton("Bewerken")
            bewerk_btn.setStyleSheet(Styles.button_primary(Dimensions.BUTTON_HEIGHT_TINY))
            bewerk_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            bewerk_btn.clicked.connect(lambda checked, v=versie: self.bewerk_typetabel(v))  # type: ignore
            buttons_layout.addWidget(bewerk_btn)

            activeer_btn = QPushButton("Activeren")
            activeer_btn.setStyleSheet(Styles.button_success(Dimensions.BUTTON_HEIGHT_TINY))
            activeer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            activeer_btn.clicked.connect(lambda checked, v=versie: self.activeer_versie(v))  # type: ignore
            buttons_layout.addWidget(activeer_btn)

            verwijder_btn = QPushButton("Verwijderen")
            verwijder_btn.setStyleSheet(Styles.button_danger(Dimensions.BUTTON_HEIGHT_TINY))
            verwijder_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            verwijder_btn.clicked.connect(lambda checked, v=versie: self.verwijder_versie(v))  # type: ignore
            buttons_layout.addWidget(verwijder_btn)

        else:  # archief
            bekijk_btn = QPushButton("Bekijken")
            bekijk_btn.setStyleSheet(Styles.button_secondary(Dimensions.BUTTON_HEIGHT_TINY))
            bekijk_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            bekijk_btn.clicked.connect(
                lambda checked, v=versie: self.bekijk_typetabel(v, readonly=True))  # type: ignore
            buttons_layout.addWidget(bekijk_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        return card

    def nieuwe_typetabel(self):
        """Maak nieuwe typetabel concept"""
        from gui.dialogs.typetabel_dialogs import NieuweTypetabelDialog

        dialog = NieuweTypetabelDialog(self)
        if dialog.exec():
            data = dialog.get_data()

            try:
                conn = get_connection()
                cursor = conn.cursor()

                # Maak nieuwe versie
                cursor.execute("""
                    INSERT INTO typetabel_versies 
                    (versie_naam, aantal_weken, status, laatste_wijziging, opmerking)
                    VALUES (?, ?, 'concept', ?, ?)
                """, (
                    data['naam'],
                    data['aantal_weken'],
                    datetime.now().isoformat(),
                    data.get('opmerking', '')
                ))

                nieuwe_id = cursor.lastrowid

                # Initialiseer lege data (alle weken, alle dagen)
                for week in range(1, data['aantal_weken'] + 1):
                    for dag in range(1, 8):  # Ma-Zo
                        cursor.execute("""
                            INSERT INTO typetabel_data (versie_id, week_nummer, dag_nummer, shift_type)
                            VALUES (?, ?, ?, NULL)
                        """, (nieuwe_id, week, dag))

                conn.commit()
                conn.close()

                QMessageBox.information(
                    self,
                    "Succes",
                    f"Typetabel '{data['naam']}' aangemaakt!\n\n"
                    f"Je kan deze nu bewerken om het patroon in te vullen."
                )

                self.load_data()

            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Fout", f"Kon typetabel niet aanmaken:\n{e}")

    def kopieer_actieve(self):
        """Kopieer actieve typetabel naar nieuw concept"""
        if not self.actieve_versies:
            QMessageBox.warning(self, "Geen Actieve Typetabel", "Er is geen actieve typetabel om te kopiëren.")
            return

        # Neem eerste actieve (zou er maar 1 moeten zijn)
        self.kopieer_versie(self.actieve_versies[0])

    def kopieer_versie(self, versie: Dict[str, Any]):
        """Kopieer een versie naar nieuw concept"""
        nieuwe_naam = f"{versie['versie_naam']} - Kopie"

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Maak nieuwe versie
            cursor.execute("""
                INSERT INTO typetabel_versies 
                (versie_naam, aantal_weken, status, laatste_wijziging, opmerking)
                VALUES (?, ?, 'concept', ?, ?)
            """, (
                nieuwe_naam,
                versie['aantal_weken'],
                datetime.now().isoformat(),
                f"Gekopieerd van '{versie['versie_naam']}'"
            ))

            nieuwe_id = cursor.lastrowid

            # Kopieer alle data
            cursor.execute("""
                INSERT INTO typetabel_data (versie_id, week_nummer, dag_nummer, shift_type)
                SELECT ?, week_nummer, dag_nummer, shift_type
                FROM typetabel_data
                WHERE versie_id = ?
            """, (nieuwe_id, versie['id']))

            conn.commit()
            conn.close()

            QMessageBox.information(
                self,
                "Gekopieerd",
                f"Typetabel gekopieerd als '{nieuwe_naam}'!"
            )

            self.load_data()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon niet kopiëren:\n{e}")

    def bewerk_typetabel(self, versie: Dict[str, Any]):
        """Open editor voor typetabel"""
        from gui.dialogs.typetabel_editor_dialog import TypetabelEditorDialog

        dialog = TypetabelEditorDialog(self, versie)
        dialog.exec()

        # Reload na sluiten (ongeacht of opgeslagen)
        self.load_data()

    def bekijk_typetabel(self, versie: Dict[str, Any], readonly: bool = True):
        """Bekijk typetabel (read-only)"""
        from gui.dialogs.typetabel_editor_dialog import TypetabelEditorDialog

        dialog = TypetabelEditorDialog(self, versie, readonly=readonly)
        dialog.exec()

    def activeer_versie(self, versie: Dict[str, Any]):
        """Activeer concept typetabel"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Validatie 1: Check of typetabel compleet is (geen lege cellen)
            cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM typetabel_data
                WHERE versie_id = ? AND (shift_type IS NULL OR shift_type = '')
            """, (versie['id'],))

            lege_cellen = cursor.fetchone()['cnt']

            if lege_cellen > 0:
                QMessageBox.warning(
                    self,
                    "Typetabel Incompleet",
                    f"Deze typetabel is nog niet compleet!\n\n"
                    f"Er zijn {lege_cellen} lege cellen.\n\n"
                    f"Vul eerst alle cellen in voordat je activeert."
                )
                conn.close()
                return

            # Check of er al een actieve typetabel is
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM typetabel_versies WHERE status = 'actief'
            """)
            heeft_actieve = cursor.fetchone()['cnt'] > 0

            conn.close()

            # Toon activatie dialog
            from gui.dialogs.typetabel_dialogs import ActiveerTypetabelDialog

            dialog = ActiveerTypetabelDialog(self, versie, heeft_actieve)
            if not dialog.exec():
                return

            # Haal gekozen datum op
            actief_vanaf = dialog.get_datum()

            # Voer activatie uit
            conn = get_connection()
            cursor = conn.cursor()

            # Stap 1: Archiveer bestaande actieve typetabel(len)
            if heeft_actieve:
                cursor.execute("""
                    UPDATE typetabel_versies
                    SET status = 'archief', actief_tot = ?
                    WHERE status = 'actief'
                """, (datetime.now().date().isoformat(),))

            # Stap 2: Activeer nieuwe typetabel
            cursor.execute("""
                UPDATE typetabel_versies
                SET status = 'actief', actief_vanaf = ?
                WHERE id = ?
            """, (actief_vanaf, versie['id']))

            conn.commit()
            conn.close()

            QMessageBox.information(
                self,
                "Geactiveerd",
                f"Typetabel '{versie['versie_naam']}' is geactiveerd!\n\n"
                f"Actief vanaf: {actief_vanaf}\n\n"
                f"Deze typetabel wordt nu gebruikt bij auto-generatie."
            )

            # Reload data om nieuwe status te tonen
            self.load_data()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon niet activeren:\n{e}")

    def verwijder_versie(self, versie: Dict[str, Any]):
        """Verwijder concept typetabel"""
        reply = QMessageBox.question(
            self,
            "Bevestiging",
            f"Weet je zeker dat je '{versie['versie_naam']}' wilt verwijderen?\n\n"
            f"Dit kan niet ongedaan gemaakt worden!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()

                # DELETE CASCADE zorgt dat typetabel_data ook verwijderd wordt
                cursor.execute("DELETE FROM typetabel_versies WHERE id = ?", (versie['id'],))

                conn.commit()
                conn.close()

                QMessageBox.information(self, "Verwijderd", "Typetabel is verwijderd.")
                self.load_data()

            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Fout", f"Kon niet verwijderen:\n{e}")