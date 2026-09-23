import os
import time
import zipfile

import requests
from PyQt5.QtCore import QThread, pyqtSignal

from config import GITHUB_OWNER, GITHUB_REPO, ASSETS_ZIP_NAME
from core.paths import assets_dir, app_data_dir, mark_first_run_done


class AssetDownloadThread(QThread):
    # bytes_downloaded, total_bytes, elapsed_seconds
    progress = pyqtSignal(int, int, float)
    # human readable status line (e.g. "Extracting...")
    status = pyqtSignal(str)
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def run(self):
        try:
            self.status.emit("Locating latest release...")
            api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
            r = requests.get(api_url, timeout=20)
            r.raise_for_status()
            release = r.json()

            asset_url = None
            for asset in release.get("assets", []):
                if asset.get("name") == ASSETS_ZIP_NAME:
                    asset_url = asset.get("browser_download_url")
                    break

            if not asset_url:
                self.failed.emit(
                    f"Could not find '{ASSETS_ZIP_NAME}' in the latest GitHub release."
                )
                return

            zip_path = os.path.join(app_data_dir(), ASSETS_ZIP_NAME)

            self.status.emit("Downloading core assets...")
            start = time.time()
            with requests.get(asset_url, stream=True, timeout=30) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                downloaded = 0
                with open(zip_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total, time.time() - start)

            self.status.emit("Extracting...")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(assets_dir())

            try:
                os.remove(zip_path)
            except OSError:
                pass

            mark_first_run_done()
            self.finished_ok.emit()

        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
