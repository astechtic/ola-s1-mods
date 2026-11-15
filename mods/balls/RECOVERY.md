# Balls — recovery delta report

Recovered from `balls-1.1.0-lite-release.apk` (manifest + resources + declared components).
The release APK is R8/ProGuard-obfuscated, so business logic was **not** recoverable as
source; reconstruct from QuickBall upstream and re-apply the deltas below.

## Identity
- applicationId: `com.asjohn720.ball`   (upstream QuickBall: `io.github.chayanforyou.quickball`)
- versionName `1.1.0-lite`, versionCode `2`
- minSdk 21, targetSdk 37
- app label: **Balls**

## This is a substantive fork
Unlike the other mods, Balls has a reorganized first-party package tree
`com.asjohn720.ball.{core,domain.models,ui,ui.floating}` — the internal package was renamed
and restructured from upstream. Treat QuickBall as the base, not a drop-in rebrand.

## Declared components (must exist after reconstruction)
- `com.asjohn720.ball.ui.MainActivity` — launcher; S1Mods launches it via
  `am start -n com.asjohn720.ball/.ui.MainActivity` (see `AdbManager.grantBallPermissions`).
- `com.asjohn720.ball.core.QuickBallService` — accessibility service; S1Mods enables it via
  `settings put secure enabled_accessibility_services com.asjohn720.ball/com.asjohn720.ball.core.QuickBallService`.
- `com.asjohn720.ball.core.QuickBallCommandReceiver` — **not in upstream**; broadcast entry
  for external/ADB-driven control. Recreate.

## Permissions (from manifest)
`SYSTEM_ALERT_WINDOW`, `BIND_ACCESSIBILITY_SERVICE`, `WRITE_SETTINGS`, `VIBRATE`,
`CHANGE_WIFI_STATE`, `ACCESS_WIFI_STATE`, `BLUETOOTH`, `BLUETOOTH_ADMIN`,
`ACCESS_NOTIFICATION_POLICY`, `QUERY_ALL_PACKAGES`, `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`.

## S1-specific features to re-implement (from CHANGELOG 1.2 + behavior)
- Floating **Back / Home / Settings** nav buttons for the MoveOS HMI.
- Lockscreen/standby auto-hide of the overlay (hide controls when vehicle parked/locked).
- Auto-return timer that brings the MoveOS speedometer cluster (`com.olaelectric.hmiclient`) back to front.
- Native app drawer to switch between installed mods (Music, Maps, Settings, CarPlay, Browser).

## Reconstruction TODO
- [ ] `git subtree add --prefix mods/balls https://github.com/chayanforyou/QuickBall <tag>`
- [ ] rename internal package → `com.asjohn720.ball`, restructure to match tree above
- [ ] re-implement the four S1 features + `QuickBallCommandReceiver`
- [ ] release signing via `keystore.properties`; build; verify on S1; record SHA-256
