#!/usr/bin/env python3
"""Integrity checks for apks/manifest.json — the single source of truth for the
mod APKs S1Mods installs.

Device-free, so it runs in CI. Verifies the manifest's shape, that every
*bundled* APK file exists and its SHA-256 matches, and that every *download*
entry carries a hash to verify against. Mirrors what setup.py / ApkDownloader
enforce at install time.

Run (from the repo root):  python test_manifest.py   (or: pytest)
"""
import hashlib
import json
import os

_REPO = os.path.dirname(os.path.abspath(__file__))
_MANIFEST = os.path.join(_REPO, "apks", "manifest.json")

_REQUIRED = ("id", "packageName", "fileName", "distribution", "license", "upstream")
_SHA_RE_LEN = 64


def _load():
    with open(_MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_manifest_parses_and_has_apks():
    data = _load()
    assert data.get("schema") == 1, "unexpected manifest schema version"
    assert isinstance(data.get("apks"), list) and data["apks"], "no apks listed"


def test_every_entry_has_required_fields():
    for apk in _load()["apks"]:
        for key in _REQUIRED:
            assert apk.get(key), f"{apk.get('id', '?')}: missing field {key!r}"
        assert apk["distribution"] in ("bundled", "download"), apk["distribution"]


def test_ids_and_package_names_unique():
    apks = _load()["apks"]
    ids = [a["id"] for a in apks]
    pkgs = [a["packageName"] for a in apks]
    assert len(ids) == len(set(ids)), "duplicate id in manifest"
    assert len(pkgs) == len(set(pkgs)), "duplicate packageName in manifest"


def test_bundled_apks_exist_and_match_sha256():
    for apk in _load()["apks"]:
        if apk["distribution"] != "bundled":
            continue
        path = os.path.join(_REPO, "apks", apk["fileName"])
        assert os.path.isfile(path), f"{apk['id']}: bundled APK missing at {path}"
        expected = apk.get("sha256")
        assert expected and len(expected) == _SHA_RE_LEN, f"{apk['id']}: bad sha256 field"
        actual = _sha256(path)
        assert actual == expected, (
            f"{apk['id']}: sha256 mismatch\n  expected {expected}\n  actual   {actual}"
        )
        if apk.get("sizeBytes") is not None:
            assert os.path.getsize(path) == apk["sizeBytes"], f"{apk['id']}: sizeBytes mismatch"


def test_download_entries_are_verifiable():
    """A download entry with no sha256 would install unverified — refuse that."""
    for apk in _load()["apks"]:
        if apk["distribution"] != "download":
            continue
        assert apk.get("downloadUrl"), f"{apk['id']}: download entry without downloadUrl"
        sha = apk.get("sha256")
        assert sha and len(sha) == _SHA_RE_LEN, (
            f"{apk['id']}: download entry without a sha256 to verify against"
        )


def test_every_entry_points_at_vendored_source():
    for apk in _load()["apks"]:
        src = apk.get("source")
        assert src and os.path.isdir(os.path.join(_REPO, src)), (
            f"{apk['id']}: source dir {src!r} not found"
        )


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
