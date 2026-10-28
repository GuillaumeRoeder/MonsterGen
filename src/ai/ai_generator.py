"""
Module de génération IA locale pour compléter les champs manquants.

Toute la génération passe par un petit modèle embarqué (GGUF, 2 à 6 Go)
exécuté en locale avec llama-cpp-python : aucune clé API n'est nécessaire.
Les statistiques équilibrées, elles, sont calculées par src/rules/stat_builder
d'après les tables officielles du Guide du Maître (aucune IA requise).
"""

import json
import random
import re
from typing import List, Optional

from src.models.monster import Monster, Action
from src.rules.encounter_builder import Encounter
from src.ai.local_model import local_model, ModelNotAvailableError
from src.ai.api_client import api_client
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
    'Abyssal', 'Aklo', 'Aquatique', 'Auran',
    'Chtonien', 'Commun', 'Céleste', 'Draconique',
    'Elfique', 'Gnome', 'Gobelin', 'Géant',
    'Ignan', 'Infernal', 'Nain', 'Orque',
    'Primordial', 'Sylvestre', 'Terran'
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
            "name": "Propose 3 noms de fantaisie adaptés, un seul nom par proposition, sans guillemets ni numérotation, séparés par des points-virgules.",
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

    def generate_actions(self, monster: Monster,
                          actions_prompt: Optional[str] = None) -> List[Action]:
        """Génère des actions complètes (nom + description + stats) pour le monstre.

        actions_prompt : description libre des actions souhaitées par l'utilisateur ;
        si fournie, elle oriente fortement la génération.
        """
        context = f"{monster_stats_summary(monster)}"
        if monster.race:
            context += f"\nRace : {monster.race}"
        if monster.description:
            context += f"\nDescription : {monster.description}"
        if actions_prompt:
            context += (
                f"\nActions demandées par l'utilisateur (à générer telles quelles, "
                f"enrichies des stats équilibrées) : {actions_prompt}"
            )
        prompt = (
            f"Fiche de PNJ/Monstre DnD 5e. {context}\n"
            "Génère 3 actions de combat cohérentes avec ces statistiques "
            "et la description ci-dessus — les armes et aptitudes mentionnées "
            "dans la description sont OBLIGATOIRES (ex. doué à l'arc -> au "
            "moins une attaque à distance à l'arc). "
            "Si des actions sont demandées par l'utilisateur, génère exactement "
            "celles-là, une action par demande. "
            "(bonus d'attaque et dégâts équilibrés pour ce CR).\n"
            "OBLIGATOIRE : la description de chaque action doit contenir les "
            "chiffres du jeu — pour une attaque, écris par exemple : 'Attaque "
            "d'arme au corps à corps : +6 au toucher, 2d8+4 (11) dégâts "
            "tranchants, portée 1,50 m.' ; pour un effet à jet de sauvegarde, "
            "écris le DD : 'DD 13 des jets de sauvegarde de Constitution'. "
            "Aucune action sans bonus au toucher et dégâts, ni sans DD si c'est "
            "un effet de sauvegarde.\n"
            'Réponds UNIQUEMENT en JSON valide, format strict :\n'
            '{"actions": [{"name": "...", "description": "...", '
            '"attack_bonus": 0, "damage": "...", "damage_type": "..."}]}\n'
            "Pas de texte en dehors du JSON."
        )

        raw = _backend_generate(prompt, max_tokens=700)
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

        self._complete_action_stats(actions, monster)
        return actions

    def _complete_action_stats(self, actions: List[Action], monster: Monster) -> None:
        """Complète les actions IA avec les valeurs des tables DMG.

        Pour chaque attaque sans bonus d'attaque ni dégâts, ajoute le bonus
        et les dégâts équilibrés pour le CR du monstre ; pour une action à
        jet de sauvegarde (mentionne un DD), ajoute le DD officiel si
        manquant. La description est enrichie avec ces valeurs.
        """
        cr = monster.challenge_rating
        if cr is None:
            return

        from src.rules.stat_builder import DMG_TABLE, _cr_key
        _, _, _, _, _, dmg_min, dmg_max, save_dc = DMG_TABLE[_cr_key(cr)]

        for action in actions:
            text = f"{action.name} {action.description}".lower()
            # Action à jet de sauvegarde : mentionne un DD/sauvegarde/recharge,
            # ou ressemble à un effet (souffle, hurlement, regard, gaz...).
            is_save = bool(re.search(
                r"\bdd\b|sauvegarde|recharge|souffle|hurlement|regard|gaz|"
                r"aura|nuage|explosion|cri|siphon",
                text,
            ))
            is_attack = (
                action.attack_bonus is not None
                or action.damage is not None
                or "au toucher" in text
            )

            desc = action.description

            if is_save and not is_attack:
                has_dc = bool(re.search(r"dd\s*\d+", text))
                if not has_dc:
                    prefix = f"Jet de sauvegarde DD {save_dc}."
                    action.description = f"{prefix} {desc}" if desc else prefix
                elif f"dd {save_dc}" not in text:
                    # Un DD est cité mais différent de la valeur équilibrée :
                    # on remplace par le DD officiel du CR.
                    action.description = re.sub(
                        r"dd\s*\d+", f"DD {save_dc}", action.description, flags=re.IGNORECASE
                    )
            elif not is_attack:
                target = random.randint(dmg_min, max(dmg_min, dmg_max))
                action.attack_bonus = DMG_TABLE[_cr_key(cr)][4]
                action.damage = f"{max(1, target // 8)}d8 + {max(0, target % 8)}" if target % 8 else f"{max(1, target // 8)}d8"
                line = f"+{action.attack_bonus} au toucher, {action.damage} dégâts"
                action.description = f"{desc} {line}." if desc else f"Attaque : {line}."
            else:
                # Attaque déjà décrite : garantir la présence des dégâts
                if "au toucher" in text and "dégât" not in text:
                    target = random.randint(dmg_min, max(dmg_min, dmg_max))
                    action.damage = f"{max(1, target // 8)}d8 + {max(0, target % 8)}" if target % 8 else f"{max(1, target // 8)}d8"
                    suffix = f" Dégâts : {action.damage}."
                    action.description = f"{action.description.rstrip('.')} {suffix.strip()}"
                # Garantir le DD pour un effet de sauvegarde déjà décrit
                if "sauvegarde" in text and not re.search(r"dd\s*\d+", text):
                    action.description = (
                        f"{action.description.rstrip('.')} "
                        f"(Jet de sauvegarde DD {save_dc})."
                    )

            if not action.description:
                action.description = "Description non fournie par le modèle."

    def correct_text(self, monster: Monster, field_name: str, text: str) -> str:
        """Corrige l'orthographe et le style d'un champ textuel existant.

        Le fond (contenu, concept) est conservé ; seule la forme est
        améliorée. Retourne le texte corrigé, ou le texte original en cas
        d'échec.
        """
        labels = {
            "name": "Nom du monstre",
            "description": "Description",
            "scenario": "Scénario de rencontre",
        }
        label = labels.get(field_name, field_name)

        prompt = (
            f"{label} actuel d'une créature :\n{text}\n\n"
            f"Corrige l'orthographe, la grammaire et la ponctuation de ce texte. "
            "Garde exactement le même contenu, le même concept et la même "
            "longueur approximative — ne rajoute rien, ne supprime rien, "
            "conserve le formatage markdown (gras **) s'il est présent.\n"
            "IMPORTANT : ne recopie ni l'en-tête, ni le label, ni le texte "
            "d'aucune fiche. Réponds UNIQUEMENT avec le texte corrigé, sans "
            "préambule ni explication."
        )

        raw = _backend_generate(prompt, max_tokens=500, temperature=0.3)
        cleaned = raw.replace('```', '').strip()
        if not cleaned:
            raise RuntimeError("Le modèle n'a pas produit de correction.")
        return AIGenerator._sanitize_short_text(cleaned)

    @staticmethod
    def _sanitize_short_text(text: str) -> str:
        """Nettoie une reponse IA courte (nom, race) : guillemets englobants,
        prefixes du type "Nom corrige : ..." et lignes parasites."""
        text = text.strip()
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            return ""
        text = lines[0]
        # Echo du prompt (le modèle rejoue l'en-tête) : garder la 2e ligne,
        # qui contient la vraie réponse.
        if len(lines) > 1 and (
            text.startswith("Fiche de PNJ")
            or text.startswith("Nom=")
            or text.startswith("Race=")
        ):
            text = lines[1]
        text = text.strip("\u00ab\u00bb\u201c\u201d\u2018\u2019\"' ")
        m = re.match(r"^\s*(?:le\s+|la\s+)?(?:nom|race|description|texte)\s*(?:corrig\u00e9e?|corrigee?|final|finale)?\s*:\s*(.+)$",
                     text, flags=re.IGNORECASE)
        if m:
            text = m.group(1).strip("\u00ab\u00bb\u201c\u201d\u2018\u2019\"' ")
        return text

    def generate_scenario(self, monster: Monster,
                         party_size: Optional[int] = None,
                         avg_level: Optional[int] = None,
                         difficulty: Optional[str] = None) -> str:
        """Génère un scénario de rencontre de combat basé sur les stats actuelles.

        Le scénario décrit la rencontre ET la manière de jouer le monstre :
        tactique d'ouverture, ciblage, utilisation des actions, réactions aux
        dégâts et conditions de repli ou de mort.
        """
        party_line = ""
        if party_size and avg_level:
            party_line = f" Groupe adversaire : {party_size} joueurs de niveau moyen {avg_level}"
            if difficulty:
                party_line += f" (difficulté visée : {difficulty})."

        actions_detail = "; ".join(
            f"{a.name} ({a.description})" if a.description else a.name
            for a in monster.actions
        ) if monster.actions else "aucune action connue"

        prompt = (
            f"Fiche de PNJ/Monstre DnD 5e. {monster_stats_summary(monster)}\n"
            f"Actions du monstre : {actions_detail}\n"
            f"{party_line}\n"
            "Écris, en français, un scénario de RENCONTRE DE COMBAT pour le MJ, "
            "structuré ainsi, avec ces titres exacts en gras :\n"
            "**Contexte** : 1 à 2 phrases (lieu, circonstances, pourquoi le combat éclate).\n"
            "**Déroulement** : 1 à 2 phrases (déclencheur, disposition initiale des forces en présence).\n"
            "**Tactique du monstre** : 3 à 5 phrases détaillant comment jouer le monstre : "
            "comment il ouvre le combat et avec quelle action, qui il cible en priorité "
            "(soigneurs, lanceurs de sorts, personnages fragiles...) et pourquoi, "
            "comment il réagit quand il perd la moitié de ses PV, quand il utilise son "
            "action spéciale ou sa recharge, et dans quelle condition il fuit, se rend "
            "ou se bat jusqu'à la mort.\n"
            "**Récompense** : 1 phrase (butin, information ou objet récupéré après le combat).\n"
            "N'invente pas de stats nouvelles : appuie-toi uniquement sur la fiche ci-dessus. "
            "Réponds UNIQUEMENT avec le texte du scénario, sans préambule ni conclusion."
        )

        raw = _backend_generate(prompt, max_tokens=600, temperature=0.8)
        cleaned = raw.replace('```', '').strip()
        if not cleaned:
            raise RuntimeError("Le modèle n'a pas produit de scénario.")
        return cleaned
    def generate_encounter_scenario(self, encounter: Encounter,
                                    monster_files: Optional[dict] = None) -> str:
        """Génère un scénario de rencontre multi-monstres pour le MJ.

        encounter : la rencontre complète (monstres, quantités, groupe
        cible, difficulté visée). monster_files : dictionnaire optionnel
        nom -> résumé de fiche détaillée (race, description, actions).
        """
        from src.rules.encounter import DIFFICULTY_LABELS
        from src.rules.encounter_builder import cr_display

        lines = []
        for m in encounter.monsters:
            cr = cr_display(m.challenge_rating)
            line = f"- {m.count} × {m.name} (CR {cr})"
            if monster_files and m.name in monster_files:
                line += f" — {monster_files[m.name]}"
            lines.append(line)
        monsters_detail = "\n".join(lines)

        target = DIFFICULTY_LABELS.get(encounter.difficulty, encounter.difficulty)
        actual = DIFFICULTY_LABELS.get(encounter.actual_difficulty,
                                       encounter.actual_difficulty)

        context_line = ""
        if encounter.description:
            context_line = (
                f"Description de la rencontre fournie par le MJ (contexte "
                f"à rendre cohérent, éléments à intégrer tels quels) :\n"
                f"{encounter.description}\n\n"
            )

        prompt = (
            f"Rencontre DnD 5e pour un groupe de {encounter.party_size} "
            f"joueurs de niveau moyen {encounter.party_level}.\n"
            f"Difficulté visée : {target} (difficulté réelle calculée : "
            f"{actual}, {encounter.adjusted_xp} PX ajustés).\n"
            f"Monstres :\n{monsters_detail}\n\n"
            f"{context_line}"
            "Écris, en français, un scénario de RENCONTRE DE COMBAT pour le MJ, "
            "structuré ainsi, avec ces titres exacts en gras :\n"
            "**Contexte** : 1 à 2 phrases (lieu, circonstances, pourquoi le combat éclate — "
            "reprend le contexte décrit par le MJ s'il est fourni).\n"
            "**Disposition** : 1 à 2 phrases (placement des monstres, terrain, "
            "déclencheur de l'initiative — reprend les armes, compositions et "
            "détails décrits par le MJ s'ils sont fournis).\n"
            "**Tactique** : 3 à 5 phrases (qui ouvre le combat, ciblage prioritaire, "
            "coordination entre les monstres, réaction à mi-PV, conditions de "
            "repli ou de reddition).\n"
            "**Récompense** : 1 phrase (butin, information ou objet récupéré).\n"
            "N'invente pas de stats nouvelles : appuie-toi uniquement sur les "
            "monstres listés ci-dessus. "
            "R\u00e9ponds UNIQUEMENT avec le texte du scénario, sans préambule."
        )

        raw = _backend_generate(prompt, max_tokens=600, temperature=0.8)
        cleaned = raw.replace('```', '').strip()
        if not cleaned:
            raise RuntimeError("Le modèle n'a pas produit de scénario.")
        return cleaned


# Instance globale
ai_generator = AIGenerator()
