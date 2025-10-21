"""
Term Code Service
Centrale service voor het ophalen van codes op basis van systeem-termen

GEBRUIK:
    from services.term_code_service import TermCodeService

    verlof_code = TermCodeService.get_code_for_term('verlof')
    # Returns: 'VV' (of wat de gebruiker heeft ingesteld)

CACHE:
- Bij eerste gebruik wordt de mapping geladen
- Refresh automatisch na wijzigingen in ShiftCodesScreen
- Bij ontbrekende term: fallback naar standaard codes

VERPLICHTE TERMEN:
- verlof (standaard: VV)
- kompensatiedag (standaard: KD)
- zondagrust (standaard: RX)
- zaterdagrust (standaard: CX)
- ziek (standaard: Z)
- arbeidsduurverkorting (standaard: DA)
"""

from typing import Dict, Optional
import sqlite3
from database.connection import get_connection


class TermCodeService:
    """Singleton service voor term→code mapping met cache"""

    # Cache: term → code mapping
    _cache: Dict[str, str] = {}
    _initialized: bool = False

    # Fallback codes als term niet gevonden wordt
    _FALLBACK_CODES = {
        'verlof': 'VV',
        'kompensatiedag': 'KD',
        'zondagrust': 'RX',
        'zaterdagrust': 'CX',
        'ziek': 'Z',
        'arbeidsduurverkorting': 'DA'
    }

    @classmethod
    def get_code_for_term(cls, term: str) -> str:
        """
        Haal code op voor een systeemterm

        Args:
            term: Systeem term (verlof, kompensatiedag, zondagrust, zaterdagrust, ziek, arbeidsduurverkorting)

        Returns:
            Code string (bijv. 'VV', 'RX', etc.)
            Bij ontbrekende term: fallback naar standaard code
        """
        # Laad cache bij eerste gebruik
        if not cls._initialized:
            cls.refresh()

        # Haal code uit cache
        code = cls._cache.get(term)

        if code:
            return code

        # Fallback naar standaard code
        fallback = cls._FALLBACK_CODES.get(term, '')

        if fallback:
            print(f"⚠ Waarschuwing: Term '{term}' heeft geen code in database, "
                  f"gebruik fallback '{fallback}'")

        return fallback

    @classmethod
    def get_all_term_codes(cls) -> Dict[str, str]:
        """
        Haal alle term→code mappings op

        Returns:
            Dictionary met term als key, code als value
        """
        if not cls._initialized:
            cls.refresh()

        return cls._cache.copy()

    @classmethod
    def refresh(cls):
        """
        Herlaad cache vanuit database
        Aanroepen na wijzigingen in speciale codes
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Haal alle codes met termen op
            cursor.execute("""
                SELECT term, code
                FROM speciale_codes
                WHERE term IS NOT NULL
            """)

            rows = cursor.fetchall()
            conn.close()

            # Update cache
            cls._cache.clear()
            for row in rows:
                cls._cache[row['term']] = row['code']

            cls._initialized = True

        except sqlite3.Error as e:
            print(f"❌ Fout bij laden term-code mapping: {e}")
            # Bij fout: gebruik fallback codes
            cls._cache = cls._FALLBACK_CODES.copy()
            cls._initialized = True

    @classmethod
    def validate_required_terms(cls) -> tuple[bool, list[str]]:
        """
        Valideer of alle verplichte termen aanwezig zijn

        Returns:
            (success: bool, missing_terms: list[str])
        """
        if not cls._initialized:
            cls.refresh()

        missing = []
        for term in cls._FALLBACK_CODES.keys():
            if term not in cls._cache:
                missing.append(term)

        return (len(missing) == 0, missing)

    @classmethod
    def reset(cls):
        """Reset cache (voor tests)"""
        cls._cache.clear()
        cls._initialized = False
