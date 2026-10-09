"""
Module d'export PDF pour les fiches de PNJ/Monstre.
"""

import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from src.models.monster import Monster, Alignment, Size


class PDFExporter:
    """Exporteur PDF pour les fiches de PNJ/Monstre."""
    
    def __init__(self, page_size=A4):
        self.page_size = page_size
        self.styles = self._create_styles()
    
    def _create_styles(self):
        """Crée les styles pour le document."""
        # Créer une nouvelle feuille de styles
        from reportlab.lib.styles import StyleSheet1
        styles = StyleSheet1()
        
        # Style de base
        base_style = ParagraphStyle(
            name="Normal",
            fontSize=10,
            leading=12,
            spaceAfter=3,
            fontName="Helvetica",
        )
        styles.add(base_style)
        
        # Style pour le titre principal
        title_style = ParagraphStyle(
            name="Title",
            parent=base_style,
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.darkred,
            fontName="Helvetica-Bold",
        )
        styles.add(title_style)
        
        # Style pour les sections
        section_style = ParagraphStyle(
            name="Section",
            parent=base_style,
            fontSize=16,
            leading=18,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.darkblue,
            fontName="Helvetica-Bold",
        )
        styles.add(section_style)
        
        # Style pour les sous-sections
        subsection_style = ParagraphStyle(
            name="SubSection",
            parent=base_style,
            fontSize=12,
            leading=14,
            spaceBefore=6,
            spaceAfter=3,
            textColor=colors.darkgreen,
            fontName="Helvetica-Bold",
        )
        styles.add(subsection_style)
        
        # Style pour les statistiques
        stat_style = ParagraphStyle(
            name="Stat",
            parent=base_style,
            fontSize=10,
            leading=12,
            fontName="Helvetica-Bold",
        )
        styles.add(stat_style)
        
        # Style pour les valeurs
        value_style = ParagraphStyle(
            name="Value",
            parent=base_style,
            fontSize=10,
            leading=12,
            fontName="Helvetica",
        )
        styles.add(value_style)
        
        # Style pour les tables
        table_header_style = ParagraphStyle(
            name="TableHeader",
            parent=base_style,
            fontSize=9,
            leading=11,
            fontName="Helvetica-Bold",
            textColor=colors.white,
            alignment=TA_CENTER,
        )
        styles.add(table_header_style)
        
        table_cell_style = ParagraphStyle(
            name="TableCell",
            parent=base_style,
            fontSize=9,
            leading=11,
            fontName="Helvetica",
        )
        styles.add(table_cell_style)
        
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
            Size.TINY: "M",
            Size.SMALL: "P",
            Size.MEDIUM: "M",
            Size.LARGE: "G",
            Size.HUGE: "É",
            Size.GARGANTUAN: "Gig",
        }
        return mapping.get(size, "—")
    
    def _create_header(self, monster: Monster) -> list:
        """Crée l'en-tête de la fiche."""
        elements = []
        
        # Titre
        elements.append(Paragraph(monster.name or "PNJ/Monstre", self.styles["Title"]))
        
        # Informations principales
        info_table = Table([
            [Paragraph("Race :", self.styles["Stat"]), Paragraph(monster.race or "—", self.styles["Value"])],
            [Paragraph("Alignement :", self.styles["Stat"]), Paragraph(self._get_alignment_abbreviation(monster.alignment), self.styles["Value"])],
            [Paragraph("Taille :", self.styles["Stat"]), Paragraph(self._get_size_abbreviation(monster.size), self.styles["Value"])],
            [Paragraph("CR :", self.styles["Stat"]), Paragraph(str(monster.challenge_rating) if monster.challenge_rating else "—", self.styles["Value"])],
        ], colWidths=[50, 100])
        
        info_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 2, 2),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_stats_block(self, monster: Monster) -> list:
        """Crée le bloc des statistiques."""
        elements = []
        
        elements.append(Paragraph("Statistiques", self.styles["Section"]))
        
        # Classe d'armure et Points de vie
        ac_hp_table = Table([
            [Paragraph("Classe d'Armure", self.styles["Stat"]), Paragraph(str(monster.armor_class) if monster.armor_class else "—", self.styles["Value"])],
            [Paragraph("Points de Vie", self.styles["Stat"]), Paragraph(f"{monster.hit_points or '—'} ({monster.hit_dice or '—'})", self.styles["Value"])],
            [Paragraph("Vitesse", self.styles["Stat"]), Paragraph(monster.speed or "—", self.styles["Value"])],
        ], colWidths=[100, 100])
        
        ac_hp_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 2, 2),
        ]))
        
        elements.append(ac_hp_table)
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_ability_scores(self, monster: Monster) -> list:
        """Crée le tableau des caractéristiques."""
        elements = []
        
        elements.append(Paragraph("Caractéristiques", self.styles["SubSection"]))
        
        scores = monster.ability_scores
        
        data = [
            ["", "Score", "Modificateur"],
            [Paragraph("Force (FOR)", self.styles["Stat"]), 
             Paragraph(str(scores.strength), self.styles["Value"]),
             Paragraph(f"{scores.get_modifier('strength'):+d}", self.styles["Value"])],
            [Paragraph("Dextérité (DEX)", self.styles["Stat"]),
             Paragraph(str(scores.dexterity), self.styles["Value"]),
             Paragraph(f"{scores.get_modifier('dexterity'):+d}", self.styles["Value"])],
            [Paragraph("Constitution (CON)", self.styles["Stat"]),
             Paragraph(str(scores.constitution), self.styles["Value"]),
             Paragraph(f"{scores.get_modifier('constitution'):+d}", self.styles["Value"])],
            [Paragraph("Intelligence (INT)", self.styles["Stat"]),
             Paragraph(str(scores.intelligence), self.styles["Value"]),
             Paragraph(f"{scores.get_modifier('intelligence'):+d}", self.styles["Value"])],
            [Paragraph("Sagesse (SAG)", self.styles["Stat"]),
             Paragraph(str(scores.wisdom), self.styles["Value"]),
             Paragraph(f"{scores.get_modifier('wisdom'):+d}", self.styles["Value"])],
            [Paragraph("Charisme (CHA)", self.styles["Stat"]),
             Paragraph(str(scores.charisma), self.styles["Value"]),
             Paragraph(f"{scores.get_modifier('charisma'):+d}", self.styles["Value"])],
        ]
        
        table = Table(data, colWidths=[80, 40, 40])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 2, 2),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_defense_section(self, monster: Monster) -> list:
        """Crée la section de défense."""
        elements = []
        
        if (monster.damage_resistances or monster.damage_immunities or 
            monster.damage_vulnerabilities or monster.condition_immunities):
            
            elements.append(Paragraph("Défense", self.styles["SubSection"]))
            
            defense_data = []
            
            if monster.damage_resistances:
                defense_data.append([Paragraph("Résistances :", self.styles["Stat"]), 
                                    Paragraph(", ".join(monster.damage_resistances), self.styles["Value"])])
            if monster.damage_immunities:
                defense_data.append([Paragraph("Immunités :", self.styles["Stat"]), 
                                    Paragraph(", ".join(monster.damage_immunities), self.styles["Value"])])
            if monster.damage_vulnerabilities:
                defense_data.append([Paragraph("Vulnérabilités :", self.styles["Stat"]), 
                                    Paragraph(", ".join(monster.damage_vulnerabilities), self.styles["Value"])])
            if monster.condition_immunities:
                defense_data.append([Paragraph("Immunités aux états :", self.styles["Stat"]), 
                                    Paragraph(", ".join(monster.condition_immunities), self.styles["Value"])])
            
            if defense_data:
                table = Table(defense_data, colWidths=[100, 200])
                table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                    ('PADDING', (0, 0), (-1, -1), 2, 2),
                ]))
                elements.append(table)
            
            elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_senses_section(self, monster: Monster) -> list:
        """Crée la section des sens."""
        elements = []
        
        if monster.senses or monster.passive_perception:
            elements.append(Paragraph("Sens", self.styles["SubSection"]))
            
            senses_data = []
            
            if monster.senses:
                senses_data.append([Paragraph("Sens :", self.styles["Stat"]), 
                                  Paragraph(", ".join(monster.senses), self.styles["Value"])])
            if monster.passive_perception:
                senses_data.append([Paragraph("Perception passive :", self.styles["Stat"]), 
                                  Paragraph(str(monster.passive_perception), self.styles["Value"])])
            
            if senses_data:
                table = Table(senses_data, colWidths=[120, 180])
                table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                    ('PADDING', (0, 0), (-1, -1), 2, 2),
                ]))
                elements.append(table)
            
            elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_languages_section(self, monster: Monster) -> list:
        """Crée la section des langues."""
        elements = []
        
        if monster.languages:
            elements.append(Paragraph("Langues", self.styles["SubSection"]))
            elements.append(Paragraph(", ".join(monster.languages), self.styles["Normal"]))
            elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_actions_section(self, monster: Monster) -> list:
        """Crée la section des actions."""
        elements = []
        
        if monster.actions:
            elements.append(Paragraph("Actions", self.styles["Section"]))
            
            for action in monster.actions:
                elements.append(Paragraph(f"• {action.name}", self.styles["SubSection"]))
                if action.description:
                    elements.append(Paragraph(action.description, self.styles["Normal"]))
                if action.attack_bonus:
                    attack_info = f"Attaque : +{action.attack_bonus}"
                    if action.damage:
                        attack_info += f", Dégâts : {action.damage} {action.damage_type or ''}"
                    elements.append(Paragraph(attack_info, self.styles["Normal"]))
                elements.append(Spacer(1, 5))
            
            elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_legendary_actions_section(self, monster: Monster) -> list:
        """Crée la section des actions légendaires."""
        elements = []
        
        if monster.legendary_actions:
            elements.append(Paragraph("Actions Légendaires", self.styles["Section"]))
            
            for action in monster.legendary_actions:
                elements.append(Paragraph(f"• {action.name}", self.styles["SubSection"]))
                if action.description:
                    elements.append(Paragraph(action.description, self.styles["Normal"]))
                elements.append(Spacer(1, 5))
            
            elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_reactions_section(self, monster: Monster) -> list:
        """Crée la section des réactions."""
        elements = []
        
        if monster.reactions:
            elements.append(Paragraph("Réactions", self.styles["Section"]))
            
            for reaction in monster.reactions:
                elements.append(Paragraph(f"• {reaction.name}", self.styles["SubSection"]))
                if reaction.description:
                    elements.append(Paragraph(reaction.description, self.styles["Normal"]))
                elements.append(Spacer(1, 5))
            
            elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_description_section(self, monster: Monster) -> list:
        """Crée la section de description."""
        elements = []
        
        if monster.description:
            elements.append(Paragraph("Description", self.styles["Section"]))
            elements.append(Paragraph(monster.description, self.styles["Normal"]))
            elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_notes_section(self, monster: Monster) -> list:
        """Crée la section des notes."""
        elements = []
        
        if monster.notes:
            elements.append(Paragraph("Notes", self.styles["Section"]))
            elements.append(Paragraph(monster.notes, self.styles["Normal"]))
            elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_footer(self) -> list:
        """Crée le pied de page."""
        elements = []
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Fiche générée avec MonsterGen", self.styles["Normal"]))
        elements.append(Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), self.styles["Normal"]))
        
        return elements
    
    def export_to_pdf(self, monster: Monster, output_path: str) -> str:
        """Exporte le monstre en PDF."""
        # Créer le chemin de sortie
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Créer le document
        doc = SimpleDocTemplate(str(path), pagesize=self.page_size)
        
        # Construire les éléments
        elements = []
        
        # En-tête
        elements.extend(self._create_header(monster))
        
        # Description
        elements.extend(self._create_description_section(monster))
        
        # Statistiques
        elements.extend(self._create_stats_block(monster))
        
        # Caractéristiques
        elements.extend(self._create_ability_scores(monster))
        
        # Défense
        elements.extend(self._create_defense_section(monster))
        
        # Sens
        elements.extend(self._create_senses_section(monster))
        
        # Langues
        elements.extend(self._create_languages_section(monster))
        
        # Actions
        elements.extend(self._create_actions_section(monster))
        
        # Actions légendaires
        elements.extend(self._create_legendary_actions_section(monster))
        
        # Réactions
        elements.extend(self._create_reactions_section(monster))
        
        # Notes
        elements.extend(self._create_notes_section(monster))
        
        # Pied de page
        elements.extend(self._create_footer())
        
        # Construire le PDF
        doc.build(elements)
        
        return str(path)


# Instance globale de l'exporteur PDF
pdf_exporter = PDFExporter()
