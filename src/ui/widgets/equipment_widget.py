"""Section « Équipement / Inventaire » repliable (cartes d'objets)."""

import re

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.models.monster import Action
from src.ui.widgets.card_list import CardListWidget, card_add_button
from src.ui.widgets.collapsible_header import CollapsibleHeader

EQUIPMENT_DESCRIPTION_PLACEHOLDER = (
    "Effets de l'objet : dégâts, CA, pouvoir…\n"
    "Ex : +2 à la CA, ou perforant 1d6, légère."
)


class EquipmentWidget(QWidget):
    """Inventaire en cartes éditables, synchronisé avec monster.notes."""

    from PySide6.QtCore import Signal
    add_requested = Signal()
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._expanded = False
        self.toggle_header = CollapsibleHeader(
            "Équipement / Inventaire (optionnel)"
        )
        self.toggle_header.setToolTip(
            "Cliquer pour déplier ou replier la section équipement"
        )
        self.toggle_header.clicked.connect(self._toggle)
        layout.addWidget(self.toggle_header)

        self.content = QWidget()
        self.content.setStyleSheet("""
            QWidget {
                background-color: #161f2a;
                border: 1px solid #3e5a8a;
                border-top: none;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
            }
        """)
        equipment_vlayout = QVBoxLayout(self.content)
        equipment_vlayout.setContentsMargins(8, 8, 8, 8)
        equipment_vlayout.setSpacing(8)

        equipment_title = QLabel("Équipement / Inventaire :")
        equipment_title.setStyleSheet(
            "color: #bbdefb; font-weight: bold; background: transparent; border: none;"
        )
        equipment_vlayout.addWidget(equipment_title)

        self.cards = CardListWidget(
            empty_text=(
                "Aucun objet — cliquez sur \"Nouvel objet\" pour ajouter du "
                "matériel à l'inventaire."
            ),
            name_placeholder="Nom de l'objet",
            remove_tooltip="Supprimer cet objet",
            description_placeholder=EQUIPMENT_DESCRIPTION_PLACEHOLDER,
        )
        equipment_vlayout.addWidget(self.cards, stretch=1)

        equipment_control_layout = QHBoxLayout()
        equipment_control_layout.addStretch()
        self.add_equipment_btn = card_add_button(
            "Nouvel objet", "Ajouter un nouvel objet à l'inventaire"
        )
        self.add_equipment_btn.clicked.connect(self.add_requested.emit)
        equipment_control_layout.addWidget(self.add_equipment_btn)
        equipment_control_layout.addStretch()
        equipment_vlayout.addLayout(equipment_control_layout)

        layout.addWidget(self.content)
        self._apply_toggle_state()

    def _toggle(self):
        """Affiche ou masque la section équipement."""
        self._expanded = not self._expanded
        self._apply_toggle_state()

    def _apply_toggle_state(self):
        """Applique l'état replié/déplié de la section équipement."""
        self.content.setVisible(self._expanded)
        self.toggle_header.set_expanded(self._expanded)

    def add_item(self):
        """Ajoute une carte d'objet vide à l'inventaire."""
        self.add_item_to_list("")

    def add_item_to_list(self, item: str):
        """Ajoute un widget d'objet éditable (nom + effets) à la liste."""
        widget = self.cards.create_card(
            Action(name=item, description="")
        )
        widget.changed.connect(self.changed.emit)
        widget.removeRequested.connect(self.cards.remove_card)
        widget.removeRequested.connect(lambda: self.changed.emit())
        self.cards.add_card(widget)

    def set_notes(self, notes: str):
        """Remplit la liste de cartes d'objets depuis le texte d'inventaire
        (format « objet (effets) » ou « objet », séparés par virgules ou
        retours à la ligne — les séparateurs internes aux parenthèses
        sont préservés)."""
        self.clear_items()

        items = []
        depth = 0
        current = ""
        for ch in notes or "":
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth = max(0, depth - 1)
            if ch in ",\n" and depth == 0:
                items.append(current)
                current = ""
            else:
                current += ch
        if current.strip():
            items.append(current)

        for chunk in items:
            chunk = chunk.strip()
            if not chunk:
                continue
            match = re.match(r"(.+?)\s*\((.*)\)\s*$", chunk, flags=re.S)
            effects = match.group(2).strip() if match else ""
            cards = self.cards.get_cards()
            if cards:
                cards[-1].description_edit.setPlainText(effects)

    def clear_items(self):
        """Retire toutes les cartes d'objets."""
        self.cards.clear()

    def to_notes(self) -> str:
        """Reconstruit le texte d'inventaire (monster.notes) depuis les
        cartes d'objets : chaque carte est une ligne « nom (effets) »."""
        parts = []
        for widget in self.cards.get_cards():
            name = widget.name_edit.text().strip()
            effects = widget.description_edit.toPlainText().strip()
            if name and effects:
                parts.append(f"{name} ({effects})")
            elif name:
                parts.append(name)
        return "\n".join(parts)
