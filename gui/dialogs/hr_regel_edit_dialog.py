# gui/dialogs/hr_regel_edit_dialog.py
"""
HR Regel Edit Dialog
Voor het wijzigen van HR regels met nieuwe versie + datum
"""
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QDoubleSpinBox, QDateEdit, QComboBox,
                             QFormLayout, QMessageBox, QCheckBox, QGroupBox)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont
from datetime import datetime
from gui.styles import Styles, Colors, Fonts, Dimensions
from services.term_code_service import TermCodeService


class HRRegelEditDialog(QDialog):
    """Dialog voor het wijzigen van een HR regel"""

    def __init__(self, parent, regel: Dict[str, Any]):
        super().__init__(parent)
        self.regel = regel

        self.setWindowTitle(f"HR Regel Wijzigen: {regel['naam']}")
        self.setModal(True)
        self.setMinimumWidth(500)

        # Instance attributes
        self.waarde_input: Optional[QDoubleSpinBox] = None
        self.datum_dag_input: Optional[QComboBox] = None
        self.datum_maand_input: Optional[QComboBox] = None
        self.term_checkboxes: Dict[str, QCheckBox] = {}  # term -> checkbox mapping
        self.actief_vanaf_input: QDateEdit = QDateEdit()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Title
        naam_display = self.regel['naam'].replace('_', ' ').title()
        title = QLabel(f"Wijzig: {naam_display}")
        title.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_HEADING, QFont.Weight.Bold))
        layout.addWidget(title)

        # Info box
        info = QLabel(
            "Bij wijzigen wordt een nieuwe versie aangemaakt.\n"
            "De oude regel wordt gearchiveerd met einddatum = nieuwe startdatum."
        )
        info.setStyleSheet(Styles.info_box())
        info.setWordWrap(True)
        layout.addWidget(info)

        # Huidige waarde
        huidig_group = QVBoxLayout()
        huidig_label = QLabel("HUIDIGE WAARDE:")
        huidig_label.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_NORMAL, QFont.Weight.Bold))
        huidig_group.addWidget(huidig_label)

        # Format huidige waarde leesbaar
        if self.regel['eenheid'] == 'datum':
            huidige_waarde_text = self._format_datum_leesbaar(str(self.regel['waarde']))
        else:
            huidige_waarde_text = f"{self.regel['waarde']} {self.regel['eenheid']}"

        huidige_waarde = QLabel(huidige_waarde_text)
        huidige_waarde.setFont(QFont(Fonts.FAMILY, Fonts.SIZE_LARGE))
        huidige_waarde.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        huidig_group.addWidget(huidige_waarde)

        # Actief vanaf
        if self.regel.get('actief_vanaf'):
            datum = datetime.fromisoformat(self.regel['actief_vanaf'])
            datum_str = datum.strftime('%d-%m-%Y')
            vanaf_label = QLabel(f"Actief vanaf: {datum_str}")
            vanaf_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: {Fonts.SIZE_SMALL}px;")
            huidig_group.addWidget(vanaf_label)

        layout.addLayout(huidig_group)

        # Nieuwe waarde form
        form_layout = QFormLayout()
        form_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Nieuwe waarde input (conditioneel: terms, datum of numeriek)
        if self.regel['eenheid'] == 'terms':
            # Term type: gebruik checkbox lijst voor system terms
            self._create_term_checkboxes(form_layout)
        elif self.regel['eenheid'] == 'datum':
            # Datum type: gebruik dag/maand dropdowns
            datum_layout = QHBoxLayout()

            # Parse huidige datum waarde
            dag_start, maand_start = self._parse_datum_waarde(str(self.regel['waarde']))

            # Dag dropdown (1-31)
            self.datum_dag_input = QComboBox()
            self.datum_dag_input.addItems([str(d) for d in range(1, 32)])
            self.datum_dag_input.setCurrentText(str(dag_start))
            self.datum_dag_input.setStyleSheet(Styles.input_field())
            self.datum_dag_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
            datum_layout.addWidget(QLabel("Dag:"))
            datum_layout.addWidget(self.datum_dag_input)

            # Maand dropdown
            self.datum_maand_input = QComboBox()
            maanden = ['januari', 'februari', 'maart', 'april', 'mei', 'juni',
                       'juli', 'augustus', 'september', 'oktober', 'november', 'december']
            self.datum_maand_input.addItems(maanden)
            self.datum_maand_input.setCurrentIndex(maand_start - 1)
            self.datum_maand_input.setStyleSheet(Styles.input_field())
            self.datum_maand_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
            datum_layout.addWidget(QLabel("Maand:"))
            datum_layout.addWidget(self.datum_maand_input)

            datum_layout.addStretch()

            form_layout.addRow("Nieuwe datum:", datum_layout)
        else:
            # Numeriek type: gebruik spinbox
            self.waarde_input = QDoubleSpinBox()
            self.waarde_input.setMinimum(0.0)
            self.waarde_input.setMaximum(9999.0)
            self.waarde_input.setDecimals(1)
            self.waarde_input.setValue(float(self.regel['waarde']))
            self.waarde_input.setSuffix(f" {self.regel['eenheid']}")
            self.waarde_input.setStyleSheet(Styles.input_field())
            self.waarde_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
            form_layout.addRow("Nieuwe waarde:", self.waarde_input)

        # Actief vanaf datum
        self.actief_vanaf_input.setCalendarPopup(True)
        self.actief_vanaf_input.setDisplayFormat("dd-MM-yyyy")
        self.actief_vanaf_input.setDate(QDate.currentDate())
        self.actief_vanaf_input.setStyleSheet(Styles.input_field())
        self.actief_vanaf_input.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        form_layout.addRow("Actief vanaf:", self.actief_vanaf_input)

        layout.addLayout(form_layout)

        # Beschrijving tonen
        if self.regel.get('beschrijving'):
            beschrijving_clean = self.regel['beschrijving'].replace('VOORBEELD - ', '')
            beschrijving = QLabel(f"Beschrijving: {beschrijving_clean}")
            beschrijving.setStyleSheet(
                f"color: {Colors.TEXT_SECONDARY}; "
                f"font-style: italic; "
                f"font-size: {Fonts.SIZE_SMALL}px; "
                f"padding: {Dimensions.SPACING_MEDIUM}px; "
                f"background-color: {Colors.BG_LIGHT}; "
                f"border-radius: {Dimensions.RADIUS_MEDIUM}px;"
            )
            beschrijving.setWordWrap(True)
            layout.addWidget(beschrijving)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        annuleer_btn = QPushButton("Annuleren")
        annuleer_btn.setStyleSheet(Styles.button_secondary())
        annuleer_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        annuleer_btn.clicked.connect(self.reject)  # type: ignore
        button_layout.addWidget(annuleer_btn)

        opslaan_btn = QPushButton("Nieuwe Versie Opslaan")
        opslaan_btn.setStyleSheet(Styles.button_success())
        opslaan_btn.setMinimumHeight(Dimensions.BUTTON_HEIGHT_NORMAL)
        opslaan_btn.clicked.connect(self.valideer_en_accept)  # type: ignore
        button_layout.addWidget(opslaan_btn)

        layout.addLayout(button_layout)

    def valideer_en_accept(self):
        """Valideer input voordat we accepteren"""
        # Haal nieuwe waarde op (afhankelijk van type)
        if self.regel['eenheid'] == 'terms':
            # Term type: valideer dat minimaal 1 checkbox geselecteerd is
            geselecteerde_terms = [
                term for term, checkbox in self.term_checkboxes.items()
                if checkbox.isChecked()
            ]

            if not geselecteerde_terms:
                QMessageBox.warning(
                    self,
                    "Geen uitzonderingen geselecteerd",
                    "Selecteer minimaal 1 uitzondering die de regel mag onderbreken.\n\n"
                    "Tip: Meestal wil je minimaal 'verlof' en 'ziekte' selecteren."
                )
                return

            # Maak comma-separated string
            nieuwe_waarde = ','.join(sorted(geselecteerde_terms))
            oude_waarde = str(self.regel.get('beschrijving', ''))

        elif self.regel['eenheid'] == 'datum':
            # Datum type: maak DD-MM string
            dag = int(self.datum_dag_input.currentText())  # type: ignore
            maand = self.datum_maand_input.currentIndex() + 1  # type: ignore
            nieuwe_waarde = f"{dag:02d}-{maand:02d}"
            oude_waarde = str(self.regel['waarde'])
        else:
            # Numeriek type
            nieuwe_waarde = self.waarde_input.value()  # type: ignore
            oude_waarde = str(self.regel['waarde'])

        # Check of waarde is gewijzigd
        if str(nieuwe_waarde) == oude_waarde:
            QMessageBox.warning(
                self,
                "Geen wijziging",
                "De nieuwe waarde is hetzelfde als de huidige waarde.\n"
                "Wijzig de waarde of annuleer."
            )
            return

        # Check datum in verleden
        gekozen_datum = self.actief_vanaf_input.date().toPyDate()
        vandaag = datetime.now().date()

        if gekozen_datum < vandaag:
            reply = QMessageBox.question(
                self,
                "Datum in verleden",
                f"De gekozen datum ({gekozen_datum.strftime('%d-%m-%Y')}) ligt in het verleden.\n\n"
                "Dit betekent dat planning vanaf die datum opnieuw gevalideerd moet worden.\n"
                "Weet je zeker dat je wilt doorgaan?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.accept()

    def get_data(self) -> Dict[str, Any]:
        """Haal nieuwe data op"""
        datum = self.actief_vanaf_input.date().toPyDate()

        # Bepaal waarde op basis van type
        if self.regel['eenheid'] == 'terms':
            # Term type: verzamel geselecteerde terms
            geselecteerde_terms = [
                term for term, checkbox in self.term_checkboxes.items()
                if checkbox.isChecked()
            ]
            waarde = self.regel['waarde']  # Blijft 0.0
            beschrijving = ','.join(sorted(geselecteerde_terms))

            return {
                'waarde': waarde,
                'beschrijving': beschrijving,
                'actief_vanaf': datum.isoformat()
            }

        elif self.regel['eenheid'] == 'datum':
            dag = int(self.datum_dag_input.currentText())  # type: ignore
            maand = self.datum_maand_input.currentIndex() + 1  # type: ignore
            waarde = f"{dag:02d}-{maand:02d}"
        else:
            waarde = self.waarde_input.value()  # type: ignore

        return {
            'waarde': waarde,
            'actief_vanaf': datum.isoformat()
        }

    def _create_term_checkboxes(self, form_layout: QFormLayout):
        """
        Maak checkbox lijst voor term selectie

        Args:
            form_layout: Form layout om checkboxes aan toe te voegen
        """
        # Haal huidige geselecteerde terms op
        huidige_beschrijving = str(self.regel.get('beschrijving', ''))
        geselecteerde_terms = {term.strip() for term in huidige_beschrijving.split(',') if term.strip()}

        # Haal alle beschikbare system terms op (uit TermCodeService)
        # Deze zijn gegarandeerd beschikbaar
        beschikbare_terms = {
            'verlof': 'Verlof',
            'ziek': 'Ziekte',
            'kompensatiedag': 'Kompensatiedag',
            'zondagrust': 'Zondagrust',
            'zaterdagrust': 'Zaterdagrust',
            'arbeidsduurverkorting': 'Arbeidsduurverkorting'
        }

        # GroupBox voor checkboxes
        group = QGroupBox("Uitzonderingen (codes die de regel onderbreken)")
        group_layout = QVBoxLayout()
        group_layout.setSpacing(Dimensions.SPACING_SMALL)

        # Info label
        info = QLabel("Selecteer welke codes het patroon 'nacht → vroeg' mogen onderbreken:")
        info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: {Fonts.SIZE_SMALL}px;")
        info.setWordWrap(True)
        group_layout.addWidget(info)

        # Maak checkbox voor elke term
        for term, display_naam in sorted(beschikbare_terms.items()):
            # Haal actuele code op via TermCodeService
            actuele_code = TermCodeService.get_code_for_term(term)

            # Maak checkbox
            checkbox = QCheckBox(f"{display_naam} ({actuele_code})")
            checkbox.setChecked(term in geselecteerde_terms)
            checkbox.setStyleSheet(f"font-size: {Fonts.SIZE_NORMAL}px;")

            # Sla checkbox op
            self.term_checkboxes[term] = checkbox

            group_layout.addWidget(checkbox)

        group.setLayout(group_layout)
        form_layout.addRow(group)

    @staticmethod
    def _parse_datum_waarde(waarde: str) -> tuple[int, int]:
        """
        Parse DD-MM formaat naar (dag, maand).
        Returns: (dag, maand) tuple, default (1, 5) bij fout
        """
        try:
            parts = waarde.split('-')
            if len(parts) == 2:
                dag = int(parts[0])
                maand = int(parts[1])
                return (dag, maand)
        except (ValueError, IndexError):
            pass

        return (1, 5)  # Default: 1 mei

    @staticmethod
    def _format_datum_leesbaar(waarde: str) -> str:
        """
        Format DD-MM naar leesbare vorm (bijv. "1 mei").
        """
        try:
            parts = waarde.split('-')
            if len(parts) == 2:
                dag = int(parts[0])
                maand = int(parts[1])

                maanden = ['', 'januari', 'februari', 'maart', 'april', 'mei', 'juni',
                           'juli', 'augustus', 'september', 'oktober', 'november', 'december']

                if 1 <= maand <= 12:
                    return f"{dag} {maanden[maand]}"
        except (ValueError, IndexError):
            pass

        return waarde  # Fallback: raw value
