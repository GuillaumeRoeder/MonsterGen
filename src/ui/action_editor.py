"""
Widget d'action pour la liste des actions : carte visuelle avec nom,
description complète, badges de stats de combat (bonus d'attaque, dégâts,
DD) et une croix pour supprimer l'action directement.
"""

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QTextEdit,
    QVBoxLayout, QWidget,
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
    QLabel#ActionHeader {
        color: #e8e8f0;
        font-size: 12px;
    }
    QLabel#StatCaption {
        color: #9aa0b4;
        font-size: 11px;
    }
    QLabel#ActionBadge {
        background-color: #005f8a;
        color: #ffffff;
        border-radius: 9px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: bold;
    }
    QLabel#ActionBadgeDamage {
        background-color: #8a2f45;
        color: #ffffff;
        border-radius: 9px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: bold;
    }
    QLabel#ActionBadgeDC {
        background-color: #6a4f8a;
        color: #ffffff;
        border-radius: 9px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: bold;
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
    """Carte d'édition d'une action : nom, stats structurées, description."""

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

        # --- Ligne 1 : nom + badges + croix ---
        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)

        self.name_edit = QLineEdit(action.name or "")
        self.name_edit.setPlaceholderText("Nom de l'action")
        self.name_edit.setStyleSheet(
            "font-weight: bold; font-size: 13px; background: transparent; border: none;"
        )
        top_layout.addWidget(self.name_edit, stretch=1)

        self.bonus_label = self._make_badge("ActionBadge")
        top_layout.addWidget(self.bonus_label)

        self.damage_label = self._make_badge("ActionBadgeDamage")
        top_layout.addWidget(self.damage_label)

        self.dc_label = self._make_badge("ActionBadgeDC")
        top_layout.addWidget(self.dc_label)

        self.remove_btn = QPushButton("✕")
        self.remove_btn.setObjectName("RemoveButton")
        self.remove_btn.setFixedSize(22, 22)
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.setToolTip("Supprimer cette action")
        self.remove_btn.clicked.connect(lambda *args: self.removeRequested.emit(self))
        top_layout.addWidget(self.remove_btn)

        layout.addLayout(top_layout)

        # --- Champs structurés (bonus, dégâts, type, DD) ---
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(6)

        stats_layout.addWidget(self._caption("Bonus :"))
        self.bonus_spin = self._make_spin(-20, 30)
        self.bonus_spin.setValue(action.attack_bonus or 0)
        stats_layout.addWidget(self.bonus_spin)

        stats_layout.addWidget(self._caption("Dégâts :"))
        self.damage_edit = QLineEdit(action.damage or "")
        self.damage_edit.setPlaceholderText("2d6+3")
        self.damage_edit.setMaximumWidth(80)
        stats_layout.addWidget(self.damage_edit)

        stats_layout.addWidget(self._caption("Type :"))
        self.type_edit = QLineEdit(action.damage_type or "")
        self.type_edit.setPlaceholderText("tranchant")
        self.type_edit.setMaximumWidth(100)
        stats_layout.addWidget(self.type_edit)

        stats_layout.addWidget(self._caption("DD :"))
        self.dd_spin = self._make_spin(0, 30)
        self.dd_spin.setToolTip("DD de sauvegarde (0 = aucun)")
        stats_layout.addWidget(self.dd_spin)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # --- Description (récupérée telle quelle sur le PDF) ---
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            "Description de l'action (exportée dans le PDF)"
        )
        self.description_edit.setPlainText(action.description or "")
        self.description_edit.setMaximumHeight(64)
        self.description_edit.setAcceptRichText(False)
        layout.addWidget(self.description_edit)

        # DD extrait de la description si présent
        dd = 0
        match = re.search(r"DD\s*(\d+)", action.description or "")
        if match:
            dd = int(match.group(1))
        self.dd_spin.setValue(dd)

        self._update_badges()

        self.name_edit.textChanged.connect(self._on_changed)
        self.bonus_spin.valueChanged.connect(self._on_changed)
        self.damage_edit.textChanged.connect(self._on_changed)
        self.type_edit.textChanged.connect(self._on_changed)
        self.dd_spin.valueChanged.connect(self._on_changed)
        self.description_edit.textChanged.connect(self._on_changed)

    def _caption(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("StatCaption")
        return label

    def _make_badge(self, object_name: str) -> QLabel:
        label = QLabel("")
        label.setObjectName(object_name)
        label.hide()
        return label

    def _make_spin(self, minimum: int, maximum: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        spin.setFixedWidth(46)
        return spin

    def _on_changed(self):
        if self._updating:
            return
        self._update_badges()
        self.changed.emit()

    def _update_badges(self):
        """Met à jour les badges visuels selon les champs structurés."""
        bonus = self.bonus_spin.value()
        damage = self.damage_edit.text().strip()
        damage_type = self.type_edit.text().strip()
        dd = self.dd_spin.value()

        if damage:
            text = damage
            if damage_type:
                text += f" {damage_type}"
            self.damage_label.setText(text)
            self.damage_label.show()
        else:
            self.damage_label.hide()

        if bonus:
            self.bonus_label.setText(f"+{bonus} atq")
            self.bonus_label.show()
        else:
            self.bonus_label.hide()

        if dd:
            self.dc_label.setText(f"DD {dd}")
            self.dc_label.show()
        else:
            self.dc_label.hide()

    def get_action(self) -> Action:
        """Construit l'objet Action depuis les champs du widget."""
        return Action(
            name=self.name_edit.text().strip(),
            description=self.description_edit.toPlainText().strip(),
            attack_bonus=self.bonus_spin.value() or None,
            damage=self.damage_edit.text().strip() or None,
            damage_type=self.type_edit.text().strip() or None,
        )

    def set_action(self, action: Action):
        """Remplit le widget depuis un objet Action."""
        self._updating = True
        self.name_edit.setText(action.name or "")
        self.bonus_spin.setValue(action.attack_bonus or 0)
        self.damage_edit.setText(action.damage or "")
        self.type_edit.setText(action.damage_type or "")
        self.description_edit.setPlainText(action.description or "")

        dd = 0
        match = re.search(r"DD\s*(\d+)", action.description or "")
        if match:
            dd = int(match.group(1))
        self.dd_spin.setValue(dd)
        self._updating = False
        self._update_badges()
