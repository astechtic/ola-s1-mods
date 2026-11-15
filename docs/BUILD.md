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
Each `mods/<x>` is (once its upstream source is vendored) a standalone Gradle project built
the same way, with its own `keystore.properties`. See each `mods/<x>/README.md` and
`RECOVERY.md`. Rebuilt APKs are placed in `apks/` and their SHA-256 recorded in
`apks/manifest.json`.
