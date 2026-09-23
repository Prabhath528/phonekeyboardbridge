from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QCheckBox, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt

from config import APP_NAME, TERMS_URL
from core import autostart


class TermsDialog(QDialog):
    """Blocking modal shown once, before the main window is usable."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Terms & Conditions")
        self.setFixedSize(440, 260)
        self.setStyleSheet("background:#121218; color:#f2f0f8;")
        self.accepted_terms = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        info = QLabel(
            f"Before using {APP_NAME}, please review and accept the Terms & Conditions."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        link = QLabel(f'<a href="{TERMS_URL}" style="color:#b98cff;">Read the full Terms & Conditions</a>')
        link.setOpenExternalLinks(True)
        layout.addWidget(link)

        self.terms_checkbox = QCheckBox("I have read and agree to the Terms & Conditions")
        layout.addWidget(self.terms_checkbox)

        self.autostart_checkbox = QCheckBox("Launch automatically when Windows starts")
        self.autostart_checkbox.setChecked(True)  # ticked by default
        self.autostart_checkbox.stateChanged.connect(self._on_autostart_toggle)
        layout.addWidget(self.autostart_checkbox)

        layout.addStretch()

        btn_row = QHBoxLayout()
        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7c5cff, stop:1 #b98cff);"
            "color:white; padding:10px; border-radius:8px; font-weight:600;"
        )
        self.continue_btn.clicked.connect(self._on_continue)
        btn_row.addStretch()
        btn_row.addWidget(self.continue_btn)
        layout.addLayout(btn_row)

    def _on_autostart_toggle(self, state):
        if state == Qt.Unchecked:
            QMessageBox.warning(
                self,
                "Autostart disabled",
                f"{APP_NAME} will NOT start automatically with Windows.\n"
                "You'll need to open it manually whenever you want to use it.",
            )

    def _on_continue(self):
        if not self.terms_checkbox.isChecked():
            QMessageBox.information(
                self, "Please accept", "You must accept the Terms & Conditions to continue."
            )
            return
        autostart.set_enabled(self.autostart_checkbox.isChecked())
        self.accepted_terms = True
        self.accept()
