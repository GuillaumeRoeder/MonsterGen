"""
Export PNG d'une fiche de monstre au style du stat block officiel DnD 5e :
en-tête rouge sur fond parchemin, lignes de caractéristiques, sections
avec titres rouges et filets, actions en gras-italique.
"""

from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from src.models.monster import Monster
from src.rules.stat_builder import cr_display, cr_xp, armor_class_detail

try:
    import importlib.resources as _resources
except ImportError:
    _resources = None

# Couleurs du stat block officiel
BG_COLOR = (245, 235, 210)      # parchemin clair
BG_DARK = (237, 224, 195)      # parchemin foncé (dégradé)
HEADER_RED = (140, 22, 22)     # rouge brique des titres
TEXT_DARK = (40, 30, 20)       # texte principal
RULE_COLOR = (140, 22, 22)     # filets
TRIM_COLOR = (155, 25, 25)     # bordure décorative

MARGIN_X = 36
MARGIN_TOP = 30
LINE_GAP = 6


class PNGExporter:
    """Exporteur PNG au format stat block DnD 5e."""

    def __init__(self, width: int = 800):
        self.width = width

    def _load_fonts(self):
        """Charge les polices (Vera embarquées avec reportlab, fallback par défaut)."""
        base = Path(__import__("reportlab").__file__).parent / "fonts"

        def load(name: str, size: int):
            path = base / name
            if path.exists():
                return ImageFont.truetype(str(path), size)
            return ImageFont.load_default()

        self.font_name = load("VeraBI.ttf", 38)
        self.font_meta = load("VeraIt.ttf", 17)
        self.font_section = load("VeraBd.ttf", 20)
        self.font_bold = load("VeraBd.ttf", 16)
        self.font_text = load("Vera.ttf", 16)
        self.font_ability = load("VeraBd.ttf", 17)
        self.font_ability_mod = load("Vera.ttf", 15)
        self.font_italic = load("VeraIt.ttf", 16)

    def _wrap_text(self, draw: ImageDraw.ImageDraw, text: str,
                   font, max_width: int) -> List[str]:
        """Découpe un texte en lignes tenant dans max_width."""
        if not text:
            return [""]
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def _measure_content(self, monster: Monster) -> Tuple[int, ImageDraw.ImageDraw]:
        """Pré-calcul du contenu pour mesurer la hauteur nécessaire."""
        img = Image.new("RGB", (self.width, 100), BG_COLOR)
        draw = ImageDraw.Draw(img)
        self._load_fonts()
        content = self._build_content(monster, draw)
        height = MARGIN_TOP + 20
        for kind, *rest in content:
            if kind == "name":
                height += 48
            elif kind == "meta":
                height += 26
            elif kind == "ac":
                height += 24
            elif kind == "hp":
                height += 24
            elif kind == "speed":
                height += 32
            elif kind == "abilities":
                height += 78
            elif kind == "section":
                height += 30
            elif kind == "line":
                text, bold = rest
                font = self.font_bold if bold else self.font_text
                wrapped = self._wrap_text(draw, text, font, self.width - 2 * MARGIN_X)
                height += len(wrapped) * 21 + 4
            elif kind == "action":
                name, desc = rest
                wrapped = self._wrap_text(draw, f"{name} : {desc}", self.font_text,
                                           self.width - 2 * MARGIN_X)
                height += len(wrapped) * 21 + 10
            elif kind == "scenario_subtitle":
                height += 26
            elif kind == "scenario_text":
                text = rest[0]
                wrapped = self._wrap_text(draw, text, self.font_text,
                                           self.width - 2 * MARGIN_X)
                height += len(wrapped) * 21 + 6
            elif kind == "gap":
                height += 14
            elif kind == "rule":
                height += 12
        height += MARGIN_TOP + 10
        return height, draw

    def _build_content(self, monster: Monster, draw: ImageDraw.ImageDraw) -> list:
        """Construit la liste ordonnée des éléments de la fiche."""
        content = []
        content.append(("name", monster.name or "PNJ / Monstre"))

        meta_parts = []
        if monster.size:
            meta_parts.append(monster.size.value)
        if monster.alignment:
            meta_parts.append(monster.alignment.value.lower())
        content.append(("meta", ", ".join(meta_parts) if meta_parts else ""))

        if monster.armor_class:
            ac_text = str(monster.armor_class)
            detail = armor_class_detail(monster.armor_class, monster.notes)
            if detail:
                ac_text += f" ({detail})"
            content.append(("ac", ac_text))
        if monster.hit_points:
            dice = f" ({monster.hit_dice})" if monster.hit_dice else ""
            content.append(("hp", f"{monster.hit_points}{dice}"))
        if monster.speed:
            content.append(("speed", monster.speed))

        scores = monster.ability_scores
        content.append(("abilities", scores))

        content.append(("rule",))

        if monster.saving_throws:
            st_text = ", ".join(
                f"{st.ability[:3].upper()} {st.modifier:+d}" for st in monster.saving_throws
            )
            content.append(("line", f"Jets de sauvegarde {st_text}", True))
        proficient_skills = [sk for sk in monster.skills if sk.proficiency]
        if proficient_skills:
            sk_text = ", ".join(f"{sk.name} {monster.skill_modifier(sk):+d}"
                                for sk in proficient_skills)
            content.append(("line", f"Compétences {sk_text}", False))
        if monster.damage_resistances:
            content.append(("line", f"Résistances {', '.join(monster.damage_resistances)}", False))
        if monster.damage_immunities:
            content.append(("line", f"Immunités {', '.join(monster.damage_immunities)}", False))
        if monster.condition_immunities:
            content.append(("line", f"Immunités aux états {', '.join(monster.condition_immunities)}", False))
        if monster.senses or monster.passive_perception:
            senses = list(monster.senses)
            if monster.passive_perception:
                senses.append(f"Perception passive {monster.passive_perception}")
            if senses:
                content.append(("line", f"Sens {', '.join(senses)}", False))
        if monster.languages:
            content.append(("line", f"Langues {', '.join(monster.languages)}", False))
        if monster.challenge_rating is not None:
            xp = cr_xp(monster.challenge_rating)
            content.append(("line", f"Degré de difficulté {cr_display(monster.challenge_rating)} ({xp} PX)", True))

        content.append(("rule",))

        if monster.description:
            content.append(("gap",))
            content.append(("line", monster.description, False))
            content.append(("gap",))

        if monster.actions:
            content.append(("rule",))
            content.append(("section", "Actions"))
            for action in monster.actions:
                content.append(("action", action.name, action.description or ""))

        if monster.legendary_actions:
            content.append(("rule",))
            content.append(("section", "Actions légendaires"))
            for action in monster.legendary_actions:
                content.append(("action", action.name, action.description or ""))

        if monster.reactions:
            content.append(("rule",))
            content.append(("section", "Réactions"))
            for action in monster.reactions:
                content.append(("action", action.name, action.description or ""))

        if monster.scenario:
            content.append(("rule",))
            content.append(("section", "Scénario de rencontre"))
            for item in self._scenario_items(monster.scenario):
                content.append(item)

        return content

    def _scenario_items(self, scenario: str) -> list:
        """Découpe le scénario en sous-éléments formatés.

        Les sections en gras (**Contexte**, **Tactique du monstre**...)
        deviennent des sous-titres suivis de leur texte ; les paragraphes
        vides créent un espacement. Le texte brut sans format est rendu
        tel quel.
        """
        import re as _re
        items = []
        # Séparer sur les titres en gras
        parts = _re.split(r"(\*\*[^*]+\*\*)", scenario)
        current_title = None
        buffer = []

        for part in parts:
            bold_match = _re.fullmatch(r"\*\*([^*]+)\*\*", part.strip())
            if bold_match:
                # flush du buffer précédent
                if buffer:
                    text = " ".join(" ".join(buffer).split())
                    if text:
                        items.append(("scenario_text", text))
                    buffer = []
                current_title = bold_match.group(1).strip().rstrip(":")
                items.append(("scenario_subtitle", current_title))
            else:
                if part.strip():
                    buffer.append(part.strip())
        if buffer:
            text = " ".join(" ".join(buffer).split())
            if text:
                items.append(("scenario_text", text))

        # Scénario sans aucun format gras : texte simple
        if not items:
            items.append(("scenario_text", scenario.strip()))
        return items

    def export_to_png(self, monster: Monster, output_path: str) -> str:
        """Exporte la fiche en PNG au style officiel DnD 5e."""
        height, _ = self._measure_content(monster)

        img = Image.new("RGB", (self.width, height), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Fond en dégradé parchemin
        for y in range(height):
            ratio = y / max(1, height - 1)
            r = int(BG_COLOR[0] * (1 - ratio) + BG_DARK[0] * ratio)
            g = int(BG_COLOR[1] * (1 - ratio) + BG_DARK[1] * ratio)
            b = int(BG_COLOR[2] * (1 - ratio) + BG_DARK[2] * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        # Bordure décorative double
        draw.rectangle([10, 10, self.width - 11, height - 11],
                       outline=TRIM_COLOR, width=3)
        draw.rectangle([16, 16, self.width - 17, height - 17],
                       outline=TRIM_COLOR, width=1)

        content = self._build_content(monster, draw)
        x = MARGIN_X
        y = MARGIN_TOP + 10
        text_width = self.width - 2 * MARGIN_X

        for item in content:
            kind = item[0]

            if kind == "name":
                draw.text((x, y), item[1], font=self.font_name, fill=HEADER_RED)
                y += 52
            elif kind == "meta":
                if item[1]:
                    draw.text((x, y), item[1], font=self.font_italic, fill=TEXT_DARK)
                y += 28
            elif kind == "ac":
                draw.text((x, y), "Classe d'armure ", font=self.font_bold, fill=TEXT_DARK)
                offset = draw.textbbox((x, y), "Classe d'armure ", font=self.font_bold)[2]
                draw.text((offset, y), str(item[1]), font=self.font_text, fill=TEXT_DARK)
                y += 24
            elif kind == "hp":
                draw.text((x, y), "Points de vie ", font=self.font_bold, fill=TEXT_DARK)
                offset = draw.textbbox((x, y), "Points de vie ", font=self.font_bold)[2]
                draw.text((offset, y), item[1], font=self.font_text, fill=TEXT_DARK)
                y += 24
            elif kind == "speed":
                draw.text((x, y), "Vitesse ", font=self.font_bold, fill=TEXT_DARK)
                offset = draw.textbbox((x, y), "Vitesse ", font=self.font_bold)[2]
                draw.text((offset, y), item[1], font=self.font_text, fill=TEXT_DARK)
                y += 32
            elif kind == "abilities":
                y = self._draw_ability_table(draw, x, y, item[1])
            elif kind == "rule":
                draw.line([(x, y + 2), (x + text_width, y + 2)], fill=RULE_COLOR, width=2)
                y += 12
            elif kind == "section":
                y += 8
                draw.text((x, y), item[1], font=self.font_section, fill=HEADER_RED)
                y += 32
            elif kind == "line":
                text, bold = item[1], item[2]
                font = self.font_bold if bold else self.font_text
                for line in self._wrap_text(draw, text, font, text_width):
                    draw.text((x, y), line, font=font, fill=TEXT_DARK)
                    y += 21
                y += 4
            elif kind == "action":
                name, desc = item[1], item[2]
                # Nom en gras suivi de " :" puis description (style officiel)
                full = f"{name} : {desc}" if desc else name
                wrapped = self._wrap_text(draw, full, self.font_text, text_width)
                for i, wline in enumerate(wrapped):
                    if i == 0 and name and wline.startswith(name.split()[0]):
                        # rendu gras du début = nom
                        draw.text((x, y), name + " :", font=self.font_bold, fill=TEXT_DARK)
                        rest = wline[len(name):].lstrip(". :")
                        if rest:
                            off = draw.textbbox((x, y), name + "  ", font=self.font_bold)[2]
                            draw.text((off, y), rest, font=self.font_text, fill=TEXT_DARK)
                    else:
                        draw.text((x, y), wline, font=self.font_text, fill=TEXT_DARK)
                    y += 21
                y += 10
            elif kind == "scenario_subtitle":
                draw.text((x, y), item[1], font=self.font_bold, fill=TEXT_DARK)
                y += 24
            elif kind == "scenario_text":
                for line in self._wrap_text(draw, item[1], self.font_text, text_width):
                    draw.text((x, y), line, font=self.font_text, fill=TEXT_DARK)
                    y += 21
                y += 6
            elif kind == "gap":
                y += 14

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(path), "PNG")
        return str(path)

    def _draw_ability_table(self, draw: ImageDraw.ImageDraw, x: int, y: int,
                            scores) -> int:
        """Dessine la ligne des 6 caractéristiques du stat block officiel."""
        abilities = [
            ("FOR", scores.strength),
            ("DEX", scores.dexterity),
            ("CON", scores.constitution),
            ("INT", scores.intelligence),
            ("SAG", scores.wisdom),
            ("CHA", scores.charisma),
        ]
        col_width = (self.width - 2 * MARGIN_X) // 6
        for i, (abbr, score) in enumerate(abilities):
            cx = x + i * col_width + col_width // 2
            mod = (score - 10) // 2
            label = f"{abbr} {score} ({mod:+d})"
            bbox = draw.textbbox((0, 0), label, font=self.font_ability)
            tw = bbox[2] - bbox[0]
            draw.text((cx - tw // 2, y), label, font=self.font_ability, fill=TEXT_DARK)
        y += 34
        return y


# Instance globale
png_exporter = PNGExporter()
