#!/usr/bin/env python3
"""End-to-end test of setup.py's install/uninstall flow over a fake `adb` binary.

This exercises the REAL setup.py code paths — grant_mod, revoke_mod,
_installed_packages, uninstall_mods — through the actual subprocess -> adb boundary
(no monkeypatched _adb_shell), against a FakeAndroid device. No scooter, no emulator.

Run (from the repo root):  python test_setup_integration.py   (or: pytest)
"""
import importlib.util
import json
import os
import stat
import sys
import tempfile
import types

_REPO = os.path.dirname(os.path.abspath(__file__))
BALL = "com.yaaratech.ball"
BALL_SVC = f"{BALL}/{BALL}.core.QuickBallService"
FOREIGN_SVC = "com.other/.SvcA"


def _load_setup():
    for name in ("grpc", "ola"):
        sys.modules.setdefault(name, types.ModuleType(name))
    spec = importlib.util.spec_from_file_location("setup_it", os.path.join(_REPO, "setup.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_fake_adb(tmpdir: str, state_path: str) -> str:
    """Write a tiny executable that runs testsupport/fake_adb.py, and point its state file."""
    adb = os.path.join(tmpdir, "adb")
    fake = os.path.join(_REPO, "testsupport", "fake_adb.py")
    with open(adb, "w") as fh:
        fh.write(f'#!/bin/sh\nexport FAKE_ADB_STATE="{state_path}"\nexec "{sys.executable}" "{fake}" "$@"\n')
    os.chmod(adb, os.stat(adb).st_mode | stat.S_IEXEC | stat.S_IRWXU)
    return adb


def _seed_state(state_path: str):
    # Device already has Balls installed and a FOREIGN accessibility service enabled.
    json.dump(
        {
            "packages": [BALL, "com.other"],
            "secure": {"enabled_accessibility_services": FOREIGN_SVC, "accessibility_enabled": "1"},
            "appops": {},
            "perms": {},
        },
        open(state_path, "w"),
    )


def _read_state(state_path: str) -> dict:
    return json.load(open(state_path))


def test_install_grant_then_uninstall_is_clean_and_preserves_foreign_service():
    setup = _load_setup()
    balls = next(a for a in setup._manifest_apks() if a["packageName"] == BALL)
    grants = balls["grants"]

    with tempfile.TemporaryDirectory() as tmp:
        state = os.path.join(tmp, "device.json")
        _seed_state(state)
        adb = _make_fake_adb(tmp, state)
        dev = "fake-0"

        # INSTALL half: apply the grant contract.
        setup.grant_mod(adb, dev, BALL, grants)
        s = _read_state(state)
        svcs = s["secure"]["enabled_accessibility_services"].split(":")
        assert FOREIGN_SVC in svcs, "foreign accessibility service was clobbered!"
        assert BALL_SVC in svcs, "Balls service was not enabled"
        assert s["secure"]["accessibility_enabled"] == "1"
        assert s["appops"][BALL]["SYSTEM_ALERT_WINDOW"] == "allow"
        assert s["appops"][BALL]["WRITE_SETTINGS"] == "allow"

        # UNINSTALL half: revert grants + pm uninstall.
        setup.uninstall_mods(dev, adb, [BALL])
        s = _read_state(state)
        assert BALL not in s["packages"], "package was not uninstalled"
        svcs = [x for x in s["secure"]["enabled_accessibility_services"].split(":") if x]
        assert svcs == [FOREIGN_SVC], f"foreign service not preserved / Balls not removed: {svcs}"
        assert s["secure"]["accessibility_enabled"] == "1", "accessibility disabled despite other svc"
        # appops for the package are gone once it is uninstalled (as on a real device);
        # that revoke_mod reset them to "default" first is covered by test_flow.py.


def test_uninstall_skips_packages_not_installed():
    setup = _load_setup()
    with tempfile.TemporaryDirectory() as tmp:
        state = os.path.join(tmp, "device.json")
        json.dump({"packages": [], "secure": {}, "appops": {}, "perms": {}}, open(state, "w"))
        adb = _make_fake_adb(tmp, state)
        # Should not raise, and should not resurrect anything.
        setup.uninstall_mods("fake-0", adb, [BALL])
        assert BALL not in _read_state(state)["packages"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"ok   {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    raise SystemExit(1 if failed else 0)
