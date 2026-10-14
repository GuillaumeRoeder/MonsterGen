"""
Module de génération IA locale pour compléter les champs manquants.

Toute la génération passe par un petit modèle embarqué (GGUF, 2 à 6 Go)
exécuté en locale avec llama-cpp-python : aucune clé API n'est nécessaire.
Les statistiques équilibrées, elles, sont calculées par src/rules/stat_builder
d'après les tables officielles du Guide du Maître (aucune IA requise).
"""

import json
import re
from typing import List, Optional

from src.models.monster import Monster, Action
from src.ai.local_model import local_model
from src.ai.api_client import api_client, APIConfigError
from config.config_manager import config_manager
from src.rules.stat_builder import cr_display, cr_xp

SYSTEM_PROMPT = (
    "Tu es un assistant de création de contenu pour Donjons & Dragons 5e. "
    "Tu réponds en français, de façon concise, dans le format exact demandé."
)


def _backend_generate(prompt: str, max_tokens: int, temperature: float = 0.7) -> str:
    """Route la génération vers le modèle local ou l'API selon la config."""
    if config_manager.get_ai_mode() == "api":
        return api_client.generate(prompt, max_tokens=max_tokens,
                                   temperature=temperature, system_prompt=SYSTEM_PROMPT)
    return local_model.generate(prompt, max_tokens=max_tokens,
                                 temperature=temperature, system_prompt=SYSTEM_PROMPT)

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

def monster_stats_summary(monster: Monster) -> str:
    """Résumé texte des stats actuelles du monstre, pour les prompts."""
    s = monster.ability_scores
    return (
        f"Nom={monster.name or 'sans nom'}, "
        f"Race={monster.race or 'inconnue'}, "
        f"CA={monster.armor_class or '—'}, "
        f"PV={monster.hit_points or '—'} ({monster.hit_dice or '—'}), "
        f"CR={cr_display(monster.challenge_rating)} ({cr_xp(monster.challenge_rating)} PX), "
        f"FOR={s.strength}, DEX={s.dexterity}, CON={s.constitution}, "
        f"INT={s.intelligence}, SAG={s.wisdom}, CHA={s.charisma}"
    )


class AIGenerator:
    """Générateur IA local pour compléter les données manquantes."""

    def _clean_json_string(self, json_str: str) -> str:
        """Nettoie une réponse potentiellement mal formée en JSON."""
        json_str = re.sub(r'//.*', '', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        json_str = json_str.replace('```json', '').replace('```', '').strip()
        json_match = re.search(r'\{.*\}|\[.*\]', json_str, re.DOTALL)
        if json_match:
            json_str = json_match.group()
        return json_str

    def _parse_json(self, text: str) -> Optional[dict]:
        """Tente de parser une réponse JSON du modèle."""
        cleaned = self._clean_json_string(text)
        try:
            data = json.loads(cleaned)
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None

    def generate_options(self, monster: Monster, field_name: str) -> List[str]:
        """Génère des options pour un champ textuel (nom, race, description...)."""
        if field_name == "languages":
            return DND5_LANGUAGES

        prompts = {
            "name": "Propose 3 noms de fantaisie adaptés, séparés par des points-virgules.",
            "race": "Propose 3 races DnD 5e (ex: Gobelin, Orc, Elfe Noir, Tiefling), séparées par des points-virgules.",
            "description": (
                "Propose 3 descriptions courtes (1 phrase chacune) pour cette créature, "
                "séparées par des points-virgules."
            ),
        }

        if field_name not in prompts:
            return []

        prompt = (
            f"Fiche de PNJ/Monstre DnD 5e. {monster_stats_summary(monster)}\n"
            f"{prompts[field_name]}\n"
            "Réponds UNIQUEMENT avec les valeurs, sans numérotation ni texte supplémentaire."
        )

        try:
            raw = _backend_generate(prompt, max_tokens=200)
        except ModelNotAvailableError:
            raise

        options = [opt.strip() for opt in raw.replace('\n', ';').split(';') if opt.strip()]
        return options[:3]

    def generate_actions(self, monster: Monster) -> List[Action]:
        """Génère des actions complètes (nom + description + stats) pour le monstre."""
        prompt = (
            f"Fiche de PNJ/Monstre DnD 5e. {monster_stats_summary(monster)}\n"
            "Génère 3 actions de combat cohérentes avec ces statistiques "
            "(bonus d'attaque et dégâts équilibrés pour ce CR).\n"
            'Réponds UNIQUEMENT en JSON valide, format strict :\n'
            '{"actions": [{"name": "...", "description": "...", '
            '"attack_bonus": 0, "damage": "...", "damage_type": "..."}]}\n'
            "Pas de texte en dehors du JSON."
        )

        raw = _backend_generate(prompt, max_tokens=600)
        data = self._parse_json(raw)

        actions: List[Action] = []
        if data and isinstance(data.get("actions"), list):
            for entry in data["actions"][:4]:
                if not isinstance(entry, dict) or not entry.get("name"):
                    continue
                attack_bonus = entry.get("attack_bonus")
                actions.append(Action(
                    name=str(entry.get("name", "")).strip(),
                    description=str(entry.get("description", "")).strip(),
                    attack_bonus=int(attack_bonus) if isinstance(attack_bonus, (int, float)) else None,
                    damage=str(entry["damage"]).strip() if entry.get("damage") else None,
                    damage_type=str(entry.get("damage_type", "")).strip() or None,
                ))

        if not actions:
            raise RuntimeError("Le modèle n'a pas produit d'actions exploitables.")
        return actions

    def generate_scenario(self, monster: Monster) -> str:
        """Génère un scénario de rencontre rapide basé sur les stats actuelles."""
        prompt = (
            f"Fiche de PNJ/Monstre DnD 5e. {monster_stats_summary(monster)}\n"
            "Actions connues : "
            + ("; ".join(a.name for a in monster.actions) if monster.actions else "aucune")
            + ".\n"
            "Écris un scénario de rencontre rapide (4 à 6 phrases) pour un groupe "
            "d'aventuriers affrontant cette créature : contexte, environnement, "
            "déroulement suggéré et récompense possible. "
            "Réponds UNIQUEMENT avec le texte du scénario, sans titre ni préambule."
        )

        raw = _backend_generate(prompt, max_tokens=350, temperature=0.8)
        cleaned = raw.replace('```', '').strip()
        if not cleaned:
            raise RuntimeError("Le modèle n'a pas produit de scénario.")
        return cleaned


# Instance globale
ai_generator = AIGenerator()
