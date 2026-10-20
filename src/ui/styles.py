"""
Styles partagés pour les widgets de l'interface MonsterGen.
Palette en tons de bleus.
"""

# Bouton d'action principale (générations IA, équilibrage) : accent bleu.
ACCENT_BUTTON_STYLE = """
    QPushButton {
        background-color: #1e5fa8;
        color: #ffffff;
        border: 1px solid #2d7cd6;
        border-radius: 4px;
        padding: 6px 14px;
        min-height: 20px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #2672b8;
        border: 1px solid #42a5f5;
    }
    QPushButton:pressed {
        background-color: #154a7d;
        border: 1px solid #42a5f5;
    }
    QPushButton:disabled {
        background-color: #33374a;
        color: #7a7a8a;
        border: 1px solid #4a5a7a;
    }
"""

# Bouton secondaire (sous-action d'une génération) : plus discret,
# texte plus petit, pas de gras.
SECONDARY_BUTTON_STYLE = """
    QPushButton {
        background-color: #333c4a;
        color: #c8d4e8;
        border: 1px solid #506080;
        border-radius: 4px;
        padding: 3px 10px;
        min-height: 0px;
        min-width: 0px;
        font-size: 11px;
    }
    QPushButton:hover {
        background-color: #3a4a55;
        border: 1px solid #42a5f5;
        color: #ffffff;
    }
    QPushButton:pressed {
        background-color: #262c33;
    }
"""
