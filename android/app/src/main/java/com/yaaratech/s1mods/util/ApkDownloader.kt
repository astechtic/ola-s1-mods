package com.yaaratech.s1mods.util

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest

/**
 * Clean file downloader with progress tracking and HTTP redirect support.
 */
object ApkDownloader {

    /** SHA-256 of a file as lowercase hex. */
    fun sha256(file: File): String {
        val md = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { input ->
            val buf = ByteArray(1 shl 16)
            while (true) {
                val n = input.read(buf)
                if (n < 0) break
                md.update(buf, 0, n)
            }
        }
        return md.digest().joinToString("") { "%02x".format(it) }
    }

    suspend fun download(
        urlStr: String,
        destinationFile: File,
        expectedSha256: String? = null, // null = not pinned; skip verification
        onProgress: (Float, Long, Long) -> Unit // (fraction 0f..1f, bytesRead, totalBytes)
    ): Boolean = withContext(Dispatchers.IO) {
        val parent = destinationFile.parentFile ?: throw IllegalStateException("Invalid destination path")
        if (!parent.exists()) parent.mkdirs()

        val tempFile = File(parent, destinationFile.name + ".tmp")
        if (tempFile.exists()) tempFile.delete()

        var connection: HttpURLConnection? = null
        try {
            var currentUrl = urlStr
            var redirects = 0
            val maxRedirects = 5

            while (redirects < maxRedirects) {
                val url = URL(currentUrl)
                connection = (url.openConnection() as HttpURLConnection).apply {
                    instanceFollowRedirects = true
                    connectTimeout = 20000
                    readTimeout = 40000
                    setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android) S1Mods/1.0")
                    setRequestProperty("Accept", "*/*")
                }

                val responseCode = connection.responseCode
                if (responseCode == HttpURLConnection.HTTP_MOVED_TEMP ||
                    responseCode == HttpURLConnection.HTTP_MOVED_PERM ||
                    responseCode == 307 || responseCode == 308) {
                    val location = connection.getHeaderField("Location")
                    connection.disconnect()
                    if (location.isNullOrBlank()) {
                        throw IllegalStateException("Redirected with empty Location header")
                    }
                    currentUrl = if (location.startsWith("http")) location else URL(url, location).toString()
                    redirects++
                } else if (responseCode in 200..299) {
                    break
                } else {
                    throw IllegalStateException("Server returned HTTP $responseCode")
                }
            }

            val conn = connection ?: throw IllegalStateException("Failed to open HTTP connection")
            val totalBytes = conn.contentLengthLong

            conn.inputStream.use { input ->
                FileOutputStream(tempFile).use { output ->
                    val buffer = ByteArray(32 * 1024)
                    var bytesRead: Int
                    var totalRead = 0L

                    while (input.read(buffer).also { bytesRead = it } != -1) {
                        output.write(buffer, 0, bytesRead)
                        totalRead += bytesRead
                        val fraction = if (totalBytes > 0) (totalRead.toFloat() / totalBytes.toFloat()) else -1f
                        onProgress(fraction, totalRead, totalBytes)
                    }
                }
            }

            if (destinationFile.exists()) destinationFile.delete()
            if (!tempFile.renameTo(destinationFile)) {
                // Fallback copy if rename fails across mount points
                tempFile.copyTo(destinationFile, overwrite = true)
                tempFile.delete()
            }

            // Integrity check: if a hash is pinned, the file must match or we delete it and fail.
            if (!expectedSha256.isNullOrBlank()) {
                val actual = sha256(destinationFile)
                if (!actual.equals(expectedSha256, ignoreCase = true)) {
                    destinationFile.delete()
                    throw IllegalStateException(
                        "SHA-256 mismatch: expected $expectedSha256 but got $actual. File rejected."
                    )
                }
            }
            true
        } catch (e: Exception) {
            if (tempFile.exists()) tempFile.delete()
            throw e
        } finally {
            connection?.disconnect()
        }
    }
}

