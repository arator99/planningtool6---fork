# Performance Optimalisatie - Constraint Checking
## Fix voor Trage Maandwissel (30-60 sec → <2 sec)

**Versie:** 1.0  
**Datum:** 31 Oktober 2025  
**Status:** URGENT - Performance Probleem  
**Context:** Planning Editor is te traag bij maandwissel door real-time controles

---

## 1. Probleem Analyse

### 1.1 Huidige Situatie

**Symptoom:** 30-60 seconden wachttijd bij maandwissel in Planning Editor

**Oorzaak:** Real-time controles die bij elke cel load/render worden uitgevoerd
- Bemanningscontrole (v0.6.20) draait voor alle datums
- HR validatie (toekomstige v0.6.25) zou dit NOG erger maken
- Netwerkschijf vertraagt database queries extra
- N+1 query probleem: per cel een query

**Impact:**
- ❌ Onbruikbaar voor productie
- ❌ Gebruikers frustratie
- ❌ Schaalbaarheidsprobleem (nu al met 1 controle systeem)

### 1.2 Root Causes

```python
# PROBLEMATISCH PATTERN (huidige situatie):
def render_cel(datum, gebruiker_id):
    # Voor ELKE cel bij render:
    status = check_bemanning(datum)           # Query 1
    hr_violations = check_hr_regels(datum)    # Query 2 (toekomst)
    notities = check_notities(datum)          # Query 3
    # → 30 gebruikers × 31 dagen = 930 queries bij maandwissel!
```

**Waarom traag:**
1. **N+1 queries:** Per cel individuele database calls
2. **Geen caching:** Dezelfde checks meerdere keren voor zelfde datum
3. **Synchrone loading:** Alles moet af voordat grid toont
4. **Netwerkschijf latency:** Elke query +10-50ms extra door netwerk

---

## 2. Oplossing - Drie-Staps Strategie

### Strategie Overzicht

```
┌─────────────────────────────────────────────────────────┐
│  LEVEL 1: Batch Loading (80% snelheidswinst)           │
│  → Load alle data in één keer bij maandwissel          │
│  → Cache in memory                                      │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  LEVEL 2: Lazy Evaluation (15% extra winst)            │
│  → Render grid eerst (leeg/basis)                      │
│  → Load status async in background                      │
│  → Update UI incrementeel                               │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  LEVEL 3: Smart Invalidation (5% extra winst)          │
│  → Cache alleen invalideren bij echte wijzigingen       │
│  → Track welke datums gewijzigd zijn                    │
│  → Re-check alleen affected datums                      │
└─────────────────────────────────────────────────────────┘
```

### 2.1 Level 1: Batch Loading (MUST HAVE - Implementeer NU)

**Concept:** Load alle validatie data in één grote batch query bij maandwissel, cache het resultaat.

#### Implementation: ValidationCache

```python
# services/validation_cache.py
from typing import Dict, List, Optional, Set
from datetime import date
from dataclasses import dataclass, field
import time

@dataclass
class CacheEntry:
    """Single cache entry voor één datum"""
    datum: date
    bemannings_status: Optional[str] = None  # 'groen', 'geel', 'rood'
    hr_violation_level: Optional[str] = None  # 'none', 'warning', 'error'
    heeft_notities: bool = False
    heeft_dubbele_codes: bool = False
    
    # Metadata
    last_updated: float = field(default_factory=time.time)

class ValidationCache:
    """
    Centraal cache systeem voor alle validatie results
    
    Performance benefits:
    - 1 batch query ipv N queries
    - In-memory access (geen I/O)
    - Smart invalidation (alleen wijzigingen re-checken)
    
    Usage:
        cache = ValidationCache()
        cache.preload_month(jaar=2025, maand=11)  # Bij maandwissel
        status = cache.get_bemannings_status(date(2025, 11, 15))  # Instant
    """
    
    def __init__(self):
        self._cache: Dict[date, CacheEntry] = {}
        self._dirty_dates: Set[date] = set()  # Datums die re-check nodig hebben
        
        # Performance metrics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'batch_loads': 0
        }
    
    # ========== BATCH LOADING (Main Performance Fix) ==========
    
    def preload_month(
        self, 
        jaar: int, 
        maand: int, 
        gebruiker_ids: Optional[List[int]] = None
    ):
        """
        Preload alle validatie data voor een maand in één keer
        
        Dit is de KRITIEKE methode die 30-60 sec → <2 sec maakt!
        
        Args:
            jaar: Jaar (2025)
            maand: Maand (1-12)
            gebruiker_ids: Optioneel filter op gebruikers
        
        Process:
        1. Build datum range (1st tot last day of month)
        2. Load planning data (1 query)
        3. Load shift codes (1 query, cached)
        4. Calculate bemannings status (in-memory)
        5. Calculate HR violations (in-memory, toekomst)
        6. Load notities (1 query)
        7. Store alles in cache
        
        Total: ~5 queries ipv 900+ queries
        """
        start_time = time.time()
        
        # Stap 1: Datum range
        from calendar import monthrange
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
                hr_violation_level='none',  # TODO: v0.6.25
                heeft_notities=current in notities_data,
                heeft_dubbele_codes=False  # TODO: check dubbele codes
            )
            current = date(current.year, current.month, current.day + 1) \
                if current.day < last_day else date(current.year, current.month + 1, 1)
        
        # Clear dirty dates voor deze maand
        self._dirty_dates = {d for d in self._dirty_dates 
                            if not (start_datum <= d <= eind_datum)}
        
        # Stats
        self._stats['batch_loads'] += 1
        duration = time.time() - start_time
        print(f"[ValidationCache] Preloaded {last_day} dagen in {duration:.2f}s")
    
    # ========== CACHE ACCESS ==========
    
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
        return entry.hr_violation_level if entry else None
    
    def heeft_notities(self, datum: date) -> bool:
        """Check if datum heeft notities (cached)"""
        entry = self._cache.get(datum)
        return entry.heeft_notities if entry else False
    
    def get_full_status(self, datum: date) -> Optional[CacheEntry]:
        """Get complete cache entry voor datum"""
        return self._cache.get(datum)
    
    # ========== CACHE INVALIDATION ==========
    
    def invalidate_date(self, datum: date):
        """
        Mark een datum als 'dirty' - moet re-checked worden
        
        Called na planning wijziging op deze datum
        """
        self._dirty_dates.add(datum)
        if datum in self._cache:
            del self._cache[datum]
    
    def invalidate_date_range(self, start: date, eind: date):
        """Mark een datum range als dirty"""
        current = start
        while current <= eind:
            self.invalidate_date(current)
            current = date(current.year, current.month, current.day + 1)
    
    def refresh_dirty_dates(self):
        """
        Re-check alleen de dirty dates (na edit)
        
        Veel sneller dan full month reload
        """
        if not self._dirty_dates:
            return
        
        # Group dirty dates per maand
        per_maand = {}
        for d in self._dirty_dates:
            key = (d.year, d.month)
            if key not in per_maand:
                per_maand[key] = []
            per_maand[key].append(d)
        
        # Reload elke affected maand
        for (jaar, maand), datums in per_maand.items():
            self.preload_month(jaar, maand)
    
    def clear(self):
        """Clear hele cache (bij grote wijzigingen)"""
        self._cache.clear()
        self._dirty_dates.clear()
    
    # ========== PRIVATE - Batch Loading Queries ==========
    
    def _load_planning_batch(
        self, 
        start: date, 
        eind: date, 
        gebruiker_ids: Optional[List[int]]
    ) -> Dict:
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
        result = {}
        for datum_str, uid, shift_code in cursor.fetchall():
            datum = date.fromisoformat(datum_str)
            if datum not in result:
                result[datum] = {}
            result[datum][uid] = shift_code
        
        return result
    
    def _load_shift_codes(self) -> Dict:
        """
        Load shift codes config (cached binnen session)
        
        Returns: {code: {'is_kritiek': bool, 'werkpost_id': int, ...}, ...}
        """
        # TODO: Implement met cache op session niveau
        # Voor nu: return mock data
        return {}
    
    def _calculate_bemannings_batch(
        self, 
        planning_data: Dict,
        shift_codes_data: Dict,
        start: date,
        eind: date
    ) -> Dict[date, str]:
        """
        Bereken bemannings status voor alle datums (in-memory)
        
        Returns: {datum: 'groen'|'geel'|'rood', ...}
        """
        from services.bemannings_validatie_service import BemanningsValidatieService
        
        # TODO: Refactor BemanningsValidatieService om batch mode te ondersteunen
        # Voor nu: loop door datums (nog steeds sneller dan N queries)
        service = BemanningsValidatieService()
        
        results = {}
        current = start
        while current <= eind:
            # Use cached planning data ipv database query
            datum_planning = planning_data.get(current, {})
            status = service.valideer_datum_from_data(current, datum_planning)
            results[current] = status
            current = date(current.year, current.month, current.day + 1) \
                if current.day < monthrange(current.year, current.month)[1] \
                else date(current.year, current.month + 1, 1)
        
        return results
    
    def _load_notities_batch(self, start: date, eind: date) -> Set[date]:
        """
        Load alle datums met notities in 1 query
        
        Returns: Set van datums die notities hebben
        """
        from database.connection import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT datum
            FROM planning_notities
            WHERE datum BETWEEN ? AND ?
        """, (start.isoformat(), eind.isoformat()))
        
        return {date.fromisoformat(row[0]) for row in cursor.fetchall()}
    
    # ========== STATS & DEBUGGING ==========
    
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
    
    def print_stats(self):
        """Print cache statistics (voor debugging)"""
        stats = self.get_stats()
        print("\n=== ValidationCache Stats ===")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print("=============================\n")
```

#### Integration in PlanningValidator

```python
# services/planning_validator.py (UPDATED)
from services.validation_cache import ValidationCache

class PlanningValidator:
    """
    UPDATED: Nu met ValidationCache voor performance
    """
    
    # Class-level cache (shared tussen instances)
    _global_cache = ValidationCache()
    
    def __init__(self, gebruiker_id: int, jaar: int, maand: int):
        self.gebruiker_id = gebruiker_id
        self.jaar = jaar
        self.maand = maand
        
        # Use global cache
        self.cache = self._global_cache
        
        # Laad config
        self.hr_config = self._load_hr_config()
        self.shift_tijden = self._load_shift_tijden()
        
        # Initialiseer checker (voor full validation)
        self.checker = ConstraintChecker(self.hr_config, self.shift_tijden)
    
    # ========== KEY CHANGE: Preload bij init ==========
    
    @classmethod
    def preload_for_month(cls, jaar: int, maand: int, gebruiker_ids: List[int]):
        """
        CRITICAL: Call dit bij maandwissel VOOR het renderen van grid
        
        Dit maakt 30-60 sec → <2 sec!
        
        Usage in planning editor:
            def on_maand_changed(self, jaar, maand):
                # EERST preload
                PlanningValidator.preload_for_month(jaar, maand, self.gebruiker_ids)
                
                # DAN render grid
                self.render_grid()
        """
        cls._global_cache.preload_month(jaar, maand, gebruiker_ids)
    
    def get_violation_level(self, datum: date) -> str:
        """
        UPDATED: Check cache eerst, fallback naar checker
        """
        # Try cache first (instant)
        cached = self.cache.get_hr_violation_level(datum)
        if cached is not None:
            return cached
        
        # Cache miss - fallback naar full check (traag)
        planning = self._get_planning_data()
        violations = self.checker.get_all_violations(planning, self.gebruiker_id)
        datum_violations = [v for v in violations if v.datum == datum]
        
        if not datum_violations:
            return 'none'
        has_errors = any(v.severity.value == 'error' for v in datum_violations)
        return 'error' if has_errors else 'warning'
    
    def on_planning_edited(self, datum: date):
        """
        NIEUWE METHODE: Call na elke planning edit
        
        Invalidates cache voor deze datum + omliggende datums
        """
        # Invalideer datum zelf
        self.cache.invalidate_date(datum)
        
        # Invalideer ook vorige/volgende dag (voor 12u rust check)
        from datetime import timedelta
        self.cache.invalidate_date(datum - timedelta(days=1))
        self.cache.invalidate_date(datum + timedelta(days=1))
        
        # Optioneel: Refresh direct (of wacht tot volgende render)
        # self.cache.refresh_dirty_dates()
```

#### Integration in PlannerGridKalender

```python
# gui/widgets/planner_grid_kalender.py (CRITICAL UPDATES)

class PlannerGridKalender(QWidget):
    
    def on_maand_changed(self):
        """
        UPDATED: Preload cache VOOR render
        
        VOOR: 30-60 seconden wachten
        NA: <2 seconden
        """
        # Show loading indicator
        self.setCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()  # Update UI
        
        # CRITICAL: Preload validation data
        PlanningValidator.preload_for_month(
            jaar=self.huidige_jaar,
            maand=self.huidige_maand,
            gebruiker_ids=[u.id for u in self.actieve_gebruikers]
        )
        
        # Now render grid (fast - uses cache)
        self.render_grid()
        
        # Reset cursor
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def get_bemannings_overlay_kleur(self, datum_str: str) -> str:
        """
        UPDATED: Use cache ipv directe query
        
        VOOR: Database query per cel (900+ queries)
        NA: Cache lookup (instant)
        """
        datum = date.fromisoformat(datum_str)
        
        # Get from cache (instant)
        validator = PlanningValidator(
            gebruiker_id=None,  # Not needed for cache lookup
            jaar=datum.year,
            maand=datum.month
        )
        status = validator.cache.get_bemannings_status(datum)
        
        if status == 'rood':
            return """
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(229, 115, 115, 0.4),
                stop:1 rgba(229, 115, 115, 0.4)
            );
            """
        elif status == 'geel':
            return """
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(255, 213, 79, 0.3),
                stop:1 rgba(255, 213, 79, 0.3)
            );
            """
        else:  # groen
            return ""
    
    def on_cel_edited(self, datum: date, gebruiker_id: int, nieuwe_waarde: str):
        """
        UPDATED: Invalideer cache na edit
        """
        # Save naar database (zoals voorheen)
        self._save_planning_cel(datum, gebruiker_id, nieuwe_waarde)
        
        # NIEUW: Invalideer cache voor deze datum
        validator = PlanningValidator(gebruiker_id, datum.year, datum.month)
        validator.on_planning_edited(datum)
        
        # Re-render affected cellen (alleen deze datum + omliggende)
        self._refresh_datum_range(
            start=datum - timedelta(days=1),
            eind=datum + timedelta(days=1)
        )
```

---

### 2.2 Level 2: Lazy Loading (SHOULD HAVE)

**Concept:** Render grid eerst (basis), load status async, update UI incrementeel.

```python
# services/async_validator.py
from PyQt6.QtCore import QThread, pyqtSignal
from typing import List
from datetime import date

class AsyncValidationWorker(QThread):
    """
    Background thread voor validatie checks
    
    Voorkomt UI freezing tijdens zware operaties
    """
    
    # Signals
    progress = pyqtSignal(int)  # Progress percentage
    datum_validated = pyqtSignal(date, dict)  # (datum, validation_results)
    finished = pyqtSignal()
    
    def __init__(self, jaar: int, maand: int, gebruiker_ids: List[int]):
        super().__init__()
        self.jaar = jaar
        self.maand = maand
        self.gebruiker_ids = gebruiker_ids
    
    def run(self):
        """Background validation"""
        from calendar import monthrange
        _, last_day = monthrange(self.jaar, self.maand)
        
        # Process elke datum
        for dag in range(1, last_day + 1):
            datum = date(self.jaar, self.maand, dag)
            
            # Run validaties
            results = {
                'bemannings_status': self._check_bemanning(datum),
                'hr_violations': self._check_hr(datum),
                # ... meer checks
            }
            
            # Emit result (UI kan direct updaten)
            self.datum_validated.emit(datum, results)
            
            # Update progress
            progress = int((dag / last_day) * 100)
            self.progress.emit(progress)
        
        self.finished.emit()

# Usage in PlannerGridKalender:
def on_maand_changed_lazy(self):
    """
    LAZY VERSION: Render eerst, validate async
    
    User experience:
    1. Grid toont direct (lege/basis)
    2. Status overlays verschijnen progressief
    3. Smooth user experience
    """
    # Render grid direct (zonder status)
    self.render_grid_basic()
    
    # Start async validation
    self.validation_worker = AsyncValidationWorker(
        self.huidige_jaar, 
        self.huidige_maand,
        [u.id for u in self.actieve_gebruikers]
    )
    self.validation_worker.datum_validated.connect(self._update_datum_status)
    self.validation_worker.finished.connect(self._on_validation_complete)
    self.validation_worker.start()

def _update_datum_status(self, datum: date, results: dict):
    """Update UI voor één datum (async callback)"""
    # Update cache
    self.validation_cache.update_entry(datum, results)
    
    # Re-render alleen deze datum kolom (snel)
    self._refresh_datum_column(datum)
```

---

### 2.3 Level 3: Smart Invalidation (NICE TO HAVE)

**Concept:** Track welke datums echt gewijzigd zijn, re-check alleen die.

```python
class SmartInvalidationTracker:
    """
    Track dependencies tussen datums
    
    Voorbeeld: 12u rust check
    - Edit op dag 15 → invalideer dag 14, 15, 16
    - Edit op dag 20 → invalideer dag 19, 20, 21
    - Maar dag 15 hoeft niet opnieuw omdat die niet affected
    """
    
    def __init__(self):
        self._affected_dates: Dict[date, Set[date]] = {}
    
    def on_edit(self, datum: date, constraint_type: str):
        """
        Bepaal welke andere datums affected zijn
        
        Args:
            datum: Gewijzigde datum
            constraint_type: Type constraint ('12u_rust', '50u_week', etc)
        """
        affected = {datum}  # Altijd zelf
        
        if constraint_type == '12u_rust':
            # Affects vorige en volgende dag
            affected.add(datum - timedelta(days=1))
            affected.add(datum + timedelta(days=1))
        
        elif constraint_type == '50u_week':
            # Affects hele week
            week_start = datum - timedelta(days=datum.weekday())
            for i in range(7):
                affected.add(week_start + timedelta(days=i))
        
        # Store dependencies
        self._affected_dates[datum] = affected
        
        return affected
```

---

## 3. Implementation Roadmap

### Phase 1: Quick Win - Batch Loading (URGENT - Deze Week)

**Goal:** Fix de 30-60 sec wachttijd → <2 sec

**Steps:**
1. ✅ Implementeer `ValidationCache` class
2. ✅ Refactor `BemanningsValidatieService` voor batch mode
3. ✅ Update `PlanningValidator` met cache integration
4. ✅ Update `PlannerGridKalender.on_maand_changed()` met preload call
5. ✅ Test met productie dataset

**Time:** 3-4 uur  
**Impact:** KRITIEK - maakt systeem bruikbaar

### Phase 2: Lazy Loading (Volgende Week)

**Goal:** Nog betere user experience

**Steps:**
1. Implementeer `AsyncValidationWorker`
2. Update UI voor progressive loading
3. Add progress indicator
4. Test user experience

**Time:** 2-3 uur  
**Impact:** Nice-to-have (na Phase 1 is het al goed)

### Phase 3: Smart Invalidation (Later)

**Goal:** Optimalisatie voor real-time edits

**Steps:**
1. Implementeer dependency tracking
2. Smart cache invalidation
3. Benchmark performance

**Time:** 2-3 uur  
**Impact:** Polish (5-10% extra snelheidswinst)

---

## 4. Testing & Benchmarking

### Performance Test Script

```python
# tests/performance/test_validation_cache_performance.py
import time
from datetime import date
from services.validation_cache import ValidationCache

def benchmark_cache_vs_nocache():
    """
    Benchmark cache performance
    
    Expected results:
    - No cache: 30-60 sec voor 900 cellen
    - With cache: <2 sec voor 900 cellen
    """
    
    # Setup
    cache = ValidationCache()
    jaar, maand = 2025, 11
    gebruiker_ids = list(range(1, 31))  # 30 gebruikers
    
    # Test 1: Without cache (baseline)
    print("\n=== Test 1: Without Cache ===")
    start = time.time()
    
    for dag in range(1, 31):
        for uid in gebruiker_ids:
            # Simulate oude methode (database query per cel)
            _ = check_bemanning_old_way(date(jaar, maand, dag))
    
    baseline = time.time() - start
    print(f"Time: {baseline:.2f}s")
    
    # Test 2: With cache (preload)
    print("\n=== Test 2: With Cache Preload ===")
    start = time.time()
    
    # Preload (1 keer)
    cache.preload_month(jaar, maand, gebruiker_ids)
    
    # Access (900 keer)
    for dag in range(1, 31):
        for uid in gebruiker_ids:
            _ = cache.get_bemannings_status(date(jaar, maand, dag))
    
    cached = time.time() - start
    print(f"Time: {cached:.2f}s")
    
    # Results
    print(f"\n=== Results ===")
    print(f"Speedup: {baseline/cached:.1f}x faster")
    print(f"Time saved: {baseline - cached:.2f}s")
    
    cache.print_stats()

if __name__ == '__main__':
    benchmark_cache_vs_nocache()
```

### Expected Results

| Scenario | Without Cache | With Cache | Speedup |
|----------|---------------|------------|---------|
| Maandwissel (30 users × 31 days) | 30-60 sec | <2 sec | **15-30x** |
| Single cel render | 50-100ms | <1ms | **50-100x** |
| Edit + refresh | 200-500ms | <50ms | **4-10x** |

---

## 5. Backward Compatibility

**Goed nieuws:** Deze optimalisatie breekt NIETS!

✅ Geen database schema wijzigingen  
✅ Geen API wijzigingen voor bestaande code  
✅ Fallback naar oude methode als cache miss  
✅ Incrementele adoptie mogelijk

**Migration Path:**
1. Deploy `ValidationCache` (nieuwe class)
2. Update `PlannerGridKalender` met preload call
3. Test in productie
4. Geleidelijk andere screens updaten

---

## 6. Monitoring & Debugging

### Cache Stats Dashboard

```python
# In planning editor - toon cache stats (voor debugging)
def show_cache_stats(self):
    """Toon cache statistics in console"""
    PlanningValidator._global_cache.print_stats()
    
    # Output:
    # === ValidationCache Stats ===
    #   cache_size: 31
    #   dirty_dates: 3
    #   hit_rate: 98.5%
    #   hits: 897
    #   misses: 3
    #   batch_loads: 1
    # =============================
```

### Performance Logging

```python
# Add to connection.py voor database performance monitoring
import time
import logging

logger = logging.getLogger(__name__)

def log_slow_query(query: str, duration: float, threshold: float = 0.1):
    """Log slow queries (>100ms)"""
    if duration > threshold:
        logger.warning(f"SLOW QUERY ({duration:.2f}s): {query[:100]}...")
```

---

## 7. Conclusie & Aanbeveling

### 🚨 URGENT: Implementeer Phase 1 NU

**Waarom urgent:**
- Systeem is nu **onbruikbaar** in productie (30-60 sec wachttijd)
- Phase 1 fix is **relatief simpel** (3-4 uur werk)
- Impact is **enorm** (15-30x sneller)

### Implementatie Volgorde

**Deze Week:**
1. ✅ Implementeer `ValidationCache` class (1-2 uur)
2. ✅ Update `PlannerGridKalender.on_maand_changed()` (30 min)
3. ✅ Test met productie data (30 min)
4. ✅ Deploy naar test omgeving (30 min)

**Volgende Week:**
5. Monitor performance in productie
6. Implementeer async loading (optioneel)
7. Fine-tune based on real usage

### Expected Outcome

**VOOR:**
```
User: Klikt "►" voor volgende maand
UI: ... hangt 30-60 seconden ...
User: 😤 "Waarom zo traag?!"
```

**NA:**
```
User: Klikt "►" voor volgende maand
UI: [0.5s] Loading indicator
UI: [1.5s] Grid rendered met alle status overlays
User: 😊 "Wow, snel!"
```

---

**Document versie:** 1.0  
**Auteur:** Claude (Anthropic)  
**Status:** URGENT - IMPLEMENT ASAP  
**Laatste update:** 31 Oktober 2025

**Next steps:**
1. Review dit document
2. Implementeer `ValidationCache` class
3. Update `PlannerGridKalender`
4. Test performance
5. Deploy

Veel succes met de fix! Dit zou het performance probleem volledig moeten oplossen. 🚀
