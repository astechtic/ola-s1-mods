package com.yaaratech.s1mods.ui.screens

import android.widget.Toast
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.yaaratech.s1mods.model.EcosystemState
import com.yaaratech.s1mods.model.ModHealthStatus
import com.yaaratech.s1mods.model.ModOverall
import com.yaaratech.s1mods.model.ModProfile
import com.yaaratech.s1mods.model.ScooterManager
import com.yaaratech.s1mods.ui.theme.*
import kotlinx.coroutines.launch
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Mod management center: per-mod health + one-tap repair, install profiles, backup /
 * restore of the mod state, and an OTA-safe watchdog. Everything here reuses the same
 * ADB/ModRegistry grant contract as the setup flow — no new vehicle access.
 */
@Composable
fun ModHealthScreen(manager: ScooterManager) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val isConnected by manager.isConnected.collectAsState()

    var health by remember { mutableStateOf<List<ModHealthStatus>>(emptyList()) }
    var ecosystem by remember { mutableStateOf<EcosystemState?>(null) }
    var isLoading by remember { mutableStateOf(false) }
    var busyAction by remember { mutableStateOf<String?>(null) }
    var backups by remember { mutableStateOf<List<File>>(emptyList()) }
    var showRevertConfirm by remember { mutableStateOf(false) }

    fun refresh() {
        if (!isConnected) return
        scope.launch {
            isLoading = true
            try {
                health = manager.fetchModHealth()
                ecosystem = manager.checkEcosystemState()
                backups = manager.listBackups()
            } catch (e: Exception) {
                Toast.makeText(context, "Load failed: ${e.message}", Toast.LENGTH_LONG).show()
            } finally {
                isLoading = false
            }
        }
    }

    // Runs a per-mod action keyed by package, then refreshes. [block] returns a result
    // whose string form (if any) is toasted; exceptions are surfaced as a toast.
    fun runModAction(key: String, block: suspend () -> Any?) {
        if (busyAction != null) return
        scope.launch {
            busyAction = key
            try {
                val res = block()
                (res as? String)?.let { Toast.makeText(context, it, Toast.LENGTH_SHORT).show() }
                health = manager.fetchModHealth()
                ecosystem = manager.checkEcosystemState()
            } catch (e: Exception) {
                Toast.makeText(context, "Failed: ${e.message}", Toast.LENGTH_LONG).show()
            } finally {
                busyAction = null
            }
        }
    }

    // Runs a non-mod action (backup/restore/reapply) under a named busy key, then refreshes.
    fun runNamedAction(key: String, block: suspend () -> Any?) {
        if (busyAction != null) return
        scope.launch {
            busyAction = key
            try {
                block()
                Toast.makeText(context, "Done", Toast.LENGTH_SHORT).show()
                health = manager.fetchModHealth()
                ecosystem = manager.checkEcosystemState()
                backups = manager.listBackups()
            } catch (e: Exception) {
                Toast.makeText(context, "Failed: ${e.message}", Toast.LENGTH_LONG).show()
            } finally {
                busyAction = null
            }
        }
    }

    // Auto-load once connected.
    LaunchedEffect(isConnected) {
        backups = manager.listBackups()
        if (isConnected && health.isEmpty()) refresh()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(BgDark)
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text("Mod health", fontSize = 15.sp, fontWeight = FontWeight.SemiBold, color = TextPrimary)
                Text("Status, repair, profiles & backup", fontSize = 11.sp, color = TextMuted)
            }
            OutlinedButton(
                onClick = { refresh() },
                enabled = isConnected && !isLoading,
                shape = RoundedCornerShape(8.dp),
                border = BorderStroke(1.dp, CardBorder),
                contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = TextPrimary)
            ) {
                if (isLoading) {
                    CircularProgressIndicator(modifier = Modifier.size(14.dp), color = TextPrimary, strokeWidth = 2.dp)
                } else {
                    Icon(Icons.Default.Refresh, contentDescription = null, modifier = Modifier.size(15.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Refresh", fontSize = 12.sp, fontWeight = FontWeight.Medium)
                }
            }
        }

        if (!isConnected) {
            NotConnectedCard()
            return@Column
        }

        // OTA-safe watchdog banner
        ecosystem?.let { eco ->
            EcosystemCard(eco, busyAction == "reapply") {
                runNamedAction("reapply") { manager.reapplyFromLastBackup() }
            }
        }

        // Per-mod health
        if (health.isEmpty() && !isLoading) {
            Text("Tap Refresh to inspect installed mods.", fontSize = 12.sp, color = TextMuted)
        }
        health.forEach { status ->
            ModHealthCard(
                status = status,
                busy = busyAction == status.packageName,
                onRepair = { runModAction(status.packageName) { manager.repairMod(status.packageName) } },
                onInstall = { runModAction(status.packageName) { manager.installModByPackage(status.packageName) } },
                onUninstall = { runModAction(status.packageName) { manager.uninstallPackage(status.packageName) } }
            )
        }

        // Profiles
        ProfilesCard(enabled = busyAction == null && !isLoading) { profile ->
            runNamedAction("profile") { manager.applyProfile(profile) }
        }

        // Backup & restore
        BackupCard(
            backups = backups,
            busy = busyAction == "backup" || busyAction == "restore",
            onBackup = { runNamedAction("backup") { manager.backupModState() } },
            onRestore = { file -> runNamedAction("restore") { manager.restoreModState(file) } }
        )

        // Restore stock MoveOS state (reverts the one persistent change; safe for OTA/handover)
        RestoreStockCard(
            canRestore = manager.canRestoreStock(),
            busy = busyAction == "revert",
            onRevert = { showRevertConfirm = true }
        )

        Spacer(modifier = Modifier.height(8.dp))
    }

    if (showRevertConfirm) {
        AlertDialog(
            onDismissRequest = { showRevertConfirm = false },
            icon = { Icon(Icons.Default.Restore, contentDescription = null, tint = TextPrimary) },
            title = { Text("Restore stock state?", fontSize = 16.sp, fontWeight = FontWeight.SemiBold, color = TextPrimary) },
            text = {
                Text(
                    "This puts MoveOS's one persistent setting (scooter mode) back to the stock " +
                        "value captured before setup, and removes the temporary ADB key files. " +
                        "Reboot the scooter afterwards to re-lock ADB. Installed mods are left in " +
                        "place — remove those separately if you want. Use this before an Ola OTA or handover.",
                    fontSize = 12.sp, color = TextSecondary, lineHeight = 17.sp
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        showRevertConfirm = false
                        runNamedAction("revert") { manager.restoreStockState() }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = AccentMint, contentColor = BgDark),
                    shape = RoundedCornerShape(8.dp)
                ) { Text("Restore", fontWeight = FontWeight.SemiBold, fontSize = 13.sp) }
            },
            dismissButton = {
                TextButton(onClick = { showRevertConfirm = false }) { Text("Cancel", color = TextSecondary) }
            },
            containerColor = SurfaceDark,
            shape = RoundedCornerShape(12.dp)
        )
    }
}

@Composable
private fun NotConnectedCard() {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, CardBorder, RoundedCornerShape(12.dp)),
        colors = CardDefaults.cardColors(containerColor = SurfaceDark),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.LinkOff, contentDescription = null, tint = TextMuted, modifier = Modifier.size(20.dp))
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text("Not connected", fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = TextPrimary)
                Text("Connect to your scooter from the Setup tab to inspect and manage mods.", fontSize = 11.sp, color = TextSecondary, lineHeight = 15.sp)
            }
        }
    }
}

@Composable
private fun EcosystemCard(eco: EcosystemState, busy: Boolean, onReapply: () -> Unit) {
    val warn = eco.needsReapply
    val accent = if (warn) StatusWarning else StatusOk
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, accent.copy(alpha = 0.4f), RoundedCornerShape(12.dp)),
        colors = CardDefaults.cardColors(containerColor = SurfaceDark),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    if (warn) Icons.Default.Warning else Icons.Default.VerifiedUser,
                    contentDescription = null, tint = accent, modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    if (warn) "Mods need re-applying" else "Ecosystem healthy",
                    fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = TextPrimary
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            InfoRow("Mods installed", "${eco.installedModCount} / ${eco.totalMods}")
            InfoRow("Scooter mode", eco.scootermode.ifBlank { "—" })
            if (warn) {
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    "These were in your last backup but are gone now (a MoveOS update may have wiped them): ${eco.missingSinceBackup.joinToString()}",
                    fontSize = 11.sp, color = TextSecondary, lineHeight = 15.sp
                )
                Spacer(modifier = Modifier.height(10.dp))
                Button(
                    onClick = onReapply,
                    enabled = !busy,
                    modifier = Modifier.fillMaxWidth().height(40.dp),
                    shape = RoundedCornerShape(8.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = AccentMint, contentColor = BgDark)
                ) {
                    if (busy) {
                        CircularProgressIndicator(modifier = Modifier.size(14.dp), color = BgDark, strokeWidth = 2.dp)
                    } else {
                        Icon(Icons.Default.Restore, contentDescription = null, modifier = Modifier.size(15.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Re-apply from backup", fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                    }
                }
            } else if (!eco.hasBackup) {
                Spacer(modifier = Modifier.height(4.dp))
                Text("Tip: back up below so the watchdog can detect and restore wiped mods.", fontSize = 11.sp, color = TextMuted)
            }
        }
    }
}

@Composable
private fun ModHealthCard(
    status: ModHealthStatus,
    busy: Boolean,
    onRepair: () -> Unit,
    onInstall: () -> Unit,
    onUninstall: () -> Unit
) {
    val (dot, label) = when (status.overall) {
        ModOverall.HEALTHY -> StatusOk to "Healthy"
        ModOverall.NEEDS_ATTENTION -> StatusWarning to "Needs attention"
        ModOverall.NOT_INSTALLED -> TextMuted to "Not installed"
    }
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, CardBorder, RoundedCornerShape(12.dp)),
        colors = CardDefaults.cardColors(containerColor = SurfaceDark),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(8.dp).clip(CircleShape).background(dot))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(status.displayName, fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = TextPrimary)
                }
                Text(label, fontSize = 11.sp, color = dot, fontWeight = FontWeight.Medium)
            }

            Spacer(modifier = Modifier.height(10.dp))

            if (status.installed) {
                val installedV = status.installedVersionName?.ifBlank { null } ?: "unknown"
                val latestV = status.expectedVersionName ?: "—"
                InfoRow("Version", if (status.updateAvailable) "$installedV → $latestV" else installedV)
                if (status.hasAccessibility) {
                    StatusLine("Accessibility", status.accessibilityOk)
                }
                StatusLine("Overlay / appops", status.appopsOk)
                if (status.updateAvailable) {
                    Spacer(modifier = Modifier.height(6.dp))
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Upgrade, contentDescription = null, tint = StatusWarning, modifier = Modifier.size(14.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Update available ($latestV)", fontSize = 11.sp, color = StatusWarning)
                    }
                }
            } else {
                Text(
                    if (status.isBundled) "Not on the vehicle — install it below." else "Not on the vehicle — download from the Apps tab.",
                    fontSize = 11.sp, color = TextMuted
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (status.installed) {
                    Button(
                        onClick = onRepair,
                        enabled = !busy,
                        modifier = Modifier.weight(1f).height(38.dp),
                        shape = RoundedCornerShape(8.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AccentMint, contentColor = BgDark)
                    ) {
                        if (busy) {
                            CircularProgressIndicator(modifier = Modifier.size(13.dp), color = BgDark, strokeWidth = 2.dp)
                        } else {
                            Icon(Icons.Default.Build, contentDescription = null, modifier = Modifier.size(14.dp))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text("Repair", fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                        }
                    }
                    OutlinedButton(
                        onClick = onUninstall,
                        enabled = !busy,
                        modifier = Modifier.weight(1f).height(38.dp),
                        shape = RoundedCornerShape(8.dp),
                        border = BorderStroke(1.dp, StatusDanger.copy(alpha = 0.5f)),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = StatusDanger)
                    ) {
                        Icon(Icons.Default.DeleteOutline, contentDescription = null, modifier = Modifier.size(14.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Remove", fontSize = 12.sp, fontWeight = FontWeight.Medium)
                    }
                } else if (status.isBundled) {
                    Button(
                        onClick = onInstall,
                        enabled = !busy,
                        modifier = Modifier.weight(1f).height(38.dp),
                        shape = RoundedCornerShape(8.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AccentMint, contentColor = BgDark)
                    ) {
                        if (busy) {
                            CircularProgressIndicator(modifier = Modifier.size(13.dp), color = BgDark, strokeWidth = 2.dp)
                        } else {
                            Icon(Icons.Default.Download, contentDescription = null, modifier = Modifier.size(14.dp))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text("Install & grant", fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun RestoreStockCard(canRestore: Boolean, busy: Boolean, onRevert: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, CardBorder, RoundedCornerShape(12.dp)),
        colors = CardDefaults.cardColors(containerColor = SurfaceDark),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text("Restore stock state", fontSize = 11.sp, fontWeight = FontWeight.Medium, color = TextMuted)
            Text(
                "Reverts the one persistent MoveOS change (scooter mode) and removes the temporary ADB key. Run before an Ola OTA or handover; reboot after to re-lock ADB.",
                fontSize = 11.sp, color = TextMuted, lineHeight = 15.sp
            )
            Spacer(modifier = Modifier.height(10.dp))
            OutlinedButton(
                onClick = onRevert,
                enabled = !busy && canRestore,
                modifier = Modifier.fillMaxWidth().height(40.dp),
                shape = RoundedCornerShape(8.dp),
                border = BorderStroke(1.dp, CardBorder),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = TextPrimary)
            ) {
                if (busy) {
                    CircularProgressIndicator(modifier = Modifier.size(14.dp), color = TextPrimary, strokeWidth = 2.dp)
                } else {
                    Icon(Icons.Default.Restore, contentDescription = null, modifier = Modifier.size(15.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        if (canRestore) "Restore stock state (safe for OTA)" else "No stock value captured yet",
                        fontSize = 12.sp, fontWeight = FontWeight.SemiBold
                    )
                }
            }
        }
    }
}

@Composable
private fun StatusLine(label: String, ok: Boolean) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 3.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(label, fontSize = 12.sp, color = TextSecondary)
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                if (ok) Icons.Default.CheckCircle else Icons.Default.ErrorOutline,
                contentDescription = null,
                tint = if (ok) StatusOk else StatusWarning,
                modifier = Modifier.size(14.dp)
            )
            Spacer(modifier = Modifier.width(5.dp))
            Text(if (ok) "Active" else "Missing", fontSize = 12.sp, color = if (ok) StatusOk else StatusWarning, fontWeight = FontWeight.Medium)
        }
    }
}

@Composable
private fun ProfilesCard(enabled: Boolean, onApply: (ModProfile) -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, CardBorder, RoundedCornerShape(12.dp)),
        colors = CardDefaults.cardColors(containerColor = SurfaceDark),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text("Profiles", fontSize = 11.sp, fontWeight = FontWeight.Medium, color = TextMuted)
            Text("Install + grant a bundle in one tap", fontSize = 11.sp, color = TextMuted)
            Spacer(modifier = Modifier.height(10.dp))
            ModProfile.values().toList().chunked(2).forEach { rowItems ->
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    rowItems.forEach { profile ->
                        OutlinedButton(
                            onClick = { onApply(profile) },
                            enabled = enabled,
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(8.dp),
                            border = BorderStroke(1.dp, CardBorder),
                            contentPadding = PaddingValues(vertical = 8.dp, horizontal = 8.dp),
                            colors = ButtonDefaults.outlinedButtonColors(contentColor = TextPrimary)
                        ) {
                            Column(horizontalAlignment = Alignment.Start, modifier = Modifier.fillMaxWidth()) {
                                Text(profile.displayName, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                                Text(profile.description, fontSize = 10.sp, color = TextMuted)
                            }
                        }
                    }
                    if (rowItems.size == 1) Spacer(modifier = Modifier.weight(1f))
                }
                Spacer(modifier = Modifier.height(8.dp))
            }
        }
    }
}

@Composable
private fun BackupCard(
    backups: List<File>,
    busy: Boolean,
    onBackup: () -> Unit,
    onRestore: (File) -> Unit
) {
    val fmt = remember { SimpleDateFormat("dd MMM, HH:mm", Locale.getDefault()) }
    val latest = backups.firstOrNull()
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, CardBorder, RoundedCornerShape(12.dp)),
        colors = CardDefaults.cardColors(containerColor = SurfaceDark),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text("Backup & restore", fontSize = 11.sp, fontWeight = FontWeight.Medium, color = TextMuted)
            Text("Snapshot mods + scooter mode; restore after an OTA or reset", fontSize = 11.sp, color = TextMuted, lineHeight = 15.sp)
            Spacer(modifier = Modifier.height(10.dp))
            if (latest != null) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(SurfaceVariantDark)
                        .padding(horizontal = 10.dp, vertical = 8.dp)
                ) {
                    Column {
                        Text("Last backup", fontSize = 10.sp, color = TextMuted)
                        Text(fmt.format(Date(latest.lastModified())), fontSize = 12.sp, fontFamily = FontFamily.Monospace, color = TextPrimary)
                    }
                }
                Spacer(modifier = Modifier.height(10.dp))
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(
                    onClick = onBackup,
                    enabled = !busy,
                    modifier = Modifier.weight(1f).height(40.dp),
                    shape = RoundedCornerShape(8.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = SurfaceVariantDark, contentColor = TextPrimary)
                ) {
                    if (busy) {
                        CircularProgressIndicator(modifier = Modifier.size(14.dp), color = TextPrimary, strokeWidth = 2.dp)
                    } else {
                        Icon(Icons.Default.Save, contentDescription = null, modifier = Modifier.size(15.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Back up now", fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                    }
                }
                Button(
                    onClick = { latest?.let(onRestore) },
                    enabled = !busy && latest != null,
                    modifier = Modifier.weight(1f).height(40.dp),
                    shape = RoundedCornerShape(8.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = AccentMint, contentColor = BgDark,
                        disabledContainerColor = SurfaceHighlight, disabledContentColor = TextMuted
                    )
                ) {
                    Icon(Icons.Default.Restore, contentDescription = null, modifier = Modifier.size(15.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Restore", fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                }
            }
        }
    }
}
