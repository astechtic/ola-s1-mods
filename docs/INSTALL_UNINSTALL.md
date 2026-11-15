# Install / uninstall flow

Installing and uninstalling a mod read the **same per-mod contract**, so they stay
symmetric: whatever install turns on, uninstall turns back off. The contract lives in the
`grants` block of each entry in [`apks/manifest.json`](../apks/manifest.json) (the
cross-tool source of truth) and is mirrored by `ModRegistry` in the Android app
(`android/app/src/main/java/com/yaaratech/s1mods/adb/ModSpec.kt`).

## The grant contract
Each mod declares:

| Field | Meaning |
| --- | --- |
| `launchActivity` | explicit launcher component to start after install (Balls only), else `null` |
| `accessibilityService` | accessibility service component to enable, else `null` |
| `appops` | app-ops to `allow` on install / reset to `default` on uninstall |
| `permissions` | runtime permissions to `pm grant` on install / `pm revoke` on uninstall |

## Install
1. **Verify** — the APK's SHA-256 is checked against `manifest.json`; a mismatch refuses the install.
2. **Install** — `pm install -r -d` (reinstall, keep data, allow downgrade).
3. **Grant** — `appops` → runtime `permissions` → accessibility service.
4. **Launch** — if the mod declares a `launchActivity` (Balls), start it so its one-time
   setup runs, then bring the MoveOS speedometer cluster back to the front.

### Accessibility is merge-safe (the important fix)
Enabling a service **reads the current `enabled_accessibility_services` list, adds ours if
absent, and writes it back** — it never overwrites the whole list. The old code did
`settings put secure enabled_accessibility_services <ours>`, which silently disabled any
other accessibility app the rider had enabled. Adding is idempotent.

## Uninstall (the exact inverse)
1. **Stop** — `am force-stop` so the uninstall is not racing a live process.
2. **Remove accessibility** — drop *our* service from the list (others are preserved); if
   the list becomes empty, set `accessibility_enabled 0`.
3. **Reset app-ops** — each granted op back to `default`.
4. **Revoke permissions** — each granted runtime permission.
5. **Uninstall** — `pm uninstall`.
6. Return the dashboard to the MoveOS HMI.

Every grant/revoke step is best-effort (one unsupported op cannot abort the rest).

## Where it runs
- **In-app (App Manager):** `ScooterManager.installSingleModApp` / `configureInstalledMod`
  (also used for the downloaded OpenPlay) and the symmetric `uninstallPackage`, over
  `AdbManager.grantMod` / `revokeMod`. The UI's existing install/uninstall buttons use these
  unchanged.
- **PC installer (`setup.py`):**
  ```bash
  python setup.py                 # install bundled mods + grant each contract
  python setup.py --uninstall     # revert grants, then remove every mod in the manifest
  python setup.py --uninstall com.yaaratech.ball com.yaaratech.musicmod   # specific mods
  ```
  Both paths share the same discover → connect → unlock-ADB steps first.

## Testing it without a scooter
The flow is tested on three levels, all without hardware (see also the
`android.permission` grant / `settings put secure` behaviour this relies on):

1. **Logic** — `test_flow.py`: merge-safe enable/disable, idempotency, grant/revoke symmetry
   (pure, monkeypatched ADB layer).
2. **ADB flow, end-to-end** — `test_setup_integration.py`: runs the *real* `setup.py`
   `grant_mod` / `uninstall_mods` through an actual `adb` subprocess against a fake device
   (`testsupport/fake_adb.py` + `fake_android.py`). Proves a real install→uninstall leaves a
   foreign accessibility service intact and removes the package cleanly.
3. **gRPC transport** — `test_grpc.py`: starts a fake `wifican.WifiCanRpc` daemon
   (`testsupport/fake_wifican.py`) on localhost and drives `ola.py`'s connect + command
   round-trip, verifying the hand-rolled protobuf wire format. Needs `grpcio`; skips without.

```bash
pip install pytest grpcio
pytest -q                     # runs all of the above
python testsupport/fake_wifican.py    # or run the fake daemon standalone, then:
python ola.py info --ipv6 ::1 --port <printed-port>
```

**With an emulator (optional, still no scooter):** the install/grant/uninstall half is plain
ADB, so an AVD exercises it for real — `adb install` a built mod, run the grant commands, and
check `adb shell settings get secure enabled_accessibility_services`. See `docs/BUILD.md`.
