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

v0.6.28+ - WERKPOST FILTERING (ISSUE-011)
- Selecteer werkposten om mee te plannen (checkboxes)
- Filter gebruikers op werkpost kennis (via gebruiker_werkposten)
- Meerdere werkposten tegelijk mogelijk

Zie: refactor performance/PLANNING_SESSIE_CONFIGURATIE-1.md
     bugs.md ISSUE-011
"""
from typing import Dict, List
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QComboBox, QRadioButton, QCheckBox,
                             QPushButton, QDialogButtonBox, QWidget, QScrollArea)
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
        self.werkpost_ids: List[int] = []  # NIEUW: geselecteerde werkposten

        # UI components (voor type hints)
        self.jaar_combo: QComboBox
        self.maand_combo: QComboBox
        self.radio_actief: QRadioButton
        self.radio_alle: QRadioButton
        self.check_verberg_reserves: QCheckBox
        self.check_verberg_inactief: QCheckBox
        self.check_filter_op_werkpost: QCheckBox  # NIEUW: filter op werkpost kennis
        self.werkpost_checkboxes: Dict[int, QCheckBox] = {}  # NIEUW: werkpost checkboxes {werkpost_id: checkbox}
        self.label_selected_count: QLabel
        self.label_selected_werkposten: QLabel  # NIEUW: werkpost count
        self.label_cellen: QLabel
        self.label_laadtijd: QLabel
        self.label_tip: QLabel
        self.check_onthoud: QCheckBox

        self._setup_ui()
        self._load_defaults()
        self._update_werkpost_selectie()  # NIEUW: update werkpost IDs
        self._update_gebruikers_filter()

    def _setup_ui(self) -> None:
        """Build dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Periode sectie
        periode_group = self._create_periode_section()
        layout.addWidget(periode_group)

        # NIEUW: Werkposten sectie (ISSUE-011)
        werkpost_group = self._create_werkpost_section()
        layout.addWidget(werkpost_group)

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

    def _create_werkpost_section(self) -> QGroupBox:
        """
        Werkpost selectie sectie (ISSUE-011)

        Laat gebruiker kiezen voor welke werkposten te plannen.
        """
        group = QGroupBox("🏢 WERKPOST SELECTIE (Team Filter)")
        layout = QVBoxLayout()

        # Info label
        info = QLabel(
            "Selecteer werkposten om mee te plannen. "
            "Meerdere selecties mogelijk."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic;")
        layout.addWidget(info)

        # Scroll area voor werkpost checkboxes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(150)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        # Container voor checkboxes
        checkbox_container = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(10, 5, 10, 5)
        checkbox_layout.setSpacing(5)

        # Laad werkposten uit database
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, naam, beschrijving
            FROM werkposten
            WHERE is_actief = 1
            ORDER BY naam
        """)
        werkposten = cursor.fetchall()
        conn.close()

        # Maak checkbox per werkpost
        for werkpost in werkposten:
            werkpost_id = werkpost['id']
            werkpost_naam = werkpost['naam']
            werkpost_beschrijving = werkpost['beschrijving'] or ""

            checkbox = QCheckBox(werkpost_naam)
            checkbox.setChecked(True)  # Default: alle werkposten geselecteerd

            # Tooltip met beschrijving
            if werkpost_beschrijving:
                checkbox.setToolTip(werkpost_beschrijving)

            # Connect signal
            checkbox.toggled.connect(self._on_werkpost_changed)  # type: ignore

            # Opslaan in dictionary
            self.werkpost_checkboxes[werkpost_id] = checkbox

            checkbox_layout.addWidget(checkbox)

        checkbox_layout.addStretch()
        scroll_area.setWidget(checkbox_container)
        layout.addWidget(scroll_area)

        # Selected count label
        self.label_selected_werkposten = QLabel("✓ 0 werkposten geselecteerd")
        self.label_selected_werkposten.setStyleSheet(f"color: {Colors.SUCCESS}; font-weight: bold;")
        layout.addWidget(self.label_selected_werkposten)

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
        # NIEUW (ISSUE-011): Filter op werkpost kennis
        self.check_filter_op_werkpost = QCheckBox("Alleen gebruikers die geselecteerde werkposten kennen")

        self.check_verberg_reserves.setChecked(True)  # Default ON
        self.check_verberg_inactief.setChecked(True)  # Default ON
        self.check_filter_op_werkpost.setChecked(False)  # Default OFF (optioneel)

        self.check_verberg_reserves.toggled.connect(self._update_gebruikers_filter)  # type: ignore
        self.check_verberg_inactief.toggled.connect(self._update_gebruikers_filter)  # type: ignore
        self.check_filter_op_werkpost.toggled.connect(self._update_gebruikers_filter)  # type: ignore

        filter_layout.addWidget(self.check_verberg_reserves)
        filter_layout.addWidget(self.check_verberg_inactief)
        filter_layout.addWidget(self.check_filter_op_werkpost)

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

    def _on_werkpost_changed(self) -> None:
        """
        Handle werkpost checkbox wijziging (ISSUE-011)

        Update lijst van geselecteerde werkposten en gebruikers filter
        """
        self._update_werkpost_selectie()
        self._update_gebruikers_filter()

    def _update_werkpost_selectie(self) -> None:
        """
        Update lijst van geselecteerde werkpost IDs (ISSUE-011)

        Leest alle checkboxes en update self.werkpost_ids
        """
        self.werkpost_ids = [
            werkpost_id
            for werkpost_id, checkbox in self.werkpost_checkboxes.items()
            if checkbox.isChecked()
        ]

        # Update UI label
        count = len(self.werkpost_ids)
        self.label_selected_werkposten.setText(
            f"✓ {count} werkpost{'en' if count != 1 else ''} geselecteerd"
        )

        # Update kleur op basis van selectie
        if count == 0:
            self.label_selected_werkposten.setStyleSheet(
                f"color: {Colors.WARNING}; font-weight: bold;"
            )
        else:
            self.label_selected_werkposten.setStyleSheet(
                f"color: {Colors.SUCCESS}; font-weight: bold;"
            )

    def _update_gebruikers_filter(self) -> None:
        """
        Update gebruiker lijst op basis van filters

        Dit bepaalt hoeveel data we laden!

        ISSUE-011: Filtert ook op werkpost kennis via gebruiker_werkposten
        """
        conn = get_connection()
        cursor = conn.cursor()

        # NIEUW (ISSUE-011): Check of werkpost filtering actief is
        filter_op_werkpost = (
            self.check_filter_op_werkpost.isChecked() and
            len(self.werkpost_ids) > 0
        )

        if filter_op_werkpost:
            # Query met JOIN op gebruiker_werkposten (alleen gebruikers die geselecteerde werkposten kennen)
            placeholders = ','.join(['?'] * len(self.werkpost_ids))
            query = f"""
                SELECT DISTINCT g.id
                FROM gebruikers g
                INNER JOIN gebruiker_werkposten gw ON g.id = gw.gebruiker_id
                WHERE g.gebruikersnaam != 'admin'
                AND gw.werkpost_id IN ({placeholders})
            """
            params = list(self.werkpost_ids)
            conditions = []

            # Filter op actief/inactief
            if self.check_verberg_inactief.isChecked():
                conditions.append("g.is_actief = 1")

            # Filter op reserves
            if self.check_verberg_reserves.isChecked():
                conditions.append("g.is_reserve = 0")

            # Radio button filter
            if self.radio_actief.isChecked():
                conditions.append("g.is_actief = 1")

            # Add WHERE conditions
            if conditions:
                query += " AND " + " AND ".join(conditions)

            # Execute met params
            cursor.execute(query, params)

        else:
            # Oude query zonder werkpost filtering
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

            # Execute zonder params
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
                # NIEUW (ISSUE-011): Restore werkpost filter checkbox
                self.check_filter_op_werkpost.setChecked(
                    config.get('filter_op_werkpost', False)
                )

                # Restore radio
                if config.get('filter_mode') == 'actief':
                    self.radio_actief.setChecked(True)
                elif config.get('filter_mode') == 'alle':
                    self.radio_alle.setChecked(True)

                # NIEUW (ISSUE-011): Restore werkpost selecties
                saved_werkpost_ids = config.get('werkpost_ids', [])
                for werkpost_id, checkbox in self.werkpost_checkboxes.items():
                    # Zet checked state op basis van saved config
                    # Default = alle aan als geen config, of check of in saved list
                    if saved_werkpost_ids:
                        checkbox.setChecked(werkpost_id in saved_werkpost_ids)
                    # else: blijft default (alle aan)

        except Exception:
            pass
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
            'filter_op_werkpost': self.check_filter_op_werkpost.isChecked(),  # NIEUW (ISSUE-011)
            'filter_mode': 'actief' if self.radio_actief.isChecked() else 'alle',
            'werkpost_ids': self.werkpost_ids  # NIEUW (ISSUE-011): save geselecteerde werkposten
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
        except Exception:
            pass
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
                'werkpost_ids': [1, 2, ...],  # NIEUW (ISSUE-011)
                'filters': {...}
            }
        """
        return {
            'jaar': self.huidige_jaar,
            'maand': self.huidige_maand,
            'gebruiker_ids': self.gebruiker_ids,
            'werkpost_ids': self.werkpost_ids,  # NIEUW (ISSUE-011)
            'filters': {
                'verberg_reserves': self.check_verberg_reserves.isChecked(),
                'verberg_inactief': self.check_verberg_inactief.isChecked(),
                'filter_op_werkpost': self.check_filter_op_werkpost.isChecked(),  # NIEUW (ISSUE-011)
            }
        }

    def accept(self) -> None:
        """Override accept to save config"""
        self.save_config()
        super().accept()
