package com.idtdownloader.app.data

import kotlinx.coroutines.*
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileOutputStream
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong

data class DownloadProgressState(
    val completedFiles: Int,
    val totalFiles: Int,
    val totalBytes: Long,
    val speedBps: Double,
    val elapsedTimeSec: Double
)

class IDTDownloader(private val concurrency: Int = 5) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    private val isPaused = AtomicBoolean(false)
    private val isCancelled = AtomicBoolean(false)

    fun pause() { isPaused.set(true) }
    fun resume() { isPaused.set(false) }
    fun cancel() { isCancelled.set(true) }

    suspend fun downloadAll(
        items: List<DownloadTaskItem>,
        onFileProgress: (filePath: String, downloaded: Long, total: Long, status: String) -> Unit,
        onOverallProgress: (DownloadProgressState) -> Unit
    ) = withContext(Dispatchers.IO) {
        val totalFiles = items.size
        var completedFiles = 0
        val totalDownloadedBytes = AtomicLong(0L)
        val startTime = System.currentTimeMillis()

        val semaphore = Semaphore(concurrency)
        val jobs = items.map { item ->
            async {
                semaphore.withPermit {
                    if (isCancelled.get()) return@withPermit

                    val file = File(item.savePath)
                    if (file.exists()) {
                        onFileProgress(item.savePath, file.length(), file.length(), "Skipped")
                        completedFiles++
                        return@withPermit
                    }

                    val tempFile = File(item.savePath + ".part")
                    var downloaded = if (tempFile.exists()) tempFile.length() else 0L

                    try {
                        val requestBuilder = Request.Builder()
                            .url(item.url)
                            .header("User-Agent", "Mozilla/5.0 (Linux; Android 14)")

                        if (downloaded > 0) {
                            requestBuilder.header("Range", "bytes=$downloaded-")
                        }

                        val response = client.newCall(requestBuilder.build()).execute()
                        if (response.isSuccessful) {
                            val body = response.body
                            val contentLength = body?.contentLength() ?: 0L
                            val totalSize = if (response.code == 206) downloaded + contentLength else contentLength
                            val mode = response.code == 206

                            val inputStream = body?.byteStream()
                            val outputStream = FileOutputStream(tempFile, mode)

                            val buffer = ByteArray(8192)
                            var bytesRead: Int

                            inputStream?.use { input ->
                                outputStream.use { output ->
                                    while (input.read(buffer).also { bytesRead = it } != -1) {
                                        if (isCancelled.get()) break
                                        while (isPaused.get()) {
                                            Thread.sleep(300)
                                            if (isCancelled.get()) break
                                        }

                                        output.write(buffer, 0, bytesRead)
                                        downloaded += bytesRead
                                        totalDownloadedBytes.addAndGet(bytesRead.toLong())

                                        onFileProgress(item.savePath, downloaded, totalSize, "Downloading")
                                    }
                                }
                            }

                            if (!isCancelled.get()) {
                                tempFile.renameTo(file)
                                onFileProgress(item.savePath, downloaded, totalSize, "Completed")
                                completedFiles++
                            }
                        }
                    } catch (e: Exception) {
                        onFileProgress(item.savePath, 0, 0, "Failed")
                    }

                    val elapsed = (System.currentTimeMillis() - startTime) / 1000.0
                    val speed = if (elapsed > 0) totalDownloadedBytes.get() / elapsed else 0.0
                    onOverallProgress(
                        DownloadProgressState(
                            completedFiles = completedFiles,
                            totalFiles = totalFiles,
                            totalBytes = totalDownloadedBytes.get(),
                            speedBps = speed,
                            elapsedTimeSec = elapsed
                        )
                    )
                }
            }
        }
        jobs.awaitAll()
    }
}
