"""
Éditeur de langues sous forme de "pills" (étiquettes détachables).
Réutilise PillEditor avec la liste des langues DnD 5e et conserve la
compatibilité avec l'ancien champ QTextEdit (setPlainText/toPlainText).
"""

from typing import List

from src.ai.ai_generator import DND5_LANGUAGES
from src.ui.pill_editor import PillEditor


class LanguagesEditor(PillEditor):
    """Champ de saisie de langues en pills détachables."""

    def __init__(self, parent=None):
        super().__init__(suggestions=DND5_LANGUAGES,
                         empty_text="Aucune langue", parent=parent)

    def get_languages(self) -> List[str]:
        """Liste des langues sélectionnées."""
        return self.get_values()

    def set_languages(self, languages: List[str]):
        """Définit la liste des langues sélectionnées."""
        self.set_values(languages)

    def setPlainText(self, text: str):
        """Compatibilité avec l'ancien champ QTextEdit (texte séparé par virgules)."""
        self.set_values([l.strip() for l in text.split(",") if l.strip()])

    def toPlainText(self) -> str:
        """Compatibilité avec l'ancien champ QTextEdit."""
        return ", ".join(self._values)
