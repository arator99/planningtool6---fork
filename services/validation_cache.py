# services/validation_cache.py
"""
Validation Cache Service
v0.6.25 - PERFORMANCE OPTIMALISATIE

Centraal cache systeem voor alle validatie resultaten.
Voorkomt N+1 query probleem bij grid rendering.

PERFORMANCE BENEFITS:
- Batch loading: 1 query ipv 900+ queries
- In-memory access: Geen I/O overhead
- Smart invalidation: Alleen wijzigingen re-checken

USAGE:
    # Bij maandwissel:
    ValidationCache.get_instance().preload_month(jaar=2025, maand=11)

    # Bij cel render:
    status = ValidationCache.get_instance().get_bemannings_status(datum)

    # Na planning edit:
    ValidationCache.get_instance().invalidate_date(datum)

TARGET:
- Maandwissel: 30-60s → <2s (15-30x sneller)
- Cel render: 50-100ms → <1ms (50-100x sneller)

Zie: refactor performance/PERFORMANCE_OPTIMALISATIE_CONSTRAINT_CHECKING.md
"""
from typing import Dict, List, Optional, Set
from datetime import date, timedelta
from dataclasses import dataclass, field
from calendar import monthrange
import time


@dataclass
class CacheEntry:
    """
    Single cache entry voor één datum

    Bevat alle validatie resultaten die nodig zijn voor UI rendering
    """
    datum: date
    bemannings_status: Optional[str] = None  # 'groen', 'geel', 'rood'
    hr_violation_level: Optional[str] = None  # 'none', 'warning', 'error'
    heeft_notities: bool = False
    heeft_dubbele_codes: bool = False

    # Metadata
    last_updated: float = field(default_factory=time.time)


class ValidationCache:
    """
    Singleton cache voor validatie resultaten

    CRITICAL voor performance: voorkomt N+1 queries bij grid rendering
    """

    _instance: Optional['ValidationCache'] = None

    def __init__(self):
        """Private constructor - gebruik get_instance()"""
        self._cache: Dict[date, CacheEntry] = {}
        self._dirty_dates: Set[date] = set()  # Datums die re-check nodig hebben

        # Performance metrics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'batch_loads': 0
        }

    @classmethod
    def get_instance(cls) -> 'ValidationCache':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = ValidationCache()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (voor testing)"""
        cls._instance = None

    # ========================================================================
    # BATCH LOADING (Main Performance Fix)
    # ========================================================================

    def preload_month(
        self,
        jaar: int,
        maand: int,
        gebruiker_ids: Optional[List[int]] = None
    ) -> None:
        """
        Preload alle validatie data voor een maand in één keer

        KRITIEKE METHODE: 30-60 sec → <2 sec!

        Process:
        1. Bepaal datum range (1st tot last day of month)
        2. Batch load planning data (1 query)
        3. Batch load shift codes (1 query, cached)
        4. Calculate bemannings status (in-memory)
        5. Load notities (1 query)
        6. Store alles in cache

        Total: ~5 queries ipv 900+ queries

        Args:
            jaar: Jaar (2025)
            maand: Maand (1-12)
            gebruiker_ids: Optioneel filter op gebruikers (voor snelheid)
        """
        start_time = time.time()

        # Stap 1: Datum range
        _, last_day = monthrange(jaar, maand)
        start_datum = date(jaar, maand, 1)
        eind_datum = date(jaar, maand, last_day)

        # Stap 2: Batch load planning data
        planning_data = self._load_planning_batch(
            start_datum, eind_datum, gebruiker_ids
        )

        # Stap 3: Load shift codes (eenmalig, cache this)
        shift_codes_data = self._load_shift_codes()

        # Stap 4: Bereken bemannings status (in-memory)
        bemannings_results = self._calculate_bemannings_batch(
            planning_data, shift_codes_data, start_datum, eind_datum
        )

        # Stap 5: Load notities
        notities_data = self._load_notities_batch(start_datum, eind_datum)

        # Stap 6: Build cache entries
        current = start_datum
        while current <= eind_datum:
            self._cache[current] = CacheEntry(
                datum=current,
                bemannings_status=bemannings_results.get(current, 'groen'),
                hr_violation_level='none',  # TODO: v0.6.25+ HR validatie
                heeft_notities=current in notities_data,
                heeft_dubbele_codes=False  # TODO: detect dubbele codes
            )

            # Next day
            current = current + timedelta(days=1)

        # Clear dirty dates voor deze maand
        self._dirty_dates = {
            d for d in self._dirty_dates
            if not (start_datum <= d <= eind_datum)
        }

        # Stats
        self._stats['batch_loads'] += 1
        duration = time.time() - start_time
        print(f"[ValidationCache] Preloaded {last_day} dagen in {duration:.2f}s")

    # ========================================================================
    # CACHE ACCESS
    # ========================================================================

    def get_bemannings_status(self, datum: date) -> Optional[str]:
        """
        Get cached bemannings status voor datum

        Returns: 'groen', 'geel', 'rood', or None if not cached
        """
        entry = self._cache.get(datum)
        if entry:
            self._stats['hits'] += 1
            return entry.bemannings_status
        else:
            self._stats['misses'] += 1
            return None

    def get_hr_violation_level(self, datum: date) -> Optional[str]:
        """Get cached HR violation level voor datum"""
        entry = self._cache.get(datum)
        if entry:
            self._stats['hits'] += 1
            return entry.hr_violation_level
        else:
            self._stats['misses'] += 1
            return None

    def heeft_notities(self, datum: date) -> bool:
        """Check if datum heeft notities (cached)"""
        entry = self._cache.get(datum)
        return entry.heeft_notities if entry else False

    def get_full_status(self, datum: date) -> Optional[CacheEntry]:
        """Get complete cache entry voor datum"""
        return self._cache.get(datum)

    # ========================================================================
    # CACHE INVALIDATION
    # ========================================================================

    def invalidate_date(self, datum: date) -> None:
        """
        Mark een datum als 'dirty' - moet re-checked worden

        Called na planning wijziging op deze datum
        """
        self._dirty_dates.add(datum)
        if datum in self._cache:
            del self._cache[datum]

    def invalidate_date_range(self, start: date, eind: date) -> None:
        """Mark een datum range als dirty"""
        current = start
        while current <= eind:
            self.invalidate_date(current)
            current = current + timedelta(days=1)

    def refresh_dirty_dates(self) -> None:
        """
        Re-check alleen de dirty dates (na edit)

        Veel sneller dan full month reload
        """
        if not self._dirty_dates:
            return

        # Group dirty dates per maand
        per_maand: Dict[tuple, List[date]] = {}
        for d in self._dirty_dates:
            key = (d.year, d.month)
            if key not in per_maand:
                per_maand[key] = []
            per_maand[key].append(d)

        # Reload elke affected maand
        for (jaar, maand), datums in per_maand.items():
            self.preload_month(jaar, maand)

    def clear(self) -> None:
        """Clear hele cache (bij grote wijzigingen)"""
        self._cache.clear()
        self._dirty_dates.clear()

    # ========================================================================
    # PRIVATE - Batch Loading Queries
    # ========================================================================

    def _load_planning_batch(
        self,
        start: date,
        eind: date,
        gebruiker_ids: Optional[List[int]]
    ) -> Dict[date, Dict[int, str]]:
        """
        Load alle planning data voor periode in 1 query

        Returns: {datum: {gebruiker_id: shift_code, ...}, ...}
        """
        from database.connection import get_connection

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT datum, gebruiker_id, shift_code
            FROM planning
            WHERE datum BETWEEN ? AND ?
        """
        params = [start.isoformat(), eind.isoformat()]

        if gebruiker_ids:
            placeholders = ','.join('?' * len(gebruiker_ids))
            query += f" AND gebruiker_id IN ({placeholders})"
            params.extend(gebruiker_ids)

        cursor.execute(query, params)

        # Group by datum
        result: Dict[date, Dict[int, str]] = {}
        for row in cursor.fetchall():
            datum_str = row['datum']
            uid = row['gebruiker_id']
            shift_code = row['shift_code']

            # Parse datum
            datum = date.fromisoformat(datum_str) if isinstance(datum_str, str) else datum_str

            if datum not in result:
                result[datum] = {}
            result[datum][uid] = shift_code

        conn.close()
        return result

    def _load_shift_codes(self) -> Dict[str, Dict]:
        """
        Load shift codes config (cached binnen session)

        Returns: {code: {'is_kritisch': bool, 'werkpost_id': int, ...}, ...}
        """
        from database.connection import get_connection

        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Check which columns exist
            cursor.execute("PRAGMA table_info(shift_codes)")
            columns = [row[1] for row in cursor.fetchall()]
            has_kritisch = 'is_kritisch' in columns
            has_actief = 'is_actief' in columns

            # Build query based on available columns
            select_parts = ['code', 'werkpost_id']
            if has_kritisch:
                select_parts.append('is_kritisch')

            where_clause = 'WHERE is_actief = 1' if has_actief else ''

            query = f"SELECT {', '.join(select_parts)} FROM shift_codes {where_clause}"
            cursor.execute(query)

            result = {}
            for row in cursor.fetchall():
                result[row['code']] = {
                    'werkpost_id': row['werkpost_id'],
                    'is_kritisch': bool(row['is_kritisch']) if has_kritisch else True
                }

        except Exception as e:
            print(f"[ValidationCache] Fout bij laden shift codes: {e}")
            result = {}
        finally:
            conn.close()

        return result

    def _calculate_bemannings_batch(
        self,
        planning_data: Dict[date, Dict[int, str]],
        shift_codes_data: Dict[str, Dict],
        start: date,
        eind: date
    ) -> Dict[date, str]:
        """
        Bereken bemannings status voor alle datums (in-memory)

        Returns: {datum: 'groen'|'geel'|'rood', ...}
        """
        from services.bemannings_controle_service import valideer_datum_from_data

        results = {}
        current = start

        while current <= eind:
            # Use cached planning data ipv database query
            datum_planning = planning_data.get(current, {})

            # Valideer deze datum (in-memory)
            status = valideer_datum_from_data(current, datum_planning, shift_codes_data)
            results[current] = status

            # Next day
            current = current + timedelta(days=1)

        return results

    def _load_notities_batch(self, start: date, eind: date) -> Set[date]:
        """
        Load alle datums met notities in 1 query

        Returns: Set van datums die notities hebben
        """
        from database.connection import get_connection

        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Check if notities column exists
            cursor.execute("PRAGMA table_info(planning)")
            columns = [row[1] for row in cursor.fetchall()]
            has_notities = 'notities' in columns

            if has_notities:
                cursor.execute("""
                    SELECT DISTINCT datum
                    FROM planning
                    WHERE datum BETWEEN ? AND ?
                      AND (notities IS NOT NULL AND notities != '')
                """, (start.isoformat(), eind.isoformat()))

                result = set()
                for row in cursor.fetchall():
                    datum_str = row['datum']
                    datum = date.fromisoformat(datum_str) if isinstance(datum_str, str) else datum_str
                    result.add(datum)
            else:
                # Geen notities kolom - return empty set
                result = set()

        except Exception as e:
            print(f"[ValidationCache] Fout bij laden notities: {e}")
            result = set()
        finally:
            conn.close()

        return result

    # ========================================================================
    # STATS & DEBUGGING
    # ========================================================================

    def get_stats(self) -> Dict:
        """Get cache performance stats"""
        total = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0

        return {
            'cache_size': len(self._cache),
            'dirty_dates': len(self._dirty_dates),
            'hit_rate': f"{hit_rate:.1f}%",
            **self._stats
        }

    def print_stats(self) -> None:
        """Print cache statistics (voor debugging)"""
        stats = self.get_stats()
        print("\n=== ValidationCache Stats ===")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print("=============================\n")
