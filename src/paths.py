"""
Chemins de données de MonsterGen, sensibles au mode d'exécution.

En développement : tout reste à la racine du projet (comportement historique).
En exécution empaquetée (PyInstaller, sys.frozen) : les données modifiables
vivent dans un répertoire utilisateur inscriptible (~/.monstergen), car le
répertoire d'installation ne l'est pas forcément (ex. Program Files).
"""

import sys
from pathlib import Path

APP_DIR_NAME = "monstergen"


def is_frozen() -> bool:
    """L'application tourne-t-elle dans un binaire PyInstaller ?"""
    return getattr(sys, "frozen", False)


def app_root() -> Path:
    """Racine de l'application : dossier du binaire, ou racine du projet."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    """Répertoire des données utilisateur (config, modèles, fiches)."""
    if is_frozen():
        path = Path.home() / f".{APP_DIR_NAME}"
        path.mkdir(parents=True, exist_ok=True)
        return path
    return app_root()


def models_dir() -> Path:
    """Répertoire des modèles GGUF téléchargés."""
    return data_dir() / "models"


def config_file() -> Path:
    """Fichier de configuration persistée."""
    if is_frozen():
        return data_dir() / "config.json"
    return app_root() / "config" / "config.json"


def default_save_dir() -> Path:
    """Répertoire par défaut des exports et de la bibliothèque."""
    if is_frozen():
        return data_dir() / "fiches"
    return Path("fiches")
