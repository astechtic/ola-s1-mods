# Building S1Mods from source

## S1Mods companion app (`android/`)

```bash
cd android
./gradlew assembleRelease     # output: app/build/outputs/apk/release/app-release.apk
```

### Mod APKs
The APKs S1Mods installs live in the top-level [`apks/`](../apks) directory (the single
source of truth, described by [`apks/manifest.json`](../apks/manifest.json)). A Gradle task
(`syncModApks`) copies the bundled ones into a generated assets dir at build time, so they
are **not** committed under `src/main/assets`. If an APK is missing, the build fails with a
clear message naming the expected path.

### Release signing
Release builds use a keystore read from `android/keystore.properties` (git-ignored) or from
CI environment variables. Without either, the build falls back to the **debug** key and logs
a warning — usable for local testing, **not** for distribution.

1. Create a keystore once:
   ```bash
   keytool -genkeypair -v -keystore android/s1mods-release.jks \
     -alias s1mods -keyalg RSA -keysize 2048 -validity 10000
   ```
2. `cp android/keystore.properties.sample android/keystore.properties` and fill it in.
   `storeFile` is resolved relative to `android/` (or use an absolute path).
3. In CI, provide instead: `S1MODS_KEYSTORE_FILE`, `S1MODS_KEYSTORE_PASSWORD`,
   `S1MODS_KEY_ALIAS`, `S1MODS_KEY_PASSWORD`.

Verify the signer:
```bash
$ANDROID_HOME/build-tools/<ver>/apksigner verify --print-certs app-release.apk
```

## Mod apps (`mods/`)
Each `mods/<x>` is a standalone Gradle project vendored from its open-source upstream (via
`git subtree --squash`) and rebranded to its S1 `applicationId`. All four build **from
source** and were verified to produce an exact identity match (package / version / launcher /
label) to the shipped APK. See each `mods/<x>/S1_RECOVERY.md` for the reconstruction record.

### Verified build matrix
Each fork pins its own Gradle wrapper and toolchain; they differ, so build each in its own
directory with the matching JDK/NDK. These are the exact combinations that built green:

| Fork | Module / task | Gradle | JDK | NDK / native | Extra toolchain |
| --- | --- | --- | --- | --- | --- |
| `balls` (QuickBall) | `:app:assembleFossRelease` | 9.4.1 | 25 | — | pick the **foss** flavor (not `play`) |
| `openplay` (DiPlay) | `:mobile:assembleRelease` | 9.5.0 (wrapper) | 25 | NDK via `:shared` (ndkBuild) | — |
| `music` (Square) | `:app:assembleRelease` | 9.4.1¹ | 25 | NDK `28.2.13676358` | `cargo install cargo-ndk` + `rustup target add aarch64-linux-android armv7-linux-androideabi` |
| `androidauto` (open-headunit) | `:app:assembleGithubRelease` | 8.14.x² | **21**³ | NDK `29.0.14206865`, CMake `3.22.1` | Shizuku AIDL (built-in); use the **github** flavor |

¹ Square's wrapper pins 9.3.0; AGP 8.13.2 is incompatible with Gradle 9.6 (removed internal
API), so build with 9.3–9.5 (9.4.1 verified). ² open-headunit's wrapper pins 8.14.4; do
**not** use Gradle 9.x — it removes the `archivesBaseName` property the build sets. ³ JDK 25
fails open-headunit's Gradle 8.14 with a bare version-string error; use JDK 21 (or 17).

### Release signing (per fork)
Each upstream already supports a keystore-from-config pattern (no S1-specific shim added):

| Fork | Keystore source |
| --- | --- |
| `balls` | `keystore.properties` beside the project (debug-key fallback if absent) |
| `openplay` | env: `ANDROID_KEYSTORE_PATH`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` (fails cleanly if unset — no debug fallback) |
| `music` | `keystore.properties` beside the project (debug-key fallback if absent) |
| `androidauto` | `key.properties` / `secrets.properties` / `HEADUNIT_KEYSTORE_*` env (upstream also ships a `keystore.jkc` — **do not** use it for releases) |

Rebuilt APKs are **functionally equivalent, not byte-identical** to the originals (new build
env + new signing key); installing one over an existing copy requires an uninstall first.

## Continuous integration (`.github/workflows/`)
[`release.yml`](../.github/workflows/release.yml) builds the S1Mods app and all four mods on
a version tag, signs each from CI secrets, writes `SHA256SUMS`, attaches everything to a
GitHub Release, and attests build provenance. [`ci.yml`](../.github/workflows/ci.yml) runs
the Python test suite (`pytest`) on every push/PR. The mod signing secrets map to the table
above; see the workflow comments for the exact secret names.
