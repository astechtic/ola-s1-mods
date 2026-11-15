#!/usr/bin/env python3
"""Tests for the install/uninstall flow in setup.py — the grant/revoke contract.

These are the parts that silently corrupt a user's device if wrong: enabling an
accessibility service must NOT clobber another app's, and uninstall must leave
the device exactly as install found it. No scooter and no grpcio needed — the
ADB layer and the grpc/ola imports are stubbed.

Run (from the repo root):  python test_flow.py   (or: pytest)
"""
import importlib.util
import os
import sys
import types

_REPO = os.path.dirname(os.path.abspath(__file__))
BALL = "com.yaaratech.ball/com.yaaratech.ball.core.QuickBallService"


def _load_setup():
    """Import setup.py with its heavy imports stubbed so it loads in any env."""
    for name in ("grpc", "ola"):
        sys.modules.setdefault(name, types.ModuleType(name))
    spec = importlib.util.spec_from_file_location("setup_under_test", os.path.join(_REPO, "setup.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _FakeDevice:
    """Records ADB shell calls and models the two secure settings we touch."""

    def __init__(self, enabled="", accessibility_enabled="0"):
        self.secure = {
            "enabled_accessibility_services": enabled,
            "accessibility_enabled": accessibility_enabled,
        }
        self.calls = []

    def shell(self, _adb, _dev, *args, capture=False):
        self.calls.append(tuple(args))
        if args[:3] == ("settings", "get", "secure"):
            return self.secure.get(args[3], "null") if capture else ""
        if args[:3] == ("settings", "put", "secure"):
            self.secure[args[3]] = args[4]
        return ""

    def services(self):
        v = self.secure["enabled_accessibility_services"]
        return [s for s in v.split(":") if s]


def _bind(setup, dev):
    setup._adb_shell = dev.shell


def test_enable_does_not_clobber_existing_service():
    setup = _load_setup()
    dev = _FakeDevice(enabled="com.other/.SvcA", accessibility_enabled="1")
    _bind(setup, dev)
    setup.add_accessibility_service("a", "d", BALL)
    assert set(dev.services()) == {"com.other/.SvcA", BALL}
    assert dev.secure["accessibility_enabled"] == "1"


def test_enable_is_idempotent():
    setup = _load_setup()
    dev = _FakeDevice()
    _bind(setup, dev)
    setup.add_accessibility_service("a", "d", BALL)
    setup.add_accessibility_service("a", "d", BALL)
    assert dev.services().count(BALL) == 1


def test_remove_keeps_other_services_and_stays_enabled():
    setup = _load_setup()
    dev = _FakeDevice(enabled=f"com.other/.SvcA:{BALL}", accessibility_enabled="1")
    _bind(setup, dev)
    setup.remove_accessibility_service("a", "d", BALL)
    assert dev.services() == ["com.other/.SvcA"]
    assert dev.secure["accessibility_enabled"] == "1"


def test_remove_last_service_disables_accessibility():
    setup = _load_setup()
    dev = _FakeDevice(enabled=BALL, accessibility_enabled="1")
    _bind(setup, dev)
    setup.remove_accessibility_service("a", "d", BALL)
    assert dev.services() == []
    assert dev.secure["accessibility_enabled"] == "0"


def test_grant_and_revoke_are_symmetric():
    setup = _load_setup()
    dev = _FakeDevice()
    _bind(setup, dev)
    grants = {
        "appops": ["SYSTEM_ALERT_WINDOW"],
        "permissions": ["android.permission.RECORD_AUDIO"],
        "accessibilityService": None,
        "launchActivity": None,
    }
    setup.grant_mod("a", "d", "pkg.x", grants)
    setup.revoke_mod("a", "d", "pkg.x", grants)
    for expected in (
        ("appops", "set", "pkg.x", "SYSTEM_ALERT_WINDOW", "allow"),
        ("appops", "set", "pkg.x", "SYSTEM_ALERT_WINDOW", "default"),
        ("pm", "grant", "pkg.x", "android.permission.RECORD_AUDIO"),
        ("pm", "revoke", "pkg.x", "android.permission.RECORD_AUDIO"),
        ("am", "force-stop", "pkg.x"),
    ):
        assert expected in dev.calls, expected


def test_manifest_grants_match_registered_packages():
    """Every mod in the manifest carries a usable grants block."""
    setup = _load_setup()
    for apk in setup._manifest_apks():
        grants = apk.get("grants")
        assert grants is not None, f"{apk.get('id')}: no grants block"
        assert isinstance(grants.get("appops", []), list)
        assert isinstance(grants.get("permissions", []), list)


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
