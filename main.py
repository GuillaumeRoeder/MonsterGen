"""
Point d'entrée principal de l'application MonsterGen.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from src.ui.main_window import MainWindow
from src.ui.config_dialog import ConfigDialog
from config.config_manager import config_manager


def main():
    """Fonction principale."""
    app = QApplication(sys.argv)
    
    # Définir le nom de l'application
    app.setApplicationName("MonsterGen")
    app.setOrganizationName("DnD Tools")
    
    # Créer la fenêtre principale
    main_window = MainWindow()
    
    # Ajouter un menu de configuration
    create_menus(main_window)
    
    # Afficher la fenêtre
    main_window.show()
    
    # Exécuter l'application
    sys.exit(app.exec())


def create_menus(window: MainWindow):
    """Crée les menus de l'application."""
    # Menu Fichier
    file_menu = window.menuBar().addMenu("Fichier")
    
    # Menu Configuration
    config_action = file_menu.addAction("Configuration")
    config_action.triggered.connect(lambda: show_config_dialog(window))
    
    # Menu Quitter
    quit_action = file_menu.addAction("Quitter")
    quit_action.triggered.connect(window.close)
    
    # Menu Aide
    help_menu = window.menuBar().addMenu("Aide")
    about_action = help_menu.addAction("À propos")
    about_action.triggered.connect(lambda: show_about_dialog(window))


def show_config_dialog(parent: MainWindow):
    """Affiche la boîte de dialogue de configuration."""
    dialog = ConfigDialog(parent)
    dialog.exec()


def show_about_dialog(parent: MainWindow):
    """Affiche la boîte de dialogue À propos."""
    from PyQt6.QtWidgets import QMessageBox
    
    about_text = """
    <h2>MonsterGen</h2>
    <p>Générateur de fiches de PNJ/Monstres pour Donjons & Dragons 5e.</p>
    <p>Version : 1.0.0</p>
    <p>Auteur : Guillaume Roeder</p>
    <p>Licence : MIT</p>
    """
    
    QMessageBox.about(parent, "À propos de MonsterGen", about_text)


if __name__ == "__main__":
    main()
