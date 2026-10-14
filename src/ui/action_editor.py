"""
Widget d'action pour la liste des actions : carte visuelle avec nom et
description complète. Les stats de combat (bonus d'attaque, dégâts, DD)
sont écrites directement dans la description, comme sur les stat blocks
officiels DnD 5e.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

from src.models.monster import Action

ACTION_CARD_STYLE = """
    ActionEditorWidget#ActionCard {
        background-color: #3f4149;
        border: 1px solid #5a5a6a;
        border-radius: 8px;
    }
    ActionEditorWidget#ActionCard:hover {
        border: 1px solid #00aaff;
    }
    QPushButton#RemoveButton {
        background-color: transparent;
        border: none;
        color: #888899;
        font-size: 14px;
        font-weight: bold;
        padding: 2px;
    }
    QPushButton#RemoveButton:hover {
        color: #ff6666;
    }
"""


class ActionEditorWidget(QWidget):
    """Carte d'édition d'une action : nom + description (tout y est écrit)."""

    changed = Signal()
    removeRequested = Signal(object)

    def __init__(self, action: Action, parent=None):
        super().__init__(parent)
        self.setObjectName("ActionCard")
        self.setStyleSheet(ACTION_CARD_STYLE)
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # --- Ligne 1 : nom + croix ---
        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)

        self.name_edit = QLineEdit(action.name or "")
        self.name_edit.setPlaceholderText("Nom de l'action")
        self.name_edit.setStyleSheet(
            "font-weight: bold; font-size: 13px; background: transparent; border: none;"
        )
        top_layout.addWidget(self.name_edit, stretch=1)

        self.remove_btn = QPushButton("✕")
        self.remove_btn.setObjectName("RemoveButton")
        self.remove_btn.setFixedSize(22, 22)
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.setToolTip("Supprimer cette action")
        self.remove_btn.clicked.connect(lambda *args: self.removeRequested.emit(self))
        top_layout.addWidget(self.remove_btn)

        layout.addLayout(top_layout)

        # --- Description : tout (bonus, dégâts, DD) y est écrit ---
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            "Description complète : bonus au toucher, dégâts, DD de sauvegarde…\n"
            "Ex : Attaque d'arme au corps à corps : +6 au toucher, 2d8+4 dégâts "
            "tranchants, portée 1,50 m."
        )
        self.description_edit.setPlainText(action.description or "")
        self.description_edit.setAcceptRichText(False)
        layout.addWidget(self.description_edit)

        self.name_edit.textChanged.connect(self._on_changed)
        self.description_edit.textChanged.connect(self._on_changed)

    def _on_changed(self):
        if self._updating:
            return
        self.changed.emit()

    def get_action(self) -> Action:
        """Construit l'objet Action (nom + description uniquement)."""
        return Action(
            name=self.name_edit.text().strip(),
            description=self.description_edit.toPlainText().strip(),
        )

    def set_action(self, action: Action):
        """Remplit le widget depuis un objet Action."""
        self._updating = True
        self.name_edit.setText(action.name or "")
        self.description_edit.setPlainText(action.description or "")
        self._updating = False
