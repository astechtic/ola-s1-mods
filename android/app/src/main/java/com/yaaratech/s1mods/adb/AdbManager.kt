package com.yaaratech.s1mods.adb

import android.content.Context
import dadb.AdbKeyPair
import dadb.Dadb
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

/**
 * Manages ADB keypair generation and Dadb connection to the vehicle over TCP Port 5555.
 */
class AdbManager(private val context: Context) {

    private var activeDadb: Dadb? = null

    /**
     * Retrieves or generates an RSA 2048 keypair in standard ADB format.
     */
    fun getOrCreateAdbKeyPair(): Pair<AdbKeyPair, String> {
        val adbDir = File(context.filesDir, "adb").apply { mkdirs() }
        val privFile = File(adbDir, "adbkey")
        val pubFile = File(adbDir, "adbkey.pub")

        if (!privFile.exists() || !pubFile.exists()) {
            AdbKeyPair.generate(privFile, pubFile)
        }

        val keyPair = AdbKeyPair.read(privFile, pubFile)
        val pubKeyContent = pubFile.readText().trim()
        return Pair(keyPair, pubKeyContent)
    }

    /**
     * Connects to the vehicle's ADB daemon at [host]:[port].
     */
    suspend fun connect(host: String, port: Int = 5555): Dadb = withContext(Dispatchers.IO) {
        activeDadb?.close()
        val (keyPair, _) = getOrCreateAdbKeyPair()

        val cleanHost = com.yaaratech.s1mods.discovery.NetworkScanner.normalizeHost(host)

        val dadbInstance = Dadb.create(cleanHost, port, keyPair)
        activeDadb = dadbInstance
        dadbInstance
    }

    /**
     * Checks if a package is already installed on the vehicle.
     */
    suspend fun isPackageInstalled(packageName: String): Boolean = withContext(Dispatchers.IO) {
        val client = activeDadb ?: return@withContext false
        val out = client.shell("pm list packages $packageName").allOutput
        out.contains("package:$packageName")
    }

    /**
     * Installs an APK file onto the vehicle via ADB streaming install (-r reinstall with data kept).
     */
    suspend fun installApk(apkFile: File): String = withContext(Dispatchers.IO) {
        val client = activeDadb ?: throw IllegalStateException("ADB not connected")
        client.install(apkFile)
        "Success"
    }

    /**
     * Uninstalls a package cleanly from the vehicle.
     */
    suspend fun uninstallPackage(packageName: String): String = withContext(Dispatchers.IO) {
        val client = activeDadb ?: throw IllegalStateException("ADB not connected")
        val out = client.shell("pm uninstall $packageName").allOutput.trim()
        out
    }

    /**
     * Runs shell command via ADB and returns stdout + stderr.
     */
    suspend fun shell(command: String): String = withContext(Dispatchers.IO) {
        val client = activeDadb ?: throw IllegalStateException("ADB not connected")
        val response = client.shell(command)
        (response.allOutput).trim()
    }

    /** Stops the app if it is running, so an uninstall is not racing a live process. */
    suspend fun forceStop(packageName: String) = withContext(Dispatchers.IO) {
        val client = activeDadb ?: throw IllegalStateException("ADB not connected")
        client.shell("am force-stop $packageName")
        Unit
    }

    /** The current `enabled_accessibility_services` list, split into components. */
    private suspend fun enabledAccessibilityServices(): MutableList<String> {
        val client = activeDadb ?: throw IllegalStateException("ADB not connected")
        val raw = client.shell("settings get secure enabled_accessibility_services").allOutput.trim()
        // `settings get` prints the literal string "null" when the key is unset.
        if (raw.isEmpty() || raw == "null") return mutableListOf()
        return raw.split(':').map { it.trim() }.filter { it.isNotEmpty() }.toMutableList()
    }

    /**
     * Enables an accessibility service **without clobbering** any already-enabled one:
     * read the colon-separated list, add our component if absent, write it back.
     */
    suspend fun addAccessibilityService(service: String) = withContext(Dispatchers.IO) {
        val client = activeDadb ?: throw IllegalStateException("ADB not connected")
        val services = enabledAccessibilityServices()
        if (!services.contains(service)) services.add(service)
        client.shell("settings put secure enabled_accessibility_services ${services.joinToString(":")}")
        client.shell("settings put secure accessibility_enabled 1")
        Unit
    }

    /**
     * Removes our accessibility service from the list (leaving any others intact). If the
     * list becomes empty, also flips `accessibility_enabled` back to 0.
     */
    suspend fun removeAccessibilityService(service: String) = withContext(Dispatchers.IO) {
        val client = activeDadb ?: throw IllegalStateException("ADB not connected")
        val services = enabledAccessibilityServices()
        services.remove(service)
        client.shell("settings put secure enabled_accessibility_services ${services.joinToString(":")}")
        if (services.isEmpty()) client.shell("settings put secure accessibility_enabled 0")
        Unit
    }

    /**
     * Applies a mod's full [ModSpec]: appops → runtime permissions → accessibility
     * (merge-safe). Each step is best-effort so one unsupported op can't abort the rest.
     */
    suspend fun grantMod(spec: ModSpec) = withContext(Dispatchers.IO) {
        val client = activeDadb ?: throw IllegalStateException("ADB not connected")
        spec.appops.forEach { op ->
            runCatching { client.shell("appops set ${spec.packageName} $op allow") }
        }
        spec.permissions.forEach { perm ->
            runCatching { client.shell("pm grant ${spec.packageName} $perm") }
        }
        spec.accessibilityService?.let { addAccessibilityService(it) }
        Unit
    }

    /**
     * The exact inverse of [grantMod], run before `pm uninstall`: stop the app, drop the
     * accessibility service from the shared list, reset appops to default and revoke the
     * runtime permissions we granted. Best-effort throughout.
     */
    suspend fun revokeMod(spec: ModSpec) = withContext(Dispatchers.IO) {
        val client = activeDadb ?: throw IllegalStateException("ADB not connected")
        runCatching { forceStop(spec.packageName) }
        spec.accessibilityService?.let { runCatching { removeAccessibilityService(it) } }
        spec.appops.forEach { op ->
            runCatching { client.shell("appops set ${spec.packageName} $op default") }
        }
        spec.permissions.forEach { perm ->
            runCatching { client.shell("pm revoke ${spec.packageName} $perm") }
        }
        Unit
    }

    fun disconnect() {
        try {
            activeDadb?.close()
        } catch (_: Exception) {}
        activeDadb = null
    }
}
