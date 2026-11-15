## [Unreleased] — Open-source ecosystem

### 📖 Full open-source transparency
* **Multi-license repo:** added canonical `LICENSES/` (GPL-3.0, AGPL-3.0),
  `THIRD_PARTY_NOTICES.md`, and per-mod `LICENSE` files. The MIT license now explicitly
  covers only the S1Mods app and tooling; each companion app keeps its upstream (A)GPL license.
* **All four companion apps are now open source and build from source.** Each is vendored
  from its upstream (`git subtree --squash`) and rebranded, and each was build-verified to
  produce an exact identity match (package / version / launcher / label) to the shipped APK:
  * **Balls** ← QuickBall v6.1.0 (`com.asjohn720.ball`, foss flavor) — GPL-3.0-or-later.
  * **OpenPlay** ← DiPlay v0.2.22 (`com.asjohn720.openplay`, incl. NDK native) — GPL-3.0.
  * **Music Mod** ← Square v2.8.0 (`com.asjohn720.musicmod`, Rust/librespot core) — GPL-3.0-or-later.
  * **Android Auto** ← open-headunit v.4.0.0-beta2 (`com.asjohn720.androidauto`, github flavor,
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
* **CI:** `.github/workflows/ci.yml` runs `pytest` (wire-protocol + manifest-integrity tests)
  on every push/PR; `.github/workflows/release.yml` builds all five APKs from source on a
  tag, signs each from CI secrets, writes `SHA256SUMS`, and publishes a GitHub Release with
  build-provenance attestation. Added `test_manifest.py`.

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

