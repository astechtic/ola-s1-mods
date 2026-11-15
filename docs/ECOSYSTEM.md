# The S1Mods ecosystem

A complete, open-source toolkit for modding an Ola S1 head unit (which runs Android under
Ola's MoveOS skin). Everything here is built from source and rebrandable; see
[`SAFETY.md`](SAFETY.md) for the non-destructive / OTA-safe design and
[`BUILD.md`](BUILD.md) for building it yourself.

## What's in the box

| Piece | What it is | Where |
| --- | --- | --- |
| **S1Mods app** (`com.yaaratech.s1mods`) | Zero-PC Android companion app: discover the scooter, unlock ADB, install mods, grant permissions, inspect the head unit, run a root shell | `android/` |
| **PC installer** (`setup.py`) | Same flow from a computer over Wi-Fi; `--uninstall` and `--revert` included | repo root |
| **`ola.py`** | Low-level CLI for the head unit's root gRPC channel (TCP 50005) | repo root |
| **Balls** (`com.yaaratech.ball`) | Floating Back/Home/Settings nav overlay — fork of QuickBall (GPL-3.0) | `mods/balls` |
| **Music Mod** (`com.yaaratech.musicmod`) | Ad-free music client (Rust/librespot core) — fork of Square (GPL-3.0) | `mods/music` |
| **Android Auto** (`com.yaaratech.androidauto`) | Wireless Android Auto receiver — fork of open-headunit (AGPL-3.0) | `mods/androidauto` |
| **OpenPlay** (`com.yaaratech.openplay`) | CarPlay-compatible projection receiver — fork of DiPlay (GPL-3.0) | `mods/openplay` |

## How it connects

```
   Phone (S1Mods app)  ──Wi-Fi / hotspot──►  Ola S1 head unit (Android + MoveOS)
        │                                            │
        │  gRPC  wifican.WifiCanRpc  (TCP 50005)     │  runs commands as root (uid 0)
        │  ───────────────────────────────────────► │  pm / am / settings / getprop …
        │                                            │
        │  ADB over TCP (5555), unlocked via an      │  installs the mod APKs into /data
        └─ in-RAM key bind-mount (reverts on reboot) ┘
```

The scooter is, in effect, "an Android device at an IP address." The app finds it over
link-local IPv6, talks to its root gRPC daemon, briefly unlocks ADB **in RAM** (nothing is
flashed), installs the mod APKs, and grants each mod exactly the permissions it needs.

## The app in both states

The app works the same whether or not a scooter is reachable — it just gates the vehicle
actions behind a live connection. The status pill (top-right) and the per-card state make the
mode obvious.

### 🔴 Not connected (offline)

You can browse everything, read the steps, and prepare — but vehicle actions wait for a link.

| Connect screen | Setup (offline) | App Manager (offline) |
| --- | --- | --- |
| ![Connect screen, not connected](images/connect-not-connected.png) | ![Setup tab, offline](images/setup-offline.png) | ![App Manager, not connected](images/apps-not-connected.png) |
| "Not connected", no address yet — **Auto Scan**, **Manual**, **Test**, or continue offline. | The pill reads **Offline**; the 5-step install flow (detect → unlock → install → grant → home) is shown but idle. | Live RAM reads "Not connected"; each mod shows its size and an **Install** button that waits for a connection. |

### 🟢 Connected

Once the handshake succeeds the pill turns **Connected** (green), the scooter is identified,
and every vehicle action lights up.

| Setup (connected) | App Manager (connected) | Toolbox (connected) |
| --- | --- | --- |
| ![Setup tab, connected](images/setup-connected.png) | ![App Manager, connected](images/apps-connected.png) | ![Toolbox, connected](images/toolbox-connected.png) |
| **Scooter found** — model + MoveOS version, with a one-tap **Connect / install** path. | **Head Unit Live RAM** now reads `/proc/meminfo`; **Install** actions are live. | Controls (Home / Settings), quick shortcuts (Wi-Fi, Bluetooth, Display…), device info, and a one-tap display **screenshot**. |

> The connected screenshots above were produced against the project's own fake
> `wifican` test daemon (see [`SAFETY.md`](SAFETY.md) and `testsupport/`), so the whole flow
> is demonstrable with no scooter. A real head unit shows the same UI with real values.

## Install / uninstall, safely

- **Install:** verify APK SHA-256 → `pm install` → grant app-ops / permissions / accessibility
  (merge-safe) → launch. See [`INSTALL_UNINSTALL.md`](INSTALL_UNINSTALL.md).
- **Uninstall:** the exact inverse — stop, revert grants, clean accessibility, then remove.
  The tool **refuses to touch MoveOS / system packages**.
- **Restore for OTA / handover:** `python setup.py --revert` puts MoveOS back to its captured
  stock state; a reboot clears the in-RAM ADB key. Nothing persistent is left behind.

## Build & verify

Every component builds from source and is covered by a device-free test suite
(`pytest`, 23 tests) plus CI. See [`BUILD.md`](BUILD.md) for the per-fork toolchain matrix and
[`../.github/workflows/`](../.github/workflows) for the build/sign/release pipeline.
