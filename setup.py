#!/usr/bin/env python3
"""
Ola S1 Quick Mod & Setup Tool
Automates:
  1. Finding Ola scooter IP over local Wi-Fi
  2. Keeping scooter awake via Ola Diagnostic App
  3. Unlocking ADB access (safe, reversible RAM bind-mount)
  4. Verifying bundled local APKs (Balls & Music Mod)
  5. Installing APKs & granting required permissions
  6. Launching Balls for easy floating navigation
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time

try:
    import grpc
    import ola
except ImportError:
    print("[!] Missing dependencies. Installing grpcio...")
    subprocess.run([sys.executable, "-m", "pip", "install", "grpcio>=1.50.0"], check=True)
    import grpc
    import ola

BANNER = r"""
========================================================================
     ___  _          ____  _     ___        _      _     ____       _               
    / _ \| | __ _   / ___|/ |   / _ \ _   _(_) ___| | __/ ___|  ___| |_ _   _ _ __  
   | | | | |/ _` |  \___ \| |  | | | | | | | |/ __| |/ /\___ \ / _ \ __| | | | '_ \ 
   | |_| | | (_| |   ___) | |  | |_| | |_| | | (__|   <  ___) |  __/ |_| |_| | |_) |
    \___/|_|\__,_|  |____/|_|   \__\_\\__,_|_|\___|_|\_\|____/ \___|\__|\__,_| .__/ 
                                                                              |_|    
               Automated Floating Navigation & Music Installer
========================================================================
"""

def print_step(num: int, title: str):
    print(f"\n[{num}/6] {title}")
    print("-" * 60)

def _repo_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))

def load_apk_manifest() -> dict:
    """Loads apks/manifest.json (the single source of truth for mod APKs)."""
    path = os.path.join(_repo_dir(), "apks", "manifest.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        print(f"[!] Could not read {path}: {e}")
        return {"apks": []}

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def verify_apk(path: str, expected_sha256: str | None) -> bool:
    """Returns True if the file matches the expected SHA-256. No expected hash -> skip (warn)."""
    if not expected_sha256:
        print(f"    [!] No pinned SHA-256 for {os.path.basename(path)}; skipping verification.")
        return True
    actual = sha256_file(path)
    if actual.lower() == expected_sha256.lower():
        print(f"    [+] Verified {os.path.basename(path)} (SHA-256 OK).")
        return True
    print(f"    [!] SHA-256 MISMATCH for {os.path.basename(path)}!")
    print(f"        expected {expected_sha256}")
    print(f"        actual   {actual}")
    return False

def find_adb() -> str:
    """Finds adb executable path on the system."""
    found = shutil.which("adb")
    if found:
        return found
    
    # Common Android SDK locations
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
        r"C:\platform-tools\adb.exe",
        r"C:\Program Files\platform-tools\adb.exe",
        r"C:\Program Files\DroidCam\Client\data\obs-plugins\droidcam-obs\adb\adb.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return ""

def test_tcp_port6(ip: str, port: int, scope: int | None, timeout: float = 0.8) -> bool:
    """Tests if an IPv6 TCP port is open."""
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s.settimeout(timeout)
        scope_id = scope if scope is not None else 0
        s.connect((ip, port, 0, scope_id))
        s.close()
        return True
    except Exception:
        return False

def _probe_candidates(candidates: list[tuple[str, int]]) -> tuple[str, int] | None:
    """Tries port 50005 on each (ip, scope) candidate; returns the first that answers."""
    seen = set()
    for ip, scope in candidates:
        key = (ip, scope)
        if key in seen:
            continue
        seen.add(key)
        print(f"    Checking {ip}%{scope} ...", end="", flush=True)
        if test_tcp_port6(ip, 50005, scope):
            print(" [OPEN] -> Found Ola Scooter!")
            return ip, scope
        print(" [closed]")
    return None

def _iface_index(name: str) -> int:
    try:
        return socket.if_nametoindex(name)
    except Exception:
        return 0

def _scan_windows() -> tuple[str, int] | None:
    ps_cmd = 'Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Select-Object -ExpandProperty InterfaceIndex'
    try:
        proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        indices = [int(x.strip()) for x in proc.stdout.splitlines() if x.strip().isdigit()]
    except Exception:
        indices = []
    for idx in indices:
        subprocess.run(f"ping -6 -n 1 -w 300 ff02::1%{idx}", shell=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)
    try:
        out = subprocess.check_output("netsh interface ipv6 show neighbors", text=True, stderr=subprocess.DEVNULL)
    except Exception:
        out = ""
    current_idx = None
    candidates = []
    for line in out.splitlines():
        m_if = re.match(r"Interface\s+(\d+):", line)
        if m_if:
            current_idx = int(m_if.group(1))
        elif current_idx and line.strip().startswith("fe80:"):
            parts = line.split()
            if len(parts) >= 3 and parts[2].lower() != "unreachable":
                candidates.append((parts[0], current_idx))
    return _probe_candidates(candidates)

def _active_unix_ifaces() -> list[str]:
    """Best-effort list of up, non-loopback interface names on macOS/Linux."""
    names: list[str] = []
    try:
        # Works on both macOS and Linux
        out = subprocess.check_output(["ifconfig"], text=True, stderr=subprocess.DEVNULL)
        for blk in re.split(r"\n(?=\S)", out):
            m = re.match(r"(\w+):", blk)
            if m and "LOOPBACK" not in blk and ("UP" in blk or "RUNNING" in blk):
                names.append(m.group(1))
    except Exception:
        pass
    if not names:
        try:
            out = subprocess.check_output(["ip", "-o", "link", "show", "up"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                m = re.search(r"\d+:\s+([^:@]+)", line)
                if m and m.group(1) != "lo":
                    names.append(m.group(1).strip())
        except Exception:
            pass
    return names

def _scan_unix() -> tuple[str, int] | None:
    ifaces = _active_unix_ifaces()
    # Nudge the neighbor table via multicast ping on each interface.
    for name in ifaces:
        subprocess.run(["ping6", "-c", "1", f"ff02::1%{name}"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ping", "-6", "-c", "1", f"ff02::1%{name}"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    candidates: list[tuple[str, int]] = []
    # macOS: `ndp -an`  -> "fe80::...%en0   <mac>   en0 ..."
    try:
        out = subprocess.check_output(["ndp", "-an"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            m = re.match(r"(fe80::[0-9a-fA-F:]+)%(\w+)", line.strip())
            if m:
                candidates.append((m.group(1), _iface_index(m.group(2))))
    except Exception:
        pass
    # Linux: `ip -6 neigh` -> "fe80::... dev wlan0 lladdr <mac> REACHABLE"
    if not candidates:
        try:
            out = subprocess.check_output(["ip", "-6", "neigh"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                m = re.match(r"(fe80::[0-9a-fA-F:]+)\s+dev\s+(\w+)", line.strip())
                if m and "FAILED" not in line:
                    candidates.append((m.group(1), _iface_index(m.group(2))))
        except Exception:
            pass
    return _probe_candidates(candidates)

def scan_for_scooter() -> tuple[str, int] | None:
    """Pings IPv6 multicast and scans the neighbor table for open port 50005.

    Cross-platform: Windows (netsh), macOS (ndp), Linux (ip -6 neigh).
    """
    print("[*] Pinging local IPv6 multicast to discover network devices...")
    print("[*] Scanning IPv6 neighbor table for Ola Head Unit (Port 50005)...")
    system = platform.system()
    if system == "Windows":
        return _scan_windows()
    if system in ("Darwin", "Linux"):
        return _scan_unix()
    print(f"[!] Automatic scan not supported on {system}. Use --ipv6 / Manual Mode.")
    return None

def pre_setup_wake(channel):
    """Wakes screen safely without modifying persistent sleep/power states."""
    print("[*] Waking display...")
    ola.run(channel, "input keyevent 224", quiet=True)
    print("    >> PRE-CHECK: Ensure scooter side stand is UP and screen stays awake during mods.")
    import time
    time.sleep(0.5)

def unlock_adb(channel, ipv6: str, scope: int | None, adb_exe: str) -> str:
    """Safely unlocks ADB via RAM bind mount without flashing partitions."""
    print("[*] Preparing ADB key...")
    adb_key_dir = os.path.expanduser("~/.android")
    adb_pub = os.path.join(adb_key_dir, "adbkey.pub")
    if not os.path.exists(adb_pub):
        print("    Generating fresh ADB keypair on PC...")
        os.makedirs(adb_key_dir, exist_ok=True)
        subprocess.run([adb_exe, "keygen", os.path.join(adb_key_dir, "adbkey")], check=True, stdout=subprocess.DEVNULL)

    print("    Uploading PC public key to scooter...")
    ola.push(channel, adb_pub, "/data/local/tmp/adb_keys_mine")
    ola.run(channel, "chmod 644 /data/local/tmp/adb_keys_mine", quiet=True)

    print("    Setting scootermode=serv...")
    ola.run(channel, "setprop persist.ola.security.scootermode serv", quiet=True)

    bind_script = """#!/system/bin/sh
if [ -f /data/misc/adb/adbkeymoveos3_pub_prod ]; then
    T=/data/misc/adb/adbkeymoveos3_pub_prod
elif [ -f /data/misc/adb/adb_keys ]; then
    T=/data/misc/adb/adb_keys
else
    T=/adbkeymoveos3_pub_prod
fi
mount | grep -q " $T " && umount "$T"
mount --bind /data/local/tmp/adb_keys_mine "$T" || exit 1
echo "bound $T"
"""
    tmp_path = os.path.join(tempfile.gettempdir(), "ola_bind_key.sh")
    with open(tmp_path, "wb") as f:
        f.write(bind_script.replace("\r\n", "\n").encode("ascii"))

    ola.push(channel, tmp_path, "/data/local/tmp/bind_key.sh")
    ola.run(channel, "chmod 755 /data/local/tmp/bind_key.sh", quiet=True)
    ola.run(channel, "sh /data/local/tmp/bind_key.sh", quiet=True)
    time.sleep(1.0)

    device = f"[{ipv6}%{scope}]:5555" if scope else f"[{ipv6}]:5555"
    print(f"[*] Connecting ADB to {device}...")

    # Retry the connect a few times and verify the real device state before claiming success.
    connected = False
    for attempt in range(1, 4):
        subprocess.run([adb_exe, "connect", device], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.0)
        res = subprocess.run([adb_exe, "-s", device, "get-state"], capture_output=True, text=True)
        if "device" in res.stdout:
            connected = True
            break
        print(f"    [*] ADB not ready (attempt {attempt}/3): {res.stdout.strip() or res.stderr.strip() or 'no state'}")

    if not connected:
        raise SystemExit(
            "[!] ADB authorization failed: device did not reach 'device' state on "
            f"{device}.\n"
            "    The in-memory key bind may not have taken. Check that the scooter screen is\n"
            "    awake and that port 5555 is reachable, then re-run. (Nothing persistent was\n"
            "    changed; a vehicle restart clears the temporary key mount.)")

    print("    [+] ADB connected and verified as 'device'.")
    return device

# --- Mod grant contracts (from apks/manifest.json "grants") --------------------------
# Install and uninstall read the SAME contract, so they stay symmetric: everything
# install turns on, uninstall turns back off. Mirrors ModRegistry.kt in the app.

def _manifest_apks() -> list[dict]:
    return load_apk_manifest().get("apks", [])


def all_mod_packages() -> list[str]:
    return [a["packageName"] for a in _manifest_apks() if a.get("packageName")]


def _adb_shell(adb_exe: str, device: str, *args: str, capture: bool = False) -> str:
    """Run `adb -s <device> shell <args...>`. Quiet by default; returns stdout if capture."""
    cmd = [adb_exe, "-s", device, "shell", *args]
    if capture:
        res = subprocess.run(cmd, capture_output=True, text=True)
        return (res.stdout or "").strip()
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return ""


def _enabled_accessibility_services(adb_exe: str, device: str) -> list[str]:
    # `settings get` prints the literal "null" when the key is unset.
    raw = _adb_shell(adb_exe, device, "settings", "get", "secure",
                     "enabled_accessibility_services", capture=True)
    if not raw or raw == "null":
        return []
    return [s for s in (p.strip() for p in raw.split(":")) if s]


def add_accessibility_service(adb_exe: str, device: str, service: str):
    """Enable an accessibility service WITHOUT clobbering any already-enabled one."""
    services = _enabled_accessibility_services(adb_exe, device)
    if service not in services:
        services.append(service)
    _adb_shell(adb_exe, device, "settings", "put", "secure",
               "enabled_accessibility_services", ":".join(services))
    _adb_shell(adb_exe, device, "settings", "put", "secure", "accessibility_enabled", "1")


def remove_accessibility_service(adb_exe: str, device: str, service: str):
    """Drop our accessibility service from the list, leaving any others intact."""
    services = [s for s in _enabled_accessibility_services(adb_exe, device) if s != service]
    _adb_shell(adb_exe, device, "settings", "put", "secure",
               "enabled_accessibility_services", ":".join(services))
    if not services:
        _adb_shell(adb_exe, device, "settings", "put", "secure", "accessibility_enabled", "0")


def grant_mod(adb_exe: str, device: str, pkg: str, grants: dict, launch: bool = True):
    """Apply a mod's contract: appops -> runtime permissions -> accessibility (merge-safe)."""
    for op in grants.get("appops", []):
        _adb_shell(adb_exe, device, "appops", "set", pkg, op, "allow")
    for perm in grants.get("permissions", []):
        _adb_shell(adb_exe, device, "pm", "grant", pkg, perm)
    svc = grants.get("accessibilityService")
    if svc:
        add_accessibility_service(adb_exe, device, svc)
    activity = grants.get("launchActivity")
    if launch and activity:
        _adb_shell(adb_exe, device, "am", "start", "-n", activity)
        time.sleep(1.0)


def revoke_mod(adb_exe: str, device: str, pkg: str, grants: dict):
    """Exact inverse of grant_mod, run before `pm uninstall`."""
    _adb_shell(adb_exe, device, "am", "force-stop", pkg)
    svc = grants.get("accessibilityService")
    if svc:
        remove_accessibility_service(adb_exe, device, svc)
    for op in grants.get("appops", []):
        _adb_shell(adb_exe, device, "appops", "set", pkg, op, "default")
    for perm in grants.get("permissions", []):
        _adb_shell(adb_exe, device, "pm", "revoke", pkg, perm)


def _installed_packages(adb_exe: str, device: str) -> set[str]:
    out = _adb_shell(adb_exe, device, "pm", "list", "packages", capture=True)
    return {
        line.strip().removeprefix("package:")
        for line in out.splitlines()
        if line.strip().startswith("package:")
    }


def install_and_grant(device: str, adb_exe: str, apks: dict[str, str]):
    """Installs bundled APKs (integrity-verified) and grants each one's contract."""
    manifest = _manifest_apks()
    sha_by_name = {a.get("fileName"): a.get("sha256") for a in manifest}
    pkg_by_name = {a.get("fileName"): a.get("packageName") for a in manifest}
    grants_by_pkg = {a.get("packageName"): (a.get("grants") or {}) for a in manifest}

    def safe_install(apk_path: str, app_name: str) -> bool:
        print(f"[*] Installing {app_name} ({os.path.basename(apk_path)})...")
        if not verify_apk(apk_path, sha_by_name.get(os.path.basename(apk_path))):
            print(f"    [!] REFUSING to install {app_name}: integrity check failed.")
            return False
        res = subprocess.run([adb_exe, "-s", device, "install", "-r", "-d", apk_path], capture_output=True, text=True)
        combined = (res.stdout + " " + res.stderr).strip()
        if "Success" in combined:
            print(f"    [+] {app_name} installed successfully.")
            return True
        if "ALREADY_EXISTS" in combined or "signatures do not match" in combined:
            print(f"    [+] {app_name} is already installed / updated.")
            return True
        print(f"    [!] Install failed for {app_name}: {combined or 'unknown error'}")
        return False

    installed_pkgs: list[str] = []
    for name, path in apks.items():
        if os.path.isfile(path) and safe_install(path, name):
            pkg = pkg_by_name.get(os.path.basename(path))
            if pkg:
                installed_pkgs.append(pkg)

    for pkg in installed_pkgs:
        grants = grants_by_pkg.get(pkg) or {}
        if not grants:
            continue
        print(f"[*] Granting permissions to {pkg} via ADB...")
        grant_mod(adb_exe, device, pkg, grants)
        print(f"    [+] {pkg}: permissions & settings applied.")

    print("[*] Bringing Dashboard Home to front...")
    _adb_shell(adb_exe, device, "am", "start", "-n", "com.olaelectric.hmiclient/.MainActivity")
    _adb_shell(adb_exe, device, "input", "keyevent", "3")
    print("    [+] Scooter returned to speedometer dashboard.")


def uninstall_mods(device: str, adb_exe: str, packages: list[str]):
    """Cleanly removes mods: revert each one's grant contract, THEN `pm uninstall`."""
    grants_by_pkg = {a.get("packageName"): (a.get("grants") or {}) for a in _manifest_apks()}
    present = _installed_packages(adb_exe, device)
    any_done = False
    for pkg in packages:
        if pkg not in present:
            print(f"[*] {pkg} is not installed; skipping.")
            continue
        any_done = True
        print(f"[*] Uninstalling {pkg} ...")
        grants = grants_by_pkg.get(pkg) or {}
        if grants:
            print("    [*] Reverting permissions, accessibility & appops...")
            revoke_mod(adb_exe, device, pkg, grants)
        else:
            _adb_shell(adb_exe, device, "am", "force-stop", pkg)
        res = subprocess.run([adb_exe, "-s", device, "uninstall", pkg], capture_output=True, text=True)
        out = (res.stdout + " " + res.stderr).strip()
        print(f"    [+] {pkg}: {out or 'removed'}")
    if not any_done:
        print("[*] Nothing to uninstall.")
    print("[*] Bringing Dashboard Home to front...")
    _adb_shell(adb_exe, device, "am", "start", "-n", "com.olaelectric.hmiclient/.MainActivity")
    _adb_shell(adb_exe, device, "input", "keyevent", "3")

def main():
    print(BANNER)

    parser = argparse.ArgumentParser(description="Ola S1 Quick Mod & Setup Tool")
    parser.add_argument("--ipv6", help="Scooter IPv6 address (e.g. fe80::1234:5678:9abc:def0)")
    parser.add_argument("--scope", type=int, help="Interface scope ID (e.g. 22)")
    parser.add_argument("--port", type=int, default=50005, help="Ola gRPC port (default 50005)")
    parser.add_argument(
        "--uninstall", nargs="*", metavar="PKG",
        help="Uninstall mods (revert grants, then remove) instead of installing. "
             "With no package names, removes every mod listed in apks/manifest.json.",
    )
    args = parser.parse_args()

    # Step 1: Check ADB
    print_step(1, "Verifying Tools & Environment")
    adb_exe = find_adb()
    if not adb_exe:
        print("[!] ERROR: 'adb' was not found on your system.")
        print("    Please install Android Platform Tools or add adb.exe to your PATH.")
        print("    Download from: https://developer.android.com/tools/releases/platform-tools")
        sys.exit(1)
    print(f"[+] ADB found: {adb_exe}")

    # Step 2: Locate Scooter
    print_step(2, "Connecting to Ola Scooter on Wi-Fi")
    ipv6 = args.ipv6
    scope = args.scope

    if not ipv6:
        while True:
            found = scan_for_scooter()
            if found:
                ipv6, scope = found
                print(f"[+] Discovered scooter at: {ipv6} (Scope {scope})")
                break
            else:
                print("\n[!] Could not automatically detect scooter on Wi-Fi.")
                print("    Please ensure:")
                print("    1. Your PC and Scooter are connected to the SAME Wi-Fi.")
                print("    2. The scooter screen is AWAKE (press power button or tap display).")
                print("\nOptions:")
                print("  [1] Try scanning again")
                print("  [2] Enter Scooter IPv6 address manually")
                print("  [3] Exit")
                choice = input("\nEnter choice [1-3] (default 1): ").strip()
                if choice == "2":
                    ipv6 = input("Enter Scooter IPv6 (e.g. fe80::1234:5678:9abc:def0): ").strip()
                    scope_str = input("Enter Interface Scope ID (e.g. 22): ").strip()
                    scope = int(scope_str) if scope_str else None
                    break
                elif choice == "3":
                    sys.exit(0)

    target = ola.build_target(ipv6, args.port, scope)
    print(f"[*] Connecting to Ola daemon at {target} ...")
    try:
        channel = ola.connect(target, wait=6.0)
    except Exception as e:
        print(f"[!] Failed to connect to scooter at {target}: {e}")
        print("    Ensure scooter is awake and Wi-Fi is active.")
        sys.exit(1)

    # Step 3: Prevent Sleep & Wake Screen
    print_step(3, "Waking Screen & Pre-Flight Check")
    pre_setup_wake(channel)

    # Step 4: Unlock ADB
    print_step(4, "Unlocking ADB Access")
    device = unlock_adb(channel, ipv6, scope, adb_exe)

    # Uninstall path: revert each mod's grants, then remove it. Shares steps 1-4 above.
    if args.uninstall is not None:
        print_step(5, "Uninstalling Mods & Reverting Permissions")
        targets = args.uninstall or all_mod_packages()
        print(f"[*] Targets: {', '.join(targets)}")
        uninstall_mods(device, adb_exe, targets)
        print("\n" + "=" * 72)
        print("              MODS UNINSTALLED & SETTINGS REVERTED              ")
        print("=" * 72)
        print("[+] Scooter display is back on your Speedometer Dashboard.")
        return

    # Step 5: Verify Bundled APKs
    print_step(5, "Verifying Bundled Mod APK Packages")
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    apks_dir = os.path.join(repo_dir, "apks")

    apks_to_install = {
        "Balls Navigation": os.path.join(apks_dir, "balls-1.1.0-lite-release.apk"),
        "Music Mod": os.path.join(apks_dir, "musicmod-release.apk"),
        "Android Auto": os.path.join(apks_dir, "com.asjohn720.androidauto.apk")
    }

    if not os.path.isfile(apks_to_install["Balls Navigation"]):
        print(f"[!] Error: Mandatory APK missing at {apks_to_install['Balls Navigation']}")
        sys.exit(1)

    for name, path in apks_to_install.items():
        if os.path.isfile(path):
            print(f"    [+] Found: {os.path.basename(path)} ({os.path.getsize(path)/1024/1024:.2f} MB)")
        else:
            print(f"    [-] Optional APK not found: {os.path.basename(path)} (skipping)")

    # Step 6: Install & Configure
    print_step(6, "Installing Modded Apps & Granting Permissions")
    install_and_grant(device, adb_exe, apks_to_install)

    # Completion Banner & User Guide
    print("\n" + "=" * 72)
    print("         CONGRATULATIONS! ALL MODS INSTALLED SUCCESSFULLY!       ")
    print("=" * 72)
    print("\n[+] Scooter display is now back on your Speedometer Dashboard.")
    print("[+] Balls navigation overlay is active and ready to use!")
    print("\n>>> HOW TO USE YOUR NEW MODS:")
    print("  Tap the floating ball on your screen anytime to access:")
    print("    * Back          -> Instant Back button inside any app")
    print("    * Home          -> Instant return to Speedometer Dashboard")
    print("    * Settings      -> Direct access to Android Settings (Wi-Fi, Bluetooth, etc.)")
    print("    * Music Mod     -> Ad-free streaming & offline music playback")
    print("    * Android Auto  -> OpenHeadUnit projection")
    print("    * Via Browser   -> Lightweight web browsing")
    print("\nNo manual configuration required - everything is ready to enjoy!")
    print("=" * 72)

if __name__ == "__main__":
    main()
