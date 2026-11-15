# Music Mod — S1 fork notes (reconstruction record)

This directory is **Square v2.8.0** ([Lelonio/Square](https://github.com/Lelonio/Square),
an ad-free Spotify / YouTube-Music client with a Rust (librespot) native core,
GPL-3.0-or-later; the lyrics file is AGPL-3.0), vendored via `git subtree --squash`, then
rebranded to the S1 app.

## Confirmed: Music Mod == applicationId-rebranded Square
The shipped `musicmod-release.apk` decompiled to:

| Field | Shipped APK | Square v2.8.0 upstream |
| --- | --- | --- |
| applicationId | `com.yaaratech.musicmod` | `dev.lelonio.square` |
| versionCode / Name | `62` / `2.8.0` | `62` / `2.8.0` (**same**) |
| code namespace | `dev.lelonio.square` | `dev.lelonio.square` (**same**) |
| launcher | `dev.lelonio.square.ui.MainActivity` | `dev.lelonio.square.ui.MainActivity` (**same**) |
| label | `Music Mod` | `Square` |

Same namespace, launcher and version → Music Mod is an **applicationId/label rebrand of
Square v2.8.0**, nothing more.

## Rebrand applied in this repo (vs upstream)
- `applicationId`: `dev.lelonio.square` → **`com.yaaratech.musicmod`** (`app/build.gradle.kts`).
  `namespace` stays `dev.lelonio.square` (as the shipped APK proves).
- `app_name` string → **"Music Mod"** (`app/src/main/res/values/strings.xml`).
- Version unchanged (already 62 / 2.8.0).

## Build: VERIFIED ✅ (compiles, Rust native core, signs)
Module `:app`. Builds with Gradle **9.4.1** (AGP 8.13.2 needs Gradle 9.3–9.5; it is
incompatible with 9.6's removed internal API — the project wrapper pins 9.3.0).
`:app:assembleRelease` → `com.yaaratech.musicmod`, 62 / 2.8.0, label **Music Mod**, launcher
`dev.lelonio.square.ui.MainActivity` — an exact match to the shipped APK. Output: per-ABI
APKs (`arm64-v8a`, `armeabi-v7a`) plus a universal APK.

### Native toolchain (one-time)
The native core is Rust built through `cargo-ndk`:
- NDK `28.2.13676358` (pinned in `app/build.gradle.kts`).
- `cargo install cargo-ndk`.
- `rustup target add aarch64-linux-android armv7-linux-androideabi` (one per shipped ABI;
  the build fails with "can't find crate for `std`" if a target's std is missing).

### Signing
Upstream reads `keystore.properties` beside the project and **falls back to the debug key**
when absent (fine for running, not for distribution) — same pattern as `android/`. For a
real signed build, drop a `keystore.properties` (git-ignored) or wire CI secrets, then
`:app:assembleRelease`.

## Content/legal note (document, user's decision)
Square is an **unofficial Spotify / YouTube-Music client**. Redistributing it carries
Spotify/YouTube ToS exposure that is independent of the GPL-3.0-or-later code license. The
decision to ship it is the user's; the AGPL-3.0 exception on the lyrics file must be
preserved.

## License
GPL-3.0-or-later (upstream `LICENSE` retained); lyrics file AGPL-3.0. Preserve Square
copyright headers.
