"""
HR Regels Service
Versie: 0.6.25 - Uitgebreid voor HR Validatie Systeem

Helper functies voor opvragen van HR regels uit de database.
"""

from datetime import datetime, date
from typing import Tuple, Optional
from database.connection import get_connection


class HRRegelsService:
    """Service voor het ophalen en gebruiken van HR regels"""

    @staticmethod
    def get_verlof_vervaldatum(jaar: int) -> date:
        """
        Haal vervaldatum overgedragen verlof op uit HR regels.

        Args:
            jaar: Het jaar waarvoor de vervaldatum geldt

        Returns:
            date object met vervaldatum (bijv. 1 mei 2025)

        Default:
            1 mei (Nederlandse standaard) als geen regel gevonden

        Format in database:
            "DD-MM" (bijv. "01-05" voor 1 mei)
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Query actieve regel
            cursor.execute("""
                SELECT waarde
                FROM hr_regels
                WHERE naam = 'Vervaldatum overgedragen verlof'
                  AND is_actief = 1
                ORDER BY actief_vanaf DESC
                LIMIT 1
            """)

            row = cursor.fetchone()

            if row and row['waarde']:
                # Parse "DD-MM" format
                datum_str = str(row['waarde'])

                try:
                    # Split op "-"
                    parts = datum_str.split('-')
                    if len(parts) == 2:
                        dag = int(parts[0])
                        maand = int(parts[1])

                        # Validatie
                        if 1 <= dag <= 31 and 1 <= maand <= 12:
                            return datetime(jaar, maand, dag).date()

                except (ValueError, IndexError):
                    pass  # Fallback naar default

        except Exception:
            pass
        finally:
            conn.close()

        # Fallback: 1 mei (Nederlandse standaard)
        return datetime(jaar, 5, 1).date()

    @staticmethod
    def get_actieve_regel(naam: str) -> dict:
        """
        Haal een actieve HR regel op bij naam.

        Args:
            naam: Naam van de regel

        Returns:
            Dictionary met regel data, of None als niet gevonden
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, naam, waarde, eenheid, beschrijving, actief_vanaf
                FROM hr_regels
                WHERE naam = ? AND is_actief = 1
                ORDER BY actief_vanaf DESC
                LIMIT 1
            """, (naam,))

            row = cursor.fetchone()

            if row:
                return {
                    'id': row['id'],
                    'naam': row['naam'],
                    'waarde': row['waarde'],
                    'eenheid': row['eenheid'],
                    'beschrijving': row['beschrijving'],
                    'actief_vanaf': row['actief_vanaf']
                }

        except Exception:
            pass
        finally:
            conn.close()

        return None

    # ========================================================================
    # HR VALIDATIE SYSTEEM - Nieuwe methodes (v0.6.25)
    # ========================================================================

    @staticmethod
    def get_min_rust_uren() -> float:
        """
        Haal minimum rust uren op tussen shifts

        Returns:
            Aantal uren (default: 12.0)
        """
        regel = HRRegelsService.get_actieve_regel('min_rust_uren')
        if regel and regel['waarde']:
            try:
                return float(regel['waarde'])
            except (ValueError, TypeError):
                pass

        # Default: 12u (wettelijk minimum)
        return 12.0

    @staticmethod
    def get_max_uren_week() -> float:
        """
        Haal maximum uren per week op

        Returns:
            Aantal uren (default: 50.0)
        """
        regel = HRRegelsService.get_actieve_regel('max_uren_week')
        if regel and regel['waarde']:
            try:
                return float(regel['waarde'])
            except (ValueError, TypeError):
                pass

        # Default: 50u (wettelijk maximum gemiddeld)
        return 50.0

    @staticmethod
    def get_max_werkdagen_cyclus() -> int:
        """
        Haal maximum werkdagen per 28-dagen cyclus op

        Returns:
            Aantal dagen (default: 19)
        """
        regel = HRRegelsService.get_actieve_regel('max_werkdagen_cyclus')
        if regel and regel['waarde']:
            try:
                return int(float(regel['waarde']))
            except (ValueError, TypeError):
                pass

        # Default: 19 dagen per 28-dagen cyclus
        return 19

    @staticmethod
    def get_max_dagen_tussen_rx() -> int:
        """
        Haal maximum dagen tussen rustdagen (RX/CX) op

        Returns:
            Aantal dagen (default: 7)
        """
        regel = HRRegelsService.get_actieve_regel('max_dagen_tussen_rx')
        if regel and regel['waarde']:
            try:
                return int(float(regel['waarde']))
            except (ValueError, TypeError):
                pass

        # Default: 7 dagen tussen rustdagen
        return 7

    @staticmethod
    def get_max_werkdagen_reeks() -> int:
        """
        Haal maximum werkdagen achter elkaar op

        Returns:
            Aantal dagen (default: 7)
        """
        regel = HRRegelsService.get_actieve_regel('max_werkdagen_reeks')
        if regel and regel['waarde']:
            try:
                return int(float(regel['waarde']))
            except (ValueError, TypeError):
                pass

        # Default: 7 werkdagen achter elkaar
        return 7

    @staticmethod
    def get_max_weekends_achter_elkaar() -> int:
        """
        Haal maximum weekends achter elkaar op

        Returns:
            Aantal weekends (default: 6)
        """
        regel = HRRegelsService.get_actieve_regel('max_weekends_achter_elkaar')
        if regel and regel['waarde']:
            try:
                return int(float(regel['waarde']))
            except (ValueError, TypeError):
                pass

        # Default: 6 weekends achter elkaar
        return 6

    @staticmethod
    def get_week_definitie() -> Tuple[str, str, str, str]:
        """
        Haal week definitie op

        Returns:
            Tuple (start_dag, start_uur, eind_dag, eind_uur)
            Default: ('ma', '00:00', 'zo', '23:59')

        Format in database:
            "dag-HH:MM|dag-HH:MM" (bijv. "ma-00:00|zo-23:59")
        """
        regel = HRRegelsService.get_actieve_regel('week_definitie')

        if regel and regel['waarde']:
            try:
                waarde = str(regel['waarde'])
                start, eind = waarde.split('|')
                start_dag, start_uur = start.split('-', 1)
                eind_dag, eind_uur = eind.split('-', 1)

                return (
                    start_dag.strip(),
                    start_uur.strip(),
                    eind_dag.strip(),
                    eind_uur.strip()
                )

            except (ValueError, IndexError):
                pass  # Fallback naar default

        # Default: Maandag 00:00 - Zondag 23:59
        return ('ma', '00:00', 'zo', '23:59')

    @staticmethod
    def get_weekend_definitie() -> Tuple[str, str, str, str]:
        """
        Haal weekend definitie op

        Returns:
            Tuple (start_dag, start_uur, eind_dag, eind_uur)
            Default: ('vr', '22:00', 'ma', '06:00')

        Format in database:
            "dag-HH:MM|dag-HH:MM" (bijv. "vr-22:00|ma-06:00")
        """
        regel = HRRegelsService.get_actieve_regel('weekend_definitie')

        if regel and regel['waarde']:
            try:
                waarde = str(regel['waarde'])
                start, eind = waarde.split('|')
                start_dag, start_uur = start.split('-', 1)
                eind_dag, eind_uur = eind.split('-', 1)

                return (
                    start_dag.strip(),
                    start_uur.strip(),
                    eind_dag.strip(),
                    eind_uur.strip()
                )

            except (ValueError, IndexError):
                pass  # Fallback naar default

        # Default: Vrijdag 22:00 - Maandag 06:00
        return ('vr', '22:00', 'ma', '06:00')
