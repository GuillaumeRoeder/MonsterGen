"""
Génération et évaluation de rencontres multi-monstres pour DnD 5e.

Étend src/rules/encounter.py (mono-monstre) au cas d'une rencontre
composée de plusieurs monstres :

- Budget de PX par difficulté (tables DMG ch. 9, déjà présentes).
- Multiplicateurs de PX par nombre de monstres (DMG ch. 9).
- Génération depuis la bibliothèque : quand les monstres choisis ont
  un CR trop haut (ou trop bas) pour la difficulté visée, le système
  estime combien d'exemplaires de chaque monstre il faut pour
  converger vers le budget — et explique les cas impossibles.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.rules.encounter import (
    DIFFICULTY_COLORS,
    DIFFICULTY_LABELS,
    XP_THRESHOLDS,
    party_xp_budget,
)
from src.rules.stat_builder import cr_display, cr_xp

# Multiplicateur de PX selon le nombre de monstres (DMG ch. 9).
# La tranche est indexée par le nombre total de monstres.
XP_MULTIPLIERS: List[Tuple[int, float]] = [
    (1, 1.0),
    (2, 1.5),
    (3, 2.0),
    (6, 2.5),
    (10, 3.0),
    (14, 4.0),
]


def xp_multiplier(monster_count: int) -> float:
    """Multiplicateur de difficulté pour un nombre total de monstres."""
    count = max(1, int(monster_count))
    for threshold, multiplier in XP_MULTIPLIERS:
        if count <= threshold:
            return multiplier
    return XP_MULTIPLIERS[-1][1]


def difficulty_from_xp(party_size: int, avg_level: int, adjusted_xp: int) -> str:
    """Difficulté réelle d'une rencontre à partir de ses PX ajustés.

    Retourne la clé de difficulté ('easy', 'medium', 'hard', 'deadly')
    la plus élevée dont le seuil est atteint, ou 'easy' en dessous du
    seuil facile (rencontre anecdotique).
    """
    level = max(1, min(20, int(avg_level)))
    size = max(1, int(party_size))
    thresholds = XP_THRESHOLDS[level]
    keys = ["easy", "medium", "hard", "deadly"]
    result = "easy"
    for key, per_player in zip(keys, thresholds):
        if adjusted_xp >= per_player * size:
            result = key
    return result


@dataclass
class EncounterMonster:
    """Un monstre de la rencontre : sa fiche + un nombre d'exemplaires."""
    name: str
    challenge_rating: Optional[float]
    count: int = 1

    @property
    def xp(self) -> int:
        return cr_xp(self.challenge_rating)

    @property
    def total_xp(self) -> int:
        return self.xp * max(1, self.count)


@dataclass
class Encounter:
    """Une rencontre complète : monstres, groupe cible et difficulté visée."""
    name: str = ""
    party_size: int = 4
    party_level: int = 2
    difficulty: str = "medium"
    description: str = ""
    monsters: List[EncounterMonster] = field(default_factory=list)
    scenario: str = ""

    @property
    def monster_count(self) -> int:
        return sum(max(1, m.count) for m in self.monsters)

    @property
    def raw_xp(self) -> int:
        """PX bruts : somme des PX de tous les exemplaires."""
        return sum(m.total_xp for m in self.monsters)

    @property
    def adjusted_xp(self) -> int:
        """PX ajustés : PX bruts × multiplicateur de nombre de monstres."""
        return round(self.raw_xp * xp_multiplier(self.monster_count))

    @property
    def budget(self) -> int:
        """Budget de PX de la difficulté visée pour ce groupe."""
        return party_xp_budget(self.party_size, self.party_level, self.difficulty)

    @property
    def actual_difficulty(self) -> str:
        """Difficulté réelle de la rencontre (PX ajustés vs seuils)."""
        return difficulty_from_xp(
            self.party_size, self.party_level, self.adjusted_xp
        )

    def to_dict(self) -> Dict:
        """Sérialisation JSON (sauvegarde bibliothèque de rencontres)."""
        return {
            "name": self.name,
            "party_size": self.party_size,
            "party_level": self.party_level,
            "difficulty": self.difficulty,
            "description": self.description,
            "monsters": [
                {"name": m.name, "challenge_rating": m.challenge_rating,
                 "count": m.count}
                for m in self.monsters
            ],
            "scenario": self.scenario,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Encounter":
        """Désérialisation depuis un dictionnaire JSON."""
        monsters = [
            EncounterMonster(
                name=m.get("name", ""),
                challenge_rating=m.get("challenge_rating"),
                count=max(1, int(m.get("count", 1) or 1)),
            )
            for m in data.get("monsters", [])
        ]
        return cls(
            name=data.get("name", ""),
            party_size=max(1, int(data.get("party_size", 4) or 4)),
            party_level=max(1, min(20, int(data.get("party_level", 2) or 2))),
            difficulty=data.get("difficulty", "medium"),
            description=data.get("description", ""),
            monsters=monsters,
            scenario=data.get("scenario", ""),
        )

    def summary_parts(self) -> Tuple[str, str]:
        """Résumé lisible (texte + couleur selon la difficulté réelle)."""
        target = DIFFICULTY_LABELS.get(self.difficulty, self.difficulty)
        actual = DIFFICULTY_LABELS.get(self.actual_difficulty, self.actual_difficulty)
        color = DIFFICULTY_COLORS.get(self.actual_difficulty, "#e0e0e0")
        text = (
            f"{self.adjusted_xp} PX ajustés / budget {self.budget} PX "
            f"({target}) — difficulté réelle : {actual}"
        )
        return text, color


def evaluate(encounter: Encounter) -> Dict:
    """Évaluation complète d'une rencontre (pour le label temps réel de l'UI)."""
    return {
        "raw_xp": encounter.raw_xp,
        "adjusted_xp": encounter.adjusted_xp,
        "budget": encounter.budget,
        "multiplier": xp_multiplier(encounter.monster_count),
        "monster_count": encounter.monster_count,
        "actual_difficulty": encounter.actual_difficulty,
        "actual_label": DIFFICULTY_LABELS.get(encounter.actual_difficulty, ""),
        "actual_color": DIFFICULTY_COLORS.get(encounter.actual_difficulty, "#e0e0e0"),
        "matches_target": encounter.actual_difficulty == encounter.difficulty,
    }


def suggest_count(monster_cr: Optional[float], party_size: int, avg_level: int,
                  difficulty: str) -> int:
    """Nombre d'exemplaires d'un monstre pour atteindre la difficulté visée.

    Cherche le nombre n (1 à 30) dont les PX ajustés (n × PX ×
    multiplicateur(n)) s'approchent le plus du budget de la difficulté,
    sans jamais le dépasser massivement : les petits écarts sont tolérés,
    mais on préfère sous-estimer légèrement (le renfort est plus simple
    à gérer en jeu qu'un TPK).
    """
    budget = party_xp_budget(party_size, avg_level, difficulty)
    xp = cr_xp(monster_cr)
    if xp <= 0:
        return 1

    best_n = 1
    best_score = None
    for n in range(1, 31):
        adjusted = round(xp * n * xp_multiplier(n))
        # Score : pénalise le dépassement du budget plus fortement que
        # l'approximation par défaut (dépassement = TPK potentiel).
        if adjusted > budget:
            over = adjusted - budget
            score = over * 2.0
        else:
            score = budget - adjusted
        if best_score is None or score < best_score:
            best_score = score
            best_n = n
        if adjusted > budget * 2:
            break
    return best_n


def fill_counts(encounter: Encounter) -> Encounter:
    """Complète les quantités manquantes d'une rencontre (count <= 0).

    Pour chaque monstre sans quantité, suggère le nombre d'exemplaires
    pour atteindre la difficulté visée, puis vérifie la cohérence
    globale : si le total dépasse le budget, réduit les quantités les
    plus grandes en priorité (les monstres nombreux font plus vite
    dévier la rencontre que les monstres solitaires).
    """
    for m in encounter.monsters:
        if m.count is None or m.count <= 0:
            m.count = suggest_count(
                m.challenge_rating,
                encounter.party_size,
                encounter.party_level,
                encounter.difficulty,
            )
    return encounter


@dataclass
class SelectionIssue:
    """Diagnostic d'une sélection de monstres incompatible avec la difficulté."""
    kind: str          # 'too_strong' | 'too_weak' | 'fits'
    message: str
    suggestions: List[str] = field(default_factory=list)


def check_selection(monsters: List[EncounterMonster], party_size: int,
                    avg_level: int, difficulty: str) -> List[SelectionIssue]:
    """Analyse une sélection de monstres (1 exemplaire de chaque) face au budget.

    Détecte les cas dégénérés que la génération de quantités ne peut pas
    résoudre seule :
    - Un monstre seul dépasse déjà le budget (CR trop haut) : suggère
      soit une difficulté supérieure, soit de baisser son CR.
    - Le total à 1 exemplaire dépasse largement le budget.
    - Chaque monstre est si faible que même 30 exemplaires n'atteignent
      pas le budget (CR trop bas pour le groupe).
    """
    budget = party_xp_budget(party_size, avg_level, difficulty)
    issues: List[SelectionIssue] = []

    # Cas 1 : un monstre solitaire dépasse le budget
    for m in monsters:
        if m.xp > budget:
            issues.append(SelectionIssue(
                kind="too_strong",
                message=(
                    f"« {m.name} » (CR {cr_display(m.challenge_rating)}, "
                    f"{m.xp} PX) dépasse à lui seul le budget de "
                    f"{budget} PX pour cette difficulté."
                ),
                suggestions=[
                    "Choisir une difficulté supérieure",
                    "Remplacer le monstre par une version plus faible",
                    "Garder le monstre et accepter une rencontre mortelle "
                    "(délibérée)",
                ],
            ))

    # Cas 2 : le total de la sélection (1 exemplaire chacun) explose le budget
    total = sum(m.xp for m in monsters)
    if total > budget * 1.5 and len(monsters) > 1:
        issues.append(SelectionIssue(
            kind="too_strong",
            message=(
                f"La sélection complète ({total} PX à 1 exemplaire chacun) "
                f"dépasse largement le budget de {budget} PX : la rencontre "
                f"sera au-dessus de la difficulté visée."
            ),
            suggestions=[
                "Retirer un ou plusieurs monstres de la sélection",
                "Choisir une difficulté supérieure",
            ],
        ))

    # Cas 3 : monstre trop faible pour espérer atteindre le budget
    max_count = 30
    for m in monsters:
        best = round(m.xp * max_count * xp_multiplier(max_count))
        if best < budget * 0.5:
            issues.append(SelectionIssue(
                kind="too_weak",
                message=(
                    f"« {m.name} » (CR {cr_display(m.challenge_rating)}) est "
                    f"trop faible : même {max_count} exemplaires n'atteignent "
                    f"pas la moitié du budget de {budget} PX."
                ),
                suggestions=[
                    "Choisir une difficulté inférieure",
                    "Remplacer le monstre par une version plus forte",
                ],
            ))

    return issues


def build_auto_encounter(monsters: List[EncounterMonster], party_size: int,
                         avg_level: int, difficulty: str,
                         name: str = "") -> Tuple[Encounter, List[SelectionIssue]]:
    """Construit une rencontre depuis une sélection de monstres.

    Stratégie de gestion des CR inadaptés :
    1. Détecte les cas impossibles (monstre trop fort pour le budget :
       suggère d'ajuster, mais ne bloque pas — le MJ décide).
    2. Ajuste les quantités pour converger vers le budget (les monstres
       forts restent en faible nombre, les faibles en grand nombre).
    3. Réduit les quantités si le total dépasse le budget après ajustement.
    """
    encounter = Encounter(
        name=name,
        party_size=party_size,
        party_level=avg_level,
        difficulty=difficulty,
        monsters=[EncounterMonster(m.name, m.challenge_rating, 1)
                  for m in monsters],
    )
    issues = check_selection(
        encounter.monsters, party_size, avg_level, difficulty
    )

    # Un monstre qui dépasse déjà le budget reste seul exemplaire :
    # on ne multiplie pas les quantités, le MJ ajustera la difficulté.
    too_strong = any(i.kind == "too_strong" for i in issues)

    if not too_strong:
        # Chaque monstre reçoit la quantité qui l'amène au budget,
        # puis on répartit le reliquat : les monstres dont le CR est
        # le plus proche du budget unitaire reçoivent le surplus.
        budget = encounter.budget
        for m in encounter.monsters:
            m.count = suggest_count(
                m.challenge_rating, party_size, avg_level, difficulty
            )

        # Réduction si les PX ajustés dépassent le budget de plus de 10 %
        # (sinon la rencontre est trop difficile par rapport à la cible).
        while (encounter.adjusted_xp > budget * 1.10
               and any(m.count > 1 for m in encounter.monsters)):
            biggest = max(
                (m for m in encounter.monsters if m.count > 1),
                key=lambda m: m.count,
            )
            biggest.count -= 1

    return encounter, issues


def generate_random_encounter(monsters: List[EncounterMonster],
                               party_size: int, avg_level: int,
                               difficulty: str,
                               rng=None) -> Tuple[Encounter, List[SelectionIssue]]:
    """Génère une rencontre aléatoire depuis un pool de monstres.

    Choisit un sous-ensemble du pool (1 à 4 monstres distincts) puis
    laisse build_auto_encounter ajuster les quantités pour la
    difficulté visée.
    """
    import random as _random

    rng = rng or _random
    if not monsters:
        return Encounter(party_size=party_size, party_level=avg_level,
                         difficulty=difficulty), []
    pool = list(monsters)
    rng.shuffle(pool)
    picks = pool[:rng.randint(1, min(4, len(pool)))]
    return build_auto_encounter(
        picks, party_size, avg_level, difficulty,
        name="Rencontre générée",
    )
