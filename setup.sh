#!/usr/bin/env bash
# Ola S1 Quick Setup Tool — macOS / Linux launcher (mirror of setup.bat).
set -euo pipefail

echo "========================================================================"
echo "                Ola S1 Quick Mod and Navigation Installer"
echo "========================================================================"
echo

# 1. Python 3
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1 && python -c 'import sys; exit(0 if sys.version_info[0]==3 else 1)'; then
    PY=python
else
    echo "[ERROR] Python 3 was not found. Install it from https://www.python.org/downloads/"
    exit 1
fi

# 2. adb
if ! command -v adb >/dev/null 2>&1; then
    for c in "$HOME/Library/Android/sdk/platform-tools/adb" \
             "$HOME/Android/Sdk/platform-tools/adb" \
             "/usr/local/bin/adb" "/opt/homebrew/bin/adb"; do
        if [ -x "$c" ]; then PATH="$(dirname "$c"):$PATH"; export PATH; break; fi
    done
fi
if ! command -v adb >/dev/null 2>&1; then
    echo "[ERROR] 'adb' not found. Install Android platform-tools:"
    echo "        https://developer.android.com/tools/releases/platform-tools"
    echo "        (macOS: 'brew install android-platform-tools')"
    exit 1
fi

cd "$(dirname "$0")"

# 3. Dependencies
echo "[*] Checking dependencies..."
"$PY" -m pip install -q --disable-pip-version-check -r requirements.txt || \
    echo "[!] Warning: pip install had an issue, trying to proceed..."

# 4. Launch
echo "[*] Starting installer..."
echo
exec "$PY" -u setup.py "$@"
