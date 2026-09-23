import os
import re

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtGui import QPixmap, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from config import APP_NAME, DEVELOPER_NAME, LOADING_SUBTITLE
from core.paths import loading_image_path, is_first_run
from core.updater import AssetDownloadThread, human_size


class LoadingScreen(QWidget):
    """
    Split-panel splash (dark left brand panel / artwork right panel),
    in the spirit of a professional installer splash screen.
    """

    ready = pyqtSignal()  # emitted when it's safe to show the main window

    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setFixedSize(680, 380)
        self.setStyleSheet("background:#000000;")
        self._downloader = None
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------------- left: brand panel ----------------
        left = QWidget()
        left.setFixedWidth(300)
        left.setStyleSheet("background:#000000;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(30, 34, 24, 24)
        left_layout.setSpacing(6)

        company = QLabel(DEVELOPER_NAME)
        company.setStyleSheet("color:#b98cff; font-size:13px; font-weight:600; letter-spacing:1px;")
        left_layout.addWidget(company)

        appname = QLabel(self._wrap_app_name(max_width=246, pixel_size=24))
        appname.setStyleSheet("color:#f2f0f8; font-size:24px; font-weight:800;")
        appname.setWordWrap(True)
        left_layout.addWidget(appname)

        left_layout.addSpacing(10)

        subtitle = QLabel(LOADING_SUBTITLE)
        subtitle.setStyleSheet("color:#8a8a9a; font-size:11px;")
        subtitle.setWordWrap(True)
        left_layout.addWidget(subtitle)

        left_layout.addStretch()

        copyright_line = QLabel(f"\u00A9 2026 {DEVELOPER_NAME}. All rights reserved.")
        copyright_line.setStyleSheet("color:#5c5c6e; font-size:10px;")
        copyright_line.setWordWrap(True)
        left_layout.addWidget(copyright_line)

        self.status_label = QLabel("Starting...")
        self.status_label.setStyleSheet("color:#b98cff; font-size:11px;")
        self.status_label.setWordWrap(True)
        left_layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet("""
            QProgressBar { background:#1a1a20; border:none; border-radius:3px; }
            QProgressBar::chunk { background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7c5cff, stop:1 #b98cff); border-radius:3px; }
        """)
        self.progress.setVisible(False)
        left_layout.addWidget(self.progress)

        root.addWidget(left)

        # ---------------- right: artwork panel ----------------
        right = QLabel()
        right.setFixedWidth(380)
        right.setAlignment(Qt.AlignCenter)
        right.setScaledContents(True)
        right.setStyleSheet("background:#0a0a0d;")
        self.art_label = right
        self._load_background()
        root.addWidget(right)

    def _wrap_app_name(self, max_width: int, pixel_size: int) -> str:
        """
        APP_NAME is one CamelCase word with no spaces, so QLabel's own word
        wrap can't break it — it just clips ('PhoneKeyboardBridge' -> cut
        off mid-letter). Split on CamelCase word boundaries instead and
        greedily wrap those pieces into lines that actually fit the panel.
        """
        words = re.findall(r"[A-Z][a-z0-9]*|[a-z0-9]+", APP_NAME) or [APP_NAME]
        font = QFont("Segoe UI", weight=QFont.ExtraBold)
        font.setPixelSize(pixel_size)
        fm = QFontMetrics(font)

        lines, current = [], ""
        for word in words:
            trial = f"{current} {word}".strip()
            if not current or fm.horizontalAdvance(trial) <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return "<br>".join(lines)

    def _load_background(self):
        path = loading_image_path()
        if os.path.exists(path):
            pix = QPixmap(path)
            self.art_label.setPixmap(pix)

    def start(self):
        if is_first_run():
            self._run_first_time_download()
        else:
            self.status_label.setText("Loading...")
            QTimer.singleShot(600, self.ready.emit)

    def _run_first_time_download(self):
        self.progress.setVisible(True)
        self.status_label.setText("Preparing first-time setup...")

        self._downloader = AssetDownloadThread()
        self._downloader.status.connect(self.status_label.setText)
        self._downloader.progress.connect(self._on_progress)
        self._downloader.finished_ok.connect(self._on_done)
        self._downloader.failed.connect(self._on_failed)
        self._downloader.start()

    def _on_progress(self, downloaded: int, total: int, elapsed: float):
        if total > 0:
            pct = int(downloaded * 100 / total)
            self.progress.setValue(pct)
            self.status_label.setText(
                f"Downloading... {human_size(downloaded)} / {human_size(total)} ({elapsed:.1f}s)"
            )
        else:
            self.status_label.setText(f"Downloading... {human_size(downloaded)} ({elapsed:.1f}s)")

    def _on_done(self):
        self._load_background()
        self.status_label.setText("Setup complete.")
        self.progress.setValue(100)
        QTimer.singleShot(450, self.ready.emit)

    def _on_failed(self, message: str):
        self.status_label.setText(f"Setup failed: {message}")
        QTimer.singleShot(1800, self.ready.emit)
