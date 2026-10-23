"""Onglet « Actions » : génération IA et cartes d'actions éditables."""

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

from src.models.monster import Action
from src.ui.styles import ACCENT_BUTTON_STYLE, SECONDARY_BUTTON_STYLE
from src.ui.widgets.card_list import CardListWidget, card_add_button


class ActionsTab(QWidget):
    """Liste d'actions éditables + boutons de génération IA."""

    from PySide6.QtCore import Signal
    generate_requested = Signal()
    generate_from_prompt_requested = Signal()
    add_requested = Signal()
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        actions_frame = QFrame()
        actions_frame.setFrameShape(QFrame.Shape.StyledPanel)
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: #161f2a;
                border: 1px solid #3e5a8a;
                border-radius: 6px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        actions_vlayout = QVBoxLayout(actions_frame)
        actions_vlayout.setContentsMargins(8, 8, 8, 8)
        actions_vlayout.setSpacing(8)

        actions_title = QLabel("Actions :")
        actions_title.setStyleSheet(
            "color: #bbdefb; font-weight: bold; background: transparent; border: none;"
        )
        actions_vlayout.addWidget(actions_title)

        gen_actions_btn = QPushButton("Générer des actions")
        gen_actions_btn.setIcon(QIcon.fromTheme("system-run"))
        gen_actions_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        gen_actions_btn.clicked.connect(self.generate_requested.emit)
        actions_vlayout.addWidget(gen_actions_btn)

        prompt_row = QHBoxLayout()
        prompt_row.setContentsMargins(14, 0, 0, 0)
        prompt_row.setSpacing(6)
        self.actions_prompt_edit = QTextEdit()
        self.actions_prompt_edit.setPlaceholderText(
            "Ou décrivez vos actions ici (ex : tir à l'arc, morsure empoisonnée…)"
        )
        self.actions_prompt_edit.setMaximumHeight(34)
        self.actions_prompt_edit.setAcceptRichText(False)
        self.actions_prompt_edit.setStyleSheet("font-size: 11px; padding: 2px 6px;")
        prompt_row.addWidget(self.actions_prompt_edit, stretch=1)
        self.gen_actions_prompt_btn = QPushButton("Générer")
        self.gen_actions_prompt_btn.setToolTip(
            "Génère les actions décrites à gauche, avec les stats équilibrées pour le CR"
        )
        self.gen_actions_prompt_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self.gen_actions_prompt_btn.clicked.connect(
            self.generate_from_prompt_requested.emit
        )
        prompt_row.addWidget(self.gen_actions_prompt_btn)
        actions_vlayout.addLayout(prompt_row)

        self.cards = CardListWidget(
            empty_text=(
                "Aucune action — cliquez sur \"Nouvelle action\" "
                "ou générez-les automatiquement."
            ),
        )
        actions_vlayout.addWidget(self.cards, stretch=1)

        actions_control_layout = QHBoxLayout()
        actions_control_layout.addStretch()

        self.add_action_btn = card_add_button(
            "Nouvelle action", "Ajouter une nouvelle action à la liste"
        )
        self.add_action_btn.clicked.connect(self.add_requested.emit)
        actions_control_layout.addWidget(self.add_action_btn)
        actions_control_layout.addStretch()

        actions_vlayout.addLayout(actions_control_layout)

        layout.addWidget(actions_frame, stretch=1)

    def add_action(self, action: Action):
        """Ajoute une carte d'action éditable à la liste."""
        widget = self.cards.create_card(action)
        widget.changed.connect(self.changed.emit)
        widget.removeRequested.connect(self.cards.remove_card)
        widget.removeRequested.connect(lambda: self.changed.emit())
        self.cards.add_card(widget)

    def set_actions(self, actions):
        """Remplace toutes les cartes par les actions données."""
        self.cards.clear()
        for action in actions:
            self.add_action(action)

    def get_actions(self) -> list:
        """Actions valides (avec nom) présentes dans les cartes."""
        return [
            widget.get_action()
            for widget in self.cards.get_cards()
            if widget.get_action().name
        ]
