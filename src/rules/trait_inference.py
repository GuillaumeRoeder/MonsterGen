"""
Inférence de traits de créature à partir de la race et de la description.

Analyse le texte (race + description) pour déterminer un archétype crédible
(brute, discret, lanceur de sorts...), des armes cohérentes, un type de
dégâts pour l'action spéciale et une vitesse adaptée. Utilisé par
stat_builder pour que les statistiques générées collent au concept du
monstre décrit par l'utilisateur.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class InferredTraits:
    """Traits déduits de la race et de la description."""
    archetype: Optional[str] = None
    weapons: List[Tuple[str, str, int]] = field(default_factory=list)
    special_damage_type: Optional[str] = None
    special_name: Optional[str] = None
    speed: Optional[str] = None
    swim: bool = False
    fly: bool = False


# Mots-clés (minuscules, sans accents pour le match) -> archétype.
ARCHETYPE_KEYWORDS: List[Tuple[str, List[str]]] = [
    ("caster", [
        "mage", "magie", "magique", "sorci", "sorcier", "ensorcelle", "arcane",
        "arcanique", "sort", "sorts", "alchimiste", "rituel",
        "invocation", "occulte", "wizard", "enchante",
    ]),
    ("divin", [
        "pretre", "clerc", "culte", "devot", "sanctuaire",
        "temple", "chapelain", "celeste", "ange", "paladin", "benediction",
        "holy", "sacre", "divin", "spirituel",
    ]),
    ("charismatique", [
        "barde", "chante", "musique", "chef", "leader", "warlord",
        "roi", "reine", "prince", "princesse", "noble", "diplomate",
        "meneur", "orateur", "charism", "tribun",
    ]),
    ("sneaky", [
        "voleur", "assassin", "rodeur", "ninja",
        "embuscade", "furtif", "discret", "sournois", "ombre", "pickpocket",
        "espion", "roublard", "dague", "poison",
        "venin", "toxique", "venimeux", "scout", "traqueur", "silence",
    ]),
    ("brute", [
        "brute", "ogre", "troll", "golem", "geant", "colossal", "force",
        "muscle", "massif", "enorme", "ecrase",
        "cogne", "barbare", "berserk", "berserker", "furie", "rage", "furieux",
        "orc", "orque", "minotaure", "cyclope", "titan",
    ]),
]

# Mots-clés -> arme (nom, type de dégâts, dé). L'ordre compte.
WEAPON_KEYWORDS: List[Tuple[List[str], Tuple[str, str, int]]] = [
    (["dague", "poignard"], ("dague", "perforant", 4)),
    (["epee", "sabre", "rapiere", "katana"], ("épée longue", "tranchant", 8)),
    (["hache", "hachoir"], ("hache de bataille", "tranchant", 10)),
    (["marteau", "masse", "gourdin"], ("marteau de guerre", "contondant", 8)),
    (["lance", "javelot", "pieu", "harpon", "trident"], ("lance", "perforant", 6)),
    (["fleche", "arc ", "arbalete", "carquois"], ("arc long", "perforant", 8)),
    (["griffe", "serre", "talon", "patte"], ("griffes", "tranchant", 4)),
    (["morsure", "mord", "croc", "dent", "gueule", "mandibule"], ("morsure", "perforant", 6)),
    (["queue", "tentacule", "fouet"], ("queue fouettante", "contondant", 6)),
    (["bouclier", "ecusson"], ("coup de bouclier", "contondant", 4)),
]

# Mots-clés -> type de dégâts de l'action spéciale.
SPECIAL_DAMAGE_KEYWORDS: List[Tuple[List[str], str]] = [
    (["feu", "flamme", "brasier", "incendie", "brulant", "lave", "magma",
      "souffle de feu", "pyro"], "feu"),
    (["glace", "gel", "froid", "givre", "neige", "hivernal", "congel"], "froid"),
    (["foudre", "eclair", "tonnerre", "orage", "electr", "tempete"], "foudre"),
    (["poison", "venin", "toxine", "toxique", "venimeux", "miasme"], "poison"),
    (["acide", "corrosif", "bave", "dissolution"], "acide"),
    (["necrose", "sombre", "tenebre", "negati", "spectral",
      "fantome", "sang-drain"], "nécrotique"),
    (["radiant", "lumiere", "sacree", "aube", "soleil"], "radiant"),
    (["psychique", "mental", "esprit", "cauchemar", "terreur", "peur", "effroi", "hurlement"], "psychique"),
    (["onde", "supersonique", "rugissement", "sonore"], "tonnerre"),
]

SPECIAL_NAMES: List[Tuple[List[str], str]] = [
    (["souffle", "bave", "crache"], "Souffle"),
    (["gaz", "miasme", "nuage", "brume", "vapeur"], "Nuvée toxique"),
    (["hurlement", "cri", "rugissement"], "Hurlement terrifiant"),
    (["regard", "oeil", "gaze", "petrifi"], "Regard maléfique"),
    (["explosion", "burst", "nova", "detonation"], "Explosion"),
]

SPEED_KEYWORDS: List[Tuple[List[str], str]] = [
    (["vole", "aile", "plane", "levite", "ciel",
      "aerien", "volant"], "vol 9 m (12 cases)"),
    (["nage", "aquatique", "marin", "sous-marin", "ocean",
      "riviere", "poisson", "requin", "nageoire"], "nage 12 m (8 cases)"),
    (["fouisse", "tunnel", "souterrain", "creuse", "sable", "terrier", "mine"], "fouisse 4,50 m (3 cases)"),
    (["grimpe", "escalade", "arbre", "forestier"], "grimpe 4,50 m (3 cases)"),
]

_SLOW = ["massif", "lourd", "pesant", "colossal", "golem", "pierre", "roc", "tank"]
_FAST = ["rapide", "veloce", "fleche", "eclair", "felin",
         "guepard", "cheval", "coursier", "charge", "sprint", "cavale"]


def _normalize(text: str) -> str:
    """Minuscule + suppression des accents pour un match simple."""
    lowered = text.lower()
    return lowered.translate(str.maketrans("àâäéèêëîïôöùûüçñ", "aaaeeeeiioouuucn"))


def _count_matches(text: str, keywords: List[str]) -> int:
    """Nombre de mots-clés présents dans le texte."""
    return sum(1 for kw in keywords if kw in text)


def infer_traits(race: Optional[str], description: Optional[str]) -> InferredTraits:
    """Déduit archétype, armes, dégâts spéciaux et vitesse du texte."""
    race_stripped = _normalize(race or "")
    desc_stripped = _normalize(description or "")
    combined = f"{race_stripped} {desc_stripped}"

    # "lance des sorts", "lance un eclair" etc. ne sont pas des armes.
    import re
    combined_for_weapons = re.sub(
        r"lance\s+(?:des\s+|un\s+|d\s+)?(?:sorts?|eclairs?|foudre|rayons?|boules?)",
        "",
        combined,
    )

    traits = InferredTraits()

    # Archétype : la race pèse double par rapport à la description.
    best_archetype = None
    best_score = 0
    for archetype, keywords in ARCHETYPE_KEYWORDS:
        score = _count_matches(race_stripped, keywords) * 2 + _count_matches(desc_stripped, keywords)
        if score > best_score:
            best_score = score
            best_archetype = archetype
    if best_archetype:
        traits.archetype = best_archetype

    # Armes : premiers mots-clés trouvés (max 3).
    weapons: List[Tuple[str, str, int]] = []
    for keywords, weapon in WEAPON_KEYWORDS:
        if any(kw in combined_for_weapons for kw in keywords):
            weapons.append(weapon)
        if len(weapons) >= 3:
            break
    traits.weapons = weapons

    # Type de dégâts de l'action spéciale.
    for keywords, damage_type in SPECIAL_DAMAGE_KEYWORDS:
        if any(kw in combined for kw in keywords):
            traits.special_damage_type = damage_type
            break

    for keywords, name in SPECIAL_NAMES:
        if any(kw in combined for kw in keywords):
            traits.special_name = name
            break

    # Vitesse spéciale.
    for keywords, speed in SPEED_KEYWORDS:
        if any(kw in combined for kw in keywords):
            traits.speed = speed
            if "vol" in speed:
                traits.fly = True
            if "nage" in speed:
                traits.swim = True
            break

    # Vitesse de base ajustée au concept.
    if traits.speed is None:
        if any(kw in combined for kw in _FAST):
            traits.speed = "12 m (8 cases)"
        elif any(kw in combined for kw in _SLOW):
            traits.speed = "6 m (4 cases)"

    return traits
