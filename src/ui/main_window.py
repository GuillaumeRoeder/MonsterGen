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

from src.models.monster import Monster, Alignment, Size, AbilityScores, Action
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
        self.setGeometry(100, 100, 1024, 768)
        
        self.monster = Monster()
        self.signal_emitter = SignalEmitter()
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Panneau de gauche (formulaire)
        self.form_panel = self.create_form_panel()
        main_layout.addWidget(self.form_panel, stretch=1)
        
        # Panneau de droite (aperçu et actions)
        self.preview_panel = self.create_preview_panel()
        main_layout.addWidget(self.preview_panel, stretch=1)
    
    def create_form_panel(self) -> QWidget:
        """Crée le panneau de formulaire."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Onglets
        tab_widget = QTabWidget()
        
        # Onglet Informations de base
        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "Informations de base")
        
        # Onglet Statistiques
        stats_tab = self.create_stats_tab()
        tab_widget.addTab(stats_tab, "Statistiques")
        
        # Onglet Défense
        defense_tab = self.create_defense_tab()
        tab_widget.addTab(defense_tab, "Défense")
        
        # Onglet Sens et Langues
        senses_tab = self.create_senses_tab()
        tab_widget.addTab(senses_tab, "Sens et Langues")
        
        # Onglet Actions
        actions_tab = self.create_actions_tab()
        tab_widget.addTab(actions_tab, "Actions")
        
        # Onglet Autres
        other_tab = self.create_other_tab()
        tab_widget.addTab(other_tab, "Autres")
        
        layout.addWidget(tab_widget)
        
        # Boutons de contrôle
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
        
        # Nom
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nom du PNJ/Monstre")
        layout.addRow("Nom :", self.name_edit)
        
        # Race
        self.race_edit = QLineEdit()
        self.race_edit.setPlaceholderText("Race ou type de créature")
        layout.addRow("Race :", self.race_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Description du PNJ/Monstre")
        self.description_edit.setMaximumHeight(100)
        layout.addRow("Description :", self.description_edit)
        
        # Alignement
        self.alignment_combo = QComboBox()
        self.alignment_combo.addItem("", None)
        for alignment in Alignment:
            self.alignment_combo.addItem(alignment.value, alignment)
        layout.addRow("Alignement :", self.alignment_combo)
        
        # Taille
        self.size_combo = QComboBox()
        self.size_combo.addItem("", None)
        for size in Size:
            self.size_combo.addItem(size.value, size)
        layout.addRow("Taille :", self.size_combo)
        
        return tab
    
    def create_stats_tab(self) -> QWidget:
        """Crée l'onglet des statistiques."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Classe d'armure
        self.ac_spin = QSpinBox()
        self.ac_spin.setRange(0, 50)
        self.ac_spin.setSpecialValueText("")
        layout.addRow("Classe d'Armure (CA) :", self.ac_spin)
        
        # Points de vie
        self.hp_spin = QSpinBox()
        self.hp_spin.setRange(0, 1000)
        self.hp_spin.setSpecialValueText("")
        layout.addRow("Points de Vie (PV) :", self.hp_spin)
        
        # Dés de vie
        self.hit_dice_edit = QLineEdit()
        self.hit_dice_edit.setPlaceholderText("Ex: 3d8+6")
        layout.addRow("Dés de Vie :", self.hit_dice_edit)
        
        # Vitesse
        self.speed_edit = QLineEdit()
        self.speed_edit.setPlaceholderText("Ex: 30 pieds, vol 60 pieds")
        layout.addRow("Vitesse :", self.speed_edit)
        
        # Caractéristiques
        layout.addRow(QLabel("Caractéristiques :"), QLabel(""))
        
        chars_layout = QHBoxLayout()
        
        # Force
        self.str_spin = QSpinBox()
        self.str_spin.setRange(0, 30)
        self.str_spin.setSpecialValueText("")
        chars_layout.addWidget(QLabel("FOR :"))
        chars_layout.addWidget(self.str_spin)
        
        # Dextérité
        self.dex_spin = QSpinBox()
        self.dex_spin.setRange(0, 30)
        self.dex_spin.setSpecialValueText("")
        chars_layout.addWidget(QLabel("DEX :"))
        chars_layout.addWidget(self.dex_spin)
        
        # Constitution
        self.con_spin = QSpinBox()
        self.con_spin.setRange(0, 30)
        self.con_spin.setSpecialValueText("")
        chars_layout.addWidget(QLabel("CON :"))
        chars_layout.addWidget(self.con_spin)
        
        layout.addRow(chars_layout)
        
        chars_layout2 = QHBoxLayout()
        
        # Intelligence
        self.int_spin = QSpinBox()
        self.int_spin.setRange(0, 30)
        self.int_spin.setSpecialValueText("")
        chars_layout2.addWidget(QLabel("INT :"))
        chars_layout2.addWidget(self.int_spin)
        
        # Sagesse
        self.wis_spin = QSpinBox()
        self.wis_spin.setRange(0, 30)
        self.wis_spin.setSpecialValueText("")
        chars_layout2.addWidget(QLabel("SAG :"))
        chars_layout2.addWidget(self.wis_spin)
        
        # Charisme
        self.cha_spin = QSpinBox()
        self.cha_spin.setRange(0, 30)
        self.cha_spin.setSpecialValueText("")
        chars_layout2.addWidget(QLabel("CHA :"))
        chars_layout2.addWidget(self.cha_spin)
        
        layout.addRow(chars_layout2)
        
        # Challenge Rating
        self.cr_spin = QDoubleSpinBox()
        self.cr_spin.setRange(0, 30)
        self.cr_spin.setDecimals(1)
        self.cr_spin.setSingleStep(0.5)
        self.cr_spin.setSpecialValueText("")
        layout.addRow("Challenge Rating (CR) :", self.cr_spin)
        
        return tab
    
    def create_defense_tab(self) -> QWidget:
        """Crée l'onglet de défense."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Résistances aux dégâts
        self.resistances_edit = QTextEdit()
        self.resistances_edit.setPlaceholderText("Ex: feu, froid, foudre")
        self.resistances_edit.setMaximumHeight(60)
        layout.addRow("Résistances aux dégâts :", self.resistances_edit)
        
        # Immunités aux dégâts
        self.immunities_edit = QTextEdit()
        self.immunities_edit.setPlaceholderText("Ex: poison, psychique")
        self.immunities_edit.setMaximumHeight(60)
        layout.addRow("Immunités aux dégâts :", self.immunities_edit)
        
        # Vulnérabilités aux dégâts
        self.vulnerabilities_edit = QTextEdit()
        self.vulnerabilities_edit.setPlaceholderText("Ex: feu, acide")
        self.vulnerabilities_edit.setMaximumHeight(60)
        layout.addRow("Vulnérabilités aux dégâts :", self.vulnerabilities_edit)
        
        # Immunités aux états
        self.condition_immunities_edit = QTextEdit()
        self.condition_immunities_edit.setPlaceholderText("Ex: empoisonné, paralysé")
        self.condition_immunities_edit.setMaximumHeight(60)
        layout.addRow("Immunités aux états :", self.condition_immunities_edit)
        
        return tab
    
    def create_senses_tab(self) -> QWidget:
        """Crée l'onglet des sens et langues."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Sens
        self.senses_edit = QTextEdit()
        self.senses_edit.setPlaceholderText("Ex: vision dans le noir 60 pieds, perception passive 12")
        self.senses_edit.setMaximumHeight(60)
        layout.addRow("Sens :", self.senses_edit)
        
        # Perception passive
        self.passive_perception_spin = QSpinBox()
        self.passive_perception_spin.setRange(0, 30)
        self.passive_perception_spin.setSpecialValueText("")
        layout.addRow("Perception passive :", self.passive_perception_spin)
        
        # Langues
        self.languages_edit = QTextEdit()
        self.languages_edit.setPlaceholderText("Ex: commun, elfique, nain")
        self.languages_edit.setMaximumHeight(60)
        layout.addRow("Langues :", self.languages_edit)
        
        return tab
    
    def create_actions_tab(self) -> QWidget:
        """Crée l'onglet des actions."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Liste des actions
        self.actions_list = QListWidget()
        self.actions_list.setMinimumHeight(200)
        layout.addWidget(self.actions_list)
        
        # Boutons pour les actions
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
        
        # Actions légendaires
        layout.addWidget(QLabel("Actions Légendaires :"))
        self.legendary_actions_list = QListWidget()
        self.legendary_actions_list.setMinimumHeight(100)
        layout.addWidget(self.legendary_actions_list)
        
        legendary_control_layout = QHBoxLayout()
        
        self.add_legendary_btn = QPushButton("Ajouter")
        legendary_control_layout.addWidget(self.add_legendary_btn)
        
        self.edit_legendary_btn = QPushButton("Modifier")
        legendary_control_layout.addWidget(self.edit_legendary_btn)
        
        self.remove_legendary_btn = QPushButton("Supprimer")
        legendary_control_layout.addWidget(self.remove_legendary_btn)
        
        layout.addLayout(legendary_control_layout)
        
        # Réactions
        layout.addWidget(QLabel("Réactions :"))
        self.reactions_list = QListWidget()
        self.reactions_list.setMinimumHeight(100)
        layout.addWidget(self.reactions_list)
        
        reactions_control_layout = QHBoxLayout()
        
        self.add_reaction_btn = QPushButton("Ajouter")
        reactions_control_layout.addWidget(self.add_reaction_btn)
        
        self.edit_reaction_btn = QPushButton("Modifier")
        reactions_control_layout.addWidget(self.edit_reaction_btn)
        
        self.remove_reaction_btn = QPushButton("Supprimer")
        reactions_control_layout.addWidget(self.remove_reaction_btn)
        
        layout.addLayout(reactions_control_layout)
        
        return tab
    
    def create_other_tab(self) -> QWidget:
        """Crée l'onglet des autres informations."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Trésor
        self.treasure_edit = QTextEdit()
        self.treasure_edit.setPlaceholderText("Description du trésor ou butin")
        self.treasure_edit.setMaximumHeight(60)
        layout.addRow("Trésor :", self.treasure_edit)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notes supplémentaires")
        self.notes_edit.setMaximumHeight(100)
        layout.addRow("Notes :", self.notes_edit)
        
        return tab
    
    def create_preview_panel(self) -> QWidget:
        """Crée le panneau d'aperçu."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Titre
        title_label = QLabel("Aperçu de la fiche")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Zone de défilement pour l'aperçu
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.preview_content = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_content)
        self.preview_layout.setContentsMargins(10, 10, 10, 10)
        self.preview_layout.setSpacing(10)
        
        scroll_area.setWidget(self.preview_content)
        layout.addWidget(scroll_area, stretch=1)
        
        # Bouton de rafraîchissement
        refresh_btn = QPushButton("Rafraîchir l'aperçu")
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.clicked.connect(self.refresh_preview)
        layout.addWidget(refresh_btn)
        
        return panel
    
    def setup_connections(self):
        """Configure les connexions des signaux."""
        # Connexions des boutons
        self.generate_btn.clicked.connect(self.generate_missing_fields)
        self.export_btn.clicked.connect(self.export_to_pdf)
        self.save_btn.clicked.connect(self.save_monster)
        self.load_btn.clicked.connect(self.load_monster)
        
        self.add_action_btn.clicked.connect(self.add_action)
        self.edit_action_btn.clicked.connect(self.edit_action)
        self.remove_action_btn.clicked.connect(self.remove_action)
        
        self.add_legendary_btn.clicked.connect(lambda: self.add_legendary_action())
        self.edit_legendary_btn.clicked.connect(lambda: self.edit_legendary_action())
        self.remove_legendary_btn.clicked.connect(lambda: self.remove_legendary_action())
        
        self.add_reaction_btn.clicked.connect(lambda: self.add_reaction())
        self.edit_reaction_btn.clicked.connect(lambda: self.edit_reaction())
        self.remove_reaction_btn.clicked.connect(lambda: self.remove_reaction())
        
        # Connexion des signaux de l'émetteur
        self.signal_emitter.show_options.connect(self.show_options_dialog)
        self.signal_emitter.generation_complete.connect(self.on_generation_complete)
    
    def refresh_preview(self):
        """Rafraîchit l'aperçu de la fiche."""
        self.update_preview()
    
    def update_preview(self):
        """Met à jour l'aperçu avec les données actuelles."""
        # Effacer l'aperçu actuel
        for i in reversed(range(self.preview_layout.count())):
            widget = self.preview_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Créer un monstre temporaire avec les données du formulaire
        monster = self.get_monster_from_form()
        
        # Ajouter les informations de base
        if monster.name:
            name_label = QLabel(f"<b>Nom :</b> {monster.name}")
            self.preview_layout.addWidget(name_label)
        
        if monster.race:
            race_label = QLabel(f"<b>Race :</b> {monster.race}")
            self.preview_layout.addWidget(race_label)
        
        if monster.alignment:
            alignment_label = QLabel(f"<b>Alignement :</b> {monster.alignment.value}")
            self.preview_layout.addWidget(alignment_label)
        
        if monster.size:
            size_label = QLabel(f"<b>Taille :</b> {monster.size.value}")
            self.preview_layout.addWidget(size_label)
        
        if monster.armor_class:
            ac_label = QLabel(f"<b>CA :</b> {monster.armor_class}")
            self.preview_layout.addWidget(ac_label)
        
        if monster.hit_points:
            hp_label = QLabel(f"<b>PV :</b> {monster.hit_points}")
            self.preview_layout.addWidget(hp_label)
        
        if monster.speed:
            speed_label = QLabel(f"<b>Vitesse :</b> {monster.speed}")
            self.preview_layout.addWidget(speed_label)
        
        if monster.description:
            desc_label = QLabel(f"<b>Description :</b>")
            self.preview_layout.addWidget(desc_label)
            desc_text = QLabel(monster.description)
            desc_text.setWordWrap(True)
            self.preview_layout.addWidget(desc_text)
        
        # Ajouter un espaceur
        self.preview_layout.addStretch()
    
    def get_monster_from_form(self) -> Monster:
        """Récupère les données du monstre depuis le formulaire."""
        monster = Monster()
        
        # Informations de base
        monster.name = self.name_edit.text().strip() or None
        monster.race = self.race_edit.text().strip() or None
        monster.description = self.description_edit.toPlainText().strip() or None
        
        alignment_index = self.alignment_combo.currentIndex()
        if alignment_index > 0:
            monster.alignment = self.alignment_combo.itemData(alignment_index)
        
        size_index = self.size_combo.currentIndex()
        if size_index > 0:
            monster.size = self.size_combo.itemData(size_index)
        
        # Statistiques
        if self.ac_spin.value() > 0:
            monster.armor_class = self.ac_spin.value()
        
        if self.hp_spin.value() > 0:
            monster.hit_points = self.hp_spin.value()
        
        monster.hit_dice = self.hit_dice_edit.text().strip() or None
        monster.speed = self.speed_edit.text().strip() or None
        
        # Caractéristiques
        monster.ability_scores = AbilityScores(
            strength=self.str_spin.value() if self.str_spin.value() > 0 else 10,
            dexterity=self.dex_spin.value() if self.dex_spin.value() > 0 else 10,
            constitution=self.con_spin.value() if self.con_spin.value() > 0 else 10,
            intelligence=self.int_spin.value() if self.int_spin.value() > 0 else 10,
            wisdom=self.wis_spin.value() if self.wis_spin.value() > 0 else 10,
            charisma=self.cha_spin.value() if self.cha_spin.value() > 0 else 10,
        )
        
        # Challenge Rating
        if self.cr_spin.value() > 0:
            monster.challenge_rating = self.cr_spin.value()
        
        # Défense
        resistances_text = self.resistances_edit.toPlainText().strip()
        if resistances_text:
            monster.damage_resistances = [r.strip() for r in resistances_text.split(",") if r.strip()]
        
        immunities_text = self.immunities_edit.toPlainText().strip()
        if immunities_text:
            monster.damage_immunities = [i.strip() for i in immunities_text.split(",") if i.strip()]
        
        vulnerabilities_text = self.vulnerabilities_edit.toPlainText().strip()
        if vulnerabilities_text:
            monster.damage_vulnerabilities = [v.strip() for v in vulnerabilities_text.split(",") if v.strip()]
        
        condition_immunities_text = self.condition_immunities_edit.toPlainText().strip()
        if condition_immunities_text:
            monster.condition_immunities = [c.strip() for c in condition_immunities_text.split(",") if c.strip()]
        
        # Sens
        senses_text = self.senses_edit.toPlainText().strip()
        if senses_text:
            monster.senses = [s.strip() for s in senses_text.split(",") if s.strip()]
        
        if self.passive_perception_spin.value() > 0:
            monster.passive_perception = self.passive_perception_spin.value()
        
        # Langues
        languages_text = self.languages_edit.toPlainText().strip()
        if languages_text:
            monster.languages = [l.strip() for l in languages_text.split(",") if l.strip()]
        
        # Actions
        for i in range(self.actions_list.count()):
            item = self.actions_list.item(i)
            action_data = item.data(Qt.ItemDataRole.UserRole)
            if action_data:
                action = Action(**action_data)
                monster.actions.append(action)
        
        # Actions légendaires
        for i in range(self.legendary_actions_list.count()):
            item = self.legendary_actions_list.item(i)
            action_data = item.data(Qt.ItemDataRole.UserRole)
            if action_data:
                action = Action(**action_data)
                monster.legendary_actions.append(action)
        
        # Réactions
        for i in range(self.reactions_list.count()):
            item = self.reactions_list.item(i)
            action_data = item.data(Qt.ItemDataRole.UserRole)
            if action_data:
                action = Action(**action_data)
                monster.reactions.append(action)
        
        # Autres
        monster.treasure = self.treasure_edit.toPlainText().strip() or None
        monster.notes = self.notes_edit.toPlainText().strip() or None
        
        return monster
    
    def set_monster_to_form(self, monster: Monster):
        """Remplit le formulaire avec les données du monstre."""
        # Informations de base
        self.name_edit.setText(monster.name or "")
        self.race_edit.setText(monster.race or "")
        self.description_edit.setPlainText(monster.description or "")
        
        if monster.alignment:
            index = self.alignment_combo.findData(monster.alignment)
            if index >= 0:
                self.alignment_combo.setCurrentIndex(index)
        
        if monster.size:
            index = self.size_combo.findData(monster.size)
            if index >= 0:
                self.size_combo.setCurrentIndex(index)
        
        # Statistiques
        self.ac_spin.setValue(monster.armor_class or 0)
        self.hp_spin.setValue(monster.hit_points or 0)
        self.hit_dice_edit.setText(monster.hit_dice or "")
        self.speed_edit.setText(monster.speed or "")
        
        # Caractéristiques
        self.str_spin.setValue(monster.ability_scores.strength)
        self.dex_spin.setValue(monster.ability_scores.dexterity)
        self.con_spin.setValue(monster.ability_scores.constitution)
        self.int_spin.setValue(monster.ability_scores.intelligence)
        self.wis_spin.setValue(monster.ability_scores.wisdom)
        self.cha_spin.setValue(monster.ability_scores.charisma)
        
        # Challenge Rating
        self.cr_spin.setValue(monster.challenge_rating or 0)
        
        # Défense
        self.resistances_edit.setPlainText(", ".join(monster.damage_resistances))
        self.immunities_edit.setPlainText(", ".join(monster.damage_immunities))
        self.vulnerabilities_edit.setPlainText(", ".join(monster.damage_vulnerabilities))
        self.condition_immunities_edit.setPlainText(", ".join(monster.condition_immunities))
        
        # Sens
        self.senses_edit.setPlainText(", ".join(monster.senses))
        self.passive_perception_spin.setValue(monster.passive_perception or 0)
        
        # Langues
        self.languages_edit.setPlainText(", ".join(monster.languages))
        
        # Actions
        self.actions_list.clear()
        for action in monster.actions:
            self.add_action_to_list(self.actions_list, action)
        
        # Actions légendaires
        self.legendary_actions_list.clear()
        for action in monster.legendary_actions:
            self.add_action_to_list(self.legendary_actions_list, action)
        
        # Réactions
        self.reactions_list.clear()
        for action in monster.reactions:
            self.add_action_to_list(self.reactions_list, action)
        
        # Autres
        self.treasure_edit.setPlainText(monster.treasure or "")
        self.notes_edit.setPlainText(monster.notes or "")
    
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
        """Ajoute une nouvelle action."""
        dialog = ActionDialog(self)
        if dialog.exec() == QMessageBox.StandardButton.Ok:
            action_data = dialog.get_action_data()
            if action_data:
                action = Action(**action_data)
                self.add_action_to_list(self.actions_list, action)
    
    def edit_action(self):
        """Modifie une action existante."""
        selected = self.actions_list.currentItem()
        if not selected:
            return
        
        action_data = selected.data(Qt.ItemDataRole.UserRole)
        if not action_data:
            return
        
        dialog = ActionDialog(self)
        dialog.set_action_data(action_data)
        if dialog.exec() == QMessageBox.StandardButton.Ok:
            new_action_data = dialog.get_action_data()
            if new_action_data:
                selected.setText(new_action_data["name"])
                selected.setData(Qt.ItemDataRole.UserRole, new_action_data)
    
    def remove_action(self):
        """Supprime une action."""
        selected = self.actions_list.currentItem()
        if selected:
            self.actions_list.takeItem(self.actions_list.row(selected))
    
    def add_legendary_action(self):
        """Ajoute une nouvelle action légendaire."""
        dialog = SimpleActionDialog(self, "Ajouter une action légendaire")
        if dialog.exec() == QMessageBox.StandardButton.Ok:
            action_data = dialog.get_action_data()
            if action_data:
                action = Action(**action_data)
                self.add_action_to_list(self.legendary_actions_list, action)
    
    def edit_legendary_action(self):
        """Modifie une action légendaire."""
        selected = self.legendary_actions_list.currentItem()
        if not selected:
            return
        
        action_data = selected.data(Qt.ItemDataRole.UserRole)
        if not action_data:
            return
        
        dialog = SimpleActionDialog(self, "Modifier l'action légendaire")
        dialog.set_action_data(action_data)
        if dialog.exec() == QMessageBox.StandardButton.Ok:
            new_action_data = dialog.get_action_data()
            if new_action_data:
                selected.setText(new_action_data["name"])
                selected.setData(Qt.ItemDataRole.UserRole, new_action_data)
    
    def remove_legendary_action(self):
        """Supprime une action légendaire."""
        selected = self.legendary_actions_list.currentItem()
        if selected:
            self.legendary_actions_list.takeItem(self.legendary_actions_list.row(selected))
    
    def add_reaction(self):
        """Ajoute une nouvelle réaction."""
        dialog = SimpleActionDialog(self, "Ajouter une réaction")
        if dialog.exec() == QMessageBox.StandardButton.Ok:
            action_data = dialog.get_action_data()
            if action_data:
                action = Action(**action_data)
                self.add_action_to_list(self.reactions_list, action)
    
    def edit_reaction(self):
        """Modifie une réaction."""
        selected = self.reactions_list.currentItem()
        if not selected:
            return
        
        action_data = selected.data(Qt.ItemDataRole.UserRole)
        if not action_data:
            return
        
        dialog = SimpleActionDialog(self, "Modifier la réaction")
        dialog.set_action_data(action_data)
        if dialog.exec() == QMessageBox.StandardButton.Ok:
            new_action_data = dialog.get_action_data()
            if new_action_data:
                selected.setText(new_action_data["name"])
                selected.setData(Qt.ItemDataRole.UserRole, new_action_data)
    
    def remove_reaction(self):
        """Supprime une réaction."""
        selected = self.reactions_list.currentItem()
        if selected:
            self.reactions_list.takeItem(self.reactions_list.row(selected))
    
    def generate_missing_fields(self):
        """Génère les champs manquants avec l'IA."""
        # Vérifier que la clé API est configurée
        api_key = config_manager.get_api_key()
        if not api_key:
            QMessageBox.warning(
                self,
                "Clé API manquante",
                "Veuillez configurer votre clé API dans les paramètres avant de générer des champs."
            )
            return
        
        # Recharger la configuration du générateur IA
        ai_generator.reload_config()
        
        # Récupérer le monstre actuel
        monster = self.get_monster_from_form()
        
        # Identifier les champs manquants
        missing_fields = []
        if not monster.name:
            missing_fields.append("name")
        if not monster.race:
            missing_fields.append("race")
        if not monster.description:
            missing_fields.append("description")
        if not monster.alignment:
            missing_fields.append("alignment")
        if not monster.size:
            missing_fields.append("size")
        if not monster.armor_class:
            missing_fields.append("armor_class")
        if not monster.hit_points:
            missing_fields.append("hit_points")
        if not monster.speed:
            missing_fields.append("speed")
        if not monster.challenge_rating:
            missing_fields.append("challenge_rating")
        
        if not missing_fields:
            QMessageBox.information(
                self,
                "Aucun champ manquant",
                "Tous les champs principaux sont déjà remplis."
            )
            return
        
        # Générer toutes les options en une seule boîte de dialogue
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
        
        # Afficher une seule boîte de dialogue pour tous les champs
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
        
        # Limiter à 5 options pour éviter un dialogue trop grand
        display_options = options[:5]
        
        text = f"Sélectionnez une option pour {field_name} :\n\n"
        for i, option in enumerate(display_options, 1):
            text += f"{i}. {option}\n"
        
        dialog.setText(text)
        
        # Ajouter des boutons pour chaque option
        for i, option in enumerate(display_options):
            btn = dialog.addButton(f"Option {i+1}", QMessageBox.ButtonRole.ActionRole)
            btn.setData(option)
        
        # Bouton personnalisé
        custom_btn = dialog.addButton("Personnalisé", QMessageBox.ButtonRole.ActionRole)
        
        # Bouton annuler
        cancel_btn = dialog.addButton(QMessageBox.StandardButton.Cancel)
        
        dialog.exec()
        
        clicked = dialog.clickedButton()
        
        if clicked == cancel_btn:
            return
        
        if clicked == custom_btn:
            # Permettre à l'utilisateur de saisir une valeur personnalisée
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
    
    def set_field_value(self, field_name: str, value: str):
        """Définit la valeur d'un champ dans le formulaire."""
        if field_name == "name":
            self.name_edit.setText(value)
        elif field_name == "race":
            self.race_edit.setText(value)
        elif field_name == "description":
            self.description_edit.setPlainText(value)
        elif field_name == "alignment":
            index = self.alignment_combo.findText(value)
            if index >= 0:
                self.alignment_combo.setCurrentIndex(index)
        elif field_name == "size":
            index = self.size_combo.findText(value)
            if index >= 0:
                self.size_combo.setCurrentIndex(index)
        elif field_name == "armor_class":
            try:
                self.ac_spin.setValue(int(value))
            except ValueError:
                pass
        elif field_name == "hit_points":
            try:
                self.hp_spin.setValue(int(value))
            except ValueError:
                pass
        elif field_name == "speed":
            self.speed_edit.setText(value)
        elif field_name == "challenge_rating":
            try:
                self.cr_spin.setValue(float(value))
            except ValueError:
                pass
    
    def export_to_pdf(self):
        """Exporte le monstre en PDF."""
        monster = self.get_monster_from_form()
        
        # Vérifier que le nom est présent
        if not monster.name:
            QMessageBox.warning(
                self,
                "Nom manquant",
                "Veuillez fournir un nom pour le PNJ/Monstre avant l'export."
            )
            return
        
        # Demander le chemin de sortie
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


class ActionDialog(QMessageBox):
    """Boîte de dialogue pour ajouter/modifier une action."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter/Modifier une action")
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface."""
        layout = QFormLayout(self)
        
        # Nom
        self.name_edit = QLineEdit()
        layout.addRow("Nom :", self.name_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        layout.addRow("Description :", self.description_edit)
        
        # Bonus d'attaque
        self.attack_bonus_spin = QSpinBox()
        self.attack_bonus_spin.setRange(-10, 20)
        self.attack_bonus_spin.setSpecialValueText("")
        layout.addRow("Bonus d'attaque :", self.attack_bonus_spin)
        
        # Dégâts
        self.damage_edit = QLineEdit()
        self.damage_edit.setPlaceholderText("Ex: 1d8+3")
        layout.addRow("Dégâts :", self.damage_edit)
        
        # Type de dégâts
        self.damage_type_edit = QLineEdit()
        self.damage_type_edit.setPlaceholderText("Ex: tranchant, perforant")
        layout.addRow("Type de dégâts :", self.damage_type_edit)
        
        # Boutons
        ok_btn = self.addButton(QMessageBox.StandardButton.Ok)
        cancel_btn = self.addButton(QMessageBox.StandardButton.Cancel)
        
        # Connexions
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
    
    def set_action_data(self, action_data: Dict):
        """Remplit le formulaire avec les données d'une action."""
        self.name_edit.setText(action_data.get("name", ""))
        self.description_edit.setPlainText(action_data.get("description", ""))
        
        attack_bonus = action_data.get("attack_bonus")
        if attack_bonus is not None:
            self.attack_bonus_spin.setValue(attack_bonus)
        
        self.damage_edit.setText(action_data.get("damage", ""))
        self.damage_type_edit.setText(action_data.get("damage_type", ""))
    
    def get_action_data(self) -> Optional[Dict]:
        """Récupère les données de l'action."""
        name = self.name_edit.text().strip()
        if not name:
            return None
        
        return {
            "name": name,
            "description": self.description_edit.toPlainText().strip(),
            "attack_bonus": self.attack_bonus_spin.value() if self.attack_bonus_spin.value() != 0 else None,
            "damage": self.damage_edit.text().strip() or None,
            "damage_type": self.damage_type_edit.text().strip() or None,
        }


class SimpleActionDialog(QMessageBox):
    """Boîte de dialogue simplifiée pour les actions légendaires et réactions."""
    
    def __init__(self, parent=None, title=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface."""
        layout = QFormLayout(self)
        
        # Nom
        self.name_edit = QLineEdit()
        layout.addRow("Nom :", self.name_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        layout.addRow("Description :", self.description_edit)
        
        # Boutons
        ok_btn = self.addButton(QMessageBox.StandardButton.Ok)
        cancel_btn = self.addButton(QMessageBox.StandardButton.Cancel)
        
        # Connexions
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
    
    def set_action_data(self, action_data: Dict):
        """Remplit le formulaire avec les données d'une action."""
        self.name_edit.setText(action_data.get("name", ""))
        self.description_edit.setPlainText(action_data.get("description", ""))
    
    def get_action_data(self) -> Optional[Dict]:
        """Récupère les données de l'action."""
        name = self.name_edit.text().strip()
        if not name:
            return None
        
        return {
            "name": name,
            "description": self.description_edit.toPlainText().strip(),
            "attack_bonus": None,
            "damage": None,
            "damage_type": None,
        }
