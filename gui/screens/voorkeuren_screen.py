"""
Voorkeuren Screen - Shift voorkeuren instellen voor gebruikers
v0.6.11

Gebruikers kunnen hun shift voorkeuren instellen in volgorde van prioriteit.
Dit wordt gebruikt bij automatische planning generatie.
"""

from typing import Callable, Dict, Any, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from gui.styles import Styles, Colors, Fonts, Dimensions
from database.connection import get_connection
import sqlite3
import json


class VoorkeurenScreen(QWidget):
    """Scherm voor het instellen van shift voorkeuren"""

    def __init__(self, router: Callable, user_data: Dict[str, Any]):
        super().__init__()
        self.router = router
        self.user_data = user_data

        # Instance attributes
        self.vroeg_combo: QComboBox = QComboBox()
        self.laat_combo: QComboBox = QComboBox()
        self.nacht_combo: QComboBox = QComboBox()
        self.typetabel_combo: QComboBox = QComboBox()
        self.huidige_voorkeuren: Dict[str, str] = {}
        self.loading: bool = False  # Flag om auto-save te blokkeren tijdens laden

        self.init_ui()
        self.load_voorkeuren()

    def init_ui(self) -> None:
        """Initialiseer de user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE,
            Dimensions.SPACING_LARGE
        )
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Mijn Shift Voorkeuren")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_TITLE, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Terug knop
        terug_btn = QPushButton("Terug")
        terug_btn.setStyleSheet(Styles.button_secondary())
        terug_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        terug_btn.clicked.connect(self.router)  # type: ignore
        header_layout.addWidget(terug_btn)

        layout.addLayout(header_layout)

        # Uitleg
        uitleg = QLabel(
            "Stel je shift voorkeuren in voor automatische planning generatie.\n"
            "Kies een prioriteit (1 = hoogste voorkeur) voor elk shift type.\n"
            "Elke prioriteit mag maar 1 keer gebruikt worden. Je kunt opties ook leeg laten."
        )
        uitleg.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        uitleg.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: {Dimensions.SPACING_MEDIUM}px;")
        uitleg.setWordWrap(True)
        layout.addWidget(uitleg)

        # Info box
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_LIGHT};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Dimensions.RADIUS_MEDIUM}px;
                padding: {Dimensions.SPACING_MEDIUM}px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)

        info_title = QLabel("Hoe werkt het?")
        info_title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        info_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        info_layout.addWidget(info_title)

        info_text = QLabel(
            "• Prioriteit 1 = hoogste voorkeur, 4 = laagste voorkeur\n"
            "• Je kunt ook opties leeg laten (geen voorkeur)\n"
            "• 'Typetabel' = volg het standaard rooster patroon\n"
            "• Bij automatische planning krijgen je voorkeuren voorrang\n"
            "• Als geen voorkeuren zijn ingesteld, wordt de typetabel gebruikt"
        )
        info_text.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        info_text.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        layout.addWidget(info_frame)

        # Voorkeuren formulier
        form_frame = QFrame()
        form_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Dimensions.RADIUS_LARGE}px;
                padding: {Dimensions.SPACING_LARGE}px;
            }}
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Prioriteit opties
        prioriteit_opties = ["(Geen voorkeur)", "1 (Hoogste)", "2", "3", "4 (Laagste)"]

        # Vroege shift
        vroeg_layout = QHBoxLayout()
        vroeg_label = QLabel("Vroege Dienst:")
        vroeg_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        vroeg_label.setMinimumWidth(200)
        vroeg_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        vroeg_layout.addWidget(vroeg_label)

        self.vroeg_combo.addItems(prioriteit_opties)
        self.vroeg_combo.setStyleSheet(Styles.input_field())
        self.vroeg_combo.setMinimumWidth(200)
        vroeg_layout.addWidget(self.vroeg_combo)

        vroeg_desc = QLabel("Shifts in de ochtend/voormiddag")
        vroeg_desc.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        vroeg_desc.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        vroeg_layout.addWidget(vroeg_desc)
        vroeg_layout.addStretch()

        form_layout.addLayout(vroeg_layout)

        # Late shift
        laat_layout = QHBoxLayout()
        laat_label = QLabel("Late Dienst:")
        laat_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        laat_label.setMinimumWidth(200)
        laat_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        laat_layout.addWidget(laat_label)

        self.laat_combo.addItems(prioriteit_opties)
        self.laat_combo.setStyleSheet(Styles.input_field())
        self.laat_combo.setMinimumWidth(200)
        laat_layout.addWidget(self.laat_combo)

        laat_desc = QLabel("Shifts in de middag/avond")
        laat_desc.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        laat_desc.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        laat_layout.addWidget(laat_desc)
        laat_layout.addStretch()

        form_layout.addLayout(laat_layout)

        # Nacht shift
        nacht_layout = QHBoxLayout()
        nacht_label = QLabel("Nachtdienst:")
        nacht_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        nacht_label.setMinimumWidth(200)
        nacht_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        nacht_layout.addWidget(nacht_label)

        self.nacht_combo.addItems(prioriteit_opties)
        self.nacht_combo.setStyleSheet(Styles.input_field())
        self.nacht_combo.setMinimumWidth(200)
        nacht_layout.addWidget(self.nacht_combo)

        nacht_desc = QLabel("Shifts in de nacht")
        nacht_desc.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        nacht_desc.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        nacht_layout.addWidget(nacht_desc)
        nacht_layout.addStretch()

        form_layout.addLayout(nacht_layout)

        # Typetabel
        typetabel_layout = QHBoxLayout()
        typetabel_label = QLabel("Typetabel:")
        typetabel_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL))
        typetabel_label.setMinimumWidth(200)
        typetabel_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        typetabel_layout.addWidget(typetabel_label)

        self.typetabel_combo.addItems(prioriteit_opties)
        self.typetabel_combo.setStyleSheet(Styles.input_field())
        self.typetabel_combo.setMinimumWidth(200)
        typetabel_layout.addWidget(self.typetabel_combo)

        typetabel_desc = QLabel("Volg het standaard rooster patroon")
        typetabel_desc.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        typetabel_desc.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        typetabel_layout.addWidget(typetabel_desc)
        typetabel_layout.addStretch()

        form_layout.addLayout(typetabel_layout)

        layout.addWidget(form_frame)

        # Huidige voorkeuren weergave
        self.preview_label = QLabel()
        self.preview_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_SMALL))
        self.preview_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: {Dimensions.SPACING_SMALL}px;")
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)

        # Connect change signals voor auto-save en live preview
        self.vroeg_combo.currentIndexChanged.connect(self.on_voorkeur_changed)  # type: ignore
        self.laat_combo.currentIndexChanged.connect(self.on_voorkeur_changed)  # type: ignore
        self.nacht_combo.currentIndexChanged.connect(self.on_voorkeur_changed)  # type: ignore
        self.typetabel_combo.currentIndexChanged.connect(self.on_voorkeur_changed)  # type: ignore

        layout.addStretch()

        # Acties
        acties_layout = QHBoxLayout()
        acties_layout.addStretch()

        # Reset knop
        reset_btn = QPushButton("Reset naar Standaard")
        reset_btn.setStyleSheet(Styles.button_secondary())
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self.reset_voorkeuren)  # type: ignore
        acties_layout.addWidget(reset_btn)

        layout.addLayout(acties_layout)

    def load_voorkeuren(self) -> None:
        """Laad huidige voorkeuren uit database"""
        self.loading = True  # Blokkeer auto-save tijdens laden

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT shift_voorkeuren
                FROM gebruikers
                WHERE id = ?
            """, (self.user_data['id'],))

            result = cursor.fetchone()
            conn.close()

            if result and result['shift_voorkeuren']:
                voorkeuren_json = result['shift_voorkeuren']
                self.huidige_voorkeuren = json.loads(voorkeuren_json)
                self.apply_voorkeuren_to_ui()
            else:
                self.huidige_voorkeuren = {}

            self.update_preview()

        except (sqlite3.Error, json.JSONDecodeError) as e:
            QMessageBox.critical(self, "Fout", f"Kan voorkeuren niet laden: {e}")

        finally:
            self.loading = False  # Heractiveer auto-save

    def apply_voorkeuren_to_ui(self) -> None:
        """Pas geladen voorkeuren toe op UI elementen"""
        # Reverse mapping: van {"1": "vroeg"} naar {"vroeg": "1"}
        reverse_map = {v: k for k, v in self.huidige_voorkeuren.items()}

        # Zet comboboxes
        self.set_combo_prioriteit(self.vroeg_combo, reverse_map.get("vroeg"))
        self.set_combo_prioriteit(self.laat_combo, reverse_map.get("laat"))
        self.set_combo_prioriteit(self.nacht_combo, reverse_map.get("nacht"))
        self.set_combo_prioriteit(self.typetabel_combo, reverse_map.get("typetabel"))

    def set_combo_prioriteit(self, combo: QComboBox, prioriteit: Optional[str]) -> None:
        """Zet combobox op juiste prioriteit"""
        if prioriteit is None:
            combo.setCurrentIndex(0)  # Geen voorkeur
        else:
            # Prioriteit 1-4 mapped naar index 1-4
            combo.setCurrentIndex(int(prioriteit))

    def get_combo_prioriteit(self, combo: QComboBox) -> Optional[str]:
        """Haal prioriteit op uit combobox"""
        index = combo.currentIndex()
        if index == 0:
            return None  # Geen voorkeur
        return str(index)

    def on_voorkeur_changed(self) -> None:
        """Handler voor wijziging in voorkeuren - auto-save + preview update"""
        # Skip tijdens laden
        if self.loading:
            return

        # Update preview
        self.update_preview()

        # Check voor duplicaten
        if self.has_duplicate_priorities():
            # Toon warning in preview label
            self.preview_label.setText("LET OP: Je hebt dezelfde prioriteit meerdere keren gebruikt!")
            self.preview_label.setStyleSheet(f"color: {Colors.DANGER}; padding: {Dimensions.SPACING_SMALL}px; font-weight: bold;")
            return

        # Auto-save naar database
        self.auto_save_voorkeuren()

    def has_duplicate_priorities(self) -> bool:
        """Check of er dubbele prioriteiten zijn zonder dialog te tonen"""
        prioriteiten = []

        vroeg_prio = self.get_combo_prioriteit(self.vroeg_combo)
        laat_prio = self.get_combo_prioriteit(self.laat_combo)
        nacht_prio = self.get_combo_prioriteit(self.nacht_combo)
        typetabel_prio = self.get_combo_prioriteit(self.typetabel_combo)

        for prio in [vroeg_prio, laat_prio, nacht_prio, typetabel_prio]:
            if prio is not None:
                if prio in prioriteiten:
                    return True
                prioriteiten.append(prio)

        return False

    def auto_save_voorkeuren(self) -> None:
        """Automatisch opslaan van voorkeuren naar database"""
        try:
            # Bouw voorkeuren dictionary
            voorkeuren_map = {}

            vroeg_prio = self.get_combo_prioriteit(self.vroeg_combo)
            laat_prio = self.get_combo_prioriteit(self.laat_combo)
            nacht_prio = self.get_combo_prioriteit(self.nacht_combo)
            typetabel_prio = self.get_combo_prioriteit(self.typetabel_combo)

            if vroeg_prio:
                voorkeuren_map[vroeg_prio] = "vroeg"
            if laat_prio:
                voorkeuren_map[laat_prio] = "laat"
            if nacht_prio:
                voorkeuren_map[nacht_prio] = "nacht"
            if typetabel_prio:
                voorkeuren_map[typetabel_prio] = "typetabel"

            # Converteer naar JSON
            voorkeuren_json = json.dumps(voorkeuren_map) if voorkeuren_map else None

            # Opslaan in database
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE gebruikers
                SET shift_voorkeuren = ?
                WHERE id = ?
            """, (voorkeuren_json, self.user_data['id']))

            conn.commit()
            conn.close()

            self.huidige_voorkeuren = voorkeuren_map

        except sqlite3.Error:
            # Stille fout - geen dialog tonen bij auto-save
            pass

    def update_preview(self) -> None:
        """Update live preview van voorkeuren"""
        voorkeuren_map = {}

        # Verzamel alle instellingen
        vroeg_prio = self.get_combo_prioriteit(self.vroeg_combo)
        laat_prio = self.get_combo_prioriteit(self.laat_combo)
        nacht_prio = self.get_combo_prioriteit(self.nacht_combo)
        typetabel_prio = self.get_combo_prioriteit(self.typetabel_combo)

        # Bouw voorkeuren map
        if vroeg_prio:
            voorkeuren_map[vroeg_prio] = "vroeg"
        if laat_prio:
            voorkeuren_map[laat_prio] = "laat"
        if nacht_prio:
            voorkeuren_map[nacht_prio] = "nacht"
        if typetabel_prio:
            voorkeuren_map[typetabel_prio] = "typetabel"

        # Toon preview
        if voorkeuren_map:
            preview_text = "Huidige volgorde: "
            sorted_items = sorted(voorkeuren_map.items(), key=lambda x: int(x[0]))
            preview_parts = [f"{prio}. {naam.capitalize()}" for prio, naam in sorted_items]
            preview_text += " > ".join(preview_parts)
            self.preview_label.setText(preview_text)
            self.preview_label.setStyleSheet(f"color: {Colors.SUCCESS}; padding: {Dimensions.SPACING_SMALL}px; font-weight: bold;")
        else:
            self.preview_label.setText("Geen voorkeuren ingesteld (standaard: typetabel of vrije invulling)")
            self.preview_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: {Dimensions.SPACING_SMALL}px;")


    def reset_voorkeuren(self) -> None:
        """Reset voorkeuren naar standaard (leeg)"""
        reply = QMessageBox.question(
            self,
            "Reset Voorkeuren",
            "Weet je zeker dat je alle voorkeuren wilt resetten?\n"
            "Dit zet alles terug naar standaard (geen voorkeuren).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.vroeg_combo.setCurrentIndex(0)
            self.laat_combo.setCurrentIndex(0)
            self.nacht_combo.setCurrentIndex(0)
            self.typetabel_combo.setCurrentIndex(0)

            self.huidige_voorkeuren = {}
            self.update_preview()
