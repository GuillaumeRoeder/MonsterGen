"""Styles partagés pour les widgets de l'interface MonsterGen."""

# Bouton d'action principale (générations IA, équilibrage) : accent bleu.
ACCENT_BUTTON_STYLE = """
    QPushButton {
        background-color: #005f8a;
        color: #ffffff;
        border: 1px solid #0077b0;
        border-radius: 4px;
        padding: 6px 14px;
        min-height: 20px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #0077b0;
        border: 1px solid #00aaff;
    }
    QPushButton:pressed {
        background-color: #004a6e;
        border: 1px solid #00aaff;
    }
    QPushButton:disabled {
        background-color: #3a3a3a;
        color: #6a6a6a;
        border: 1px solid #5a5a5a;
    }
"""

# Bouton secondaire (sous-action d'une génération) : plus discret,
# texte plus petit, pas de gras.
SECONDARY_BUTTON_STYLE = """
    QPushButton {
        background-color: #3f4650;
        color: #c8d4e0;
        border: 1px solid #556170;
        border-radius: 4px;
        padding: 3px 10px;
        min-height: 0px;
        min-width: 0px;
        font-size: 11px;
    }
    QPushButton:hover {
        background-color: #4a5360;
        border: 1px solid #00aaff;
        color: #ffffff;
    }
    QPushButton:pressed {
        background-color: #353b44;
    }
"""
