"""Onglet « Statistiques » : chiffres, caractéristiques, pills."""

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSpinBox, QWidget,
)

from src.ui.dnd_data import DND5_DAMAGE_TYPES, DND5_SKILLS
from src.ui.pill_editor import PillEditor
from src.ui.styles import ACCENT_BUTTON_STYLE


class StatsTab(QScrollArea):
    """Formulaire défilable des statistiques du monstre."""

    from PySide6.QtCore import Signal
    gen_stats_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        tab = QWidget()
        tab.setObjectName("statsTabContent")
        tab.setStyleSheet("""
            #statsTabContent {
                background: transparent;
                border: none;
            }
            #statsTabContent QWidget {
                background: transparent;
                border: none;
            }
            #statsTabContent QLineEdit, #statsTabContent QTextEdit,
            #statsTabContent QComboBox, #statsTabContent QSpinBox,
            #statsTabContent QDoubleSpinBox {
                background-color: #1e2632;
                color: #dce4ee;
                border: 1px solid #39485c;
                border-radius: 4px;
                padding: 6px;
                selection-background-color: #1e88e5;
                selection-color: #ffffff;
            }
            #statsTabContent QLineEdit:focus, #statsTabContent QTextEdit:focus,
            #statsTabContent QComboBox:focus, #statsTabContent QSpinBox:focus,
            #statsTabContent QDoubleSpinBox:focus {
                border: 1px solid #42a5f5;
                background-color: #1e2632;
            }
        """)
        layout = QFormLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.gen_stats_btn = QPushButton("Équilibrer les stats")
        self.gen_stats_btn.setIcon(QIcon.fromTheme("system-run"))
        self.gen_stats_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.gen_stats_btn.clicked.connect(self.gen_stats_requested.emit)
        layout.addRow(self.gen_stats_btn)

        self.ac_spin = QSpinBox()
        self.ac_spin.setRange(0, 50)
        self.ac_spin.setSpecialValueText("")
        layout.addRow("Classe d'Armure (CA) :", self.ac_spin)

        self.hp_spin = QSpinBox()
        self.hp_spin.setRange(0, 1000)
        self.hp_spin.setSpecialValueText("")
        layout.addRow("Points de Vie (PV) :", self.hp_spin)

        self.hit_dice_edit = QLineEdit()
        self.hit_dice_edit.setPlaceholderText("Ex: 3d8+6")
        layout.addRow("Dés de Vie :", self.hit_dice_edit)

        self.speed_edit = QLineEdit()
        self.speed_edit.setPlaceholderText("Ex: 30 pieds, vol 60 pieds")
        layout.addRow("Vitesse :", self.speed_edit)

        self.proficiency_spin = QSpinBox()
        self.proficiency_spin.setRange(0, 15)
        self.proficiency_spin.setSpecialValueText("")
        self.proficiency_spin.setToolTip(
            "Bonus de maîtrise (non affiché sur la fiche finale). "
            "Sert uniquement à calculer le bonus des compétences maîtrisées."
        )
        layout.addRow("Bonus de maîtrise :", self.proficiency_spin)

        layout.addRow(QLabel("Caractéristiques :"), QLabel(""))

        chars_layout = QHBoxLayout()
        self.str_spin = self._ability_spin(chars_layout, "FOR :")
        self.dex_spin = self._ability_spin(chars_layout, "DEX :")
        self.con_spin = self._ability_spin(chars_layout, "CON :")
        layout.addRow(chars_layout)

        chars_layout2 = QHBoxLayout()
        self.int_spin = self._ability_spin(chars_layout2, "INT :")
        self.wis_spin = self._ability_spin(chars_layout2, "SAG :")
        self.cha_spin = self._ability_spin(chars_layout2, "CHA :")
        layout.addRow(chars_layout2)

        self.skills_edit = PillEditor(suggestions=DND5_SKILLS,
                                      empty_text="Aucune compétence maîtrisée")
        layout.addRow("Compétences maîtrisées :", self.skills_edit)

        self.resistances_edit = PillEditor(suggestions=DND5_DAMAGE_TYPES,
                                           empty_text="Aucune résistance")
        layout.addRow("Résistances :", self.resistances_edit)

        self.immunities_edit = PillEditor(suggestions=DND5_DAMAGE_TYPES,
                                          empty_text="Aucune immunité")
        layout.addRow("Immunités :", self.immunities_edit)

        self.setWidget(tab)

    def _ability_spin(self, layout: QHBoxLayout, label: str) -> QSpinBox:
        """Crée un spinbox de caractéristique et l'ajoute à la ligne."""
        spin = QSpinBox()
        spin.setRange(0, 30)
        spin.setSpecialValueText("")
        layout.addWidget(QLabel(label))
        layout.addWidget(spin)
        return spin

    def ability_spins(self) -> dict:
        """Spinboxes de caractéristiques, dans l'ordre du modèle."""
        return {
            "strength": self.str_spin,
            "dexterity": self.dex_spin,
            "constitution": self.con_spin,
            "intelligence": self.int_spin,
            "wisdom": self.wis_spin,
            "charisma": self.cha_spin,
        }
