#!/usr/bin/env python3
"""A fake `adb` executable backed by FakeAndroid, for driving setup.py's ADB flow
without a device. Install it as the `adb_exe` setup.py calls; device state persists
across invocations in the JSON file named by $FAKE_ADB_STATE.

Supports the subset setup.py uses:
    adb -s <serial> shell <cmd...>
    adb -s <serial> install -r -d <apk>
    adb -s <serial> uninstall <pkg>
    adb -s <serial> get-state      (prints "device")
"""
from __future__ import annotations

import os
import sys

# Allow running as a plain script (no package context).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from testsupport.fake_android import FakeAndroid  # noqa: E402


def main(argv: list[str]) -> int:
    state_path = os.environ.get("FAKE_ADB_STATE")
    if not state_path:
        print("FAKE_ADB_STATE not set", file=sys.stderr)
        return 2
    device = FakeAndroid.load(state_path)

    # Strip a leading "-s <serial>".
    args = list(argv)
    if args[:1] == ["-s"]:
        args = args[2:]
    if not args:
        return 0

    sub, rest = args[0], args[1:]
    code, out = 0, ""
    if sub == "shell":
        status, out = device.execute_tokens(rest)
        code = 0 if status in (0, 1) else 1
    elif sub == "install":
        status, out = device.execute_tokens(["pm", "install", *rest])
    elif sub == "uninstall":
        status, out = device.execute_tokens(["pm", "uninstall", *rest])
    elif sub == "get-state":
        out = "device"
    # other adb subcommands (connect, wait-for-device, tcpip) are accepted as no-ops

    device.save(state_path)
    if out:
        sys.stdout.write(out + ("\n" if not out.endswith("\n") else ""))
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
