"""
Fenêtre principale de l'application MonsterGen.
"""

from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton, QSpinBox,
    QFormLayout, QMessageBox, QFileDialog, QTabWidget,
    QScrollArea, QInputDialog, QFrame
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtGui import QFont, QIcon

from src.models.monster import Monster, AbilityScores, Action, Skill
from src.ai.ai_generator import ai_generator
from src.ai.api_client import api_client
from src.ai.local_model import local_model, ModelNotAvailableError
from src.rules.encounter import (
    DIFFICULTIES, DIFFICULTY_COLORS, encounter_cr, difficulty_summary,
)
from src.rules.stat_builder import (
    cr_display, cr_xp, build_balanced_monster,
)
from src.ui.languages_editor import LanguagesEditor
from src.ui.pill_editor import PillEditor
from src.ui.styles import ACCENT_BUTTON_STYLE, SECONDARY_BUTTON_STYLE

# Compétences DnD 5e (suggestions pour l'éditeur en pills).
DND5_SKILLS = [
    "Acrobaties", "Arcanes", "Athlétisme", "Discrétion", "Escamotage",
    "Histoire", "Intimidation", "Intuition", "Investigation", "Médecine",
    "Nature", "Perception", "Perspicacité", "Persuasion", "Représentation",
    "Religion", "Supercherie", "Survie",
]

# Races DnD 5e (liste hardcodée pour le champ Race).
DND5_RACES = [
    "Humain", "Elfe", "Haut-elfe", "Elfe des bois", "Elfe noir (Drow)",
    "Nain", "Nain des collines", "Nain des montagnes", "Gnome",
    "Gnome des forêts", "Gnome des roches", "Halfelin", "Dem elfe",
    "Dem-orc", "Tiefling", "Drakéide (Dragonborn)", "Goliath",
    "Aasimar", "Genasi", "Gobelin", "Hobgobelin", "Orc", "Bugbear",
    "Kobold", "Gnoll", "Homme-lézard", "Ogre", "Troll", "Géant",
    "Squelette", "Zombie", "Goule", "Spectre", "Liche",
    "Diable", "Démon", "Ange", "Fée", "Dryade", "Satyre",
    "Méduse", "Minotaure", "Centaure", "Hydre", "Basilic",
    "Béhir", "Wyverne", "Dragon", "Griffon", "Hippogriffe",
    "Chimère", "Manticore", "Sphinx", "Kraken", "Aboleth",
    "Golem d'argile", "Golem de chair", "Golem de fer", "Golem de pierre",
]

# Types de dégâts DnD 5e (résistances/immunités).
DND5_DAMAGE_TYPES = [
    "contondant", "tranchant", "perforant", "feu", "froid", "foudre",
    "poison", "acide", "psychique", "radiant", "nécrotique", "tonnerre",
]
from src.ui.action_editor import ActionEditorWidget
from src.export.pdf_exporter import pdf_exporter
from src.export.png_exporter import png_exporter
from config.config_manager import config_manager


class SignalEmitter(QObject):
    """
    Émetteur de signaux pour la communication entre threads.
    """
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
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(250)
        self._preview_timer.timeout.connect(self.update_preview)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.backend_status_label = QLabel("")
        self.backend_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.backend_status_label.setFixedHeight(26)
        root_layout.addWidget(self.backend_status_label)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        root_layout.addLayout(main_layout, stretch=1)

        self.form_panel = self.create_form_panel()
        main_layout.addWidget(self.form_panel, stretch=1)

        self.preview_panel = self.create_preview_panel()
        main_layout.addWidget(self.preview_panel, stretch=1)

        self.update_backend_status()

    def update_backend_status(self):
        """Met à jour l'étiquette du mode IA (API ou modèle local)."""
        mode = config_manager.get_ai_mode()
        if mode == "api":
            model = config_manager.get_api_model() or "API"
            self.backend_status_label.setText(f"● Mode API — {model}")
            self.backend_status_label.setStyleSheet(
                "background-color: #4a3f14; color: #ffd54a; "
                "font-weight: bold; padding: 3px; "
                "border-bottom: 1px solid #5a5a6a;"
            )
        else:
            from src.ai.local_model import local_model
            info = local_model.get_model_info()
            if local_model.is_available():
                status = "prêt"
                bg = "#1e3a24"
                fg = "#66bb6a"
            else:
                status = "non téléchargé"
                bg = "#3a2a1a"
                fg = "#ffab40"
            self.backend_status_label.setText(
                f"● Modèle local — {info['label']} ({status})"
            )
            self.backend_status_label.setStyleSheet(
                f"background-color: {bg}; color: {fg}; "
                "font-weight: bold; padding: 3px; "
                "border-bottom: 1px solid #5a5a6a;"
            )

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
        self.generate_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        control_layout.addWidget(self.generate_btn)

        self.export_btn = QPushButton("Exporter en PDF")
        self.export_btn.setIcon(QIcon.fromTheme("document-export"))
        control_layout.addWidget(self.export_btn)

        self.export_png_btn = QPushButton("Exporter en PNG")
        self.export_png_btn.setIcon(QIcon.fromTheme("image-x-generic"))
        control_layout.addWidget(self.export_png_btn)

        self.reset_btn = QPushButton("Réinitialiser")
        self.reset_btn.setIcon(QIcon.fromTheme("document-new"))
        self.reset_btn.setToolTip("Effacer tous les champs : identité, stats, actions, scénario, équipement…")
        self.reset_btn.clicked.connect(self.reset_all_fields)
        control_layout.addWidget(self.reset_btn)

        layout.addLayout(control_layout)

        return panel

    def create_basic_tab(self) -> QWidget:
        """Crée l'onglet des informations de base."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        layout.addRow("Groupe :", self._create_party_widgets())
        layout.addRow("Difficulté résultante :", self.difficulty_result_label)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nom du PNJ/Monstre")
        layout.addRow("Nom :", self.name_edit)

        race_layout = QHBoxLayout()
        race_layout.setSpacing(4)
        self.race_edit = QLineEdit()
        self.race_edit.setPlaceholderText("Race ou type de créature")
        race_layout.addWidget(self.race_edit, stretch=1)

        self.race_menu_btn = QPushButton("▾")
        self.race_menu_btn.setFixedSize(24, 24)
        self.race_menu_btn.setToolTip("Choisir une race DnD 5e")
        self.race_menu_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self.race_menu_btn.clicked.connect(self._show_race_menu)
        race_layout.addWidget(self.race_menu_btn)

        layout.addRow("Race :", race_layout)

        self.languages_edit = LanguagesEditor()
        languages_frame = QFrame()
        languages_frame.setFrameShape(QFrame.Shape.StyledPanel)
        languages_frame.setStyleSheet("""
            QFrame {
                background-color: #f4f7fa;
                border: 1px solid #b8c6d3;
                border-radius: 6px;
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
            "color: #45607a; font-size: 11px; background: transparent; border: none;"
        )
        languages_layout.addWidget(languages_header)
        languages_layout.addWidget(self.languages_edit)

        layout.addRow("Langues :", languages_frame)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Description du PNJ/Monstre")
        self.description_edit.setMaximumHeight(100)
        layout.addRow("Description :", self.description_edit)

        scenario_layout = QHBoxLayout()
        self.scenario_edit = QTextEdit()
        self.scenario_edit.setPlaceholderText(
            "Scénario de rencontre — cliquez sur le bouton pour le générer "
            "à partir des stats actuelles du monstre."
        )
        scenario_layout.addWidget(self.scenario_edit, stretch=1)

        self.gen_scenario_btn = QPushButton("Générer\nscénario")
        self.gen_scenario_btn.setIcon(QIcon.fromTheme("system-run"))
        self.gen_scenario_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.gen_scenario_btn.setMaximumWidth(110)
        self.gen_scenario_btn.clicked.connect(self._generate_scenario)
        scenario_layout.addWidget(self.gen_scenario_btn)

        layout.addRow("Scénario :", scenario_layout)

        return tab

    def _show_race_menu(self):
        """Affiche le menu déroulant des races DnD 5e sous la flèche."""
        from PySide6.QtWidgets import QMenu

        menu = QMenu(self)
        for race in DND5_RACES:
            action = menu.addAction(race)
            action.triggered.connect(
                lambda checked, r=race: self.race_edit.setText(r)
            )
        btn_pos = self.race_menu_btn.mapTo(self, self.race_menu_btn.rect().bottomLeft())
        menu.exec(btn_pos)

    def _create_party_widgets(self) -> QHBoxLayout:
        """Crée la ligne 'groupe de joueurs + difficulté' (tab Informations)."""
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

        self.gen_stats_btn = QPushButton("Équilibrer les stats")
        self.gen_stats_btn.setIcon(QIcon.fromTheme("system-run"))
        self.gen_stats_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.gen_stats_btn.clicked.connect(self._fill_balanced_stats)
        party_layout.addWidget(self.gen_stats_btn)

        self.difficulty_result_label = QLabel("")
        self.difficulty_result_label.setStyleSheet("font-weight: bold;")

        self.party_size_spin.valueChanged.connect(self._update_difficulty_label)
        self.party_level_spin.valueChanged.connect(self._update_difficulty_label)
        self.difficulty_combo.currentIndexChanged.connect(self._update_difficulty_label)
        self._update_difficulty_label()

        return party_layout

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

        self.skills_edit = PillEditor(suggestions=DND5_SKILLS,
                                      empty_text="Aucune compétence maîtrisée")
        layout.addRow("Compétences maîtrisées :", self.skills_edit)

        self.resistances_edit = PillEditor(suggestions=DND5_DAMAGE_TYPES,
                                           empty_text="Aucune résistance")
        layout.addRow("Résistances :", self.resistances_edit)

        self.immunities_edit = PillEditor(suggestions=DND5_DAMAGE_TYPES,
                                          empty_text="Aucune immunité")
        layout.addRow("Immunités :", self.immunities_edit)

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
        gen_actions_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        gen_actions_btn.clicked.connect(self._generate_actions)
        layout.addWidget(gen_actions_btn)

        # Sous-fonction : description libre des actions souhaitées,
        # présentée comme sous-action compacte de la génération automatique.
        prompt_row = QHBoxLayout()
        prompt_row.setContentsMargins(14, 0, 0, 0)   # indentation visuelle
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
        self.gen_actions_prompt_btn.clicked.connect(self._generate_actions_from_prompt)
        prompt_row.addWidget(self.gen_actions_prompt_btn)
        layout.addLayout(prompt_row)

        self.actions_scroll = QScrollArea()
        self.actions_scroll.setWidgetResizable(True)
        self.actions_scroll.setMinimumHeight(200)
        self.actions_container = QWidget()
        self.actions_layout = QVBoxLayout(self.actions_container)
        self.actions_layout.setContentsMargins(4, 4, 4, 4)
        self.actions_layout.setSpacing(8)
        self.actions_layout.addStretch()
        self.actions_scroll.setWidget(self.actions_container)
        layout.addWidget(self.actions_scroll)

        actions_control_layout = QHBoxLayout()

        self.add_action_btn = QPushButton("Ajouter une action")
        self.add_action_btn.setIcon(QIcon.fromTheme("list-add"))
        actions_control_layout.addWidget(self.add_action_btn)

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
        self.export_png_btn.clicked.connect(self.export_to_png)

        self.add_action_btn.clicked.connect(self.add_action)

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
            self._add_preview_label(f"<b>PV :</b> {monster.hit_points} ({monster.hit_dice or '—'})")
        if monster.speed:
            self._add_preview_label(f"<b>Vitesse :</b> {monster.speed}")
        if monster.challenge_rating:
            self._add_preview_label(
                f"<b>CR :</b> {cr_display(monster.challenge_rating)} ({cr_xp(monster.challenge_rating)} PX)"
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
            skill_parts = [f"{sk.name} {monster.skill_modifier(sk):+d}" for sk in proficient_skills]
            self._add_preview_label(f"<b>Compétences maîtrisées :</b> {', '.join(skill_parts)}")

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

    def _get_selected_cr(self) -> Optional[float]:
        """CR dérivé du groupe (joueurs, niveau moyen, difficulté choisie)."""
        return encounter_cr(
            self.party_size_spin.value(),
            self.party_level_spin.value(),
            self.difficulty_combo.currentData() or "medium",
        )

    def _ensure_difficulty(self) -> Optional[float]:
        """Le CR est toujours dérivé du groupe ; aucun dialogue nécessaire."""
        return self._get_selected_cr()

    def _update_difficulty_label(self):
        """Met à jour le label coloré de la difficulté résultante."""
        difficulty_key = self.difficulty_combo.currentData() or "medium"
        summary = difficulty_summary(
            self.party_size_spin.value(),
            self.party_level_spin.value(),
            difficulty_key,
        )
        color = DIFFICULTY_COLORS.get(difficulty_key, "#e0e0e0")
        self.difficulty_result_label.setText(f"● {summary}")
        self.difficulty_result_label.setStyleSheet(
            f"font-weight: bold; color: {color};"
        )

    def _fill_balanced_stats(self):
        """Remplit directement un monstre équilibré pour le CR choisi."""
        cr = self._ensure_difficulty()
        if cr is None:
            return

        monster = build_balanced_monster(cr, base=self.get_monster_from_form())
        self.set_monster_to_form(monster, keep_scenario=True)
        self.update_preview()

    def get_monster_from_form(self) -> Monster:
        """Récupère les données du monstre depuis le formulaire."""
        monster = Monster()

        monster.name = self.name_edit.text().strip() or None
        monster.race = self.race_edit.text().strip() or None
        monster.description = self.description_edit.toPlainText().strip() or None
        monster.scenario = self.scenario_edit.toPlainText().strip()

        languages_text = self.languages_edit.toPlainText().strip()
        if languages_text:
            monster.languages = [l.strip() for l in languages_text.split(",") if l.strip()]

        monster.armor_class = self.ac_spin.value() if self.ac_spin.value() > 0 else None
        monster.hit_points = self.hp_spin.value() if self.hp_spin.value() > 0 else None
        monster.hit_dice = self.hit_dice_edit.text().strip() or None
        monster.speed = self.speed_edit.text().strip() or None

        selected_cr = self._get_selected_cr()
        monster.challenge_rating = selected_cr
        prof_value = self.proficiency_spin.value()
        monster.proficiency_bonus = prof_value if prof_value > 0 else None

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

        monster.skills = [
            Skill(name=name, ability="", proficiency=True)
            for name in self.skills_edit.get_values()
        ]
        monster.damage_resistances = self.resistances_edit.get_values()
        monster.damage_immunities = self.immunities_edit.get_values()

        for widget in self.get_action_widgets():
            action = widget.get_action()
            if action.name:
                monster.actions.append(action)

        monster.notes = self.equipment_edit.toPlainText().strip() or None

        return monster

    def set_monster_to_form(self, monster: Monster, keep_scenario: bool = False):
        """Remplit le formulaire avec les données du monstre."""
        self.name_edit.setText(monster.name or "")
        self.race_edit.setText(monster.race or "")
        self.description_edit.setPlainText(monster.description or "")

        self.languages_edit.setPlainText(", ".join(monster.languages))

        self.ac_spin.setValue(monster.armor_class or 0)
        self.hp_spin.setValue(monster.hit_points or 0)
        self.hit_dice_edit.setText(monster.hit_dice or "")
        self.speed_edit.setText(monster.speed or "")
        self.proficiency_spin.setValue(monster.proficiency_bonus or 0)


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

        self.skills_edit.set_values([sk.name for sk in monster.skills if sk.proficiency])
        self.resistances_edit.set_values(monster.damage_resistances)
        self.immunities_edit.set_values(monster.damage_immunities)

        self.clear_actions()
        for action in monster.actions:
            self.add_action_to_list(action)

        self.equipment_edit.setPlainText(monster.notes or "")

        if not keep_scenario:
            self.scenario_edit.setPlainText(monster.scenario or "")

    def add_action_to_list(self, action: Action):
        """Ajoute un widget d'action éditable à la liste."""
        widget = ActionEditorWidget(action)
        widget.changed.connect(self.on_action_changed)
        widget.removeRequested.connect(self._on_remove_action)
        self.actions_layout.insertWidget(self.actions_layout.count() - 1, widget)

    def _on_remove_action(self, widget: ActionEditorWidget):
        """Supprime l'action dont la croix a été cliquée."""
        self.remove_action_widget(widget)
        self._schedule_preview()

    def remove_action_widget(self, widget: ActionEditorWidget):
        """Retire un widget d'action de la liste."""
        self.actions_layout.removeWidget(widget)
        widget.deleteLater()

    def get_action_widgets(self) -> list:
        """Liste des widgets d'action présents dans la liste."""
        return [
            self.actions_layout.itemAt(i).widget()
            for i in range(self.actions_layout.count())
            if self.actions_layout.itemAt(i).widget() is not None
            and isinstance(self.actions_layout.itemAt(i).widget(), ActionEditorWidget)
        ]

    def on_action_changed(self):
        """Une action a été modifiée : aperçu rafraîchi (avec délai anti-spam)."""
        self._schedule_preview()

    def _schedule_preview(self):
        """Programme un rafraîchissement de l'aperçu (250 ms de délai)."""
        self._preview_timer.start()

    def clear_actions(self):
        """Retire tous les widgets d'action."""
        for widget in self.get_action_widgets():
            self.remove_action_widget(widget)

    def reset_all_fields(self):
        """Réinitialise tous les champs du formulaire après confirmation."""
        reponse = QMessageBox.question(
            self,
            "Réinitialiser la fiche",
            "Effacer tous les champs (identité, statistiques, actions, "
            "scénario, équipement) ?\n\nCette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reponse != QMessageBox.StandardButton.Yes:
            return

        # Onglet Informations : identité, langues, description, scénario
        self.name_edit.clear()
        self.race_edit.clear()
        self.languages_edit.set_values([])
        self.description_edit.clear()
        self.scenario_edit.clear()

        # Onglet Statistiques : groupe aux valeurs par défaut
        self.party_size_spin.setValue(4)
        self.party_level_spin.setValue(2)
        self.difficulty_combo.setCurrentIndex(1)
        self._update_difficulty_label()

        # Chiffres : CA, PV, dés de vie, vitesse, maîtrise
        self.ac_spin.setValue(0)
        self.hp_spin.setValue(0)
        self.hit_dice_edit.clear()
        self.speed_edit.clear()
        if hasattr(self, "proficiency_spin"):
            self.proficiency_spin.setValue(0)

        # Caractéristiques
        for widget in (self.str_spin, self.dex_spin, self.con_spin,
                       self.int_spin, self.wis_spin, self.cha_spin):
            widget.setValue(0)

        # Pills : compétences, résistances, immunités
        self.skills_edit.set_values([])
        self.resistances_edit.set_values([])
        self.immunities_edit.set_values([])

        # Actions et équipement
        self.clear_actions()
        self.equipment_edit.clear()

        self.update_preview()

    def add_action(self):
        """Ajoute une nouvelle action (widget vide éditable)."""
        self.add_action_to_list(Action(name="", description=""))

    def _generate_actions_from_prompt(self):
        """Génère les actions décrites dans la zone de description libre."""
        prompt = self.actions_prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.information(
                self,
                "Description vide",
                "Décrivez d'abord brièvement les actions souhaitées "
                "dans la zone de texte à gauche du bouton.",
            )
            return
        if not self._check_backend():
            return

        monster = self.get_monster_from_form()

        try:
            actions = ai_generator.generate_actions(monster, actions_prompt=prompt)
            self.clear_actions()
            for action in actions:
                self.add_action_to_list(action)
            self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération : {str(e)}")

    def _check_backend(self) -> bool:
        """Vérifie le backend IA actif (local ou API), sinon guide l'utilisateur."""
        from config.config_manager import config_manager
        mode = config_manager.get_ai_mode()

        if mode == "api":
            if api_client.is_configured():
                return True
            QMessageBox.warning(
                self,
                "Configuration API incomplète",
                "Le mode API est sélectionné mais la clé API est manquante.\n\n"
                "Fichier > Configuration : renseignez la clé API,\n"
                "ou repassez sur le modèle local."
            )
            return False

        if local_model.is_available():
            return True

        from src.bootstrap import llama_cpp_available
        if not llama_cpp_available():
            switch = QMessageBox.question(
                self,
                "Modèle local indisponible",
                "llama-cpp-python n'est pas installé : le modèle local ne peut pas "
                "fonctionner.\n\n"
                "Basculer maintenant en mode API ?\n"
                "(Vous pourrez renseigner la clé API dans Fichier > Configuration.)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if switch == QMessageBox.StandardButton.Yes:
                from config.config_manager import config_manager as cm
                cm.set_ai_mode("api")
                return api_client.is_configured()
            return False

        info = local_model.get_model_info()
        retry = QMessageBox.question(
            self,
            "Modèle local manquant",
            "Le modèle IA local n'est pas encore prêt.\n\n"
            f"Modèle sélectionné : {info['label']}\n\n"
            "Voulez-vous le télécharger maintenant ?\n\n"
            "(Astuce : Fichier > Configuration permet aussi de basculer\n"
            "sur une API distante avec clé API.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if retry != QMessageBox.StandardButton.Yes:
            return False

        try:
            local_model.download()
            QMessageBox.information(self, "Téléchargement terminé",
                                     "Le modèle local a été téléchargé avec succès.")
            return True
        except ModelNotAvailableError as e:
            QMessageBox.critical(self, "Erreur de téléchargement", str(e))
            return False

    def _generate_actions(self):
        """Génère des actions complètes pour le monstre."""
        if not self._check_backend():
            return

        monster = self.get_monster_from_form()

        try:
            actions = ai_generator.generate_actions(monster)
            self.clear_actions()
            for action in actions:
                self.add_action_to_list(action)
            self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération : {str(e)}")

    def _generate_scenario(self):
        """Génère un scénario rapide basé sur les stats actuelles du monstre."""
        if not self._check_backend():
            return

        monster = self.get_monster_from_form()

        try:
            scenario = ai_generator.generate_scenario(
                monster,
                party_size=self.party_size_spin.value(),
                avg_level=self.party_level_spin.value(),
                difficulty=self.difficulty_combo.currentText(),
            )
            self.scenario_edit.setPlainText(scenario)
            self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération : {str(e)}")

    def generate_missing_fields(self):
        """Génère les champs manquants avec le modèle local/API.

        Remplit aussi la tab Statistiques : les champs vides (CA, PV, dés de
        vie, vitesse, caractéristiques, actions) sont complétés avec des
        valeurs équilibrées pour le CR courant, sans toucher aux champs que
        l'utilisateur a déjà remplis. Les langues sont proposées depuis la
        liste hardcodée DnD 5e.
        """
        monster = self.get_monster_from_form()

        # --- Passe de correction orthographique sur les champs remplis ---
        if self._check_backend():
            # (champ, texte actuel, application du corrigé)
            correctable = [
                ("description", monster.description or "",
                 lambda v: self.description_edit.setPlainText(v)),
                ("scenario", monster.scenario or "",
                 lambda v: self.scenario_edit.setPlainText(v)),
            ]
            for field, current, apply_correction in correctable:
                if not current:
                    continue
                try:
                    corrected = ai_generator.correct_text(monster, field, current)
                    if corrected and corrected != current:
                        apply_correction(corrected)
                except Exception:
                    continue

        # --- Race : remplie automatiquement depuis la liste hardcodée ---
        if not monster.race:
            self.race_edit.setText(self._suggest_race(monster))
            monster.race = self.race_edit.text()

        # --- Champs IA : uniquement s'il en manque, et backend disponible ---
        missing_fields = []
        if not monster.name:
            missing_fields.append("name")
        if not monster.description:
            missing_fields.append("description")

        if missing_fields:
            if self._check_backend():
                all_options = {}
                error_messages = []
                for field in missing_fields:
                    try:
                        options = ai_generator.generate_options(monster, field)
                        if options:
                            all_options[field] = options
                    except Exception as e:
                        error_messages.append(f"{field} : {str(e)}")
                        continue

                if all_options:
                    self.show_all_options_dialog(all_options)
                elif error_messages:
                    QMessageBox.warning(
                        self,
                        "Erreurs de génération",
                        "Impossible de générer les champs textuels :\n\n"
                        + "\n".join(error_messages)
                    )

        # --- Équilibrage complet des stats pour le CR courant ---
        self._fill_balanced_stats()

        # --- Actions : toujours régénérées via l'IA selon le contexte ---
        if self._check_backend():
            try:
                fresh = self.get_monster_from_form()
                actions = ai_generator.generate_actions(fresh)
                self.clear_actions()
                for action in actions:
                    self.add_action_to_list(action)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Génération des actions",
                    f"Les actions n'ont pas pu être régénérées :\n{e}\n\n"
                    "Les actions issues des tables DMG sont conservées."
                )

        self.update_preview()

    def _suggest_race(self, monster: Monster) -> str:
        """Devine une race DnD 5e depuis le nom et la description (liste hardcodée)."""
        haystack = (f"{monster.name or ''} {monster.description or ''}").lower()
        for race in DND5_RACES:
            base = race.split(" (")[0].lower()
            if base in haystack:
                return race
        return "Humain"

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

        intro_label = QLabel("Le modèle local a généré des options pour les champs manquants.\nSélectionnez une option pour chaque champ :")
        layout.addWidget(intro_label)

        self.field_combos = {}
        for field_name, options in all_options.items():
            field_layout = QHBoxLayout()

            label = QLabel({
                "name": "Nom", "race": "Race", "description": "Description",
            }.get(field_name, field_name) + " :")
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

    def export_to_png(self):
        """Exporte la fiche en PNG au style officiel DnD 5e."""
        monster = self.get_monster_from_form()

        if not monster.name:
            QMessageBox.warning(
                self,
                "Nom manquant",
                "Veuillez fournir un nom pour le PNJ/Monstre avant l'export."
            )
            return

        save_path = config_manager.get_save_path()
        default_filename = f"{monster.name.replace(' ', '_')}_fiche_DnD.png"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter en PNG",
            f"{save_path}/{default_filename}",
            "Images PNG (*.png)"
        )

        if not file_path:
            return

        try:
            png_exporter.export_to_png(monster, file_path)
            QMessageBox.information(
                self,
                "Export réussi",
                f"La fiche a été exportée avec succès vers :\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur d'export",
                f"Erreur lors de l'export PNG : {str(e)}"
            )

    def open_library(self):
        """Ouvre la bibliothèque de monstres (sauvegarder/charger/supprimer)."""
        from src.ui.monster_library import MonsterLibraryDialog
        dialog = MonsterLibraryDialog(
            get_current_monster=self.get_monster_from_form,
            load_monster_callback=self._load_monster_from_library,
            parent=self,
        )
        dialog.exec()

    def _load_monster_from_library(self, monster: Monster):
        """Charge un monstre depuis la bibliothèque."""
        self.set_monster_to_form(monster)
        self.update_preview()

    def on_generation_complete(self, monster: Monster):
        """Appelé lorsque la génération complète est terminée."""
        self.set_monster_to_form(monster)
        self.update_preview()
