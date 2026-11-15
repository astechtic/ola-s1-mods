#!/usr/bin/env python3
"""End-to-end test of ola.py's gRPC transport against a fake wifican daemon.

Starts a real gRPC server implementing /wifican.WifiCanRpc/ExecuteADBCommand on
localhost and drives ola.py's connect + command round-trip through it — proving the
hand-rolled protobuf request/response wire format matches, with no scooter.

Needs grpcio (ola.py imports grpc). Skips cleanly when it is not installed, so the
rest of the suite still runs. Run (from the repo root):  python test_grpc.py
"""
import importlib.util
import os

_REPO = os.path.dirname(os.path.abspath(__file__))

try:
    import grpc  # noqa: F401
    from testsupport.fake_android import FakeAndroid
    from testsupport import fake_wifican
    _spec = importlib.util.spec_from_file_location("ola_under_test", os.path.join(_REPO, "ola.py"))
    ola = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ola)
    _HAVE_GRPC = True
except Exception:  # grpcio missing in this environment
    _HAVE_GRPC = False

try:
    import pytest  # for skipping under pytest
except Exception:
    pytest = None


def _requires_grpc():
    if not _HAVE_GRPC:
        if pytest is not None:
            pytest.skip("grpcio not installed")
        return False
    return True


def test_connect_and_info_roundtrip():
    if not _requires_grpc():
        return
    device = FakeAndroid({"packages": ["com.asjohn720.ball"], "secure": {}, "appops": {}, "perms": {}})
    server, port, _ = fake_wifican.start(device)
    try:
        channel = ola.connect(f"127.0.0.1:{port}", wait=5.0)
        status, out = ola.run(channel, "id -u", quiet=True)
        assert ola.ok(status), status
        assert out == "0", f"expected root uid, got {out!r}"
        status, rel = ola.run(channel, "getprop ro.build.version.release", quiet=True)
        assert rel == "11", rel
        channel.close()
    finally:
        server.stop(0)


def test_shell_wrapped_command_roundtrip():
    """ola.py base64-wraps shell commands; the daemon must unwrap and run them."""
    if not _requires_grpc():
        return
    device = FakeAndroid()
    server, port, dev = fake_wifican.start(device)
    try:
        channel = ola.connect(f"127.0.0.1:{port}", wait=5.0)
        # Enable an accessibility service through the wrapped-shell path, then read it back.
        svc = "com.asjohn720.ball/com.asjohn720.ball.core.QuickBallService"
        ola.run(channel, ola.sh_wrap(f"settings put secure enabled_accessibility_services {svc}"), quiet=True)
        status, out = ola.run(channel, ola.sh_wrap("settings get secure enabled_accessibility_services"), quiet=True)
        assert ola.ok(status)
        assert out == svc, f"round-trip mismatch: {out!r}"
    finally:
        server.stop(0)


if __name__ == "__main__":
    if not _HAVE_GRPC:
        print("SKIP: grpcio not installed in this interpreter")
        raise SystemExit(0)
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as exc:
                failed += 1
                print(f"FAIL {name}: {exc}")
    raise SystemExit(1 if failed else 0)
