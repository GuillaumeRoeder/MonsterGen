"""
Client API distante (compatible OpenAI/Mistral) pour MonsterGen.

Alternative au modèle local : envoie les prompts à un endpoint
de chat completions (Mistral AI, OpenAI, serveur local compatible, etc.).
"""

from typing import Optional

import requests

from config.config_manager import config_manager


class APIConfigError(RuntimeError):
    """La configuration API est incomplète."""


class APIClient:
    """Client pour une API de chat completions compatible OpenAI."""

    def reload_config(self):
        """Recharge la configuration API depuis le gestionnaire."""
        self.api_key = config_manager.get_api_key()
        self.endpoint = config_manager.get_api_endpoint()
        self.model = config_manager.get_api_model()

    def is_configured(self) -> bool:
        """L'API est-elle prête à être utilisée ?"""
        return bool(config_manager.get_api_key() and config_manager.get_api_endpoint())

    def generate(self, prompt: str, max_tokens: int = 400,
                 temperature: float = 0.7,
                 system_prompt: Optional[str] = None) -> str:
        """Génère du texte via l'API distante."""
        self.reload_config()
        if not self.api_key:
            raise APIConfigError(
                "Aucune clé API configurée. "
                "Fichier > Configuration > mode API, puis renseignez la clé."
            )
        if not self.endpoint:
            raise APIConfigError("Aucun endpoint API configuré.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            raise APIConfigError("Réponse API inattendue (aucun choix retourné).")
        except requests.exceptions.RequestException as e:
            raise APIConfigError(f"Erreur API : {e}")


# Instance globale
api_client = APIClient()
