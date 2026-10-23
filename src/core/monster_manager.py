"""Gestionnaire central du monstre courant et de ses exports.

Le MonsterManager est l'unique point d'accès de l'UI aux données du
monstre : il détient l'objet Monster actif, notifie l'UI via un signal
Qt quand les données changent, et délègue les exports aux systèmes
d'export PNG/PDF. Aucune dépendance aux widgets de l'interface.
"""

from PySide6.QtCore import QObject, Signal

from src.export.pdf_exporter import pdf_exporter
from src.export.png_exporter import png_exporter
from src.models.monster import Monster


class MonsterManager(QObject):
    """Détient le monstre courant et gère les exports PNG/PDF."""

    monster_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._monster = Monster()

    @property
    def monster(self) -> Monster:
        return self._monster

    def set_monster(self, monster: Monster):
        """Remplace le monstre courant et notifie l'UI."""
        self._monster = monster or Monster()
        self.monster_changed.emit(self._monster)

    def update_monster(self, monster: Monster):
        """Met à jour le monstre courant depuis le formulaire de l'UI."""
        self._monster = monster

    def export_to_pdf(self, monster: Monster, file_path: str):
        """Exporte la fiche du monstre en PDF."""
        pdf_exporter.export_to_pdf(monster, file_path)

    def export_to_png(self, monster: Monster, file_path: str):
        """Exporte la fiche du monstre en PNG (style stat block officiel)."""
        png_exporter.export_to_png(monster, file_path)
