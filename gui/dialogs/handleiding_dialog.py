# gui/dialogs/handleiding_dialog.py
"""
Handleiding Dialog
Opent gebruikershandleiding in standaard browser
"""
from PyQt6.QtWidgets import QMessageBox
from gui.styles import Styles, Dimensions
import os
import webbrowser


class HandleidingDialog:
    """Opent handleiding in standaard browser"""

    def __init__(self, parent):
        self.parent = parent
        self.open_handleiding()

    def exec(self):
        """Dummy exec() methode voor backwards compatibility"""
        # Handleiding is al geopend in __init__, deze methode doet niets
        return 0

    def open_handleiding(self):
        """Open Handleiding.html in standaard browser"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        handleiding_path = os.path.join(script_dir, '..', '..', 'Handleiding.html')

        # Controleer of bestand bestaat
        if not os.path.exists(handleiding_path):
            QMessageBox.warning(
                self.parent,
                "Handleiding niet gevonden",
                f"De handleiding kon niet gevonden worden:\n{handleiding_path}"
            )
            return

        # Open in standaard browser
        try:
            webbrowser.open('file://' + os.path.abspath(handleiding_path))
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Fout bij openen handleiding",
                f"Kon handleiding niet openen:\n{str(e)}"
            )