"""Ligne « groupe de joueurs + difficulté » (onglet Description)."""

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout

from src.rules.encounter import DIFFICULTIES, DIFFICULTY_COLORS, difficulty_summary


class PartyWidget(QVBoxLayout):
    """Saisie du groupe (joueurs, niveau, difficulté) + label coloré du CR."""

    def __init__(self):
        super().__init__()
        self.setSpacing(2)

        party_layout = QHBoxLayout()
        party_layout.setSpacing(6)

        self.party_size_spin = QSpinBox()
        self.party_size_spin.setRange(1, 10)
        self.party_size_spin.setValue(4)
        party_layout.addWidget(QLabel("Joueurs :"))
        party_layout.addWidget(self.party_size_spin)

        self.party_level_spin = QSpinBox()
        self.party_level_spin.setRange(1, 20)
        self.party_level_spin.setValue(2)
        party_layout.addWidget(QLabel("Niveau moyen :"))
        party_layout.addWidget(self.party_level_spin)

        self.difficulty_combo = QComboBox()
        for key, label in DIFFICULTIES:
            self.difficulty_combo.addItem(label, key)
        self.difficulty_combo.setCurrentIndex(1)
        party_layout.addWidget(QLabel("Difficulté :"))
        party_layout.addWidget(self.difficulty_combo)

        self.difficulty_result_label = QLabel("")
        self.difficulty_result_label.setStyleSheet(
            "font-weight: bold; margin-top: -4px; margin-bottom: -4px;"
        )

        self.party_size_spin.valueChanged.connect(self.update_difficulty_label)
        self.party_level_spin.valueChanged.connect(self.update_difficulty_label)
        self.difficulty_combo.currentIndexChanged.connect(self.update_difficulty_label)

        self.addLayout(party_layout)
        self.addWidget(self.difficulty_result_label)
        self.update_difficulty_label()

    def selected_difficulty(self) -> str:
        """Clé de difficulté sélectionnée."""
        return self.difficulty_combo.currentData() or "medium"

    def update_difficulty_label(self):
        """Met à jour le label coloré de la difficulté résultante."""
        difficulty_key = self.selected_difficulty()
        summary = difficulty_summary(
            self.party_size_spin.value(),
            self.party_level_spin.value(),
            difficulty_key,
        )
        color = DIFFICULTY_COLORS.get(difficulty_key, "#e0e0e0")
        self.difficulty_result_label.setText(f"● {summary}")
        self.difficulty_result_label.setStyleSheet(
            f"font-weight: bold; color: {color}; "
            "margin-top: -4px; margin-bottom: -4px;"
        )

    def set_party(self, party_size, party_level, difficulty):
        """Applique les valeurs de groupe d'un monstre chargé."""
        if party_size is not None:
            self.party_size_spin.setValue(party_size)
        if party_level is not None:
            self.party_level_spin.setValue(party_level)
        if difficulty:
            index = self.difficulty_combo.findData(difficulty)
            if index >= 0:
                self.difficulty_combo.setCurrentIndex(index)
        self.update_difficulty_label()

    def reset(self):
        """Réinitialise aux valeurs par défaut."""
        self.party_size_spin.setValue(4)
        self.party_level_spin.setValue(2)
        self.difficulty_combo.setCurrentIndex(1)
        self.update_difficulty_label()
