# Music Mod — recovery delta report

Recovered from `musicmod-release.apk` (manifest + resources + declared components).

## Identity
- applicationId: `com.asjohn720.musicmod`
- **internal package unchanged: `dev.lelonio.square`** (all code still under this namespace)
- versionName `2.8.0`, versionCode `62`
- minSdk 26, targetSdk 35
- app label: **Music Mod**

## This is a rebrand, not a code fork
Only `applicationId` and label changed; the codebase is Square `2.8.0`. Reconstruction:
fork Square at the matching version, set `applicationId = "com.asjohn720.musicmod"` and the
label, build.

## Declared components (Square, unchanged)
Activities: `playback.websdk.WebSdkActivity`, `ui.MainActivity`.
Services: `playback.websdk.WebSdkService`, `download.DownloadService`, `auth.LoginKeepAlive`,
`playback.PlaybackService`.
Receivers/providers: `widget.SquareWidget` (+ `$Tile`), media3 MediaButtonReceiver, FileProvider.

## License note
Square is GPL-3.0-or-later **except** its lyrics view, ported from Spicy Lyrics and licensed
AGPL-3.0 (combined per section 13). Preserve that file's AGPL header; `mods/music/LICENSE`
is GPL-3.0, add an AGPL note for the lyrics file.

## Content/legal note (document, user's decision)
Square is an **unofficial client for Spotify Premium / YouTube Music**. Redistributing it may
conflict with those services' terms independent of the open-source license. Flag in docs.

## Reconstruction TODO
- [ ] `git subtree add --prefix mods/music https://github.com/Lelonio/Square <tag for 2.8.0>`
- [ ] set `applicationId "com.asjohn720.musicmod"`, label "Music Mod"
- [ ] keep AGPL-3.0 lyrics-file exception intact
- [ ] release signing; build; verify on S1; record SHA-256
