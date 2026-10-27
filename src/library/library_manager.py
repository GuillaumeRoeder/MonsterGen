"""Système de bibliothèque de monstres (logique, sans interface).

LibraryManager centralise toutes les opérations de persistance des
monstres : liste des sauvegardes, chargement, sauvegarde, suppression,
export vers un fichier de bibliothèque et import. Les dialogues de
l'UI (src/ui/monster_library.py) ne font qu'appeler ce gestionnaire.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config.config_manager import config_manager
from src.models.monster import Monster


@dataclass
class LibraryEntry:
    """Une sauvegarde de la bibliothèque, telle qu'affichée dans l'UI."""
    file: Path
    name: str
    challenge_rating: Optional[float]
    modified: datetime

    @property
    def label(self) -> str:
        cr_str = f"CR {self.challenge_rating}" if self.challenge_rating is not None else "sans CR"
        date_str = self.modified.strftime("%d/%m/%Y %H:%M")
        return f"{self.name} — {cr_str} — {date_str}"

    @property
    def readable(self) -> bool:
        return self.name != self.file.stem or self.challenge_rating is not None


@dataclass
class ImportResult:
    """Résultat d'un import de fichier de bibliothèque."""
    imported: int = 0
    overwritten: int = 0


class LibraryManager:
    """Gestionnaire de la bibliothèque : CRUD + import/export."""

    def __init__(self):
        self._dir: Optional[Path] = None

    @property
    def library_dir(self) -> Path:
        """Dossier de sauvegarde (config), créé s'il n'existe pas."""
        path = Path(config_manager.get_save_path())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_entries(self) -> List[LibraryEntry]:
        """Liste triée des sauvegardes, avec métadonnées d'affichage."""
        entries = []
        for file in sorted(self.library_dir.glob("*.json")):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                entries.append(LibraryEntry(
                    file=file,
                    name=data.get("name") or file.stem,
                    challenge_rating=data.get("challenge_rating"),
                    modified=datetime.fromtimestamp(file.stat().st_mtime),
                ))
            except (json.JSONDecodeError, OSError, ValueError):
                entries.append(LibraryEntry(
                    file=file,
                    name=file.stem,
                    challenge_rating=None,
                    modified=datetime.fromtimestamp(file.stat().st_mtime),
                ))
        return entries

    def load(self, file: Path) -> Monster:
        """Charge un monstre depuis un fichier de la bibliothèque."""
        data = json.loads(file.read_text(encoding="utf-8"))
        return Monster.from_dict(data)

    def target_path(self, filename: str) -> Path:
        """Chemin cible pour un nom de sauvegarde donné."""
        safe = filename.strip().replace(" ", "_")
        return self.library_dir / f"{safe}.json"

    def save(self, monster: Monster, filename: str) -> Path:
        """Écrit la sauvegarde et retourne son chemin."""
        target = self.target_path(filename)
        target.write_text(
            json.dumps(monster.to_dict(), indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        return target

    def delete(self, file: Path):
        """Supprime un fichier de sauvegarde."""
        file.unlink()

    def read_raw(self, file: Path) -> dict:
        """Lit le JSON brut d'une sauvegarde (pour l'export)."""
        return json.loads(file.read_text(encoding="utf-8"))

    def export_entries(self, files: List[Path], destination: Path):
        """Écrit les monstres des fichiers donnés dans un fichier unique."""
        monsters = [self.read_raw(file) for file in files]
        payload = {"monsters": monsters}
        destination.write_text(
            json.dumps(payload, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )

    def import_file(self, source: Path) -> ImportResult:
        """Importe les monstres d'un fichier dans la bibliothèque.

        Formats acceptés : monstre seul, {"monsters": [...]} ou liste.
        """
        payload = json.loads(source.read_text(encoding="utf-8"))

        if isinstance(payload, dict) and "monsters" in payload:
            entries = payload["monsters"]
        elif isinstance(payload, list):
            entries = payload
        elif isinstance(payload, dict) and payload.get("name"):
            entries = [payload]
        else:
            raise ValueError(
                "Format non reconnu : le fichier doit être un monstre "
                "exporté (fichier individuel ou export de bibliothèque "
                "MonsterGen)."
            )

        result = ImportResult()
        for data in entries:
            name = (data.get("name") or "Monstre").strip()
            target = self.target_path(name)
            if target.exists():
                result.overwritten += 1
            try:
                target.write_text(
                    json.dumps(data, indent=4, ensure_ascii=False),
                    encoding="utf-8",
                )
                result.imported += 1
            except OSError:
                continue
        return result


library_manager = LibraryManager()
