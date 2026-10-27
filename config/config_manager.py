"""
Gestionnaire de configuration pour l'application MonsterGen.
Gère le modèle IA local et les paramètres utilisateur.
"""

import json
from pathlib import Path
from typing import Dict, Any

from src.paths import config_file


class ConfigManager:
    """Gère la configuration de l'application."""

    DEFAULT_CONFIG = {
        "ai_mode": "local",
        "local_model_size": "2gb",
        "local_model_path": "",
        "local_context": 4096,
        "local_threads": 4,
        "api_key": "",
        "api_endpoint": "https://api.mistral.ai/v1/chat/completions",
        "api_model": "mistral-small-latest",
        "default_save_path": "fiches",
        "language": "fr"
    }

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = config_file()
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        self.load_config()

    def load_config(self) -> None:
        """Charge la configuration depuis le fichier."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
            except (json.JSONDecodeError, IOError):
                pass

    def save_config(self) -> None:
        """Sauvegarde la configuration dans le fichier."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            raise RuntimeError(f"Impossible de sauvegarder la configuration: {e}")

    def get_ai_mode(self) -> str:
        """Récupère le mode IA : 'local' (modèle embarqué) ou 'api' (API distante)."""
        return self.config.get("ai_mode", "local")
    
    def set_ai_mode(self, mode: str) -> None:
        """Définit le mode IA ('local' ou 'api')."""
        self.config["ai_mode"] = mode
        self.save_config()
    
    def get_api_key(self) -> str:
        """Récupère la clé API distante."""
        return self.config.get("api_key", "")
    
    def set_api_key(self, api_key: str) -> None:
        """Définit la clé API distante."""
        self.config["api_key"] = api_key
        self.save_config()
    
    def get_api_endpoint(self) -> str:
        """Récupère l'endpoint de l'API distante."""
        return self.config.get("api_endpoint", "https://api.mistral.ai/v1/chat/completions")
    
    def set_api_endpoint(self, endpoint: str) -> None:
        """Définit l'endpoint de l'API distante."""
        self.config["api_endpoint"] = endpoint
        self.save_config()
    
    def get_api_model(self) -> str:
        """Récupère le nom du modèle API."""
        return self.config.get("api_model", "mistral-small-latest")
    
    def set_api_model(self, model: str) -> None:
        """Définit le nom du modèle API."""
        self.config["api_model"] = model
        self.save_config()
    
    def get_local_model_size(self) -> str:
        """Récupère la taille du modèle local ('2gb' ou '4gb')."""
        return self.config.get("local_model_size", "2gb")

    def set_local_model_size(self, size: str) -> None:
        """Définit la taille du modèle local."""
        self.config["local_model_size"] = size
        self.save_config()

    def get_local_model_path(self) -> str:
        """Récupère le chemin du fichier modèle GGUF."""
        return self.config.get("local_model_path", "")

    def set_local_model_path(self, path: str) -> None:
        """Définit le chemin du fichier modèle GGUF."""
        self.config["local_model_path"] = path
        self.save_config()

    def get_local_context(self) -> int:
        """Récupère la taille du contexte du modèle."""
        return int(self.config.get("local_context", 4096))

    def set_local_context(self, ctx: int) -> None:
        """Définit la taille du contexte du modèle."""
        self.config["local_context"] = int(ctx)
        self.save_config()

    def get_local_threads(self) -> int:
        """Récupère le nombre de threads CPU pour le modèle."""
        return int(self.config.get("local_threads", 4))

    def set_local_threads(self, threads: int) -> None:
        """Définit le nombre de threads CPU pour le modèle."""
        self.config["local_threads"] = int(threads)
        self.save_config()

    def get_save_path(self) -> str:
        """Récupère le chemin de sauvegarde par défaut."""
        path = str(self.config.get("default_save_path", "fiches"))
        if path.startswith("./"):
            path = path[2:]
        return path

    def set_save_path(self, path: str) -> None:
        """Définit le chemin de sauvegarde par défaut."""
        self.config["default_save_path"] = path
        self.save_config()

    def get_language(self) -> str:
        """Récupère la langue."""
        return self.config.get("language", "fr")

    def set_language(self, language: str) -> None:
        """Définit la langue."""
        self.config["language"] = language
        self.save_config()


# Instance globale du gestionnaire de configuration
config_manager = ConfigManager()
