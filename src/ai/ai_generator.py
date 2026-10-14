"""
Module de génération IA pour compléter les champs manquants.
"""

import requests
import json
from typing import List, Dict, Optional
from src.models.monster import Monster, Alignment, Size, AbilityScores, SavingThrow, Skill, Action
from config.config_manager import config_manager


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
    
    def _generate_prompt(self, monster: Monster, field_name: str) -> str:
        """Génère un prompt pour la génération d'un champ spécifique."""
        language = config_manager.get_language()
        
        base_info = f"""RÈGLE ABSOLUE : Réponds UNIQUEMENT avec un JSON valide : {{"options": ["val1", "val2", "val3"]}}
        Ne mets AUCUN commentaire, AUCUNE explication, AUCUN texte supplémentaire.
        Contexte : Fiche de PNJ/Monstre pour DnD 5e. Nom={monster.name or 'None'}, Race={monster.race or 'None'}.
        """
        
        prompts = {
            "name": "Propose 3 noms adaptés.",
            "race": "Propose 3 races adaptées.",
            "description": "Propose 3 descriptions courtes (1 phrase).",
            "alignment": "Propose 3 alignements parmi: Loyal Bon, Neutre Bon, Chaotique Bon, Loyal Neutre, Neutre, Chaotique Neutre, Loyal Mauvais, Neutre Mauvais, Chaotique Mauvais.",
            "size": "Propose 3 tailles parmi: Minuscule, Petit, Moyen, Grand, Énorme, Colossal.",
            "armor_class": "Propose 3 valeurs de CA (entiers 10-25).",
            "hit_points": "Propose 3 valeurs de PV (entiers).",
            "hit_dice": "Propose 3 dés de vie (ex: 2d8, 3d10).",
            "speed": "Propose 3 vitesses (ex: 30 pieds, vol 60 pieds).",
            "languages": "Propose 3 langues (ex: Commun, Elfique, Nain).",
            "challenge_rating": "Propose 3 valeurs de CR (ex: 0.5, 1, 2).",
            "ability_scores": "Propose 3 ensembles de 6 caractéristiques au format FOR,DEX,CON,INT,SAG,CHA (ex: 15,14,13,10,12,8).",
            "actions": "Propose 3 noms d'actions.",
        }
        
        if field_name in prompts:
            return f"""{base_info}
            {prompts[field_name]}
            """
        else:
            return f"""{base_info}
            Propose 3 valeurs simples pour {field_name}.
            """

# Instance globale du générateur IA
ai_generator = AIGenerator()
