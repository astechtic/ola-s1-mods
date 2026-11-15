# Android Auto — S1 fork notes (reconstruction record)

This directory is **open-headunit v.4.0.0-beta2**
([andreknieriem/open-headunit](https://github.com/andreknieriem/open-headunit), a wireless
Android Auto head-unit receiver with a C++/NDK core, AGPL-3.0), vendored via
`git subtree --squash`, then rebranded to the S1 app.

## Confirmed: Android Auto == applicationId-rebranded open-headunit
The shipped `com.asjohn720.androidauto.apk` decompiled to:

| Field | Shipped APK | open-headunit v.4.0.0-beta2 upstream |
| --- | --- | --- |
| applicationId | `com.asjohn720.androidauto` | `com.andrerinas.headunitrevived` |
| versionCode / Name | `122` / `4.0.0-beta2` | `122` / `4.0.0-beta2` (**same**) |
| code namespace | `com.andrerinas.openheadunit` | `com.andrerinas.openheadunit` (**same**) |
| launcher | `com.andrerinas.openheadunit.main.MainActivity` | `com.andrerinas.openheadunit.main.MainActivity` (**same**) |
| label | `Android Auto` | `Open Headunit` |

Same namespace, launcher and version → Android Auto is an **applicationId/label rebrand of
open-headunit v.4.0.0-beta2**. (Upstream deliberately keeps `applicationId` ≠ `namespace`,
so only the applicationId and label change here.)

## Rebrand applied in this repo (vs upstream)
- `applicationId`: `com.andrerinas.headunitrevived` → **`com.asjohn720.androidauto`**
  (`app/build.gradle.kts`). `namespace` stays `com.andrerinas.openheadunit`.
- `title` + `app_name` strings → **"Android Auto"** (`app/src/main/res/values/strings.xml`;
  the launcher inherits the application `android:label="@string/title"`).
- Version unchanged (already 122 / 4.0.0-beta2).

## Build: VERIFIED ✅ (compiles, C++/AIDL/NDK, signs) — use the `github` flavor
Module `:app`, two product flavors on the `distribution` dimension: **`github`** (FOSS,
the one to ship) and `playstore`. Build with **Gradle 8.14.x** (the wrapper pins 8.14.4;
AGP 8.13.2) on **JDK 21** (JDK 25 fails this Gradle with a bare version string; Gradle 9.x
removes the `archivesBaseName` property the build sets, so do not use 9.x here).
- `:app:assembleGithubDebug` → full APK (C++ `src/main/cpp` + Shizuku AIDL all compile).
- `:app:assembleGithubRelease` with a release keystore → **`com.asjohn720.androidauto`**,
  122 / 4.0.0-beta2, label **Android Auto**, launcher
  `com.andrerinas.openheadunit.main.MainActivity` — an exact match to the shipped APK. The
  APK is named `com.asjohn720.androidauto_4.0.0-beta2.apk` (upstream sets
  `archivesBaseName = applicationId_versionName`).

### Native toolchain (one-time)
- NDK `29.0.14206865` (pinned in `app/build.gradle.kts`); CMake `3.22.1`.

### Signing
Upstream's release config reads `key.properties` (git-ignored) / `secrets.properties` /
`HEADUNIT_KEYSTORE_*` env vars — compatible with the CI-secret approach in `docs/BUILD.md`.
Set those (locally or in CI) and run `:app:assembleGithubRelease`.

### ⚠️ Upstream ships a `keystore.jkc`
open-headunit commits a `keystore.jkc` into its own repository, so it arrived here with the
faithful subtree. **Our signing never uses it** — the `release` signingConfig requires
`key.properties`/`secrets.properties`/env, and the `debug` reference to it is commented out.
It is upstream's published artifact, not a credential this fork relies on; treat it as such
and never point a release build at it.

## Permissions note (optional future trim; document)
The projection app declares broad permissions seen in the shipped APK (e.g. `READ_LOGS`,
superuser/Shizuku paths). The S1Mods installer's `AdbManager.grantAndroidAutoPermissions()`
grants the runtime set it actually needs (mic, location, overlay, storage). Trimming the
unused manifest permissions is an optional hardening step, not required for parity.

## Content/legal note (document, user's decision)
"Android Auto" is a Google trademark; this is an independent, interoperable receiver, not a
Google product. AGPL-3.0's network-use clause requires the **published source to correspond
to the shipped build** — this vendored tree + the recorded rebrand satisfy that.

## License
AGPL-3.0 (upstream `LICENSE` retained). Preserve open-headunit copyright headers, including
`COPYRIGHT_MICHAEL_REID_GPLv3AFFERO.txt`.
