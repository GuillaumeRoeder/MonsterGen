"""
Éditeur de langues sous forme de "pills" (étiquettes détachables).

Chaque langue sélectionnée apparaît comme une pillule avec une petite croix
pour la retirer. L'ajout se fait via une liste déroulante des langues DnD 5e
(hardcodées) et un bouton Ajouter.
"""

from typing import List

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QLayout, QPushButton,
    QVBoxLayout, QWidget
)

from src.ai.ai_generator import DND5_LANGUAGES


class FlowLayout(QLayout):
    """Disposition qui fait passer les widgets à la ligne automatiquement."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self._items = []

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation.Horizontal)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        margins = self.contentsMargins()
        x = rect.x() + margins.left()
        y = rect.y() + margins.top()
        line_height = 0
        right = rect.right() - margins.right()

        for item in self._items:
            hint = item.sizeHint()
            next_x = x + hint.width() + 6
            if next_x - 6 > right and line_height > 0:
                x = rect.x() + margins.left()
                y = y + line_height + 6
                line_height = 0
                next_x = x + hint.width() + 6
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x = next_x
            line_height = max(line_height, hint.height())
        return y + line_height + margins.bottom() - rect.y()


class LanguagesEditor(QWidget):
    """Champ de saisie de langues en pills détachables."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._languages: List[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._pills_widget = QWidget()
        self._pills_layout = FlowLayout(self._pills_widget)
        layout.addWidget(self._pills_widget)

        self._empty_label = QLabel("Aucune langue")
        self._empty_label.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(self._empty_label)

        add_layout = QHBoxLayout()
        add_layout.setContentsMargins(0, 0, 0, 0)

        self._combo = QComboBox()
        self._combo.addItems(DND5_LANGUAGES)
        add_layout.addWidget(self._combo, stretch=1)

        add_btn = QPushButton("+ Ajouter")
        add_btn.clicked.connect(self._add_selected)
        add_layout.addWidget(add_btn)

        layout.addLayout(add_layout)

        self._refresh()

    def _add_selected(self):
        language = self._combo.currentText().strip()
        if language and language not in self._languages:
            self._languages.append(language)
            self._refresh()

    def _remove_language(self, language: str):
        if language in self._languages:
            self._languages.remove(language)
            self._refresh()

    def _refresh(self):
        while self._pills_layout.count():
            item = self._pills_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for language in self._languages:
            pill = QWidget()
            pill.setStyleSheet("""
                QWidget {
                    background-color: #005f8a;
                    color: #ffffff;
                    border-radius: 9px;
                }
            """)
            pill_layout = QHBoxLayout(pill)
            pill_layout.setContentsMargins(8, 2, 2, 2)
            pill_layout.setSpacing(4)

            label = QLabel(language)
            label.setStyleSheet("background: transparent; border: none; color: #ffffff;")
            pill_layout.addWidget(label)

            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(16, 16)
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.setToolTip(f"Retirer {language}")
            remove_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #ffffff;
                    font-size: 9px;
                }
                QPushButton:hover {
                    color: #ff8888;
                }
            """)
            remove_btn.clicked.connect(lambda *args, lang=language: self._remove_language(lang))
            pill_layout.addWidget(remove_btn)

            self._pills_layout.addWidget(pill)

        self._empty_label.setVisible(not self._languages)

    def get_languages(self) -> List[str]:
        """Liste des langues sélectionnées."""
        return list(self._languages)

    def set_languages(self, languages: List[str]):
        """Définit la liste des langues sélectionnées."""
        self._languages = [l.strip() for l in languages if l and l.strip()]
        self._refresh()

    def setPlainText(self, text: str):
        """Compatibilité avec l'ancien champ QTextEdit (texte séparé par virgules)."""
        languages = [l.strip() for l in text.split(",") if l.strip()]
        self.set_languages(languages)

    def toPlainText(self) -> str:
        """Compatibilité avec l'ancien champ QTextEdit."""
        return ", ".join(self._languages)
