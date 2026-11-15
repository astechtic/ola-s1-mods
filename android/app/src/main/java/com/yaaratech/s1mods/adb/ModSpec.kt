package com.yaaratech.s1mods.adb

/**
 * The install/uninstall contract for one mod: what to grant when it goes on, and
 * therefore what to undo when it comes off. Install and uninstall read the *same*
 * spec, so they stay symmetric — anything install turns on, uninstall turns back off.
 *
 * This mirrors the `grants` block of each entry in `apks/manifest.json` (the
 * cross-tool source of truth that `setup.py` reads). Keep the two in sync.
 */
data class ModSpec(
    val packageName: String,
    /** Human-readable name shown in the Health dashboard. */
    val displayName: String,
    /** Explicit launcher component (`pkg/.Activity`), or null to launch via monkey. */
    val launchActivity: String? = null,
    /** Accessibility service component to enable, or null if the mod has none. */
    val accessibilityService: String? = null,
    /** appops to `allow` on install and reset to `default` on uninstall. */
    val appops: List<String> = emptyList(),
    /** Runtime permissions to `pm grant` on install and `pm revoke` on uninstall. */
    val permissions: List<String> = emptyList(),
    /** Bundled asset filename (installable offline), or null for download-only mods. */
    val assetFileName: String? = null,
    /** Latest shipped versionName per the manifest (for update detection). */
    val expectedVersionName: String? = null,
    /** Latest shipped versionCode per the manifest (for update detection). */
    val expectedVersionCode: Long? = null,
) {
    /** True when the mod can be (re)installed offline from bundled assets. */
    val isBundled: Boolean get() = assetFileName != null
}

/**
 * The known mods. Looked up by package name so both the bundled [ModApp]s and the
 * downloaded ones (OpenPlay) resolve to the same install/uninstall behaviour.
 *
 * Versions mirror `apks/manifest.json`; bump them here when the manifest bumps so the
 * Health dashboard can flag an out-of-date mod on the vehicle.
 */
object ModRegistry {
    val specs: List<ModSpec> = listOf(
        ModSpec(
            packageName = "com.yaaratech.ball",
            displayName = "Balls Navigation",
            launchActivity = "com.yaaratech.ball/.ui.MainActivity",
            accessibilityService = "com.yaaratech.ball/com.yaaratech.ball.core.QuickBallService",
            appops = listOf("SYSTEM_ALERT_WINDOW", "WRITE_SETTINGS"),
            assetFileName = "balls-release.apk",
            expectedVersionName = "6.1.0",
            expectedVersionCode = 25,
        ),
        ModSpec(
            packageName = "com.yaaratech.androidauto",
            displayName = "Android Auto",
            appops = listOf("SYSTEM_ALERT_WINDOW", "WRITE_SETTINGS", "MANAGE_EXTERNAL_STORAGE"),
            permissions = listOf(
                "android.permission.RECORD_AUDIO",
                "android.permission.ACCESS_FINE_LOCATION",
                "android.permission.ACCESS_COARSE_LOCATION",
                "android.permission.READ_EXTERNAL_STORAGE",
                "android.permission.WRITE_EXTERNAL_STORAGE",
                "android.permission.NEARBY_WIFI_DEVICES",
                "android.permission.BLUETOOTH_CONNECT",
                "android.permission.BLUETOOTH_SCAN",
            ),
            assetFileName = "com.yaaratech.androidauto.apk",
            expectedVersionName = "4.0.0-beta2",
            expectedVersionCode = 122,
        ),
        ModSpec(
            packageName = "com.yaaratech.musicmod",
            displayName = "Music Mod",
            permissions = listOf("android.permission.READ_EXTERNAL_STORAGE"),
            assetFileName = "musicmod-release.apk",
            expectedVersionName = "2.8.0",
            expectedVersionCode = 62,
        ),
        ModSpec(
            packageName = "com.yaaratech.openplay",
            displayName = "OpenPlay",
            appops = listOf("SYSTEM_ALERT_WINDOW", "WRITE_SETTINGS", "GET_USAGE_STATS"),
            permissions = listOf(
                "android.permission.RECORD_AUDIO",
                "android.permission.ACCESS_FINE_LOCATION",
                "android.permission.ACCESS_COARSE_LOCATION",
                "android.permission.NEARBY_WIFI_DEVICES",
                "android.permission.BLUETOOTH_CONNECT",
            ),
            // Download-only (not bundled); fetched from the GitHub release at runtime.
            assetFileName = null,
            expectedVersionName = "1.0.1",
            expectedVersionCode = 42,
        ),
    )

    fun byPackage(packageName: String): ModSpec? =
        specs.firstOrNull { it.packageName == packageName }
}
