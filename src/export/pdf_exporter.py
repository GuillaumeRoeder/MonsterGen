"""
Module d'export PDF pour les fiches de PNJ/Monstre au format DnD 5e officiel.
"""

from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER

from src.models.monster import Monster, Alignment, Size


class PDFExporter:
    """Exporteur PDF pour les fiches de PNJ/Monstre au format DnD 5e."""
    
    def __init__(self, page_size=A4):
        self.page_size = page_size
        self.styles = self._create_styles()
    
    def _create_styles(self):
        """Crée les styles pour le document."""
        styles = StyleSheet1()
        
        # Style de base
        base_style = ParagraphStyle(
            name="Normal",
            fontSize=9,
            leading=10,
            spaceAfter=2,
            fontName="Helvetica",
        )
        styles.add(base_style)
        
        # Style pour le titre principal
        title_style = ParagraphStyle(
            name="Title",
            parent=base_style,
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=0,
            textColor=colors.black,
            fontName="Helvetica-Bold",
        )
        styles.add(title_style)
        
        # Style pour le nom du monstre
        name_style = ParagraphStyle(
            name="MonsterName",
            parent=base_style,
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=0,
            textColor=colors.black,
            fontName="Helvetica-Bold",
        )
        styles.add(name_style)
        
        # Style pour les sections
        section_style = ParagraphStyle(
            name="Section",
            parent=base_style,
            fontSize=10,
            leading=12,
            spaceBefore=4,
            spaceAfter=2,
            textColor=colors.black,
            fontName="Helvetica-Bold",
        )
        styles.add(section_style)
        
        # Style pour les valeurs
        value_style = ParagraphStyle(
            name="Value",
            parent=base_style,
            fontSize=9,
            leading=10,
            spaceAfter=0,
            fontName="Helvetica",
        )
        styles.add(value_style)
        
        # Style pour les petites valeurs
        small_value_style = ParagraphStyle(
            name="SmallValue",
            parent=base_style,
            fontSize=8,
            leading=9,
            spaceAfter=0,
            fontName="Helvetica",
        )
        styles.add(small_value_style)
        
        # Style pour les stats
        stat_style = ParagraphStyle(
            name="Stat",
            parent=base_style,
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            spaceAfter=0,
            fontName="Helvetica-Bold",
        )
        styles.add(stat_style)
        
        # Style pour les modificateurs
        mod_style = ParagraphStyle(
            name="Mod",
            parent=base_style,
            fontSize=8,
            leading=9,
            alignment=TA_CENTER,
            spaceAfter=0,
            fontName="Helvetica",
        )
        styles.add(mod_style)
        
        return styles
    
    def _get_alignment_abbreviation(self, alignment: Optional[Alignment]) -> str:
        """Récupère l'abréviation de l'alignement."""
        if not alignment:
            return "—"
        
        mapping = {
            Alignment.LG: "LB",
            Alignment.NG: "NB",
            Alignment.CG: "CB",
            Alignment.LN: "LN",
            Alignment.TN: "N",
            Alignment.CN: "CN",
            Alignment.LE: "LM",
            Alignment.NE: "NM",
            Alignment.CE: "CM",
        }
        return mapping.get(alignment, "—")
    
    def _get_size_abbreviation(self, size: Optional[Size]) -> str:
        """Récupère l'abréviation de la taille."""
        if not size:
            return "—"
        
        mapping = {
            Size.TINY: "TP",
            Size.SMALL: "P",
            Size.MEDIUM: "M",
            Size.LARGE: "G",
            Size.HUGE: "É",
            Size.GARGANTUAN: "Gig",
        }
        return mapping.get(size, "—")
    
    def _get_ability_modifier(self, score: int) -> str:
        """Calcule le modificateur pour une caractéristique."""
        mod = (score - 10) // 2
        if mod >= 0:
            return f"+{mod}"
        return str(mod)
    
    def _create_header(self, monster: Monster) -> list:
        """Crée l'en-tête de la fiche."""
        elements = []
        
        # Nom du monstre
        name_text = f"{monster.name or 'PNJ/Monstre'}"
        elements.append(Paragraph(name_text, self.styles["MonsterName"]))
        
        # Ligne de séparation
        elements.append(Spacer(1, 2))
        
        # Informations principales (petite ligne)
        info_parts = []
        if monster.size:
            info_parts.append(self._get_size_abbreviation(monster.size))
        if monster.alignment:
            info_parts.append(self._get_alignment_abbreviation(monster.alignment))
        
        if info_parts:
            info_text = ", ".join(info_parts)
            elements.append(Paragraph(info_text, self.styles["SmallValue"]))
            elements.append(Spacer(1, 4))
        
        return elements
    
    def _create_stats_block(self, monster: Monster) -> list:
        """Crée le bloc des statistiques (CA, PV, Vitesse)."""
        elements = []
        
        # Classe d'armure
        ac_text = f"Classe d'armure {monster.armor_class or '—'}"
        elements.append(Paragraph(ac_text, self.styles["Section"]))
        
        # Points de vie
        hp_text = f"Points de vie {monster.hit_points or '—'} ({monster.hit_dice or '—'})"
        elements.append(Paragraph(hp_text, self.styles["Value"]))
        
        # Vitesse
        speed_text = f"Vitesse {monster.speed or '—'}"
        elements.append(Paragraph(speed_text, self.styles["Value"]))
        
        elements.append(Spacer(1, 6))
        
        return elements
    
    def _create_ability_scores_table(self, monster: Monster) -> Table:
        """Crée le tableau des caractéristiques."""
        scores = monster.ability_scores
        
        # En-tête
        header = [
            Paragraph("CARACTÉRISTIQUES", self.styles["Section"]),
            Paragraph("Valeur", self.styles["Section"]),
            Paragraph("Modificateur", self.styles["Section"])
        ]
        
        # Données
        data = [
            header,
            [
                Paragraph("Force", self.styles["Value"]),
                Paragraph(str(scores.strength), self.styles["Stat"]),
                Paragraph(self._get_ability_modifier(scores.strength), self.styles["Mod"])
            ],
            [
                Paragraph("Dextérité", self.styles["Value"]),
                Paragraph(str(scores.dexterity), self.styles["Stat"]),
                Paragraph(self._get_ability_modifier(scores.dexterity), self.styles["Mod"])
            ],
            [
                Paragraph("Constitution", self.styles["Value"]),
                Paragraph(str(scores.constitution), self.styles["Stat"]),
                Paragraph(self._get_ability_modifier(scores.constitution), self.styles["Mod"])
            ],
            [
                Paragraph("Intelligence", self.styles["Value"]),
                Paragraph(str(scores.intelligence), self.styles["Stat"]),
                Paragraph(self._get_ability_modifier(scores.intelligence), self.styles["Mod"])
            ],
            [
                Paragraph("Sagesse", self.styles["Value"]),
                Paragraph(str(scores.wisdom), self.styles["Stat"]),
                Paragraph(self._get_ability_modifier(scores.wisdom), self.styles["Mod"])
            ],
            [
                Paragraph("Charisme", self.styles["Value"]),
                Paragraph(str(scores.charisma), self.styles["Stat"]),
                Paragraph(self._get_ability_modifier(scores.charisma), self.styles["Mod"])
            ],
        ]
        
        table = Table(data, colWidths=[60, 30, 30])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, 0), 1, colors.black),
            ('GRID', (0, 1), (-1, -1), 0.5, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 1, 1),
            ('SPAN', (0, 0), (2, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        
        return table
    
    def _create_info_section(self, monster: Monster) -> list:
        """Crée la section d'informations (Race, Langues, CR)."""
        elements = []
        
        # Race
        if monster.race:
            elements.append(Paragraph(f"<b>Race.</b> {monster.race}", self.styles["Value"]))
        
        # Langues
        if monster.languages:
            languages_text = ", ".join(monster.languages)
            elements.append(Paragraph(f"<b>Langues.</b> {languages_text}", self.styles["Value"]))
        
        # Challenge Rating
        if monster.challenge_rating:
            from src.rules.stat_builder import cr_display, cr_xp
            cr_text = f"{cr_display(monster.challenge_rating)} ({cr_xp(monster.challenge_rating)} PX)" if monster.challenge_rating else "—"
            elements.append(Paragraph(f"<b>Dés de vie.</b> {monster.hit_dice or '—'}", self.styles["Value"]))
            elements.append(Paragraph(f"<b>Défis.</b> {cr_text}", self.styles["Value"]))
        
        elements.append(Spacer(1, 6))
        
        return elements
    
    def _create_skills_section(self, monster: Monster) -> list:
        """Crée la section des compétences maîtrisées."""
        elements = []
        
        # Compétences maîtrisées (avec bonus incluant la maîtrise)
        proficient_skills = [sk for sk in monster.skills if sk.proficiency]
        if proficient_skills:
            elements.append(Paragraph("Compétences maîtrisées", self.styles["Section"]))
            skill_parts = [f"{sk.name} {monster.skill_modifier(sk):+d}" for sk in proficient_skills]
            elements.append(Paragraph(", ".join(skill_parts), self.styles["Value"]))
            elements.append(Spacer(1, 4))
        
        return elements
    
    def _create_actions_section(self, monster: Monster) -> list:
        """Crée la section des actions."""
        elements = []
        
        if monster.actions:
            elements.append(Paragraph("Actions", self.styles["Section"]))
            
            for action in monster.actions:
                # Nom de l'action
                elements.append(Paragraph(f"• {action.name}", self.styles["Value"]))
                
                # Description (contient déjà bonus, dégâts, DD)
                if action.description:
                    elements.append(Paragraph(action.description, self.styles["SmallValue"]))
                
                elements.append(Spacer(1, 2))
            
            elements.append(Spacer(1, 4))
        
        return elements
    
    def _create_equipment_section(self, monster: Monster) -> list:
        """Crée la section des armements."""
        elements = []
        
        # Armements (extrait des actions ou notes)
        weapons = []
        for action in monster.actions:
            if action.attack_bonus is not None:
                weapons.append(action.name)
        
        if monster.notes:
            elements.append(Paragraph("Équipement", self.styles["Section"]))
            elements.append(Paragraph(monster.notes, self.styles["SmallValue"]))
            elements.append(Spacer(1, 4))
        elif weapons:
            elements.append(Paragraph("Armements", self.styles["Section"]))
            elements.append(Paragraph(", ".join(weapons), self.styles["Value"]))
            elements.append(Spacer(1, 4))
        
        return elements
    
    def _create_scenario_section(self, monster: Monster) -> list:
        """Crée la section du scénario de rencontre."""
        elements = []
        
        if monster.scenario:
            elements.append(Paragraph("Scénario de rencontre", self.styles["Section"]))
            elements.append(Paragraph(monster.scenario, self.styles["Value"]))
            elements.append(Spacer(1, 6))
        
        return elements
    
    def _create_description_section(self, monster: Monster) -> list:
        """Crée la section de description."""
        elements = []
        
        if monster.description:
            elements.append(Paragraph(monster.description, self.styles["Value"]))
            elements.append(Spacer(1, 6))
        
        return elements
    
    def export_to_pdf(self, monster: Monster, output_path: str) -> str:
        """Exporte le monstre en PDF au format DnD 5e."""
        # Créer le chemin de sortie
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Créer le document
        doc = SimpleDocTemplate(str(path), pagesize=self.page_size, 
                               topMargin=10*mm, bottomMargin=10*mm, 
                               leftMargin=10*mm, rightMargin=10*mm)
        
        # Construire les éléments
        elements = []
        
        # En-tête
        elements.extend(self._create_header(monster))
        
        # Statistiques (CA, PV, Vitesse)
        elements.extend(self._create_stats_block(monster))
        
        # Tableau des caractéristiques
        elements.append(self._create_ability_scores_table(monster))
        elements.append(Spacer(1, 8))
        
        # Informations (Race, Langues, CR)
        elements.extend(self._create_info_section(monster))
        
        # Compétences maîtrisées
        elements.extend(self._create_skills_section(monster))
        
        # Description
        elements.extend(self._create_description_section(monster))
        
        # Scénario
        elements.extend(self._create_scenario_section(monster))
        
        # Actions
        elements.extend(self._create_actions_section(monster))
        
        # Équipement
        elements.extend(self._create_equipment_section(monster))
        
        # Construire le PDF
        doc.build(elements)
        
        return str(path)


    def export_encounter_to_pdf(self, monsters, encounter, output_path: str) -> str:
        """Exporte une rencontre complète en un PDF unique minimaliste.

        Chaque monstre tient dans un bloc compact (nom + stats clés +
        caractéristiques sur une ligne + actions), séparé du suivant
        par une ligne horizontale. Objectif : lisible à la table, sans
        fiche d'une page par monstre.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(path), pagesize=self.page_size,
            topMargin=12 * mm, bottomMargin=12 * mm,
            leftMargin=12 * mm, rightMargin=12 * mm,
        )

        base = ParagraphStyle(
            "EncBase", fontName="Helvetica", fontSize=8.5, leading=10.5,
        )
        name_style = ParagraphStyle(
            "EncName", parent=base, fontName="Helvetica-Bold", fontSize=12,
            leading=14, spaceAfter=1,
        )
        label_style = ParagraphStyle(
            "EncLabel", parent=base, fontName="Helvetica-Bold", fontSize=8.5,
            textColor=colors.HexColor("#555555"),
        )
        header_style = ParagraphStyle(
            "EncHeader", parent=base, fontName="Helvetica-Bold", fontSize=14,
            leading=16, alignment=TA_CENTER, spaceAfter=2,
        )
        sub_style = ParagraphStyle(
            "EncSub", parent=base, fontSize=8, leading=10,
            textColor=colors.HexColor("#555555"), alignment=TA_CENTER,
        )

        from src.rules.stat_builder import cr_display

        def mod(value):
            return f"+{(value - 10) // 2}" if value >= 10 else f"{(value - 10) // 2}"

        elements = []
        if getattr(encounter, "name", ""):
            elements.append(Paragraph(encounter.name, header_style))
        subtitle = (
            f"{encounter.party_size} joueurs · niveau {encounter.party_level} · "
            f"{encounter.difficulty}"
        )
        elements.append(Paragraph(subtitle, sub_style))
        elements.append(Spacer(1, 6))

        if getattr(encounter, "description", ""):
            elements.append(Paragraph(encounter.description, base))
            elements.append(Spacer(1, 4))

        from src.rules.encounter_builder import evaluate
        info = evaluate(encounter)
        elements.append(Paragraph(
            f"{info['adjusted_xp']} PX ajustés — difficulté réelle : "
            f"{info['actual_label']}", sub_style,
        ))
        elements.append(Spacer(1, 6))

        for index, entry in enumerate(encounter.monsters):
            monster = monsters.get(entry.name)
            if monster is None:
                continue
            if index > 0:
                elements.append(Spacer(1, 4))
                elements.append(Table(
                    [[""]],
                    colWidths=[doc.width],
                    style=TableStyle([
                        ("LINEBELOW", (0, 0), (-1, -1), 0.75,
                         colors.HexColor("#999999")),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]),
                ))
                elements.append(Spacer(1, 4))

            title = f"{monster.name or entry.name} ×{max(1, entry.count)}"
            elements.append(Paragraph(title, name_style))
            stats = (
                f"CA {monster.armor_class or '-'} · "
                f"PV {monster.hit_points or '-'} "
                f"({monster.hit_dice or '-'}) · "
                f"Vit {monster.speed or '-'} · "
                f"CR {cr_display(monster.challenge_rating)}"
            )
            elements.append(Paragraph(stats, base))
            abilities = monster.ability_scores
            line = " · ".join(
                f"{label} {getattr(abilities, key)} ({mod(getattr(abilities, key))})"
                for key, label in [
                    ("strength", "FOR"), ("dexterity", "DEX"),
                    ("constitution", "CON"), ("intelligence", "INT"),
                    ("wisdom", "SAG"), ("charisma", "CHA"),
                ]
            )
            elements.append(Paragraph(line, base))
            if monster.saving_throws:
                saves = " · ".join(
                    f"{s.ability} {s.modifier:+d}" if s.modifier else s.ability
                    for s in monster.saving_throws
                )
                elements.append(Paragraph(
                    f"Sauvegardes : {saves}", base,
                ))
            if monster.skills:
                skills = " · ".join(
                    f"{s.name} {self._skill_bonus(monster, s):+d}"
                    for s in monster.skills
                )
                elements.append(Paragraph(f"Compétences : {skills}", base))
            if monster.languages:
                elements.append(Paragraph(
                    f"Langues : {', '.join(monster.languages)}", base,
                ))
            if monster.description:
                elements.append(Spacer(1, 2))
                elements.append(Paragraph(monster.description, base))
            for action in monster.actions:
                if not action.name:
                    continue
                text = f"<b>{action.name}</b>"
                if action.attack_bonus:
                    text += f" {action.attack_bonus:+d}"
                if action.damage:
                    text += f" ({action.damage}"
                    if action.damage_type:
                        text += f" {action.damage_type}"
                    text += ")"
                if action.description:
                    text += f" — {action.description}"
                elements.append(Paragraph(text, base))

        if getattr(encounter, "scenario", ""):
            elements.append(Spacer(1, 6))
            elements.append(Paragraph("Scénario", label_style))
            elements.append(Paragraph(encounter.scenario, base))

        doc.build(elements)
        return str(path)

    def _skill_bonus(self, monster: Monster, skill) -> int:
        """Bonus de compétence affiché sur la fiche rencontre."""
        return monster.skill_modifier(skill)



# Instance globale de l'exporteur PDF
pdf_exporter = PDFExporter()
