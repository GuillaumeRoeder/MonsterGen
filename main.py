"""
Point d'entrée principal de l'application MonsterGen.
"""

import sys

from src.bootstrap import BootstrapError, ensure_dependencies, ensure_optional_llama_cpp, llama_cpp_available

try:
    ensure_dependencies()
except BootstrapError as e:
    print(f"[MonsterGen] {e}", flush=True)
    sys.exit(1)

from PySide6.QtWidgets import QApplication, QMessageBox

from src.ui.main_window import MainWindow
from src.ui.config_dialog import ConfigDialog
from config.config_manager import config_manager


def main():
    """Fonction principale."""
    app = QApplication(sys.argv)
    
    # Définir le nom de l'application
    app.setApplicationName("MonsterGen")
    app.setOrganizationName("DnD Tools")
    
    # Appliquer le style sheet global
    set_stylesheet(app)
    
    # Créer la fenêtre principale
    main_window = MainWindow()
    
    # Ajouter un menu de configuration
    create_menus(main_window)
    
    # Afficher la fenêtre
    main_window.show()
    
    # llama-cpp-python est optionnel : en cas d'échec d'installation, on
    # prévient l'utilisateur et on bascule la config en mode API.
    if config_manager.get_ai_mode() == "local" and not llama_cpp_available():
        ok = ensure_optional_llama_cpp()
        if not ok:
            config_manager.set_ai_mode("api")
            QMessageBox.warning(
                main_window,
                "Modèle local indisponible",
                "llama-cpp-python n'a pas pu être installé automatiquement.\n\n"
                "L'application passe en mode API par défaut.\n"
                "Renseignez votre clé API dans Fichier > Configuration, ou installez "
                "llama-cpp-python manuellement pour revenir au modèle local."
            )
    
    # Exécuter l'application
    sys.exit(app.exec())


def set_stylesheet(app):
    """Applique le style sheet global à l'application."""
    app.setStyleSheet("""
        /* Style global pour MonsterGen - Thème sombre vert DnD */
        QMainWindow {
            background-color: #121a12;
        }
        
        QWidget {
            background-color: #1a231a;
            color: #dfe8df;
            border: none;
        }
        
        QLabel {
            color: #dfe8df;
        }
        
        QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            background-color: #222d22;
            color: #dfe8df;
            border: 1px solid #3e4e3e;
            border-radius: 4px;
            padding: 6px;
            selection-background-color: #4caf50;
            selection-color: #ffffff;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border: 1px solid #66bb6a;
            background-color: #222d22;
        }
        
        QPushButton {
            background-color: #253225;
            color: #dfe8df;
            border: 1px solid #3e4e3e;
            border-radius: 4px;
            padding: 8px 16px;
            min-height: 28px;
        }
        
        QPushButton:hover {
            background-color: #2c3a2c;
            border: 1px solid #66bb6a;
        }
        
        QPushButton:pressed {
            background-color: #1c261c;
            border: 1px solid #66bb6a;
        }
        
        QPushButton:disabled {
            background-color: #1c261c;
            color: #6a7a6a;
            border: 1px solid #3e4e3e;
        }
        
        QTabWidget {
            background-color: #1a231a;
        }
        
        QTabWidget::pane {
            border: 1px solid #3e4e3e;
            border-radius: 4px;
            background-color: #1a231a;
        }
        
        QTabBar::tab {
            background-color: #222d22;
            color: #dfe8df;
            border: 1px solid #3e4e3e;
            border-bottom: none;
            border-radius: 4px 4px 0 0;
            padding: 8px 16px;
            min-width: 100px;
        }
        
        QTabBar::tab:selected {
            background-color: #253d25;
            color: #a5d6a7;
            border-bottom: 1px solid #253d25;
            margin-bottom: -1px;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #2c3a2c;
        }
        
        QListWidget {
            background-color: #222d22;
            color: #dfe8df;
            border: 1px solid #3e4e3e;
            border-radius: 4px;
            padding: 4px;
        }
        
        QListWidget::item {
            background-color: #222d22;
            color: #dfe8df;
            padding: 4px;
            border: none;
        }
        
        QListWidget::item:selected {
            background-color: #2e7d32;
            color: #ffffff;
        }
        
        QScrollArea {
            background-color: #1a231a;
            border: none;
        }
        
        QScrollArea > QWidget {
            background-color: #1a231a;
        }
        
        QGroupBox {
            background-color: #1a231a;
            border: 1px solid #3e4e3e;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 15px;
        }
        
        QGroupBox::title {
            color: #81c784;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        
        QMenuBar {
            background-color: #121a12;
            color: #dfe8df;
            border-bottom: 1px solid #3e4e3e;
        }
        
        QMenuBar::item {
            background: transparent;
            color: #dfe8df;
            padding: 4px 8px;
        }
        
        QMenuBar::item:selected {
            background-color: #222d22;
            border-radius: 4px;
        }
        
        QMenu {
            background-color: #222d22;
            color: #dfe8df;
            border: 1px solid #3e4e3e;
            border-radius: 4px;
        }
        
        QMenu::item {
            background-color: #222d22;
            color: #dfe8df;
            padding: 6px 20px;
        }
        
        QMenu::item:selected {
            background-color: #2e7d32;
            color: #ffffff;
        }
        
        QMessageBox {
            background-color: #1a231a;
            color: #dfe8df;
        }
        
        QMessageBox QLabel {
            color: #dfe8df;
        }
        
        QMessageBox QPushButton {
            background-color: #253225;
            color: #dfe8df;
            border: 1px solid #3e4e3e;
            border-radius: 4px;
            padding: 6px 12px;
            min-width: 80px;
        }
        
        QMessageBox QPushButton:hover {
            background-color: #2c3a2c;
        }
        
        QInputDialog {
            background-color: #1a231a;
        }
        
        QInputDialog QLabel {
            color: #dfe8df;
        }
        
        QInputDialog QLineEdit {
            background-color: #222d22;
            color: #dfe8df;
            border: 1px solid #3e4e3e;
            border-radius: 4px;
        }
        
        QInputDialog QPushButton {
            background-color: #253225;
            color: #dfe8df;
            border: 1px solid #3e4e3e;
            border-radius: 4px;
        }
        
        QDialog {
            background-color: #1a231a;
        }
        
        QDialog QLabel {
            color: #dfe8df;
        }
        
        QFormLayout QLabel {
            color: #a5d6a7;
            min-width: 150px;
        }
    """)


def create_menus(window: MainWindow):
    """Crée les menus de l'application."""
    # Menu Fichier
    file_menu = window.menuBar().addMenu("Fichier")
    
    # Menu Bibliothèque (sauvegarder/charger/supprimer des monstres)
    library_menu = window.menuBar().addMenu("Bibliothèque")
    library_action = library_menu.addAction("Gérer les monstres sauvegardés")
    library_action.triggered.connect(lambda: window.open_library())
    
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
    parent.update_backend_status()


def show_about_dialog(parent: MainWindow):
    """Affiche la boîte de dialogue À propos."""
    from PySide6.QtWidgets import QMessageBox
    
    about_text = """
    <h2 style='color: #81c784;'>MonsterGen</h2>
    <p style='color: #e0e0e0;'>Générateur de fiches de PNJ/Monstres pour Donjons & Dragons 5e.</p>
    <p style='color: #e0e0e0;'>Version : 1.0.0</p>
    <p style='color: #e0e0e0;'>Auteur : Guillaume Roeder</p>
    <p style='color: #e0e0e0;'>Licence : MIT</p>
    """
    
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle("À propos de MonsterGen")
    msg_box.setTextFormat(1)  # HTML
    msg_box.setText(about_text)
    msg_box.exec()


if __name__ == "__main__":
    main()
