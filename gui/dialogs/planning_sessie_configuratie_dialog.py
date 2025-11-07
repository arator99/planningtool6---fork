# gui/dialogs/planning_sessie_configuratie_dialog.py
"""
Planning Sessie Configuratie Dialog
v0.6.25 - PERFORMANCE OPTIMALISATIE

Laat gebruiker kiezen welke data te laden voor planning editor.
Voorkomt laden van 30 users × 31 dagen als je maar 5 users wil bewerken.

PERFORMANCE VOORDEEL:
- Load alleen wat nodig is
- Geschatte laadtijd preview
- Session persistence (onthoud laatste keuze)
- 100-300x sneller voor gefilterde sessies

Zie: refactor performance/PLANNING_SESSIE_CONFIGURATIE-1.md
"""
from typing import Dict, List
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QComboBox, QRadioButton, QCheckBox,
                             QPushButton, QDialogButtonBox, QWidget)
from PyQt6.QtCore import Qt
from datetime import date
from calendar import monthrange
from database.connection import get_connection
from gui.styles import Styles, Colors, Dimensions
import json


class PlanningSessieConfiguratieDialog(QDialog):
    """
    Configuratie dialog voor planning sessie

    Laat gebruiker kiezen:
    - Welke maand
    - Welke gebruikers (filter opties)
    - Preview van performance impact
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Planning Sessie Configureren")
        self.setModal(True)
        self.resize(600, 750)

        # Default waarden
        vandaag = date.today()
        self.huidige_jaar: int = vandaag.year
        self.huidige_maand: int = vandaag.month
        self.gebruiker_ids: List[int] = []

        # UI components (voor type hints)
        self.jaar_combo: QComboBox
        self.maand_combo: QComboBox
        self.radio_actief: QRadioButton
        self.radio_alle: QRadioButton
        self.check_verberg_reserves: QCheckBox
        self.check_verberg_inactief: QCheckBox
        self.label_selected_count: QLabel
        self.label_cellen: QLabel
        self.label_laadtijd: QLabel
        self.label_tip: QLabel
        self.check_onthoud: QCheckBox

        self._setup_ui()
        self._load_defaults()
        self._update_gebruikers_filter()

    def _setup_ui(self) -> None:
        """Build dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Periode sectie
        periode_group = self._create_periode_section()
        layout.addWidget(periode_group)

        # Gebruikers sectie
        gebruikers_group = self._create_gebruikers_section()
        layout.addWidget(gebruikers_group)

        # Performance preview
        perf_group = self._create_performance_section()
        layout.addWidget(perf_group)

        # Sessie opties
        opties_group = self._create_opties_section()
        layout.addWidget(opties_group)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Ok
        )
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Open Planning")
        ok_button.setStyleSheet(Styles.button_success())

        button_box.accepted.connect(self.accept)  # type: ignore
        button_box.rejected.connect(self.reject)  # type: ignore
        layout.addWidget(button_box)

    def _create_periode_section(self) -> QGroupBox:
        """Periode selectie sectie"""
        group = QGroupBox("📅 PLANNING PERIODE")
        layout = QVBoxLayout()

        # Jaar combo
        jaar_row = QHBoxLayout()
        jaar_row.addWidget(QLabel("Jaar:"))
        self.jaar_combo = QComboBox()
        # Vorig jaar, dit jaar, volgend jaar
        huidige_jaar = date.today().year
        for jaar in range(huidige_jaar - 1, huidige_jaar + 2):
            self.jaar_combo.addItem(str(jaar))
        self.jaar_combo.setCurrentText(str(self.huidige_jaar))
        self.jaar_combo.currentTextChanged.connect(self._on_periode_changed)  # type: ignore
        jaar_row.addWidget(self.jaar_combo)
        jaar_row.addStretch()
        layout.addLayout(jaar_row)

        # Maand combo
        maand_row = QHBoxLayout()
        maand_row.addWidget(QLabel("Maand:"))
        self.maand_combo = QComboBox()
        maanden = ['Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni',
                   'Juli', 'Augustus', 'September', 'Oktober', 'November', 'December']
        for maand_naam in maanden:
            self.maand_combo.addItem(maand_naam)
        self.maand_combo.setCurrentIndex(self.huidige_maand - 1)
        self.maand_combo.currentIndexChanged.connect(self._on_periode_changed)  # type: ignore
        maand_row.addWidget(self.maand_combo)
        maand_row.addStretch()
        layout.addLayout(maand_row)

        # Dagen preview
        _, dagen = monthrange(self.huidige_jaar, self.huidige_maand)
        dagen_label = QLabel(f"📊 {dagen} dagen")
        dagen_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")
        layout.addWidget(dagen_label)

        group.setLayout(layout)
        return group

    def _create_gebruikers_section(self) -> QGroupBox:
        """Gebruikers filtering sectie"""
        group = QGroupBox("👥 GEBRUIKERS SELECTIE")
        layout = QVBoxLayout()

        # Radio buttons voor snelle filters
        self.radio_actief = QRadioButton("Alleen Actieve Gebruikers")
        self.radio_alle = QRadioButton("Alle Gebruikers")

        self.radio_actief.setChecked(True)  # Default
        self.radio_actief.toggled.connect(self._update_gebruikers_filter)  # type: ignore
        self.radio_alle.toggled.connect(self._update_gebruikers_filter)  # type: ignore

        layout.addWidget(self.radio_actief)
        layout.addWidget(self.radio_alle)

        # Filter opties (checkboxes)
        filter_container = QWidget()
        filter_layout = QVBoxLayout(filter_container)
        filter_layout.setContentsMargins(20, 10, 10, 10)

        self.check_verberg_reserves = QCheckBox("Verberg reserves")
        self.check_verberg_inactief = QCheckBox("Verberg inactieve gebruikers")

        self.check_verberg_reserves.setChecked(True)  # Default ON
        self.check_verberg_inactief.setChecked(True)  # Default ON

        self.check_verberg_reserves.toggled.connect(self._update_gebruikers_filter)  # type: ignore
        self.check_verberg_inactief.toggled.connect(self._update_gebruikers_filter)  # type: ignore

        filter_layout.addWidget(self.check_verberg_reserves)
        filter_layout.addWidget(self.check_verberg_inactief)

        layout.addWidget(filter_container)

        # Selected count label
        self.label_selected_count = QLabel("✓ 0 gebruikers geselecteerd")
        self.label_selected_count.setStyleSheet(f"color: {Colors.SUCCESS}; font-weight: bold;")
        layout.addWidget(self.label_selected_count)

        group.setLayout(layout)
        return group

    def _create_performance_section(self) -> QGroupBox:
        """Performance preview sectie"""
        group = QGroupBox("⚡ PERFORMANCE PREVIEW")
        layout = QVBoxLayout()

        self.label_cellen = QLabel("Te laden cellen: ...")
        self.label_laadtijd = QLabel("Geschatte laadtijd: ...")
        self.label_tip = QLabel()
        self.label_tip.setWordWrap(True)

        layout.addWidget(self.label_cellen)
        layout.addWidget(self.label_laadtijd)
        layout.addWidget(self.label_tip)

        group.setLayout(layout)
        return group

    def _create_opties_section(self) -> QGroupBox:
        """Sessie opties sectie"""
        group = QGroupBox("💾 SESSIE OPTIES")
        layout = QVBoxLayout()

        self.check_onthoud = QCheckBox("Onthoud deze configuratie voor volgende keer")
        self.check_onthoud.setChecked(True)  # Default ON

        layout.addWidget(self.check_onthoud)

        group.setLayout(layout)
        return group

    def _on_periode_changed(self) -> None:
        """Handle periode wijziging"""
        self.huidige_jaar = int(self.jaar_combo.currentText())
        self.huidige_maand = self.maand_combo.currentIndex() + 1
        self._update_statistics()

    def _update_gebruikers_filter(self) -> None:
        """
        Update gebruiker lijst op basis van filters

        Dit bepaalt hoeveel data we laden!
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Base query
        query = "SELECT id FROM gebruikers WHERE gebruikersnaam != 'admin'"
        conditions = []

        # Filter op actief/inactief
        if self.check_verberg_inactief.isChecked():
            conditions.append("is_actief = 1")

        # Filter op reserves
        if self.check_verberg_reserves.isChecked():
            conditions.append("is_reserve = 0")

        # Radio button filter
        if self.radio_actief.isChecked():
            conditions.append("is_actief = 1")

        # Add WHERE conditions
        if conditions:
            query += " AND " + " AND ".join(conditions)

        # Execute
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        # Update state
        self.gebruiker_ids = [row['id'] for row in results]

        # Update UI
        self.label_selected_count.setText(
            f"✓ {len(self.gebruiker_ids)} gebruikers geselecteerd"
        )

        # Update performance preview
        self._update_statistics()

    def _update_statistics(self) -> None:
        """
        Update performance statistics real-time

        Geeft gebruiker feedback over impact van filters
        """
        # Bereken aantal dagen
        _, dagen = monthrange(self.huidige_jaar, self.huidige_maand)

        # Bereken cellen
        gebruikers_count = len(self.gebruiker_ids)
        cellen = gebruikers_count * dagen

        # Schat laadtijd (gebaseerd op ValidationCache benchmark)
        # Met cache: ~1ms per 31 cellen = ~0.03s per gebruiker per maand
        laadtijd_sec = (gebruikers_count * 0.03) if gebruikers_count > 0 else 0

        # Update labels
        self.label_cellen.setText(
            f"Te laden cellen: {cellen} ({gebruikers_count} × {dagen})"
        )

        # Kleurcodering op basis van laadtijd
        if laadtijd_sec < 0.5:
            tijd_str = f"~{int(laadtijd_sec * 1000)}ms"
            kleur = Colors.SUCCESS
            tip = "✓ Snelle loading - optimale configuratie!"
        elif laadtijd_sec < 2:
            tijd_str = f"~{laadtijd_sec:.1f} seconden"
            kleur = Colors.WARNING
            tip = "⚠ Acceptabele snelheid - overweeg meer filtering"
        else:
            tijd_str = f"~{laadtijd_sec:.1f} seconden"
            kleur = Colors.ERROR
            tip = "⚠ Trage loading - verhoog filtering voor betere performance"

        self.label_laadtijd.setText(f"Geschatte laadtijd: {tijd_str}")
        self.label_laadtijd.setStyleSheet(f"color: {kleur}; font-weight: bold;")

        self.label_tip.setText(f"ℹ️  {tip}")
        self.label_tip.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")

    def _load_defaults(self) -> None:
        """
        Load saved defaults uit settings

        Onthoud laatste configuratie gebruiker
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Check if settings table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='settings'
            """)
            if not cursor.fetchone():
                # Geen settings tabel - gebruik defaults
                conn.close()
                return

            # Load uit settings tabel
            cursor.execute("""
                SELECT waarde FROM settings
                WHERE sleutel = 'planning_sessie_config'
            """)

            row = cursor.fetchone()
            if row:
                config = json.loads(row['waarde'])

                # Restore filters
                self.check_verberg_reserves.setChecked(
                    config.get('verberg_reserves', True)
                )
                self.check_verberg_inactief.setChecked(
                    config.get('verberg_inactief', True)
                )

                # Restore radio
                if config.get('filter_mode') == 'actief':
                    self.radio_actief.setChecked(True)
                elif config.get('filter_mode') == 'alle':
                    self.radio_alle.setChecked(True)

        except Exception as e:
            print(f"[PlanningSessieConfig] Fout bij laden defaults: {e}")
        finally:
            conn.close()

    def save_config(self) -> None:
        """
        Sla configuratie op voor volgende keer

        Alleen als "Onthoud deze configuratie" aangevinkt is
        """
        if not self.check_onthoud.isChecked():
            return

        config = {
            'verberg_reserves': self.check_verberg_reserves.isChecked(),
            'verberg_inactief': self.check_verberg_inactief.isChecked(),
            'filter_mode': 'actief' if self.radio_actief.isChecked() else 'alle'
        }

        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Create settings table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    sleutel TEXT PRIMARY KEY,
                    waarde TEXT
                )
            """)

            # Insert or replace
            cursor.execute("""
                INSERT OR REPLACE INTO settings (sleutel, waarde)
                VALUES ('planning_sessie_config', ?)
            """, (json.dumps(config),))

            conn.commit()
        except Exception as e:
            print(f"[PlanningSessieConfig] Fout bij opslaan config: {e}")
        finally:
            conn.close()

    def get_configuratie(self) -> Dict:
        """
        Get finale configuratie voor planning editor

        Returns:
            {
                'jaar': 2025,
                'maand': 11,
                'gebruiker_ids': [1, 2, 3, ...],
                'filters': {...}
            }
        """
        return {
            'jaar': self.huidige_jaar,
            'maand': self.huidige_maand,
            'gebruiker_ids': self.gebruiker_ids,
            'filters': {
                'verberg_reserves': self.check_verberg_reserves.isChecked(),
                'verberg_inactief': self.check_verberg_inactief.isChecked(),
            }
        }

    def accept(self) -> None:
        """Override accept to save config"""
        self.save_config()
        super().accept()
