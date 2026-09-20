# 🎵 idt-dlp (Multi-Platform Audio Downloader)

[![Build All Platforms & Release](https://github.com/yusakukudo/idt-folder-downloader/actions/workflows/build_all_platforms.yml/badge.svg)](https://github.com/yusakukudo/idt-folder-downloader/actions/workflows/build_all_platforms.yml)

**idt-dlp** is a high-speed, asynchronous audio folder downloader for the **ISKCON Desire Tree (IDT)** website, built for **macOS**, **Windows**, and **Android**.

---

## 📥 Direct Downloads (Latest Release)

| Platform | Download Link | Format | Description |
| :--- | :--- | :--- | :--- |
| **📱 Android** | [**Download for Android**](https://github.com/yusakukudo/idt-folder-downloader/releases/latest/download/idt-dlp-android.apk) | `.apk` (Direct Install) | Android 7.0+ (Folder Picker, Public Downloads) |
| **🪟 Windows** | [**Download for Windows**](https://github.com/yusakukudo/idt-folder-downloader/releases/latest/download/idt-dlp-windows.zip) | `.zip` (`.exe` standalone) | Windows 10 & 11 (x64 with Custom Icon) |
| **🍏 macOS** | [**Download for macOS**](https://github.com/yusakukudo/idt-folder-downloader/releases/latest/download/idt-dlp-macos.zip) | `.zip` (`.app` bundle) | macOS 11+ (Intel & Apple Silicon with ICNS) |

> 🔗 All releases & version history: [**GitHub Releases Page**](https://github.com/yusakukudo/idt-folder-downloader/releases)

---

## ✨ Key Features

- 🎨 **Unified idt-dlp Branding & Logo**: Official app logo integrated into Android launcher, Windows taskbar/executable, and macOS dock.
- 📁 **Customizable Save Location**: Directory browser on **all platforms** (including Android SAF folder picker), defaulting to public `Downloads/IDT_Downloads`.
- ⚡ **Asynchronous Parallel Downloading**: Multi-threaded downloads with configurable concurrency (1–20 workers).
- 🔄 **Smart Resume & Partial Download Recovery**: Interrupted downloads resume from the exact byte where they stopped (`.part` files).
- 📂 **Recursive Directory Scraping**: Stays strictly within the requested folder and child subdirectories, avoiding parent breadcrumbs.
- 🎨 **Dark / Light Mode**: Native theme toggle switch across desktop and mobile.
- 📊 **Real-Time Dashboard**: Live statistics for files completed, total downloaded size, transfer speed (MB/s), and elapsed time.
- 🌐 **Auto URL Normalization**: Automatically prepends `https://` if links are pasted without protocols.
- 📋 **Collapsible Diagnostic Logs**: Real-time console log pane can be toggled on/off.

---

## 📂 Repository Structure

```
├── idt_mac_app/                # 🍏 macOS Desktop Application source & PyInstaller builder
├── idt_win_app/                # 🪟 Windows Desktop Application source & PyInstaller builder
├── idt_android_app/            # 📱 Native Android Studio project (Kotlin + Jetpack Compose)
├── all_platform/               # 📦 Unified local multi-platform workspace folder
├── logo.png                    # 🎨 Master logo artwork
└── .github/workflows/          # ⚙️ GitHub Actions CI/CD to auto-compile binaries on push
```

---

## 📄 License
MIT License.
