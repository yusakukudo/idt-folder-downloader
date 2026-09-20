package com.idtdownloader.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.idtdownloader.app.viewmodel.DownloadViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            val viewModel: DownloadViewModel = viewModel()
            val isDarkMode by viewModel.isDarkMode.collectAsState()

            MaterialTheme(
                colorScheme = if (isDarkMode) darkColorScheme(
                    background = Color(0xFF0F172A),
                    surface = Color(0xFF1E293B),
                    primary = Color(0xFF38BDF8),
                    secondary = Color(0xFF10B981)
                ) else lightColorScheme(
                    background = Color(0xFFF1F5F9),
                    surface = Color.White,
                    primary = Color(0xFF0284C7),
                    secondary = Color(0xFF059669)
                )
            ) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    MainScreen(viewModel)
                }
            }
        }
    }
}

@Composable
fun MainScreen(viewModel: DownloadViewModel) {
    val url by viewModel.url.collectAsState()
    val isDownloading by viewModel.isDownloading.collectAsState()
    val isPaused by viewModel.isPaused.collectAsState()
    val progressState by viewModel.progressState.collectAsState()
    val fileMap by viewModel.fileMap.collectAsState()
    val logs by viewModel.logs.collectAsState()
    val showLogs by viewModel.showLogs.collectAsState()
    val isDarkMode by viewModel.isDarkMode.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Header
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(14.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "🎵 IDT Audio Downloader",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Text(
                        text = "Android Mobile Edition",
                        fontSize = 12.sp,
                        color = Color.Gray
                    )
                }

                IconButton(onClick = { viewModel.toggleTheme() }) {
                    Text(if (isDarkMode) "🌙" else "☀️", fontSize = 20.sp)
                }
            }
        }

        // URL Input
        OutlinedTextField(
            value = url,
            onValueChange = { viewModel.setUrl(it) },
            label = { Text("IDT Folder URL") },
            placeholder = { Text("audio.iskcondesiretree.com/...") },
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(8.dp)
        )

        // Control Buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Button(
                onClick = { viewModel.startDownload() },
                enabled = !isDownloading,
                modifier = Modifier.weight(1f),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0284C7))
            ) {
                Text("▶ Start", color = Color.White)
            }

            Button(
                onClick = {
                    if (isPaused) viewModel.resumeDownload() else viewModel.pauseDownload()
                },
                enabled = isDownloading,
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFD97706))
            ) {
                Text(if (isPaused) "▶ Resume" else "⏸ Pause", color = Color.White)
            }

            Button(
                onClick = { viewModel.cancelDownload() },
                enabled = isDownloading,
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFDC2626))
            ) {
                Text("⏹ Stop", color = Color.White)
            }
        }

        // Dashboard Metrics
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            MetricCard("FILES", "${progressState.completedFiles}/${progressState.totalFiles}", Modifier.weight(1f))
            MetricCard("SIZE", String.format("%.1f MB", progressState.totalBytes / (1024.0 * 1024.0)), Modifier.weight(1f))
            MetricCard("SPEED", String.format("%.2f MB/s", progressState.speedBps / (1024.0 * 1024.0)), Modifier.weight(1f))
        }

        // Overall Progress Bar
        val pct = if (progressState.totalFiles > 0) progressState.completedFiles.toFloat() / progressState.totalFiles else 0f
        LinearProgressIndicator(
            progress = { pct },
            modifier = Modifier
                .fillMaxWidth()
                .height(10.dp),
            color = Color(0xFF10B981)
        )

        // Queue Header + Log Toggle
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("📄 Audio Files Queue (${fileMap.size})", fontWeight = FontWeight.Bold)
            TextButton(onClick = { viewModel.toggleShowLogs() }) {
                Text(if (showLogs) "📋 Hide Logs" else "📋 Show Logs")
            }
        }

        // File Queue List
        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            items(fileMap.values.toList()) { fileState ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(8.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(10.dp),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(fileState.name, fontWeight = FontWeight.SemiBold, fontSize = 13.sp, maxLines = 1)
                            Text("${fileState.sizeText} | ${fileState.status}", fontSize = 11.sp, color = Color.Gray)
                        }
                        Text("${fileState.progress}%", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                    }
                }
            }
        }

        // Collapsible Log Console
        if (showLogs) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(120.dp),
                shape = RoundedCornerShape(8.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF090D16))
            ) {
                LazyColumn(modifier = Modifier.padding(8.dp)) {
                    items(logs) { logMsg ->
                        Text(logMsg, fontSize = 10.sp, color = Color(0xFF38BDF8), fontFamily = FontFamily.Monospace)
                    }
                }
            }
        }
    }
}

@Composable
fun MetricCard(title: String, value: String, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(8.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(modifier = Modifier.padding(10.dp)) {
            Text(title, fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Color.Gray)
            Text(value, fontSize = 14.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
        }
    }
}
