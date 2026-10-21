"""
Inférence de traits de créature à partir de la race et de la description.

Analyse le texte (race + description) pour déterminer un archétype crédible
(brute, discret, lanceur de sorts...), des armes cohérentes, un type de
dégâts pour l'action spéciale et une vitesse adaptée. Utilisé par
stat_builder pour que les statistiques générées collent au concept du
monstre décrit par l'utilisateur.
"""

from dataclasses import dataclass, field
import re
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
    skills: List[str] = field(default_factory=list)
    resistances: List[str] = field(default_factory=list)
    immunities: List[str] = field(default_factory=list)
    equipment: List[str] = field(default_factory=list)


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
    (["epee courte", "epees courtes"], ("épée courte", "perforant", 6)),
    (["epee longue", "epees longues", "sabre", "rapiere", "katana"],
     ("épée longue", "tranchant", 8)),
    ([r"re:\bepees?\b(?!\s+courtes?)"], ("épée longue", "tranchant", 8)),
    (["hache", "hachoir"], ("hache de bataille", "tranchant", 10)),
    (["marteau", "masse", "gourdin"], ("marteau de guerre", "contondant", 8)),
    (["lance", "javelot", "pieu", "harpon", "trident"], ("lance", "perforant", 6)),
    (["fleche", "arc ", "arbalete", "carquois"], ("arc long", "perforant", 8)),
    (["griffe", "serre", "talon", "patte"], ("griffes", "tranchant", 4)),
    (["morsure", "mord", "croc", "dent", "gueule", "mandibule"], ("morsure", "perforant", 6)),
    (["queue", "tentacule", "fouet"], ("queue fouettante", "contondant", 6)),
    (["bouclier", "ecusson"], ("coup de bouclier", "contondant", 4)),
]

# Objets d'inventaire portés (armes réelles, armures, boucliers, objets
# magiques) — uniquement les éléments importants, pas le butin.
EQUIPMENT_KEYWORDS: List[Tuple[List[str], str]] = [
    (["dague", "poignard"], "dague"),
    (["epee courte", "epees courtes"], "épée courte"),
    (["epee longue", "epees longues", "sabre", "rapiere", "katana"], "épée longue"),
    ([r"re:\bepees?\b(?!\s+courtes?)"], "épée longue"),
    (["hache"], "hache de bataille"),
    (["marteau", "masse d'arme"], "marteau de guerre"),
    (["lance", "javelot", "trident"], "lance"),
    (["arc ", "arc", "arbalete"], "arc long"),
    (["bouclier", "ecusson"], "bouclier"),
    (["armure de cuir", "cuir"], "armure de cuir"),
    (["armure matelassee", "matelass"], "armure matelassée"),
    (["armure de peau", "peausserie"], "armure de peausserie"),
    (["cotte de maille", "maille"], "cotte de mailles"),
    (["cloutee", "clouté"], "armure cloutée"),
    (["ecailles", "armure d'ecaille"], "armure d'écailles"),
    (["plate", "harnois"], "armure de plates"),
    (["anneau magique", "anneau"], "anneau magique"),
    (["amulette", "talisman"], "amulette"),
    (["potion"], "potion de soin"),
    (["baguette", "wand"], "baguette"),
    (["baton", "sceptre"], "bâton magique"),
    (["cape", "manteau"], "cape"),
    (["livre", "grimoire", "tom"], "grimoire"),
]
# Note : les attaques naturelles (griffes, morsure, queue) ne font pas
# partie de l'inventaire — elles sont déjà des actions.

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

# Compétences suggérées par archétype (compétences DnD 5e en français).
ARCHETYPE_SKILLS = {
    "brute": ["Athlétisme", "Intimidation"],
    "sneaky": ["Discrétion", "Escamotage", "Perception"],
    "caster": ["Arcanes", "Histoire", "Perspicacité"],
    "divin": ["Perspicacité", "Religion", "Médecine"],
    "charismatique": ["Persuasion", "Représentation", "Intimidation"],
}

# Mots-clés supplémentaires pour compétences spécifiques.
SKILL_KEYWORDS: List[Tuple[List[str], str]] = [
    (["chasse", "traque", "piege", "piège", "chasseur", "pistage"], "Survie"),
    (["nature", "foret", "forêt", "sauvage", "bete", "bête", "animal"], "Nature"),
    (["acrobate", "saut", "agile", "pirouette", "equilibre", "équilibre"], "Acrobaties"),
    (["menti", "mensonge", "trompe", "bluff", "imposture", "dissimul"], "Tromperie"),
    (["observe", "guette", "sentinelle", "vigilan", "surveille"], "Perception"),
    (["negoci", "négoci", "marchand", "commerce", "barguign"], "Persuasion"),
    (["cuisine", "forge", "artisan", "fabricat", "bricole"], "Artisanat"),
    (["connais le terrain", "carte", "cartographe", "explorat"], "Histoire"),
]

# Types de dégâts DnD 5e et mots-clés associés pour résistances/immunités.
DAMAGE_TYPES_KEYWORDS: List[Tuple[List[str], str]] = [
    (["feu", "flamme", "brasier", "incendie", "brulant", "lave", "magma", "pyro"], "feu"),
    (["glace", "gel", "froid", "givre", "neige", "hivernal", "congel"], "froid"),
    (["foudre", "eclair", "éclair", "tonnerre", "orage", "electr"], "foudre"),
    (["poison", "venin", "toxine", "toxique", "venimeux", "miasme"], "poison"),
    (["acide", "corrosif", "bave", "digest", "dissolut"], "acide"),
    (["tenebre", "ténèbre", "sombre", "negati", "négati", "spectral", "fantome",
      "fantôme", "necro", "non-vie", "sang-drain"], "nécrotique"),
    (["radiant", "lumiere", "lumière", "sacre", "sacré", "aube", "celeste", "céleste"], "radiant"),
    (["psychique", "mental", "esprit", "cauchemar", "terreur", "effroi"], "psychique"),
    (["tonnerre", "onde", "supersonique", "rugissement", "cri", "sonore", "vibration"], "tonnerre"),
    (["perforant", "fleche", "flèche", "pointe", "piqu"], "perforant"),
    (["tranchant", " lame", "epee", "épée", "griffe", "coupe"], "tranchant"),
    (["contondant", "ecrase", "écrase", "masse", "choc", "impact"], "contondant"),
    (["foudre", "eclair", "éclair", "paralys", "electr"], "paralysie"),
]

# Mots-clés signalant une IMMUNITÉ (plutôt qu'une résistance).
IMMUNITY_SIGNALS = ["immunise", "immunisé", "immunis", "insensible", "indestructible",
                   "ne subit aucun", "aucun degat", "aucun dégât", "epaisse peau",
                   "épaisse peau", "carapace"]

# Mots-clés signalant une RÉSISTANCE.
RESISTANCE_SIGNALS = ["resiste", "résiste", "resistance", "résistance", "endurc",
                      "peau dure", "ecaille", "écaille", "cuirasse", "protege", "protégé"]


_SLOW = ["massif", "lourd", "pesant", "colossal", "golem", "pierre", "roc", "tank"]
_FAST = ["rapide", "veloce", "fleche", "eclair", "felin",
         "guepard", "cheval", "coursier", "charge", "sprint", "cavale"]


def _normalize(text: str) -> str:
    """Minuscule + suppression des accents pour un match simple."""
    lowered = text.lower()
    return lowered.translate(str.maketrans("àâäéèêëîïôöùûüçñ", "aaaeeeeiioouuucn"))



def _kw_match(keyword: str, text: str) -> bool:
    """Matche un mot-clé : sous-chaîne simple, ou regex si préfixé re:."""
    if keyword.startswith("re:"):
        return re.search(keyword[3:], text) is not None
    return keyword in text

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
        if any(_kw_match(kw, combined_for_weapons) for kw in keywords) \
                and weapon not in weapons:
            weapons.append(weapon)
        if len(weapons) >= 3:
            break
    traits.weapons = weapons

    # Équipement porté : armes réelles, armures, boucliers, objets magiques.
    equipment: List[str] = []
    for keywords, item in EQUIPMENT_KEYWORDS:
        if any(_kw_match(kw, combined) for kw in keywords) and item not in equipment:
            equipment.append(item)
    traits.equipment = equipment[:6]

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
        # Intensité de vitesse : « très rapide » / comparaisons animales
        # (guépard, éclair...) = 18 m ; « rapide » standard = 12 m.
        very_fast = any(kw in combined for kw in ("tres rapide", "aussi vite", "extremement rapide"))
        if very_fast or "guepard" in combined:
            traits.speed = "18 m (12 cases)"
        elif any(kw in combined for kw in _FAST):
            traits.speed = "12 m (8 cases)"
        elif any(kw in combined for kw in _SLOW):
            traits.speed = "6 m (4 cases)"

    # Compétences maîtrisées : base par archétype + détection de mots-clés.
    skills: List[str] = []
    if traits.archetype:
        skills.extend(ARCHETYPE_SKILLS.get(traits.archetype, []))
    for keywords, skill in SKILL_KEYWORDS:
        if any(kw in combined for kw in keywords) and skill not in skills:
            skills.append(skill)
    traits.skills = skills[:4]

    # Résistances/immunités : signal (résiste/immunisé) + type de dégâts cité.
    is_resistant = any(kw in combined for kw in RESISTANCE_SIGNALS)
    is_immune = any(kw in combined for kw in IMMUNITY_SIGNALS)
    if is_resistant or is_immune:
        for keywords, damage_type in DAMAGE_TYPES_KEYWORDS:
            if any(kw in combined for kw in keywords):
                if is_immune:
                    if damage_type not in traits.immunities:
                        traits.immunities.append(damage_type)
                elif is_resistant:
                    if damage_type not in traits.resistances:
                        traits.resistances.append(damage_type)

    return traits
