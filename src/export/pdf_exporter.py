"""
Module d'export PDF pour les fiches de PNJ/Monstre au format DnD 5e officiel.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, StyleSheet1
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Frame,
    PageTemplate,
    Image,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

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
        
        # Compétences maîtrisées
        proficient_skills = [sk for sk in monster.skills if sk.proficiency]
        if proficient_skills:
            elements.append(Paragraph("Compétences maîtrisées", self.styles["Section"]))
            skill_names = [sk.name for sk in proficient_skills]
            elements.append(Paragraph(", ".join(skill_names), self.styles["Value"]))
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
        
        if weapons or monster.notes:
            elements.append(Paragraph("Équipement", self.styles["Section"]))
            
            if weapons:
                elements.append(Paragraph(", ".join(weapons), self.styles["Value"]))
            
            if monster.notes:
                elements.append(Paragraph(monster.notes, self.styles["SmallValue"]))
            
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


# Instance globale de l'exporteur PDF
pdf_exporter = PDFExporter()
