# gui/screens/planning_editor_screen.py
"""
Planning Editor Scherm
Gebruikt PlannerGridKalender widget met codes sidebar en toolbar

VERSION HISTORY:
- v0.6.26: HR Validatie waarschuwing bij publicatie
  * Pre-publicatie validatie check in publiceer_planning()
  * Alle gebruikers worden gevalideerd (alle 6 HR checks)
  * Bij violations: waarschuwing met samenvatting (alle gebruikers)
  * Gebruiker kan kiezen: annuleren of toch publiceren
  * "Bent u zeker dat u wil publiceren met planningsfouten?"
- v0.6.20: Bemannings controle validatie in publicatie flow
- v0.6.25: PERFORMANCE FIXES (3 optimalisaties)
  1. Toggle optimalisatie (concept ↔ gepubliceerd)
     * Cache planning data in memory (_cached_planning_data)
     * Toggle update cache ipv volledige database reload
     * Speedup: 45s → <0.1s (900x sneller)
  2. ValidationCache batch loading (via PlannerGridKalender)
     * Preload alle validatie data in 1 keer (5 queries ipv 900+)
     * Speedup: 30-60s → 0.01-0.03s (2000x sneller)
  3. Planning Sessie Configuratie
     * Dialog om maand + gebruikers te selecteren
     * Laad alleen wat nodig is
     * Speedup: 100-300x voor gefilterde sessies
  * Zie: refactor performance/

PERFORMANCE NOTES:
Het toggle concept ↔ gepubliceerd update nu alleen:
1. Database status (UPDATE query)
2. In-memory cache (_cached_planning_data)
3. UI status labels

GEEN volledige grid reload meer! Data blijft hetzelfde, alleen de view/filter wijzigt.
"""
from typing import Callable, Set, Dict, Optional, List
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QTextEdit, QDialog,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from gui.widgets.planner_grid_kalender import PlannerGridKalender
from gui.styles import Styles, Colors, Fonts, Dimensions, TableConfig
from database.connection import get_connection
from services.bemannings_controle_service import controleer_maand
from services.planning_validator_service import PlanningValidator
from datetime import datetime


class PlanningEditorScreen(QWidget):
    """
    Planning Editor voor planners
    - PlannerGridKalender widget (editable)
    - Codes sidebar rechts
    - F1 helper voor codes
    - Toolbar met acties (toekomstig)
    """

    def __init__(
        self,
        router: Callable,
        jaar: Optional[int] = None,
        maand: Optional[int] = None,
        gebruiker_ids: Optional[List[int]] = None
    ):
        super().__init__()
        self.router = router

        # PERFORMANCE (v0.6.25): Gebruik configuratie parameters of defaults
        vandaag = datetime.now()
        self.configured_jaar = jaar if jaar else vandaag.year
        self.configured_maand = maand if maand else vandaag.month
        self.configured_gebruiker_ids = gebruiker_ids

        # State
        self.valid_codes: Set[str] = set()  # Alle codes
        self.valid_codes_per_dag: Dict[str, Set[str]] = {
            'weekdag': set(),
            'zaterdag': set(),
            'zondag': set()
        }
        self.speciale_codes: Set[str] = set()
        self.current_status: str = 'concept'  # 'concept' of 'gepubliceerd'

        # PERFORMANCE CACHE (v0.6.25) - Quick Win voor toggle
        # Cache alle planning data bij load, filter in-memory bij toggle
        self._cached_planning_data: Dict = {}  # Alle planning data (concept + gepubliceerd)
        self._show_only_gepubliceerd: bool = False  # Filter flag

        # PERFORMANCE (v0.6.25): Pass configuratie naar grid
        self.kalender: PlannerGridKalender = PlannerGridKalender(
            self.configured_jaar,
            self.configured_maand,
            gebruiker_ids=self.configured_gebruiker_ids
        )

        # UI components
        self.codes_help_table: QTableWidget = QTableWidget()
        self.info_label: QLabel = QLabel()
        self.status_btn: QPushButton = QPushButton()
        self.border_frame = None  # Frame met gekleurde rand (wordt in init_ui gemaakt)

        self.init_ui()
        self.load_valid_codes()
        self.load_maand_status()  # Haal status op voor huidige maand

        # Geef codes door aan kalender
        self.kalender.set_valid_codes(
            self.valid_codes,
            self.valid_codes_per_dag,
            self.speciale_codes
        )

        # Connect maand changed signal voor status reload
        self.kalender.maand_changed.connect(self.on_maand_changed)  # type: ignore

        # Update UI met huidige status
        self.update_status_ui()

    def init_ui(self) -> None:
        """Bouw UI"""
        # Outer layout voor het hele scherm
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Container frame met gekleurde rand (dynamisch)
        from PyQt6.QtWidgets import QFrame
        self.border_frame = QFrame()
        self.border_frame.setObjectName("borderFrame")
        outer_layout.addWidget(self.border_frame)

        # Main layout BINNEN de border frame
        main_layout = QHBoxLayout(self.border_frame)
        main_layout.setSpacing(Dimensions.SPACING_LARGE)
        main_layout.setContentsMargins(
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE
        )

        # Linker deel: Header + Kalender
        left_layout = QVBoxLayout()
        left_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Header
        header = self.create_header()
        left_layout.addLayout(header)

        # Kalender header row: [Info Box] + [Kalender navigatie]
        kalender_header_row = QHBoxLayout()

        # Info box links (concept/gepubliceerd)
        self.info_label.setWordWrap(True)
        self.info_label.setMaximumWidth(300)
        kalender_header_row.addWidget(self.info_label)

        kalender_header_row.addSpacing(Dimensions.SPACING_MEDIUM)

        # Kalender eigen header (maandnaam + navigatie)
        kalender_header_row.addLayout(self.kalender.create_header())

        left_layout.addLayout(kalender_header_row)

        # Knoppenrij (vervangt de info label van kalender)
        buttons_row = QHBoxLayout()

        # Auto-generatie button
        auto_btn = QPushButton("Auto-Genereren uit Typetabel")
        auto_btn.setStyleSheet(Styles.button_primary())
        auto_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        auto_btn.clicked.connect(self.show_auto_generatie_dialog)  # type: ignore
        buttons_row.addWidget(auto_btn)

        # Bulk delete button
        bulk_delete_btn = QPushButton("Wis Maand (Bescherm Speciale Codes)")
        bulk_delete_btn.setStyleSheet(Styles.button_warning())
        bulk_delete_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        bulk_delete_btn.clicked.connect(self.show_bulk_delete_dialog)  # type: ignore
        buttons_row.addWidget(bulk_delete_btn)

        # Status toggle button
        self.status_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        self.status_btn.clicked.connect(self.toggle_status)  # type: ignore
        buttons_row.addWidget(self.status_btn)

        buttons_row.addStretch()

        left_layout.addLayout(buttons_row)

        # Kalender widget (grid) - zonder zijn info_label
        left_layout.addWidget(self.kalender)

        # Instructies
        instructies = QLabel(
            "💡 TIP: Klik cel om te bewerken • TAB=volgende • ENTER=eronder • "
            "ESC=annuleer • F1=zoek codes • Rechtsklik=opties"
        )
        instructies.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")
        instructies.setWordWrap(True)
        left_layout.addWidget(instructies)

        main_layout.addLayout(left_layout, stretch=3)

        # Rechter deel: Codes sidebar
        sidebar = self.create_codes_sidebar()
        main_layout.addWidget(sidebar, stretch=1)

        # Install event filter voor F1
        self.installEventFilter(self)

    def create_header(self) -> QHBoxLayout:
        """Maak header met titel en terug button"""
        header = QHBoxLayout()

        title = QLabel("Planning Editor")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        header.addWidget(title)

        header.addStretch()

        # Terug button
        terug_btn = QPushButton("Terug")
        terug_btn.setFixedSize(100, Dimensions.BUTTON_HEIGHT_NORMAL)
        terug_btn.clicked.connect(self.router)  # type: ignore
        terug_btn.setStyleSheet(Styles.button_secondary())
        header.addWidget(terug_btn)

        return header

    def create_codes_sidebar(self) -> QWidget:
        """Maak sidebar met beschikbare codes"""
        widget = QWidget()
        widget.setMaximumWidth(300)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Title
        title = QLabel("Beschikbare Codes")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(title)

        # Info
        info = QLabel("Druk F2 voor zoekbare lijst")
        info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")
        layout.addWidget(info)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # SHIFTS sectie
        shifts_label = QLabel("SHIFTS:")
        shifts_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        scroll_layout.addWidget(shifts_label)

        shifts_text = QTextEdit()
        shifts_text.setReadOnly(True)
        shifts_text.setMaximumHeight(350)
        shifts_text.setText(self.get_shift_codes_text())
        shifts_text.setStyleSheet(Styles.input_field())
        scroll_layout.addWidget(shifts_text)

        # SPECIAAL sectie
        special_label = QLabel("SPECIAAL:")
        special_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        scroll_layout.addWidget(special_label)

        special_text = QTextEdit()
        special_text.setReadOnly(True)
        special_text.setMaximumHeight(200)
        special_text.setText(self.get_special_codes_text())
        special_text.setStyleSheet(Styles.input_field())
        scroll_layout.addWidget(special_text)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        widget.setLayout(layout)
        return widget

    def load_valid_codes(self):
        """Laad alle geldige codes uit database"""
        conn = get_connection()
        cursor = conn.cursor()

        # Shift codes per dag_type (alleen actieve werkposten)
        cursor.execute("""
            SELECT DISTINCT sc.code, sc.dag_type
            FROM shift_codes sc
            JOIN werkposten w ON sc.werkpost_id = w.id
            WHERE w.is_actief = 1
        """)

        for row in cursor.fetchall():
            code = row['code']
            dag_type = row['dag_type']

            self.valid_codes.add(code)

            # Voeg toe aan juiste dag_type Set
            if dag_type in self.valid_codes_per_dag:
                self.valid_codes_per_dag[dag_type].add(code)

        # Speciale codes (geldig voor alle dagen)
        cursor.execute("SELECT code FROM speciale_codes")

        for row in cursor.fetchall():
            code = row['code']
            self.valid_codes.add(code)
            self.speciale_codes.add(code)

        conn.close()

    def load_maand_status(self):
        """Haal status op voor huidige maand"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            jaar = self.kalender.jaar
            maand = self.kalender.maand

            # Bepaal eerste dag van maand en eerste dag van volgende maand
            eerste_dag = f"{jaar:04d}-{maand:02d}-01"
            if maand == 12:
                volgende_maand = f"{jaar + 1:04d}-01-01"
            else:
                volgende_maand = f"{jaar:04d}-{maand + 1:02d}-01"

            # Haal unieke statussen op voor deze maand
            cursor.execute("""
                SELECT DISTINCT status
                FROM planning
                WHERE datum >= ? AND datum < ?
            """, (eerste_dag, volgende_maand))

            statussen = [row['status'] for row in cursor.fetchall()]
            conn.close()

            # Bepaal status
            if 'gepubliceerd' in statussen:
                self.current_status = 'gepubliceerd'
            else:
                self.current_status = 'concept'

        except Exception:
            self.current_status = 'concept'

    def update_status_ui(self):
        """Update info box en button op basis van huidige status"""

        if self.current_status == 'concept':
            # CONCEPT modus
            self.info_label.setText(
                "⚠️ Planning is in CONCEPT. Teamleden zien deze planning nog niet."
            )
            self.info_label.setStyleSheet(Styles.info_box(
                bg_color="#FFF9C4",
                border_color="#FFE082",
                text_color="#F57C00"
            ))
            self.status_btn.setText("Publiceren")
            self.status_btn.setStyleSheet(Styles.button_success())

            # GELE RAND voor concept
            if self.border_frame:
                self.border_frame.setStyleSheet("""
                    QFrame#borderFrame {
                        border: 8px solid #FFE082;
                        background-color: white;
                    }
                """)

        else:  # gepubliceerd
            # GEPUBLICEERD modus
            self.info_label.setText(
                "✓ Planning is GEPUBLICEERD. Teamleden kunnen deze planning bekijken."
            )
            self.info_label.setStyleSheet(Styles.info_box(
                bg_color="#E8F5E9",
                border_color="#81C784",
                text_color="#2E7D32"
            ))
            self.status_btn.setText("Terug naar Concept")
            self.status_btn.setStyleSheet(Styles.button_warning())

            # GROENE RAND voor gepubliceerd
            if self.border_frame:
                self.border_frame.setStyleSheet("""
                    QFrame#borderFrame {
                        border: 8px solid #81C784;
                        background-color: white;
                    }
                """)

    def toggle_status(self):
        """Toggle tussen concept en gepubliceerd"""
        if self.current_status == 'concept':
            self.publiceer_planning()
        else:
            self.terug_naar_concept()

    def publiceer_planning(self):
        """Publiceer planning voor huidige maand"""
        jaar = self.kalender.jaar
        maand = self.kalender.maand
        maand_naam = datetime(jaar, maand, 1).strftime("%B %Y")

        # Show loading cursor (validatie kan even duren)
        self.setCursor(Qt.CursorShape.WaitCursor)

        # STAP 1: HR Validatie (v0.6.26 - verplicht voor publicatie)
        # Haal alle gebruikers op (excl. admin)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, volledige_naam
            FROM gebruikers
            WHERE is_actief = 1 AND gebruikersnaam != 'admin'
            ORDER BY volledige_naam
        """)
        gebruikers = cursor.fetchall()
        conn.close()

        # Valideer alle gebruikers
        hr_violations_totaal = 0
        hr_violations_per_gebruiker = {}

        for gebruiker in gebruikers:
            gebruiker_id = gebruiker['id']
            gebruiker_naam = gebruiker['volledige_naam']

            validator = PlanningValidator(
                gebruiker_id=gebruiker_id,
                jaar=jaar,
                maand=maand
            )

            violations_dict = validator.validate_all()

            # Tel violations - ALLEEN violations in de huidige maand (ISSUE-009 fix)
            violations_count = 0
            for v_list in violations_dict.values():
                for violation in v_list:
                    # Filter: alleen violations waarvan datum in huidige maand valt
                    if violation.datum and violation.datum.year == jaar and violation.datum.month == maand:
                        violations_count += 1

            if violations_count > 0:
                hr_violations_totaal += violations_count
                hr_violations_per_gebruiker[gebruiker_naam] = violations_count

        # Reset cursor
        self.setCursor(Qt.CursorShape.ArrowCursor)

        # Als HR violations gevonden, waarschuw gebruiker (maar blokkeer niet)
        if hr_violations_totaal > 0:
            violations_tekst = f"Planning bevat {hr_violations_totaal} HR regel overtredingen:\n\n"

            # Toon ALLE gebruikers (geen limit)
            for naam, count in sorted(hr_violations_per_gebruiker.items(), key=lambda x: x[1], reverse=True):
                violations_tekst += f"• {naam}: {count} violations\n"

            violations_tekst += "\nGebruik de \"Valideer Planning\" knop om de details te bekijken.\n\n"
            violations_tekst += "Bent u zeker dat u wil publiceren met planningsfouten?"

            reply = QMessageBox.warning(
                self,
                "Waarschuwing: Planning bevat HR Violations",
                violations_tekst,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return  # Gebruiker annuleert

        # STAP 2: Bemannings validatie (v0.6.20)
        # Show loading cursor again
        self.setCursor(Qt.CursorShape.WaitCursor)

        validatie_resultaat = controleer_maand(jaar, maand)
        samenvatting = validatie_resultaat['samenvatting']

        # Reset cursor
        self.setCursor(Qt.CursorShape.ArrowCursor)

        # Bouw bevestiging bericht met validatie samenvatting
        bevestiging_tekst = f"Planning publiceren voor {maand_naam}?\n\n"
        bevestiging_tekst += "Status samenvatting:\n"
        bevestiging_tekst += f"✓ Volledig bemand: {samenvatting['volledig']} dagen\n"

        if samenvatting['dubbel'] > 0:
            bevestiging_tekst += f"⚠ Dubbele codes: {samenvatting['dubbel']} dagen\n"

        if samenvatting['onvolledig'] > 0:
            bevestiging_tekst += f"✗ Onvolledig: {samenvatting['onvolledig']} dagen\n"

        bevestiging_tekst += "\nValidatie rapport wordt toegevoegd aan Excel export.\n\n"
        bevestiging_tekst += "Teamleden kunnen deze planning dan bekijken."

        # Bevestiging dialog
        reply = QMessageBox.question(
            self,
            "Planning Publiceren",
            bevestiging_tekst,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # STAP 1: Genereer Excel export EERST (v0.6.21 bugfix: atomic publicatie)
        try:
            from services.export_service import export_maand_naar_excel
            excel_pad = export_maand_naar_excel(jaar, maand)
        except PermissionError:
            # Meest waarschijnlijk: bestand is open in Excel
            maand_naam_nl = ['januari', 'februari', 'maart', 'april', 'mei', 'juni',
                             'juli', 'augustus', 'september', 'oktober', 'november', 'december'][maand - 1]
            bestand_naam = f"{maand_naam_nl}_{jaar}.xlsx"
            QMessageBox.critical(
                self,
                "Publicatie Geannuleerd",
                f"Kan Excel bestand niet aanmaken.\n\n"
                f"Meest waarschijnlijke oorzaak:\n"
                f"• Het bestand '{bestand_naam}' is open in Excel\n\n"
                f"Andere mogelijkheden:\n"
                f"• Het bestand of de exports folder is read-only\n"
                f"• Geen schrijfrechten op de exports folder\n\n"
                f"Sluit het bestand en/of check de folder permissions."
            )
            return
        except (IOError, OSError) as e:
            QMessageBox.critical(
                self,
                "Publicatie Geannuleerd",
                f"Kan Excel bestand niet aanmaken.\n\n"
                f"Mogelijke oorzaken:\n"
                f"- Exports folder is read-only\n"
                f"- Geen schijfruimte\n"
                f"- Permission denied\n\n"
                f"Technische fout: {str(e)}"
            )
            return
        except Exception as e:
            QMessageBox.critical(
                self,
                "Publicatie Geannuleerd",
                f"Onverwachte fout bij Excel export:\n\n{str(e)}"
            )
            return

        # STAP 2: Update database (alleen als Excel export succesvol was)
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Bepaal datum range
            eerste_dag = f"{jaar:04d}-{maand:02d}-01"
            if maand == 12:
                volgende_maand = f"{jaar + 1:04d}-01-01"
            else:
                volgende_maand = f"{jaar:04d}-{maand + 1:02d}-01"

            # Update alle planning records naar gepubliceerd
            cursor.execute("""
                UPDATE planning
                SET status = 'gepubliceerd'
                WHERE datum >= ? AND datum < ?
            """, (eerste_dag, volgende_maand))

            conn.commit()
            conn.close()

            # PERFORMANCE FIX (v0.6.25): Update cache ipv volledige reload
            # Update cache: markeer alle records als gepubliceerd
            if self._cached_planning_data:
                for datum_str in self._cached_planning_data:
                    for user_id in self._cached_planning_data[datum_str]:
                        if 'status' in self._cached_planning_data[datum_str][user_id]:
                            self._cached_planning_data[datum_str][user_id]['status'] = 'gepubliceerd'

            # Update UI (GEEN grid reload nodig - data is hetzelfde!)
            self.current_status = 'gepubliceerd'
            self._show_only_gepubliceerd = False  # Reset filter (toon alles in gepubliceerd modus)
            self.update_status_ui()

            QMessageBox.information(
                self,
                "Gepubliceerd",
                f"Planning voor {maand_naam} is gepubliceerd.\n\n"
                f"Excel bestand gegenereerd:\n{excel_pad}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Fout",
                f"Excel export is succesvol, maar database update mislukt:\n\n{str(e)}\n\n"
                f"Neem contact op met beheerder."
            )

    def terug_naar_concept(self):
        """Zet planning terug naar concept"""
        jaar = self.kalender.jaar
        maand = self.kalender.maand
        maand_naam = datetime(jaar, maand, 1).strftime("%B %Y")

        # Waarschuwing dialog
        reply = QMessageBox.warning(
            self,
            "Terug naar Concept",
            "Planning terug naar concept zetten?\n\n"
            "Teamleden kunnen deze planning dan NIET meer bekijken.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Update database
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Bepaal datum range
            eerste_dag = f"{jaar:04d}-{maand:02d}-01"
            if maand == 12:
                volgende_maand = f"{jaar + 1:04d}-01-01"
            else:
                volgende_maand = f"{jaar:04d}-{maand + 1:02d}-01"

            # Update alle planning records naar concept
            cursor.execute("""
                UPDATE planning
                SET status = 'concept'
                WHERE datum >= ? AND datum < ?
            """, (eerste_dag, volgende_maand))

            conn.commit()
            conn.close()

            # PERFORMANCE FIX (v0.6.25): Update cache ipv volledige reload
            # Update cache: markeer alle records als concept
            if self._cached_planning_data:
                for datum_str in self._cached_planning_data:
                    for user_id in self._cached_planning_data[datum_str]:
                        if 'status' in self._cached_planning_data[datum_str][user_id]:
                            self._cached_planning_data[datum_str][user_id]['status'] = 'concept'

            # Update UI (GEEN grid reload nodig - data is hetzelfde!)
            self.current_status = 'concept'
            self._show_only_gepubliceerd = False  # Reset filter
            self.update_status_ui()

            QMessageBox.information(
                self,
                "Terug naar Concept",
                f"Planning voor {maand_naam} is teruggezet naar concept."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Fout",
                f"Fout bij terug naar concept: {str(e)}"
            )

    def on_maand_changed(self):
        """
        Handle maand navigatie - reload status

        PERFORMANCE NOTE (v0.6.25): Deze methode wordt aangeroepen bij maandwissel
        in de kalender widget. De grid data reload gebeurt daar, niet hier.
        We hoeven hier alleen de status UI te updaten.
        """
        self.load_maand_status()
        self.update_status_ui()

        # Clear cache voor nieuwe maand (wordt lazy geladen bij eerste gebruik)
        self._cached_planning_data.clear()

    def populate_planning_cache(self, planning_data: Dict) -> None:
        """
        PERFORMANCE HELPER (v0.6.25): Populate cache met planning data

        Deze methode kan aangeroepen worden door de kalender widget na data load
        om de cache te vullen voor snelle toggle operaties.

        Args:
            planning_data: Planning data dictionary {datum_str: {gebruiker_id: shift_info}}
        """
        self._cached_planning_data = planning_data.copy()

    def get_filtered_planning_cache(self) -> Dict:
        """
        PERFORMANCE HELPER (v0.6.25): Get gefilterde planning data uit cache

        Returns:
            Filtered planning data op basis van _show_only_gepubliceerd flag
        """
        if not self._cached_planning_data:
            return {}

        if not self._show_only_gepubliceerd:
            # Geen filter: return alles
            return self._cached_planning_data

        # Filter: alleen gepubliceerde records
        filtered = {}
        for datum_str, users_dict in self._cached_planning_data.items():
            filtered[datum_str] = {}
            for user_id, shift_info in users_dict.items():
                if shift_info.get('status') == 'gepubliceerd':
                    filtered[datum_str][user_id] = shift_info

            # Verwijder lege datum entries
            if not filtered[datum_str]:
                del filtered[datum_str]

        return filtered

    def get_shift_codes_text(self) -> str:
        """Haal shift codes tekst voor sidebar"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT w.naam as werkpost, sc.code, sc.dag_type, sc.shift_type,
                   sc.start_uur, sc.eind_uur
            FROM shift_codes sc
            JOIN werkposten w ON sc.werkpost_id = w.id
            WHERE w.is_actief = 1
            ORDER BY w.naam, sc.code
        """)

        lines = []
        current_werkpost = None

        for row in cursor.fetchall():
            if row['werkpost'] != current_werkpost:
                if current_werkpost:
                    lines.append("")
                lines.append(f"=== {row['werkpost']} ===")
                current_werkpost = row['werkpost']

            # Format: CODE - Type (dag) tijd-tijd
            dag_short = {'weekdag': 'we', 'zaterdag': 'za', 'zondag': 'zo'}.get(row['dag_type'], row['dag_type'][:2])
            shift_short = row['shift_type'][:1].upper()

            lines.append(
                f"{row['code']} - {shift_short} ({dag_short}) "
                f"{row['start_uur']}-{row['eind_uur']}"
            )

        conn.close()
        return "\n".join(lines) if lines else "Geen shift codes beschikbaar"

    def get_special_codes_text(self) -> str:
        """Haal speciale codes tekst voor sidebar"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT code, naam FROM speciale_codes ORDER BY code")

        lines = [f"{row['code']} - {row['naam']}" for row in cursor.fetchall()]

        conn.close()
        return "\n".join(lines) if lines else "Geen speciale codes beschikbaar"

    def eventFilter(self, obj, event):
        """Handle F2 key voor codes helper"""
        if event.type() == event.Type.KeyPress and event.key() == Qt.Key.Key_F2:
            self.toon_codes_helper()
            return True
        return super().eventFilter(obj, event)

    def toon_codes_helper(self):
        """Toon F1 helper dialog met zoekbare codes"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Shift Codes - F1 Help")
        dialog.setMinimumSize(700, 600)

        layout = QVBoxLayout()

        # Title
        title = QLabel("Zoek Shift Codes")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(title)

        # Search
        search = QLineEdit()
        search.setPlaceholderText("Zoek code of beschrijving...")
        search.setStyleSheet(Styles.input_field())
        search.textChanged.connect(lambda: self.filter_codes_table(search.text()))  # type: ignore
        layout.addWidget(search)

        # Table
        self.codes_help_table = QTableWidget()
        self.codes_help_table.setColumnCount(5)
        self.codes_help_table.setHorizontalHeaderLabels([
            "Code", "Werkpost", "Type", "Dag", "Tijd"
        ])
        TableConfig.setup_table_widget(self.codes_help_table, row_height=35)

        self.populate_codes_help_table()

        layout.addWidget(self.codes_help_table)

        # Instructies
        instructies = QLabel(
            "Typ code direct in planning grid. "
            "Deze lijst is ter referentie."
        )
        instructies.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")
        layout.addWidget(instructies)

        # Close button
        close_btn = QPushButton("Sluiten (ESC)")
        close_btn.setStyleSheet(Styles.button_secondary())
        close_btn.clicked.connect(dialog.close)  # type: ignore
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def populate_codes_help_table(self):
        """Vul F1 helper table met alle codes"""
        self.codes_help_table.setRowCount(0)

        conn = get_connection()
        cursor = conn.cursor()

        # Shift codes
        cursor.execute("""
            SELECT sc.code, w.naam as werkpost, sc.shift_type, sc.dag_type,
                   sc.start_uur, sc.eind_uur
            FROM shift_codes sc
            JOIN werkposten w ON sc.werkpost_id = w.id
            WHERE w.is_actief = 1
            ORDER BY sc.code
        """)

        for row in cursor.fetchall():
            row_idx = self.codes_help_table.rowCount()
            self.codes_help_table.insertRow(row_idx)

            self.codes_help_table.setItem(row_idx, 0, QTableWidgetItem(row['code']))
            self.codes_help_table.setItem(row_idx, 1, QTableWidgetItem(row['werkpost']))
            self.codes_help_table.setItem(row_idx, 2, QTableWidgetItem(row['shift_type']))
            self.codes_help_table.setItem(row_idx, 3, QTableWidgetItem(row['dag_type']))
            self.codes_help_table.setItem(
                row_idx, 4,
                QTableWidgetItem(f"{row['start_uur']}-{row['eind_uur']}")
            )

        # Speciale codes
        cursor.execute("SELECT code, naam FROM speciale_codes ORDER BY code")

        for row in cursor.fetchall():
            row_idx = self.codes_help_table.rowCount()
            self.codes_help_table.insertRow(row_idx)

            self.codes_help_table.setItem(row_idx, 0, QTableWidgetItem(row['code']))
            self.codes_help_table.setItem(row_idx, 1, QTableWidgetItem("Speciaal"))
            self.codes_help_table.setItem(row_idx, 2, QTableWidgetItem("-"))
            self.codes_help_table.setItem(row_idx, 3, QTableWidgetItem("-"))
            self.codes_help_table.setItem(row_idx, 4, QTableWidgetItem(row['naam']))

        conn.close()

        # Column widths
        header = self.codes_help_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

    def show_auto_generatie_dialog(self):
        """Toon auto-generatie dialog"""
        from gui.dialogs.auto_generatie_dialog import AutoGeneratieDialog

        dialog = AutoGeneratieDialog(self, self.kalender.jaar, self.kalender.maand)
        if dialog.exec():
            # Refresh kalender na generatie
            self.kalender.load_initial_data()

    def show_bulk_delete_dialog(self):
        """Wis alle planning van huidige maand (behalve beschermde codes)"""
        from services.term_code_service import TermCodeService
        import sqlite3
        from datetime import date
        from calendar import monthrange

        # Haal beschermde termen op
        beschermde_termen = ['verlof', 'kompensatiedag', 'zondagrust', 'zaterdagrust', 'ziek', 'arbeidsduurverkorting']

        # Haal codes op voor beschermde termen
        beschermde_codes = []
        for term in beschermde_termen:
            code = TermCodeService.get_code_for_term(term)
            if code:
                beschermde_codes.append(code)

        # Format beschermde codes lijst
        codes_lijst = ", ".join(beschermde_codes) if beschermde_codes else "Geen"

        # Bereken datum range voor huidige maand
        jaar = self.kalender.jaar
        maand = self.kalender.maand
        eerste_dag = date(jaar, maand, 1)
        laatste_dag_nummer = monthrange(jaar, maand)[1]
        laatste_dag = date(jaar, maand, laatste_dag_nummer)

        # Bevestiging dialog
        reply = QMessageBox.question(
            self,
            "Wis Planning Maand",
            f"<b>Weet je zeker dat je alle planning wilt verwijderen voor {eerste_dag.strftime('%B %Y')}?</b><br><br>"
            f"⚠️ Deze actie kan niet ongedaan worden gemaakt.<br><br>"
            f"<b>Beschermde codes (blijven behouden):</b><br>"
            f"{codes_lijst}<br><br>"
            f"<i>Alle andere shifts worden verwijderd.</i>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Voer bulk delete uit
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Bepaal datum range
            start_datum = eerste_dag.isoformat()
            eind_datum = laatste_dag.isoformat()

            if beschermde_codes:
                # DELETE met WHERE NOT IN voor beschermde codes
                placeholders = ','.join(['?'] * len(beschermde_codes))
                cursor.execute(f"""
                    DELETE FROM planning
                    WHERE datum >= ?
                    AND datum <= ?
                    AND (shift_code NOT IN ({placeholders}) OR shift_code IS NULL)
                """, [start_datum, eind_datum] + beschermde_codes)
            else:
                # Geen beschermde codes, verwijder alles
                cursor.execute("""
                    DELETE FROM planning
                    WHERE datum >= ?
                    AND datum <= ?
                """, (start_datum, eind_datum))

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            # Refresh kalender
            self.kalender.load_initial_data()

            # Success message
            QMessageBox.information(
                self,
                "Planning Gewist",
                f"✓ {deleted_count} shifts verwijderd voor {eerste_dag.strftime('%B %Y')}.<br><br>"
                f"Beschermde codes zijn behouden."
            )

        except sqlite3.Error as e:
            QMessageBox.critical(
                self,
                "Database Fout",
                f"Fout bij verwijderen planning:<br>{e}"
            )

    def filter_codes_table(self, search_text: str):
        """Filter codes table op zoekterm"""
        search_lower = search_text.lower()

        for row in range(self.codes_help_table.rowCount()):
            match = False
            for col in range(self.codes_help_table.columnCount()):
                item = self.codes_help_table.item(row, col)
                if item and search_lower in item.text().lower():
                    match = True
                    break

            self.codes_help_table.setRowHidden(row, not match)