"""Dialogue d'édition d'une fiche de monstre (mode Rencontre).

Édition pure : pas de génération IA, pas de persistance automatique.
Le MJ passe la fiche en revue, la modifie, puis choisit :
- « Valider » : modifications appliquées à l'objet en mémoire ;
- « Intégrer dans la bibliothèque » : sauvegarde en bibliothèque
  (géré par l'appelant via la valeur de retour).
"""

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QWidget,
)

from src.models.monster import Action
from src.rules.stat_builder import cr_display, parse_cr


class MonsterEditDialog(QDialog):
    """Édition manuelle d'une fiche Monster (stats + actions)."""

    def __init__(self, monster, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Fiche — {monster.name or 'sans nom'}")
        self.setMinimumSize(520, 560)
        self._monster = monster
        self.integrate_requested = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        form = QFormLayout()
        form.setSpacing(6)

        self.name_edit = QLineEdit(monster.name)
        form.addRow("Nom :", self.name_edit)

        self.race_edit = QLineEdit(monster.race or "")
        form.addRow("Race / type :", self.race_edit)

        self.ac_spin = QSpinBox()
        self.ac_spin.setRange(0, 40)
        self.ac_spin.setValue(monster.armor_class or 10)
        form.addRow("Classe d'armure :", self.ac_spin)

        self.hp_spin = QSpinBox()
        self.hp_spin.setRange(1, 999)
        self.hp_spin.setValue(monster.hit_points or 1)
        form.addRow("Points de vie :", self.hp_spin)

        self.hit_dice_edit = QLineEdit(monster.hit_dice or "")
        form.addRow("Dés de vie :", self.hit_dice_edit)

        self.speed_edit = QLineEdit(monster.speed or "")
        form.addRow("Vitesse :", self.speed_edit)

        self.cr_edit = QLineEdit(cr_display(monster.challenge_rating))
        self.cr_edit.setToolTip("CR éditable (ex. 1/4, 2)")
        form.addRow("CR :", self.cr_edit)

        self.prof_spin = QSpinBox()
        self.prof_spin.setRange(0, 15)
        self.prof_spin.setValue(monster.proficiency_bonus or 2)
        form.addRow("Bonus de maîtrise :", self.prof_spin)
        layout.addLayout(form)

        abilities_label = QLabel("Caractéristiques")
        abilities_label.setStyleSheet("color: #90caf9; font-weight: bold;")
        layout.addWidget(abilities_label)

        ability_layout = QHBoxLayout()
        ability_layout.setSpacing(6)
        self._ability_spins = {}
        labels = {
            "strength": "FOR", "dexterity": "DEX", "constitution": "CON",
            "intelligence": "INT", "wisdom": "SAG", "charisma": "CHA",
        }
        for key, short in labels.items():
            box = QSpinBox()
            box.setRange(1, 30)
            box.setValue(getattr(monster.ability_scores, key))
            self._ability_spins[key] = box
            wrap = QVBoxLayout()
            wrap.addWidget(QLabel(short))
            wrap.addWidget(box)
            container = QWidget()
            container.setLayout(wrap)
            ability_layout.addWidget(container)
        layout.addLayout(ability_layout)

        desc_label = QLabel("Description")
        desc_label.setStyleSheet("color: #90caf9; font-weight: bold;")
        layout.addWidget(desc_label)
        self.description_edit = QTextEdit()
        self.description_edit.setPlainText(monster.description or "")
        layout.addWidget(self.description_edit, stretch=1)

        actions_label = QLabel("Actions")
        actions_label.setStyleSheet("color: #90caf9; font-weight: bold;")
        layout.addWidget(actions_label)

        self._action_rows = []
        self._actions_widget = QWidget()
        self._actions_layout = QVBoxLayout(self._actions_widget)
        self._actions_layout.setContentsMargins(0, 0, 0, 0)
        self._actions_layout.setSpacing(4)
        layout.addWidget(self._actions_widget)

        add_action_btn = QPushButton("＋ Ajouter une action")
        add_action_btn.clicked.connect(lambda: self._add_action_row(Action("")))
        layout.addWidget(add_action_btn)

        for action in monster.actions:
            self._add_action_row(action)

        buttons = QHBoxLayout()
        buttons.addStretch()
        integrate_btn = QPushButton("💾 Intégrer dans la bibliothèque")
        integrate_btn.setToolTip(
            "Sauvegarde la fiche dans la bibliothèque de monstres"
        )
        integrate_btn.clicked.connect(self._integrate)
        buttons.addWidget(integrate_btn)
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        buttons.addWidget(button_box)
        layout.addLayout(buttons)

    def _add_action_row(self, action: Action):
        """Une ligne d'action : nom, dégâts, description, suppression."""
        row = QHBoxLayout()
        row.setSpacing(4)

        name_edit = QLineEdit(action.name)
        name_edit.setPlaceholderText("Nom de l'action")
        damage_edit = QLineEdit(action.damage or "")
        damage_edit.setPlaceholderText("Dégâts (ex. 1d6+2)")
        damage_edit.setMaximumWidth(110)
        description_edit = QLineEdit(action.description or "")
        description_edit.setPlaceholderText("Description")

        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(24, 22)
        remove_btn.setStyleSheet(
            "QPushButton { color: #ff8888; border: none; "
            "background: transparent; font-size: 11px; }"
        )
        remove_btn.setToolTip("Supprimer cette action")
        row_data = [name_edit, damage_edit, description_edit, row]
        remove_btn.clicked.connect(lambda: self._remove_action_row(row_data))

        row.addWidget(name_edit, stretch=2)
        row.addWidget(damage_edit)
        row.addWidget(description_edit, stretch=3)
        row.addWidget(remove_btn)
        self._actions_layout.addLayout(row)
        self._action_rows.append(row_data)

    def _remove_action_row(self, row_data):
        for widget in row_data[:3]:
            widget.deleteLater()
        if row_data in self._action_rows:
            self._action_rows.remove(row_data)
        layout = row_data[3]
        if layout is not None:
            index = self._actions_layout.indexOf(layout)
            if index >= 0:
                self._actions_layout.takeAt(index)
        row_data[3] = None

    def _integrate(self):
        self.integrate_requested = True
        self.accept()

    def apply_to_monster(self, monster):
        """Reporte les saisies sur le Monster fourni."""
        monster.name = self.name_edit.text().strip() or monster.name
        monster.race = self.race_edit.text().strip()
        monster.armor_class = self.ac_spin.value()
        monster.hit_points = self.hp_spin.value()
        monster.hit_dice = self.hit_dice_edit.text().strip() or None
        monster.speed = self.speed_edit.text().strip() or None
        cr = parse_cr(self.cr_edit.text())
        if cr is not None:
            monster.challenge_rating = cr
        monster.proficiency_bonus = self.prof_spin.value()
        for key, spin in self._ability_spins.items():
            setattr(monster.ability_scores, key, spin.value())
        monster.description = self.description_edit.toPlainText().strip()
        monster.actions = [
            Action(
                name=row[0].text().strip(),
                description=row[2].text().strip(),
                damage=row[1].text().strip() or None,
            )
            for row in self._action_rows
            if row[0].text().strip() or row[2].text().strip()
        ]
        return monster
