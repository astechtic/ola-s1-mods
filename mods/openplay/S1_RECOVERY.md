# OpenPlay — S1 fork notes (reconstruction record)

This directory is **DiPlay v0.2.22** ([shihabal3amri/DiPlay](https://github.com/shihabal3amri/DiPlay),
a CarPlay-compatible projection receiver built on **xcertplay**, GPL-3.0), vendored via
`git subtree --squash`, then rebranded to the S1 app.

## Confirmed: OpenPlay == applicationId-rebranded DiPlay
The shipped `openplay-olas1-release.apk` (downloaded from the GCS bucket for analysis,
treated as untrusted data) decompiled to:

| Field | Shipped APK | DiPlay v0.2.22 upstream |
| --- | --- | --- |
| applicationId | `com.yaaratech.openplay` | `com.shihab.diplay` |
| versionCode | `42` | `41` (**+1**) |
| versionName | `1.0.1` | `0.2.22` |
| code namespace | `com.shilapi.xcertplay` | `com.shilapi.xcertplay` (**same**) |
| launcher | `com.shilapi.xcertplay.DiPlayActivity` | `com.shilapi.xcertplay.DiPlayActivity` (**same**) |
| label | `OpenPlay` | `DiPlay` |

The code namespace and launcher activity are identical, and the versionCode is exactly
upstream + 1. So OpenPlay is an **applicationId/branding rebrand of DiPlay v0.2.22**, not a
code fork.

## Rebrand applied in this repo (vs upstream)
- `applicationId`: `com.shihab.diplay` → **`com.yaaratech.openplay`** (`mobile/build.gradle.kts`).
  `namespace` stays `com.shilapi.xcertplay` (as the shipped APK proves).
- `versionCode` 41 → **42**, `versionName` "0.2.22" → **"1.0.1"** (match the shipped build).
- `app_name` string → **"OpenPlay"** (all locale `strings.xml` in `mobile/` and `common/`).

## Build: VERIFIED ✅ (compiles, native builds, signs)
Built with the vendored Gradle wrapper (9.5.0; a cached 9.6.0 was used locally due to a
sandbox download block — behaviour is identical). Module `:mobile` is the app.
- `:mobile:assembleDebug` → full APK (debug variant carries upstream's `.hudtest`
  applicationIdSuffix + "DiPlay HUD Test" label — a debug-only source set).
- `:mobile:assembleRelease` with a release keystore → **`com.yaaratech.openplay`**,
  versionCode 42, versionName 1.0.1, label **OpenPlay**, launcher
  `com.shilapi.xcertplay.DiPlayActivity` — an exact match to the shipped APK. The
  `:shared` NDK native libs (arm64-v8a, armeabi-v7a, x86, x86_64) build from source too.

### Signing
Upstream already reads a release keystore from env vars
(`ANDROID_KEYSTORE_PATH` / `ANDROID_KEYSTORE_PASSWORD` / `ANDROID_KEY_ALIAS` /
`ANDROID_KEY_PASSWORD`), which matches the CI-secret approach in `docs/BUILD.md`. No
`keystore.properties` shim is needed; set those four vars (locally or in CI) and run
`:mobile:assembleRelease`. With no keystore, the build fails cleanly at
`validateSigningRelease` (never falls back to a debug key).

## CarPlay authentication — intentionally NOT shipped
DiPlay's `mobile/build.gradle.kts` keeps ordinary source/CI builds **identity-free**: the
Apple MFi accessory credentials (`identity.pk8`, `certificate.p7b`) are only injected via
`DIPLAY_AUTH_ASSETS_DIR` for a *standalone car-test* APK, and a `rejectBundledCredentials`
task refuses any stray credential files in assets. Our open-source build is the identity-free
source build — correct both legally (the MFi assets are Apple's, not ours to redistribute)
and per the project's "functional equivalence, not bit-identity" principle.

## Distribution
OpenPlay is **downloaded** at runtime (not bundled, to keep the app APK small) from this
repo's own GitHub Release — a from-source `com.yaaratech.openplay` build hosted at
`.../releases/download/v1.0.0/openplay-olas1-release.apk`. `apks/manifest.json` and the app's
`OnlineApp` catalog pin its SHA-256, so `setup.py` / `ApkDownloader` verify it before install.
(It originally came from a third-party GCS bucket serving the pre-rebrand build; that
dependency is now gone.)

## Content/legal note (document, user's decision)
A CarPlay receiver interoperates with Apple's protocol; trademark ("CarPlay is a trademark of
Apple Inc." — nominative use) and protocol terms are the distributor's responsibility,
independent of the GPL-3.0 code license.

## License
GPL-3.0 (upstream `LICENSE` retained). Preserve DiPlay / xcertplay copyright headers.
