# Android Auto — recovery delta report

Recovered from `com.asjohn720.androidauto.apk` (manifest + resources + declared components).

## Identity
- applicationId: `com.asjohn720.androidauto`
- **internal package unchanged: `com.andrerinas.openheadunit`** (all code, activities,
  services still under this namespace — some locale labels still read "Open Headunit")
- versionName `4.0.0-beta2`, versionCode `122`
- minSdk 16, targetSdk 36
- app label: **Android Auto**

## This is essentially a rebrand, not a code fork
Only the `applicationId` and app label were changed; the entire codebase is open-headunit
`4.0.0-beta2`. Reconstruction is therefore: fork open-headunit at the matching version, set
`applicationId = "com.asjohn720.androidauto"`, set the label, build. Low effort.

## Declared components (open-headunit, unchanged)
Activities: `aap.AapProjectionActivity`, `app.UsbAttachedActivity`, `main.MainActivity`,
`main.SettingsActivity`, `main.OnboardingActivity`, `main.AutomationActivity`,
`connection.self.PermissionTrampolineActivity`.
Services: `aap.AapService`, `aap.DummyVpnService`, `location.GpsLocationService`,
`main.FloatingButtonService`.
Receivers: USB/auto-start/boot/carkey/automation/screen-off. Providers: Shizuku, FileProvider.

## Permissions of note / trim candidates
Declares, among many: `READ_LOGS` (maxSdk 32), `ACCESS_SUPERUSER`,
`moe.shizuku.manager.permission.API_V23` (Shizuku), full Bluetooth, mic, location, storage.
`READ_LOGS`/`ACCESS_SUPERUSER`/Shizuku are **upstream features** (self-mode/privileged
start), not S1 additions — decide per build whether S1 needs them;
`AdbManager.grantAndroidAutoPermissions()` currently grants mic/location/overlay/storage/BT.

## Reconstruction TODO
- [ ] `git subtree add --prefix mods/androidauto https://github.com/andreknieriem/open-headunit v4.0.0-beta2` (confirm exact tag)
- [ ] set `applicationId "com.asjohn720.androidauto"`, label "Android Auto"
- [ ] (optional) trim `READ_LOGS`/`ACCESS_SUPERUSER`/Shizuku if S1 projection doesn't use them
- [ ] AGPL-3.0: ensure published source corresponds to the shipped build
- [ ] release signing; build; verify on S1; record SHA-256
