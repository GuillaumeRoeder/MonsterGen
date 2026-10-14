"""
Boîte de dialogue de configuration.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QSpinBox, QWidget
)

from config.config_manager import config_manager
from src.ai.local_model import LOCAL_MODELS, DEFAULT_MODEL_SIZE


class ConfigDialog(QDialog):
    """Boîte de dialogue pour configurer l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration de MonsterGen")
        self.setMinimumWidth(480)
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

        # Mode IA : modèle local ou API distante
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode IA :")
        mode_label.setStyleSheet("color: #00aaff;")
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Modèle local (hors ligne)", "local")
        self.mode_combo.addItem("API distante (clé API requise)", "api")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo, stretch=1)
        layout.addLayout(mode_layout)

        # --- Groupe modèle local ---
        self.local_group = QWidget()
        local_layout = QVBoxLayout(self.local_group)
        local_layout.setContentsMargins(0, 0, 0, 0)
        local_layout.setSpacing(15)

        model_layout = QHBoxLayout()
        model_label = QLabel("Modèle IA local :")
        model_label.setStyleSheet("color: #00aaff;")
        self.model_combo = QComboBox()
        for key, info in LOCAL_MODELS.items():
            self.model_combo.addItem(info["label"], key)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo, stretch=1)
        local_layout.addLayout(model_layout)

        path_layout = QHBoxLayout()
        path_label = QLabel("Chemin du modèle :")
        path_label.setStyleSheet("color: #00aaff;")
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setPlaceholderText("Laisser vide pour utiliser models/ automatiquement")
        path_layout.addWidget(path_label)
        browse_btn = QPushButton("Parcourir…")
        browse_btn.clicked.connect(self._browse_model)
        path_layout.addWidget(browse_btn)
        local_layout.addLayout(path_layout)

        ctx_layout = QHBoxLayout()
        ctx_label = QLabel("Taille du contexte :")
        ctx_label.setStyleSheet("color: #00aaff;")
        self.ctx_spin = QSpinBox()
        self.ctx_spin.setRange(1024, 32768)
        self.ctx_spin.setSingleStep(1024)
        ctx_layout.addWidget(ctx_label)
        ctx_layout.addWidget(ctx_spin)
        local_layout.addLayout(ctx_layout)

        threads_layout = QHBoxLayout()
        threads_label = QLabel("Threads CPU :")
        threads_label.setStyleSheet("color: #00aaff;")
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 64)
        threads_layout.addWidget(threads_label)
        threads_layout.addWidget(self.threads_spin)
        local_layout.addLayout(threads_layout)

        layout.addWidget(self.local_group)

        # --- Groupe API distante ---
        self.api_group = QWidget()
        api_layout = QVBoxLayout(self.api_group)
        api_layout.setContentsMargins(0, 0, 0, 0)
        api_layout.setSpacing(15)

        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("Clé API :")
        api_key_label.setStyleSheet("color: #00aaff;")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Ex : clé Mistral AI ou OpenAI")
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_edit, stretch=1)
        api_layout.addLayout(api_key_layout)

        api_model_layout = QHBoxLayout()
        api_model_label = QLabel("Modèle API :")
        api_model_label.setStyleSheet("color: #00aaff;")
        self.api_model_edit = QLineEdit()
        self.api_model_edit.setPlaceholderText("Ex : mistral-small-latest, gpt-4o-mini")
        api_model_layout.addWidget(api_model_label)
        api_model_layout.addWidget(self.api_model_edit, stretch=1)
        api_layout.addLayout(api_model_layout)

        api_endpoint_layout = QHBoxLayout()
        api_endpoint_label = QLabel("Endpoint API :")
        api_endpoint_label.setStyleSheet("color: #00aaff;")
        self.api_endpoint_edit = QLineEdit()
        self.api_endpoint_edit.setPlaceholderText("https://api.mistral.ai/v1/chat/completions")
        api_endpoint_layout.addWidget(api_endpoint_label)
        api_endpoint_layout.addWidget(self.api_endpoint_edit, stretch=1)
        api_layout.addLayout(api_endpoint_layout)

        layout.addWidget(self.api_group)

        # --- Commun ---
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

    def _on_mode_changed(self):
        is_local = self.mode_combo.currentData() == "local"
        self.local_group.setVisible(is_local)
        self.api_group.setVisible(not is_local)

    def load_config(self):
        """Charge la configuration actuelle."""
        mode = config_manager.get_ai_mode()
        index = self.mode_combo.findData(mode)
        self.mode_combo.setCurrentIndex(index if index >= 0 else 0)
        self._on_mode_changed()

        size = config_manager.get_local_model_size()
        index = list(LOCAL_MODELS.keys()).index(size) if size in LOCAL_MODELS else \
            list(LOCAL_MODELS.keys()).index(DEFAULT_MODEL_SIZE)
        self.model_combo.setCurrentIndex(index)
        self.model_path_edit.setText(config_manager.get_local_model_path())
        self.ctx_spin.setValue(config_manager.get_local_context())
        self.threads_spin.setValue(config_manager.get_local_threads())

        self.api_key_edit.setText(config_manager.get_api_key())
        self.api_model_edit.setText(config_manager.get_api_model())
        self.api_endpoint_edit.setText(config_manager.get_api_endpoint())

        self.save_path_edit.setText(config_manager.get_save_path())

    def save_config(self):
        """Sauvegarde la configuration."""
        mode = self.mode_combo.currentData()

        if mode == "api" and not self.api_key_edit.text().strip():
            QMessageBox.warning(
                self,
                "Clé API manquante",
                "Le mode API nécessite une clé API. Renseignez-la ou revenez au modèle local."
            )
            return

        config_manager.set_ai_mode(mode)
        config_manager.set_local_model_size(self.model_combo.currentData())
        config_manager.set_local_model_path(self.model_path_edit.text().strip())
        config_manager.set_local_context(self.ctx_spin.value())
        config_manager.set_local_threads(self.threads_spin.value())
        config_manager.set_api_key(self.api_key_edit.text().strip())
        config_manager.set_api_model(self.api_model_edit.text().strip() or "mistral-small-latest")
        config_manager.set_api_endpoint(self.api_endpoint_edit.text().strip()
                                        or "https://api.mistral.ai/v1/chat/completions")

        save_path = self.save_path_edit.text().strip()
        if save_path:
            config_manager.set_save_path(save_path)

        QMessageBox.information(
            self,
            "Configuration sauvegardée",
            "La configuration a été sauvegardée avec succès."
        )

        self.accept()
