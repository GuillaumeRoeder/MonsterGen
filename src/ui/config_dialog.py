"""
Boîte de dialogue de configuration.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt

from config.config_manager import config_manager


class ConfigDialog(QDialog):
    """Boîte de dialogue pour configurer l'application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration de MonsterGen")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Clé API
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("Clé API IA :")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Entrez votre clé API")
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_edit, stretch=1)
        layout.addLayout(api_key_layout)
        
        # Modèle IA
        model_layout = QHBoxLayout()
        model_label = QLabel("Modèle IA :")
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "mistral-tiny",
            "mistral-small",
            "mistral-medium",
            "mistral-large",
        ])
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo, stretch=1)
        layout.addLayout(model_layout)
        
        # Endpoint IA
        endpoint_layout = QHBoxLayout()
        endpoint_label = QLabel("Endpoint IA :")
        self.endpoint_edit = QLineEdit()
        self.endpoint_edit.setPlaceholderText("URL de l'endpoint IA")
        endpoint_layout.addWidget(endpoint_label)
        endpoint_layout.addWidget(self.endpoint_edit, stretch=1)
        layout.addLayout(endpoint_layout)
        
        # Chemin de sauvegarde
        save_path_layout = QHBoxLayout()
        save_path_label = QLabel("Chemin de sauvegarde :")
        self.save_path_edit = QLineEdit()
        self.save_path_edit.setPlaceholderText("Chemin par défaut pour les fiches")
        save_path_layout.addWidget(save_path_label)
        save_path_layout.addWidget(self.save_path_edit, stretch=1)
        layout.addLayout(save_path_layout)
        
        # Boutons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Sauvegarder")
        self.save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Charger la configuration actuelle
        self.load_config()
    
    def load_config(self):
        """Charge la configuration actuelle."""
        self.api_key_edit.setText(config_manager.get_api_key())
        self.model_combo.setCurrentText(config_manager.get_model())
        self.endpoint_edit.setText(config_manager.get_endpoint())
        self.save_path_edit.setText(config_manager.get_save_path())
    
    def save_config(self):
        """Sauvegarde la configuration."""
        api_key = self.api_key_edit.text().strip()
        model = self.model_combo.currentText()
        endpoint = self.endpoint_edit.text().strip()
        save_path = self.save_path_edit.text().strip()
        
        if api_key:
            config_manager.set_api_key(api_key)
        
        if model:
            config_manager.set_model(model)
        
        if endpoint:
            config_manager.set_endpoint(endpoint)
        
        if save_path:
            config_manager.set_save_path(save_path)
        
        QMessageBox.information(
            self,
            "Configuration sauvegardée",
            "La configuration a été sauvegardée avec succès."
        )
        
        self.accept()
