#gui/widgets/grid_kalender_base.py
"""
Grid Kalender Base Class
Gemeenschappelijke functionaliteit voor planner en teamlid kalenders
"""
from typing import Dict, Any, List, Optional, Tuple
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
from database.connection import get_connection
from gui.styles import Styles, Colors, Fonts, Dimensions
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
            query += " WHERE is_actief = 1"
        query += " ORDER BY volledige_naam"

        cursor.execute(query)
        self.gebruikers_data = cursor.fetchall()
        conn.close()

        # Initialiseer filter (allemaal aan)
        self.filter_gebruikers = {user['id']: True for user in self.gebruikers_data}

    def load_planning_data(self, start_datum: str, eind_datum: str) -> None:
        """
        Laad planning data voor periode
        Args:
            start_datum: YYYY-MM-DD
            eind_datum: YYYY-MM-DD
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Haal planning shifts op
        cursor.execute("""
            SELECT 
                ps.gebruiker_id,
                ps.datum,
                ps.shift_code_id,
                ps.speciale_code_id,
                sc.code as shift_code,
                sc.naam as shift_naam,
                sc.start_tijd,
                sc.eind_tijd,
                spc.code as speciale_code,
                spc.naam as speciale_naam
            FROM planning_shifts ps
            LEFT JOIN shift_codes sc ON ps.shift_code_id = sc.id
            LEFT JOIN speciale_codes spc ON ps.speciale_code_id = spc.id
            WHERE ps.datum BETWEEN ? AND ?
        """, (start_datum, eind_datum))

        # Organiseer per datum per gebruiker
        self.planning_data = {}
        for row in cursor.fetchall():
            datum = row['datum']
            gebruiker_id = row['gebruiker_id']

            if datum not in self.planning_data:
                self.planning_data[datum] = {}

            self.planning_data[datum][gebruiker_id] = {
                'shift_code_id': row['shift_code_id'],
                'speciale_code_id': row['speciale_code_id'],
                'shift_code': row['shift_code'],
                'shift_naam': row['shift_naam'],
                'start_tijd': row['start_tijd'],
                'eind_tijd': row['eind_tijd'],
                'speciale_code': row['speciale_code'],
                'speciale_naam': row['speciale_naam']
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

        # Check shift data voor DA/VD
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
            # Teamlid ziet eigen verlof/DA/VD
            if shift_info and shift_info['speciale_code']:
                if shift_info['speciale_code'] == 'VV':
                    return 'rgba(144, 238, 144, 0.4)'  # Lichtgroen (verlof)
                elif shift_info['speciale_code'] == 'DA':
                    return 'rgba(173, 216, 230, 0.4)'  # Lichtblauw (ADV)
                elif shift_info['speciale_code'] == 'VD':
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

        # Speciale codes hebben voorrang
        if shift_info['speciale_code']:
            return shift_info['speciale_code']

        # Reguliere shift codes
        elif shift_info['shift_code']:
            return shift_info['shift_code']

        return ""

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

            if shift_info['speciale_code']:
                tooltip_lines.append(f"{shift_info['speciale_code']}: {shift_info['speciale_naam']}")
            elif shift_info['shift_code']:
                tooltip_lines.append(f"Shift: {shift_info['shift_naam']}")
                tooltip_lines.append(f"Tijden: {shift_info['start_tijd']} - {shift_info['eind_tijd']}")

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
        """
        if overlay:
            # Linear gradient overlay over achtergrond
            return f"""
                QLabel {{
                    background: linear-gradient({overlay}, {overlay}), {achtergrond};
                    color: {Colors.TEXT_PRIMARY};
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
                    color: {Colors.TEXT_PRIMARY};
                    font-size: {Fonts.SIZE_SMALL}px;
                    font-weight: bold;
                    border: 1px solid {Colors.BORDER_LIGHT};
                    padding: 4px;
                    qproperty-alignment: AlignCenter;
                }}
            """