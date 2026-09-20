package com.idtdownloader.app.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.jsoup.Jsoup
import java.io.File
import java.net.URLDecoder

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
    // LinkedHashMap keyed by savePath ensures unique files and stable ordering
    private val discoveredFiles = LinkedHashMap<String, DownloadTaskItem>()

    suspend fun crawl(
        onProgress: (visitedCount: Int, filesCount: Int, lastFile: String) -> Unit
    ): List<DownloadTaskItem> = withContext(Dispatchers.IO) {
        val rootFolderName = getFolderName(baseUrl)
        val targetDir = File(outputDir, rootFolderName)
        targetDir.mkdirs()

        crawlRecursive(baseUrl, targetDir, onProgress)
        return@withContext discoveredFiles.values.toList()
    }

    private fun crawlRecursive(
        url: String,
        currentDir: File,
        onProgress: (Int, Int, String) -> Unit
    ) {
        val visitKey = getNormalizedPath(url)
        if (visited.contains(visitKey)) return
        visited.add(visitKey)
        currentDir.mkdirs()

        try {
            val doc = Jsoup.connect(url)
                .userAgent("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                .timeout(20000)
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
                    if (!discoveredFiles.containsKey(targetFile.absolutePath)) {
                        discoveredFiles[targetFile.absolutePath] = DownloadTaskItem(fullUrl, targetFile.absolutePath, fileName)
                        onProgress(visited.size, discoveredFiles.size, fileName)
                    }
                } else if (link.contains("index.php?q=f&f=")) {
                    // Critical: only traverse into true child subdirectories, NEVER breadcrumbs or parent folders!
                    if (!isChildLink(url, link)) {
                        continue
                    }

                    val folderName = getFolderName(link)
                    val newDir = File(currentDir, folderName)
                    crawlRecursive(fullUrl, newDir, onProgress)
                }
            }
        } catch (e: Exception) {
            // Ignore non-fatal connection or parsing errors
        }
    }

    private fun getPathPart(rawUrl: String): String {
        return if (rawUrl.contains("f=")) rawUrl.substringAfter("f=") else rawUrl
    }

    private fun getNormalizedPath(rawUrl: String): String {
        val part = getPathPart(rawUrl)
        val decoded = try { URLDecoder.decode(part, "UTF-8") } catch (e: Exception) { part }
        return "/" + decoded.trim('/')
    }

    private fun isChildLink(parentUrl: String, childLink: String): Boolean {
        val parentPart = getPathPart(parentUrl)
        val childPart = getPathPart(childLink)

        // Raw prefix check (handles standard IDT URL encodings)
        if (childPart.startsWith("$parentPart%2F") || childPart.startsWith("$parentPart/")) {
            return true
        }

        // Decoded path check
        val parentNorm = getNormalizedPath(parentUrl)
        val childNorm = getNormalizedPath(childLink)

        return childNorm.startsWith("$parentNorm/") && childNorm.length > parentNorm.length + 1
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

    private fun sanitize(name: String): String {
        if (name.isBlank()) return "IDT_Folder"
        val decoded = try { URLDecoder.decode(name, "UTF-8") } catch (e: Exception) { name }
        val cleaned = decoded
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
            .replace("*", "_")
            .replace("?", "_")
            .replace("\"", "_")
            .replace("<", "_")
            .replace(">", "_")
            .replace("|", "_")
            .trim()
        return if (cleaned.isBlank()) "IDT_Folder" else cleaned
    }

    private fun getFolderName(link: String): String {
        val part = if (link.contains("f=")) link.substringAfter("f=") else link
        val decoded = try { URLDecoder.decode(part, "UTF-8") } catch (e: Exception) { part }
        val lastSegment = decoded.trim('/').split('/').lastOrNull() ?: "IDT_Folder"
        return sanitize(lastSegment)
    }

    private fun getFileName(link: String): String {
        val name = link.split("/").lastOrNull() ?: "audio.mp3"
        return sanitize(name)
    }

    private fun resolveUrl(base: String, link: String): String {
        return if (link.startsWith("http")) link else {
            val root = if (base.contains("index.php")) base.substringBefore("index.php") else base
            root.trimEnd('/') + "/" + link.removePrefix("/")
        }
    }
}
