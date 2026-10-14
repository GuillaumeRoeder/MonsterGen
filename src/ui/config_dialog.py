"""
Boîte de dialogue de configuration.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QSpinBox
)

from config.config_manager import config_manager
from src.ai.local_model import LOCAL_MODELS, DEFAULT_MODEL_SIZE


class ConfigDialog(QDialog):
    """Boîte de dialogue pour configurer l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration de MonsterGen")
        self.setMinimumWidth(450)
        self.setStyleSheet("""
            QDialog {
                background-color: #3a3a3a;
            }

            QLabel {
                color: #e0e0e0;
            }

            QLineEdit, QComboBox, QSpinBox {
                background-color: #4a4a4a;
                color: #e0e0e0;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                padding: 6px;
            }

            QPushButton {
                background-color: #4a4a4a;
                color: #e0e0e0;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                padding: 8px 16px;
            }

            QPushButton:hover {
                background-color: #5a5a5a;
                border: 1px solid #00aaff;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Taille du modèle local (panel hardcodé : 2 ou 4 Go)
        model_layout = QHBoxLayout()
        model_label = QLabel("Modèle IA local :")
        model_label.setStyleSheet("color: #00aaff;")
        self.model_combo = QComboBox()
        for key, info in LOCAL_MODELS.items():
            self.model_combo.addItem(info["label"], key)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo, stretch=1)
        layout.addLayout(model_layout)

        # Chemin du fichier modèle (optionnel, sinon dossier models/)
        path_layout = QHBoxLayout()
        path_label = QLabel("Chemin du modèle :")
        path_label.setStyleSheet("color: #00aaff;")
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setPlaceholderText("Laisser vide pour utiliser models/ automatiquement")
        path_layout.addWidget(path_label)
        browse_btn = QPushButton("Parcourir…")
        browse_btn.clicked.connect(self._browse_model)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # Taille du contexte
        ctx_layout = QHBoxLayout()
        ctx_label = QLabel("Taille du contexte :")
        ctx_label.setStyleSheet("color: #00aaff;")
        self.ctx_spin = QSpinBox()
        self.ctx_spin.setRange(1024, 32768)
        self.ctx_spin.setSingleStep(1024)
        ctx_layout.addWidget(ctx_label)
        ctx_layout.addWidget(self.ctx_spin)
        layout.addLayout(ctx_layout)

        # Threads CPU
        threads_layout = QHBoxLayout()
        threads_label = QLabel("Threads CPU :")
        threads_label.setStyleSheet("color: #00aaff;")
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 64)
        threads_layout.addWidget(threads_label)
        threads_layout.addWidget(self.threads_spin)
        layout.addLayout(threads_layout)

        # Chemin de sauvegarde
        save_path_layout = QHBoxLayout()
        save_path_label = QLabel("Chemin de sauvegarde :")
        save_path_label.setStyleSheet("color: #00aaff;")
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

        self.load_config()

    def _browse_model(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choisir un fichier modèle GGUF", "", "Modèle GGUF (*.gguf)"
        )
        if file_path:
            self.model_path_edit.setText(file_path)

    def load_config(self):
        """Charge la configuration actuelle."""
        size = config_manager.get_local_model_size()
        index = list(LOCAL_MODELS.keys()).index(size) if size in LOCAL_MODELS else \
            list(LOCAL_MODELS.keys()).index(DEFAULT_MODEL_SIZE)
        self.model_combo.setCurrentIndex(index)
        self.model_path_edit.setText(config_manager.get_local_model_path())
        self.ctx_spin.setValue(config_manager.get_local_context())
        self.threads_spin.setValue(config_manager.get_local_threads())
        self.save_path_edit.setText(config_manager.get_save_path())

    def save_config(self):
        """Sauvegarde la configuration."""
        config_manager.set_local_model_size(self.model_combo.currentData())
        config_manager.set_local_model_path(self.model_path_edit.text().strip())
        config_manager.set_local_context(self.ctx_spin.value())
        config_manager.set_local_threads(self.threads_spin.value())

        save_path = self.save_path_edit.text().strip()
        if save_path:
            config_manager.set_save_path(save_path)

        QMessageBox.information(
            self,
            "Configuration sauvegardée",
            "La configuration a été sauvegardée avec succès."
        )

        self.accept()
