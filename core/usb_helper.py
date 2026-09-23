import shutil
import subprocess
from typing import Optional

ADB_TIMEOUT = 6


def adb_available() -> bool:
    return shutil.which("adb") is not None


def usb_device_connected() -> bool:
    """True if `adb devices` lists at least one attached device."""
    if not adb_available():
        return False
    try:
        out = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, timeout=ADB_TIMEOUT
        ).stdout
    except Exception:  # noqa: BLE001
        return False
    lines = [ln.strip() for ln in out.splitlines()[1:] if ln.strip()]
    return any(ln.endswith("device") for ln in lines)


def usb_tethering_active() -> bool:
    """
    Heuristic: after USB tethering is switched on, Windows exposes a new
    'Remote NDIS'/RNDIS network adapter. We look for it via `ipconfig`.
    This is best-effort — adapter naming differs by phone/driver, so treat
    a False result as "unknown/off" rather than a hard error.
    """
    try:
        out = subprocess.run(
            ["ipconfig"], capture_output=True, text=True, timeout=ADB_TIMEOUT
        ).stdout.lower()
    except Exception:  # noqa: BLE001
        return False
    return ("remote ndis" in out) or ("rndis" in out) or ("android" in out and "ethernet adapter" in out)


def get_usb_tethering_ip() -> Optional[str]:
    """
    Finds the IPv4 address Windows assigned to the USB-tethering (RNDIS)
    adapter, so the phone's browser can reach the LAN server over the cable
    even with Wi-Fi off. Parses `ipconfig /all` block-by-block:
    each adapter's description line is checked for tethering keywords, then
    its own 'IPv4 Address' line is read from that same block only.
    Best-effort — returns None if no matching adapter/IP is found.
    """
    try:
        out = subprocess.run(
            ["ipconfig", "/all"], capture_output=True, text=True, timeout=ADB_TIMEOUT
        ).stdout
    except Exception:  # noqa: BLE001
        return None

    keywords = ("remote ndis", "rndis", "android", "usb ethernet")
    blocks = out.split("\n\n")
    for block in blocks:
        header = block.lower()
        if not any(k in header for k in keywords):
            continue
        for line in block.splitlines():
            if "ipv4 address" in line.lower():
                # e.g. "   IPv4 Address. . . . . . . . . . . : 192.168.42.1(Preferred)"
                value = line.split(":", 1)[-1].strip()
                ip = value.split("(")[0].strip()
                if ip:
                    return ip
    return None


def usb_status_message() -> str:
    if not adb_available():
        return "adb.exe not found. Bundle platform-tools with the app to enable USB detection."
    if not usb_device_connected():
        return "No phone detected over USB. Plug in your phone and allow USB debugging if prompted."
    if not usb_tethering_active():
        return "Phone detected, but USB tethering looks off. On the phone: Settings → Network & Internet → Hotspot & Tethering → USB tethering → On."
    return "USB tethering is active."
