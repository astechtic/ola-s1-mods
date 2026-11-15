package com.asjohn720.s1mods.adb

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
    /** Explicit launcher component (`pkg/.Activity`), or null to launch via monkey. */
    val launchActivity: String? = null,
    /** Accessibility service component to enable, or null if the mod has none. */
    val accessibilityService: String? = null,
    /** appops to `allow` on install and reset to `default` on uninstall. */
    val appops: List<String> = emptyList(),
    /** Runtime permissions to `pm grant` on install and `pm revoke` on uninstall. */
    val permissions: List<String> = emptyList(),
)

/**
 * The known mods. Looked up by package name so both the bundled [ModApp]s and the
 * downloaded ones (OpenPlay) resolve to the same install/uninstall behaviour.
 */
object ModRegistry {
    val specs: List<ModSpec> = listOf(
        ModSpec(
            packageName = "com.asjohn720.ball",
            launchActivity = "com.asjohn720.ball/.ui.MainActivity",
            accessibilityService = "com.asjohn720.ball/com.asjohn720.ball.core.QuickBallService",
            appops = listOf("SYSTEM_ALERT_WINDOW", "WRITE_SETTINGS"),
        ),
        ModSpec(
            packageName = "com.asjohn720.androidauto",
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
        ),
        ModSpec(
            packageName = "com.asjohn720.musicmod",
            permissions = listOf("android.permission.READ_EXTERNAL_STORAGE"),
        ),
        ModSpec(
            packageName = "com.asjohn720.openplay",
            appops = listOf("SYSTEM_ALERT_WINDOW", "WRITE_SETTINGS", "GET_USAGE_STATS"),
            permissions = listOf(
                "android.permission.RECORD_AUDIO",
                "android.permission.ACCESS_FINE_LOCATION",
                "android.permission.ACCESS_COARSE_LOCATION",
                "android.permission.NEARBY_WIFI_DEVICES",
                "android.permission.BLUETOOTH_CONNECT",
            ),
        ),
    )

    fun byPackage(packageName: String): ModSpec? =
        specs.firstOrNull { it.packageName == packageName }
}
