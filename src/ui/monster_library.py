"""
Bibliothèque de monstres : mini gestionnaire de sauvegardes.

Liste les monstres enregistrés dans le dossier de sauvegarde (éditable
dans la configuration) et permet de sauvegarder le monstre courant (nom
de fichier éditable), de charger ou de supprimer une sauvegarde.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QInputDialog, QLabel, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout
)

from config.config_manager import config_manager
from src.models.monster import Monster

LIBRARY_STYLE = """
    QListWidget {
        background-color: #4a4a4a;
        color: #e0e0e0;
        border: 1px solid #5a5a5a;
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

    def __init__(self, get_current_monster: Callable[[], Monster],
                 load_monster_callback: Callable[[Monster], None], parent=None):
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

        save_btn = QPushButton("💾 Sauvegarder le monstre actuel")
        save_btn.clicked.connect(self._save_current)
        buttons.addWidget(save_btn)

        load_btn = QPushButton("📂 Charger")
        load_btn.clicked.connect(self._load_selected)
        buttons.addWidget(load_btn)

        delete_btn = QPushButton("🗑 Supprimer")
        delete_btn.setStyleSheet("color: #ff8888;")
        delete_btn.clicked.connect(self._delete_selected)
        buttons.addWidget(delete_btn)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)

        layout.addLayout(buttons)

        self._refresh()

    def _library_dir(self) -> Path:
        """Dossier de sauvegarde (config), créé s'il n'existe pas."""
        path = Path(config_manager.get_save_path())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _refresh(self):
        """Recharge la liste des monstres sauvegardés."""
        self._path_label.setText(f"Dossier : {self._library_dir()}")
        self._list.clear()
        for file in sorted(self._library_dir().glob("*.json")):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                name = data.get("name") or file.stem
                cr = data.get("challenge_rating")
                modified = datetime.fromtimestamp(file.stat().st_mtime)
                date_str = modified.strftime("%d/%m/%Y %H:%M")
                cr_str = f"CR {cr}" if cr is not None else "sans CR"
                label = f"{name} — {cr_str} — {date_str}"
            except (json.JSONDecodeError, OSError):
                label = f"{file.stem} — (fichier illisible)"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, str(file))
            self._list.addItem(item)

    def _selected_file(self) -> Optional[Path]:
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

        default_name = monster.name
        filename, ok = QInputDialog.getText(
            self, "Sauvegarder le monstre",
            "Nom de la sauvegarde :",
            text=default_name,
        )
        if not ok or not filename.strip():
            return

        safe = filename.strip().replace(" ", "_")
        target = self._library_dir() / f"{safe}.json"

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
            target.write_text(
                json.dumps(monster.to_dict(), indent=4, ensure_ascii=False),
                encoding="utf-8",
            )
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
            data = json.loads(file.read_text(encoding="utf-8"))
            monster = Monster.from_dict(data)
        except (json.JSONDecodeError, OSError, KeyError) as e:
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
            file.unlink()
        except OSError as e:
            QMessageBox.critical(self, "Erreur", f"Échec de la suppression :\n{e}")
            return
        self._refresh()
