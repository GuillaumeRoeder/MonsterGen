"""
Fenêtre principale de l'application MonsterGen.
"""

import sys
from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton, QSpinBox, QDoubleSpinBox,
    QGroupBox, QFormLayout, QMessageBox, QFileDialog, QTabWidget,
    QScrollArea, QListWidget, QListWidgetItem, QInputDialog
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QIcon

from src.models.monster import Monster, Alignment, Size, AbilityScores, Action, Skill
from src.ai.ai_generator import ai_generator
from src.export.pdf_exporter import pdf_exporter
from config.config_manager import config_manager


class SignalEmitter(QObject):
    """Émetteur de signaux pour la communication entre threads."""
    update_status = Signal(str)
    show_options = Signal(str, List[str])
    generation_complete = Signal(Monster)


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MonsterGen - Générateur de fiches DnD 5e")
        self.setGeometry(100, 100, 900, 700)

        self.monster = Monster()
        self.signal_emitter = SignalEmitter()
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.form_panel = self.create_form_panel()
        main_layout.addWidget(self.form_panel, stretch=1)

        self.preview_panel = self.create_preview_panel()
        main_layout.addWidget(self.preview_panel, stretch=1)

    def create_form_panel(self) -> QWidget:
        """Crée le panneau de formulaire."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        tab_widget = QTabWidget()

        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "Informations de base")

        stats_tab = self.create_stats_tab()
        tab_widget.addTab(stats_tab, "Statistiques")

        actions_tab = self.create_actions_tab()
        tab_widget.addTab(actions_tab, "Actions et Équipement")

        layout.addWidget(tab_widget)

        control_layout = QHBoxLayout()

        self.generate_btn = QPushButton("Générer les champs manquants")
        self.generate_btn.setIcon(QIcon.fromTheme("system-run"))
        control_layout.addWidget(self.generate_btn)

        self.export_btn = QPushButton("Exporter en PDF")
        self.export_btn.setIcon(QIcon.fromTheme("document-export"))
        control_layout.addWidget(self.export_btn)

        self.save_btn = QPushButton("Sauvegarder")
        self.save_btn.setIcon(QIcon.fromTheme("document-save"))
        control_layout.addWidget(self.save_btn)

        self.load_btn = QPushButton("Charger")
        self.load_btn.setIcon(QIcon.fromTheme("document-open"))
        control_layout.addWidget(self.load_btn)

        layout.addLayout(control_layout)

        return panel

    def create_basic_tab(self) -> QWidget:
        """Crée l'onglet des informations de base."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nom du PNJ/Monstre")
        layout.addRow("Nom :", self.name_edit)

        self.race_edit = QLineEdit()
        self.race_edit.setPlaceholderText("Race ou type de créature")
        layout.addRow("Race :", self.race_edit)

        self.languages_edit = QTextEdit()
        self.languages_edit.setPlaceholderText("Ex: commun, elfique, nain")
        self.languages_edit.setMaximumHeight(60)
        layout.addRow("Langues :", self.languages_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Description du PNJ/Monstre")
        self.description_edit.setMaximumHeight(100)
        layout.addRow("Description :", self.description_edit)

        gen_scenario_btn = QPushButton("Générer un scénario")
        gen_scenario_btn.setIcon(QIcon.fromTheme("system-run"))
        gen_scenario_btn.clicked.connect(self._generate_scenario)
        layout.addRow(gen_scenario_btn)

        return tab

    def create_stats_tab(self) -> QWidget:
        """Crée l'onglet des statistiques."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

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

        self.cr_spin = QDoubleSpinBox()
        self.cr_spin.setRange(0, 30)
        self.cr_spin.setDecimals(1)
        self.cr_spin.setSingleStep(0.5)
        self.cr_spin.setSpecialValueText("")
        layout.addRow("Défi (CR) :", self.cr_spin)

        layout.addRow(QLabel("Caractéristiques :"), QLabel(""))

        chars_layout = QHBoxLayout()

        self.str_spin = QSpinBox()
        self.str_spin.setRange(0, 30)
        self.str_spin.setSpecialValueText("")
        chars_layout.addWidget(QLabel("FOR :"))
        chars_layout.addWidget(self.str_spin)

        self.dex_spin = QSpinBox()
        self.dex_spin.setRange(0, 30)
        self.dex_spin.setSpecialValueText("")
        chars_layout.addWidget(QLabel("DEX :"))
        chars_layout.addWidget(self.dex_spin)

        self.con_spin = QSpinBox()
        self.con_spin.setRange(0, 30)
        self.con_spin.setSpecialValueText("")
        chars_layout.addWidget(QLabel("CON :"))
        chars_layout.addWidget(self.con_spin)

        layout.addRow(chars_layout)

        chars_layout2 = QHBoxLayout()

        self.int_spin = QSpinBox()
        self.int_spin.setRange(0, 30)
        self.int_spin.setSpecialValueText("")
        chars_layout2.addWidget(QLabel("INT :"))
        chars_layout2.addWidget(self.int_spin)

        self.wis_spin = QSpinBox()
        self.wis_spin.setRange(0, 30)
        self.wis_spin.setSpecialValueText("")
        chars_layout2.addWidget(QLabel("SAG :"))
        chars_layout2.addWidget(self.wis_spin)

        self.cha_spin = QSpinBox()
        self.cha_spin.setRange(0, 30)
        self.cha_spin.setSpecialValueText("")
        chars_layout2.addWidget(QLabel("CHA :"))
        chars_layout2.addWidget(self.cha_spin)

        layout.addRow(chars_layout2)

        gen_stats_btn = QPushButton("Générer les caractéristiques")
        gen_stats_btn.setIcon(QIcon.fromTheme("system-run"))
        gen_stats_btn.clicked.connect(self._generate_ability_scores)
        layout.addRow(gen_stats_btn)

        layout.addRow(QLabel("Compétences maîtrisées :"), QLabel(""))
        self.skills_edit = QTextEdit()
        self.skills_edit.setPlaceholderText("Ex: Athlétisme, Perspicacité, Persuasion")
        self.skills_edit.setMaximumHeight(60)
        layout.addRow("", self.skills_edit)

        return tab

    def create_actions_tab(self) -> QWidget:
        """Crée l'onglet des actions et équipements."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Actions :"))

        gen_actions_btn = QPushButton("Générer des actions")
        gen_actions_btn.setIcon(QIcon.fromTheme("system-run"))
        gen_actions_btn.clicked.connect(self._generate_actions)
        layout.addWidget(gen_actions_btn)

        self.actions_list = QListWidget()
        self.actions_list.setMinimumHeight(150)
        layout.addWidget(self.actions_list)

        actions_control_layout = QHBoxLayout()

        self.add_action_btn = QPushButton("Ajouter une action")
        self.add_action_btn.setIcon(QIcon.fromTheme("list-add"))
        actions_control_layout.addWidget(self.add_action_btn)

        self.edit_action_btn = QPushButton("Modifier l'action")
        self.edit_action_btn.setIcon(QIcon.fromTheme("document-edit"))
        actions_control_layout.addWidget(self.edit_action_btn)

        self.remove_action_btn = QPushButton("Supprimer l'action")
        self.remove_action_btn.setIcon(QIcon.fromTheme("list-remove"))
        actions_control_layout.addWidget(self.remove_action_btn)

        layout.addLayout(actions_control_layout)

        layout.addWidget(QLabel("Équipement/Armements :"))
        self.equipment_edit = QTextEdit()
        self.equipment_edit.setPlaceholderText("Ex: Épée longue, Arc court, Armure de cuir")
        self.equipment_edit.setMinimumHeight(80)
        layout.addWidget(self.equipment_edit)

        return tab

    def create_preview_panel(self) -> QWidget:
        """Crée le panneau d'aperçu."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
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
        refresh_btn.clicked.connect(self.refresh_preview)
        layout.addWidget(refresh_btn)

        return panel

    def setup_connections(self):
        """Configure les connexions des signaux."""
        self.generate_btn.clicked.connect(self.generate_missing_fields)
        self.export_btn.clicked.connect(self.export_to_pdf)
        self.save_btn.clicked.connect(self.save_monster)
        self.load_btn.clicked.connect(self.load_monster)

        self.add_action_btn.clicked.connect(self.add_action)
        self.edit_action_btn.clicked.connect(self.edit_action)
        self.remove_action_btn.clicked.connect(self.remove_action)

        self.signal_emitter.show_options.connect(self.show_options_dialog)
        self.signal_emitter.generation_complete.connect(self.on_generation_complete)

    def refresh_preview(self):
        """Rafraîchit l'aperçu de la fiche."""
        self.update_preview()

    def _add_section_title(self, title: str):
        """Ajoute un titre de section à l'aperçu."""
        label = QLabel(f"<b>{title}</b>")
        self.preview_layout.addWidget(label)
        return label

    def _add_preview_label(self, text: str, bold: bool = False, word_wrap: bool = False):
        """Ajoute un label à l'aperçu avec des options de style."""
        label = QLabel(text)
        if bold:
            label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        if word_wrap:
            label.setWordWrap(True)
        self.preview_layout.addWidget(label)
        return label

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
            mod = self._get_modifier(score)
            parts.append(f"{name} {score} ({mod:+d})")
        return ", ".join(parts)

    def _clear_preview(self):
        """Efface l'aperçu actuel."""
        for i in reversed(range(self.preview_layout.count())):
            widget = self.preview_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def _get_modifier(self, score: int) -> int:
        """Calcule le modificateur pour une caractéristique."""
        return (score - 10) // 2

    def update_preview(self):
        """Met à jour l'aperçu avec les données actuelles."""
        self._clear_preview()
        monster = self.get_monster_from_form()

        if monster.name:
            self._add_preview_label(f"<b>{monster.name}</b>", bold=True)

        if monster.race:
            self._add_preview_label(f"<b>Race :</b> {monster.race}")
        if monster.languages:
            self._add_preview_label(f"<b>Langues :</b> {', '.join(monster.languages)}")

        if monster.armor_class:
            self._add_preview_label(f"<b>CA :</b> {monster.armor_class}")
        if monster.hit_points:
            self._add_preview_label(f"<b>PV :</b> {monster.hit_points} ({monster.hit_dice or '\u2014'})")
        if monster.speed:
            self._add_preview_label(f"<b>Vitesse :</b> {monster.speed}")
        if monster.challenge_rating:
            self._add_preview_label(f"<b>CR :</b> {monster.challenge_rating:.1f}")

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
            skill_names = [sk.name for sk in proficient_skills]
            self._add_preview_label(f"<b>Compétences maîtrisées :</b> {', '.join(skill_names)}")

        if monster.description:
            self._add_section_title("Description :")
            self._add_preview_label(monster.description, word_wrap=True)

        if monster.actions:
            self._add_section_title("Actions :")
            for action in monster.actions:
                self._add_preview_label(f"• {action.name}: {action.description}")

        if monster.notes:
            self._add_section_title("Équipement :")
            self._add_preview_label(monster.notes)

        self.preview_layout.addStretch()

    def get_monster_from_form(self) -> Monster:
        """Récupère les données du monstre depuis le formulaire."""
        monster = Monster()

        monster.name = self.name_edit.text().strip() or None
        monster.race = self.race_edit.text().strip() or None
        monster.description = self.description_edit.toPlainText().strip() or None

        languages_text = self.languages_edit.toPlainText().strip()
        if languages_text:
            monster.languages = [l.strip() for l in languages_text.split(",") if l.strip()]

        monster.armor_class = self.ac_spin.value() if self.ac_spin.value() > 0 else None
        monster.hit_points = self.hp_spin.value() if self.hp_spin.value() > 0 else None
        monster.hit_dice = self.hit_dice_edit.text().strip() or None
        monster.speed = self.speed_edit.text().strip() or None
        monster.challenge_rating = self.cr_spin.value() if self.cr_spin.value() > 0 else None

        ability_map = {
            "strength": self.str_spin,
            "dexterity": self.dex_spin,
            "constitution": self.con_spin,
            "intelligence": self.int_spin,
            "wisdom": self.wis_spin,
            "charisma": self.cha_spin,
        }
        monster.ability_scores = AbilityScores(
            **{k: (w.value() if w.value() > 0 else 10) for k, w in ability_map.items()}
        )

        skills_text = self.skills_edit.toPlainText().strip()
        if skills_text:
            skill_names = [s.strip() for s in skills_text.split(",") if s.strip()]
            monster.skills = [Skill(name=name, ability="", proficiency=True) for name in skill_names]

        for i in range(self.actions_list.count()):
            item = self.actions_list.item(i)
            action_data = item.data(Qt.ItemDataRole.UserRole)
            if action_data:
                monster.actions.append(Action(**action_data))

        monster.notes = self.equipment_edit.toPlainText().strip() or None

        return monster

    def set_monster_to_form(self, monster: Monster):
        """Remplit le formulaire avec les données du monstre."""
        self.name_edit.setText(monster.name or "")
        self.race_edit.setText(monster.race or "")
        self.description_edit.setPlainText(monster.description or "")

        self.languages_edit.setPlainText(", ".join(monster.languages))

        self.ac_spin.setValue(monster.armor_class or 0)
        self.hp_spin.setValue(monster.hit_points or 0)
        self.hit_dice_edit.setText(monster.hit_dice or "")
        self.speed_edit.setText(monster.speed or "")
        self.cr_spin.setValue(monster.challenge_rating or 0)

        ability_map = {
            "strength": self.str_spin,
            "dexterity": self.dex_spin,
            "constitution": self.con_spin,
            "intelligence": self.int_spin,
            "wisdom": self.wis_spin,
            "charisma": self.cha_spin,
        }
        scores = monster.ability_scores
        for attr, widget in ability_map.items():
            widget.setValue(getattr(scores, attr))

        proficient_skills = [sk.name for sk in monster.skills if sk.proficiency]
        self.skills_edit.setPlainText(", ".join(proficient_skills))

        self.actions_list.clear()
        for action in monster.actions:
            self.add_action_to_list(self.actions_list, action)

        self.equipment_edit.setPlainText(monster.notes or "")

    def add_action_to_list(self, list_widget: QListWidget, action: Action):
        """Ajoute une action à une liste."""
        action_data = {
            "name": action.name,
            "description": action.description,
            "attack_bonus": action.attack_bonus,
            "damage": action.damage,
            "damage_type": action.damage_type
        }

        item = QListWidgetItem(action.name)
        item.setData(Qt.ItemDataRole.UserRole, action_data)
        list_widget.addItem(item)

    def add_action(self):
        """Ajoute une nouvelle action directement."""
        name, ok = QInputDialog.getText(self, "Ajouter une action", "Nom de l'action:")
        if not ok or not name:
            return

        description, ok = QInputDialog.getText(self, "Ajouter une action", "Description:")
        if not ok:
            return

        action = Action(name=name, description=description)
        self.add_action_to_list(self.actions_list, action)

    def edit_action(self):
        """Modifie une action existante."""
        selected = self.actions_list.currentItem()
        if not selected:
            return

        action_data = selected.data(Qt.ItemDataRole.UserRole)
        if not action_data:
            return

        name, ok = QInputDialog.getText(self, "Modifier l'action", "Nom:", text=action_data.get("name", ""))
        if not ok or not name:
            return

        description, ok = QInputDialog.getText(self, "Modifier l'action", "Description:", text=action_data.get("description", ""))
        if not ok:
            return

        new_action_data = {
            "name": name,
            "description": description,
            "attack_bonus": action_data.get("attack_bonus"),
            "damage": action_data.get("damage"),
            "damage_type": action_data.get("damage_type"),
        }
        selected.setText(name)
        selected.setData(Qt.ItemDataRole.UserRole, new_action_data)

    def remove_action(self):
        """Supprime une action."""
        selected = self.actions_list.currentItem()
        if selected:
            self.actions_list.takeItem(self.actions_list.row(selected))

    def _generate_ability_scores(self):
        """Génère les caractéristiques du monstre."""
        api_key = config_manager.get_api_key()
        if not api_key:
            QMessageBox.warning(
                self,
                "Clé API manquante",
                "Veuillez configurer votre clé API dans les paramètres avant de générer."
            )
            return

        ai_generator.reload_config()
        monster = self.get_monster_from_form()

        try:
            options = ai_generator.generate_options(monster, "ability_scores")
            if options:
                scores_str = options[0]
                parts = scores_str.replace('"', '').strip().split(',')
                if len(parts) == 6:
                    self.str_spin.setValue(int(parts[0].strip()))
                    self.dex_spin.setValue(int(parts[1].strip()))
                    self.con_spin.setValue(int(parts[2].strip()))
                    self.int_spin.setValue(int(parts[3].strip()))
                    self.wis_spin.setValue(int(parts[4].strip()))
                    self.cha_spin.setValue(int(parts[5].strip()))
                    self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération: {str(e)}")

    def _generate_actions(self):
        """Génère des actions pour le monstre."""
        api_key = config_manager.get_api_key()
        if not api_key:
            QMessageBox.warning(
                self,
                "Clé API manquante",
                "Veuillez configurer votre clé API dans les paramètres avant de générer."
            )
            return

        ai_generator.reload_config()
        monster = self.get_monster_from_form()

        try:
            options = ai_generator.generate_options(monster, "actions")
            if options:
                for action_name in options[:3]:
                    action = Action(name=action_name, description="")
                    self.add_action_to_list(self.actions_list, action)
                self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération: {str(e)}")

    def _generate_scenario(self):
        """Génère un scénario pour le monstre."""
        api_key = config_manager.get_api_key()
        if not api_key:
            QMessageBox.warning(
                self,
                "Clé API manquante",
                "Veuillez configurer votre clé API dans les paramètres avant de générer."
            )
            return

        ai_generator.reload_config()
        monster = self.get_monster_from_form()

        base_prompt = (
            "RÈGLE ABSOLUE: Réponds UNIQUEMENT avec un JSON valide: {\"options\": [\"scenario\"]}. "
            "Ne mets AUCUN commentaire, AUCUNE explication, AUCUN texte supplémentaire. "
            "Contexte: Fiche de PNJ/Monstre pour DnD 5e. "
            "Nom={}, Race={}, CA={}, PV={}. "
            "Génère un scénario court (3-5 phrases) pour une rencontre avec ce monstre. "
            "Décris le contexte, l'environnement et un objectif possible."
        )

        prompt = base_prompt.format(
            monster.name or 'None',
            monster.race or 'None',
            monster.armor_class or 'None',
            monster.hit_points or 'None'
        )

        try:
            import requests
            import json as json_module
            import re as re_module

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": ai_generator.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 200,
            }

            response = requests.post(
                ai_generator.endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                resp_content = result["choices"][0]["message"]["content"].strip()

                json_match = re_module.search(r'\{.*\}', resp_content, re_module.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    json_str = json_str.replace('```json', '').replace('```', '').strip()
                    json_str = re_module.sub(r'//.*', '', json_str)
                    data = json_module.loads(json_str)
                    if "options" in data and len(data["options"]) > 0:
                        scenario = data["options"][0]
                        current_desc = self.description_edit.toPlainText().strip()
                        separator = "\n\n" if current_desc else ""
                        new_desc = f"{current_desc}{separator}Scénario:\n{scenario}"
                        self.description_edit.setPlainText(new_desc)
                        self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération: {str(e)}")

    def generate_missing_fields(self):
        """Génère les champs manquants avec l'IA."""
        api_key = config_manager.get_api_key()
        if not api_key:
            QMessageBox.warning(
                self,
                "Clé API manquante",
                "Veuillez configurer votre clé API dans les paramètres avant de générer des champs."
            )
            return

        ai_generator.reload_config()
        monster = self.get_monster_from_form()

        missing_fields = []
        if not monster.name:
            missing_fields.append("name")
        if not monster.race:
            missing_fields.append("race")
        if not monster.description:
            missing_fields.append("description")
        if not monster.armor_class:
            missing_fields.append("armor_class")
        if not monster.hit_points:
            missing_fields.append("hit_points")
        if not monster.hit_dice:
            missing_fields.append("hit_dice")
        if not monster.speed:
            missing_fields.append("speed")
        if not monster.challenge_rating:
            missing_fields.append("challenge_rating")
        if not monster.languages:
            missing_fields.append("languages")

        scores = monster.ability_scores
        if (scores.strength == 10 and scores.dexterity == 10 and scores.constitution == 10 and
           scores.intelligence == 10 and scores.wisdom == 10 and scores.charisma == 10):
            missing_fields.append("ability_scores")

        if not missing_fields:
            QMessageBox.information(
                self,
                "Aucun champ manquant",
                "Tous les champs principaux sont déjà remplis."
            )
            return

        all_options = {}
        error_messages = []
        for field in missing_fields:
            try:
                options = ai_generator.generate_options(monster, field)
                if options:
                    all_options[field] = options
            except Exception as e:
                error_messages.append(f"{field}: {str(e)}")
                continue

        if all_options:
            self.show_all_options_dialog(all_options)
        elif error_messages:
            QMessageBox.critical(
                self,
                "Erreurs de génération",
                "Impossible de générer des options:\n\n" + "\n".join(error_messages)
            )

    def show_options_dialog(self, field_name: str, options: List[str]):
        """Affiche une boîte de dialogue pour sélectionner une option."""
        dialog = QMessageBox(self)
        dialog.setWindowTitle(f"Sélectionner {field_name}")

        if len(options) == 0:
            dialog.setText(f"Aucune option générée pour {field_name}.")
            dialog.exec()
            return

        display_options = options[:5]
        text = f"Sélectionnez une option pour {field_name} :\n\n"
        for i, option in enumerate(display_options, 1):
            text += f"{i}. {option}\n"

        dialog.setText(text)

        for i, option in enumerate(display_options):
            btn = dialog.addButton(f"Option {i+1}", QMessageBox.ButtonRole.ActionRole)
            btn.setData(option)

        custom_btn = dialog.addButton("Personnalisé", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = dialog.addButton(QMessageBox.StandardButton.Cancel)

        dialog.exec()

        clicked = dialog.clickedButton()

        if clicked == cancel_btn:
            return

        if clicked == custom_btn:
            custom_value, ok = QInputDialog.getText(
                self,
                f"Valeur personnalisée pour {field_name}",
                f"Entrez une valeur pour {field_name} :"
            )
            if ok and custom_value:
                self.set_field_value(field_name, custom_value)
        elif clicked and clicked != custom_btn:
            selected_option = clicked.data()
            if selected_option:
                self.set_field_value(field_name, str(selected_option))

    def show_all_options_dialog(self, all_options: Dict[str, List[str]]):
        """Affiche une boîte de dialogue unique pour tous les champs manquants."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Sélectionner les options générées")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        intro_label = QLabel("L'IA a généré des options pour les champs manquants.\nSélectionnez une option pour chaque champ :")
        layout.addWidget(intro_label)

        self.field_combos = {}
        for field_name, options in all_options.items():
            field_layout = QHBoxLayout()

            label = QLabel(f"{field_name}:")
            field_layout.addWidget(label)

            combo = QComboBox()
            combo.addItems(options)
            self.field_combos[field_name] = combo
            field_layout.addWidget(combo, stretch=1)

            layout.addLayout(field_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        apply_btn = QPushButton("Appliquer tout")
        apply_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(apply_btn)

        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            for field_name, combo in self.field_combos.items():
                selected_option = combo.currentText()
                if selected_option:
                    self.set_field_value(field_name, selected_option)

    def set_field_value(self, field_name: str, value: str):
        """Définit la valeur d'un champ dans le formulaire."""
        field_mapping = {
            "name": lambda v: self.name_edit.setText(v),
            "race": lambda v: self.race_edit.setText(v),
            "description": lambda v: self.description_edit.setPlainText(v),
            "hit_dice": lambda v: self.hit_dice_edit.setText(v),
            "speed": lambda v: self.speed_edit.setText(v),
            "languages": lambda v: self.languages_edit.setPlainText(v),
        }

        if field_name in field_mapping:
            field_mapping[field_name](value)
            return

        numeric_fields = {
            "armor_class": (self.ac_spin, int),
            "hit_points": (self.hp_spin, int),
            "challenge_rating": (self.cr_spin, float),
        }

        if field_name in numeric_fields:
            widget, converter = numeric_fields[field_name]
            try:
                widget.setValue(converter(value))
            except (ValueError, TypeError):
                pass
            return

        if field_name == "ability_scores":
            try:
                parts = value.replace('"', '').strip().split(',')
                if len(parts) == 6:
                    ability_map = {
                        0: self.str_spin,
                        1: self.dex_spin,
                        2: self.con_spin,
                        3: self.int_spin,
                        4: self.wis_spin,
                        5: self.cha_spin,
                    }
                    for idx, widget in ability_map.items():
                        widget.setValue(int(parts[idx].strip()))
            except Exception:
                pass

    def export_to_pdf(self):
        """Exporte le monstre en PDF."""
        monster = self.get_monster_from_form()

        if not monster.name:
            QMessageBox.warning(
                self,
                "Nom manquant",
                "Veuillez fournir un nom pour le PNJ/Monstre avant l'export."
            )
            return

        save_path = config_manager.get_save_path()
        default_filename = f"{monster.name.replace(' ', '_')}_fiche_DnD.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter en PDF",
            f"{save_path}/{default_filename}",
            "Fichiers PDF (*.pdf)"
        )

        if not file_path:
            return

        try:
            pdf_exporter.export_to_pdf(monster, file_path)
            QMessageBox.information(
                self,
                "Export réussi",
                f"La fiche a été exportée avec succès vers :\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur d'export",
                f"Erreur lors de l'export PDF : {str(e)}"
            )

    def save_monster(self):
        """Sauvegarde le monstre dans un fichier."""
        monster = self.get_monster_from_form()

        if not monster.name:
            QMessageBox.warning(
                self,
                "Nom manquant",
                "Veuillez fournir un nom pour le PNJ/Monstre avant la sauvegarde."
            )
            return

        save_path = config_manager.get_save_path()
        default_filename = f"{monster.name.replace(' ', '_')}.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder le monstre",
            f"{save_path}/{default_filename}",
            "Fichiers JSON (*.json)"
        )

        if not file_path:
            return

        try:
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(monster.to_dict(), f, indent=4, ensure_ascii=False)

            QMessageBox.information(
                self,
                "Sauvegarde réussie",
                f"Le monstre a été sauvegardé avec succès vers :\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur de sauvegarde",
                f"Erreur lors de la sauvegarde : {str(e)}"
            )

    def load_monster(self):
        """Charge un monstre depuis un fichier."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Charger un monstre",
            config_manager.get_save_path(),
            "Fichiers JSON (*.json)"
        )

        if not file_path:
            return

        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            monster = Monster.from_dict(data)
            self.set_monster_to_form(monster)
            self.update_preview()

            QMessageBox.information(
                self,
                "Chargement réussi",
                f"Le monstre a été chargé avec succès depuis :\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur de chargement",
                f"Erreur lors du chargement : {str(e)}"
            )

    def on_generation_complete(self, monster: Monster):
        """Appelé lorsque la génération complète est terminée."""
        self.set_monster_to_form(monster)
        self.update_preview()
