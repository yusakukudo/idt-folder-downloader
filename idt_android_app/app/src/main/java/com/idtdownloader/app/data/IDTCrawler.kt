package com.idtdownloader.app.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.jsoup.Jsoup
import java.io.File
import java.net.URLDecoder
import java.net.URLEncoder

data class DownloadTaskItem(
    val url: String,
    val savePath: String,
    val fileName: String
)

class IDTCrawler(
    private val baseUrl: String,
    private val outputDir: File
) {
    private val visited = mutableSetOf<String>()
    private val discoveredFiles = mutableListOf<DownloadTaskItem>()

    suspend fun crawl(
        onProgress: (visitedCount: Int, filesCount: Int, lastFile: String) -> Unit
    ): List<DownloadTaskItem> = withContext(Dispatchers.IO) {
        val rootFolderName = getFolderName(baseUrl)
        val targetDir = File(outputDir, rootFolderName)
        targetDir.mkdirs()

        crawlRecursive(baseUrl, targetDir, onProgress)
        return@withContext discoveredFiles.toList()
    }

    private fun crawlRecursive(
        url: String,
        currentDir: File,
        onProgress: (Int, Int, String) -> Unit
    ) {
        if (visited.contains(url)) return
        visited.add(url)
        currentDir.mkdirs()

        try {
            val doc = Jsoup.connect(url)
                .userAgent("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36")
                .timeout(15000)
                .get()

            val links = doc.select("a[href]")
            for (element in links) {
                val href = element.attr("href")
                val onclick = element.attr("onclick")

                val link = extractLink(href, onclick) ?: continue
                val fullUrl = resolveUrl(url, link)

                if (isMp3(link)) {
                    val fileName = getFileName(link)
                    val targetFile = File(currentDir, fileName)
                    discoveredFiles.add(DownloadTaskItem(fullUrl, targetFile.absolutePath, fileName))
                    onProgress(visited.size, discoveredFiles.size, fileName)
                } else if (link.contains("index.php?q=f&f=")) {
                    val folderName = getFolderName(link)
                    val newDir = File(currentDir, folderName)
                    crawlRecursive(fullUrl, newDir, onProgress)
                }
            }
        } catch (_: Exception) {
            // Skip broken links
        }
    }

    private fun extractLink(href: String, onclick: String): String? {
        if (href.contains("index.php?q=f&f=")) return href
        if (onclick.contains("index.php?q=f&f=")) {
            val regex = Regex("""index\.php\?q=f&f=[^']+""")
            return regex.find(onclick)?.value
        }
        if (href.endsWith(".mp3", ignoreCase = true)) return href
        return null
    }

    private fun isMp3(link: String): Boolean = link.endsWith(".mp3", ignoreCase = true)

    private fun getFolderName(link: String): String {
        val part = if (link.contains("f=")) link.substringAfter("f=") else link
        val decoded = try { URLDecoder.decode(part, "UTF-8") } catch (_: Exception) { part }
        return decoded.trim('/').split('/').lastOrNull()?.replace("/", "_") ?: "IDT_Folder"
    }

    private fun getFileName(link: String): String {
        val name = link.split("/").lastOrNull() ?: "audio.mp3"
        return try { URLDecoder.decode(name, "UTF-8") } catch (_: Exception) { name }
    }

    private fun resolveUrl(base: String, link: String): String {
        return if (link.startsWith("http")) link else {
            val root = if (base.contains("index.php")) base.substringBefore("index.php") else base
            root + link.removePrefix("/")
        }
    }
}
