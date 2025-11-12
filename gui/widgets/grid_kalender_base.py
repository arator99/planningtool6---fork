# gui/widgets/grid_kalender_base.py
"""
Grid Kalender Base Class
Gemeenschappelijke functionaliteit voor planner en teamlid kalenders
UPDATED: Database compatibiliteit met nieuwe planning tabel structuur
"""
from typing import Dict, Any, List, Optional, Tuple
from PyQt6.QtWidgets import QWidget, QDialog, QPushButton, QLabel, QComboBox, QHBoxLayout
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
from database.connection import get_connection
from gui.styles import Colors, Fonts, Styles, Dimensions
from services.term_code_service import TermCodeService
import calendar


class GridKalenderBase(QWidget):
    """
    Base class voor grid kalenders
    Gemeenschappelijke functionaliteit voor planner en teamlid views
    """

    def __init__(self, jaar: int, maand: int):
        super().__init__()

        # Instance attributes
        self.jaar: int = jaar
        self.maand: int = maand
        self.gebruikers_data: List[Dict[str, Any]] = []
        self.planning_data: Dict[str, Dict[int, Dict[str, Any]]] = {}  # {datum_str: {gebruiker_id: shift_info}}
        self.feestdagen: List[str] = []  # List van datum strings
        self.verlof_data: Dict[str, Dict[int, Dict[str, Any]]] = {}  # {datum_str: {gebruiker_id: verlof_info}}
        self.filter_gebruikers: Dict[int, bool] = {}  # {gebruiker_id: zichtbaar}

        # UI components (gedefinieerd in subclasses)
        self.grid_container: Optional[QWidget] = None

    def load_feestdagen(self) -> None:
        """Laad feestdagen voor huidig jaar"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT datum FROM feestdagen 
            WHERE datum LIKE ?
        """, (f"{self.jaar}-%",))
        self.feestdagen = [row['datum'] for row in cursor.fetchall()]
        conn.close()

    def load_gebruikers(self, alleen_actief: bool = True) -> None:
        """Laad gebruikers lijst"""
        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT id, volledige_naam, gebruikersnaam, is_reserve FROM gebruikers"
        if alleen_actief:
            query += " WHERE is_actief = 1 AND gebruikersnaam != 'admin'"
        else:
            query += " WHERE gebruikersnaam != 'admin'"
        query += " ORDER BY is_reserve, achternaam, voornaam"

        cursor.execute(query)
        nieuwe_gebruikers_data = cursor.fetchall()
        conn.close()

        # Update gebruikers data
        nieuwe_gebruiker_ids = {user['id'] for user in nieuwe_gebruikers_data}
        self.gebruikers_data = nieuwe_gebruikers_data

        # Behoud bestaande filter waar mogelijk, alleen nieuwe gebruikers toevoegen
        if not hasattr(self, 'filter_gebruikers'):
            # Eerste keer - initialiseer met subclass-specifieke logic
            self.filter_gebruikers = {
                user['id']: self.get_initial_filter_state(user['id'])
                for user in self.gebruikers_data
            }
        else:
            # Filter bestaat al - behoud bestaande instellingen
            # Verwijder gebruikers die niet meer bestaan
            for user_id in list(self.filter_gebruikers.keys()):
                if user_id not in nieuwe_gebruiker_ids:
                    del self.filter_gebruikers[user_id]

            # Voeg nieuwe gebruikers toe met subclass-specifieke logic
            for user_id in nieuwe_gebruiker_ids:
                if user_id not in self.filter_gebruikers:
                    self.filter_gebruikers[user_id] = self.get_initial_filter_state(user_id)

    def load_planning_data(self, start_datum: str, eind_datum: str, alleen_gepubliceerd: bool = False) -> None:
        """
        Laad planning data voor periode
        Args:
            start_datum: YYYY-MM-DD
            eind_datum: YYYY-MM-DD
            alleen_gepubliceerd: Als True, toon alleen gepubliceerde planning (voor teamleden)
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Bouw WHERE clause
        where_clause = "WHERE p.datum BETWEEN ? AND ?"
        if alleen_gepubliceerd:
            where_clause += " AND p.status = 'gepubliceerd'"

        # Haal planning op met details van shift_codes en speciale_codes
        query = f"""
            SELECT
                p.gebruiker_id,
                p.datum,
                p.shift_code,
                p.notitie,
                p.status,
                -- Details van shift_codes (indien match)
                sc.shift_type as shift_naam,
                sc.start_uur,
                sc.eind_uur,
                w.naam as werkpost_naam,
                -- Details van speciale_codes (indien match)
                spc.naam as speciale_naam
            FROM planning p
            LEFT JOIN shift_codes sc ON p.shift_code = sc.code
            LEFT JOIN werkposten w ON sc.werkpost_id = w.id
            LEFT JOIN speciale_codes spc ON p.shift_code = spc.code
            {where_clause}
        """
        cursor.execute(query, (start_datum, eind_datum))

        # Organiseer per datum per gebruiker
        self.planning_data = {}
        for row in cursor.fetchall():
            datum = row['datum']
            gebruiker_id = row['gebruiker_id']

            if datum not in self.planning_data:
                self.planning_data[datum] = {}

            # Bepaal of het een shift of speciale code is
            is_speciale_code = row['speciale_naam'] is not None

            self.planning_data[datum][gebruiker_id] = {
                'shift_code': row['shift_code'],
                'notitie': row['notitie'],
                'status': row['status'],
                # Shift details (None als speciale code)
                'shift_naam': row['shift_naam'],
                'start_tijd': row['start_uur'],
                'eind_tijd': row['eind_uur'],
                'werkpost_naam': row['werkpost_naam'],
                # Speciale code details (None als shift)
                'speciale_code': row['shift_code'] if is_speciale_code else None,
                'speciale_naam': row['speciale_naam'],
                'is_speciale_code': is_speciale_code
            }

        conn.close()

    def load_verlof_data(self, start_datum: str, eind_datum: str) -> None:
        """
        Laad verlof aanvragen voor periode
        Args:
            start_datum: YYYY-MM-DD
            eind_datum: YYYY-MM-DD
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                gebruiker_id,
                start_datum,
                eind_datum,
                status,
                aangevraagd_op
            FROM verlof_aanvragen
            WHERE (start_datum BETWEEN ? AND ?)
               OR (eind_datum BETWEEN ? AND ?)
               OR (start_datum <= ? AND eind_datum >= ?)
        """, (start_datum, eind_datum, start_datum, eind_datum, start_datum, eind_datum))

        # Organiseer per datum per gebruiker
        self.verlof_data = {}
        for row in cursor.fetchall():
            gebruiker_id = row['gebruiker_id']
            start = datetime.strptime(row['start_datum'], '%Y-%m-%d')
            eind = datetime.strptime(row['eind_datum'], '%Y-%m-%d')

            # Voor elke dag in de verlof periode
            huidige = start
            while huidige <= eind:
                datum_str = huidige.strftime('%Y-%m-%d')

                if datum_str not in self.verlof_data:
                    self.verlof_data[datum_str] = {}

                self.verlof_data[datum_str][gebruiker_id] = {
                    'status': row['status'],
                    'aangevraagd_op': row['aangevraagd_op']
                }

                huidige += timedelta(days=1)

        conn.close()

    def get_datum_achtergrond(self, datum_str: str) -> str:
        """
        Bepaal achtergrondkleur voor datum
        Returns: Hex kleur code
        """
        datum = datetime.strptime(datum_str, '%Y-%m-%d')
        weekdag = datum.weekday()  # 0=Ma, 6=Zo

        # Zondag of feestdag
        if weekdag == 6 or datum_str in self.feestdagen:
            return '#FFF9C4'  # Geel

        # Zaterdag
        elif weekdag == 5:
            return '#EEEEEE'  # Lichtgrijs

        # Weekdag
        else:
            return '#FFFFFF'  # Wit

    def get_verlof_overlay(self, datum_str: str, gebruiker_id: int, mode: str) -> Optional[str]:
        """
        Bepaal overlay kleur voor verlof status
        Args:
            datum_str: YYYY-MM-DD
            gebruiker_id: ID van gebruiker
            mode: 'planner' of 'teamlid'
        Returns: RGBA kleur string of None
        """
        # Check verlof data
        verlof_info = None
        if datum_str in self.verlof_data and gebruiker_id in self.verlof_data[datum_str]:
            verlof_info = self.verlof_data[datum_str][gebruiker_id]

        # Check shift data voor VV/DA/VD
        shift_info = None
        if datum_str in self.planning_data and gebruiker_id in self.planning_data[datum_str]:
            shift_info = self.planning_data[datum_str][gebruiker_id]

        if mode == 'planner':
            # Planner ziet verlof aanvragen status
            if verlof_info:
                if verlof_info['status'] == 'goedgekeurd':
                    return 'rgba(144, 238, 144, 0.4)'  # Lichtgroen
                elif verlof_info['status'] == 'geweigerd':
                    return 'rgba(255, 182, 193, 0.4)'  # Lichtrood
                elif verlof_info['status'] == 'pending':
                    return 'rgba(173, 216, 230, 0.4)'  # Lichtblauw

        elif mode == 'teamlid':
            # Teamlid ziet eigen verlof/DA/VD via shift_code
            if shift_info:
                code = shift_info.get('shift_code', '')

                # Gebruik term-based checks voor systeem codes
                verlof_code = TermCodeService.get_code_for_term('verlof')
                adv_code = TermCodeService.get_code_for_term('arbeidsduurverkorting')

                if code == verlof_code:
                    return 'rgba(144, 238, 144, 0.4)'  # Lichtgroen (verlof)
                elif code == adv_code:
                    return 'rgba(173, 216, 230, 0.4)'  # Lichtblauw (ADV)
                elif code == 'VD':
                    return 'rgba(216, 191, 216, 0.4)'  # Lichtpaars (Vrij van dienst)

        return None

    def get_display_code(self, datum_str: str, gebruiker_id: int) -> str:
        """
        Haal shift code op voor weergave
        Returns: Shift code string (7101, RX, VV, etc.) of lege string
        """
        if datum_str not in self.planning_data:
            return ""

        if gebruiker_id not in self.planning_data[datum_str]:
            return ""

        shift_info = self.planning_data[datum_str][gebruiker_id]

        # Return gewoon de shift_code
        return shift_info.get('shift_code', '')

    def get_cel_tooltip(self, datum_str: str, gebruiker_id: int, mode: str) -> str:
        """
        Genereer tooltip tekst voor cel
        """
        tooltip_lines = []

        # Datum info
        datum = datetime.strptime(datum_str, '%Y-%m-%d')
        tooltip_lines.append(f"Datum: {datum.strftime('%d-%m-%Y')}")

        # Shift info
        if datum_str in self.planning_data and gebruiker_id in self.planning_data[datum_str]:
            shift_info = self.planning_data[datum_str][gebruiker_id]

            code = shift_info.get('shift_code', '')

            if shift_info.get('is_speciale_code'):
                # Speciale code
                tooltip_lines.append(f"{code}: {shift_info.get('speciale_naam', '')}")
            elif code:
                # Reguliere shift
                shift_naam = shift_info.get('shift_naam', '')
                start = shift_info.get('start_tijd', '')
                eind = shift_info.get('eind_tijd', '')
                werkpost = shift_info.get('werkpost_naam', '')

                tooltip_lines.append(f"Shift: {code}")
                if shift_naam:
                    tooltip_lines.append(f"Type: {shift_naam}")
                if werkpost:
                    tooltip_lines.append(f"Werkpost: {werkpost}")
                if start and eind:
                    tooltip_lines.append(f"Tijden: {start} - {eind}")

        # Verlof info (alleen voor planner mode)
        if mode == 'planner' and datum_str in self.verlof_data and gebruiker_id in self.verlof_data[datum_str]:
            verlof_info = self.verlof_data[datum_str][gebruiker_id]
            status_tekst = {
                'pending': '⏳ Verlof aanvraag in behandeling',
                'goedgekeurd': '✓ Verlof goedgekeurd',
                'geweigerd': '✗ Verlof geweigerd'
            }
            tooltip_lines.append("")
            tooltip_lines.append(status_tekst[verlof_info['status']])
            tooltip_lines.append(f"Aangevraagd op: {verlof_info['aangevraagd_op']}")

        # Notitie info (voor alle modes)
        if datum_str in self.planning_data and gebruiker_id in self.planning_data[datum_str]:
            notitie = self.planning_data[datum_str][gebruiker_id].get('notitie', '')
            if notitie:
                tooltip_lines.append("")
                tooltip_lines.append("--- NOTITIE ---")
                tooltip_lines.append(notitie)

        return '\n'.join(tooltip_lines) if tooltip_lines else ""

    def get_datum_lijst(self, start_offset: int = 0, eind_offset: int = 0) -> List[Tuple[str, str]]:
        """
        Genereer lijst van datums voor weergave
        Args:
            start_offset: Aantal dagen voor de maand (bijv. 8)
            eind_offset: Aantal dagen na de maand (bijv. 8)
        Returns: List van (datum_str, label) tuples
        """
        # Eerste dag van de maand
        eerste_dag = datetime(self.jaar, self.maand, 1)

        # Laatste dag van de maand
        laatste_dag_nummer = calendar.monthrange(self.jaar, self.maand)[1]
        laatste_dag = datetime(self.jaar, self.maand, laatste_dag_nummer)

        # Start datum (met offset)
        start = eerste_dag - timedelta(days=start_offset)

        # Eind datum (met offset)
        eind = laatste_dag + timedelta(days=eind_offset)

        # Genereer alle datums
        datum_lijst = []
        huidige = start
        while huidige <= eind:
            datum_str = huidige.strftime('%Y-%m-%d')

            # Label: weekdag + datum + maand (als niet huidige maand)
            weekdag_naam = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'][huidige.weekday()]
            dag = huidige.day

            if huidige.month != self.maand:
                # Andere maand: toon ook maand naam
                maand_naam = ['jan', 'feb', 'mrt', 'apr', 'mei', 'jun',
                              'jul', 'aug', 'sep', 'okt', 'nov', 'dec'][huidige.month - 1]
                label = f"{weekdag_naam}\n{dag}\n{maand_naam}"
            else:
                # Huidige maand: alleen weekdag + dag
                label = f"{weekdag_naam}\n{dag}"

            datum_lijst.append((datum_str, label))
            huidige += timedelta(days=1)

        return datum_lijst

    def get_zichtbare_gebruikers(self) -> List[Dict[str, Any]]:
        """Return lijst van gebruikers die zichtbaar zijn volgens filter"""
        return [user for user in self.gebruikers_data if self.filter_gebruikers.get(user['id'], True)]

    def toggle_gebruiker_filter(self, gebruiker_id: int) -> None:
        """Toggle zichtbaarheid van gebruiker"""
        if gebruiker_id in self.filter_gebruikers:
            self.filter_gebruikers[gebruiker_id] = not self.filter_gebruikers[gebruiker_id]

    def set_alle_gebruikers_filter(self, zichtbaar: bool) -> None:
        """Zet alle gebruikers zichtbaar of onzichtbaar"""
        for gebruiker_id in self.filter_gebruikers:
            self.filter_gebruikers[gebruiker_id] = zichtbaar

    def refresh_data(self, jaar: int, maand: int) -> None:
        """
        Herlaad alle data voor nieuwe jaar/maand
        Moet geïmplementeerd worden in subclass
        """
        self.jaar = jaar
        self.maand = maand
        # Subclass implementeert verder

    def create_cel_stylesheet(self, achtergrond: str, overlay: Optional[str] = None) -> str:
        """
        Genereer stylesheet voor cel met optionele overlay

        Overlay wordt als achtergrondkleur gebruikt (met opacity voor transparantie)
        """
        if overlay:
            # Overlay overschrijft achtergrond (overlay heeft al opacity voor transparantie effect)
            return f"""
                QLabel {{
                    background-color: {overlay};
                    color: #000000;
                    font-size: {Fonts.SIZE_SMALL}px;
                    font-weight: bold;
                    border: 1px solid {Colors.BORDER_LIGHT};
                    padding: 4px;
                    qproperty-alignment: AlignCenter;
                }}
            """
        else:
            return f"""
                QLabel {{
                    background-color: {achtergrond};
                    color: #000000;
                    font-size: {Fonts.SIZE_SMALL}px;
                    font-weight: bold;
                    border: 1px solid {Colors.BORDER_LIGHT};
                    padding: 4px;
                    qproperty-alignment: AlignCenter;
                }}
            """

    def load_rode_lijnen(self) -> None:
        """Laad rode lijnen (28-daagse HR-cycli) voor huidige periode"""
        conn = get_connection()
        cursor = conn.cursor()

        # Laad alle rode lijnen start datums (deze markeren begin van een nieuwe periode)
        cursor.execute("""
            SELECT start_datum, eind_datum, periode_nummer
            FROM rode_lijnen
            ORDER BY start_datum
        """)

        # Dictionary met start_datum als key voor snelle lookup
        # Converteer datetime naar date string (YYYY-MM-DD)
        self.rode_lijnen_starts: Dict[str, int] = {}
        for row in cursor.fetchall():
            datum_str = row['start_datum']
            # Strip timestamp als die er is (2024-07-28T00:00:00 -> 2024-07-28)
            if 'T' in datum_str:
                datum_str = datum_str.split('T')[0]
            self.rode_lijnen_starts[datum_str] = row['periode_nummer']

        conn.close()

    def update_title(self) -> None:
        """Update titel met maand/jaar"""
        maanden = ['Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni',
                   'Juli', 'Augustus', 'September', 'Oktober', 'November', 'December']
        self.title_label.setText(f"Planning {maanden[self.maand - 1]} {self.jaar}")

    def on_jaar_changed(self, jaar_str: str) -> None:
        """Jaar gewijzigd"""
        self.refresh_data(int(jaar_str), self.maand)

    def on_maand_changed(self, index: int) -> None:
        """Maand gewijzigd"""
        self.refresh_data(self.jaar, index + 1)

    def open_filter_dialog(self) -> None:
        """Open dialog om gebruikers te filteren"""
        from gui.widgets.teamlid_grid_kalender import FilterDialog
        dialog = FilterDialog(self.gebruikers_data, self.filter_gebruikers, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.filter_gebruikers = dialog.get_filter()
            self.build_grid()

    def get_header_extra_buttons(self) -> List[QPushButton]:
        """
        Template method: Override in subclass voor extra header buttons
        Returns: List van buttons om toe te voegen aan header
        """
        return []  # Default: geen extra buttons

    def get_initial_filter_state(self, user_id: int) -> bool:
        """
        Template method: MOET overridden worden in subclass

        Deze method bepaalt welke gebruikers initieel zichtbaar zijn in de filter.
        Elke subclass moet expliciet aangeven wat het gewenste gedrag is.

        Args:
            user_id: ID van gebruiker
        Returns:
            True als gebruiker initieel zichtbaar moet zijn, False anders

        Raises:
            NotImplementedError: Als subclass deze method niet implementeert
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} moet get_initial_filter_state() implementeren"
        )

    def create_header(self) -> QHBoxLayout:
        """
        Maak header met jaar/maand selectie en filter
        Subclasses kunnen extra buttons toevoegen via get_header_extra_buttons()
        """
        header = QHBoxLayout()

        # Titel (normaal, geen kadertje)
        self.title_label = QLabel()
        self.title_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_LARGE))
        self.update_title()
        header.addWidget(self.title_label)

        header.addStretch()

        # Template method: Extra buttons van subclass
        extra_buttons = self.get_header_extra_buttons()
        for btn in extra_buttons:
            header.addWidget(btn)

        # Filter knop
        filter_btn = QPushButton("Filter Teamleden")
        filter_btn.setFixedSize(150, Dimensions.BUTTON_HEIGHT_NORMAL)
        filter_btn.clicked.connect(self.open_filter_dialog)  # type: ignore
        filter_btn.setStyleSheet(Styles.button_secondary())
        header.addWidget(filter_btn)

        # Jaar selector
        jaar_label = QLabel("Jaar:")
        jaar_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        header.addWidget(jaar_label)

        self.jaar_combo = QComboBox()
        self.jaar_combo.setFixedWidth(100)
        jaren = [str(jaar) for jaar in range(datetime.now().year - 1, datetime.now().year + 3)]
        self.jaar_combo.addItems(jaren)
        self.jaar_combo.setCurrentText(str(self.jaar))
        self.jaar_combo.currentTextChanged.connect(self.on_jaar_changed)  # type: ignore
        header.addWidget(self.jaar_combo)

        # Maand selector
        maand_label = QLabel("Maand:")
        maand_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        header.addWidget(maand_label)

        self.maand_combo = QComboBox()
        self.maand_combo.setFixedWidth(120)
        maanden = ['Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni',
                   'Juli', 'Augustus', 'September', 'Oktober', 'November', 'December']
        self.maand_combo.addItems(maanden)
        self.maand_combo.setCurrentIndex(self.maand - 1)
        self.maand_combo.currentIndexChanged.connect(self.on_maand_changed)  # type: ignore
        header.addWidget(self.maand_combo)

        return header