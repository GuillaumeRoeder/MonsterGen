"""Fenêtre de dialogue unique de la bibliothèque de monstres.

Toute la logique de persistance vit dans
src/library/library_manager.py ; ce module ne contient que les
dialogues Qt (sauvegarder/charger/supprimer, exporter, importer).
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QFileDialog, QHBoxLayout, QInputDialog, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout
)

from src.library.library_manager import library_manager

LIBRARY_STYLE = """
    QListWidget {
        background-color: #4a4a4a;
        color: #e0e0e0;
        border: 1px solid #5a5a6a;
        border-radius: 4px;
        padding: 4px;
    }
    QListWidget::item {
        padding: 6px;
        border: none;
    }
    QListWidget::item:selected {
        background-color: #00aaff;
        color: #ffffff;
    }
"""


class MonsterLibraryDialog(QDialog):
    """Popup de gestion de la bibliothèque de monstres sauvegardés."""

    def __init__(self, get_current_monster, load_monster_callback, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bibliothèque de monstres")
        self.setMinimumSize(520, 420)
        self.setStyleSheet(LIBRARY_STYLE)

        self._get_current_monster = get_current_monster
        self._load_monster_callback = load_monster_callback

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        header = QHBoxLayout()
        self._path_label = QLabel("")
        self._path_label.setStyleSheet("color: #9aa0b4; font-size: 11px;")
        header.addWidget(self._path_label, stretch=1)
        layout.addLayout(header)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._load_selected)
        layout.addWidget(self._list, stretch=1)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        save_btn = QPushButton("\U0001F4BE Sauvegarder le monstre actuel")
        save_btn.clicked.connect(self._save_current)
        buttons.addWidget(save_btn)

        load_btn = QPushButton("\U0001F4C2 Charger")
        load_btn.clicked.connect(self._load_selected)
        buttons.addWidget(load_btn)

        import_btn = QPushButton("\U0001F4E5 Importer")
        import_btn.clicked.connect(self._import_from_file)
        buttons.addWidget(import_btn)

        delete_btn = QPushButton("\U0001F5D1 Supprimer")
        delete_btn.setStyleSheet("color: #ff8888;")
        delete_btn.clicked.connect(self._delete_selected)
        buttons.addWidget(delete_btn)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)

        layout.addLayout(buttons)

        self._refresh()

    def _refresh(self):
        """Recharge la liste des monstres sauvegardés."""
        self._path_label.setText(f"Dossier : {library_manager.library_dir}")
        self._list.clear()
        for entry in library_manager.list_entries():
            label = entry.label if entry.readable else f"{entry.file.stem} — (fichier illisible)"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, str(entry.file))
            self._list.addItem(item)

    def _selected_file(self):
        item = self._list.currentItem()
        if not item:
            return None
        return Path(item.data(Qt.ItemDataRole.UserRole))

    def _save_current(self):
        """Sauvegarde le monstre actuel, nom de fichier éditable."""
        monster = self._get_current_monster()
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

        self._refresh()

    def _load_selected(self):
        """Charge la sauvegarde sélectionnée dans l'éditeur."""
        file = self._selected_file()
        if not file:
            QMessageBox.information(self, "Charger", "Sélectionnez un monstre dans la liste.")
            return
        try:
            monster = library_manager.load(file)
        except (ValueError, KeyError, OSError) as e:
            QMessageBox.critical(self, "Erreur", f"Fichier illisible :\n{e}")
            return

        confirm = QMessageBox.question(
            self, "Charger le monstre",
            "Charger cette sauvegarde remplacera le monstre actuel (non sauvegardé).\n"
            "Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._load_monster_callback(monster)
        self.accept()

    def _delete_selected(self):
        """Supprime la sauvegarde sélectionnée (avec confirmation)."""
        file = self._selected_file()
        if not file:
            QMessageBox.information(self, "Supprimer", "Sélectionnez un monstre dans la liste.")
            return

        confirm = QMessageBox.question(
            self, "Supprimer la sauvegarde",
            f"Supprimer définitivement « {file.stem} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            library_manager.delete(file)
        except OSError as e:
            QMessageBox.critical(self, "Erreur", f"Échec de la suppression :\n{e}")
            return
        self._refresh()

    def _import_from_file(self):
        """Importe des monstres depuis un fichier d'export de bibliothèque."""
        imported = import_library_file(self)
        if imported > 0:
            self._refresh()


class LibraryExportDialog(QDialog):
    """Sélection des monstres à exporter vers un fichier de bibliothèque."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exporter la bibliothèque")
        self.setMinimumSize(380, 340)
        self.setStyleSheet(LIBRARY_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        intro = QLabel("Cochez les monstres à exporter, puis choisissez "
                       "l'emplacement du fichier :")
        intro.setStyleSheet("color: #dce4ee;")
        layout.addWidget(intro)

        self._checks = []
        for entry in library_manager.list_entries():
            label = entry.label if entry.readable else f"{entry.file.stem} — (fichier illisible)"
            label = label.rsplit(" — ", 1)[0]
            check = QCheckBox(label)
            self._checks.append((check, entry.file))
            layout.addWidget(check)

        layout.addStretch()

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        export_btn = QPushButton("Exporter...")
        export_btn.clicked.connect(self._export)
        buttons.addWidget(export_btn)
        layout.addLayout(buttons)

    def _export(self):
        """Écrit les monstres cochés dans un fichier unique choisi."""
        files = [f for check, f in self._checks if check.isChecked()]
        if not files:
            QMessageBox.information(
                self, "Exporter", "Cochez au moins un monstre à exporter."
            )
            return

        default = "bibliotheque_monstres.json"
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter la bibliothèque", default,
            "Fichier de bibliothèque (*.json)"
        )
        if not path:
            return

        errors = []
        monsters = []
        for file in files:
            try:
                monsters.append(library_manager.read_raw(file))
            except (ValueError, OSError) as e:
                errors.append(f"{file.stem} : {e}")

        try:
            library_manager.export_entries(files, Path(path))
        except (ValueError, OSError) as e:
            QMessageBox.critical(self, "Erreur", f"Échec de l'export :\n{e}")
            return

        msg = f"{len(monsters)} monstre(s) exporté(s) vers :\n{path}"
        if errors:
            msg += "\n\nFichiers ignorés :\n" + "\n".join(errors)
        QMessageBox.information(self, "Export réussi", msg)


def import_library_file(parent) -> int:
    """Importe les monstres d'un fichier d'export dans la bibliothèque.

    Retourne le nombre de monstres importés.
    """
    path, _ = QFileDialog.getOpenFileName(
        parent, "Importer une bibliothèque", "",
        "Fichier de bibliothèque (*.json);;Tous les fichiers (*)"
    )
    if not path:
        return 0

    try:
        result = library_manager.import_file(Path(path))
    except (ValueError, OSError) as e:
        QMessageBox.critical(parent, "Erreur", f"Fichier illisible :\n{e}")
        return 0

    msg = f"{result.imported} monstre(s) importé(s) dans la bibliothèque."
    if result.overwritten:
        msg += f"\n({result.overwritten} sauvegarde(s) existante(s) écrasée(s) "
        msg += "— portant le même nom.)"
    QMessageBox.information(parent, "Import réussi", msg)
    return result.imported
