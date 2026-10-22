"""
Calcul de difficulté de rencontre pour DnD 5e (tables du Guide du Maître).

À partir du nombre de joueurs, du niveau moyen et d'une difficulté souhaitée,
calcule le CR (niveau de difficulté) approprié pour le monstre.
"""

from typing import Dict, List, Tuple

from src.rules.stat_builder import CR_ENTRIES, cr_display, cr_xp

# Difficultés proposées dans l'UI (panel hardcodé).
DIFFICULTIES: List[Tuple[str, str]] = [
    ("easy", "Facile"),
    ("medium", "Moyen"),
    ("hard", "Difficile"),
    ("deadly", "Mortel"),
]

DIFFICULTY_LABELS = {key: label for key, label in DIFFICULTIES}
DIFFICULTY_KEYS = {label: key for key, label in DIFFICULTIES}

# Couleurs associées à chaque difficulté pour le label dynamique de l'UI.
DIFFICULTY_COLORS: Dict[str, str] = {
    "easy": "#4caf50",
    "medium": "#2196f3",
    "hard": "#ff9800",
    "deadly": "#f4433a",
}

# Seuils de PX par personnage selon le niveau et la difficulté (DMG, ch. 9).
# niveau : (facile, moyen, difficile, mortel)
XP_THRESHOLDS: Dict[int, Tuple[int, int, int, int]] = {
    1: (25, 50, 75, 100),
    2: (50, 100, 150, 200),
    3: (75, 150, 225, 400),
    4: (125, 250, 375, 500),
    5: (250, 500, 750, 1100),
    6: (300, 600, 900, 1400),
    7: (350, 750, 1100, 1700),
    8: (450, 900, 1400, 2100),
    9: (550, 1100, 1600, 2400),
    10: (600, 1200, 1900, 2800),
    11: (800, 1600, 2400, 3600),
    12: (1000, 2000, 3000, 4500),
    13: (1100, 2200, 3400, 5100),
    14: (1250, 2500, 3800, 5700),
    15: (1400, 2800, 4300, 6400),
    16: (1600, 3200, 4800, 7200),
    17: (2000, 3900, 5900, 8800),
    18: (2100, 4200, 6300, 9500),
    19: (2400, 4900, 7300, 10900),
    20: (2800, 5700, 8500, 12700),
}

DIFFICULTY_INDEX = {"easy": 0, "medium": 1, "hard": 2, "deadly": 3}


def party_xp_budget(party_size: int, avg_level: int, difficulty: str) -> int:
    """Budget de PX total de la rencontre selon le groupe et la difficulté."""
    level = max(1, min(20, int(avg_level)))
    index = DIFFICULTY_INDEX.get(difficulty, 1)
    per_player = XP_THRESHOLDS[level][index]
    return per_player * max(1, int(party_size))


def budget_to_cr(budget: int) -> float:
    """CR dont les PX sont les plus proches du budget.

    Un monstre unique doit consommer le budget complet de la
    rencontre : on arrondit au CR le plus proche (par défaut ou\n    excès), pas au CR inférieur — sinon le monstre n'utilise que
    la moitié du budget quand les CR adjacents sont éloignés.
    """
    best = 0.0
    best_diff = float("inf")
    for frac, _ in CR_ENTRIES:
        cr = float(frac)
        diff = abs(cr_xp(cr) - budget)
        if diff < best_diff:
            best_diff = diff
            best = cr
    return best


def encounter_cr(party_size: int, avg_level: int, difficulty: str) -> float:
    """CR du monstre pour un groupe de taille et niveau donnés, à la difficulté donnée."""
    return budget_to_cr(party_xp_budget(party_size, avg_level, difficulty))


def difficulty_summary(party_size: int, avg_level: int, difficulty: str) -> str:
    """Texte récapitulatif pour le label dynamique de l'UI."""
    cr = encounter_cr(party_size, avg_level, difficulty)
    budget = party_xp_budget(party_size, avg_level, difficulty)
    return f"CR {cr_display(cr)} ({cr_xp(cr)} PX / budget {budget} PX)"
