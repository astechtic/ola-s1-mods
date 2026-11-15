# mods/ — the S1Mods companion apps, from source

Each subdirectory is a buildable fork of an upstream open-source app. These were previously
shipped only as compiled APKs; this directory makes them fully open and reproducible.

| Dir | App | applicationId | Upstream (pin) | License | Build state |
| --- | --- | --- | --- | --- | --- |
| `balls` | Balls (floating nav) | `com.asjohn720.ball` | QuickBall | GPL-3.0-or-later | source pending (Phase 2) |
| `openplay` | OpenPlay (projection) | `com.asjohn720.openplay` | DiPlay | GPL-3.0 | source pending (Phase 3) |
| `music` | Music Mod | `com.asjohn720.musicmod` | Square 2.8.0 | GPL-3.0-or-later | source pending (Phase 4) |
| `androidauto` | Android Auto | `com.asjohn720.androidauto` | open-headunit 4.0.0-beta2 | AGPL-3.0 | source pending (Phase 5) |

## How each fork is reconstructed
No original fork source existed, so each is rebuilt **from its upstream**, not from the
decompiled binary (release APKs are R8/ProGuard-obfuscated and unusable as source):

1. `git subtree add --prefix mods/<x> <upstream-url> <tag>` at the pinned version.
2. Apply the deltas in `mods/<x>/RECOVERY.md` (recovered from the APK's **manifest,
   resources, and declared components** — the readable parts).
3. Add `keystore.properties`-based release signing (see `docs/BUILD.md`).
4. Build, install on an Ola S1 head unit, confirm behavior matches the shipped APK.
5. Record the output APK's SHA-256 in [`../apks/manifest.json`](../apks/manifest.json).

Rebuilt APKs are **functionally equivalent, not byte-identical** to the originals (new build
env + new signing key); installing them over an existing copy requires an uninstall first.
