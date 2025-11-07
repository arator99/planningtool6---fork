# BACKUP: Grid Kalender Refactoring

**Datum:** 27 Oktober 2025
**Reden:** Backup voor refactoring v0.6.17 → v0.6.18
**Doel:** Code cleanup - elimineer 170 regels duplicatie

---

## 📦 BESTANDEN

- `grid_kalender_base_BEFORE_REFACTOR.py` (17K) - Base class
- `planner_grid_kalender_BEFORE_REFACTOR.py` (58K) - Planner widget
- `teamlid_grid_kalender_BEFORE_REFACTOR.py` (16K) - Teamlid widget

---

## 🔄 RESTORE INSTRUCTIES

**Indien refactoring problemen geeft:**

```bash
# Stap 1: Navigeer naar project root
cd "C:\Users\arato\PycharmProjects\planningstool 6 - claude"

# Stap 2: Kopieer backups terug
cp backups/refactoring_grid_kalenders_20251027/grid_kalender_base_BEFORE_REFACTOR.py gui/widgets/grid_kalender_base.py
cp backups/refactoring_grid_kalenders_20251027/planner_grid_kalender_BEFORE_REFACTOR.py gui/widgets/planner_grid_kalender.py
cp backups/refactoring_grid_kalenders_20251027/teamlid_grid_kalender_BEFORE_REFACTOR.py gui/widgets/teamlid_grid_kalender.py

# Stap 3: Verifieer
python main.py
```

**Alternatief (Windows PowerShell):**
```powershell
Copy-Item "backups\refactoring_grid_kalenders_20251027\*_BEFORE_REFACTOR.py" -Destination "gui\widgets\"
# Hernoem dan handmatig (verwijder _BEFORE_REFACTOR suffix)
```

---

## 📋 REFACTORING CHECKLIST

Zie: `REFACTORING_CHECKLIST_GRID_KALENDERS.md` in project root

---

## ⚠️ BELANGRIJK

**NIET VERWIJDEREN** totdat refactoring volledig getest en gecommit is!

**Minimale bewaarperiode:** 1 week na succesvolle refactoring

---

*Backup gemaakt door: Claude Code*
*Backup type: Pre-refactoring safety backup*
*Project: Planning Tool v0.6.17*
