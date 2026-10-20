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

from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton, QWidget, QHBoxLayout
from PySide6.QtCore import Qt

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
                "Renseignez votre clé API dans Configuration, ou installez "
                "llama-cpp-python manuellement pour revenir au modèle local."
            )
    
    # Exécuter l'application
    sys.exit(app.exec())


def set_stylesheet(app):
    """Applique le style sheet global à l'application."""
    app.setStyleSheet("""
        /* Style global pour MonsterGen - Thème sombre bleu DnD */
        QMainWindow {
            background-color: #10151c;
        }
        
        QWidget {
            background-color: #161d26;
            color: #dce4ee;
            border: none;
        }
        
        QLabel {
            color: #dce4ee;
        }
        
        QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            background-color: #1e2632;
            color: #dce4ee;
            border: 1px solid #39485c;
            border-radius: 4px;
            padding: 6px;
            selection-background-color: #1e88e5;
            selection-color: #ffffff;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border: 1px solid #42a5f5;
            background-color: #1e2632;
        }
        
        QPushButton {
            background-color: #212b38;
            color: #dce4ee;
            border: 1px solid #39485c;
            border-radius: 4px;
            padding: 8px 16px;
            min-height: 28px;
        }
        
        QPushButton:hover {
            background-color: #26344a;
            border: 1px solid #42a5f5;
        }
        
        QPushButton:pressed {
            background-color: #171e28;
            border: 1px solid #42a5f5;
        }
        
        QPushButton:disabled {
            background-color: #171e28;
            color: #6a7a8a;
            border: 1px solid #39485c;
        }
        
        QTabWidget {
            background-color: #161d26;
        }
        
        QTabWidget::pane {
            border: 1px solid #39485c;
            border-radius: 4px;
            background-color: #161d26;
        }
        
        QTabBar::tab {
            background-color: #1e2632;
            color: #dce4ee;
            border: 1px solid #39485c;
            border-bottom: none;
            border-radius: 4px 4px 0 0;
            padding: 8px 16px;
            min-width: 100px;
        }
        
        QTabBar::tab:selected {
            background-color: #1e2f47;
            color: #90caf9;
            border-bottom: 1px solid #1e2f47;
            margin-bottom: -1px;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #26344a;
        }
        
        QListWidget {
            background-color: #1e2632;
            color: #dce4ee;
            border: 1px solid #39485c;
            border-radius: 4px;
            padding: 4px;
        }
        
        QListWidget::item {
            background-color: #1e2632;
            color: #dce4ee;
            padding: 4px;
            border: none;
        }
        
        QListWidget::item:selected {
            background-color: #1e5fa8;
            color: #ffffff;
        }
        
        QScrollArea {
            background-color: #161d26;
            border: none;
        }
        
        QScrollArea > QWidget {
            background-color: #161d26;
        }
        
        QGroupBox {
            background-color: #161d26;
            border: 1px solid #39485c;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 15px;
        }
        
        QGroupBox::title {
            color: #64b5f6;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        
        QMenuBar {
            background-color: #10151c;
            color: #dce4ee;
            border-bottom: 1px solid #39485c;
        }
        
        QMenuBar::item {
            background: transparent;
            color: #dce4ee;
            padding: 4px 8px;
        }
        
        QMenuBar::item:selected {
            background-color: #1e2632;
            border-radius: 4px;
        }
        
        QMenu {
            background-color: #1e2632;
            color: #dce4ee;
            border: 1px solid #39485c;
            border-radius: 4px;
        }
        
        QMenu::item {
            background-color: #1e2632;
            color: #dce4ee;
            padding: 6px 20px;
        }
        
        QMenu::item:selected {
            background-color: #1e5fa8;
            color: #ffffff;
        }
        
        QMessageBox {
            background-color: #161d26;
            color: #dce4ee;
        }
        
        QMessageBox QLabel {
            color: #dce4ee;
        }
        
        QMessageBox QPushButton {
            background-color: #212b38;
            color: #dce4ee;
            border: 1px solid #39485c;
            border-radius: 4px;
            padding: 6px 12px;
            min-width: 80px;
        }
        
        QMessageBox QPushButton:hover {
            background-color: #26344a;
        }
        
        QInputDialog {
            background-color: #161d26;
        }
        
        QInputDialog QLabel {
            color: #dce4ee;
        }
        
        QInputDialog QLineEdit {
            background-color: #1e2632;
            color: #dce4ee;
            border: 1px solid #39485c;
            border-radius: 4px;
        }
        
        QInputDialog QPushButton {
            background-color: #212b38;
            color: #dce4ee;
            border: 1px solid #39485c;
            border-radius: 4px;
        }
        
        QDialog {
            background-color: #161d26;
        }
        
        QDialog QLabel {
            color: #dce4ee;
        }
        
        QFormLayout QLabel {
            color: #90caf9;
            min-width: 150px;
        }
    """)


def create_menus(window: MainWindow):
    """Crée les menus de l'application.

    La barre est un conteneur horizontal : menus natifs à gauche,
    bouton Configuration poussé tout à droite (le corner widget natif
    de QMenuBar est masqué par certains styles/WM).
    """
    menu_bar = window.menuBar()

    # Menu Bibliothèque (sauvegarder/charger/supprimer des monstres)
    library_menu = menu_bar.addMenu("Bibliothèque")
    library_action = library_menu.addAction("Gérer les monstres sauvegardés")
    library_action.triggered.connect(lambda: window.open_library())
    
    # Menu Export (PDF / PNG)
    export_menu = menu_bar.addMenu("Export")
    pdf_action = export_menu.addAction("Exporter en PDF")
    pdf_action.triggered.connect(lambda: window.export_to_pdf())
    png_action = export_menu.addAction("Exporter en PNG")
    png_action.triggered.connect(lambda: window.export_to_png())
    
    # Menu Aide
    help_menu = menu_bar.addMenu("Aide")
    about_action = help_menu.addAction("À propos")
    about_action.triggered.connect(lambda: show_about_dialog(window))
    
    # Menu Configuration : bouton dans la barre, collé à droite
    config_btn = QPushButton("⚙ Configuration")
    config_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    config_btn.setStyleSheet("""
        QPushButton {
            background-color: transparent;
            border: none;
            color: #dce4ee;
            padding: 4px 10px;
            min-height: 0px;
            font-weight: bold;
        }
        QPushButton:hover {
            color: #42a5f5;
        }
    """)
    config_btn.clicked.connect(lambda: show_config_dialog(window))
    bar_container = QWidget()
    bar_layout = QHBoxLayout(bar_container)
    bar_layout.setContentsMargins(0, 0, 8, 0)
    bar_layout.setSpacing(0)
    bar_layout.addWidget(menu_bar)
    bar_layout.addStretch()
    bar_layout.addWidget(config_btn)
    window.setMenuBar(bar_container)


def show_config_dialog(parent: MainWindow):
    """Affiche la boîte de dialogue de configuration."""
    dialog = ConfigDialog(parent)
    dialog.exec()
    parent.update_backend_status()


def show_about_dialog(parent: MainWindow):
    """Affiche la boîte de dialogue À propos."""
    from PySide6.QtWidgets import QMessageBox
    
    about_text = """
    <h2 style='color: #64b5f6;'>MonsterGen</h2>
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
