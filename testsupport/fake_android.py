#!/usr/bin/env python3
"""A tiny in-memory model of an Android head unit that interprets the handful of
shell commands the S1Mods flows use (pm / appops / settings / am / input / getprop).

It is the shared device-double behind both test fronts:
  * fake_wifican.py  — serves it over the scooter's gRPC method (ola.py's transport)
  * fake_adb.py      — serves it over a fake `adb` binary (setup.py's transport)

So the same realistic device answers both the gRPC layer and the ADB layer, with no
scooter and no emulator. State can be persisted to JSON so it survives the many
separate `adb` subprocess invocations setup.py makes.
"""
from __future__ import annotations

import base64
import json
import os
import re

_GETPROP = {
    "ro.build.version.release": "11",
    "ro.build.display.id": "OLA.S1.FAKE",
    "ro.build.version.security_patch": "2025-01-01",
    "ro.product.model": "Ola S1 (fake)",
    "persist.ola.security.scootermode": "0",
}


class FakeAndroid:
    def __init__(self, state: dict | None = None):
        self.packages: set[str] = set(state.get("packages", [])) if state else set()
        self.secure: dict[str, str] = dict(state.get("secure", {})) if state else {}
        # appops[pkg][op] = mode ; perms[pkg] = set(granted)
        self.appops: dict[str, dict[str, str]] = state.get("appops", {}) if state else {}
        self.perms: dict[str, list[str]] = state.get("perms", {}) if state else {}

    # ---- persistence -----------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "packages": sorted(self.packages),
            "secure": self.secure,
            "appops": self.appops,
            "perms": self.perms,
        }

    @classmethod
    def load(cls, path: str) -> "FakeAndroid":
        if os.path.isfile(path):
            with open(path) as fh:
                return cls(json.load(fh))
        return cls()

    def save(self, path: str) -> None:
        with open(path, "w") as fh:
            json.dump(self.to_dict(), fh)

    # ---- command execution ----------------------------------------------
    def execute_line(self, line: str) -> tuple[int, str]:
        """Run a whitespace/${IFS} command string (gRPC form); unwraps sh -c base64."""
        line = line.replace("${IFS}", " ").strip()
        m = re.match(r"^sh -c echo\s+([A-Za-z0-9+/=]+)\s*\|\s*base64 -d\s*\|\s*sh$", line)
        if m:
            inner = base64.b64decode(m.group(1)).decode()
            return self.execute_tokens(inner.split())
        return self.execute_tokens(line.split())

    def execute_tokens(self, t: list[str]) -> tuple[int, str]:
        """Run an already-tokenised command (adb `shell` form). Returns (status, stdout).

        status follows the daemon convention ola.py expects: 1 = success.
        """
        if not t:
            return 1, ""
        cmd = t[0]

        if cmd == "id" and t[1:2] == ["-u"]:
            return 1, "0"
        if cmd == "getenforce":
            return 1, "Enforcing"
        if cmd == "getprop" and len(t) >= 2:
            return 1, _GETPROP.get(t[1], "")
        if cmd in ("am", "input", "svc", "monkey"):
            return 1, ""  # launches / key events: no stdout, success

        if cmd == "pm":
            return self._pm(t[1:])
        if cmd == "appops":
            return self._appops(t[1:])
        if cmd == "settings":
            return self._settings(t[1:])

        return 1, ""  # unknown but harmless

    # ---- subcommands -----------------------------------------------------
    def _pm(self, a: list[str]) -> tuple[int, str]:
        if not a:
            return 1, ""
        if a[0] == "list" and a[1:2] == ["packages"]:
            flt = a[2] if len(a) > 2 else None
            names = sorted(p for p in self.packages if not flt or flt in p)
            return 1, "\n".join(f"package:{p}" for p in names)
        if a[0] == "install":
            # last arg is the apk path; register a synthetic package for it
            pkg = "installed." + os.path.basename(a[-1]).split(".apk")[0]
            self.packages.add(pkg)
            return 1, "Success"
        if a[0] == "uninstall" and len(a) >= 2:
            self.packages.discard(a[-1])
            self.perms.pop(a[-1], None)
            self.appops.pop(a[-1], None)
            return 1, "Success"
        if a[0] == "grant" and len(a) >= 3:
            self.perms.setdefault(a[1], [])
            if a[2] not in self.perms[a[1]]:
                self.perms[a[1]].append(a[2])
            return 1, ""
        if a[0] == "revoke" and len(a) >= 3:
            if a[1] in self.perms and a[2] in self.perms[a[1]]:
                self.perms[a[1]].remove(a[2])
            return 1, ""
        return 1, ""

    def _appops(self, a: list[str]) -> tuple[int, str]:
        # appops set <pkg> <op> <mode>
        if len(a) >= 4 and a[0] == "set":
            self.appops.setdefault(a[1], {})[a[2]] = a[3]
            return 1, ""
        return 1, ""

    def _settings(self, a: list[str]) -> tuple[int, str]:
        # settings get|put secure <key> [value]
        if len(a) >= 3 and a[0] == "get" and a[1] == "secure":
            return 1, self.secure.get(a[2], "null")
        if len(a) >= 3 and a[0] == "put" and a[1] == "secure":
            # value may be empty string (e.g. clearing the list)
            self.secure[a[2]] = a[3] if len(a) >= 4 else ""
            return 1, ""
        return 1, ""
