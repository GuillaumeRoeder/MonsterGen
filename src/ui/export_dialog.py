"""Fen\u00eatre de dialogue d'export de la fiche courante.

Permet de choisir le dossier de destination et le format (PNG par
d\u00e9faut) ; le nom de fichier est d\u00e9riv\u00e9 du nom du monstre.
"""

from PySide6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLineEdit,
    QLabel, QMessageBox, QPushButton, QVBoxLayout,
)


class ExportDialog(QDialog):
    """Dialogue d'export : dossier + format (PNG s\u00e9lectionn\u00e9 par d\u00e9faut)."""

    def __init__(self, default_folder: str, base_filename: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exporter la fiche")
        self.setMinimumWidth(480)

        self._base_filename = base_filename

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit(default_folder)
        browse_btn = QPushButton("Parcourir...")
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(self.folder_edit, stretch=1)
        folder_row.addWidget(browse_btn)
        form.addRow("Dossier :", folder_row)

        self.format_combo = QComboBox()
        self.format_combo.addItem("PNG", "png")
        self.format_combo.addItem("PDF", "pdf")
        self.format_combo.setCurrentIndex(0)
        self.format_combo.currentIndexChanged.connect(self._update_filename)
        form.addRow("Format :", self.format_combo)

        self.filename_label = QLabel("")
        self.filename_label.setStyleSheet("color: #9aa0b4;")
        form.addRow("Fichier :", self.filename_label)

        layout.addLayout(form)
        self._update_filename()

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        export_btn = QPushButton("Exporter")
        export_btn.clicked.connect(self.accept)
        buttons.addWidget(export_btn)
        layout.addLayout(buttons)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier d'export", self.folder_edit.text()
        )
        if folder:
            self.folder_edit.setText(folder)

    def _update_filename(self):
        self.filename_label.setText(
            f"{self._base_filename}.{self.selected_format()}"
        )

    def selected_folder(self) -> str:
        return self.folder_edit.text().strip()

    def selected_format(self) -> str:
        return self.format_combo.currentData()

    def accept(self):
        if not self.selected_folder():
            QMessageBox.warning(
                self, "Dossier manquant",
                "Veuillez choisir un dossier d'export."
            )
            return
        super().accept()
