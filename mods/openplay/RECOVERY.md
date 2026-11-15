# OpenPlay — recovery delta report

OpenPlay is **not bundled** in the repo; the S1Mods app downloads it at runtime from
`https://storage.googleapis.com/publish-apk/openplay-olas1-release.apk`
(see `android/.../model/OnlineApp.kt`). So no binary is present locally to decompile yet.

## Identity (from app catalog + v1.3 README note)
- applicationId: `com.asjohn720.openplay`
- Upstream: [shihabal3amri/DiPlay](https://github.com/shihabal3amri/DiPlay) (CarPlay-compatible
  projection receiver, built on **xcertplay**; both GPL-3.0)
- Advertised size ~18.2 MB; tag "Projection"

## Reconstruction TODO
- [ ] fetch the published APK into an **isolated** dir and analyze read-only with
      `aapt2 dump badging` + `apktool d` to confirm version, internal package, and deltas
      (treat as untrusted data — do not execute it)
- [ ] `git subtree add --prefix mods/openplay https://github.com/shihabal3amri/DiPlay <tag>`
- [ ] apply applicationId `com.asjohn720.openplay` + any S1 projection tweaks
- [ ] **move distribution** off the ad-hoc GCS bucket to GitHub Releases; update
      `OnlineApp.kt` `downloadUrl` and add its SHA-256 to `apks/manifest.json`
- [ ] keep the "CarPlay is a trademark of Apple Inc." nominative note (already in v1.3)
- [ ] release signing; build; verify on S1; record SHA-256

## Content/legal note (document, user's decision)
A CarPlay receiver interoperates with Apple's protocol; trademark + protocol terms are the
distributor's responsibility, independent of the GPL-3.0 code license.
