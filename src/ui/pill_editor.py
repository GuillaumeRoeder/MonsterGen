"""
Éditeur générique en "pills" : étiquettes détachables alimentées par une
liste de valeurs prédéfinies. Utilisé pour les langues, les compétences
maîtrisées, les résistances et les immunités.
"""

from typing import List, Optional

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QLayout, QPushButton,
    QVBoxLayout, QWidget
)


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


class PillEditor(QWidget):
    """Champ en pills détachables alimenté par une liste prédéfinie.

    Les valeurs sont ajoutées via une liste déroulante (valeurs suggérées)
    ou saisie libre optionnelle, et retirées par une croix sur chaque pill.
    """

    valuesChanged = Signal()

    def __init__(self, suggestions: Optional[List[str]] = None,
                 allow_free_text: bool = False, empty_text: str = "Aucune valeur",
                 parent=None):
        super().__init__(parent)
        self._values: List[str] = []
        self._suggestions = list(suggestions or [])
        self._allow_free_text = allow_free_text

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Ligne d'ajout : combobox compacte + petit bouton, au-dessus des pills
        add_layout = QHBoxLayout()
        add_layout.setContentsMargins(0, 0, 0, 0)
        add_layout.setSpacing(6)
        self._combo = QComboBox()
        self._combo.setEditable(allow_free_text)
        if allow_free_text:
            self._combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._combo.addItems(self._suggestions)
        self._combo.setStyleSheet("""
            QComboBox {
                padding: 3px 8px;
                min-height: 0px;
            }
        """)
        add_layout.addWidget(self._combo, stretch=1)
        add_btn = QPushButton("+")
        add_btn.setFixedSize(26, 24)
        add_btn.setToolTip("Ajouter la valeur sélectionnée")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                padding: 0px;
                min-height: 0px;
                min-width: 0px;
                font-weight: bold;
            }
        """)
        add_btn.clicked.connect(self._add_selected)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)

        # Pills sous la ligne d'ajout
        self._pills_widget = QWidget()
        self._pills_layout = FlowLayout(self._pills_widget)
        layout.addWidget(self._pills_widget)
        self._empty_label = QLabel(empty_text)
        self._empty_label.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(self._empty_label)

        self._refresh()

    def _add_selected(self):
        value = self._combo.currentText().strip()
        if value and value not in self._values:
            self._values.append(value)
            self._refresh()
            self.valuesChanged.emit()

    def _remove_value(self, value: str):
        if value in self._values:
            self._values.remove(value)
            self._refresh()
            self.valuesChanged.emit()

    def _refresh(self):
        while self._pills_layout.count():
            item = self._pills_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for value in self._values:
            pill = QWidget()
            pill.setStyleSheet("""
                QWidget {
                    background-color: #1e5fa8;
                    color: #ffffff;
                    border-radius: 9px;
                }
            """)
            pill_layout = QHBoxLayout(pill)
            pill_layout.setContentsMargins(8, 2, 2, 2)
            pill_layout.setSpacing(4)

            label = QLabel(value)
            label.setStyleSheet("background: transparent; border: none; color: #ffffff;")
            pill_layout.addWidget(label)

            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(18, 18)
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.setToolTip(f"Retirer {value}")
            remove_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #ffffff;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0px;
                    min-height: 0px;
                    min-width: 0px;
                }
                QPushButton:hover {
                    color: #ff8888;
                }
            """)
            remove_btn.clicked.connect(lambda *args, v=value: self._remove_value(v))
            pill_layout.addWidget(remove_btn)

            self._pills_layout.addWidget(pill)

        self._empty_label.setVisible(not self._values)

    def get_values(self) -> List[str]:
        """Liste des valeurs sélectionnées."""
        return list(self._values)

    def set_values(self, values: List[str]):
        """Définit la liste des valeurs sélectionnées."""
        self._values = [v.strip() for v in values if v and v.strip()]
        self._refresh()

    def set_suggestions(self, suggestions: List[str]):
        """Remplace les valeurs suggérées dans la liste déroulante."""
        self._suggestions = list(suggestions)
        current = self._combo.currentText()
        self._combo.clear()
        self._combo.addItems(self._suggestions)
        if current:
            self._combo.setCurrentText(current)
