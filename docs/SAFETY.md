# Safety, MoveOS integrity & OTA compatibility

This toolkit side-loads open-source apps onto an Ola S1 head unit (which runs Android under
Ola's MoveOS skin). It is designed to be **non-destructive, reversible, and scoped to the
owner's own vehicle**. This document states exactly what it does and does not touch, how it
stays compatible with MoveOS and Ola's OTA updates, and the limits of responsible use.

## 1. What it changes — and how long each change lasts

| Change | Where | Persists? | How it's undone |
| --- | --- | --- | --- |
| ADB key **bind-mount** (`mount --bind` of your key into `/data/misc/adb/…`) | RAM | **No** — a reboot clears it | Reboot; or **phone app → Health → Restore stock state**, or `setup.py --revert`, removes the key file |
| `persist.ola.security.scootermode` set to `serv` (to enable ADB) | property store | **Yes** (survives reboot) | **Captured before change** (phone *and* PC); restored by **phone app → Health → Restore stock state** or `setup.py --revert` to the exact stock value |
| Installed mod **APKs** (`com.yaaratech.*`) | `/data` (user apps) | Yes, like any app | `setup.py --uninstall` (reverts grants, then removes) |
| Per-app **appops / runtime permissions** on the mods | per-app | Yes | Reverted on uninstall (reset to default / revoked) |
| `enabled_accessibility_services` (Balls only) | secure settings | Yes | Merge-safe add on install; **merge-safe remove** on uninstall (never clobbers other apps) |

**The system/boot/vendor partitions are never written.** No flashing, no `/system`
modification, no bootloader changes, no persistent daemons installed. Everything lives in
`/data` or in volatile RAM.

## 2. MoveOS is never modified

- The tool **reads** MoveOS state (e.g. launches `com.olaelectric.hmiclient` to return to the
  dashboard) but never installs, replaces, disables, or re-signs any Ola/MoveOS app.
- **Hard guardrail:** every destructive package action refuses MoveOS / Ola / Android system
  packages. `setup.py --uninstall` only acts on packages declared in `apks/manifest.json`;
  the Android app's `ScooterManager.uninstallPackage` refuses anything matching
  `com.olaelectric*`, `com.ola.*`, `android`, `com.android.*`, `com.google.android.*`,
  `com.qualcomm.*`, and similar. A typo or bad argument cannot remove a vehicle app.
  (Covered by tests: `test_refuses_to_uninstall_moveos_system_package`.)
- The mods are ordinary overlay / media / projection apps. Balls auto-hides on lock/standby
  so it cannot intercept touches while the vehicle is parked or locked.

## 3. Ola OTA updates keep working

Ola OTA updates flash the **system** side of the device. This toolkit only writes `/data` and
volatile RAM, so an OTA has nothing of ours to conflict with:

- **Mod APKs** are user apps in `/data`; a system OTA leaves them alone (an OTA may reasonably
  clear user apps, which is fine — they reinstall).
- The **ADB key bind-mount** is gone after any reboot (an OTA reboots), so it never persists
  into an update.
- The **one persistent property** (`scootermode`) is the only thing that could matter to an
  update flow. Before an OTA or a handover, revert it either way:

  **From the phone (v1.1.1+):** open **S1Mods → Health tab → Restore stock state (safe for
  OTA)**, then reboot the scooter. The app captured the stock value *before* the first unlock,
  so it is restored exactly, and the temporary ADB key files are removed.

  **From a PC:**

  ```bash
  python setup.py --revert         # restore the captured stock scootermode + remove the key
  # then reboot the scooter        # clears the RAM key bind-mount, ADB re-locks
  ```

  Both restore the **exact value captured** before unlock (the phone saves it in app storage,
  the PC in `~/.ola_s1_state.json`), so MoveOS sees precisely its original state. Neither
  guesses a security value it didn't capture.

To go fully back to stock: uninstall the mods (phone **Health → Remove**, or
`python setup.py --uninstall`), run the revert above, then reboot.

## 4. Not harmful — scope and responsible use

- **Owner-only, local-only.** The tool talks to a scooter on the same Wi-Fi/hotspot over
  link-local IPv6. It is for modding **your own** vehicle. It is not a remote exploit and
  targets nothing but the device you point it at.
- **No data exfiltration.** It sends nothing about you or the vehicle to third parties. APKs
  are verified by SHA-256 against `apks/manifest.json` before install; the in-app downloader
  verifies hashes too.
- **Integrity before install.** A hash mismatch refuses the install, so a tampered or
  man-in-the-middled APK is never put on the vehicle.
- **Rider safety.** Use mods with the side-stand **up**; lowering it triggers MoveOS
  auto-lock. Do not interact with the head unit while riding. These apps are for use while
  parked/stationary.

### Things the user must weigh (documented, not blockers)
- **Warranty / terms:** enabling diagnostic ADB and side-loading apps may be outside Ola's
  terms — specifically Ola's warranty exclusion of *"Control Units or software used in vehicle
  which are not designed or approved by the company"* (T&C 6.8). It's a practical risk at Ola's
  discretion, the tool is reversible (restore stock before service), and the decision is the
  owner's. Full grounded analysis with Ola's exact wording and sources: **[WARRANTY.md](WARRANTY.md)**.
- **Upstream app ToS:** Music Mod (a Spotify/YouTube-Music client) and OpenPlay/Android Auto
  (projection receivers) carry their own third-party terms and trademark considerations,
  independent of this toolkit's licensing. See `THIRD_PARTY_NOTICES.md`.
- **Upgrade over an older build:** a `com.yaaratech.*` mod will not install over a previously
  installed `com.asjohn720.*` (or other-id) build of the same fork — Android blocks the shared
  custom permission. Uninstall the old build first.

## 5. If something seems off
Reboot the scooter — that alone clears the ADB key bind-mount and returns the device to a
normal boot. Then restore the stock `scootermode` from the **phone app (Health → Restore stock
state)** or `python setup.py --revert`. Nothing this tool does requires reflashing to recover.
