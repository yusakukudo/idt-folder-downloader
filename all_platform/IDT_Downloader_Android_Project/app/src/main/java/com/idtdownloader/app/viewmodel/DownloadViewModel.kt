package com.idtdownloader.app.viewmodel

import android.app.Application
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Environment
import android.provider.DocumentsContract
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.idtdownloader.app.data.DownloadProgressState
import com.idtdownloader.app.data.DownloadTaskItem
import com.idtdownloader.app.data.IDTCrawler
import com.idtdownloader.app.data.IDTDownloader
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File

data class FileUiState(
    val name: String,
    val sizeText: String,
    val status: String,
    val progress: Int
)

class DownloadViewModel(application: Application) : AndroidViewModel(application) {
    private val _url = MutableStateFlow("")
    val url: StateFlow<String> = _url.asStateFlow()

    private val defaultDownloadDirectory: String by lazy {
        val pubDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
        val candidate = File(pubDir, "IDT_Downloads")
        if (pubDir != null && (candidate.exists() || candidate.mkdirs() || candidate.canWrite())) {
            candidate.absolutePath
        } else {
            val appExt = getApplication<Application>().getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)
            (appExt ?: File(getApplication<Application>().filesDir, "IDT_Downloads")).absolutePath
        }
    }

    private val _saveDirectory = MutableStateFlow("")
    val saveDirectory: StateFlow<String> = _saveDirectory.asStateFlow()

    init {
        _saveDirectory.value = defaultDownloadDirectory
    }

    private val _isDarkMode = MutableStateFlow(true)
    val isDarkMode: StateFlow<Boolean> = _isDarkMode.asStateFlow()

    private val _isDownloading = MutableStateFlow(false)
    val isDownloading: StateFlow<Boolean> = _isDownloading.asStateFlow()

    private val _isPaused = MutableStateFlow(false)
    val isPaused: StateFlow<Boolean> = _isPaused.asStateFlow()

    private val _progressState = MutableStateFlow(DownloadProgressState(0, 0, 0L, 0.0, 0.0))
    val progressState: StateFlow<DownloadProgressState> = _progressState.asStateFlow()

    private val _fileMap = MutableStateFlow<Map<String, FileUiState>>(emptyMap())
    val fileMap: StateFlow<Map<String, FileUiState>> = _fileMap.asStateFlow()

    private val _logs = MutableStateFlow<List<String>>(emptyList())
    val logs: StateFlow<List<String>> = _logs.asStateFlow()

    private val _showLogs = MutableStateFlow(true)
    val showLogs: StateFlow<Boolean> = _showLogs.asStateFlow()

    private var downloader: IDTDownloader? = null

    fun setUrl(newUrl: String) { _url.value = newUrl }
    fun setSaveDirectory(newDir: String) { _saveDirectory.value = newDir }

    fun setCustomDirectoryUri(uri: Uri, context: Context) {
        try {
            val flags = Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION
            context.contentResolver.takePersistableUriPermission(uri, flags)
        } catch (_: Exception) {}

        val resolved = getPathFromTreeUri(uri)
        val chosen = resolved ?: uri.toString()
        _saveDirectory.value = chosen
        addLog("📁 Selected directory: $chosen")
    }

    private fun getPathFromTreeUri(uri: Uri): String? {
        val docId = DocumentsContract.getTreeDocumentId(uri) ?: return null
        val split = docId.split(":")
        val type = split[0]
        return if ("primary".equals(type, ignoreCase = true)) {
            val relativePath = if (split.size > 1) split[1] else ""
            "${Environment.getExternalStorageDirectory()}/$relativePath".trimEnd('/')
        } else {
            val relativePath = if (split.size > 1) split[1] else ""
            "/storage/$type/$relativePath".trimEnd('/')
        }
    }

    fun toggleTheme() { _isDarkMode.value = !_isDarkMode.value }
    fun toggleShowLogs() { _showLogs.value = !_showLogs.value }

    fun startDownload() {
        var rawUrl = _url.value.trim()
        if (rawUrl.isNotEmpty() && !rawUrl.startsWith("http://") && !rawUrl.startsWith("https://")) {
            rawUrl = "https://$rawUrl"
            _url.value = rawUrl
        }

        if (rawUrl.isEmpty() || (!rawUrl.startsWith("http://") && !rawUrl.startsWith("https://"))) {
            addLog("❌ Please enter a valid HTTP/HTTPS URL.")
            return
        }

        _isDownloading.value = true
        _isPaused.value = false
        _fileMap.value = emptyMap()

        addLog("🔍 Scanning IDT website structure...")

        viewModelScope.launch {
            val chosenPath = _saveDirectory.value.trim()
            val downloadDir = if (chosenPath.isNotEmpty()) {
                val f = File(chosenPath)
                f.mkdirs()
                if (f.exists() && f.canWrite()) f else File(defaultDownloadDirectory).apply { mkdirs() }
            } else {
                File(defaultDownloadDirectory).apply { mkdirs() }
            }

            addLog("📁 Destination folder: ${downloadDir.absolutePath}")

            val crawler = IDTCrawler(rawUrl, downloadDir)
            val filesList = crawler.crawl { visited, count, lastFile ->
                addLog("Scanning: $visited page(s) | Found $count file(s)")
            }

            addLog("📦 Discovery complete: ${filesList.size} file(s) found.")

            val initialMap = filesList.associate { item ->
                item.savePath to FileUiState(item.fileName, "Waiting...", "Queued", 0)
            }
            _fileMap.value = initialMap

            if (filesList.isEmpty()) {
                _isDownloading.value = false
                addLog("⚠️ No audio files found. Please ensure the link is an IDT audio folder.")
                return@launch
            }

            addLog("⚡ Starting async downloads...")
            downloader = IDTDownloader(concurrency = 5)

            downloader?.downloadAll(
                items = filesList,
                onFileProgress = { path, downloaded, total, status ->
                    val fileName = File(path).name
                    val pct = if (total > 0) ((downloaded * 100) / total).toInt() else 0
                    val sizeMB = String.format("%.2f MB", downloaded / (1024.0 * 1024.0))

                    _fileMap.value = _fileMap.value.toMutableMap().apply {
                        put(path, FileUiState(fileName, sizeMB, status, pct))
                    }
                },
                onOverallProgress = { state ->
                    _progressState.value = state
                }
            )

            _isDownloading.value = false
            addLog("✅ All downloads finished!")
        }
    }

    fun pauseDownload() {
        downloader?.pause()
        _isPaused.value = true
        addLog("⏸ Downloads paused.")
    }

    fun resumeDownload() {
        downloader?.resume()
        _isPaused.value = false
        addLog("▶ Downloads resumed.")
    }

    fun cancelDownload() {
        downloader?.cancel()
        _isDownloading.value = false
        _isPaused.value = false
        addLog("🛑 Downloads cancelled.")
    }

    private fun addLog(message: String) {
        _logs.value = _logs.value + message
    }
}
