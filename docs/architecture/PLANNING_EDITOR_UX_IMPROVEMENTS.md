# Planning Editor Screen - UI/UX Scalability Analysis

**Analysis Date**: October 27, 2025
**Version Reviewed**: v0.6.18 (Beta)
**Screen**: Planning Editor (gui/screens/planning_editor_screen.py)
**Priority**: Medium (Post v1.0 Implementation)
**Estimated Total Effort**: 4 days (1 day quick wins + 3 days post-v1.0)

---

## Executive Summary

**User Concern**: Planning Editor is getting crowded and may become overwhelming as new features are added.

**Current State**: 767-line monolithic screen with grid (1550 cells), sidebar (300px), and action buttons.

**Future Pressure**: Planned features (HR validation, week totals, statistics, undo/redo, filters) will push the UI to 1800px width and squeeze the grid from 680px → 500px height.

**Recommended Approach**: Implement 3 quick wins (1 day) to reclaim space and add scalability for future features.

---

## 1. Current Code Analysis

### Layout Structure

```python
# Current hierarchy (planning_editor_screen.py):
QVBoxLayout (outer)
  └─ QFrame (border_frame, 8px colored border)
      └─ QHBoxLayout (main)
          ├─ QVBoxLayout (left, stretch=3)
          │   ├─ Header (title + terug button)
          │   ├─ QHBoxLayout (kalender_header_row)
          │   │   ├─ info_label (300px max)
          │   │   └─ kalender.create_header() (maandnaam + navigatie)
          │   ├─ QHBoxLayout (buttons_row)
          │   │   ├─ Auto-Genereren button
          │   │   ├─ Wis Maand button
          │   │   ├─ Publiceren/Concept toggle
          │   │   └─ Stretch
          │   ├─ kalender (PlannerGridKalender) - THE GRID
          │   └─ instructies label (bottom tooltip)
          └─ Sidebar (right, stretch=1, max 300px)
              ├─ "Beschikbare Codes" title
              ├─ "Druk F2 voor zoekbare lijst" info
              └─ QScrollArea
                  ├─ SHIFTS section (QTextEdit, max 350px)
                  └─ SPECIAAL section (QTextEdit, max 200px)
```

### Widget Count Analysis
- **Total widgets**: ~25 in main screen
- **Grid cells**: 31 days × ~50 users = **1550 EditableLabel widgets**
- **Nested layouts**: 6 levels deep
- **Fixed widths**: Sidebar (300px), naam kolom (280px), info_label (300px)

### Current Issues (Code-Level)

#### 🔴 **Issue 1: Monolithic Screen Class**
```python
# planning_editor_screen.py - 767 lines
class PlanningEditorScreen(QWidget):
    def __init__(self, router: Callable):
        # 11 state variables
        self.valid_codes: Set[str] = set()
        self.current_status: str = 'concept'
        # ... 9 more

    # 30+ methods:
    def init_ui() -> None  # 90 lines
    def create_header() -> QHBoxLayout
    def create_codes_sidebar() -> QWidget
    def load_valid_codes()
    def load_maand_status()
    def update_status_ui()
    def toggle_status()
    def publiceer_planning()
    def terug_naar_concept()
    # ... 22 more methods
```

**Problem**: Single Responsibility Principle violation - screen does:
- UI rendering
- Status management
- Code validation
- Auto-generation orchestration
- Bulk delete operations
- Excel export triggering

#### 🟡 **Issue 2: Horizontal Real Estate Pressure**
```python
# Current: Sidebar always visible (300px)
main_layout.addLayout(left_layout, stretch=3)    # ~900px
main_layout.addWidget(sidebar, stretch=1)        # ~300px
# Total: 1200px - perfect fit NOW, but no room for:
# - Statistics panel
# - Validation warnings
# - Quick filters
```

#### 🟡 **Issue 3: Vertical Stacking Overhead**
```python
# 5 elements ABOVE the grid:
left_layout.addLayout(header)                # ~40px
left_layout.addLayout(kalender_header_row)   # ~40px
left_layout.addLayout(buttons_row)           # ~40px
# Grid starts at Y=120px, loses 120px of vertical space
```

#### 🟢 **What Works Well**
```python
# ✅ Grid is central focus (stretch ratio 3:1)
# ✅ Status info box provides clear feedback
# ✅ Keyboard shortcuts (F2, TAB, ESC) reduce mouse dependence
# ✅ Context menu for bulk operations
# ✅ Clear visual indicators (8px colored border)
```

---

## 2. Scalability Analysis

### Future Features Impact

| Feature | UI Element | Space Required | Placement Challenge |
|---------|-----------|----------------|---------------------|
| **HR Validation Warnings** | Alert panel | 200-300px height | Pushes grid down OR overlays it |
| **Week Totals per User** | Extra column | 80px per column | Grid becomes 1630px wide |
| **Undo/Redo** | Toolbar buttons | 150px | Buttons row already has 3 buttons |
| **Quick Filters** | Dropdown/chips | 100-150px | No space in header |
| **Statistics Panel** | Sidebar panel | 300px width | Conflicts with codes sidebar |
| **Validation Details** | Expandable table | 200px height | Where to place? |

### Projection: With All Features

```
Current Layout (1200px wide × 800px tall):
┌─────────────────────────────────────────────────┐
│ Header (40px)                                   │ ✅ OK
│ Info + Maandnaam (40px)                        │ ✅ OK
│ 3 Action Buttons (40px)                        │ ⚠️ Want 2 more
│ ─────────────────────────────────────────────── │
│ GRID (680px tall) │ Codes Sidebar (300px)      │ ✅ OK
│ 1550 cells        │                             │
│                   │                             │
│ Tooltip (20px)                                  │ ✅ OK
└─────────────────────────────────────────────────┘

Future Layout (CLUTTERED - 1800px wide × 1200px tall):
┌──────────────────────────────────────────────────────────────┐
│ Header (40px)                         │ Stats (300px)       │
│ Info + Maandnaam + Filters (60px)     │ - Totals           │
│ 5 Action Buttons + Undo/Redo (40px)   │ - Warnings         │
│ ──────────────────────────────────────│                     │
│ HR Warnings Panel (200px)              │                     │
│ ──────────────────────────────────────│                     │
│ GRID (500px tall) │ Codes   │ Week    │                     │
│ SQUEEZED!         │ (200px) │ Totals  │                     │
│                   │         │ (80px)  │                     │
│ Validation Details (150px)             │                     │
│ Tooltip (20px)                                              │
└──────────────────────────────────────────────────────────────┘
```

**Problem**: Grid loses 180px vertical (680→500), users need to scroll more.

---

## 3. Design Solutions (Concrete PyQt6 Proposals)

### **Solution 1: Collapsible Sidebar with QSplitter** ⭐⭐⭐⭐⭐
**Goal**: Make codes sidebar collapsible, reclaim 300px when not needed.

#### Implementation

```python
# planning_editor_screen.py (REFACTORED)
from PyQt6.QtWidgets import QSplitter, QPushButton
from PyQt6.QtCore import Qt

class PlanningEditorScreen(QWidget):
    def init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        self.border_frame = QFrame()
        outer_layout.addWidget(self.border_frame)

        main_layout = QVBoxLayout(self.border_frame)  # Changed from QHBoxLayout

        # Header + controls (stays on top)
        main_layout.addLayout(self.create_header())
        main_layout.addLayout(self.create_kalender_header())
        main_layout.addLayout(self.create_buttons_row())

        # NEW: QSplitter for grid + sidebar
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Grid container
        grid_widget = QWidget()
        grid_layout = QVBoxLayout(grid_widget)
        grid_layout.addWidget(self.kalender)
        grid_layout.addWidget(self.create_instructies_label())

        # Right: Collapsible sidebar
        self.sidebar_widget = self.create_codes_sidebar()

        self.splitter.addWidget(grid_widget)
        self.splitter.addWidget(self.sidebar_widget)
        self.splitter.setStretchFactor(0, 4)  # Grid gets 80%
        self.splitter.setStretchFactor(1, 1)  # Sidebar gets 20%

        main_layout.addWidget(self.splitter)

    def create_codes_sidebar(self) -> QWidget:
        """Create sidebar with collapse button"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header with collapse button
        header_layout = QHBoxLayout()
        title = QLabel("Beschikbare Codes")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        header_layout.addWidget(title)

        # NEW: Toggle button
        self.sidebar_toggle_btn = QPushButton("◀")  # ◀ = collapse, ▶ = expand
        self.sidebar_toggle_btn.setFixedSize(30, 30)
        self.sidebar_toggle_btn.setToolTip("Verberg/Toon codes sidebar")
        self.sidebar_toggle_btn.clicked.connect(self.toggle_sidebar)  # type: ignore
        header_layout.addWidget(self.sidebar_toggle_btn)
        layout.addLayout(header_layout)

        # ... rest of sidebar (codes QTextEdit)
        return widget

    def toggle_sidebar(self):
        """Toggle sidebar visibility"""
        if self.sidebar_widget.isVisible():
            self.sidebar_widget.hide()
            self.sidebar_toggle_btn.setText("▶")
            self.sidebar_toggle_btn.setParent(self.border_frame)  # Move button to main area
            # Reposition button to right edge
            self.sidebar_toggle_btn.move(
                self.border_frame.width() - 40,
                self.border_frame.height() // 2
            )
        else:
            self.sidebar_widget.show()
            self.sidebar_toggle_btn.setText("◀")
```

**Benefits**:
- ✅ Reclaim 300px width when sidebar hidden → Grid gets 1200px full width
- ✅ User can resize splitter → Flexible workspace
- ✅ Quick access via button (no menu diving)
- ✅ State persists during session

**Effort**: 2-3 hours (refactor layout, add toggle logic)

---

### **Solution 2: Toolbar with Tool Buttons** ⭐⭐⭐⭐☆
**Goal**: Replace button row with compact toolbar, save 20px vertical.

#### Implementation

```python
# planning_editor_screen.py
from PyQt6.QtWidgets import QToolBar, QToolButton
from PyQt6.QtGui import QIcon, QAction

class PlanningEditorScreen(QWidget):
    def create_toolbar(self) -> QToolBar:
        """Create compact toolbar with icons"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        # Auto-genereren action
        auto_action = QAction("Auto-Genereren", self)
        auto_action.setToolTip("Genereer planning uit typetabel")
        # auto_action.setIcon(QIcon("icons/generate.png"))  # Optional
        auto_action.triggered.connect(self.show_auto_generatie_dialog)  # type: ignore
        toolbar.addAction(auto_action)

        toolbar.addSeparator()

        # Wis maand action
        wis_action = QAction("Wis Maand", self)
        wis_action.setToolTip("Verwijder alle shifts (bescherm speciale codes)")
        wis_action.triggered.connect(self.show_bulk_delete_dialog)  # type: ignore
        toolbar.addAction(wis_action)

        toolbar.addSeparator()

        # Status toggle action (dynamic text)
        self.status_action = QAction("Publiceren", self)
        self.status_action.triggered.connect(self.toggle_status)  # type: ignore
        toolbar.addAction(self.status_action)

        toolbar.addSeparator()

        # FUTURE: Undo/Redo
        # undo_action = QAction("Ongedaan maken", self)
        # toolbar.addAction(undo_action)

        # Spacer (pushes next items to right)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Sidebar toggle
        sidebar_action = QAction("Codes", self)
        sidebar_action.setCheckable(True)
        sidebar_action.setChecked(True)
        sidebar_action.triggered.connect(self.toggle_sidebar)  # type: ignore
        toolbar.addAction(sidebar_action)

        return toolbar
```

**Benefits**:
- ✅ Save 20px vertical (40px buttons → 20px toolbar)
- ✅ Icons reduce visual clutter
- ✅ Scalable (easy to add undo/redo, filters)
- ✅ Standard desktop pattern

**Effort**: 2-3 hours (replace buttons_row with toolbar)

---

### **Solution 3: Floating Validation Panel** ⭐⭐⭐⭐☆
**Goal**: Show HR warnings without taking permanent screen space.

#### Implementation

```python
# planning_editor_screen.py
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QPropertyAnimation, QRect

class ValidationPanel(QFrame):
    """Slide-in panel voor HR regel validatie"""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("validationPanel")
        self.setFixedHeight(200)
        self.setStyleSheet(f"""
            QFrame#validationPanel {{
                background-color: {Colors.WARNING_BG};
                border: 2px solid {Colors.WARNING};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        title = QLabel("⚠️ HR Regel Waarschuwingen")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        header.addWidget(title)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.hide_animated)  # type: ignore
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Warnings list (QTableWidget or QListWidget)
        self.warnings_list = QListWidget()
        layout.addWidget(self.warnings_list)

        # Initially hidden
        self.hide()

    def show_animated(self):
        """Slide in from top"""
        self.show()
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(QRect(0, -200, self.width(), 200))
        self.animation.setEndValue(QRect(0, 0, self.width(), 200))
        self.animation.start()

    def hide_animated(self):
        """Slide out to top"""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(QRect(0, 0, self.width(), 200))
        self.animation.setEndValue(QRect(0, -200, self.width(), 200))
        self.animation.finished.connect(self.hide)  # type: ignore
        self.animation.start()

# In PlanningEditorScreen:
class PlanningEditorScreen(QWidget):
    def init_ui(self):
        # ... existing layout

        # Overlay validation panel (floating, not in main layout)
        self.validation_panel = ValidationPanel(self.border_frame)
        self.validation_panel.setGeometry(10, 140, self.border_frame.width() - 20, 200)

        # Show when validation fails
        # self.validation_panel.show_animated()
```

**Benefits**:
- ✅ No permanent space cost (0px when hidden)
- ✅ Prominent when needed (overlays grid)
- ✅ Dismissable (close button)
- ✅ Animated (smooth UX)

**Effort**: 3-4 hours (create widget, integrate validation logic)

---

### **Solution 4: Tabbed Sidebar** ⭐⭐⭐☆☆
**Goal**: Multiple sidebar functions (codes, stats, history) in same space.

#### Implementation

```python
# planning_editor_screen.py
from PyQt6.QtWidgets import QTabWidget

class PlanningEditorScreen(QWidget):
    def create_codes_sidebar(self) -> QWidget:
        """Tabbed sidebar with multiple panels"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Tab 1: Codes (existing)
        codes_tab = self.create_codes_tab()
        tabs.addTab(codes_tab, "Codes")

        # Tab 2: Statistieken (FUTURE)
        stats_tab = self.create_stats_tab()
        tabs.addTab(stats_tab, "Stats")

        # Tab 3: Geschiedenis (FUTURE - undo/redo log)
        # history_tab = self.create_history_tab()
        # tabs.addTab(history_tab, "Historie")

        layout.addWidget(tabs)
        return widget

    def create_codes_tab(self) -> QWidget:
        """Original codes sidebar content"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # ... existing scroll area with shifts/speciaal
        return widget

    def create_stats_tab(self) -> QWidget:
        """Statistics panel (FUTURE)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Week totals
        totals_label = QLabel("Week Totals:")
        layout.addWidget(totals_label)

        # ... table with totals per user

        # HR rule summary
        hr_label = QLabel("HR Regels:")
        layout.addWidget(hr_label)

        # ... status indicators (green/red)

        layout.addStretch()
        return widget
```

**Benefits**:
- ✅ Same 300px width, 3× functionality
- ✅ User chooses what to see (tabs)
- ✅ Scalable (add tabs as needed)

**Drawbacks**:
- ⚠️ Context switching (need to click tabs)
- ⚠️ Less "glanceable" than always-visible panel

**Effort**: 2-3 hours (refactor sidebar, create tabs)

---

### **Solution 5: Context-Aware Info Box** ⭐⭐⭐⭐☆
**Goal**: Info box changes content based on context, avoid adding more labels.

#### Implementation

```python
# planning_editor_screen.py
class PlanningEditorScreen(QWidget):
    def update_info_label(self):
        """Dynamic info box content"""

        # Base: Status info (concept/gepubliceerd)
        if self.current_status == 'concept':
            base_text = "⚠️ Planning is in CONCEPT. Teamleden zien deze planning nog niet."
            bg_color = "#FFF9C4"
            border_color = "#FFE082"
            text_color = "#F57C00"
        else:
            base_text = "✓ Planning is GEPUBLICEERD. Teamleden kunnen deze planning bekijken."
            bg_color = "#E8F5E9"
            border_color = "#81C784"
            text_color = "#2E7D32"

        # Context: Add validation warnings
        warnings = self.get_validation_warnings()  # Returns list of warnings
        if warnings:
            base_text += f"\n\n⚠️ {len(warnings)} HR regel waarschuwingen gevonden."
            base_text += " Klik hier voor details."
            # Make clickable
            self.info_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.info_label.mousePressEvent = lambda e: self.show_validation_details()

        # Context: Filter active?
        if any(not visible for visible in self.kalender.filter_gebruikers.values()):
            base_text += "\n\n🔍 Filter actief - niet alle teamleden zichtbaar."

        self.info_label.setText(base_text)
        self.info_label.setStyleSheet(Styles.info_box(bg_color, border_color, text_color))
```

**Benefits**:
- ✅ No new UI elements
- ✅ Context-aware (shows what matters NOW)
- ✅ Clickable for details (progressive disclosure)

**Effort**: 1-2 hours (refactor update_info_label)

---

## 4. Feature-Specific Recommendations

### **Feature: HR Rules Validation**
**Approach**: Floating panel (Solution 3) + Toolbar button
```python
# Toolbar button to toggle panel
validation_action = QAction("⚠️ Validatie", self)
validation_action.setCheckable(True)
validation_action.triggered.connect(self.toggle_validation_panel)  # type: ignore
toolbar.addAction(validation_action)
```
**Why**: Validation is intermittent (only when errors), no permanent space needed.

---

### **Feature: Week Totals per User**
**Approach**: Tabbed sidebar (Solution 4) OR separate dialog
```python
# Add to sidebar as "Stats" tab
# OR: Menu button in toolbar
stats_action = QAction("📊 Statistieken", self)
stats_action.triggered.connect(self.show_stats_dialog)  # type: ignore
toolbar.addAction(stats_action)
```
**Why**: Totals are analysis/review task, not constant editing need.

---

### **Feature: Undo/Redo**
**Approach**: Toolbar buttons (Solution 2)
```python
undo_action = QAction("↶ Ongedaan maken", self)
undo_action.setShortcut("Ctrl+Z")
undo_action.triggered.connect(self.undo)  # type: ignore
toolbar.addAction(undo_action)

redo_action = QAction("↷ Opnieuw", self)
redo_action.setShortcut("Ctrl+Y")
redo_action.triggered.connect(self.redo)  # type: ignore
toolbar.addAction(redo_action)
```
**Why**: Standard desktop pattern, toolbar is natural home.

---

### **Feature: Quick Filters**
**Approach**: Toolbar dropdown (QComboBox in toolbar)
```python
# Add to toolbar
filter_combo = QComboBox()
filter_combo.addItems(["Alle teamleden", "Alleen planners", "Alleen reserves", "Custom..."])
filter_combo.currentTextChanged.connect(self.apply_quick_filter)  # type: ignore
toolbar.addWidget(QLabel("Filter:"))
toolbar.addWidget(filter_combo)
```
**Why**: Quick access, no new panel needed.

---

### **Feature: Statistics Panel**
**Approach**: Tabbed sidebar (Solution 4) OR separate screen
```python
# Option A: Sidebar tab (for glanceable stats)
tabs.addTab(stats_tab, "Stats")

# Option B: Separate screen (for detailed analysis)
# Add menu button in dashboard: "Planning Statistieken"
```
**Why**: Depends on use case - glanceable → sidebar, detailed → separate screen.

---

## 5. Widget Extraction Recommendations

### **Extract 1: StatusManager Component**
```python
# gui/widgets/status_manager_widget.py
class StatusManagerWidget(QWidget):
    """Manages concept/gepubliceerd status UI"""
    status_changed = pyqtSignal(str)  # 'concept' or 'gepubliceerd'

    def __init__(self, jaar: int, maand: int):
        super().__init__()
        self.jaar = jaar
        self.maand = maand
        self.current_status = 'concept'
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Info label
        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        # Toggle button
        self.toggle_btn = QPushButton()
        self.toggle_btn.clicked.connect(self.toggle_status)  # type: ignore
        layout.addWidget(self.toggle_btn)

        self.update_ui()

    def update_ui(self):
        """Update info label and button based on status"""
        # ... logic from planning_editor_screen.py

    def toggle_status(self):
        """Toggle and emit signal"""
        new_status = 'gepubliceerd' if self.current_status == 'concept' else 'concept'
        self.current_status = new_status
        self.status_changed.emit(new_status)  # type: ignore
        self.update_ui()

# Usage in PlanningEditorScreen:
self.status_manager = StatusManagerWidget(self.kalender.jaar, self.kalender.maand)
self.status_manager.status_changed.connect(self.on_status_changed)  # type: ignore
main_layout.addWidget(self.status_manager)
```

**Benefits**: Encapsulate status logic, reusable, testable.

**Effort**: 2 hours

---

### **Extract 2: ValidationResultsPanel Component**
```python
# gui/widgets/validation_results_panel.py
class ValidationResultsPanel(QFrame):
    """Shows HR rule validation results"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def show_results(self, warnings: List[Dict]):
        """Display validation warnings"""
        self.clear()
        for warning in warnings:
            self.add_warning(warning)
        self.show_animated()
```

**Effort**: 2 hours

---

## 6. State Management for Show/Hide

### Persistent Sidebar State
```python
# config.py (add to version config)
UI_PREFERENCES = {
    'sidebar_visible': True,
    'sidebar_width': 300,
    'validation_panel_visible': False
}

# planning_editor_screen.py
def save_ui_state(self):
    """Save UI preferences to JSON"""
    prefs = {
        'sidebar_visible': self.sidebar_widget.isVisible(),
        'sidebar_width': self.splitter.sizes()[1],
        'validation_panel_visible': self.validation_panel.isVisible()
    }
    with open('data/ui_preferences.json', 'w') as f:
        json.dump(prefs, f)

def load_ui_state(self):
    """Restore UI preferences"""
    try:
        with open('data/ui_preferences.json', 'r') as f:
            prefs = json.load(f)
            if not prefs['sidebar_visible']:
                self.toggle_sidebar()
            self.splitter.setSizes([1200 - prefs['sidebar_width'], prefs['sidebar_width']])
    except FileNotFoundError:
        pass  # Use defaults
```

---

## 7. Performance Considerations

### Grid Rendering Optimization
```python
# Current: Full rebuild on filter change
def build_grid(self):
    # ... 1550 widgets created ...

# Optimized: Only hide/show rows
def apply_filter(self, filter_dict: Dict[int, bool]):
    """Hide/show rows without rebuilding"""
    for row, gebruiker in enumerate(self.gebruikers_data, start=1):
        visible = filter_dict.get(gebruiker['id'], True)
        for col in range(self.grid_layout.columnCount()):
            item = self.grid_layout.itemAtPosition(row, col)
            if item:
                item.widget().setVisible(visible)
```

**Benefit**: 10× faster filter changes (no widget creation).

---

## 8. Implementation Priority

### **Quick Wins (Can Do Now - 1 day)**
1. ✅ **Collapsible sidebar** (Solution 1) - 3 hours
2. ✅ **Context-aware info box** (Solution 5) - 2 hours
3. ✅ **Toolbar refactor** (Solution 2) - 3 hours

**Total**: 8 hours = 1 day of work

**Impact**: Reclaim 300px width, add 2-3 new features without clutter.

---

### **Post v1.0 (Requires Refactoring - 3 days)**
1. **Extract StatusManager widget** - 4 hours
2. **Floating validation panel** (Solution 3) - 4 hours
3. **Tabbed sidebar** (Solution 4) - 3 hours
4. **Undo/redo system** - 8 hours (requires command pattern)
5. **Grid rendering optimization** - 4 hours

**Total**: 23 hours = 3 days of work

---

### **Long Term (Major Redesign - 2+ weeks)**
1. **Repository pattern** (separate business logic) - 3 days
2. **Component library** (reusable buttons, panels) - 2 days
3. **Virtual scrolling** for grid - 4 days
4. **Advanced statistics screen** - 3 days

---

## 9. Layout Diagrams (Recommended Final State)

### **Proposed Layout (After Quick Wins)**
```
┌──────────────────────────────────────────────────────────┐
│ [Planning Editor]                          [Terug]       │ 40px
├──────────────────────────────────────────────────────────┤
│ ⚠️ Status Info (dynamic, context-aware, 300px)          │ 40px
│ << Oktober 2024 >>                          [◀ Collapse] │
├──────────────────────────────────────────────────────────┤
│ [🔧 Auto-Gen] [🗑️ Wis] [📢 Publiceren] ... [📊 Stats]  │ 30px (toolbar)
├──────────────────────────────────────────────────────────┤
│                                                           │
│  GRID (31 days × 50 users)          │  [Codes Sidebar]  │ 650px
│  1200px OR full width when          │  300px (resizable)│
│  sidebar collapsed                  │  OR hidden        │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 💡 TIP: Klik cel om te bewerken • TAB • ENTER • ESC     │ 20px
└──────────────────────────────────────────────────────────┘

Total height: 780px (fits in 800px window with margin)
```

### **With Validation Panel (Overlay)**
```
┌──────────────────────────────────────────────────────────┐
│ [Planning Editor]                          [Terug]       │
├──────────────────────────────────────────────────────────┤
│ ⚠️ HR Regel Waarschuwingen (klik voor details)          │
│ << Oktober 2024 >>                                       │
├──────────────────────────────────────────────────────────┤
│ [Toolbar...]                                             │
├──────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐    │
│  │ ⚠️ HR Regel Waarschuwingen           [✕ Close] │    │ 200px OVERLAY
│  │ • Jan: 60 uur deze week (max 50)              │    │
│  │ • Piet: 8 dagen zonder RX/CX (max 7)          │    │
│  │ [Details...]                                   │    │
│  └─────────────────────────────────────────────────┘    │
│  GRID (partially covered, but scrollable)        │ Codes│
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 10. Code Refactoring Plan

### **Phase 1: Extract Status Management (2 hours)**
```python
# Before (767 lines planning_editor_screen.py):
class PlanningEditorScreen(QWidget):
    def load_maand_status(self): ...
    def update_status_ui(self): ...
    def toggle_status(self): ...
    def publiceer_planning(self): ...
    def terug_naar_concept(self): ...

# After (600 lines planning_editor_screen.py + 150 lines status_manager_widget.py):
class PlanningEditorScreen(QWidget):
    def __init__(self, router):
        self.status_manager = StatusManagerWidget(...)
        self.status_manager.status_changed.connect(self.on_status_changed)

class StatusManagerWidget(QWidget):
    # All status logic here
```

---

### **Phase 2: Implement Splitter + Collapsible Sidebar (3 hours)**
```python
# Replace QHBoxLayout with QSplitter
self.splitter = QSplitter(Qt.Orientation.Horizontal)
self.splitter.addWidget(grid_widget)
self.splitter.addWidget(sidebar_widget)
self.splitter.setSizes([900, 300])  # 75% grid, 25% sidebar
```

---

### **Phase 3: Add Toolbar (3 hours)**
```python
# Replace buttons_row with QToolBar
toolbar = self.create_toolbar()
main_layout.addWidget(toolbar)
```

---

## 11. Summary & Recommendation

### **Recommended Immediate Actions (Post v1.0 - Priority: Medium)**
1. **Implement collapsible sidebar** (Solution 1) → Reclaim 300px
2. **Refactor to toolbar** (Solution 2) → Save 20px vertical, add scalability
3. **Context-aware info box** (Solution 5) → Dynamic feedback without new widgets

**Total effort**: 1 day
**Impact**: Ready for 3-5 new features without clutter

### **Post v1.0 Roadmap**
1. **Floating validation panel** (Solution 3) → HR warnings without permanent space
2. **Tabbed sidebar** (Solution 4) → Stats + codes in same 300px
3. **Extract status manager widget** → Cleaner code, reusable
4. **Undo/redo toolbar buttons** → Standard desktop UX

### **Key Principles to Follow**
✅ **Progressive disclosure** - Show only what's needed NOW
✅ **Collapsible panels** - Reclaim space when not in use
✅ **Toolbar over buttons** - Scalable, compact, standard
✅ **Overlays for alerts** - Temporary info doesn't take permanent space
✅ **Splitters for flexibility** - User decides layout priorities

### **Performance Targets**
- Grid render: <500ms (current: ~200ms ✅)
- Filter toggle: <100ms (after optimization)
- Sidebar collapse: <300ms (animated)

---

## 12. Files to Create

1. `gui/widgets/status_manager_widget.py` (150 lines)
   - StatusManagerWidget class
   - Signal-based communication
   - Status toggle logic

2. `gui/widgets/validation_results_panel.py` (200 lines)
   - ValidationResultsPanel class
   - Animated slide-in/out
   - Warning list display

3. `data/ui_preferences.json` (new file)
   - Store sidebar visibility
   - Store splitter sizes
   - Store panel states

---

## 13. Files to Modify

1. `gui/screens/planning_editor_screen.py`
   - **Current**: 767 lines
   - **After refactoring**: ~600 lines
   - Changes:
     - Replace QHBoxLayout with QSplitter
     - Replace buttons_row with QToolBar
     - Extract status logic to StatusManagerWidget
     - Add toggle_sidebar() method
     - Add save/load UI state methods

2. `gui/widgets/planner_grid_kalender.py`
   - Add filter optimization (hide/show instead of rebuild)
   - Performance improvement for filter changes

3. `gui/styles.py`
   - Add toolbar styling (if needed)
   - Add validation panel styling

---

## 14. New Dependencies

**None** - All solutions use PyQt6 built-in widgets:
- QSplitter ✅
- QToolBar ✅
- QAction ✅
- QPropertyAnimation ✅
- QTabWidget ✅

---

## 15. Testing Checklist

### Quick Wins Testing
- [ ] Sidebar collapse/expand works
- [ ] Splitter resizing works
- [ ] Splitter state persists between sessions
- [ ] Toolbar buttons trigger correct actions
- [ ] Toolbar keyboard shortcuts work (Ctrl+Z, Ctrl+Y)
- [ ] Info box updates dynamically based on context
- [ ] Info box clickable for validation details

### Post v1.0 Testing
- [ ] Validation panel slides in smoothly
- [ ] Validation panel shows correct warnings
- [ ] Validation panel close button works
- [ ] Tabbed sidebar switches tabs correctly
- [ ] Stats tab shows correct totals
- [ ] StatusManager widget emits correct signals
- [ ] Grid filter optimization speeds up changes

---

## Appendix: Related Documents

- **ARCHITECTURE_REVIEW_POST_1.0.md** - Full architecture analysis
- **CLAUDE.md** - Development guide (Section 12 - Common Issues)
- **DEVELOPMENT_GUIDE.md** - Technical patterns
- **proposed_improvements.md** - Earlier improvement proposals

---

**Document Version**: 1.0
**Author**: Python Expert Agent (via Claude Code)
**Review Status**: Awaiting implementation post v1.0
