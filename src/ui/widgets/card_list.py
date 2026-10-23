"""Widget générique : liste scrollable de cartes éditables (actions/objets)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from src.models.monster import Action
from src.ui.action_editor import ActionEditorWidget
from src.ui.styles import SECONDARY_BUTTON_STYLE


class CardListWidget(QWidget):
    """Liste scrollable de cartes ActionEditorWidget (actions ou objets).

    Chaque système (actions, équipement) instancie ce widget avec ses
    libellés et placeholders propres ; il émet « changed » à chaque
    modification d'une carte.
    """

    def __init__(
        self,
        empty_text: str,
        name_placeholder: str = "",
        remove_tooltip: str = "",
        description_placeholder: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._name_placeholder = name_placeholder
        self._remove_tooltip = remove_tooltip
        self._description_placeholder = description_placeholder

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setMinimumHeight(120)
        self.scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.scroll.setStyleSheet("""
            QScrollArea {
                background-color: #141b26;
                border: 1px solid #39485c;
                border-radius: 4px;
            }
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent; border: none;")
        self.card_layout = QVBoxLayout(self.container)
        self.card_layout.setContentsMargins(4, 4, 4, 4)
        self.card_layout.setSpacing(8)
        self.card_layout.addStretch()

        self.empty_label = QLabel(empty_text)
        self.empty_label.setStyleSheet(
            "color: #7a8aa0; font-style: italic; "
            "background: transparent; border: none;"
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_layout.insertWidget(0, self.empty_label)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

    def create_card(self, action: Action) -> ActionEditorWidget:
        """Crée la carte pour une action/objet donné (sans l'insérer)."""
        return ActionEditorWidget(
            action,
            name_placeholder=self._name_placeholder,
            remove_tooltip=self._remove_tooltip,
            description_placeholder=self._description_placeholder,
        )

    def add_card(self, widget: ActionEditorWidget):
        """Insère une carte avant l'étirement final."""
        self.card_layout.insertWidget(self.card_layout.count() - 1, widget)
        self._update_empty_label()

    def get_cards(self) -> list:
        """Cartes actuellement présentes dans la liste."""
        return [
            self.card_layout.itemAt(i).widget()
            for i in range(self.card_layout.count())
            if self.card_layout.itemAt(i).widget() is not None
            and isinstance(self.card_layout.itemAt(i).widget(), ActionEditorWidget)
        ]

    def remove_card(self, widget: ActionEditorWidget):
        """Retire une carte de la liste."""
        self.card_layout.removeWidget(widget)
        widget.deleteLater()
        self._update_empty_label()

    def clear(self):
        """Retire toutes les cartes."""
        for widget in self.get_cards():
            self.remove_card(widget)

    def _update_empty_label(self):
        """Affiche le message de liste vide si aucune carte n'est présente."""
        self.empty_label.setVisible(not self.get_cards())


def card_add_button(label: str, tooltip: str) -> "QPushButton":
    """Bouton d'ajout de carte, stylé comme dans les onglets existants."""
    from PySide6.QtWidgets import QPushButton

    btn = QPushButton(label)
    btn.setToolTip(tooltip)
    btn.setStyleSheet(
        SECONDARY_BUTTON_STYLE.replace(
            "min-height: 0px;", "min-height: 20px; padding: 6px 12px;"
        )
    )
    btn.setFixedHeight(36)
    return btn
