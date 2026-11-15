# Balls — S1 fork notes (reconstruction record)

This directory is **QuickBall v6.1.0** ([chayanforyou/QuickBall](https://github.com/chayanforyou/QuickBall),
GPL-3.0-or-later), vendored via `git subtree --squash`, then rebranded to the S1 app.

## Confirmed: Balls == package-renamed QuickBall
The shipped `balls-1.1.0-lite-release.apk` decompiled to the exact QuickBall package layout
(`core/QuickBallService`, `ui/MainActivity`, `ui/floating/*`, `domain/models/*`) with only the
namespace changed. QuickBall's `minSdk 21 / targetSdk 37` match the APK. So the fork is a
rebrand, not a code rewrite.

## Rebrand applied in this repo (vs upstream)
- `namespace` + `applicationId`: `io.github.chayanforyou.quickball` → **`com.asjohn720.ball`**
  (all 71 source/config references updated; package dir moved under `com/asjohn720/ball`).
- `app_name` string → **"Balls"**.
- Manifest components resolve to `com.asjohn720.ball.ui.MainActivity` and
  `com.asjohn720.ball.core.QuickBallService` — exactly what the S1Mods installer grants
  (`AdbManager.grantBallPermissions` / `setup.py`).

## Build: VERIFIED ✅
`./gradlew :app:assembleDebug` succeeds (Gradle 9.4.1, JDK 25, AGP via wrapper). Output
`com.asjohn720.ball` labelled **Balls**. The project has two flavors — use **`foss`**
(`assembleFossRelease`) for open-source distribution; `play` pulls Google Play/billing deps.

## Still to do
- [ ] Prefer the **foss** flavor for the shipped APK; wire release signing via
      `keystore.properties` (mirror `android/`), then `assembleFossRelease`.
- [ ] **Version**: currently inherits upstream `6.1.0 (25)`. Decide whether to keep that or
      reset to an S1 scheme; only `applicationId` matters to the installer.
- [ ] **S1 feature deltas** seen in the shipped build / CHANGELOG 1.2, to re-apply as commits
      on top of upstream (QuickBall already provides most of the machinery):
  - Floating Back / Home / Settings actions mapped to the MoveOS HMI (QuickBall actions).
  - Lockscreen/standby auto-hide (QuickBall has `ui/screens/autohide` — configure for S1).
  - Auto-return timer to `com.olaelectric.hmiclient` (new S1 action).
  - App drawer to switch mods (QuickBall `ui/screens/shortcut` select-apps — configure).
  - `QuickBallCommandReceiver`: present in the old APK, **not** in upstream and **not**
    required by the installer; re-add only if external/ADB broadcast control is wanted.
- [ ] Release signing via `keystore.properties` (mirror the pattern in `android/`).
- [ ] Build, install on an S1 head unit, confirm parity; record APK SHA-256 in
      `apks/manifest.json`.

## License
GPL-3.0-or-later (upstream `LICENSE` retained). Preserve QuickBall copyright headers.
