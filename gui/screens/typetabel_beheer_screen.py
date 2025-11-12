#gui/screens/typetabel_beheer_screen.py

"""
Typetabel Beheer Scherm
Beheer van typetabel versies (concept/actief/archief)

v0.6.26.2: FASE 5 - Typetabel Pre-Activatie HR Validatie
"""
from typing import Callable, List, Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QMessageBox, QScrollArea, QFrame, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor
from database.connection import get_connection
from gui.styles import Styles, Colors, Fonts, Dimensions
from datetime import datetime, timedelta, date
from services.constraint_checker import ConstraintChecker, PlanningRegel, Violation
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

            valideer_btn = QPushButton("Valideer")
            valideer_btn.setStyleSheet(Styles.button_warning(Dimensions.BUTTON_HEIGHT_TINY))
            valideer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_TINY)
            valideer_btn.clicked.connect(lambda checked, v=versie: self.valideer_typetabel(v))  # type: ignore
            buttons_layout.addWidget(valideer_btn)

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

    def valideer_typetabel(self, versie: Dict[str, Any]):
        """
        Valideer concept typetabel VOOR activatie (FASE 5)

        Voert HR validatie uit en toont resultaten in dialog.
        Gebruiker kan dan beslissen of bewerking nodig is.
        """
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
            conn.close()

            if lege_cellen > 0:
                QMessageBox.warning(
                    self,
                    "Typetabel Incompleet",
                    f"Deze typetabel is nog niet compleet!\n\n"
                    f"Er zijn {lege_cellen} lege cellen.\n\n"
                    f"Vul eerst alle cellen in voordat je valideert."
                )
                return

            # Validatie 2: HR validatie
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

            try:
                result = self.pre_valideer_typetabel(versie)
            except Exception as e:
                print(f"Pre-validatie fout: {e}")
                import traceback
                traceback.print_exc()
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(
                    self,
                    "Validatie Fout",
                    f"Er is een fout opgetreden tijdens validatie:\n\n{e}\n\n"
                    f"Neem contact op met de beheerder."
                )
                return
            finally:
                QApplication.restoreOverrideCursor()

            # Toon resultaten dialog
            self.toon_validatie_resultaten_dialog(versie, result)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Fout", f"Kon validatie niet uitvoeren:\n{e}")

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

            conn.close()

            # Validatie 2: Pre-activatie HR validatie (FASE 5)
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

            try:
                result = self.pre_valideer_typetabel(versie)

                # DEBUG: Print eerste 20 dagen van eerste gebruiker
                print("\n" + "="*60)
                print("DEBUG: TYPETABEL SIMULATIE (eerste 20 dagen, eerste gebruiker)")
                print("="*60)

            except Exception as e:
                print(f"Pre-validatie fout: {e}")
                import traceback
                traceback.print_exc()
                result = {'total_violations': 0}  # Fout = geen blokkering
            finally:
                QApplication.restoreOverrideCursor()

            # Toon warning als violations gevonden
            if result['total_violations'] > 0:
                reply = self.toon_validatie_warning_dialog(versie, result)
                if reply == QMessageBox.StandardButton.No:
                    return  # Annuleren

            # Check of er al een actieve typetabel is
            conn = get_connection()
            cursor = conn.cursor()
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

    # ========================================================================
    # FASE 5: TYPETABEL PRE-ACTIVATIE HR VALIDATIE (v0.6.27)
    # ========================================================================

    def bereken_shift_slim(self, datum, actief_vanaf, aantal_weken, startweek,
                           typetabel_data, werkposten, shift_codes_map,
                           feestdagen) -> Optional[str]:
        """
        Bereken shift code voor een specifieke datum en gebruiker (SLIM - v0.6.14)

        Args:
            datum: Datum waarvoor shift berekend wordt
            actief_vanaf: Start datum typetabel
            aantal_weken: Aantal weken in typetabel cyclus
            startweek: Gebruiker's startweek in cyclus
            typetabel_data: {(week, dag): shift_type} - bijv. "V", "L", "N"
            werkposten: [(werkpost_id, prioriteit), ...] voor deze gebruiker
            shift_codes_map: {(werkpost_id, dag_type, shift_type): code}
            feestdagen: {datum_str: is_zondagsrust} - feestdagen mapping

        Returns:
            Concrete shift code (bijv. "7101") of None
        """
        # Bereken aantal dagen sinds actief_vanaf
        dagen_verschil = (datum - actief_vanaf).days

        # Bereken week in cyclus (0-based, dan +1 voor 1-based)
        # Met startweek offset
        week_in_cyclus = ((dagen_verschil // 7 + startweek - 1) % aantal_weken) + 1

        # Dag nummer (1=maandag, 7=zondag)
        dag_nummer = datum.isoweekday()

        # Haal shift_type op uit typetabel (bijv. "V", "L", "N", "dag")
        key = (week_in_cyclus, dag_nummer)
        shift_type = typetabel_data.get(key)

        if not shift_type:
            return None

        # CHECK FEESTDAG: Feestdagen worden behandeld als zondag voor shift codes
        datum_str = datum.isoformat()
        is_feestdag = datum_str in feestdagen

        # Bereken dag_type op basis van dag nummer (of feestdag!)
        if is_feestdag:
            # Feestdag = altijd zondag shift codes gebruiken (bijv. V -> 7701)
            dag_type = 'zondag'
        elif dag_nummer == 6:  # Zaterdag
            dag_type = 'zaterdag'
        elif dag_nummer == 7:  # Zondag
            dag_type = 'zondag'
        else:  # Ma-Vr
            dag_type = 'weekdag'

        # Check of dit een directe code is (RX, CX, T)
        # Deze codes moeten niet gemapt worden maar direct overgenomen
        shift_type_upper = shift_type.upper()
        if shift_type_upper in ['RX', 'CX', 'T']:
            # Directe code - return as-is
            return shift_type_upper

        # Normaliseer shift_type naar shift_codes formaat (V, L, N, D)
        # Typetabel kan "V", "v", "vroeg" bevatten
        shift_type_lower = shift_type.lower()
        if shift_type_lower in ['v', 'vroeg']:
            shift_type_normalized = 'vroeg'
        elif shift_type_lower in ['l', 'laat']:
            shift_type_normalized = 'laat'
        elif shift_type_lower in ['n', 'nacht']:
            shift_type_normalized = 'nacht'
        elif shift_type_lower in ['d', 'dag']:
            shift_type_normalized = 'dag'
        else:
            # Onbekend shift type - return None
            return None

        # Loop door werkposten (op prioriteit) om match te vinden
        for werkpost_id, _ in sorted(werkposten, key=lambda x: x[1]):
            lookup_key = (werkpost_id, dag_type, shift_type_normalized)
            shift_code = shift_codes_map.get(lookup_key)

            if shift_code:
                # Match gevonden!
                return shift_code

        # Geen match gevonden in shift_codes - return None
        return None

    def _load_hr_config(self) -> Dict[str, Any]:
        """Laad HR regels configuratie uit database met fallback defaults"""
        conn = get_connection()
        cursor = conn.cursor()

        # Haal actieve HR regels op
        cursor.execute("""
            SELECT naam, waarde, eenheid
            FROM hr_regels
            WHERE is_actief = 1
        """)

        # Maak config dictionary: naam -> waarde
        config = {}
        for row in cursor.fetchall():
            naam = row['naam']
            waarde = row['waarde']

            # Converteer waarde naar juiste type (int of float)
            if row['eenheid'] == 'dagen':
                config[naam] = int(waarde)
            elif row['eenheid'] == 'uren':
                config[naam] = float(waarde)
            elif row['eenheid'] == 'term':
                # Term-based regel: waarde kan REAL zijn in database maar moet string worden
                config[naam] = str(waarde) if waarde else ''
            else:  # 'periode' (week_definitie, weekend_definitie)
                config[naam] = str(waarde) if waarde else ''  # Zorg dat het string is

        conn.close()

        # Fallback defaults voor ontbrekende regels
        defaults = {
            'min_rust_uren': 12.0,
            'max_uren_week': 50.0,
            'max_werkdagen_cyclus': 19,
            'max_dagen_tussen_rx': 7,
            'max_werkdagen_reeks': 7,
            'max_weekends_achter_elkaar': 2,
            'week_definitie': 'ma-00:00|zo-23:59',
            'weekend_definitie': 'vr-22:00|ma-06:00'
        }

        # Vul ontbrekende waarden aan met defaults
        for key, default_value in defaults.items():
            if key not in config:
                config[key] = default_value

        return config

    def _load_shift_tijden(self) -> Dict[str, Dict[str, Any]]:
        """Laad shift tijden uit shift_codes en speciale_codes"""
        conn = get_connection()
        cursor = conn.cursor()

        shift_tijden = {}

        # Werkpost shift codes
        cursor.execute("""
            SELECT DISTINCT
                code,
                start_uur,
                eind_uur,
                shift_type
            FROM shift_codes
            WHERE code IS NOT NULL AND code != ''
        """)
        for row in cursor.fetchall():
            shift_tijden[row['code']] = {
                'start_uur': row['start_uur'],
                'eind_uur': row['eind_uur'],
                'shift_type': row['shift_type'],
                'telt_als_werkdag': True,  # Werkpost shifts tellen altijd als werkdag
                'reset_12u_rust': False,  # Werkpost shifts resetten 12u rust NIET (default)
                'breekt_werk_reeks': False  # Werkpost shifts breken reeks niet
            }

        # Speciale codes (geen tijden - RX, CX, verlof, etc.)
        cursor.execute("""
            SELECT
                code,
                term,
                telt_als_werkdag,
                reset_12u_rust,
                breekt_werk_reeks
            FROM speciale_codes
            WHERE code IS NOT NULL AND code != ''
        """)
        for row in cursor.fetchall():
            shift_tijden[row['code']] = {
                'start_uur': None,  # Speciale codes hebben geen vaste tijden
                'eind_uur': None,
                'term': row['term'],
                'telt_als_werkdag': row['telt_als_werkdag'] == 1,
                'reset_12u_rust': row['reset_12u_rust'] == 1,
                'breekt_werk_reeks': row['breekt_werk_reeks'] == 1
            }

        conn.close()
        return shift_tijden

    def _load_rode_lijnen(self) -> List[Dict[str, Any]]:
        """Laad rode lijnen periodes als lijst"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT start_datum, eind_datum, periode_nummer
            FROM rode_lijnen
            ORDER BY start_datum
        """)

        rode_lijnen = []
        for row in cursor.fetchall():
            # Strip timestamp indien aanwezig
            start_str = row['start_datum'].split('T')[0] if 'T' in row['start_datum'] else row['start_datum']
            eind_str = row['eind_datum'].split('T')[0] if 'T' in row['eind_datum'] else row['eind_datum']

            # Converteer naar date objecten
            start_datum = datetime.strptime(start_str, '%Y-%m-%d').date()
            eind_datum = datetime.strptime(eind_str, '%Y-%m-%d').date()

            rode_lijnen.append({
                'start_datum': start_datum,
                'eind_datum': eind_datum,
                'periode_nummer': row['periode_nummer']
            })

        conn.close()
        return rode_lijnen

    def _get_friendly_violation_name(self, type_name: str) -> str:
        """Vertaal violation type naar leesbare naam"""
        mapping = {
            'min_rust_12u': '12u rust tussen shifts',
            'max_uren_week': 'Max 50u per week',
            'max_werkdagen_cyclus': 'Max 19 werkdagen per cyclus',
            'max_dagen_tussen_rx': 'Max 7 dagen tussen rustdagen',
            'max_werkdagen_reeks': 'Max 7 opeenvolgende werkdagen',
            'max_weekends_achter_elkaar': 'Max weekends achter elkaar',
            'nacht_naar_vroeg': 'Nacht naar vroeg restrictie',
            'werkpost_onbekend': 'Onbekende werkpost koppeling'
        }
        return mapping.get(type_name, type_name)

    def _datum_naar_typetabel_locatie(self, datum: date, start_datum: date, aantal_weken: int) -> str:
        """
        Converteer datum naar typetabel locatie (Week X, Dagnaam)

        Args:
            datum: Datum om te converteren
            start_datum: Start datum van simulatie
            aantal_weken: Aantal weken in typetabel cyclus

        Returns:
            String zoals "Week 2, Dinsdag" of "Week 1, Zondag"
        """
        # Bereken dagen verschil
        dagen_verschil = (datum - start_datum).days

        # Bereken week in cyclus (1-based)
        week_in_cyclus = ((dagen_verschil // 7) % aantal_weken) + 1

        # Dag naam
        dag_namen = ['Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag', 'Zondag']
        dag_naam = dag_namen[datum.weekday()]

        return f"Week {week_in_cyclus}, {dag_naam}"

    def simuleer_typetabel_planning(self, versie_id: int, cycli: float = 2.5) -> List[PlanningRegel]:
        """
        Simuleer X cycli van typetabel voor THEORETISCH PATROON (1 dummy gebruiker)

        BELANGRIJK: Typetabel validatie is patroon-gebaseerd, NIET gebruiker-specifiek:
        - Geen feestdagen (theoretisch patroon, geen specifieke datums)
        - 1 dummy gebruiker (startweek = 1, id = 0)
        - Alle werkposten beschikbaar (voor shift code mapping)

        Args:
            versie_id: ID van typetabel versie
            cycli: Aantal cycli om te simuleren (default 2.5)

        Returns:
            List van PlanningRegel objecten voor HR validatie
        """
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Haal typetabel metadata op
        cursor.execute("""
            SELECT aantal_weken
            FROM typetabel_versies
            WHERE id = ?
        """, (versie_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return []

        aantal_weken = row['aantal_weken']

        # 2. Bereken simulatie lengte
        dagen_per_cyclus = aantal_weken * 7
        simulatie_dagen = int(dagen_per_cyclus * cycli)

        # 3. Haal typetabel data op
        cursor.execute("""
            SELECT week_nummer, dag_nummer, shift_type
            FROM typetabel_data
            WHERE versie_id = ?
        """, (versie_id,))

        typetabel_data = {}
        for row in cursor.fetchall():
            key = (row['week_nummer'], row['dag_nummer'])
            typetabel_data[key] = row['shift_type']

        # 4. Haal shift codes mapping op
        cursor.execute("""
            SELECT werkpost_id, dag_type, shift_type, code
            FROM shift_codes
            WHERE code IS NOT NULL AND code != ''
        """)

        shift_codes_map = {}
        for row in cursor.fetchall():
            key = (row['werkpost_id'], row['dag_type'], row['shift_type'])
            shift_codes_map[key] = row['code']

        # 5. Haal ALLE werkposten op (voor theoretische gebruiker)
        cursor.execute("""
            SELECT id
            FROM werkposten
            WHERE is_actief = 1
            ORDER BY id
        """)
        werkposten = [(row['id'], idx + 1) for idx, row in enumerate(cursor.fetchall())]

        conn.close()

        if not werkposten:
            # Geen werkposten = geen shift codes mogelijk
            return []

        # 6. Simuleer planning voor THEORETISCHE gebruiker
        planning_regels = []

        # Start op een theoretische MAANDAG (Week 1 Dag 1 moet maandag zijn!)
        # Gebruik eerste maandag van 2025 voor consistente simulatie
        start_datum = date(2025, 1, 6)  # 6 januari 2025 = maandag

        # Dummy gebruiker: id = 0, startweek = 1 (begin van cyclus)
        gebruiker_id = 0
        startweek = 1

        # Lege feestdagen dict (negeren voor theoretisch patroon)
        feestdagen = {}

        # Simuleer voor alle dagen
        for dagen_offset in range(simulatie_dagen):
            datum = start_datum + timedelta(days=dagen_offset)

            # Bereken shift code via bestaande logica (zonder feestdagen)
            shift_code = self.bereken_shift_slim(
                datum, start_datum, aantal_weken, startweek,
                typetabel_data, werkposten, shift_codes_map, feestdagen
            )

            if shift_code:
                planning_regels.append(PlanningRegel(
                    gebruiker_id=gebruiker_id,
                    datum=datum,
                    shift_code=shift_code,
                    is_goedgekeurd_verlof=False,
                    is_feestdag=False  # Altijd False voor theoretisch patroon
                ))

        return planning_regels

    def pre_valideer_typetabel(self, versie: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-activatie HR validatie (FASE 5)

        Args:
            versie: Typetabel versie dict

        Returns:
            {
                'total_violations': int,
                'errors': int,
                'warnings': int,
                'violations_by_type': {type_name: count},
                'violations_list': [Violation, ...],  # NIEUW: volledige lijst
                'simulatie_dagen': int,
                'aantal_cycli': float,
                'aantal_weken': int,  # NIEUW: voor week berekening
                'start_datum': date  # NIEUW: voor week berekening
            }
        """
        # 1. Simuleer planning (start op theoretische maandag in simulatie)
        planning_regels = self.simuleer_typetabel_planning(versie['id'], cycli=2.5)

        # Start datum = eerste datum in planning (theoretische maandag)
        start_datum = min(p.datum for p in planning_regels) if planning_regels else date.today()

        if not planning_regels:
            return {
                'total_violations': 0,
                'errors': 0,
                'warnings': 0,
                'violations_by_type': {},
                'violations_list': [],
                'simulatie_dagen': 0,
                'aantal_cycli': 2.5,
                'aantal_weken': versie['aantal_weken'],
                'start_datum': start_datum
            }

        # 2. Load HR config + shift tijden + rode lijnen
        hr_config = self._load_hr_config()
        shift_tijden = self._load_shift_tijden()
        rode_lijnen = self._load_rode_lijnen()

        # 3. Setup ConstraintChecker
        checker = ConstraintChecker(hr_config, shift_tijden)

        # 4. Run validaties op theoretisch patroon
        all_violations = []
        gebruiker_ids = set(p.gebruiker_id for p in planning_regels)

        for gebruiker_id in gebruiker_ids:
            gebruiker_planning = [p for p in planning_regels if p.gebruiker_id == gebruiker_id]

            results = checker.check_all(
                planning=gebruiker_planning,
                gebruiker_id=gebruiker_id,
                rode_lijnen=rode_lijnen
            )

            for result in results.values():
                all_violations.extend(result.violations)

        # 5. Count + aggregate (deduplicatie op object ID)
        seen_violation_ids = set()
        unique_violations = []
        violations_by_type = {}
        errors = 0
        warnings = 0

        for v in all_violations:
            violation_id = id(v)
            if violation_id in seen_violation_ids:
                continue  # Skip duplicaat

            seen_violation_ids.add(violation_id)
            unique_violations.append(v)

            if v.severity.value == 'error':
                errors += 1
            else:
                warnings += 1

            type_name = v.type.value
            violations_by_type[type_name] = violations_by_type.get(type_name, 0) + 1

        return {
            'total_violations': len(seen_violation_ids),
            'errors': errors,
            'warnings': warnings,
            'violations_by_type': violations_by_type,
            'violations_list': unique_violations,
            'simulatie_dagen': int(versie['aantal_weken'] * 7 * 2.5),
            'aantal_cycli': 2.5,
            'aantal_weken': versie['aantal_weken'],
            'start_datum': start_datum
        }

    def toon_validatie_resultaten_dialog(self, versie: Dict, result: Dict):
        """
        Toon HR validatie resultaten in informatieve dialog (FASE 5)

        Args:
            versie: Typetabel versie dict
            result: Validatie resultaat dict
        """
        msg_parts = [
            f"<h3>Typetabel: '{versie['versie_naam']}'</h3>",
            f"<p><b>HR Validatie Resultaten</b></p>",
            f"<p>Simulatie: {result['aantal_cycli']} cycli × {versie['aantal_weken']} weken = ",
            f"{result['simulatie_dagen']} dagen</p>",
            "<hr>",
        ]

        # Resultaat samenvatting
        if result['total_violations'] == 0:
            msg_parts.append(
                "<p style='color: #28a745; font-weight: bold;'>"
                "✓ Geen HR violations gevonden!"
                "</p>"
            )
            msg_parts.append(
                "<p>Deze typetabel voldoet aan alle HR regels en kan geactiveerd worden.</p>"
            )
        else:
            msg_parts.append(
                f"<p style='font-weight: bold;'>Gevonden violations:</p>"
            )
            msg_parts.append(
                f"<p><span style='color: #dc3545;'>✗ {result['errors']} errors</span> | "
                f"<span style='color: #ffc107;'>⚠ {result['warnings']} warnings</span></p>"
            )

            # Groepeer violations per type
            violations_by_type_details = {}
            for v in result['violations_list']:
                type_name = v.type.value
                if type_name not in violations_by_type_details:
                    violations_by_type_details[type_name] = []
                violations_by_type_details[type_name].append(v)

            # Toon breakdown per type met locaties
            if violations_by_type_details:
                msg_parts.append("<p><b>Breakdown per type:</b></p>")

                for type_name in sorted(violations_by_type_details.keys()):
                    violations = violations_by_type_details[type_name]
                    count = len(violations)
                    friendly_name = self._get_friendly_violation_name(type_name)

                    msg_parts.append(f"<p><b>{friendly_name}: {count}x</b></p><ul>")

                    # Toon eerste 10 locaties
                    max_show = 10
                    for i, v in enumerate(violations[:max_show]):
                        # Bepaal locatie string
                        if v.datum:
                            locatie = self._datum_naar_typetabel_locatie(
                                v.datum,
                                result['start_datum'],
                                result['aantal_weken']
                            )
                        elif v.datum_range:
                            # Voor range violations (bijv. max_uren_week)
                            start_locatie = self._datum_naar_typetabel_locatie(
                                v.datum_range[0],
                                result['start_datum'],
                                result['aantal_weken']
                            )
                            eind_locatie = self._datum_naar_typetabel_locatie(
                                v.datum_range[1],
                                result['start_datum'],
                                result['aantal_weken']
                            )
                            locatie = f"{start_locatie} t/m {eind_locatie}"
                        else:
                            locatie = "Onbekende locatie"

                        # Toon beschrijving (kort, eerste 80 chars)
                        beschrijving = v.beschrijving[:80] + "..." if len(v.beschrijving) > 80 else v.beschrijving

                        msg_parts.append(f"<li><i>{locatie}</i>: {beschrijving}</li>")

                    # Toon "... en X meer" als er meer zijn
                    if count > max_show:
                        msg_parts.append(f"<li><i>... en {count - max_show} meer</i></li>")

                    msg_parts.append("</ul>")

            # Advies
            msg_parts.append("<hr>")
            msg_parts.append(
                "<p><i><b>Let op:</b> Deze violations blokkeren activatie NIET, "
                "maar geven aan dat deze typetabel mogelijk problematisch is voor "
                "sommige gebruikers.</i></p>"
            )
            msg_parts.append(
                "<p><i>Overweeg om de typetabel te bewerken om violations te verminderen, "
                "of activeer deze typetabel als je zeker bent dat de violations acceptabel zijn.</i></p>"
            )

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Typetabel HR Validatie")
        msg_box.setText("".join(msg_parts))
        msg_box.setIcon(
            QMessageBox.Icon.Information if result['total_violations'] == 0
            else QMessageBox.Icon.Warning
        )
        msg_box.exec()

    def toon_validatie_warning_dialog(self, versie: Dict, result: Dict) -> int:
        """
        Toon pre-activatie validatie warning dialog

        Args:
            versie: Typetabel versie dict
            result: Validatie resultaat dict

        Returns:
            QMessageBox.StandardButton waarde (Yes/No)
        """
        msg_parts = [
            f"<b>Typetabel '{versie['versie_naam']}' Pre-Activatie Validatie</b><br><br>",
            f"Simulatie: {result['aantal_cycli']} cycli × {versie['aantal_weken']} weken = ",
            f"{result['simulatie_dagen']} dagen<br><br>",
            f"<b>Gevonden violations:</b><br>",
            f"<span style='color: #dc3545;'>✗ {result['errors']} errors</span> | ",
            f"<span style='color: #ffc107;'>⚠ {result['warnings']} warnings</span><br><br>",
        ]

        # Breakdown per type
        if result['violations_by_type']:
            msg_parts.append("<b>Breakdown:</b><br>")
            for type_name, count in sorted(result['violations_by_type'].items()):
                friendly_name = self._get_friendly_violation_name(type_name)
                msg_parts.append(f"• {friendly_name}: {count}x<br>")

        msg_parts.append("<br><i>Deze violations blokkeren NIET, maar geven aan ")
        msg_parts.append("dat deze typetabel mogelijk problematisch is.</i><br><br>")
        msg_parts.append("<b>Weet je zeker dat je deze typetabel wilt activeren?</b>")

        return QMessageBox.question(
            self,
            "Typetabel Validatie Waarschuwing",
            "".join(msg_parts),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Default = veilig
        )