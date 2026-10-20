"""
Styles partagés pour les widgets de l'interface MonsterGen.
Palette en tons de verts.
"""

# Bouton d'action principale (générations IA, équilibrage) : accent vert.
ACCENT_BUTTON_STYLE = """
    QPushButton {
        background-color: #2e7d32;
        color: #ffffff;
        border: 1px solid #43a047;
        border-radius: 4px;
        padding: 6px 14px;
        min-height: 20px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #388e3c;
        border: 1px solid #66bb6a;
    }
    QPushButton:pressed {
        background-color: #1b5e20;
        border: 1px solid #66bb6a;
    }
    QPushButton:disabled {
        background-color: #3a4a3a;
        color: #7a8a7a;
        border: 1px solid #556b55;
    }
"""

# Bouton secondaire (sous-action d'une génération) : plus discret,
# texte plus petit, pas de gras.
SECONDARY_BUTTON_STYLE = """
    QPushButton {
        background-color: #37453a;
        color: #c8dcc8;
        border: 1px solid #557055;
        border-radius: 4px;
        padding: 3px 10px;
        min-height: 0px;
        min-width: 0px;
        font-size: 11px;
    }
    QPushButton:hover {
        background-color: #40543f;
        border: 1px solid #66bb6a;
        color: #ffffff;
    }
    QPushButton:pressed {
        background-color: #2b352b;
    }
"""
