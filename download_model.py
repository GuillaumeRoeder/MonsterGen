"""
Script de téléchargement du modèle IA local (GGUF) pour MonsterGen.

Usage :
    python download_model.py           # télécharge le modèle sélectionné dans la config
    python download_model.py 4gb       # télécharge le modèle 4 Go
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.ai.local_model import LOCAL_MODELS, local_model, ModelNotAvailableError


def main():
    size = None
    if len(sys.argv) > 1 and sys.argv[1] in LOCAL_MODELS:
        size = sys.argv[1]

    if size:
        from config.config_manager import config_manager
        config_manager.set_local_model_size(size)

    info = local_model.get_model_info()
    print(f"Modèle sélectionné : {info['label']}")
    print(f"Source : https://huggingface.co/{info['repo_id']}")
    print()

    path = local_model.get_model_path()
    if path.exists():
        print(f"Le modèle est déjà téléchargé : {path}")
        return

    print("Téléchargement en cours (peut prendre plusieurs minutes)…")
    try:
        downloaded = local_model.download()
        print(f"Modèle téléchargé : {downloaded}")
    except ModelNotAvailableError as e:
        print(f"Erreur : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
