"""
Module de génération IA pour compléter les champs manquants.
"""

import requests
import json
import re
from typing import List, Dict, Optional
from src.models.monster import Monster, Alignment, Size, AbilityScores, SavingThrow, Skill, Action
from config.config_manager import config_manager


# Liste fixe des langues DnD 5e
DND5_LANGUAGES = [
    "Commun",
    "Auran",
    "Céleste",
    "Draconique",
    "Elfique",
    "Géant",
    "Gnome",
    "Gobelin",
    "Infernal",
    "Nain",
    "Orque",
    "Primordial",
    "Sylvestre",
    "Abyssal",
    "Aklo",
    "Aquatique",
    "Chtonien",
    "Ignan",
    "Terran",
]


class AIGenerator:
    """Générateur IA pour compléter les données manquantes."""

    def __init__(self):
        self.api_key = None
        self.endpoint = None
        self.model = None

    def reload_config(self):
        """Recharge la configuration depuis le gestionnaire."""
        self.api_key = config_manager.get_api_key()
        self.endpoint = config_manager.get_endpoint()
        self.model = config_manager.get_model()

    def _clean_json_string(self, json_str: str) -> str:
        """Nettoie une chaîne JSON en supprimant les commentaires et en corrigeant le format."""
        json_str = re.sub(r'//.*', '', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        json_str = json_str.replace('```json', '').replace('```', '').strip()
        
        lines = json_str.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if ':' in stripped:
                if not (stripped.endswith('}') or stripped.endswith(']') or stripped.endswith(',')):
                    stripped = stripped + ','
            cleaned_lines.append(stripped)
        
        result = ' '.join(cleaned_lines)
        result = re.sub(r'(\})\s*(\{)', r'\1, \2', result)
        result = re.sub(r',\s*([}\]])', r'\1', result)
        result = re.sub(r',\s*,', ',', result)
        result = re.sub(r'\[\s*,', '[', result)
        return result

    def _extract_simple_values(self, options: List) -> List[str]:
        """Extraire des valeurs simples d'une liste d'options."""
        simple_options = []
        for option in options:
            if isinstance(option, str):
                simple_options.append(option)
            elif isinstance(option, dict):
                for key, value in option.items():
                    if isinstance(value, (str, int, float)):
                        simple_options.append(str(value))
                        break
                    elif isinstance(value, list) and len(value) > 0:
                        simple_options.append(str(value[0]))
                        break
            elif isinstance(option, (int, float)):
                simple_options.append(str(option))
        return simple_options

    def _generate_prompt(self, monster: Monster, field_name: str) -> str:
        """Génère un prompt pour la génération d'un champ spécifique."""
        base = "RÈGLE ABSOLUE: Réponds UNIQUEMENT avec un JSON: {\"options\": [\"val1\", \"val2\", \"val3\"]}. "
        base += "Ne mets AUCUN commentaire, AUCUNE explication, AUCUN texte supplémentaire. "
        base += "Contexte: Fiche de PNJ/Monstre pour DnD 5e. "
        base += f"Nom={monster.name or 'None'}, Race={monster.race or 'None'}. "
        
        prompts = {
            "name": "Propose 3 noms adaptés.",
            "race": "Propose 3 races: Gobelin, Orc, Elfe Noir, Nain, Humain, Tiefling, Dragonné, Gnome, Halfelin, Elfe.",
            "description": "Propose 3 descriptions courtes (1 phrase).",
            "alignment": "Propose 3 alignements: Loyal Bon, Neutre Bon, Chaotique Bon, Loyal Neutre, Neutre, Chaotique Neutre, Loyal Mauvais, Neutre Mauvais, Chaotique Mauvais.",
            "size": "Propose 3 tailles: Minuscule, Petit, Moyen, Grand, Énorme, Colossal.",
            "armor_class": "Propose 3 valeurs de CA (entiers 10-25).",
            "hit_points": "Propose 3 valeurs de PV (entiers).",
            "hit_dice": "Propose 3 dés de vie: 2d8, 3d10, 5d6, 4d6, 6d8.",
            "speed": "Propose 3 vitesses: 30 pieds, 40 pieds, vol 60 pieds.",
            "challenge_rating": "Propose 3 valeurs de CR: 0.125, 0.25, 0.5, 1, 2, 5, 10.",
            "ability_scores": "Propose 3 ensembles de 6 caractéristiques au format FOR,DEX,CON,INT,SAG,CHA. Ex: 15,14,13,10,12,8.",
            "actions": "Propose 3 noms d'actions: Attaque d'épée, Arc court, Morsure, Souffle de feu.",
        }
        
        if field_name in prompts:
            return base + prompts[field_name]
        else:
            return base + f"Propose 3 valeurs simples pour {field_name}."

    def _call_ai_api(self, prompt: str) -> Optional[Dict]:
        """Appelle l'API IA."""
        self.reload_config()
        if not self.api_key:
            raise ValueError("Aucune clé API configurée.")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500,
        }
        
        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"].strip()
                print(f"[DEBUG] Raw AI response: {content[:500]}")
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    try:
                        json_str = self._clean_json_string(json_str)
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        print(f"[DEBUG] JSON parse error: {e}")
                try:
                    content = self._clean_json_string(content)
                    return json.loads(content)
                except json.JSONDecodeError:
                    print("[DEBUG] Fallback: treating as plain text")
                    return {"options": [content]}
            return None
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Erreur API IA: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Erreur JSON: {e}")

    def generate_options(self, monster: Monster, field_name: str) -> List[str]:
        """Génère des options pour un champ spécifique."""
        if field_name == "languages":
            return DND5_LANGUAGES
        
        self.reload_config()
        if not self.api_key:
            raise ValueError("Aucune clé API configurée.")
        
        prompt = self._generate_prompt(monster, field_name)
        result = self._call_ai_api(prompt)
        if result and "options" in result:
            return self._extract_simple_values(result["options"])
        return []


# Instance globale
ai_generator = AIGenerator()
