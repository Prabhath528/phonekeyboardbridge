# PhoneKeyboardBridge

Use an Android phone's on-screen/physical keyboard as a wireless keyboard for a
Windows PC — **no app install on the phone**. The phone connects with its
browser only (USB or same-Wi-Fi/LAN).

## Run in development

```bash
pip install -r requirements.txt
python main.py
```

## Branding assets

`assets_bundled/icon.png`, `assets_bundled/icon.ico` and
`assets_bundled/loading_art.png` ship with the app and are used immediately —
no download needed for the app to look right on first launch. They're used
for: the window/taskbar icon, the system tray icon, the small logo next to
the app name, and the right-hand artwork panel on the loading screen.

To customize them later without touching code, drop replacement files with
the **same names** into the GitHub release zip described below — a
downloaded file always wins over the bundled default (see
`core/paths.py: resolve_asset()`).

## Before your first real run

1. (Optional) Put a `loading_art.png` and/or `icon.png`/`icon.ico` inside a
   folder, zip it as `core_assets.zip`, and attach that zip to a GitHub
   Release on the repo set in `config.py` (`GITHUB_OWNER` / `GITHUB_REPO`).
   The app downloads and extracts this zip automatically on first launch and
   those files replace the bundled defaults. Skippable — the app looks
   complete without ever doing this.
2. Edit `config.py`:
   - `DEVELOPER_WEBSITE` / `TERMS_URL` → already set to
     `https://pixelforgestudioprabhath.netlify.app/` and its `/Terms_and_Conditions.html`.
   - `GITHUB_OWNER`, `GITHUB_REPO`, `ASSETS_ZIP_NAME` → your release details.
3. (Optional, for USB detection) bundle `adb.exe` + platform-tools next to the
   exe, or make sure `adb` is on `PATH`. Without it, the USB card will just
   tell the user adb isn't available.

## How the two connection modes work

Both cards drive the **same** local Flask + Socket.IO server (`core/lan_server.py`,
bound to `0.0.0.0:8743`) — USB tethering and Wi-Fi LAN are just two different
IPs that can reach that one server, so typing works identically either way.

- **USB Connection card** — checks `adb devices` for a phone, then looks up
  the IPv4 address Windows assigned to the RNDIS/USB-tethering adapter via
  `ipconfig /all`. If found, it starts the server (if not already running)
  and shows a QR code + PIN pointing at `http://<usb-tether-ip>:8743/` —
  exactly like the LAN card, just reached over the cable instead of Wi-Fi.
  If tethering isn't detected, it tells the user precisely what to flip on
  (this part is a best-effort heuristic; adapter names differ by phone/driver).
- **Same LAN Network card** — shows a QR code (and a 6-digit PIN as a
  fallback) pointing at `http://<your-lan-ip>:8743/`. The phone opens that
  URL in its own browser — that page (`web/phone.html`) is the entire "app":
  it shows your branding, the dev-site link, the Terms & Conditions link, and
  Cancel / Allow & Continue. Once paired, everything typed in its text box
  (plus Enter / Backspace / Space / Tab / arrow buttons) is forwarded live
  and typed on the PC via `pynput`.

## Window behavior

The title bar only shows a close button — minimize and maximize are
intentionally disabled and the window is fixed-size (`ui/main_window.py`,
`setWindowFlags` / `setFixedSize`). Closing the window hides it to the system
tray instead of exiting; use the tray icon's "Quit" to actually close the app.

## Packaging to a single .exe (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed ^
  --add-data "web;web" ^
  --name PhoneKeyboardBridge main.py
```

`web/phone.html` must ship inside the exe (the `--add-data` flag above does
that) — everything else (`loading.png`, icons, etc.) comes from the
GitHub-release download on first run instead of being baked into the exe.

## Notes / things to double-check before shipping

- Windows Firewall will prompt to allow the app on first LAN pairing attempt —
  expected, since it opens a local HTTP server.
- `allow_unsafe_werkzeug=True` in `core/lan_server.py` is fine for this
  local, single-user use case; it's not exposed to the internet.
- The system tray icon currently falls back to a blank icon until you set a
  real `.ico`/`.png` via `MainWindow.setWindowIcon(...)` in `main.py`.
