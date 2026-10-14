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
    "Auran (langue des créatures aériennes)",
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
        # Supprimer les commentaires // et /* */
        json_str = re.sub(r'//.*', '', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        # Supprimer les backticks
        json_str = json_str.replace('```json', '').replace('```', '').strip()
        
        # Approche robuste : reconstruire le JSON ligne par ligne
        lines = json_str.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Ignorer les lignes vides
            if not stripped:
                continue
            
            # Si la ligne contient une clé:valeur
            if ':' in stripped:
                # Ajouter une virgule si ce n'est pas la fin d'un objet/array
                if not (stripped.endswith('}') or stripped.endswith(']') or stripped.endswith(',')):
                    stripped = stripped + ','
            
            cleaned_lines.append(stripped)
        
        # Rejoindre avec des espaces
        result = ' '.join(cleaned_lines)
        
        # CORRIGER : Ajouter les virgules manquantes entre les objets dans un tableau
        result = re.sub(r'(\})\s*(\{)', r'\1, \2', result)
        
        # Supprimer les virgules avant } ou ]
        result = re.sub(r',\s*([}\]])', r'\1', result)
        
        # Supprimer les doubles virgules
        result = re.sub(r',\s*,', ',', result)
        
        # Supprimer les virgules après [
        result = re.sub(r'\[\s*,', '[', result)
        
        return result

    def _extract_simple_values(self, options: List) -> List[str]:
        """Extraire des valeurs simples d'une liste d'options (peut contenir des objets)."""
        simple_options = []
        for option in options:
            if isinstance(option, str):
                simple_options.append(option)
            elif isinstance(option, dict):
                # Extraire la première valeur string ou numérique
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
        base_info = """RÈGLE ABSOLUE : Réponds UNIQUEMENT avec un JSON valide : {"options": ["val1", "val2", "val3"]}
Ne mets AUCUN commentaire, AUCUNE explication, AUCUN texte supplémentaire, AUCUN objet, AUCUN tableau imbriqué.
Contexte : Fiche de PNJ/Monstre pour DnD 5e."""
        
        prompts = {
            "name": f"Propose 3 noms adaptés pour un {monster.race or 'PNJ'}. Réponds UNIQUEMENT avec des strings simples.",
            "race": "Propose 3 races adaptées (ex: Gobelin, Orc, Elfe Noir, Nain, Humain, Tiefling, Dragonné, Gnome, Halfelin, Elfe). Réponds UNIQUEMENT avec des strings simples.",
            "description": "Propose 3 descriptions courtes (1 phrase maximum). Réponds UNIQUEMENT avec des strings simples.",
            "alignment": "Propose 3 alignements parmi: Loyal Bon, Neutre Bon, Chaotique Bon, Loyal Neutre, Neutre, Chaotique Neutre, Loyal Mauvais, Neutre Mauvais, Chaotique Mauvais.",
            "size": "Propose 3 tailles parmi: Minuscule, Petit, Moyen, Grand, Énorme, Colossal.",
            "armor_class": "Propose 3 valeurs de CA (entiers entre 10 et 25).",
            "hit_points": "Propose 3 valeurs de PV (entiers).",
            "hit_dice": "Propose 3 dés de vie (ex: 2d8, 3d10, 5d6).",
            "speed": "Propose 3 vitesses (ex: 30 pieds, vol 60 pieds).",
            "challenge_rating": "Propose 3 valeurs de CR (ex: 0.125, 0.25, 0.5, 1, 2, 5).",
            "ability_scores": "Propose 3 ensembles de 6 caractéristiques au format FOR,DEX,CON,INT,SAG,CHA (ex: 15,14,13,10,12,8).",
            "actions": "Propose 3 noms d'actions (ex: Attaque d'épée, Arc court, Morsure).",
        }
        
        if field_name in prompts:
            return f"""{base_info}
{monster.name or 'None'}, Race={monster.race or 'None'}
{prompts[field_name]}
"""
        else:
            return f"""{base_info}
{monster.name or 'None'}, Race={monster.race or 'None'}
Propose 3 valeurs simples pour {field_name}.
"""
    
    def _call_ai_api(self, prompt: str) -> Optional[Dict]:
        """Appelle l'API IA pour générer des suggestions."""
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
                content = content.strip()
                print(f"[DEBUG] Raw AI response: {content[:500]}")
                
                # Essayer de trouver le JSON
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    try:
                        json_str = self._clean_json_string(json_str)
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        print(f"[DEBUG] JSON parse error: {e}")
                        print(f"[DEBUG] Cleaned JSON: {json_str[:500]}")
                
                # Essayer de parser directement
                try:
                    content = self._clean_json_string(content)
                    return json.loads(content)
                except json.JSONDecodeError:
                    print(f"[DEBUG] Fallback: treating as plain text")
                    return {"options": [content]}
            
            return None
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Erreur API IA: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Erreur JSON: {e}")
    
    def generate_options(self, monster: Monster, field_name: str) -> List[str]:
        """Génère des options pour un champ spécifique."""
        # Pour les langues, retourner la liste fixe
        if field_name == "languages":
            return DND5_LANGUAGES
        
        self.reload_config()
        
        if not self.api_key:
            raise ValueError("Aucune clé API configurée.")
        
        prompt = self._generate_prompt(monster, field_name)
        result = self._call_ai_api(prompt)
        
        if result and "options" in result:
            # Extraire les valeurs simples (au cas où l'API retourne des objets)
            return self._extract_simple_values(result["options"])
        
        return []


# Instance globale
ai_generator = AIGenerator()
