"""
Modèle de données pour un PNJ/Monstre dans DnD 5e.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class Alignment(Enum):
    """Alignements possibles pour DnD 5e."""
    LG = "Loyal Bon"
    NG = "Neutre Bon"
    CG = "Chaotique Bon"
    LN = "Loyal Neutre"
    TN = "Neutre"
    CN = "Chaotique Neutre"
    LE = "Loyal Mauvais"
    NE = "Neutre Mauvais"
    CE = "Chaotique Mauvais"


class Size(Enum):
    """Tailles possibles pour DnD 5e."""
    TINY = "Minuscule"
    SMALL = "Petit"
    MEDIUM = "Moyen"
    LARGE = "Grand"
    HUGE = "Énorme"
    GARGANTUAN = "Gigantesque"


@dataclass
class AbilityScores:
    """Caractéristiques principales."""
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    
    def get_modifier(self, ability: str) -> int:
        """Calcule le modificateur pour une caractéristique."""
        value = getattr(self, ability.lower(), 10)
        return (value - 10) // 2


@dataclass
class SavingThrow:
    """Jet de sauvegarde."""
    ability: str
    modifier: int = 0
    proficiency: bool = False


@dataclass
class Skill:
    """Compétence."""
    name: str
    ability: str
    modifier: int = 0
    proficiency: bool = False


@dataclass
class Action:
    """Action ou attaque."""
    name: str
    description: str = ""
    attack_bonus: Optional[int] = None
    damage: Optional[str] = None
    damage_type: Optional[str] = None


@dataclass
class Monster:
    """Modèle complet pour un PNJ/Monstre."""
    name: str = ""
    race: str = ""
    description: str = ""
    alignment: Optional[Alignment] = None
    size: Optional[Size] = None
    
    # Statistiques de base
    armor_class: Optional[int] = None
    hit_points: Optional[int] = None
    hit_dice: Optional[str] = None
    speed: Optional[str] = None
    
    # Caractéristiques
    ability_scores: AbilityScores = field(default_factory=AbilityScores)
    saving_throws: List[SavingThrow] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)
    
    # Défense
    damage_resistances: List[str] = field(default_factory=list)
    damage_immunities: List[str] = field(default_factory=list)
    damage_vulnerabilities: List[str] = field(default_factory=list)
    condition_immunities: List[str] = field(default_factory=list)
    
    # Sens
    senses: List[str] = field(default_factory=list)
    passive_perception: Optional[int] = None
    languages: List[str] = field(default_factory=list)
    challenge_rating: Optional[float] = None
    
    # Actions
    actions: List[Action] = field(default_factory=list)
    legendary_actions: List[Action] = field(default_factory=list)
    reactions: List[Action] = field(default_factory=list)
    
    # Autres
    treasure: Optional[str] = None
    notes: str = ""
    
    def to_dict(self) -> Dict:
        """Convertit le monstre en dictionnaire."""
        return {
            "name": self.name,
            "race": self.race,
            "description": self.description,
            "alignment": self.alignment.value if self.alignment else None,
            "size": self.size.value if self.size else None,
            "armor_class": self.armor_class,
            "hit_points": self.hit_points,
            "hit_dice": self.hit_dice,
            "speed": self.speed,
            "ability_scores": {
                "strength": self.ability_scores.strength,
                "dexterity": self.ability_scores.dexterity,
                "constitution": self.ability_scores.constitution,
                "intelligence": self.ability_scores.intelligence,
                "wisdom": self.ability_scores.wisdom,
                "charisma": self.ability_scores.charisma,
            },
            "saving_throws": [
                {"ability": st.ability, "modifier": st.modifier, "proficiency": st.proficiency}
                for st in self.saving_throws
            ],
            "skills": [
                {"name": sk.name, "ability": sk.ability, "modifier": sk.modifier, "proficiency": sk.proficiency}
                for sk in self.skills
            ],
            "damage_resistances": self.damage_resistances,
            "damage_immunities": self.damage_immunities,
            "damage_vulnerabilities": self.damage_vulnerabilities,
            "condition_immunities": self.condition_immunities,
            "senses": self.senses,
            "passive_perception": self.passive_perception,
            "languages": self.languages,
            "challenge_rating": self.challenge_rating,
            "actions": [
                {"name": a.name, "description": a.description, "attack_bonus": a.attack_bonus, 
                 "damage": a.damage, "damage_type": a.damage_type}
                for a in self.actions
            ],
            "legendary_actions": [
                {"name": la.name, "description": la.description}
                for la in self.legendary_actions
            ],
            "reactions": [
                {"name": r.name, "description": r.description}
                for r in self.reactions
            ],
            "treasure": self.treasure,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Monster':
        """Crée un Monster à partir d'un dictionnaire."""
        ability_scores = AbilityScores(
            strength=data.get("ability_scores", {}).get("strength", 10),
            dexterity=data.get("ability_scores", {}).get("dexterity", 10),
            constitution=data.get("ability_scores", {}).get("constitution", 10),
            intelligence=data.get("ability_scores", {}).get("intelligence", 10),
            wisdom=data.get("ability_scores", {}).get("wisdom", 10),
            charisma=data.get("ability_scores", {}).get("charisma", 10),
        )
        
        saving_throws = [
            SavingThrow(
                ability=st.get("ability", ""),
                modifier=st.get("modifier", 0),
                proficiency=st.get("proficiency", False)
            )
            for st in data.get("saving_throws", [])
        ]
        
        skills = [
            Skill(
                name=sk.get("name", ""),
                ability=sk.get("ability", ""),
                modifier=sk.get("modifier", 0),
                proficiency=sk.get("proficiency", False)
            )
            for sk in data.get("skills", [])
        ]
        
        actions = [
            Action(
                name=a.get("name", ""),
                description=a.get("description", ""),
                attack_bonus=a.get("attack_bonus"),
                damage=a.get("damage"),
                damage_type=a.get("damage_type")
            )
            for a in data.get("actions", [])
        ]
        
        legendary_actions = [
            Action(name=la.get("name", ""), description=la.get("description", ""))
            for la in data.get("legendary_actions", [])
        ]
        
        reactions = [
            Action(name=r.get("name", ""), description=r.get("description", ""))
            for r in data.get("reactions", [])
        ]
        
        alignment = None
        if data.get("alignment"):
            try:
                alignment = Alignment(data.get("alignment"))
            except ValueError:
                pass
        
        size = None
        if data.get("size"):
            try:
                size = Size(data.get("size"))
            except ValueError:
                pass
        
        return cls(
            name=data.get("name", ""),
            race=data.get("race", ""),
            description=data.get("description", ""),
            alignment=alignment,
            size=size,
            armor_class=data.get("armor_class"),
            hit_points=data.get("hit_points"),
            hit_dice=data.get("hit_dice"),
            speed=data.get("speed"),
            ability_scores=ability_scores,
            saving_throws=saving_throws,
            skills=skills,
            damage_resistances=data.get("damage_resistances", []),
            damage_immunities=data.get("damage_immunities", []),
            damage_vulnerabilities=data.get("damage_vulnerabilities", []),
            condition_immunities=data.get("condition_immunities", []),
            senses=data.get("senses", []),
            passive_perception=data.get("passive_perception"),
            languages=data.get("languages", []),
            challenge_rating=data.get("challenge_rating"),
            actions=actions,
            legendary_actions=legendary_actions,
            reactions=reactions,
            treasure=data.get("treasure"),
            notes=data.get("notes", ""),
        )
