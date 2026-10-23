"""Fenêtre principale de l'application MonsterGen (orchestrateur).

L'UI est compartimentée en widgets dédiés (src/ui/widgets/) et les
systèmes métier vivent dans des gestionnaires séparés :
- src/core/monster_manager.py : monstre courant + exports PNG/PDF,
- src/library/library_manager.py : persistance de la bibliothèque.
La fenêtre ne fait qu'assembler ces briques et orchestrer la
génération (règles + IA).
"""

import random
from typing import Optional

from PySide6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QHBoxLayout, QInputDialog, QLabel,
    QMainWindow, QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)
from PySide6.QtCore import QObject, Qt, QTimer, Signal

from config.config_manager import config_manager
from src.ai.ai_generator import ai_generator
from src.ai.api_client import api_client
from src.ai.local_model import local_model, ModelNotAvailableError
from src.core.monster_manager import MonsterManager
from src.models.monster import AbilityScores, Action, Monster, Skill
from src.rules.encounter import encounter_cr
from src.rules.stat_builder import build_balanced_monster
from src.ui.dnd_data import DND5_RACES
from src.ui.monster_library import (
    MonsterLibraryDialog, LibraryExportDialog, import_library_file,
)
from src.ui.styles import ACCENT_BUTTON_STYLE
from src.ui.widgets.actions_tab import ActionsTab
from src.ui.widgets.basic_tab import BasicTab
from src.ui.widgets.equipment_widget import EquipmentWidget
from src.ui.widgets.preview_panel import PreviewPanel
from src.ui.widgets.stats_tab import StatsTab


class SignalEmitter(QObject):
    """Émetteur de signaux pour la communication entre threads."""
    update_status = Signal(str)
    show_options = Signal(str, list)
    generation_complete = Signal(object)


class MainWindow(QMainWindow):
    """Fenêtre principale : assemble les onglets et orchestre la génération."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MonsterGen - Générateur de fiches DnD 5e")
        self.setGeometry(100, 100, 900, 700)

        self.monster_manager = MonsterManager(self)
        self.signal_emitter = SignalEmitter()
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(250)
        self._preview_timer.timeout.connect(self.update_preview)

        self.setup_ui()
        self.setup_connections()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

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

        main_layout.addWidget(self._create_form_panel(), stretch=1)

        self.preview_panel = PreviewPanel()
        main_layout.addWidget(self.preview_panel, stretch=1)

        self.update_backend_status()

    def _create_form_panel(self) -> QWidget:
        """Crée le panneau de formulaire (onglets + boutons de contrôle)."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        self.basic_tab = BasicTab()
        self.stats_tab = StatsTab()
        self.actions_tab = ActionsTab()
        self.equipment_widget = EquipmentWidget()

        tab_widget = QTabWidget()
        tab_widget.addTab(self.basic_tab, "Description")
        tab_widget.addTab(self.stats_tab, "Statistiques")
        tab_widget.addTab(self.actions_tab, "Actions")
        layout.addWidget(tab_widget)

        control_layout = QHBoxLayout()

        self.generate_btn = QPushButton("Compléter les champs")
        from PySide6.QtGui import QIcon
        self.generate_btn.setIcon(QIcon.fromTheme("system-run"))
        self.generate_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        control_layout.addWidget(self.generate_btn)

        self.reset_btn = QPushButton("Réinitialiser")
        self.reset_btn.setIcon(QIcon.fromTheme("document-new"))
        self.reset_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.reset_btn.setToolTip(
            "Effacer tous les champs : identité, stats, actions, scénario, équipement…"
        )
        self.reset_btn.clicked.connect(self.reset_all_fields)
        control_layout.addWidget(self.reset_btn)

        layout.addLayout(control_layout)

        return panel

    def setup_connections(self):
        """Configure les connexions des signaux entre widgets."""
        self.generate_btn.clicked.connect(self.generate_missing_fields)

        self.basic_tab.changed.connect(self._schedule_preview)
        self.basic_tab.gen_scenario_btn.clicked.connect(self._generate_scenario)
        self.basic_tab.party.difficulty_combo.currentIndexChanged.connect(
            self._schedule_preview
        )

        self.stats_tab.gen_stats_requested.connect(self._fill_balanced_stats)
        for editor in (self.stats_tab.skills_edit,
                       self.stats_tab.resistances_edit,
                       self.stats_tab.immunities_edit):
            editor.valuesChanged.connect(self._schedule_preview)

        self.actions_tab.generate_requested.connect(self._generate_actions)
        self.actions_tab.generate_from_prompt_requested.connect(
            self._generate_actions_from_prompt
        )
        self.actions_tab.add_requested.connect(
            lambda: self.actions_tab.add_action(Action(name="", description=""))
        )
        self.actions_tab.changed.connect(self._schedule_preview)

        self.equipment_widget.add_requested.connect(
            self.equipment_widget.add_item
        )
        self.equipment_widget.changed.connect(self._schedule_preview)

        self.preview_panel.refresh_requested.connect(self.update_preview)

        self.signal_emitter.show_options.connect(self.show_options_dialog)
        self.signal_emitter.generation_complete.connect(self.on_generation_complete)

    # ------------------------------------------------------------------
    # Statut du backend IA
    # ------------------------------------------------------------------

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
            info = local_model.get_model_info()
            if local_model.is_available():
                status = "prêt"
                bg = "#1e3a24"
                fg = "#42a5f5"
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

    # ------------------------------------------------------------------
    # Aperçu
    # ------------------------------------------------------------------

    def _schedule_preview(self):
        """Programme un rafraîchissement de l'aperçu (250 ms de délai)."""
        self._preview_timer.start()

    def update_preview(self):
        """Met à jour l'aperçu avec les données actuelles du formulaire."""
        monster = self.get_monster_from_form()
        self.preview_panel.update_preview(monster)

    def refresh_preview(self):
        """Rafraîchit l'aperçu de la fiche."""
        self.update_preview()

    # ------------------------------------------------------------------
    # Conversion formulaire <-> monstre
    # ------------------------------------------------------------------

    def _get_selected_cr(self) -> Optional[float]:
        """CR dérivé du groupe (joueurs, niveau moyen, difficulté choisie)."""
        party = self.basic_tab.party
        return encounter_cr(
            party.party_size_spin.value(),
            party.party_level_spin.value(),
            party.selected_difficulty(),
        )

    def get_monster_from_form(self) -> Monster:
        """Récupère les données du monstre depuis le formulaire."""
        monster = Monster()
        basic = self.basic_tab
        stats = self.stats_tab

        monster.name = basic.name_edit.text().strip() or None
        monster.race = basic.race_edit.text().strip() or None
        monster.description = basic.description_edit.toPlainText().strip() or None
        monster.scenario = basic.scenario_edit.toPlainText().strip()

        languages_text = basic.languages_edit.toPlainText().strip()
        if languages_text:
            monster.languages = [
                l.strip() for l in languages_text.split(",") if l.strip()
            ]

        monster.armor_class = stats.ac_spin.value() if stats.ac_spin.value() > 0 else None
        monster.hit_points = stats.hp_spin.value() if stats.hp_spin.value() > 0 else None
        monster.hit_dice = stats.hit_dice_edit.text().strip() or None
        monster.speed = stats.speed_edit.text().strip() or None

        party = basic.party
        monster.challenge_rating = self._get_selected_cr()
        monster.party_size = party.party_size_spin.value()
        monster.party_level = party.party_level_spin.value()
        monster.difficulty = party.selected_difficulty()
        prof_value = stats.proficiency_spin.value()
        monster.proficiency_bonus = prof_value if prof_value > 0 else None

        monster.ability_scores = AbilityScores(
            **{
                k: (w.value() if w.value() > 0 else 10)
                for k, w in stats.ability_spins().items()
            }
        )

        monster.skills = [
            Skill(name=name, ability="", proficiency=True)
            for name in stats.skills_edit.get_values()
        ]
        monster.damage_resistances = stats.resistances_edit.get_values()
        monster.damage_immunities = stats.immunities_edit.get_values()

        monster.actions = self.actions_tab.get_actions()
        monster.notes = self.equipment_widget.to_notes() or None

        self.monster_manager.update_monster(monster)
        return monster

    def set_monster_to_form(self, monster: Monster, keep_scenario: bool = False):
        """Remplit le formulaire avec les données du monstre."""
        basic = self.basic_tab
        stats = self.stats_tab

        basic.name_edit.setText(monster.name or "")
        basic.race_edit.setText(monster.race or "")
        basic.description_edit.setPlainText(monster.description or "")

        basic.languages_edit.setPlainText(", ".join(monster.languages))

        stats.ac_spin.setValue(monster.armor_class or 0)
        stats.hp_spin.setValue(monster.hit_points or 0)
        stats.hit_dice_edit.setText(monster.hit_dice or "")
        stats.speed_edit.setText(monster.speed or "")
        stats.proficiency_spin.setValue(monster.proficiency_bonus or 0)

        for attr, widget in stats.ability_spins().items():
            widget.setValue(getattr(monster.ability_scores, attr))

        stats.skills_edit.set_values([
            sk.name for sk in monster.skills if sk.proficiency
        ])
        stats.resistances_edit.set_values(monster.damage_resistances)
        stats.immunities_edit.set_values(monster.damage_immunities)

        self.actions_tab.set_actions(monster.actions)

        self.equipment_widget.set_notes(monster.notes or "")

        basic.party.set_party(
            monster.party_size, monster.party_level, monster.difficulty
        )

        if not keep_scenario:
            basic.scenario_edit.setPlainText(monster.scenario or "")

        self.monster_manager.set_monster(monster)

    # ------------------------------------------------------------------
    # Réinitialisation
    # ------------------------------------------------------------------

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

        basic = self.basic_tab
        stats = self.stats_tab

        basic.name_edit.clear()
        basic.race_edit.clear()
        basic.languages_edit.set_values([])
        basic.description_edit.clear()
        basic.scenario_edit.clear()

        basic.party.reset()

        stats.ac_spin.setValue(0)
        stats.hp_spin.setValue(0)
        stats.hit_dice_edit.clear()
        stats.speed_edit.clear()
        stats.proficiency_spin.setValue(0)
        for widget in stats.ability_spins().values():
            widget.setValue(0)

        stats.skills_edit.set_values([])
        stats.resistances_edit.set_values([])
        stats.immunities_edit.set_values([])

        self.actions_tab.set_actions([])
        self.equipment_widget.set_notes("")

        self.update_preview()

    # ------------------------------------------------------------------
    # Génération (règles + IA)
    # ------------------------------------------------------------------

    def _fill_balanced_stats(self):
        """Remplit directement un monstre équilibré pour le CR choisi."""
        cr = self._get_selected_cr()
        if cr is None:
            return

        monster = build_balanced_monster(cr, base=self.get_monster_from_form())
        self.set_monster_to_form(monster, keep_scenario=True)
        self.update_preview()

    def _check_backend(self) -> bool:
        """Vérifie le backend IA actif (local ou API), sinon guide
        l'utilisateur."""
        mode = config_manager.get_ai_mode()

        if mode == "api":
            if api_client.is_configured():
                return True
            QMessageBox.warning(
                self,
                "Configuration API incomplète",
                "Le mode API est sélectionné mais la clé API est manquante.\n\n"
                "Configuration : renseignez la clé API,\n"
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
                "(Vous pourrez renseigner la clé API dans Configuration.)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if switch == QMessageBox.StandardButton.Yes:
                config_manager.set_ai_mode("api")
                return api_client.is_configured()
            return False

        info = local_model.get_model_info()
        retry = QMessageBox.question(
            self,
            "Modèle local manquant",
            "Le modèle IA local n'est pas encore prêt.\n\n"
            f"Modèle sélectionné : {info['label']}\n\n"
            "Voulez-vous le télécharger maintenant ?\n\n"
            "(Astuce : Configuration permet aussi de basculer\n"
            "sur une API distante avec clé API.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if retry != QMessageBox.StandardButton.Yes:
            return False

        try:
            local_model.download()
            QMessageBox.information(
                self, "Téléchargement terminé",
                "Le modèle local a été téléchargé avec succès."
            )
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
            self.actions_tab.set_actions(actions)
            self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération : {str(e)}")

    def _generate_actions_from_prompt(self):
        """Génère les actions décrites dans la zone de description libre."""
        prompt = self.actions_tab.actions_prompt_edit.toPlainText().strip()
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
            self.actions_tab.set_actions(actions)
            self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération : {str(e)}")

    def _generate_scenario(self):
        """Génère un scénario rapide basé sur les stats actuelles du monstre."""
        if not self._check_backend():
            return

        monster = self.get_monster_from_form()
        party = self.basic_tab.party

        try:
            scenario = ai_generator.generate_scenario(
                monster,
                party_size=party.party_size_spin.value(),
                avg_level=party.party_level_spin.value(),
                difficulty=party.difficulty_combo.currentText(),
            )
            self.basic_tab.scenario_edit.setPlainText(scenario)
            self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération : {str(e)}")

    def generate_missing_fields(self):
        """Complète les champs manquants (bouton « Compléter les champs »).

        La race est choisie depuis la liste hardcodée des races DnD 5e
        (détection dans le texte, sinon hasard — sans IA). Le nom et la
        description sont générés par IA si le backend est disponible.
        Les stats sont ensuite équilibrées pour le CR courant, et les
        langues suggérées en dernier selon la race et l'INT finales.
        """
        monster = self.get_monster_from_form()

        # --- Passe de correction orthographique sur les champs remplis ---
        if self._check_backend():
            correctable = [
                ("description", monster.description or "",
                 lambda v: self.basic_tab.description_edit.setPlainText(v)),
                ("scenario", monster.scenario or "",
                 lambda v: self.basic_tab.scenario_edit.setPlainText(v)),
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
            self.basic_tab.race_edit.setText(self._suggest_race(monster))
            monster.race = self.basic_tab.race_edit.text()

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
                self.actions_tab.set_actions(actions)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Génération des actions",
                    f"Les actions n'ont pas pu être régénérées :\n{e}\n\n"
                    "Les actions issues des tables DMG sont conservées."
                )

        # --- Langues : en tout dernier, pour s'adapter à la race et aux
        # stats choisies/générées au cours du remplissage (le fallback
        # dépend de l'INT équilibrée) ---
        fresh = self.get_monster_from_form()
        if not fresh.languages:
            self.basic_tab.languages_edit.set_values(self._suggest_languages(fresh))

        self.update_preview()

    def _suggest_race(self, monster: Monster) -> str:
        """Race DnD 5e pour le monstre : détectée dans le nom/description
        si mentionnée, sinon tirée au hasard dans la liste hardcodée."""
        haystack = (f"{monster.name or ''} {monster.description or ''}").lower()
        for race in DND5_RACES:
            base = race.split(" (")[0].lower()
            if base in haystack:
                return race
        return random.choice(DND5_RACES)

    def _suggest_languages(self, monster: Monster) -> list:
        """Langues DnD 5e cohérentes avec la race et l'alignement du monstre."""
        race = (monster.race or "").lower()
        desc = (monster.description or "").lower()

        race_languages = {
            "drow": ["Elfique", "Commun", "Chtonien"],
            "elfe noir": ["Elfique", "Commun", "Chtonien"],
            "elfe": ["Commun", "Elfique"],
            "haut-elfe": ["Commun", "Elfique"],
            "elfe des bois": ["Commun", "Elfique"],
            "nain": ["Commun", "Nain"],
            "gnome": ["Commun", "Gnome"],
            "halfelin": ["Commun"],
            "dem-orc": ["Commun", "Orque"],
            "orc": ["Orque"],
            "tiefling": ["Commun", "Infernal"],
            "drakéide": ["Commun", "Draconique"],
            "gobelin": ["Gobelin"],
            "hobgobelin": ["Gobelin"],
            "bugbear": ["Gobelin"],
            "kobold": ["Draconique"],
            "gnoll": ["Abyssal"],
            "homme-lézard": ["Draconique"],
            "ogre": ["Commun", "Géant"],
            "troll": ["Géant"],
            "géant": ["Géant"],
            "squelette": ["—"],
            "zombie": ["—"],
            "goule": ["Commun"],
            "liche": ["Commun"],
            "diable": ["Infernal"],
            "démon": ["Abyssal"],
            "ange": ["Céleste"],
            "fée": ["Sylvestre"],
            "dryade": ["Sylvestre", "Elfique"],
            "satyre": ["Sylvestre", "Commun"],
            "méduse": ["Commun"],
            "minotaure": ["Abyssal"],
            "hydre": ["—"],
            "basilic": ["—"],
            "dragon": ["Draconique", "Commun"],
            "wyverne": ["Draconique"],
            "griffon": ["Commun", "Auran"],
            "sphinx": ["Commun"],
            "aboleth": ["Aquatique", "Chtonien"],
            "spectre": ["—"],
        }

        for key, languages in race_languages.items():
            if key in race or key in desc:
                return languages

        intelligence = monster.ability_scores.intelligence
        if intelligence >= 8:
            return ["Commun"]
        # INT animale : pas de langage, mais le champ reste explicite
        return ["—"]

    # ------------------------------------------------------------------
    # Dialogues d'options IA
    # ------------------------------------------------------------------

    def show_options_dialog(self, field_name: str, options: list):
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

    def show_all_options_dialog(self, all_options: dict):
        """Affiche une boîte de dialogue unique pour tous les champs manquants."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Sélectionner les options générées")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        intro_label = QLabel(
            "Le modèle local a généré des options pour les champs manquants.\n"
            "Sélectionnez une option pour chaque champ :"
        )
        layout.addWidget(intro_label)

        field_combos = {}
        for field_name, options in all_options.items():
            field_layout = QHBoxLayout()

            label = QLabel({
                "name": "Nom", "description": "Description",
            }.get(field_name, field_name) + " :")
            field_layout.addWidget(label)

            combo = QComboBox()
            combo.addItems(options)
            field_combos[field_name] = combo
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
            for field_name, combo in field_combos.items():
                selected_option = combo.currentText()
                if selected_option:
                    self.set_field_value(field_name, selected_option)

    def set_field_value(self, field_name: str, value: str):
        """Définit la valeur d'un champ dans le formulaire."""
        basic = self.basic_tab
        stats = self.stats_tab

        field_mapping = {
            "name": lambda v: basic.name_edit.setText(v),
            "description": lambda v: basic.description_edit.setPlainText(v),
            "hit_dice": lambda v: stats.hit_dice_edit.setText(v),
            "speed": lambda v: stats.speed_edit.setText(v),
            "languages": lambda v: basic.languages_edit.setPlainText(v),
        }

        if field_name in field_mapping:
            field_mapping[field_name](value)
            return

        numeric_fields = {
            "armor_class": (stats.ac_spin, int),
            "hit_points": (stats.hp_spin, int),
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
                    for idx, widget in enumerate(stats.ability_spins().values()):
                        widget.setValue(int(parts[idx].strip()))
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Exports (délégués au MonsterManager)
    # ------------------------------------------------------------------

    def _export_monster(self, format_key: str, title: str, filter_str: str):
        """Exporte le monstre courant via le MonsterManager."""
        monster = self.get_monster_from_form()

        if not monster.name:
            QMessageBox.warning(
                self,
                "Nom manquant",
                "Veuillez fournir un nom pour le PNJ/Monstre avant l'export."
            )
            return

        save_path = config_manager.get_save_path()
        default_filename = f"{monster.name.replace(' ', '_')}_fiche_DnD.{format_key}"
        file_path, _ = QFileDialog.getSaveFileName(
            self, title, f"{save_path}/{default_filename}", filter_str
        )

        if not file_path:
            return

        try:
            if format_key == "pdf":
                self.monster_manager.export_to_pdf(monster, file_path)
            else:
                self.monster_manager.export_to_png(monster, file_path)
            QMessageBox.information(
                self,
                "Export réussi",
                f"La fiche a été exportée avec succès vers :\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur d'export",
                f"Erreur lors de l'export {format_key.upper()} : {str(e)}"
            )

    def export_to_pdf(self):
        """Exporte le monstre en PDF."""
        self._export_monster("pdf", "Exporter en PDF", "Fichiers PDF (*.pdf)")

    def export_to_png(self):
        """Exporte la fiche en PNG au style officiel DnD 5e."""
        self._export_monster("png", "Exporter en PNG", "Images PNG (*.png)")

    # ------------------------------------------------------------------
    # Bibliothèque (déléguée au LibraryManager)
    # ------------------------------------------------------------------

    def open_library(self):
        """Ouvre la bibliothèque de monstres (sauvegarder/charger/supprimer)."""
        dialog = MonsterLibraryDialog(
            get_current_monster=self.get_monster_from_form,
            load_monster_callback=self._load_monster_from_library,
            parent=self,
        )
        dialog.exec()

    def export_library(self):
        """Ouvre le dialogue d'export de la bibliothèque vers un fichier."""
        dialog = LibraryExportDialog(parent=self)
        dialog.exec()

    def import_library(self):
        """Importe des monstres depuis un fichier d'export de bibliothèque."""
        import_library_file(self)

    def save_to_library(self):
        """Sauvegarde le monstre courant dans la bibliothèque, sans ouvrir
        l'interface de gestion (nom de fichier éditable, confirmation en
        cas d'écrasement)."""
        from src.library.library_manager import library_manager

        monster = self.get_monster_from_form()
        if not monster.name:
            QMessageBox.warning(
                self, "Nom manquant",
                "Le monstre actuel n'a pas de nom. Donnez-lui un nom avant "
                "de le sauvegarder."
            )
            return

        filename, ok = QInputDialog.getText(
            self, "Sauvegarder le monstre",
            "Nom de la sauvegarde :",
            text=monster.name,
        )
        if not ok or not filename.strip():
            return

        target = library_manager.target_path(filename)
        if target.exists():
            confirm = QMessageBox.question(
                self, "Écraser la sauvegarde",
                f"Une sauvegarde « {filename.strip()} » existe déjà.\n"
                "Voulez-vous l'écraser ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

        try:
            library_manager.save(monster, filename)
        except OSError as e:
            QMessageBox.critical(self, "Erreur", f"Échec de la sauvegarde :\n{e}")
            return

        QMessageBox.information(
            self, "Sauvegarde réussie",
            f"« {monster.name} » a été sauvegardé dans la bibliothèque."
        )

    def _load_monster_from_library(self, monster: Monster):
        """Charge un monstre depuis la bibliothèque."""
        self.set_monster_to_form(monster)
        self.update_preview()

    def on_generation_complete(self, monster: Monster):
        """Appelé lorsque la génération complète est terminée."""
        self.set_monster_to_form(monster)
        self.update_preview()
