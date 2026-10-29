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
from src.ui.widgets.row_buttons import RowButton, RowButtons
from src.ui.widgets.monster_edit_dialog import MonsterEditDialog


class EncounterTab(QWidget):
    """Onglet de création de rencontres multi-monstres."""

    def __init__(self, parent_window):
        super().__init__()
        self._parent = parent_window
        self._monsters = []          # [EncounterMonster]
        self._monster_files = {}     # nom -> chemin de fiche bibliothèque
        self._temp_monsters = {}     # nom -> Monster temporaire (non bibliothèque)
        self._creature_traits = {}   # nom -> caractéristiques extraites de la description

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

        layout.addWidget(desc_label)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            "Ex. : Embuscade de gobelins à l'arc dans un col montagneux au "
            "crépuscule ; leur chef brandit un totem tribal et crie des "
            "ordres en gobelin..."
        )
        self.description_edit.setFixedHeight(72)
        layout.addWidget(self.description_edit)

        # --- Boutons de génération (au-dessus de la liste) ---
        gen_bar = QHBoxLayout()
        gen_bar.setSpacing(8)

        random_btn = QPushButton("\U0001F3B2 G\u00e9n\u00e9rer")
        random_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        random_btn.setToolTip(
            "Si une description est saisie : compose la rencontre depuis "
            "cette description (cr\u00e9atures, CR et quantit\u00e9s conformes au "
            "texte) pour la difficult\u00e9 vis\u00e9e. Sinon : g\u00e9n\u00e8re des monstres "
            "in\u00e9dits \u00e9quilibr\u00e9s pour la difficult\u00e9, puis quantit\u00e9s, "
            "description et sc\u00e9nario. Les fiches restent temporaires "
            "jusqu'\u00e0 int\u00e9gration volontaire."
        )
        random_btn.clicked.connect(self._generate_full_from_scratch)
        gen_bar.addWidget(random_btn)

        full_btn = QPushButton("\U0001F4D6 G\u00e9n\u00e9rer depuis la biblioth\u00e8que")
        full_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        full_btn.setToolTip(
            "Choisir des monstres de la biblioth\u00e8que puis g\u00e9n\u00e9rer fiches "
            "manquantes + quantit\u00e9s + description + sc\u00e9nario"
        )
        full_btn.clicked.connect(self._generate_full)
        gen_bar.addWidget(full_btn)

        gen_bar.addStretch()
        layout.addLayout(gen_bar)

        # --- Table des monstres de la rencontre ---
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Monstre", "CR", "Quantité", "Fiche", ""]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 56)
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

        new_btn = QPushButton("✨ Générer un monstre")
        new_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        new_btn.setToolTip(
            "Génère directement une nouvelle fiche de monstre équilibrée "
            "pour la difficulté visée, sans passer par la bibliothèque"
        )
        new_btn.clicked.connect(self._generate_new_monster)
        btn_layout.addWidget(new_btn)

        counts_btn = QPushButton("⚖ Ajuster les quantités")
        counts_btn.setToolTip(
            "Recalcule les quantités pour atteindre la difficulté visée"
        )
        counts_btn.clicked.connect(self._adjust_counts)
        btn_layout.addWidget(counts_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # --- Persistance (bas de la colonne gauche) ---
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)

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

        scenario_btn = QPushButton("📝 Générer le scénario")
        scenario_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        scenario_btn.clicked.connect(self._generate_scenario)
        right_panel.addWidget(scenario_btn)

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
            if m.name in self._monster_files:
                has_sheet = "✓"
            elif m.name in self._temp_monsters:
                has_sheet = "temp"
            else:
                has_sheet = "—"
            self.table.setItem(row, 3, QTableWidgetItem(has_sheet))
            edit_btn = RowButton(
                "📝", "Éditer la fiche de ce monstre",
                normal_color="#9aa0b4", hover_color="#90caf9",
            )
            edit_btn.clicked.connect(
                lambda *args, r=row: self._edit_row_monster(r)
            )
            lib_btn = RowButton(
                "📖",
                "Remplacer cette ligne par un monstre de la bibliothèque",
                normal_color="#9aa0b4", hover_color="#90caf9",
            )
            lib_btn.clicked.connect(
                lambda *args, r=row: self._pick_library_for_row(r)
            )
            remove_btn = RowButton(
                "✕", "Retirer cette ligne de la rencontre",
                normal_color="#9aa0b4", hover_color="#ff8888",
            )
            remove_btn.clicked.connect(
                lambda *args, r=row: self._remove_row(r)
            )
            self.table.setCellWidget(
                row, 4, RowButtons([edit_btn, lib_btn, remove_btn])
            )
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
                if old_name in self._temp_monsters:
                    self._temp_monsters[name] = self._temp_monsters.pop(
                        old_name
                    )
                    self._temp_monsters[name].name = name
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
        dialog = LibraryPickDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if not dialog.selected:
            return
        file, name, cr = dialog.selected[0]
        old_name = self._monsters[row].name
        self._monsters[row] = EncounterMonster(name, cr, self._monsters[row].count or 1)
        self._monster_files[name] = str(file)
        if old_name and old_name in self._temp_monsters and old_name not in {
            m.name for m in self._monsters
        }:
            self._temp_monsters.pop(old_name, None)
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
        if name not in {m.name for m in self._monsters}:
            self._temp_monsters.pop(name, None)
        self._refresh_table()

    # ------------------------------------------------------------------
    # Fiches temporaires : édition + intégration bibliothèque
    # ------------------------------------------------------------------

    def _edit_row_monster(self, row: int):
        """Ouvre la fiche du monstre de la ligne en édition pure.

        Fiche temporaire : éditée en mémoire. « Intégrer dans la
        bibliothèque » la sauvegarde via le même dialogue et retire le
        statut temporaire. Fiche bibliothèque : chargée puis rééditable
        de la même façon.
        """
        if row < 0 or row >= len(self._monsters):
            return
        name = self._monsters[row].name
        if not name:
            QMessageBox.information(
                self, "Fiche", "Donnez d'abord un nom au monstre."
            )
            return

        monster = self._temp_monsters.get(name)
        if monster is None:
            file = self._monster_files.get(name)
            if file:
                from src.library.library_manager import library_manager
                from pathlib import Path
                try:
                    monster = library_manager.load(Path(file))
                except (OSError, ValueError) as e:
                    QMessageBox.critical(
                        self, "Erreur", f"Fiche illisible :\n{e}"
                    )
                    return
            else:
                from src.models.monster import Monster
                from src.rules.stat_builder import build_balanced_monster
                monster = build_balanced_monster(
                    self._monsters[row].challenge_rating or 0,
                    base=Monster(name=name),
                )
                self._temp_monsters[name] = monster

        # Une fiche de la bibliothèque est gelée : les modifications ne
        # s'appliquent (fiche + ligne) que si le MJ choisit explicitement
        # « Intégrer dans la bibliothèque » (écrasement volontaire).
        # Sans cela, l'édition est annulée et la fiche d'origine reste
        # intacte sur disque comme en mémoire.
        is_library = name in self._monster_files and name not in self._temp_monsters

        dialog = MonsterEditDialog(monster, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        if is_library and not dialog.integrate_requested:
            self._refresh_table()
            return

        dialog.apply_to_monster(monster)

        new_name = monster.name
        if new_name != name:
            if any(m.name == new_name for m in self._monsters
                   if m.name != name):
                QMessageBox.warning(
                    self, "Nom déjà pris",
                    f"Un monstre « {new_name} » est déjà dans la rencontre. "
                    "Le nom de la fiche est conservé mais pas la ligne."
                )
            else:
                self._monsters[row].name = new_name
                self._temp_monsters = {
                    (new_name if k == name else k): v
                    for k, v in self._temp_monsters.items()
                }
        self._monsters[row].challenge_rating = monster.challenge_rating

        if dialog.integrate_requested:
            from src.library.library_manager import library_manager
            try:
                final_name = self._monsters[row].name
                library_manager.save(monster, final_name)
                self._monster_files[final_name] = str(
                    library_manager.target_path(final_name)
                )
                self._temp_monsters.pop(final_name, None)
            except OSError as e:
                QMessageBox.critical(
                    self, "Erreur", f"Échec de la sauvegarde :\n{e}"
                )
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

    def _generate_from_description(self):
        """Pipeline description -> rencontre, en trois phases ordonn\u00e9es :

        1. D\u00e9corticage IA de la description : races, nombre d'exemplaires
           de chacune, caract\u00e9ristiques notables.
        2. Assignation des CR individuels par les tables DMG : les CR
           sont calcul\u00e9s APR\u00c8S connaissance des quantit\u00e9s pour que le
           total (PX ajust\u00e9s, multiplicateur de groupe compris) tombe
           dans la bande de la difficult\u00e9 demand\u00e9e.
        3. Ajout au tableau : les fiches existantes de la biblioth\u00e8que
           sont r\u00e9utilis\u00e9es, les autres sont g\u00e9n\u00e9r\u00e9es comme
           temporaires \u00e9quilibr\u00e9es pour leur CR.
        """
        description = self.description_edit.toPlainText().strip()
        if not description:
            QMessageBox.information(
                self, "Description vide",
                "\u00c9crivez d'abord une description de la rencontre : "
                "c'est elle qui d\u00e9termine les cr\u00e9atures."
            )
            return
        if not self._parent._check_backend():
            return

        # --- Phase 1 : d\u00e9corticage de la description (races + nombres) ---
        from src.ai.ai_generator import ai_generator
        try:
            creatures = ai_generator.extract_creatures_from_description(
                description
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur",
                f"La description n'a pas pu \u00eatre d\u00e9cortiqu\u00e9e :\n{e}"
            )
            return

        # --- Phase 2 : CR individuels pour matcher la difficult\u00e9 ---
        from src.rules.encounter_builder import assign_crs
        party_size = self.party_size_spin.value()
        party_level = self.party_level_spin.value()
        difficulty = self.difficulty_combo.currentData() or "medium"
        counts = [c["count"] for c in creatures]
        crs = assign_crs(counts, party_size, party_level, difficulty)

        # --- Phase 3 : ajout au tableau + fiches ---
        from src.library.library_manager import library_manager
        self._monsters = []
        self._monster_files = {}
        self._temp_monsters = {}
        self._creature_traits = {
            c["name"]: c["traits"] for c in creatures if c.get("traits")
        }
        for creature, cr in zip(creatures, crs):
            name = creature["name"]
            if any(m.name == name for m in self._monsters):
                self._monsters[
                    next(i for i, m in enumerate(self._monsters)
                         if m.name == name)
                ].count += creature["count"]
                continue
            self._monsters.append(
                EncounterMonster(name, cr, creature["count"])
            )
            target = library_manager.target_path(name)
            if target.exists():
                self._monster_files[name] = str(target)
        self._refresh_table()

        # Fiches manquantes : temporaires, \u00e9quilibr\u00e9es pour leur CR.
        self._generate_full(keep_counts=True)

    def _generate_new_monster(self, silent: bool = False, cr=None):
        """Génère une fiche de monstre temporaire pour la difficulté visée.

        Le CR cible est calculé comme en mode monstre : budget de PX de
        la difficulté → CR le plus proche. La fiche est construite par
        les tables DMG (stats) + IA pour nom/description/actions si le
        backend est disponible, puis ajoutée à la rencontre. Elle reste
        temporaire : le MJ l'intègre à la bibliothèque depuis la fiche
        (bouton 📝) s'il le souhaite.

        cr : CR cible explicite (sinon calculé depuis la difficulté).
        """
        from src.ai.ai_generator import ai_generator
        from src.models.monster import Monster
        from src.rules.encounter import budget_to_cr, party_xp_budget
        from src.rules.stat_builder import build_balanced_monster

        if cr is None:
            cr = budget_to_cr(party_xp_budget(
                self.party_size_spin.value(),
                self.party_level_spin.value(),
                self.difficulty_combo.currentData() or "medium",
            ))
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

        self._temp_monsters[name] = monster

        self._monsters.append(EncounterMonster(name, monster.challenge_rating, 0))
        self._adjust_counts(silent=True)
        self._refresh_table()

    def _generate_full_from_scratch(self):
        """Bouton « Générer » : depuis la description si remplie, sinon de zéro.

        Description saisie : l'IA compose la rencontre depuis le texte
        (créatures, CR et quantités conformes — une « cavalerie » donne
        plusieurs centaures) puis les fiches manquantes sont générées.
        Sinon : rencontre vide, nouveaux monstres équilibrés pour la
        difficulté visée.
        """
        description = self.description_edit.toPlainText().strip()
        if description:
            self._generate_from_description()
            return

        confirm = QMessageBox.question(
            self, "Générer",
            "La rencontre actuelle sera remplacée par des monstres "
            "entièrement générés. Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        how_many, ok = QInputDialog.getInt(
            self, "Générer",
            "Nombre de types de monstres à générer :", 2, 1, 6, 1,
        )
        if not ok:
            return

        # Cherche le CR dont la rencontre finale (types x quantités
        # ajustées par build_auto_encounter) est la plus proche de la
        # difficulté demandée : on simule chaque CR possible.
        from src.rules.encounter_builder import build_auto_encounter
        from src.rules.stat_builder import CR_ENTRIES

        party_size = self.party_size_spin.value()
        party_level = self.party_level_spin.value()
        difficulty = self.difficulty_combo.currentData() or "medium"

        # Le CR unitaire idéal vaut le budget divis\u00e9 par le nombre
        # d'exemplaires typiques ; on retient le CR dont la rencontre
        # simul\u00e9e est la plus proche de la difficult\u00e9, avec une
        # pr\u00e9f\u00e9rence pour les rencontres \u00e0 peu d'exemplaires (plus
        # lisibles \u00e0 la table) et sans d\u00e9passement du budget.
        best_cr, best_score = 0.0, None
        for frac, _label in CR_ENTRIES:
            cr = float(frac)
            probe = build_auto_encounter(
                [EncounterMonster(f"m{i}", cr, 1)
                 for i in range(how_many)],
                party_size, party_level, difficulty,
            )[0]
            # Viser la bande de la difficult\u00e9 : au-dessus du budget
            # (le budget est le seuil de la difficult\u00e9) mais sous le
            # seuil de la difficult\u00e9 sup\u00e9rieure ; bonus pour les
            # rencontres \u00e0 peu d'exemplaires (plus lisibles \u00e0 la table).
            from src.rules.encounter import XP_THRESHOLDS
            keys = ["easy", "medium", "hard", "deadly"]
            index = keys.index(difficulty)
            lower = probe.budget
            upper = (
                XP_THRESHOLDS[party_level][index + 1] * party_size
                if index < 3 else lower * 1.5
            )
            if probe.adjusted_xp < lower:
                score = (lower - probe.adjusted_xp) * 2
            elif probe.adjusted_xp > upper:
                score = (probe.adjusted_xp - upper) * 3
            else:
                score = 0
            score += probe.monster_count
            if best_score is None or score < best_score:
                best_cr, best_score = cr, score

        self._monsters = []
        self._monster_files = {}
        self._temp_monsters = {}
        for _ in range(how_many):
            self._generate_new_monster(silent=True, cr=best_cr)

        self._adjust_counts(silent=True)
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

    def _generate_full(self, keep_counts: bool = False):
        """Génération complète : fiches manquantes + quantités + scénario.

        keep_counts : conserve les quantités courantes (composition
        issue de la description) au lieu de rééquilibrer.
        """
        if not self._monsters:
            QMessageBox.information(
                self, "Aucun monstre",
                "Ajoutez d'abord des monstres depuis la bibliothèque."
            )
            return
        if not keep_counts:
            self._adjust_counts(silent=True)

        # Fiches manquantes : stats équilibrées, gardées temporaires.
        # Le MJ les intègre à la bibliothèque depuis la fiche (bouton 📝)
        # s'il le souhaite — rien n'est écrit sur disque ici.
        from src.models.monster import Monster
        from src.rules.stat_builder import build_balanced_monster

        traits = getattr(self, "_creature_traits", {})
        for m in self._monsters:
            if m.name in self._monster_files or m.name in self._temp_monsters:
                continue
            base = Monster(name=m.name)
            monster = build_balanced_monster(m.challenge_rating or 0, base=base)
            trait_text = traits.get(m.name, "")
            if trait_text and self._parent._check_backend():
                from src.ai.ai_generator import ai_generator
                try:
                    if not monster.description:
                        options = ai_generator.generate_options(
                            monster, "description"
                        )
                        if options:
                            monster.description = options[0]
                    monster.actions = ai_generator.generate_actions(
                        monster, actions_prompt=trait_text
                    )
                except Exception:
                    pass
            self._temp_monsters[m.name] = monster

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
        """Exporte la rencontre entière en un seul PDF minimaliste.

        Tous les monstres de la rencontre (temporaires ou bibliothèque)
        dans un document unique, un bloc compact par monstre, séparés
        par une ligne horizontale.
        """
        if not self._monsters:
            QMessageBox.information(
                self, "Aucun monstre",
                "Ajoutez d'abord des monstres à la rencontre."
            )
            return
        from pathlib import Path
        from src.library.library_manager import library_manager
        from src.models.monster import Monster
        from src.rules.stat_builder import build_balanced_monster
        from src.export.pdf_exporter import pdf_exporter
        from PySide6.QtWidgets import QFileDialog
        from config.config_manager import config_manager

        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter la rencontre en PDF",
            str(Path(config_manager.get_save_path()) / "rencontre.pdf"),
            "Fichier PDF (*.pdf)",
        )
        if not path:
            return

        monsters = {}
        for m in self._monsters:
            if not m.name:
                continue
            monster = self._temp_monsters.get(m.name)
            if monster is None:
                target = library_manager.target_path(m.name)
                if target.exists():
                    try:
                        monster = library_manager.load(target)
                    except (OSError, ValueError):
                        monster = None
            if monster is None:
                monster = build_balanced_monster(
                    m.challenge_rating or 0, base=Monster(name=m.name)
                )
            monsters[m.name] = monster

        try:
            pdf_exporter.export_encounter_to_pdf(
                monsters, self.current_encounter(), path
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur", f"Échec de l'export PDF :\n{e}"
            )
            return
        QMessageBox.information(
            self, "Export terminé",
            f"Rencontre exportée vers :\n{path}"
        )


class LibraryPickDialog(QDialog):
    """Sélection d'un monstre de la bibliothèque pour une ligne."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choisir un monstre")
        self.setMinimumSize(480, 400)
        self.selected = []   # [(file, name, cr)]

        from src.library.library_manager import library_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Sélectionnez un monstre :"))

        self.list = QTableWidget(0, 2)
        self.list.setHorizontalHeaderLabels(["Monstre", "CR"])
        self.list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
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
        ok_btn = QPushButton("Choisir")
        ok_btn.clicked.connect(self._confirm)
        buttons.addWidget(ok_btn)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def _confirm(self):
        row = self.list.currentRow()
        if row < 0 or row >= len(self._entries):
            return
        entry = self._entries[row]
        self.selected = [(entry.file, entry.name, entry.challenge_rating)]
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
