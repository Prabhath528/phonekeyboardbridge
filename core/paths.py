import os
import sys

from config import APP_NAME, ASSETS_FOLDER_NAME


def app_data_dir() -> str:
    """%APPDATA%/PhoneKeyboardBridge on Windows, ~/.phonekeyboardbridge elsewhere (dev)."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def assets_dir() -> str:
    path = os.path.join(app_data_dir(), ASSETS_FOLDER_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def first_run_marker() -> str:
    return os.path.join(app_data_dir(), ".assets_installed")


def is_first_run() -> bool:
    return not os.path.exists(first_run_marker())


def mark_first_run_done() -> None:
    with open(first_run_marker(), "w", encoding="utf-8") as f:
        f.write("ok")


def _bundled_assets_dir() -> str:
    """assets_bundled/ shipped next to main.py — used until/unless GitHub assets are downloaded."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(here, "assets_bundled")


def resolve_asset(filename: str) -> str:
    """
    Prefer the version downloaded from the GitHub release (so a future release
    can update branding), fall back to the bundled default that ships with
    the app so the UI never looks broken/empty before that download runs.
    """
    downloaded = os.path.join(assets_dir(), filename)
    if os.path.exists(downloaded):
        return downloaded
    return os.path.join(_bundled_assets_dir(), filename)


def loading_image_path() -> str:
    """Right-panel artwork on the loading screen."""
    return resolve_asset("loading_art.png")


def app_icon_path() -> str:
    """Window/taskbar/tray icon."""
    return resolve_asset("icon.ico") if sys.platform == "win32" else resolve_asset("icon.png")
