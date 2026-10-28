"""
Mode « Rencontre » : génération de rencontres multi-monstres.

Deux approches complémentaires :
- Depuis la bibliothèque : sélection de monstres existants ; le système
  calcule les quantités pour atteindre la difficulté visée, et gère les
  cas où les CR sélectionnés sont trop hauts ou trop bas pour le budget
  (diagnostics + suggestions, le MJ garde la main).
- Génération complète : les fiches manquantes des monstres choisis
  sont générées comme en mode monstre (tables DMG + IA pour le texte).

Logique pure dans src/rules/encounter_builder.py ; persistance dans
src/library/encounter_manager.py ; ce module ne contient que l'UI.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QHeaderView, QInputDialog, QLabel,
    QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

from src.library.encounter_manager import encounter_manager
from src.rules.encounter import DIFFICULTIES
from src.rules.encounter_builder import (
    Encounter, EncounterMonster, build_auto_encounter, evaluate,
)
from src.rules.stat_builder import cr_display
from src.ui.styles import ACCENT_BUTTON_STYLE


class EncounterTab(QWidget):
    """Onglet de création de rencontres multi-monstres."""

    def __init__(self, parent_window):
        super().__init__()
        self._parent = parent_window
        self._monsters = []          # [EncounterMonster]
        self._monster_files = {}     # nom -> chemin de fiche bibliothèque

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        root.addLayout(layout, stretch=3)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(6)
        root.addLayout(right_panel, stretch=2)

        # --- Groupe cible + difficulté ---
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

        party_layout.addStretch()
        layout.addLayout(party_layout)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.summary_label)

        # --- Description libre de la rencontre (contexte pour le MJ) ---
        desc_label = QLabel(
            "Description de la rencontre (contexte optionnel — lieu, "
            "composition, armes, circonstances...) :"
        )
        desc_label.setStyleSheet("color: #90caf9;")

        desc_header = QHBoxLayout()
        desc_header.addWidget(desc_label, stretch=1)
        self.gen_description_btn = QPushButton("\u2728 G\u00e9n\u00e9rer")
        self.gen_description_btn.setToolTip(
            "G\u00e9n\u00e8re des propositions de description par IA "
            "\u00e0 partir des monstres de la rencontre"
        )
        self.gen_description_btn.clicked.connect(self._generate_description)
        desc_header.addWidget(self.gen_description_btn)
        layout.addLayout(desc_header)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            "Ex. : Embuscade de gobelins à l'arc dans un col montagneux au "
            "crépuscule ; leur chef brandit un totem tribal et crie des "
            "ordres en gobelin..."
        )
        self.description_edit.setFixedHeight(72)
        layout.addWidget(self.description_edit)

        # --- Table des monstres de la rencontre ---
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Monstre", "CR", "Quantité", "Fiche", "", ""]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 36)
        self.table.setColumnWidth(5, 36)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, stretch=1)

        # --- Boutons d'action sur la sélection ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        add_btn = QPushButton("＋ Ligne vide")
        add_btn.setToolTip(
            "Ajoute une ligne que vous remplissez à la main, ou via le "
            "bouton 📖 qui choisit un monstre dans la bibliothèque"
        )
        add_btn.clicked.connect(self._add_empty_row)
        btn_layout.addWidget(add_btn)

        library_btn = QPushButton("＋ Depuis la bibliothèque")
        library_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        library_btn.setToolTip(
            "Ajoute à la rencontre des monstres existants de la bibliothèque"
        )
        library_btn.clicked.connect(self._add_from_library)
        btn_layout.addWidget(library_btn)

        new_btn = QPushButton("✨ Générer un monstre")
        new_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        new_btn.setToolTip(
            "Génère directement une nouvelle fiche de monstre équilibrée "
            "pour la difficulté visée, sans passer par la bibliothèque"
        )
        new_btn.clicked.connect(self._generate_new_monster)
        btn_layout.addWidget(new_btn)

        random_btn = QPushButton("🎲 Générer tout de zéro")
        random_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        random_btn.setToolTip(
            "Part d'une rencontre vide : génère de nouveaux monstres par IA "
            "(CR équilibrés pour la difficulté visée), les sauvegarde dans la "
            "bibliothèque, puis calcule les quantités, la description et le "
            "scénario"
        )
        random_btn.clicked.connect(self._generate_full_from_scratch)
        btn_layout.addWidget(random_btn)

        full_btn = QPushButton("📖 Générer depuis la bibliothèque")
        full_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        full_btn.setToolTip(
            "Choisir des monstres de la bibliothèque puis générer fiches "
            "manquantes + quantités + description + scénario"
        )
        full_btn.clicked.connect(self._generate_full)
        btn_layout.addWidget(full_btn)

        counts_btn = QPushButton("⚖ Ajuster les quantités")
        counts_btn.setToolTip(
            "Recalcule les quantités pour atteindre la difficulté visée"
        )
        counts_btn.clicked.connect(self._adjust_counts)
        btn_layout.addWidget(counts_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # --- Scénario + persistance (bas de la colonne gauche) ---
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)

        scenario_btn = QPushButton("📝 Générer le scénario")
        scenario_btn.clicked.connect(self._generate_scenario)
        bottom_layout.addWidget(scenario_btn)

        save_btn = QPushButton("💾 Sauvegarder la rencontre")
        save_btn.clicked.connect(self._save_encounter)
        bottom_layout.addWidget(save_btn)

        load_btn = QPushButton("📂 Charger une rencontre")
        load_btn.clicked.connect(self._load_encounter)
        bottom_layout.addWidget(load_btn)

        export_pdf_btn = QPushButton("📄 Exporter les fiches (PDF)")
        export_pdf_btn.clicked.connect(self._export_pdfs)
        bottom_layout.addWidget(export_pdf_btn)

        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

        # --- Colonne droite : scénario de rencontre ---
        scenario_title = QLabel("Scénario de rencontre")
        scenario_title.setStyleSheet(
            "color: #90caf9; font-weight: bold;"
        )
        right_panel.addWidget(scenario_title)
        self.scenario_edit = QTextEdit()
        self.scenario_edit.setPlaceholderText(
            "Le scénario généré (contexte, disposition, tactique, "
            "récompense) s'affichera ici. Utilisez « 📝 Générer le "
            "scénario » — reste éditable et sauvegardé avec la rencontre."
        )
        right_panel.addWidget(self.scenario_edit, stretch=1)

        # --- Signaux temps réel ---
        self.table.itemChanged.connect(self.on_count_edited)
        self.party_size_spin.valueChanged.connect(self._refresh_summary)
        self.party_level_spin.valueChanged.connect(self._refresh_summary)
        self.difficulty_combo.currentIndexChanged.connect(self._refresh_summary)

        self._refresh_table()
        self._refresh_summary()

    # ------------------------------------------------------------------
    # Construction de l'objet Rencontre depuis l'UI
    # ------------------------------------------------------------------

    def current_encounter(self) -> Encounter:
        """Rencontre telle qu'affichée dans le tableau."""
        return Encounter(
            party_size=self.party_size_spin.value(),
            party_level=self.party_level_spin.value(),
            difficulty=self.difficulty_combo.currentData() or "medium",
            description=self.description_edit.toPlainText().strip(),
            scenario=self.scenario_edit.toPlainText().strip(),
            monsters=[EncounterMonster(m.name, m.challenge_rating, m.count)
                      for m in self._monsters],
        )

    # ------------------------------------------------------------------
    # Rafraîchissement temps réel (table + label de difficulté)
    # ------------------------------------------------------------------

    def _refresh_table(self):
        """Reconstruit le tableau des monstres de la rencontre."""
        self.table.blockSignals(True)
        self.table.setRowCount(len(self._monsters))
        for row, m in enumerate(self._monsters):
            name_item = QTableWidgetItem(m.name)
            name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            cr_item = QTableWidgetItem(cr_display(m.challenge_rating))
            cr_item.setFlags(cr_item.flags() | Qt.ItemFlag.ItemIsEditable)
            cr_item.setToolTip("CR éditable (ex. 1/4, 2)")
            self.table.setItem(row, 1, cr_item)
            count_item = QTableWidgetItem()
            count_item.setData(Qt.ItemDataRole.DisplayRole, m.count)
            count_item.setFlags(count_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, count_item)
            has_sheet = "✓" if m.name in self._monster_files else "—"
            self.table.setItem(row, 3, QTableWidgetItem(has_sheet))
            lib_btn = QPushButton("📖")
            lib_btn.setFixedSize(28, 24)
            lib_btn.setToolTip("Remplacer cette ligne par un monstre de la bibliothèque")
            lib_btn.clicked.connect(lambda _, r=row: self._pick_library_for_row(r))
            self.table.setCellWidget(row, 4, lib_btn)
            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(28, 24)
            remove_btn.setToolTip("Retirer cette ligne de la rencontre")
            remove_btn.setStyleSheet("color: #ff8888;")
            remove_btn.clicked.connect(lambda _, r=row: self._remove_row(r))
            self.table.setCellWidget(row, 5, remove_btn)
        self.table.blockSignals(False)
        self._refresh_summary()

    def _refresh_summary(self):
        """Met à jour le label coloré de difficulté réelle."""
        encounter = self.current_encounter()
        if not self._monsters:
            self.summary_label.setText(
                "Aucun monstre — ajoutez-en depuis la bibliothèque."
            )
            self.summary_label.setStyleSheet("color: #9aa0b4;")
            return
        info = evaluate(encounter)
        self.summary_label.setText(
            f"● {info['adjusted_xp']} PX ajustés (×{info['multiplier']}) / "
            f"budget {info['budget']} PX — difficulté réelle : "
            f"{info['actual_label']}"
        )
        self.summary_label.setStyleSheet(
            f"font-weight: bold; color: {info['actual_color']};"
        )

    def on_count_edited(self, item):
        """Applique l'édition manuelle d'une cellule (nom, CR ou quantité)."""
        row = item.row()
        if row < 0 or row >= len(self._monsters):
            return
        column = item.column()
        if column == 0:
            name = item.text().strip()
            old_name = self._monsters[row].name
            if name and name != old_name:
                if name in self._monster_files:
                    self._monsters[row].challenge_rating = None
                self._monsters[row].name = name
                if old_name in self._monster_files and old_name not in {
                    m.name for m in self._monsters
                }:
                    self._monster_files.pop(old_name, None)
            self._refresh_summary()
            return
        if column == 1:
            from src.rules.stat_builder import parse_cr
            cr = parse_cr(item.text())
            if cr is None:
                item.setText(cr_display(self._monsters[row].challenge_rating))
                return
            self._monsters[row].challenge_rating = cr
            item.setText(cr_display(cr))
            self._refresh_summary()
            return
        if column != 2:
            return
        try:
            count = max(1, int(item.data(Qt.ItemDataRole.DisplayRole)))
        except (TypeError, ValueError):
            count = 1
        self._monsters[row].count = count
        self._refresh_summary()

    # ------------------------------------------------------------------
    # Sélection depuis la bibliothèque
    # ------------------------------------------------------------------

    def _add_from_library(self):
        """Ouvre la bibliothèque en mode sélection multiple."""
        dialog = LibraryPickDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            for file, name, cr in dialog.selected:
                if any(m.name == name for m in self._monsters):
                    continue
                self._monsters.append(EncounterMonster(name, cr, 0))
                self._monster_files[name] = str(file)
            self._adjust_counts(silent=True)
            self._refresh_table()

    def _add_empty_row(self):
        """Ajoute une ligne vide à remplir à la main."""
        self._monsters.append(EncounterMonster("", None, 1))
        self._refresh_table()
        row = self.table.rowCount() - 1
        if row >= 0:
            self.table.editItem(self.table.item(row, 0))

    def _pick_library_for_row(self, row: int):
        """Remplit une ligne depuis un monstre choisi dans la bibliothèque."""
        if row < 0 or row >= len(self._monsters):
            return
        dialog = LibraryPickDialog(self, single=True)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if not dialog.selected:
            return
        file, name, cr = dialog.selected[0]
        old_name = self._monsters[row].name
        self._monsters[row] = EncounterMonster(name, cr, self._monsters[row].count or 1)
        self._monster_files[name] = str(file)
        if old_name and old_name in self._monster_files and old_name not in {
            m.name for m in self._monsters
        }:
            self._monster_files.pop(old_name, None)
        self._refresh_table()

    def _remove_row(self, row: int):
        """Retire la ligne demandée du tableau (bouton ✕ en bout de ligne)."""
        if row < 0 or row >= len(self._monsters):
            return
        name = self._monsters[row].name
        del self._monsters[row]
        self._monster_files.pop(name, None)
        self._refresh_table()

    # ------------------------------------------------------------------
    # Quantités automatiques + diagnostics
    # ------------------------------------------------------------------

    def _adjust_counts(self, silent: bool = False):
        """Recalcule les quantités pour la difficulté visée."""
        if not self._monsters:
            if not silent:
                QMessageBox.information(
                    self, "Aucun monstre",
                    "Ajoutez d'abord des monstres à la rencontre."
                )
            return
        encounter, issues = build_auto_encounter(
            self._monsters,
            self.party_size_spin.value(),
            self.party_level_spin.value(),
            self.difficulty_combo.currentData() or "medium",
        )
        self._monsters = encounter.monsters
        self._refresh_table()
        if issues and not silent:
            text = "\n\n".join(
                f"⚠ {i.message}\n" + "\n".join(f"  • {s}" for s in i.suggestions)
                for i in issues
            )
            QMessageBox.warning(
                self, "Sélection incompatible avec la difficulté", text
            )

    # ------------------------------------------------------------------
    # Génération complète (fiches manquantes + scénario)
    # ------------------------------------------------------------------

    def _generate_new_monster(self, silent: bool = False):
        """Génère directement une fiche de monstre pour la difficulté visée.

        Le CR cible est calculé comme en mode monstre : budget de PX de
        la difficulté → CR le plus proche. La fiche est construite par
        les tables DMG (stats) + IA pour nom/description/actions si le
        backend est disponible, puis sauvegardée dans la bibliothèque
        et ajoutée à la rencontre.
        """
        from src.ai.ai_generator import ai_generator
        from src.library.library_manager import library_manager
        from src.models.monster import Monster
        from src.rules.encounter import encounter_cr
        from src.rules.stat_builder import build_balanced_monster

        party_size = self.party_size_spin.value()
        party_level = self.party_level_spin.value()
        difficulty = self.difficulty_combo.currentData() or "medium"

        cr = encounter_cr(party_size, party_level, difficulty)
        monster = build_balanced_monster(cr, base=Monster(name=""))

        if self._parent._check_backend():
            try:
                options = ai_generator.generate_options(monster, "name")
                if options:
                    monster.name = options[0]
                options = ai_generator.generate_options(monster, "description")
                if options:
                    monster.description = options[0]
                monster.actions = ai_generator.generate_actions(monster)
            except Exception:
                pass

        if not monster.name:
            monster.name = f"Monstre CR {cr_display(cr)}"

        base_name = monster.name
        name = base_name
        suffix = 2
        while any(m.name == name for m in self._monsters):
            name = f"{base_name} {suffix}"
            suffix += 1
        monster.name = name

        try:
            library_manager.save(monster, name)
            self._monster_files[name] = str(library_manager.target_path(name))
        except OSError as e:
            if not silent:
                QMessageBox.critical(self, "Erreur", f"Échec de la sauvegarde :\n{e}")
            return

        self._monsters.append(EncounterMonster(name, monster.challenge_rating, 0))
        self._adjust_counts(silent=True)
        self._refresh_table()

    def _generate_full_from_scratch(self):
        """Génération complète de zéro : rencontre vidée, nouveaux monstres IA.

        Crée plusieurs monstres inédits (CR équilibrés pour la difficulté
        visée), les sauvegarde dans la bibliothèque, puis calcule les
        quantités, la description et le scénario.
        """
        confirm = QMessageBox.question(
            self, "Générer tout de zéro",
            "La rencontre actuelle sera remplacée par des monstres "
            "entièrement générés. Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        how_many, ok = QInputDialog.getInt(
            self, "Générer tout de zéro",
            "Nombre de types de monstres à générer :", 2, 1, 6, 1,
        )
        if not ok:
            return

        self._monsters = []
        self._monster_files = {}
        for _ in range(how_many):
            self._generate_new_monster(silent=True)

        self._adjust_counts(silent=True)
        if not self.description_edit.toPlainText().strip():
            self._generate_description(silent=True)
        if self._parent._check_backend():
            from src.ai.ai_generator import ai_generator
            encounter = self.current_encounter()
            try:
                scenario = ai_generator.generate_encounter_scenario(encounter)
                self._show_scenario(scenario)
            except Exception:
                pass
        self._refresh_table()

    def _generate_full(self):
        """Génération complète : fiches manquantes + quantités + scénario."""
        if not self._monsters:
            QMessageBox.information(
                self, "Aucun monstre",
                "Ajoutez d'abord des monstres depuis la bibliothèque."
            )
            return
        self._adjust_counts(silent=True)

        # Génère les fiches manquantes en mode monstre (une par une).
        from src.library.library_manager import library_manager
        from src.models.monster import Monster
        from src.rules.stat_builder import build_balanced_monster

        for m in self._monsters:
            if m.name in self._monster_files:
                continue
            # Fiche manquante : stats équilibrées pour le CR du monstre.
            monster = build_balanced_monster(m.challenge_rating or 0,
                                             base=Monster(name=m.name))
            try:
                library_manager.save(monster, m.name)
                self._monster_files[m.name] = str(library_manager.target_path(m.name))
            except OSError:
                pass

        # Description : générée par IA si le champ est vide.
        if not self.description_edit.toPlainText().strip():
            self._generate_description(silent=True)

        # Scénario de rencontre (IA).
        if self._parent._check_backend():
            from src.ai.ai_generator import ai_generator
            encounter = self.current_encounter()
            try:
                scenario = ai_generator.generate_encounter_scenario(
                    encounter
                )
                self._show_scenario(scenario)
            except Exception as e:
                QMessageBox.warning(
                    self, "Scénario non généré",
                    f"Le scénario de rencontre n'a pas pu être généré :\n{e}\n\n"
                    "Les fiches et quantités restent disponibles."
                )
        self._refresh_table()

    def _generate_description(self, silent: bool = False):
        """Génère des propositions de description par IA (champ vide).

        Affiche un dialogue de sélection : le MJ choisit une des
        propositions ou annule (le champ reste vide). En mode silencieux
        (génération complète), prend la première proposition sans dialog.
        """
        if not self._monsters:
            QMessageBox.information(
                self, "Aucun monstre",
                "Ajoutez d'abord des monstres : la description est générée "
                "à partir de la composition de la rencontre."
            )
            return
        if self.description_edit.toPlainText().strip():
            QMessageBox.information(
                self, "Description déjà remplie",
                "La description est déjà remplie. Effacez-la si vous voulez "
                "en générer une nouvelle."
            )
            return
        if not self._parent._check_backend():
            return

        from src.ai.ai_generator import ai_generator
        encounter = self.current_encounter()
        try:
            options = ai_generator.generate_encounter_description(encounter)
        except Exception as e:
            if not silent:
                QMessageBox.critical(
                    self, "Erreur",
                    f"La description n'a pas pu être générée :\n{e}"
                )
            return
        if not options:
            if not silent:
                QMessageBox.warning(
                    self, "Génération vide",
                    "Le modèle n'a pas produit de description exploitable."
                )
            return

        if silent:
            self.description_edit.setPlainText(options[0])
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Description de la rencontre")
        dialog.setMinimumWidth(450)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Sélectionnez une description générée :"))

        combo = QComboBox()
        combo.addItems(options)
        layout.addWidget(combo, stretch=1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        ok_btn = QPushButton("Appliquer")
        ok_btn.clicked.connect(dialog.accept)
        buttons.addWidget(ok_btn)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.description_edit.setPlainText(combo.currentText())

    def _generate_scenario(self):
        """Génère uniquement le scénario de la rencontre courante."""
        if not self._monsters:
            QMessageBox.information(
                self, "Aucun monstre",
                "Ajoutez d'abord des monstres à la rencontre."
            )
            return
        if not self._parent._check_backend():
            return
        from src.ai.ai_generator import ai_generator
        encounter = self.current_encounter()
        try:
            scenario = ai_generator.generate_encounter_scenario(
                encounter
            )
            self._show_scenario(scenario)
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur", f"Erreur lors de la génération : {e}"
            )

    def _show_scenario(self, scenario: str):
        """Affiche le scénario dans la colonne dédiée (éditable par le MJ)."""
        self.scenario_edit.setPlainText(scenario)

    # ------------------------------------------------------------------
    # Persistance + export
    # ------------------------------------------------------------------

    def _save_encounter(self):
        """Sauvegarde la rencontre dans la bibliothèque de rencontres."""
        if not self._monsters:
            QMessageBox.warning(
                self, "Rencontre vide",
                "Ajoutez des monstres avant de sauvegarder."
            )
            return
        name, ok = QInputDialog.getText(
            self, "Sauvegarder la rencontre", "Nom de la rencontre :"
        )
        if not ok or not name.strip():
            return
        encounter = self.current_encounter()
        encounter.name = name.strip()
        try:
            encounter_manager.save(encounter, name)
        except OSError as e:
            QMessageBox.critical(self, "Erreur", f"Échec de la sauvegarde :\n{e}")
            return
        QMessageBox.information(
            self, "Sauvegarde réussie",
            f"La rencontre « {encounter.name} » a été sauvegardée."
        )

    def _load_encounter(self):
        """Charge une rencontre sauvegardée."""
        dialog = EncounterPickDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            encounter = dialog.selected_encounter
            self._monsters = [EncounterMonster(m.name, m.challenge_rating, m.count)
                              for m in encounter.monsters]
            self._monster_files = {}
            from src.library.library_manager import library_manager
            for m in self._monsters:
                target = library_manager.target_path(m.name)
                if target.exists():
                    self._monster_files[m.name] = str(target)
            self.party_size_spin.setValue(encounter.party_size)
            self.party_level_spin.setValue(encounter.party_level)
            index = self.difficulty_combo.findData(encounter.difficulty)
            if index >= 0:
                self.difficulty_combo.setCurrentIndex(index)
            self.description_edit.setPlainText(encounter.description or "")
            self.scenario_edit.setPlainText(encounter.scenario or "")
            self._refresh_table()

    def _export_pdfs(self):
        """Exporte chaque fiche de monstre de la rencontre en PDF."""
        if not self._monsters:
            QMessageBox.information(
                self, "Aucun monstre",
                "Ajoutez d'abord des monstres à la rencontre."
            )
            return
        from src.library.library_manager import library_manager
        from src.models.monster import Monster
        from src.rules.stat_builder import build_balanced_monster
        from PySide6.QtWidgets import QFileDialog
        from config.config_manager import config_manager

        folder = QFileDialog.getExistingDirectory(
            self, "Dossier d'export des fiches",
            config_manager.get_save_path(),
        )
        if not folder:
            return
        exported = 0
        for m in self._monsters:
            target = library_manager.target_path(m.name)
            monster = None
            if target.exists():
                try:
                    monster = library_manager.load(target)
                except (OSError, ValueError):
                    monster = None
            if monster is None:
                monster = build_balanced_monster(
                    m.challenge_rating or 0, base=Monster(name=m.name)
                )
            path = f"{folder}/{m.name.replace(' ', '_')}_fiche_DnD.pdf"
            try:
                self._parent.monster_manager.export_to_pdf(monster, path)
                exported += 1
            except Exception:
                continue
        QMessageBox.information(
            self, "Export terminé",
            f"{exported} fiche(s) PDF exportée(s) vers :\n{folder}"
        )


class LibraryPickDialog(QDialog):
    """Sélection multi-monstres dans la bibliothèque."""

    def __init__(self, parent=None, single: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Choisir un monstre" if single else "Choisir des monstres")
        self.setMinimumSize(480, 400)
        self.selected = []   # [(file, name, cr)]

        from src.library.library_manager import library_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(QLabel(
            "Sélectionnez un monstre :" if single
            else "Sélectionnez un ou plusieurs monstres (Ctrl+clic) :"
        ))

        self.list = QTableWidget(0, 2)
        self.list.setHorizontalHeaderLabels(["Monstre", "CR"])
        self.list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.list.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection if single
            else QTableWidget.SelectionMode.MultiSelection
        )
        self.list.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.list.verticalHeader().setVisible(False)
        layout.addWidget(self.list, stretch=1)

        self._entries = library_manager.list_entries()
        for entry in self._entries:
            row = self.list.rowCount()
            self.list.insertRow(row)
            self.list.setItem(row, 0, QTableWidgetItem(entry.name))
            self.list.setItem(row, 1, QTableWidgetItem(
                cr_display(entry.challenge_rating)
            ))

        buttons = QHBoxLayout()
        buttons.addStretch()
        ok_btn = QPushButton("Choisir" if single else "Ajouter à la rencontre")
        ok_btn.clicked.connect(self._confirm)
        buttons.addWidget(ok_btn)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def _confirm(self):
        rows = sorted(set(i.row() for i in self.list.selectedIndexes()))
        self.selected = [
            (self._entries[row].file, self._entries[row].name,
             self._entries[row].challenge_rating)
            for row in rows
            if row < len(self._entries)
        ]
        if not self.selected:
            return
        self.accept()


class EncounterPickDialog(QDialog):
    """Choix d'une rencontre sauvegardée."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Charger une rencontre")
        self.setMinimumSize(420, 350)
        self.selected_encounter = None

        from PySide6.QtWidgets import QListWidget, QListWidgetItem

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(QLabel("Rencontres sauvegardées :"))

        self.list = QListWidget()
        layout.addWidget(self.list, stretch=1)

        self._entries = encounter_manager.list_entries()
        for entry in self._entries:
            self.list.addItem(QListWidgetItem(entry.label))

        buttons = QHBoxLayout()
        buttons.addStretch()
        load_btn = QPushButton("Charger")
        load_btn.clicked.connect(self._confirm)
        buttons.addWidget(load_btn)
        delete_btn = QPushButton("Supprimer")
        delete_btn.setStyleSheet("color: #ff8888;")
        delete_btn.clicked.connect(self._delete)
        buttons.addWidget(delete_btn)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def _confirm(self):
        row = self.list.currentRow()
        if row < 0 or row >= len(self._entries):
            return
        try:
            self.selected_encounter = encounter_manager.load(
                self._entries[row].file
            )
        except (OSError, ValueError) as e:
            QMessageBox.critical(self, "Erreur", f"Fichier illisible :\n{e}")
            return
        self.accept()

    def _delete(self):
        row = self.list.currentRow()
        if row < 0 or row >= len(self._entries):
            return
        confirm = QMessageBox.question(
            self, "Supprimer la rencontre",
            f"Supprimer « {self._entries[row].name} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                encounter_manager.delete(self._entries[row].file)
            except OSError:
                pass
            self._entries.pop(row)
            self.list.takeItem(row)
