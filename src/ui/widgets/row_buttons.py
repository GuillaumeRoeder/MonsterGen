"""Widgets utilitaires intégrés aux lignes de tableaux (QTableWidget).

Un bouton posé directement via setCellWidget « flotte » au-dessus de la
cellule : il garde son cadre de QPushButton et dépasse visuellement de la
ligne. Les classes ci-dessous produisent des boutons plats, sans bordure
ni fond, rendus au sein d'un conteneur aligné dans la cellule — le
résultat s'intègre à la ligne au lieu d'être superposé à elle.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


ROW_BUTTON_QSS = """
    QPushButton {
        background: transparent;
        border: none;
        color: %s;
        font-size: 11px;
        padding: 0px;
        margin: 0px;
    }
    QPushButton:hover {
        color: %s;
    }
    QPushButton:pressed {
        color: %s;
    }
"""


class RowButton(QPushButton):
    """Bouton plat sans cadre ni fond, destiné à une cellule de tableau."""

    def __init__(self, glyph: str, tooltip: str = "",
                 normal_color: str = "#9aa0b4", hover_color: str = "#e0e0e0",
                 pressed_color: str = "#ffffff"):
        super().__init__(glyph)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setFixedSize(22, 18)
        style = ROW_BUTTON_QSS % (normal_color, hover_color, pressed_color)
        self.setStyleSheet(style)

    def sizeHint(self) -> QSize:
        return QSize(22, 18)


class RowButtons(QWidget):
    """Conteneur de boutons plats centrés dans une cellule de tableau."""

    def __init__(self, buttons, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addStretch()
        for button in buttons:
            layout.addWidget(button)
        layout.addStretch()
