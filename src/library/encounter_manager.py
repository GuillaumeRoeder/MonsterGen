"""
Gestionnaire de bibliothèque de rencontres (logique, sans interface).

RencontreManager centralise la persistance des rencontres :
liste des sauvegardes (dossier `rencontres` du chemin de sauvegarde),
chargement, sauvegarde et suppression. Les dialogues de l'UI
(src/ui/encounter_tab.py) ne font qu'appeler ce gestionnaire.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config.config_manager import config_manager
from src.rules.encounter_builder import Encounter


@dataclass
class EncounterEntry:
    """Une sauvegarde de rencontre, telle qu'affichée dans l'UI."""
    file: Path
    name: str
    modified: datetime

    @property
    def label(self) -> str:
        date_str = self.modified.strftime("%d/%m/%Y %H:%M")
        return f"{self.name} — {date_str}"


class EncounterManager:
    """Gestionnaire de la bibliothèque de rencontres : CRUD."""

    def __init__(self):
        self._dir: Optional[Path] = None

    @property
    def encounter_dir(self) -> Path:
        """Dossier de sauvegarde des rencontres, créé s'il n'existe pas."""
        path = Path(config_manager.get_save_path()) / "rencontres"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_entries(self) -> List[EncounterEntry]:
        """Liste triée des sauvegardes de rencontres."""
        entries = []
        for file in sorted(self.encounter_dir.glob("*.json")):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                entries.append(EncounterEntry(
                    file=file,
                    name=data.get("name") or file.stem,
                    modified=datetime.fromtimestamp(file.stat().st_mtime),
                ))
            except (json.JSONDecodeError, OSError, ValueError):
                entries.append(EncounterEntry(
                    file=file,
                    name=file.stem,
                    modified=datetime.fromtimestamp(file.stat().st_mtime),
                ))
        return entries

    def load(self, file: Path) -> Encounter:
        """Charge une rencontre depuis un fichier."""
        data = json.loads(file.read_text(encoding="utf-8"))
        return Encounter.from_dict(data)

    def target_path(self, filename: str) -> Path:
        """Chemin cible pour un nom de sauvegarde donné."""
        safe = filename.strip().replace(" ", "_")
        return self.encounter_dir / f"{safe}.json"

    def save(self, encounter: Encounter, filename: str) -> Path:
        """Écrit la sauvegarde et retourne son chemin."""
        target = self.target_path(filename)
        target.write_text(
            json.dumps(encounter.to_dict(), indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        return target

    def delete(self, file: Path):
        """Supprime un fichier de sauvegarde."""
        file.unlink()


encounter_manager = EncounterManager()
