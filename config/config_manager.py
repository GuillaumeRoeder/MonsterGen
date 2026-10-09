"""
Gestionnaire de configuration pour l'application MonsterGen.
Gère la clé API IA et les paramètres utilisateur.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Gère la configuration de l'application."""
    
    DEFAULT_CONFIG = {
        "ai_api_key": "",
        "ai_model": "mistral-tiny",
        "ai_endpoint": "https://api.mistral.ai/v1/chat/completions",
        "default_save_path": "./fiches",
        "language": "fr"
    }
    
    def __init__(self, config_path: str = "config/config.json"):
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
                # Si le fichier est corrompu, on garde la config par défaut
                pass
    
    def save_config(self) -> None:
        """Sauvegarde la configuration dans le fichier."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            raise RuntimeError(f"Impossible de sauvegarder la configuration: {e}")
    
    def get_api_key(self) -> str:
        """Récupère la clé API IA."""
        return self.config.get("ai_api_key", "")
    
    def set_api_key(self, api_key: str) -> None:
        """Définit la clé API IA."""
        self.config["ai_api_key"] = api_key
        self.save_config()
    
    def get_model(self) -> str:
        """Récupère le modèle IA."""
        return self.config.get("ai_model", "mistral-tiny")
    
    def set_model(self, model: str) -> None:
        """Définit le modèle IA."""
        self.config["ai_model"] = model
        self.save_config()
    
    def get_endpoint(self) -> str:
        """Récupère l'endpoint IA."""
        return self.config.get("ai_endpoint", "https://api.mistral.ai/v1/chat/completions")
    
    def set_endpoint(self, endpoint: str) -> None:
        """Définit l'endpoint IA."""
        self.config["ai_endpoint"] = endpoint
        self.save_config()
    
    def get_save_path(self) -> str:
        """Récupère le chemin de sauvegarde par défaut."""
        return self.config.get("default_save_path", "./fiches")
    
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
