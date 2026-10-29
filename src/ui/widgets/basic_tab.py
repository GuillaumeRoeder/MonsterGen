"""Onglet « Description » : identité, langues, scénario, équipement."""

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton,
    QFormLayout, QTextEdit, QVBoxLayout, QWidget,
)

from src.ui.dnd_data import DND5_RACES
from src.ui.styles import ACCENT_BUTTON_STYLE, SECONDARY_BUTTON_STYLE
from src.ui.languages_editor import LanguagesEditor
from src.ui.widgets.collapsible_header import CollapsibleHeader
from src.ui.widgets.party_widget import PartyWidget


class BasicTab(QWidget):
    """Formulaire d'identité du monstre + section scénario repliable.

    Émet « changed » dès qu'un champ modifiable affecte l'aperçu.
    """

    from PySide6.QtCore import Signal
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.party = PartyWidget()
        layout.addRow("Groupe :", self.party)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(
            "color: #3e5a8a; background: #3e5a8a; border: none; max-height: 1px;"
        )
        layout.addRow(separator)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nom du PNJ/Monstre")
        self.name_edit.textChanged.connect(lambda: self.changed.emit())
        layout.addRow("Nom :", self.name_edit)

        race_layout = QHBoxLayout()
        race_layout.setSpacing(4)
        self.race_edit = QLineEdit()
        self.race_edit.setPlaceholderText("Race ou type de créature")
        self.race_edit.textChanged.connect(lambda: self.changed.emit())
        race_layout.addWidget(self.race_edit, stretch=1)

        self.race_menu_btn = QPushButton("▾")
        self.race_menu_btn.setFixedSize(24, 24)
        self.race_menu_btn.setToolTip("Choisir une race DnD 5e")
        self.race_menu_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self.race_menu_btn.clicked.connect(self._show_race_menu)
        race_layout.addWidget(self.race_menu_btn)

        layout.addRow("Race :", race_layout)

        self.languages_edit = LanguagesEditor()
        self.languages_edit.valuesChanged.connect(lambda: self.changed.emit())
        languages_frame = QFrame()
        languages_frame.setFrameShape(QFrame.Shape.StyledPanel)
        languages_frame.setStyleSheet("""
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
        languages_layout = QVBoxLayout(languages_frame)
        languages_layout.setContentsMargins(8, 6, 8, 8)
        languages_layout.setSpacing(6)

        languages_header = QLabel(
            "Langues parlées — cliquez sur ▾ puis + pour ajouter une langue, "
            "✕ pour la retirer :"
        )
        languages_header.setStyleSheet(
            "color: #90caf9; font-size: 11px; background: transparent; border: none;"
        )
        languages_layout.addWidget(languages_header)
        languages_layout.addWidget(self.languages_edit)

        layout.addRow("Langues :", languages_frame)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Description du PNJ/Monstre")
        self.description_edit.setMaximumHeight(100)
        self.description_edit.textChanged.connect(lambda: self.changed.emit())
        layout.addRow("Description :", self.description_edit)

        layout.addRow(self._create_scenario_section())

    def _create_scenario_section(self) -> QWidget:
        """Crée la section scénario repliable (façon Attribute Editor Maya)."""
        scenario_widget = QWidget()
        scenario_widget.setStyleSheet("background: transparent; border: none;")
        scenario_vlayout = QVBoxLayout(scenario_widget)
        scenario_vlayout.setContentsMargins(0, 0, 0, 0)
        scenario_vlayout.setSpacing(0)

        self._scenario_expanded = False
        self.scenario_toggle_header = CollapsibleHeader(
            "Scénario de rencontre (optionnel)"
        )
        self.scenario_toggle_header.setToolTip(
            "Cliquer pour déplier ou replier la section scénario"
        )
        self.scenario_toggle_header.clicked.connect(self._toggle_scenario)
        scenario_vlayout.addWidget(self.scenario_toggle_header)

        self.scenario_content = QWidget()
        self.scenario_content.setStyleSheet("""
            QWidget {
                background-color: #161f2a;
                border: 1px solid #3e5a8a;
                border-top: none;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
            }
        """)
        scenario_inner = QVBoxLayout(self.scenario_content)
        scenario_inner.setContentsMargins(8, 6, 8, 8)
        scenario_inner.setSpacing(6)

        scenario_header = QLabel(
            "Décrivez le contexte de la rencontre, ou générez-le "
            "automatiquement à partir des stats actuelles du monstre :"
        )
        scenario_header.setStyleSheet(
            "color: #90caf9; font-size: 11px; background: transparent; border: none;"
        )
        scenario_inner.addWidget(scenario_header)

        self.scenario_edit = QTextEdit()
        self.scenario_edit.setPlaceholderText(
            "Scénario de rencontre (lieu, circonstances, motivation du monstre...)"
        )
        self.scenario_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e2632;
                color: #dce4ee;
                border: 1px solid #39485c;
                border-radius: 4px;
                font-size: 11px;
            }
        """)
        scenario_inner.addWidget(self.scenario_edit)

        self.gen_scenario_btn = QPushButton("Générer le scénario")
        self.gen_scenario_btn.setIcon(QIcon.fromTheme("system-run"))
        self.gen_scenario_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        scenario_inner.addWidget(self.gen_scenario_btn)
        scenario_vlayout.addWidget(self.scenario_content)

        self._apply_scenario_toggle_state()
        return scenario_widget

    def _toggle_scenario(self):
        """Affiche ou masque la section scénario."""
        self._scenario_expanded = not self._scenario_expanded
        self._apply_scenario_toggle_state()

    def _apply_scenario_toggle_state(self):
        """Applique l'état replié/déplié de la section scénario."""
        self.scenario_content.setVisible(self._scenario_expanded)
        self.scenario_toggle_header.set_expanded(self._scenario_expanded)

    def _show_race_menu(self):
        """Affiche le menu déroulant des races DnD 5e sous la flèche."""
        menu = QMenu(self)
        for race in DND5_RACES:
            action = menu.addAction(race)
            action.triggered.connect(
                lambda *args, r=race: self.race_edit.setText(r)
            )
        btn_pos = self.race_menu_btn.mapToGlobal(self.race_menu_btn.rect().bottomLeft())
        menu.exec(btn_pos)
