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
        /* Style global pour MonsterGen - Thème sombre DnD */
        QMainWindow {
            background-color: #2b2b2b;
        }
        
        QWidget {
            background-color: #3a3a3a;
            color: #e0e0e0;
            border: none;
        }
        
        QLabel {
            color: #e0e0e0;
        }
        
        QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            background-color: #4a4a4a;
            color: #e0e0e0;
            border: 1px solid #5a5a5a;
            border-radius: 4px;
            padding: 6px;
            selection-background-color: #00aaff;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border: 1px solid #00aaff;
            background-color: #4a4a4a;
        }
        
        QPushButton {
            background-color: #4a4a4a;
            color: #e0e0e0;
            border: 1px solid #5a5a5a;
            border-radius: 4px;
            padding: 8px 16px;
            min-height: 28px;
        }
        
        QPushButton:hover {
            background-color: #5a5a5a;
            border: 1px solid #00aaff;
        }
        
        QPushButton:pressed {
            background-color: #3a3a3a;
            border: 1px solid #00aaff;
        }
        
        QPushButton:disabled {
            background-color: #3a3a3a;
            color: #6a6a6a;
            border: 1px solid #5a5a5a;
        }
        
        QTabWidget {
            background-color: #3a3a3a;
        }
        
        QTabWidget::pane {
            border: 1px solid #5a5a5a;
            border-radius: 4px;
            background-color: #3a3a3a;
        }
        
        QTabBar::tab {
            background-color: #4a4a4a;
            color: #e0e0e0;
            border: 1px solid #5a5a5a;
            border-bottom: none;
            border-radius: 4px 4px 0 0;
            padding: 8px 16px;
            min-width: 100px;
        }
        
        QTabBar::tab:selected {
            background-color: #3a3a3a;
            color: #ffffff;
            border-bottom: 1px solid #3a3a3a;
            margin-bottom: -1px;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #5a5a5a;
        }
        
        QListWidget {
            background-color: #4a4a4a;
            color: #e0e0e0;
            border: 1px solid #5a5a5a;
            border-radius: 4px;
            padding: 4px;
        }
        
        QListWidget::item {
            background-color: #4a4a4a;
            color: #e0e0e0;
            padding: 4px;
            border: none;
        }
        
        QListWidget::item:selected {
            background-color: #00aaff;
            color: #ffffff;
        }
        
        QScrollArea {
            background-color: #3a3a3a;
            border: none;
        }
        
        QScrollArea > QWidget {
            background-color: #3a3a3a;
        }
        
        QGroupBox {
            background-color: #3a3a3a;
            border: 1px solid #5a5a5a;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 15px;
        }
        
        QGroupBox::title {
            color: #00aaff;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        
        QMenuBar {
            background-color: #2b2b2b;
            color: #e0e0e0;
            border-bottom: 1px solid #5a5a5a;
        }
        
        QMenuBar::item {
            background: transparent;
            color: #e0e0e0;
            padding: 4px 8px;
        }
        
        QMenuBar::item:selected {
            background-color: #4a4a4a;
            border-radius: 4px;
        }
        
        QMenu {
            background-color: #4a4a4a;
            color: #e0e0e0;
            border: 1px solid #5a5a5a;
            border-radius: 4px;
        }
        
        QMenu::item {
            background-color: #4a4a4a;
            color: #e0e0e0;
            padding: 6px 20px;
        }
        
        QMenu::item:selected {
            background-color: #00aaff;
            color: #ffffff;
        }
        
        QMessageBox {
            background-color: #3a3a3a;
            color: #e0e0e0;
        }
        
        QMessageBox QLabel {
            color: #e0e0e0;
        }
        
        QMessageBox QPushButton {
            background-color: #4a4a4a;
            color: #e0e0e0;
            border: 1px solid #5a5a5a;
            border-radius: 4px;
            padding: 6px 12px;
            min-width: 80px;
        }
        
        QMessageBox QPushButton:hover {
            background-color: #5a5a5a;
        }
        
        QInputDialog {
            background-color: #3a3a3a;
        }
        
        QInputDialog QLabel {
            color: #e0e0e0;
        }
        
        QInputDialog QLineEdit {
            background-color: #4a4a4a;
            color: #e0e0e0;
            border: 1px solid #5a5a5a;
            border-radius: 4px;
        }
        
        QInputDialog QPushButton {
            background-color: #4a4a4a;
            color: #e0e0e0;
            border: 1px solid #5a5a5a;
            border-radius: 4px;
        }
        
        QDialog {
            background-color: #3a3a3a;
        }
        
        QDialog QLabel {
            color: #e0e0e0;
        }
        
        QFormLayout QLabel {
            color: #00aaff;
            min-width: 150px;
        }
    """)


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
    from PySide6.QtWidgets import QMessageBox
    
    about_text = """
    <h2 style='color: #00aaff;'>MonsterGen</h2>
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
