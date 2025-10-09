#gui/screens/kalender_test_screen.py
"""
Kalender Test Scherm - DEBUG VERSION
Voor het testen van beide grid kalender widgets
"""
from typing import Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTabWidget, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime
from gui.styles import Styles, Colors, Fonts, Dimensions


class KalenderTestScreen(QWidget):
    """
    Test scherm voor kalender widgets - DEBUG
    """

    def __init__(self, router: Callable, gebruiker_id: int = 1):
        super().__init__()
        self.router = router
        self.gebruiker_id = gebruiker_id

        # Instance attributes
        self.tabs: QTabWidget = QTabWidget()

        print("KalenderTestScreen __init__ start")

        try:
            self.init_ui()
            print("KalenderTestScreen init_ui completed")
        except Exception as e:
            print(f"ERROR in init_ui: {e}")
            import traceback
            traceback.print_exc()

    def init_ui(self) -> None:
        """Bouw UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_LARGE)
        layout.setContentsMargins(
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE,
            Dimensions.MARGIN_LARGE
        )

        print("Creating header...")

        # Header
        header = QHBoxLayout()

        title = QLabel("Kalender Widget Test (DEBUG)")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE))
        header.addWidget(title)

        header.addStretch()

        # Terug knop
        terug_btn = QPushButton("Terug")
        terug_btn.setFixedSize(100, Dimensions.BUTTON_HEIGHT_NORMAL)
        terug_btn.clicked.connect(self.router.terug)  # type: ignore
        terug_btn.setStyleSheet(Styles.button_secondary())
        header.addWidget(terug_btn)

        layout.addLayout(header)

        print("Header created")

        # Info box
        info_box = QLabel(
            "DEBUG MODE:\n"
            "Dit scherm test stapsgewijs de kalender widgets.\n"
            "Klik op de knoppen hieronder om verschillende componenten te laden."
        )
        info_box.setStyleSheet(Styles.info_box())
        info_box.setWordWrap(True)
        layout.addWidget(info_box)

        print("Info box created")

        # Test buttons
        test_layout = QVBoxLayout()

        # Test 1: Laad alleen base data
        test1_btn = QPushButton("Test 1: Laad Basis Data")
        test1_btn.setFixedHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        test1_btn.clicked.connect(self.test_basis_data)  # type: ignore
        test1_btn.setStyleSheet(Styles.button_primary())
        test_layout.addWidget(test1_btn)

        # Test 2: Maak simpele grid
        test2_btn = QPushButton("Test 2: Maak Simpele Grid (5x5)")
        test2_btn.setFixedHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        test2_btn.clicked.connect(self.test_simpele_grid)  # type: ignore
        test2_btn.setStyleSheet(Styles.button_primary())
        test_layout.addWidget(test2_btn)

        # Test 3: Laad teamlid kalender
        test3_btn = QPushButton("Test 3: Laad Teamlid Kalender")
        test3_btn.setFixedHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        test3_btn.clicked.connect(self.test_teamlid_kalender)  # type: ignore
        test3_btn.setStyleSheet(Styles.button_warning())
        test_layout.addWidget(test3_btn)

        # Test 4: Laad planner kalender
        test4_btn = QPushButton("Test 4: Laad Planner Kalender")
        test4_btn.setFixedHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        test4_btn.clicked.connect(self.test_planner_kalender)  # type: ignore
        test4_btn.setStyleSheet(Styles.button_danger())
        test_layout.addWidget(test4_btn)

        layout.addLayout(test_layout)
        layout.addStretch()

        print("UI complete")

    def test_basis_data(self) -> None:
        """Test 1: Laad alleen data zonder UI"""
        try:
            print("\n=== TEST 1: BASIS DATA ===")
            from gui.widgets.grid_kalender_base import GridKalenderBase

            nu = datetime.now()
            base = GridKalenderBase(nu.year, nu.month)

            print("Loading gebruikers...")
            base.load_gebruikers(alleen_actief=True)
            print(f"✓ {len(base.gebruikers_data)} gebruikers geladen")

            print("Loading feestdagen...")
            base.load_feestdagen()
            print(f"✓ {len(base.feestdagen)} feestdagen geladen")

            datum_lijst = base.get_datum_lijst(start_offset=0, eind_offset=0)
            print(f"✓ {len(datum_lijst)} datums in lijst")

            if datum_lijst:
                start = datum_lijst[0][0]
                eind = datum_lijst[-1][0]
                print(f"Loading planning data: {start} - {eind}")
                base.load_planning_data(start, eind)
                print(f"✓ Planning data geladen voor {len(base.planning_data)} dagen")

            QMessageBox.information(
                self,
                "Test 1 Geslaagd",
                f"Basis data succesvol geladen:\n\n"
                f"• {len(base.gebruikers_data)} gebruikers\n"
                f"• {len(base.feestdagen)} feestdagen\n"
                f"• {len(datum_lijst)} datums\n"
                f"• {len(base.planning_data)} dagen planning"
            )

        except Exception as e:
            print(f"ERROR in test_basis_data: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Test 1 Gefaald", f"Fout:\n{str(e)}")

    def test_simpele_grid(self) -> None:
        """Test 2: Maak simpele grid zonder kalender widget"""
        try:
            print("\n=== TEST 2: SIMPELE GRID ===")
            from PyQt6.QtWidgets import QGridLayout, QDialog

            dialog = QDialog(self)
            dialog.setWindowTitle("Test: Simpele Grid")
            dialog.resize(600, 400)

            layout = QVBoxLayout(dialog)

            grid_widget = QWidget()
            grid_layout = QGridLayout(grid_widget)
            grid_layout.setSpacing(0)
            grid_layout.setContentsMargins(0, 0, 0, 0)

            print("Creating 5x5 grid...")

            # Maak 5x5 grid
            for row in range(5):
                for col in range(5):
                    label = QLabel(f"R{row}C{col}")
                    label.setStyleSheet("""
                        QLabel {
                            background-color: white;
                            border: 1px solid #ddd;
                            padding: 8px;
                            qproperty-alignment: AlignCenter;
                        }
                    """)
                    label.setFixedSize(80, 40)
                    grid_layout.addWidget(label, row, col)

            print("Grid created, showing dialog...")

            layout.addWidget(grid_widget)
            dialog.exec()

            print("✓ Simpele grid test geslaagd")

        except Exception as e:
            print(f"ERROR in test_simpele_grid: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Test 2 Gefaald", f"Fout:\n{str(e)}")

    def test_teamlid_kalender(self) -> None:
        """Test 3: Laad teamlid kalender"""
        try:
            print("\n=== TEST 3: TEAMLID KALENDER ===")
            from gui.widgets import TeamlidGridKalender

            nu = datetime.now()

            print("Creating TeamlidGridKalender...")
            kalender = TeamlidGridKalender(nu.year, nu.month, self.gebruiker_id)

            print("Showing kalender in dialog...")
            from PyQt6.QtWidgets import QDialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Test: Teamlid Kalender")
            dialog.resize(1200, 700)

            layout = QVBoxLayout(dialog)
            layout.addWidget(kalender)

            dialog.exec()

            print("✓ Teamlid kalender test geslaagd")

        except Exception as e:
            print(f"ERROR in test_teamlid_kalender: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Test 3 Gefaald", f"Fout:\n{str(e)}")

    def test_planner_kalender(self) -> None:
        """Test 4: Laad planner kalender"""
        try:
            print("\n=== TEST 4: PLANNER KALENDER ===")
            from gui.widgets import PlannerGridKalender

            nu = datetime.now()

            print("Creating PlannerGridKalender...")
            kalender = PlannerGridKalender(nu.year, nu.month)

            print("Connecting signal...")
            kalender.cel_clicked.connect(self.on_cel_clicked)  # type: ignore

            print("Showing kalender in dialog...")
            from PyQt6.QtWidgets import QDialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Test: Planner Kalender")
            dialog.resize(1400, 700)

            layout = QVBoxLayout(dialog)
            layout.addWidget(kalender)

            dialog.exec()

            print("✓ Planner kalender test geslaagd")

        except Exception as e:
            print(f"ERROR in test_planner_kalender: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Test 4 Gefaald", f"Fout:\n{str(e)}")

    def on_cel_clicked(self, datum_str: str, gebruiker_id: int) -> None:
        """Handle cel click"""
        print(f"Cel clicked: datum={datum_str}, gebruiker={gebruiker_id}")
        QMessageBox.information(
            self,
            "Cel Clicked",
            f"Datum: {datum_str}\nGebruiker ID: {gebruiker_id}"
        )