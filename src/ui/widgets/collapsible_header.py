"""Widgets réutilisables partagés entre les onglets de l'interface."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel


class CollapsibleHeader(QFrame):
    """Barre de titre cliquable et repliable (style Attribute Editor Maya).

    Flèche et texte sont des labels séparés : le titre reste toujours
    visible, quel que soit l'état de la section.
    """

    clicked = Signal()

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: #212b38;
                border: 1px solid #3e5a8a;
                border-radius: 3px;
            }
            QFrame:hover {
                background-color: #212b38;
            }
            QLabel {
                background: transparent;
                border: none;
                color: #bbdefb;
                font-weight: bold;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        self._arrow_label = QLabel("▸")
        self._arrow_label.setFixedWidth(14)
        self._title_label = QLabel(title)
        layout.addWidget(self._arrow_label)
        layout.addWidget(self._title_label)
        layout.addStretch()

    def set_expanded(self, expanded: bool):
        """Met à jour la flèche selon l'état de la section."""
        self._arrow_label.setText("▾" if expanded else "▸")

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
