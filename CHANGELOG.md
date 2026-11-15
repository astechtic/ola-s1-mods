## [1.0.0] - 2026-11-15 — Open-source ecosystem (first public `yaaratech` release)

First end-to-end open-source release: the S1Mods app (`com.yaaratech.s1mods` v1.0.0) plus all
four companion mods building from source, a symmetric install/uninstall flow, MoveOS-safety
guardrails with `--revert`, CI + a device-free test suite, and illustrated docs. Release APKs
(app + 4 mods + `SHA256SUMS`) are attached to the `v1.0.0` GitHub Release.

### 📖 Full open-source transparency
* **Multi-license repo:** added canonical `LICENSES/` (GPL-3.0, AGPL-3.0),
  `THIRD_PARTY_NOTICES.md`, and per-mod `LICENSE` files. The MIT license now explicitly
  covers only the S1Mods app and tooling; each companion app keeps its upstream (A)GPL license.
* **All four companion apps are now open source and build from source.** Each is vendored
  from its upstream (`git subtree --squash`) and rebranded, and each was build-verified to
  produce an exact identity match (package / version / launcher / label) to the shipped APK:
  * **Balls** ← QuickBall v6.1.0 (`com.yaaratech.ball`, foss flavor) — GPL-3.0-or-later.
  * **OpenPlay** ← DiPlay v0.2.22 (`com.yaaratech.openplay`, incl. NDK native) — GPL-3.0.
  * **Music Mod** ← Square v2.8.0 (`com.yaaratech.musicmod`, Rust/librespot core) — GPL-3.0-or-later.
  * **Android Auto** ← open-headunit v.4.0.0-beta2 (`com.yaaratech.androidauto`, github flavor,
    C++/NDK + Shizuku AIDL) — AGPL-3.0.
  Each `mods/<x>/S1_RECOVERY.md` records the exact deltas and the verified toolchain; the
  per-fork build matrix (Gradle / JDK / NDK / Rust) is in `docs/BUILD.md`.
* **OpenPlay download now verified:** `apks/manifest.json` pins the shipped OpenPlay APK's
  SHA-256 (previously `null` = installed unverified) and its upstream tag.

### 🏗️ Build & tooling
* **Single APK source of truth:** bundled mod APKs moved to top-level `apks/` with
  `apks/manifest.json` (package, version, SHA-256, upstream, license). Gradle now copies them
  into assets at build time — no more duplicate committed binaries.
* **Real release signing:** `android/` reads a release keystore from `keystore.properties` /
  CI env vars (falls back to debug with a warning). See `docs/BUILD.md`.
* **Integrity checks:** `setup.py` and the in-app downloader verify APK SHA-256 before install.
* **Cross-platform setup:** `setup.py` now scans on macOS (`ndp`) and Linux (`ip -6 neigh`)
  as well as Windows; added `setup.sh` launcher. ADB unlock now reports real success/failure
  instead of always printing success.
* **CI:** `.github/workflows/ci.yml` runs `pytest` (wire-protocol + manifest-integrity +
  install-flow tests) on every push/PR; `.github/workflows/release.yml` builds all five APKs
  from source on a tag, signs each from CI secrets, writes `SHA256SUMS`, and publishes a
  GitHub Release with build-provenance attestation. Added `test_manifest.py`, `test_flow.py`.

### 📖 Illustrated ecosystem docs
* **`docs/ECOSYSTEM.md`:** a visual walkthrough of the whole toolkit (app + 4 mods + CLI),
  how it connects to the head unit, and the app shown in **both connected and not-connected
  states** across Setup / App Manager / Toolbox. Screenshots live in `docs/images/` and are
  captured live on an Android emulator (the connected shots use the project's own fake
  `wifican` daemon, so the flow is demonstrable with no scooter). README now leads with a
  connected-vs-offline preview.

### 🛡️ MoveOS safety, reversibility & OTA compatibility
* **Nothing persistent left behind, by design:** the only persistent MoveOS change (the
  `scootermode` property needed for ADB) is now **captured before it's changed** and restored
  exactly by a new `setup.py --revert`. The ADB key is a RAM bind-mount (cleared by a reboot);
  mods live in `/data`; the system partition is never written. Run `--revert` (and reboot)
  before an Ola OTA or handover — see the corrected, accurate messaging.
* **Guardrail against touching the vehicle's own software:** `setup.py --uninstall` only acts
  on packages listed in the manifest, and the app's uninstall path refuses MoveOS/Ola/Android
  system packages outright — a typo can never remove `com.olaelectric.hmiclient` or a system
  app. Covered by tests.
* **New `docs/SAFETY.md`** documenting exactly what is touched, its persistence, OTA
  compatibility, integrity verification, and responsible-use limits.

### 🔁 Proper install / uninstall flow
* **Symmetric, data-driven grants:** install and uninstall now read one per-mod contract
  (the `grants` block in `apks/manifest.json`, mirrored by `ModRegistry` in the app), so
  uninstall undoes exactly what install did — stop app, remove accessibility entry, reset
  app-ops, revoke permissions, then `pm uninstall`. See `docs/INSTALL_UNINSTALL.md`.
* **Fixed accessibility clobber:** enabling a mod's accessibility service now **merges** into
  `enabled_accessibility_services` instead of overwriting it, so it no longer silently
  disables any other accessibility app the rider had on. Fixed in both `setup.py` and the
  app's `AdbManager`.
* **`setup.py --uninstall`:** a real uninstall path (all mods, or named packages) that
  reverts grants before removing — previously the PC tool could only install.
* **Build fix:** `android/gradle.properties` opts into the Provider-based assets source
  (`android.sourceset.disallowProvider=false`) so the app actually assembles on AGP 9.x.
* **Testable without a scooter:** added `testsupport/` test doubles — a fake
  `wifican.WifiCanRpc` gRPC daemon (`fake_wifican.py`) and a fake `adb` backed by a shared
  in-memory device (`fake_android.py`, `fake_adb.py`). New tests exercise the real code:
  `test_setup_integration.py` runs the install→uninstall flow through an actual `adb`
  subprocess, and `test_grpc.py` drives `ola.py` over the fake daemon. CI now installs
  `grpcio` and runs the full suite. See `docs/INSTALL_UNINSTALL.md`.

---

## [1.2.0] - 2026-11-08

### 🚗 Vehicle Projection Mods Added
* **Android Auto Support:**
  * Added automated 1-click installation and configuration for Android Auto wireless projection.
  * Automated ADB permission grants for Microphone (`RECORD_AUDIO`), Location (`ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`), Overlay (`SYSTEM_ALERT_WINDOW`), and Storage access.
* **Apple CarPlay Support (`OpenPlay`):**
  * Added official integration for Apple CarPlay wireless projection mod.
  * High-speed online stream-installation.
  * Direct "Open" and "Uninstall" controls provided on the App Manager dashboard.

### 🔮 Balls Navigation Update
* **Lockscreen Security Protection:**
  * Overlay automatically detects MoveOS lock and standby states, instantly hiding floating controls to prevent unauthorized touch interactions when the vehicle is parked.
* **Auto-Return to Home:**
  * Added intelligent auto-return timer to bring the primary MoveOS speedometer cluster to the front, ensuring rider safety while riding.
* **Native MoveOS App Drawer:**
  * Enhanced overlay menu with a dedicated native app drawer to quickly switch between installed mods (Music, Maps, Settings, CarPlay, Browser) directly from any screen.

### 🛡️ Safety & Usability
* **Side Stand Safety Notice:**
  * Added interactive post-install reminder popup and diagnostic log:
    > *"Important: Use mod apps with the scooter stand UP. Lowering the side stand triggers vehicle auto-lock."*
* **Install / Uninstall Confirmation Dialogs:**
  * Added safety confirmation prompts for all actions (Install, Uninstall, Custom Sideload) in App Manager to eliminate accidental clicks.
* **Direct App Launch ("Open" Button):**
  * Added an instant "Open" button next to "Uninstall" for all detected apps, allowing riders to launch any mod directly onto the scooter display over ADB.
* **Live Console Integration:**
  * Every in-app action (Download, ADB install, package removal, app launch, display wake, screenshot save) now streams live logs to the in-app Terminal console.
* **UI Polish:**
  * Changed setup trigger CTA button to **"Install Mod"**.
  * Removed duplicate console stream snippet from the bottom of Setup tab in favor of the dedicated full-screen Live Console.
  * Pruned redundant repository APK binaries in favor of direct CDN distribution.

---

## [1.1.0] - 2026-11-06

### Added
* **Live Head Unit RAM Telemetry:**
  * Real-time `/proc/meminfo` query over gRPC/ADB displaying Total RAM, Used RAM, and Free RAM in MB.
  * Dynamic color-coded status card (Green $\ge$ 200 MB, Orange 150–200 MB, Red $<$ 150 MB free memory).
* **Firefox Focus Web Browser:**
  * Integrated downloadable ARM64 Firefox Focus browser catalog with download progress streaming and background installation.
* **Custom APK Sideloading:**
  * Pick and install any local `.apk` file from phone storage directly onto the scooter display.
* **Zero-Clipping UI Layout:**
  * Restructured App Manager rows into modern vertical tiered cards preventing status badge truncation on smaller smartphone screens.

### Fixed
* Fixed premature dashboard redirect on multicast auto-scan; live gRPC handshake is now verified before transitioning to connected state.
* Removed redundant Scope ID input field in Manual Connection mode for cleaner IP/MAC connection.

---

## [1.0.0] - 2026-11-01

### Added
* Initial public open-source release of **S1Mods**.
* **Zero-PC Android Application (`S1Mods`):** Complete Kotlin Jetpack Compose companion app.
* **Automatic Discovery Engine:** Multicast IPv6 link-local and subnet scanner for MoveOS root diagnostics daemon on TCP port `50005`.
* **In-Memory RAM Bind Mount:** Safe, reversible ADB authorization over TCP port `5555` without modifying persistent flash partitions.
* **Balls Touch Navigation:** Bundled overlay providing Back, Home, and Settings touch controls on the dashboard.
* **Music Mod Player:** Lightweight ad-free streaming & local media playback.
* **Toolbox Suite:** Display screenshot capture, hardware specification inspection, and settings launcher.
* **Diagnostic Root Shell:** Interactive terminal to execute arbitrary diagnostic shell commands as `uid 0`.

