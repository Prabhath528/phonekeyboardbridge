import io

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSystemTrayIcon, QMenu, QAction, QDialog
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QUrl

from config import APP_NAME, APP_VERSION, DEVELOPER_NAME, DEVELOPER_WEBSITE, TERMS_URL, PROMO_URL, LAN_HTTP_PORT
from core import usb_helper
from core.lan_server import LanServer
from core.paths import app_icon_path

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    _HAS_WEBENGINE = True
except ImportError:
    _HAS_WEBENGINE = False

try:
    import qrcode
    _HAS_QRCODE = True
except ImportError:
    _HAS_QRCODE = False


# NOTE: no background is set on the bare "QWidget" selector — that previously
# painted every child QLabel with its own #0a0a0d fill, which showed up as a
# mismatched rectangle behind text sitting on the (lighter) #121218 cards.
# QMainWindow owns the app-wide background; everything else stays transparent
# unless a rule explicitly styles it (QFrame#card, buttons, etc).
DARK_QSS = """
QMainWindow { background:#0a0a0d; }
QWidget { color:#f2f0f8; font-family:'Segoe UI'; background: transparent; }
QFrame#card {
    background:#121218; border:1px solid #242430; border-radius:14px;
}
QLabel#cardTitle { font-size:15px; font-weight:600; background: transparent; }
QLabel#cardDesc { color:#8a8a9a; font-size:12px; background: transparent; }
QLabel#statusLine { color:#b98cff; font-size:12px; background: transparent; }
QPushButton#primary {
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7c5cff, stop:1 #b98cff);
    color:white; padding:10px; border-radius:8px; font-weight:600; border:none;
}
QPushButton#textBtn { background:transparent; color:#b98cff; border:none; font-size:13px; }
QDialog { background:#121218; }
"""


class InfoDialog(QDialog):
    """Shared About/Help look: icon + title + rich-text body with real hyperlinks."""

    def __init__(self, parent, title: str, html_body: str):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(420)
        self.setStyleSheet("background:#121218; color:#f2f0f8;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        icon_label = QLabel()
        pix = QPixmap(app_icon_path())
        if not pix.isNull():
            icon_label.setPixmap(pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:16px; font-weight:700;")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        body = QLabel(html_body)
        body.setOpenExternalLinks(True)
        body.setWordWrap(True)
        body.setStyleSheet("font-size:13px; color:#d8d6e2;")
        layout.addWidget(body)

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primary")
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7c5cff, stop:1 #b98cff);"
            "color:white; padding:10px; border-radius:8px; font-weight:600; border:none;"
        )
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)

        # title bar keeps only the close button — minimize/maximize are
        # intentionally disabled; closing hides to tray instead (see closeEvent)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setFixedSize(760, 640)

        icon = QIcon(app_icon_path())
        if not icon.isNull():
            self.setWindowIcon(icon)

        self.setStyleSheet(DARK_QSS)

        self.lan_server = None

        self._build_ui()
        self._build_tray()

    # ---------- UI ----------
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(16)

        # header
        header = QHBoxLayout()

        logo = QLabel()
        pix = QPixmap(app_icon_path())
        if not pix.isNull():
            logo.setPixmap(pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header.addWidget(logo)

        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size:18px; font-weight:700; margin-left:6px;")
        header.addWidget(title)
        header.addStretch()

        about_btn = QPushButton("About")
        about_btn.setObjectName("textBtn")
        about_btn.setCursor(Qt.PointingHandCursor)
        about_btn.clicked.connect(self.show_about)
        header.addWidget(about_btn)

        help_btn = QPushButton("Help")
        help_btn.setObjectName("textBtn")
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.clicked.connect(self.show_help)
        header.addWidget(help_btn)

        outer.addLayout(header)

        # connection cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        cards_row.addWidget(self._build_usb_card())
        cards_row.addWidget(self._build_lan_card())
        outer.addLayout(cards_row, stretch=1)

        # promo / ads area
        outer.addWidget(self._build_promo_area(), stretch=1)

    # ---------- USB card (now an actual working connection method) ----------
    def _build_usb_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel("USB Connection")
        title.setObjectName("cardTitle")
        layout.addWidget(title)

        desc = QLabel("Plug your phone in with a USB cable and turn on USB tethering.")
        desc.setObjectName("cardDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.usb_qr_label = QLabel()
        self.usb_qr_label.setAlignment(Qt.AlignCenter)
        self.usb_qr_label.setFixedHeight(120)
        layout.addWidget(self.usb_qr_label)

        self.usb_pin_label = QLabel("")
        self.usb_pin_label.setObjectName("statusLine")
        self.usb_pin_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.usb_pin_label)

        self.usb_status_label = QLabel("Not checked yet.")
        self.usb_status_label.setObjectName("cardDesc")
        self.usb_status_label.setWordWrap(True)
        layout.addWidget(self.usb_status_label)

        layout.addStretch()

        check_btn = QPushButton("Connect via USB")
        check_btn.setObjectName("primary")
        check_btn.setCursor(Qt.PointingHandCursor)
        check_btn.clicked.connect(self._start_usb)
        layout.addWidget(check_btn)

        return card

    def _start_usb(self):
        usb_ip = usb_helper.get_usb_tethering_ip()
        if not usb_ip:
            self.usb_qr_label.clear()
            self.usb_pin_label.setText("")
            self.usb_status_label.setText(usb_helper.usb_status_message())
            return

        server = self._ensure_server_started()
        url = f"http://{usb_ip}:{LAN_HTTP_PORT}/"
        self.usb_pin_label.setText(f"PIN: {server.pin}")
        self.usb_status_label.setText(f"USB tethering detected. Open {url} on the phone, or scan the QR code.")
        self._render_qr(self.usb_qr_label, url + f"?pin={server.pin}")

    # ---------- LAN card ----------
    def _build_lan_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel("Same LAN Network")
        title.setObjectName("cardTitle")
        layout.addWidget(title)

        desc = QLabel("Make sure your phone is on the same Wi-Fi, then scan the QR code or enter the PIN.")
        desc.setObjectName("cardDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setFixedHeight(120)
        layout.addWidget(self.qr_label)

        self.pin_label = QLabel("")
        self.pin_label.setObjectName("statusLine")
        self.pin_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.pin_label)

        self.lan_status_label = QLabel("Not started.")
        self.lan_status_label.setObjectName("cardDesc")
        self.lan_status_label.setWordWrap(True)
        layout.addWidget(self.lan_status_label)

        layout.addStretch()

        start_btn = QPushButton("Start LAN Pairing")
        start_btn.setObjectName("primary")
        start_btn.setCursor(Qt.PointingHandCursor)
        start_btn.clicked.connect(self._start_lan)
        layout.addWidget(start_btn)

        return card

    def _start_lan(self):
        server = self._ensure_server_started()
        self.pin_label.setText(f"PIN: {server.pin}")
        self.lan_status_label.setText(f"Waiting for phone... open {server.url} or scan the QR code.")
        self._render_qr(self.qr_label, server.url + f"?pin={server.pin}")

    # ---------- shared server / QR plumbing ----------
    def _ensure_server_started(self) -> LanServer:
        """
        One Socket.IO server, bound to all interfaces, serves both cards —
        USB tethering and LAN Wi-Fi are just different IPs reaching the same
        server, so the phone-side flow and PC-side typing are identical.
        """
        if self.lan_server is None:
            self.lan_server = LanServer()
            self.lan_server.client_paired.connect(self._on_client_paired)
            self.lan_server.client_rejected.connect(self._on_client_rejected)
            self.lan_server.start()
        return self.lan_server

    def _render_qr(self, label: QLabel, data: str):
        if not _HAS_QRCODE:
            label.setText("QR unavailable\n(pip install qrcode[pil])")
            return
        img = qrcode.make(data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        pix = QPixmap()
        pix.loadFromData(buf.getvalue())
        label.setPixmap(pix.scaledToHeight(110, Qt.SmoothTransformation))

    def _on_client_paired(self, addr: str):
        msg = f"Connected — phone paired ({addr}). Start typing on the phone."
        self.lan_status_label.setText(msg)
        self.usb_status_label.setText(msg)

    def _on_client_rejected(self, addr: str):
        msg = f"A device tried to pair with the wrong PIN ({addr})."
        self.lan_status_label.setText(msg)
        self.usb_status_label.setText(msg)

    def _build_promo_area(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)

        if _HAS_WEBENGINE:
            view = QWebEngineView()
            view.load(QUrl(PROMO_URL))
            layout.addWidget(view)
        else:
            label = QLabel(f'<a href="{PROMO_URL}" style="color:#b98cff;">{PROMO_URL}</a>')
            label.setOpenExternalLinks(True)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)

        return card

    # ---------- tray ----------
    def _build_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.windowIcon() if not self.windowIcon().isNull() else QIcon())
        self.tray.setToolTip(APP_NAME)

        menu = QMenu()
        restore_action = QAction("Open", self)
        restore_action.triggered.connect(self._restore_from_tray)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(restore_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: self._restore_from_tray() if reason == QSystemTrayIcon.Trigger else None
        )
        self.tray.show()

    def _restore_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def _quit_app(self):
        from PyQt5.QtWidgets import QApplication
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        # app must always live in the tray instead of fully closing
        event.ignore()
        self.hide()
        self.tray.showMessage(APP_NAME, "Still running in the system tray.", QSystemTrayIcon.Information, 2000)

    # ---------- about / help ----------
    def show_about(self):
        html = (
            f"<b>{APP_NAME}</b> v{APP_VERSION}<br><br>"
            f"Turns an Android phone into a wireless keyboard for this PC over "
            f"USB or your local Wi-Fi network — no app install needed on the phone.<br><br>"
            f"Developed by <a href='{DEVELOPER_WEBSITE}'>{DEVELOPER_NAME}</a><br>"
            f"<a href='{TERMS_URL}'>Terms &amp; Conditions</a><br><br>"
            f"&copy; 2026 {DEVELOPER_NAME}. All rights reserved."
        )
        InfoDialog(self, f"About {APP_NAME}", html).exec_()

    def show_help(self):
        html = (
            "<b>How to use</b><br>"
            "1. Choose USB Connection or Same LAN Network.<br>"
            "2. USB: connect the cable and turn on USB tethering on the phone, "
            "then tap <i>Connect via USB</i>.<br>"
            "3. LAN: keep phone &amp; PC on the same Wi-Fi, then scan the QR code "
            "or open the link and enter the PIN shown here.<br>"
            "4. On the phone page, tap the text box and type — it goes straight to your PC.<br><br>"
            f"<a href='{TERMS_URL}'>Terms &amp; Conditions</a>"
        )
        InfoDialog(self, "Help", html).exec_()
