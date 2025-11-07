"""
Verlof & KD Saldo Service
Versie: 0.6.10

Beheert verlof en kompensatiedagen saldi voor gebruikers.
Gebruikt term-based systeem voor code-onafhankelijke queries.
"""

from datetime import datetime, timedelta
from database.connection import get_connection


class VerlofSaldoService:
    """Service voor verlof en KD saldo beheer"""

    @staticmethod
    def get_saldo(gebruiker_id: int, jaar: int) -> dict:
        """
        Haal saldo op voor gebruiker/jaar en bereken resterend.

        Args:
            gebruiker_id: ID van de gebruiker
            jaar: Jaar (bv. 2025)

        Returns:
            Dictionary met saldo informatie:
            {
                'vv_totaal': 26,
                'vv_overgedragen': 5,
                'vv_opgenomen': 12,
                'vv_resterend': 19,      # Kan negatief zijn
                'kd_totaal': 13,
                'kd_overgedragen': 8,
                'kd_opgenomen': 3,
                'kd_resterend': 18,      # Kan negatief zijn
                'opmerking': '80% deeltijd',
                'bestaat': True
            }
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Haal saldo record op
        cursor.execute("""
            SELECT
                verlof_totaal,
                verlof_overgedragen,
                verlof_opgenomen,
                kd_totaal,
                kd_overgedragen,
                kd_opgenomen,
                opmerking
            FROM verlof_saldo
            WHERE gebruiker_id = ? AND jaar = ?
        """, (gebruiker_id, jaar))

        row = cursor.fetchone()

        if not row:
            # Geen saldo record, return defaults
            return {
                'vv_totaal': 0,
                'vv_overgedragen': 0,
                'vv_opgenomen': 0,
                'vv_resterend': 0,
                'kd_totaal': 0,
                'kd_overgedragen': 0,
                'kd_opgenomen': 0,
                'kd_resterend': 0,
                'opmerking': '',
                'bestaat': False
            }

        # Bereken opgenomen uit planning (meest actueel - handmatige wijzigingen meegenomen)
        vv_opgenomen, kd_opgenomen = VerlofSaldoService.bereken_opgenomen_uit_planning(
            gebruiker_id, jaar
        )

        # Bereken resterend
        vv_totaal = row['verlof_totaal'] or 0
        vv_overgedragen = row['verlof_overgedragen'] or 0
        vv_resterend = vv_totaal + vv_overgedragen - vv_opgenomen

        kd_totaal = row['kd_totaal'] or 0
        kd_overgedragen = row['kd_overgedragen'] or 0
        kd_resterend = kd_totaal + kd_overgedragen - kd_opgenomen

        return {
            'vv_totaal': vv_totaal,
            'vv_overgedragen': vv_overgedragen,
            'vv_opgenomen': vv_opgenomen,
            'vv_resterend': vv_resterend,
            'kd_totaal': kd_totaal,
            'kd_overgedragen': kd_overgedragen,
            'kd_opgenomen': kd_opgenomen,
            'kd_resterend': kd_resterend,
            'opmerking': row['opmerking'] or '',
            'bestaat': True
        }

    @staticmethod
    def update_saldo(gebruiker_id: int, jaar: int,
                     vv_totaal: int, vv_overgedragen: int,
                     kd_totaal: int, kd_overgedragen: int,
                     opmerking: str = '') -> bool:
        """
        Update saldo voor gebruiker/jaar (admin only).

        Args:
            gebruiker_id: ID van de gebruiker
            jaar: Jaar
            vv_totaal: Jaarlijks verlof contingent
            vv_overgedragen: Overgedragen verlof van vorig jaar
            kd_totaal: Jaarlijks KD contingent
            kd_overgedragen: Overgedragen KD van vorig jaar
            opmerking: Optionele opmerking (bv. "80% deeltijd")

        Returns:
            True bij succes, False bij fout
        """
        # Validatie: KD overdracht max 35
        if kd_overgedragen > 35:
            return False

        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Check of record bestaat
            cursor.execute("""
                SELECT id FROM verlof_saldo
                WHERE gebruiker_id = ? AND jaar = ?
            """, (gebruiker_id, jaar))

            exists = cursor.fetchone()
            now = datetime.now().isoformat()

            if exists:
                # Update bestaand record
                cursor.execute("""
                    UPDATE verlof_saldo
                    SET verlof_totaal = ?,
                        verlof_overgedragen = ?,
                        kd_totaal = ?,
                        kd_overgedragen = ?,
                        opmerking = ?,
                        gewijzigd_op = ?
                    WHERE gebruiker_id = ? AND jaar = ?
                """, (vv_totaal, vv_overgedragen, kd_totaal, kd_overgedragen,
                      opmerking, now, gebruiker_id, jaar))
            else:
                # Insert nieuw record
                cursor.execute("""
                    INSERT INTO verlof_saldo
                    (gebruiker_id, jaar, verlof_totaal, verlof_overgedragen,
                     kd_totaal, kd_overgedragen, verlof_opgenomen, kd_opgenomen,
                     opmerking, aangemaakt_op)
                    VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
                """, (gebruiker_id, jaar, vv_totaal, vv_overgedragen,
                      kd_totaal, kd_overgedragen, opmerking, now))

            conn.commit()
            return True

        except Exception as e:
            print(f"Error updating saldo: {e}")
            conn.rollback()
            return False

    @staticmethod
    def bereken_opgenomen_uit_aanvragen(gebruiker_id: int, jaar: int) -> tuple[int, int]:
        """
        Bereken opgenomen VV en KD uit goedgekeurde verlof_aanvragen.
        Gebruikt term-based matching (code-onafhankelijk).

        Args:
            gebruiker_id: ID van de gebruiker
            jaar: Jaar

        Returns:
            Tuple (vv_dagen, kd_dagen)
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Query via TERM, niet via code!
        cursor.execute("""
            SELECT
                toegekende_code_term,
                start_datum,
                eind_datum
            FROM verlof_aanvragen
            WHERE gebruiker_id = ?
              AND status = 'goedgekeurd'
              AND toegekende_code_term IN ('verlof', 'kompensatiedag')
              AND STRFTIME('%Y', start_datum) = ?
        """, (gebruiker_id, str(jaar)))

        vv_dagen = 0
        kd_dagen = 0

        for row in cursor.fetchall():
            # Bereken kalenderdagen tussen start en eind (inclusief weekends)
            dagen = VerlofSaldoService._bereken_werkdagen(
                row['start_datum'],
                row['eind_datum']
            )

            if row['toegekende_code_term'] == 'verlof':
                vv_dagen += dagen
            elif row['toegekende_code_term'] == 'kompensatiedag':
                kd_dagen += dagen

        return vv_dagen, kd_dagen

    @staticmethod
    def bereken_opgenomen_uit_planning(gebruiker_id: int, jaar: int) -> tuple[int, int]:
        """
        Bereken VV en KD uit planning tabel (backup/verificatie).
        Via JOIN met speciale_codes op term!

        Args:
            gebruiker_id: ID van de gebruiker
            jaar: Jaar

        Returns:
            Tuple (vv_dagen, kd_dagen)
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                sc.term,
                COUNT(*) as dagen
            FROM planning p
            JOIN speciale_codes sc ON p.shift_code = sc.code
            WHERE p.gebruiker_id = ?
              AND sc.term IN ('verlof', 'kompensatiedag')
              AND STRFTIME('%Y', p.datum) = ?
            GROUP BY sc.term
        """, (gebruiker_id, str(jaar)))

        vv_dagen = 0
        kd_dagen = 0

        for row in cursor.fetchall():
            if row['term'] == 'verlof':
                vv_dagen = row['dagen']
            elif row['term'] == 'kompensatiedag':
                kd_dagen = row['dagen']

        return vv_dagen, kd_dagen

    @staticmethod
    def sync_saldo_naar_database(gebruiker_id: int, jaar: int):
        """
        Update verlof_opgenomen en kd_opgenomen in verlof_saldo tabel.
        Roep aan na elke wijziging in aanvragen of planning.

        Args:
            gebruiker_id: ID van de gebruiker
            jaar: Jaar
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Bereken opgenomen uit planning
        vv_opgenomen, kd_opgenomen = VerlofSaldoService.bereken_opgenomen_uit_planning(
            gebruiker_id, jaar
        )

        # Update database
        cursor.execute("""
            UPDATE verlof_saldo
            SET verlof_opgenomen = ?,
                kd_opgenomen = ?,
                gewijzigd_op = ?
            WHERE gebruiker_id = ? AND jaar = ?
        """, (vv_opgenomen, kd_opgenomen, datetime.now().isoformat(),
              gebruiker_id, jaar))

        conn.commit()

    @staticmethod
    def check_voldoende_saldo(gebruiker_id: int, jaar: int,
                               code_term: str, dagen: int) -> tuple[bool, str]:
        """
        Check of gebruiker voldoende saldo heeft.

        Args:
            gebruiker_id: ID van de gebruiker
            jaar: Jaar
            code_term: 'verlof' of 'kompensatiedag'
            dagen: Aantal aangevraagde dagen

        Returns:
            Tuple (voldoende: bool, bericht: str)
        """
        saldo = VerlofSaldoService.get_saldo(gebruiker_id, jaar)

        if code_term == 'verlof':
            resterend = saldo['vv_resterend']
            type_naam = "verlof"
        elif code_term == 'kompensatiedag':
            resterend = saldo['kd_resterend']
            type_naam = "KD"
        else:
            return False, f"Onbekende code term: {code_term}"

        if resterend >= dagen:
            return True, f"Voldoende {type_naam} saldo ({resterend} dagen)"
        else:
            tekort = dagen - resterend
            return False, f"Onvoldoende {type_naam} saldo (tekort: {tekort} dagen, resterend: {resterend})"

    @staticmethod
    def _bereken_werkdagen(start_datum_str: str, eind_datum_str: str) -> int:
        """
        Bereken aantal kalenderdagen tussen start en eind datum.
        Inclusief weekends en feestdagen.

        Args:
            start_datum_str: Start datum (ISO format YYYY-MM-DD)
            eind_datum_str: Eind datum (ISO format YYYY-MM-DD)

        Returns:
            Aantal kalenderdagen (inclusief weekends)
        """
        # Parse datums
        start = datetime.strptime(start_datum_str, '%Y-%m-%d').date()
        eind = datetime.strptime(eind_datum_str, '%Y-%m-%d').date()

        # Bereken aantal dagen (inclusief start en eind dag)
        return (eind - start).days + 1

    @staticmethod
    def get_alle_saldi(jaar: int, alleen_actief: bool = True) -> list[dict]:
        """
        Haal alle saldi op voor een jaar (voor admin scherm).

        Args:
            jaar: Jaar
            alleen_actief: Alleen actieve gebruikers tonen

        Returns:
            List van dictionaries met gebruiker info + saldo
        """
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                g.id as gebruiker_id,
                g.volledige_naam as naam,
                g.gebruikersnaam,
                g.is_reserve,
                vs.verlof_totaal,
                vs.verlof_overgedragen,
                vs.verlof_opgenomen,
                vs.kd_totaal,
                vs.kd_overgedragen,
                vs.kd_opgenomen,
                vs.opmerking
            FROM gebruikers g
            LEFT JOIN verlof_saldo vs ON g.id = vs.gebruiker_id AND vs.jaar = ?
            WHERE g.gebruikersnaam != 'admin'
        """

        if alleen_actief:
            query += " AND g.is_actief = 1"

        query += " ORDER BY g.volledige_naam"

        cursor.execute(query, (jaar,))

        resultaten = []
        for row in cursor.fetchall():
            # Bereken actuele opgenomen dagen uit planning
            vv_opgenomen, kd_opgenomen = VerlofSaldoService.bereken_opgenomen_uit_planning(
                row['gebruiker_id'], jaar
            )

            vv_totaal = row['verlof_totaal'] or 0
            vv_overgedragen = row['verlof_overgedragen'] or 0
            vv_resterend = vv_totaal + vv_overgedragen - vv_opgenomen

            kd_totaal = row['kd_totaal'] or 0
            kd_overgedragen = row['kd_overgedragen'] or 0
            kd_resterend = kd_totaal + kd_overgedragen - kd_opgenomen

            resultaten.append({
                'gebruiker_id': row['gebruiker_id'],
                'naam': row['naam'],
                'gebruikersnaam': row['gebruikersnaam'],
                'is_reserve': row['is_reserve'],
                'vv_totaal': vv_totaal,
                'vv_overgedragen': vv_overgedragen,
                'vv_opgenomen': vv_opgenomen,
                'vv_resterend': vv_resterend,
                'kd_totaal': kd_totaal,
                'kd_overgedragen': kd_overgedragen,
                'kd_opgenomen': kd_opgenomen,
                'kd_resterend': kd_resterend,
                'opmerking': row['opmerking'] or ''
            })

        return resultaten

    @staticmethod
    def maak_jaar_saldi_aan(jaar: int) -> int:
        """
        Maak saldo records aan voor alle actieve gebruikers voor een jaar.
        Gebruikt standaard waarden (0), moet handmatig ingevuld worden.

        Args:
            jaar: Jaar waarvoor saldi aangemaakt moeten worden

        Returns:
            Aantal aangemaakte records
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Haal alle actieve gebruikers (exclusief admin)
        cursor.execute("""
            SELECT id FROM gebruikers
            WHERE is_actief = 1 AND gebruikersnaam != 'admin'
        """)

        gebruikers = cursor.fetchall()
        aangemaakt = 0
        now = datetime.now().isoformat()

        for row in gebruikers:
            gebruiker_id = row['id']

            # Check of al bestaat
            cursor.execute("""
                SELECT id FROM verlof_saldo
                WHERE gebruiker_id = ? AND jaar = ?
            """, (gebruiker_id, jaar))

            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO verlof_saldo
                    (gebruiker_id, jaar, verlof_totaal, verlof_overgedragen,
                     kd_totaal, kd_overgedragen, verlof_opgenomen, kd_opgenomen,
                     opmerking, aangemaakt_op)
                    VALUES (?, ?, 0, 0, 0, 0, 0, 0, 'Handmatig in te vullen', ?)
                """, (gebruiker_id, jaar, now))
                aangemaakt += 1

        conn.commit()
        return aangemaakt
