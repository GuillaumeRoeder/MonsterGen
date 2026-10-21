"""
Génération de statistiques équilibrées pour DnD 5e, basée sur les tables du
Guide du Maître (Chapitre 9 : Créer un monstre). Aucune IA nécessaire :
toutes les valeurs sont calculées de façon déterministe à partir du CR.
"""

import random
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from src.models.monster import Monster, AbilityScores, Action, Size
from src.rules.trait_inference import InferredTraits, infer_traits

# Panel hardcodé des CR disponibles (affichés en fraction).
CR_ENTRIES: List[Tuple[Fraction, str]] = [
    (Fraction(0), "0"),
    (Fraction(1, 8), "1/8"),
    (Fraction(1, 4), "1/4"),
    (Fraction(1, 2), "1/2"),
] + [(Fraction(i), str(i)) for i in range(1, 31)]

CR_DISPLAY = {frac: label for frac, label in CR_ENTRIES}
CR_BY_DISPLAY = {label: frac for frac, label in CR_ENTRIES}


def cr_display(cr: Optional[float]) -> str:
    """Affiche un CR en fraction (1/8, 1/4, 1/2) plutôt qu'en décimal."""
    if cr is None:
        return "—"
    frac = Fraction(cr).limit_denominator(8)
    return CR_DISPLAY.get(frac, str(frac))


def parse_cr(text: str) -> Optional[float]:
    """Convertit un affichage de CR ('1/4', '3') en valeur numérique."""
    text = text.strip()
    try:
        if "/" in text:
            num, _, den = text.partition("/")
            return float(Fraction(int(num), int(den)))
        return float(Fraction(text))
    except (ValueError, ZeroDivisionError):
        return None


def cr_xp(cr: Optional[float]) -> int:
    """Points d'expérience pour un CR donné (table officielle 5e)."""
    xp_table = {
        0.0: 10, 0.125: 25, 0.25: 50, 0.5: 100,
        1: 200, 2: 450, 3: 700, 4: 1100, 5: 1800,
        6: 2300, 7: 2900, 8: 3900, 9: 5000, 10: 5900,
        11: 7200, 12: 8400, 13: 10000, 14: 11500, 15: 13000,
        16: 15000, 17: 18000, 18: 20000, 19: 22000, 20: 25000,
        21: 33000, 22: 41000, 23: 50000, 24: 62000, 25: 75000,
        26: 90000, 27: 105000, 28: 120000, 29: 135000, 30: 155000,
    }
    if cr is None:
        return 0
    key = float(Fraction(cr).limit_denominator(8))
    return xp_table.get(key, 0)


# Tables DMG : CR -> (bonus de maîtrise, CA, PV min, PV max, bonus d'attaque,
# dégâts/tour min, dégâts/tour max, DD de sauvegarde)
DMG_TABLE: Dict[float, Tuple[int, int, int, int, int, int, int, int]] = {
    0.0: (2, 13, 1, 10, 3, 0, 1, 13),
    0.125: (2, 13, 2, 20, 3, 2, 3, 13),
    0.25: (2, 13, 21, 35, 5, 4, 8, 13),
    0.5: (2, 13, 36, 50, 5, 5, 10, 13),
    1: (2, 13, 51, 85, 5, 6, 12, 13),
    2: (2, 13, 86, 100, 6, 10, 15, 13),
    3: (2, 13, 101, 115, 6, 15, 20, 13),
    4: (2, 14, 116, 130, 7, 20, 25, 14),
    5: (3, 15, 131, 145, 7, 30, 35, 15),
    6: (3, 15, 146, 160, 8, 35, 40, 15),
    7: (3, 15, 161, 175, 8, 40, 45, 15),
    8: (3, 15, 176, 190, 9, 50, 55, 15),
    9: (4, 16, 191, 205, 9, 56, 60, 16),
    10: (4, 17, 206, 220, 10, 62, 67, 16),
    11: (4, 17, 221, 235, 10, 66, 72, 17),
    12: (4, 17, 236, 250, 10, 73, 78, 17),
    13: (5, 18, 251, 265, 11, 78, 84, 18),
    14: (5, 18, 266, 280, 11, 84, 92, 18),
    15: (5, 18, 281, 295, 12, 92, 99, 18),
    16: (5, 18, 296, 310, 12, 100, 106, 18),
    17: (6, 19, 311, 325, 13, 106, 113, 19),
    18: (6, 19, 326, 340, 13, 114, 121, 19),
    19: (6, 19, 341, 355, 13, 122, 128, 19),
    20: (6, 19, 356, 400, 14, 132, 139, 19),
    21: (7, 19, 401, 445, 14, 141, 148, 20),
    22: (7, 19, 446, 490, 14, 151, 159, 20),
    23: (7, 19, 491, 535, 15, 162, 170, 20),
    24: (7, 19, 536, 580, 15, 173, 181, 21),
    25: (8, 19, 581, 625, 16, 182, 190, 21),
    26: (8, 19, 626, 670, 16, 192, 201, 21),
    27: (8, 19, 671, 715, 17, 202, 211, 22),
    28: (8, 19, 716, 760, 17, 212, 221, 22),
    29: (9, 19, 761, 805, 18, 222, 232, 22),
    30: (9, 19, 806, 850, 19, 233, 243, 24),
}

HIT_DIE_BY_SIZE = {
    Size.TINY: 4,
    Size.SMALL: 6,
    Size.MEDIUM: 8,
    Size.LARGE: 10,
    Size.HUGE: 12,
    Size.GARGANTUAN: 20,
}

# Archétypes de créatures : répartition des priorités de caractéristiques.
ARCHETYPES = [
    ("brute", ["strength", "constitution", "charisma", "wisdom", "dexterity", "intelligence"]),
    ("sneaky", ["dexterity", "constitution", "charisma", "wisdom", "intelligence", "strength"]),
    ("caster", ["intelligence", "constitution", "wisdom", "dexterity", "charisma", "strength"]),
    ("divin", ["wisdom", "constitution", "charisma", "dexterity", "strength", "intelligence"]),
    ("charismatique", ["charisma", "constitution", "wisdom", "dexterity", "intelligence", "strength"]),
]

WEAPONS = [
    ("épée longue", "tranchant", 8),
    ("hache de bataille", "tranchant", 10),
    ("marteau de guerre", "contondant", 8),
    ("lance", "perforant", 6),
    ("griffes", "tranchant", 4),
    ("morsure", "perforant", 6),
    ("queue fouettante", "contondant", 6),
    ("coup de bouclier", "contondant", 4),
]

DAMAGE_DICE = [4, 6, 8, 10, 12]


def _cr_key(cr: float) -> float:
    """Ramène n'importe quel CR à l'entrée de table la plus proche.

    Un CR imprévu (0.3, 7.5, 45...) ne doit jamais faire KeyError :
    on borne à la table officielle (0 à 30).
    """
    frac = Fraction(cr).limit_denominator(8)
    known = sorted(DMG_TABLE.keys())
    if frac in DMG_TABLE:
        return float(frac)
    value = float(frac)
    if value <= known[0]:
        return known[0]
    if value >= known[-1]:
        return known[-1]
    lower = max(k for k in known if k < value)
    return lower


def _score_from_modifier(mod: int) -> int:
    """Convertit un modificateur en valeur de caractéristique."""
    if mod >= 0:
        return mod * 2 + 10
    return mod * 2 + 10


def build_ability_scores(cr: float, rng: random.Random,
                         archetype: Optional[str] = None) -> Tuple[AbilityScores, str]:
    """Génère 6 caractéristiques équilibrées pour le CR donné."""
    prof, _, _, _, atk_bonus, _, _, _ = DMG_TABLE[_cr_key(cr)]

    valid = [a for a in ARCHETYPES if a[0] == archetype]
    if archetype is not None and valid:
        name, priorities = valid[0]
    else:
        name, priorities = rng.choice(ARCHETYPES)

    # Le bonus d'attaque cible = mod de caractéristique + maîtrise.
    # La stat principale découle donc directement du tableau DMG.
    primary_mod = atk_bonus - prof

    # Répartition des modificateurs : la stat principale correspond au bonus
    # d'attaque attendu, puis on décroît progressivement.
    mods = {}
    current = primary_mod
    for ability in priorities:
        mods[ability] = current
        current = max(current - 1, -4)

    # Petite variation aléatoire sur les stats secondaires.
    for ability in priorities[2:]:
        mods[ability] = max(mods[ability] + rng.randint(-1, 1), -4)

    scores = AbilityScores(
        strength=_score_from_modifier(mods["strength"]),
        dexterity=_score_from_modifier(mods["dexterity"]),
        constitution=_score_from_modifier(mods["constitution"]),
        intelligence=_score_from_modifier(mods["intelligence"]),
        wisdom=_score_from_modifier(mods["wisdom"]),
        charisma=_score_from_modifier(mods["charisma"]),
    )
    return scores, name


def build_hit_points(cr: float, con_mod: int, size: Optional[Size], rng: random.Random) -> Tuple[int, str]:
    """Génère les PV et les dés de vie cohérents avec le CR et la taille.

    Robuste quel que soit le modificateur de Constitution : on augmente le
    nombre de dés seulement si la moyenne par dé reste positive, sinon on
    ajuste le nombre de dés sans laisser la formule diverger.
    """
    _, _, hp_min, hp_max, _, _, _, _ = DMG_TABLE[_cr_key(cr)]
    target_hp = rng.randint(hp_min, hp_max)

    die = HIT_DIE_BY_SIZE.get(size or Size.MEDIUM, 8)
    avg_face = die / 2 + 0.5

    # Le modificateur appliqué aux dés est borné pour que la moyenne par dé
    # reste >= 1 : une CON très basse influe sur le nombre de dés, pas sur
    # un modificateur qui rendrait les dés incohérents avec les PV.
    dice_mod = max(con_mod, -(die // 2 - 1))
    per_die = avg_face + dice_mod

    num_dice = max(1, round(target_hp / per_die))
    hp = round(num_dice * per_die)

    # Garde-fou : les PV ne doivent pas diverger de la cible DMG.
    if not (target_hp * 0.5 <= hp <= target_hp * 2):
        num_dice = max(1, round(target_hp / avg_face))
        hp = target_hp
        dice_mod = 0

    if dice_mod > 0:
        hit_dice = f"{num_dice}d{die} + {num_dice * dice_mod}"
    elif dice_mod == 0:
        hit_dice = f"{num_dice}d{die}"
    else:
        hit_dice = f"{num_dice}d{die} {num_dice * dice_mod}"

    return max(1, hp), hit_dice


# Classes d'Armure officielles DnD 5e : (CA de base, bonus DEX max admis).
ARMOR_TYPES = {
    "armure matelassée": (11, 0),
    "armure de peausserie": (12, 0),
    "armure de cuir": (11, None),
    "armure cloutée": (12, 2),
    "armure d'écailles": (14, 2),
    "cotte de mailles": (13, 2),
    "armure de plaques": (18, 0),
    "armure de plates": (18, 0),
    "harnois": (18, 0),
}

# Objets magiques conférant un bonus de CA.
MAGIC_AC_ITEMS = {
    "anneau magique": 1,
    "amulette": 1,
    "bâton magique": 1,
    "baguette": 1,
    "cape": 1,
}



def _item_name(item: str) -> str:
    """Nom d'objet d'inventaire, sans le detail entre parentheses."""
    return item.strip().lower().split(" (")[0]

def armor_class_detail(ac: int, equipment: Optional[str]) -> Optional[str]:
    """Détail de la CA dérivé de l'équipement, pour l'affichage.

    Retourne par ex. « armure de plates, bouclier » ou None si aucune
    pièce d'équipement protectrice n'est identifiable.
    """
    if not equipment:
        return None
    items = [_item_name(i) for i in equipment.split(",")]
    parts = []
    for item in items:
        if item in ARMOR_TYPES:
            parts.append(item)
    if "bouclier" in items:
        parts.append("bouclier")
    for item in items:
        if item in MAGIC_AC_ITEMS:
            parts.append(f"{item} (+1)")
            break
    return ", ".join(parts) if parts else None


def build_armor_class(cr: float, dex_mod: int, rng: random.Random,
                      equipment: Optional[str] = None) -> int:
    """Génère une CA cohérente avec le CR.

    Si l'équipement est fourni, la CA est dérivée de l'armure portée
    (tables officielles DnD 5e) + bouclier (+2) + objet magique (+1),
    ajustée vers la cible du CR si l'écart devient irréaliste.
    """
    _, target_ac, _, _, _, _, _, _ = DMG_TABLE[_cr_key(cr)]

    if not equipment:
        armor_bonus = max(0, target_ac - 10 - dex_mod + rng.randint(-1, 1))
        return 10 + dex_mod + armor_bonus

    items = [_item_name(i) for i in equipment.split(",")]

    # Armure portée : la meilleure trouvée
    base_ac = None
    dex_cap = None
    for item in items:
        if item in ARMOR_TYPES:
            armor_ac, armor_cap = ARMOR_TYPES[item]
            if base_ac is None or armor_ac > base_ac:
                base_ac = armor_ac
                dex_cap = armor_cap

    if base_ac is None:
        # Pas d'armure : CA naturelle estimée pour le CR
        armor_bonus = max(0, target_ac - 10 - dex_mod + rng.randint(-1, 1))
        ac = 10 + dex_mod + armor_bonus
    else:
        effective_dex = dex_mod if dex_cap is None else min(dex_mod, dex_cap)
        ac = base_ac + effective_dex

    # Bouclier
    if "bouclier" in items:
        ac += 2

    # Objets magiques protecteurs
    for item in items:
        if item in MAGIC_AC_ITEMS:
            ac += MAGIC_AC_ITEMS[item]
            break

    # Ajustement doux vers la cible du CR : un grand écart (monstre
    # déséquilibré pour son CR) est resserré d'au maximum 2 points.
    if ac < target_ac - 2:
        ac = min(ac + 2, target_ac)
    elif ac > target_ac + 2:
        ac = max(ac - 2, target_ac)

    return ac


def build_actions(cr: float, scores: AbilityScores, rng: random.Random,
                  traits: Optional[InferredTraits] = None,
                  equipment: Optional[str] = None) -> List[Action]:
    """Génère 2-3 actions de mélée/attaque équilibrées pour le CR.

    Si des traits inférés (race/description) sont fournis, les armes
    détectées sont utilisées à la place du tirage aléatoire.
    """
    prof, _, _, _, atk_bonus, dmg_min, dmg_max, save_dc = DMG_TABLE[_cr_key(cr)]

    num_attacks = 3 if cr >= 10 else (2 if cr >= 5 else 1)
    actions: List[Action] = []

    weapon_pool = list(traits.weapons) if traits and traits.weapons else []

    # Les armes portees dans l'inventaire completent le pool.
    if equipment:
        natural = {"griffes", "morsure", "queue fouettante"}
        for item in equipment.split(","):
            item = _item_name(item)
            for weapon in WEAPONS:
                if weapon[0] == item and weapon[0] not in natural \
                        and weapon not in weapon_pool:
                    weapon_pool.append(weapon)

    for i in range(min(num_attacks, len(WEAPONS))):
        if weapon_pool:
            weapon_name, damage_type, base_die = weapon_pool.pop(0)
        else:
            weapon_name, damage_type, base_die = rng.choice(WEAPONS)
        target_damage = rng.randint(dmg_min, max(dmg_min, dmg_max))

        num_dice = max(1, target_damage // (base_die + 1))
        flat = max(0, target_damage - num_dice * (base_die // 2 + 1))
        damage = f"{num_dice}d{base_die} + {flat}" if flat else f"{num_dice}d{base_die}"

        actions.append(Action(
            name=f"Attaque : {weapon_name.capitalize()}",
            description=f"Attaque d'arme au corps à corps : +{atk_bonus} au toucher, "
                        f"portée 1,50 m, une cible. Dégâts : {damage} dégâts {damage_type}.",
            attack_bonus=atk_bonus,
            damage=damage,
            damage_type=damage_type,
        ))

    # Une action spéciale avec jet de sauvegarde pour les CR >= 2.
    if cr >= 2:
        special_name = "Souffle affaiblissant"
        if traits and traits.special_name:
            special_name = traits.special_name
        special_damage = "nécrotique"
        if traits and traits.special_damage_type:
            special_damage = traits.special_damage_type
        actions.append(Action(
            name=f"{special_name} (Recharge 5-6)",
            description=f"Chaque créature dans un cône de 4,50 m doit réussir un "
                        f"jet de sauvegarde de DD {save_dc} ou subir {max(2, dmg_min // 2)}d6 "
                        f"dégâts {special_damage} et être neutralisée jusqu'à la fin de son prochain tour.",
        ))

    return actions


def build_balanced_monster(cr: float, base: Optional[Monster] = None,
                           seed: Optional[int] = None) -> Monster:
    """Construit un monstre complet et équilibré pour le CR donné.

    Ne propose pas de choix : les valeurs sont remplies directement à partir
    des tables officielles du Guide du Maître.
    """
    rng = random.Random(seed)
    monster = base if base is not None else Monster()
    if seed is None:
        rng = random.Random()

    monster.challenge_rating = cr

    # Traits inférés de la race et de la description pour des stats crédibles.
    traits = infer_traits(monster.race, monster.description)

    scores, archetype = build_ability_scores(cr, rng, archetype=traits.archetype)
    monster.ability_scores = scores
    monster.proficiency_bonus = proficiency_bonus(cr)
    con_mod = scores.get_modifier("constitution")
    dex_mod = scores.get_modifier("dexterity")

    # Inventaire d'abord : la CA en dépend (armure, bouclier, objets
    # magiques), et les actions utilisent les armes portées.
    monster.notes = build_equipment(traits, rng)

    monster.armor_class = build_armor_class(cr, dex_mod, rng,
                                            equipment=monster.notes)
    monster.hit_points, monster.hit_dice = build_hit_points(cr, con_mod, monster.size, rng)

    # Vitesse : régénérée à chaque équilibrage. Les traits inférés de la
    # description (rapide, vol, nage...) priment ; sinon vitesse standard.
    monster.speed = traits.speed or "9 m (6 cases)"

    if not monster.passive_perception:
        monster.passive_perception = 10 + scores.get_modifier("wisdom")

    # Compétences / résistances / immunités : les traits inférés de la
    # description prennent le dessus — l'équilibrage régénère les stats
    # en tenant compte du concept décrit.
    if traits.skills:
        from src.models.monster import Skill
        monster.skills = [Skill(name=name, ability="", proficiency=True)
                          for name in traits.skills]
    elif not monster.skills:
        monster.skills = []

    if traits.resistances:
        monster.damage_resistances = list(traits.resistances)

    if traits.immunities:
        monster.damage_immunities = list(traits.immunities)

    monster.actions = build_actions(cr, scores, rng, traits=traits,
                                    equipment=monster.notes)

    return monster


# Effets détaillés des objets d'inventaire (armes, armures, magiques).
EQUIPMENT_EFFECTS = {
    "dague": "perforant 1d4, légère, lancer (portée 6/18 m)",
    "épée courte": "perforant 1d6, légère, souple",
    "épée longue": "tranchant 1d8, polyvalente (1d10)",
    "rapière": "perforant 1d8, souple",
    "hache de bataille": "tranchant 1d8, polyvalente (1d10)",
    "marteau de guerre": "contondant 1d8, polyvalent (1d10)",
    "lance": "perforant 1d6, lancer (portée 6/18 m)",
    "arc long": "perforant 1d8, portée 45/180 m, deux mains",
    "bouclier": "+2 à la CA",
    "armure matelassée": "CA 11 + DEX",
    "armure de peausserie": "CA 12 + DEX",
    "armure de cuir": "CA 11 + DEX",
    "armure cloutée": "CA 12 + DEX (max 2)",
    "cotte de mailles": "CA 13 + DEX (max 2)",
    "armure d'écailles": "CA 14 + DEX (max 2)",
    "armure de plates": "CA 18, discrétion désavantagée",
    "anneau magique": "objet magique, +1 à la CA",
    "amulette": "objet magique, +1 à la CA",
    "bâton magique": "objet magique, focaliseur arcanique, +1 à la CA",
    "baguette": "objet magique, focaliseur arcanique",
    "cape": "objet magique, +1 à la CA",
    "grimoire": "livre de sorts",
    "potion de soin": "2d4+2 PV restaurés",
    "symbole sacré": "focaliseur divin",
}


def _describe_equipment(equipment: List[str]) -> str:
    """Formate l'inventaire : « objet (effet) », une virgule par élément."""
    parts = []
    for item in equipment:
        effect = EQUIPMENT_EFFECTS.get(item.lower())
        parts.append(f"{item} ({effect})" if effect else item)
    return ", ".join(parts)


def build_equipment(traits, rng: random.Random) -> Optional[str]:
    """Construit la ligne d'inventaire détaillée du monstre.

    Priorité à l'équipement détecté dans la description ; sinon un
    équipement standard selon l'archétype. Uniquement des éléments
    importants (armes, armures, boucliers, objets magiques), chacun
    accompagné de ses effets (dégâts, CA, pouvoir).
    """
    if traits.equipment:
        return _describe_equipment(traits.equipment)

    archetype_equipment = {
        "brute": ["hache de bataille", "armure de cuir"],
        "sneaky": ["dague", "arc long", "armure de cuir"],
        "caster": ["bâton magique", "grimoire"],
        "divin": ["symbole sacré", "armure matelassée"],
        "charismatique": ["rapière", "armure de cuir"],
    }
    fallback = {
        True: ["épée longue", "bouclier", "armure de cuir"],
        False: [],
    }
    if traits.archetype and traits.archetype in archetype_equipment:
        return _describe_equipment(archetype_equipment[traits.archetype])

    # Bête (armes naturelles) : pas d'inventaire. Sinon équipement
    # standard de créature civilisée.
    if traits.weapons and all(w[0] in ("griffes", "morsure", "queue fouettante") for w in traits.weapons):
        return None
    return _describe_equipment(fallback[True])


def proficiency_bonus(cr: float) -> int:
    """Bonus de maîtrise pour un CR donné."""
    return DMG_TABLE[_cr_key(cr)][0]
