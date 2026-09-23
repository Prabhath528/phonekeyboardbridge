import random
import socket
import threading

from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO
from pynput.keyboard import Controller, Key
from PyQt5.QtCore import QObject, pyqtSignal

from config import APP_NAME, DEVELOPER_NAME, DEVELOPER_WEBSITE, TERMS_URL, LAN_HTTP_PORT, PIN_LENGTH

_SPECIAL_KEYS = {
    "enter": Key.enter,
    "backspace": Key.backspace,
    "space": Key.space,
    "tab": Key.tab,
    "esc": Key.esc,
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
}


def get_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:  # noqa: BLE001
        return "127.0.0.1"
    finally:
        s.close()


class LanServer(QObject):
    """
    Runs a local Flask + Socket.IO server.
    Phone opens http://<lan-ip>:PORT/ in its browser — nothing to install.
    A PIN (also encoded in a QR code by the UI layer) gates pairing.
    """

    client_paired = pyqtSignal(str)      # emits remote addr on successful pairing
    client_rejected = pyqtSignal(str)    # emits remote addr on bad PIN
    server_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode="threading")
        self.keyboard = Controller()
        self.pin = self._new_pin()
        self._paired_sids = set()
        self._thread = None
        self._register_routes()

    def _new_pin(self) -> str:
        return "".join(random.choice("0123456789") for _ in range(PIN_LENGTH))

    def regenerate_pin(self) -> str:
        self.pin = self._new_pin()
        self._paired_sids.clear()
        return self.pin

    @property
    def lan_ip(self) -> str:
        return get_lan_ip()

    @property
    def url(self) -> str:
        return f"http://{self.lan_ip}:{LAN_HTTP_PORT}/"

    def _register_routes(self):
        app, socketio = self.app, self.socketio

        @app.route("/")
        def phone_page():
            with open("web/phone.html", "r", encoding="utf-8") as f:
                template = f.read()
            return render_template_string(
                template,
                app_name=APP_NAME,
                dev_name=DEVELOPER_NAME,
                dev_site=DEVELOPER_WEBSITE,
                terms_url=TERMS_URL,
            )

        @app.route("/api/pin-check", methods=["POST"])
        def pin_check():
            data = request.get_json(force=True, silent=True) or {}
            ok = data.get("pin") == self.pin
            return jsonify({"ok": ok})

        @socketio.on("pair")
        def on_pair(data):
            sid = request.sid
            if data.get("pin") == self.pin:
                self._paired_sids.add(sid)
                socketio.emit("pair_result", {"ok": True}, to=sid)
                self.client_paired.emit(request.remote_addr or "")
            else:
                socketio.emit("pair_result", {"ok": False}, to=sid)
                self.client_rejected.emit(request.remote_addr or "")

        @socketio.on("key")
        def on_key(data):
            sid = request.sid
            if sid not in self._paired_sids:
                return  # ignore unpaired clients
            self._handle_key_event(data)

        @socketio.on("disconnect")
        def on_disconnect():
            self._paired_sids.discard(request.sid)

    def _handle_key_event(self, data: dict):
        kind = data.get("type")
        value = data.get("value", "")
        try:
            if kind == "text" and value:
                self.keyboard.type(value)
            elif kind == "special":
                key = _SPECIAL_KEYS.get(value)
                if key:
                    self.keyboard.press(key)
                    self.keyboard.release(key)
        except Exception as exc:  # noqa: BLE001
            self.server_error.emit(str(exc))

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self.socketio.run,
            args=(self.app,),
            kwargs={"host": "0.0.0.0", "port": LAN_HTTP_PORT, "allow_unsafe_werkzeug": True},
            daemon=True,
        )
        self._thread.start()
