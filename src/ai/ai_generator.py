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
        
        base_info = f"""
        Contexte : Tu es un assistant pour créer des fiches de PNJ/Monstres pour Donjons & Dragons 5e.
        L'utilisateur a commencé à remplir une fiche mais certains champs sont manquants.
        Aide à compléter les informations manquantes de manière cohérente avec DnD 5e.
        Réponds UNIQUEMENT en {language.upper()}.
        
        Informations déjà fournies :
        - Nom : {monster.name or 'Non spécifié'}
        - Race : {monster.race or 'Non spécifiée'}
        - Description : {monster.description or 'Aucune'}
        - Alignement : {monster.alignment.value if monster.alignment else 'Non spécifié'}
        - Taille : {monster.size.value if monster.size else 'Non spécifiée'}
        - Classe d'armure : {monster.armor_class or 'Non spécifiée'}
        - Points de vie : {monster.hit_points or 'Non spécifiés'}
        - Vitesse : {monster.speed or 'Non spécifiée'}
        """
        
        if field_name == "name":
            return f"""{base_info}
            Propose 3 noms créatifs et adaptés pour ce PNJ/Monstre basé sur sa race : {monster.race or 'race non spécifiée'}.
            Formate la réponse comme un tableau JSON avec une clé 'options' contenant la liste des noms.
            Exemple : {{"options": ["Nom 1", "Nom 2", "Nom 3"]}}
            """
        
        elif field_name == "race":
            return f"""{base_info}
            Propose 3 races ou types de créatures adaptés pour ce PNJ/Monstre.
            Formate la réponse comme un tableau JSON avec une clé 'options' contenant la liste des races.
            Exemple : {{"options": ["Race 1", "Race 2", "Race 3"]}}
            """
        
        elif field_name == "description":
            return f"""{base_info}
            Écris 3 descriptions détaillées (2-3 phrases chacune) pour ce PNJ/Monstre.
            Formate la réponse comme un tableau JSON avec une clé 'options' contenant la liste des descriptions.
            Exemple : {{"options": ["Description 1", "Description 2", "Description 3"]}}
            """
        
        elif field_name == "alignment":
            alignments = [a.value for a in Alignment]
            return f"""{base_info}
            Propose 3 alignements possibles parmi {alignments} pour ce PNJ/Monstre.
            Formate la réponse comme un tableau JSON avec une clé 'options' contenant la liste des alignements.
            Exemple : {{"options": ["Loyal Bon", "Neutre", "Chaotique Mauvais"]}}
            """
        
        elif field_name == "size":
            sizes = [s.value for s in Size]
            return f"""{base_info}
            Propose 3 tailles possibles parmi {sizes} pour ce PNJ/Monstre.
            Formate la réponse comme un tableau JSON avec une clé 'options' contenant la liste des tailles.
            Exemple : {{"options": ["Moyen", "Grand", "Petit"]}}
            """
        
        elif field_name == "armor_class":
            return f"""{base_info}
            Propose 3 valeurs de Classe d'Armure (CA) réalistes pour ce PNJ/Monstre.
            Formate la réponse comme un tableau JSON avec une clé 'options' contenant la liste des valeurs (entiers).
            Exemple : {{"options": [12, 14, 16]}}
            """
        
        elif field_name == "hit_points":
            return f"""{base_info}
            Propose 3 valeurs de Points de Vie (PV) réalistes pour ce PNJ/Monstre.
            Formate la réponse comme un tableau JSON avec une clé 'options' contenant la liste des valeurs (entiers).
            Exemple : {{"options": [20, 45, 70]}}
            """
        
        elif field_name == "speed":
            return f"""{base_info}
            Propose 3 valeurs de Vitesse réalistes pour ce PNJ/Monstre (en pieds).
            Formate la réponse comme un tableau JSON avec une clé 'options' contenant la liste des valeurs.
            Exemple : {{"options": ["30 pieds", "40 pieds", "vol 60 pieds"]}}
            """
        
        elif field_name == "ability_scores":
            return f"""{base_info}
            Propose 3 ensembles de caractéristiques (Force, Dextérité, Constitution, Intelligence, Sagesse, Charisme) 
            réalistes pour ce PNJ/Monstre. Chaque ensemble doit être sous forme d'objet avec les 6 caractéristiques.
            Formate la réponse comme un tableau JSON avec une clé 'options' contenant la liste des objets.
            Exemple : {{"options": [{{"strength": 14, "dexterity": 12, "constitution": 16, "intelligence": 10, "wisdom": 12, "charisma": 8}}, ...]}}
            """
        
        elif field_name == "actions":
            return f"""{base_info}
            Propose 3 actions ou attaques possibles pour ce PNJ/Monstre.
            Chaque action doit avoir un nom et une description.
            Formate la réponse comme un tableau JSON avec une clé 'options' contenant la liste des actions.
            Chaque action doit être un objet avec 'name' et 'description'.
            Exemple : {{"options": [{{"name": "Attaque d'épée", "description": "Attaque de mêlée : +5, 1d8+3 dégâts tranchants"}}, ...]}}
            """
        
        elif field_name == "challenge_rating":
            return f"""{base_info}
            Propose 3 valeurs de Challenge Rating (CR) réalistes pour ce PNJ/Monstre.
            Formate la réponse comme un tableau JSON avec une clé 'options' contenant la liste des valeurs (nombres).
            Exemple : {{"options": [0.5, 2, 5]}}
            """
        
        else:
            return f"""{base_info}
            Complète le champ '{field_name}' avec 3 options réalistes.
            Formate la réponse comme un tableau JSON avec une clé 'options' contenant la liste des valeurs.
            """
    
    def _call_ai_api(self, prompt: str) -> Optional[Dict]:
        """Appelle l'API IA pour générer des suggestions."""
        # Recharger la config pour s'assurer d'avoir la clé à jour
        self.reload_config()
        
        if not self.api_key:
            raise ValueError("Aucune clé API configurée. Veuillez configurer votre clé API dans les paramètres.")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500,
        }
        
        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                
                # Nettoyer la réponse pour extraire le JSON
                content = content.strip()
                
                # Essayer de trouver le JSON dans la réponse
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    return json.loads(json_str)
                
                # Si pas de JSON trouvé, essayer de parser directement
                return json.loads(content)
            
            return None
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Erreur lors de l'appel à l'API IA : {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Erreur de décodage JSON : {e}")
    
    def generate_options(self, monster: Monster, field_name: str) -> List[str]:
        """Génère des options pour un champ spécifique."""
        # Recharger la config à chaque appel pour avoir la clé API à jour
        self.reload_config()
        
        if not self.api_key:
            raise ValueError("Aucune clé API configurée. Veuillez configurer votre clé API dans les paramètres.")
        
        prompt = self._generate_prompt(monster, field_name)
        result = self._call_ai_api(prompt)
        
        if result and "options" in result:
            return result["options"]
        
        return []
    
    def generate_full_monster(self, partial_data: Dict) -> Monster:
        """Génère un monstre complet à partir de données partielles."""
        # Recharger la config
        self.reload_config()
        
        if not self.api_key:
            raise ValueError("Aucune clé API configurée. Veuillez configurer votre clé API dans les paramètres.")
        
        # Créer un monstre partiel
        monster = Monster.from_dict(partial_data)
        
        # Identifier les champs manquants
        missing_fields = []
        if not monster.name:
            missing_fields.append("name")
        if not monster.race:
            missing_fields.append("race")
        if not monster.description:
            missing_fields.append("description")
        if not monster.alignment:
            missing_fields.append("alignment")
        if not monster.size:
            missing_fields.append("size")
        if not monster.armor_class:
            missing_fields.append("armor_class")
        if not monster.hit_points:
            missing_fields.append("hit_points")
        if not monster.speed:
            missing_fields.append("speed")
        
        # Générer les champs manquants
        for field in missing_fields:
            options = self.generate_options(monster, field)
            if options:
                # Prendre la première option par défaut
                if field == "name":
                    monster.name = options[0]
                elif field == "race":
                    monster.race = options[0]
                elif field == "description":
                    monster.description = options[0]
                elif field == "alignment":
                    try:
                        monster.alignment = Alignment(options[0])
                    except ValueError:
                        pass
                elif field == "size":
                    try:
                        monster.size = Size(options[0])
                    except ValueError:
                        pass
                elif field == "armor_class":
                    try:
                        monster.armor_class = int(options[0])
                    except ValueError:
                        pass
                elif field == "hit_points":
                    try:
                        monster.hit_points = int(options[0])
                    except ValueError:
                        pass
                elif field == "speed":
                    monster.speed = options[0]
        
        return monster


# Instance globale du générateur IA
ai_generator = AIGenerator()
