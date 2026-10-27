"""Panneau d'aperçu de la fiche (moitié droite de la fenêtre)."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from src.models.monster import AbilityScores, Monster
from src.rules.stat_builder import cr_display, cr_xp
from src.ui.styles import ACCENT_BUTTON_STYLE


class PreviewPanel(QWidget):
    """Aperçu en lecture seule de la fiche du monstre courant."""

    from PySide6.QtCore import Signal
    refresh_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        title_label = QLabel("Aperçu de la fiche")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.preview_content = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_content)
        self.preview_layout.setContentsMargins(10, 10, 10, 10)
        self.preview_layout.setSpacing(10)

        scroll_area.setWidget(self.preview_content)
        layout.addWidget(scroll_area, stretch=1)

        refresh_btn = QPushButton("Rafraîchir l'aperçu")
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(refresh_btn)

    def _add_section_title(self, title: str):
        """Ajoute un titre de section à l'aperçu."""
        label = QLabel(f"<b>{title}</b>")
        self.preview_layout.addWidget(label)

    def _add_preview_label(self, text: str, bold: bool = False, word_wrap: bool = False):
        """Ajoute un label à l'aperçu avec des options de style."""
        label = QLabel(text)
        if bold:
            label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        if word_wrap:
            label.setWordWrap(True)
        self.preview_layout.addWidget(label)

    def _format_ability_scores(self, scores: AbilityScores) -> str:
        """Formate les caractéristiques avec leurs modificateurs."""
        attrs = [
            ("FOR", scores.strength),
            ("DEX", scores.dexterity),
            ("CON", scores.constitution),
            ("INT", scores.intelligence),
            ("SAG", scores.wisdom),
            ("CHA", scores.charisma),
        ]
        parts = []
        for name, score in attrs:
            mod = (score - 10) // 2
            parts.append(f"{name} {score} ({mod:+d})")
        return ", ".join(parts)

    def clear_preview(self):
        """Efface l'aperçu actuel (widgets et items de layout)."""
        for i in reversed(range(self.preview_layout.count())):
            item = self.preview_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                self.preview_layout.takeAt(i)

    def update_preview(self, monster: Monster):
        """Met à jour l'aperçu avec les données du monstre donné."""
        self.clear_preview()

        if monster.name:
            self._add_preview_label(f"<b>{monster.name}</b>", bold=True)

        if monster.race:
            self._add_preview_label(f"<b>Race :</b> {monster.race}")
        if monster.languages:
            self._add_preview_label(f"<b>Langues :</b> {', '.join(monster.languages)}")

        if monster.armor_class:
            self._add_preview_label(f"<b>CA :</b> {monster.armor_class}")
        if monster.hit_points:
            self._add_preview_label(
                f"<b>PV :</b> {monster.hit_points} ({monster.hit_dice or '—'})"
            )
        if monster.speed:
            self._add_preview_label(f"<b>Vitesse :</b> {monster.speed}")
        if monster.challenge_rating:
            self._add_preview_label(
                f"<b>CR :</b> {cr_display(monster.challenge_rating)} "
                f"({cr_xp(monster.challenge_rating)} PX)"
            )

        scores = monster.ability_scores
        has_non_default = any(v != 10 for v in [
            scores.strength, scores.dexterity, scores.constitution,
            scores.intelligence, scores.wisdom, scores.charisma
        ])
        if has_non_default:
            self._add_section_title("Caractéristiques :")
            self._add_preview_label(self._format_ability_scores(scores))

        proficient_skills = [sk for sk in monster.skills if sk.proficiency]
        if proficient_skills:
            skill_parts = [
                f"{sk.name} {monster.skill_modifier(sk):+d}"
                for sk in proficient_skills
            ]
            self._add_preview_label(
                f"<b>Compétences maîtrisées :</b> {', '.join(skill_parts)}"
            )

        if monster.damage_resistances:
            self._add_preview_label(
                f"<b>Résistances :</b> {', '.join(monster.damage_resistances)}"
            )
        if monster.damage_immunities:
            self._add_preview_label(
                f"<b>Immunités :</b> {', '.join(monster.damage_immunities)}"
            )

        if monster.description:
            self._add_section_title("Description :")
            self._add_preview_label(monster.description, word_wrap=True)

        if monster.actions:
            self._add_section_title("Actions :")
            for action in monster.actions:
                self._add_preview_label(f"• {action.name}", word_wrap=True)
                if action.description:
                    self._add_preview_label(f"  {action.description}", word_wrap=True)

        if monster.scenario:
            self._add_section_title("Scénario :")
            self._add_preview_label(monster.scenario, word_wrap=True)

        if monster.notes:
            self._add_section_title("Équipement :")
            self._add_preview_label(monster.notes)

        self.preview_layout.addStretch()
