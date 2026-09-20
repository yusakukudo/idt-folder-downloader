# 🎵 IDT Audio Folder Downloader (Multi-Platform)

[![Build All Platforms & Release](https://github.com/yusakukudo/idt-folder-downloader/actions/workflows/build_all_platforms.yml/badge.svg)](https://github.com/yusakukudo/idt-folder-downloader/actions/workflows/build_all_platforms.yml)

A high-speed, asynchronous audio folder downloader for the **ISKCON Desire Tree (IDT)** website, built for **macOS**, **Windows**, and **Android**.

---

## 📥 Direct Downloads

| Platform | Download Link | Format | Description |
| :--- | :--- | :--- | :--- |
| **🍏 macOS** | [**Download for macOS**](https://github.com/yusakukudo/idt-folder-downloader/releases/latest/download/IDT_Downloader_macOS.zip) | `.zip` (`.app` bundle) | macOS 11+ (Intel & Apple Silicon) |
| **🪟 Windows** | [**Download for Windows**](https://github.com/yusakukudo/idt-folder-downloader/releases/latest/download/IDT_Downloader_Windows.zip) | `.zip` (`.exe` standalone) | Windows 10 & 11 (x64) |
| **📱 Android** | [**Download for Android**](https://github.com/yusakukudo/idt-folder-downloader/releases/latest/download/IDT_Downloader_Android.apk) | `.apk` (Direct Install) | Android 7.0+ (ARM64 & x86) |

> 🔗 All releases & version history: [**GitHub Releases Page**](https://github.com/yusakukudo/idt-folder-downloader/releases)

---

## ✨ Features

- ⚡ **Asynchronous Parallel Downloading**: Multi-threaded downloads with configurable concurrency (1–20 workers).
- 🔄 **Smart Resume & Partial Download Recovery**: Interrupted downloads resume from the exact byte where they stopped (`.part` files).
- 📂 **Recursive Directory Scraping**: Automatically scans subdirectories, preserving the exact website folder structure locally.
- 🎨 **Dark / Light Mode**: Native theme toggle switch for comfortable viewing.
- 📊 **Real-Time Dashboard**: Live statistics for files completed, total downloaded size, transfer speed (MB/s), and elapsed time.
- 🌐 **Auto URL Normalization**: Automatically detects links pasted without `https://` or `http://`.
- 📋 **Collapsible Diagnostic Logs**: Real-time console log pane can be toggled on/off.

---

## 📂 Repository Structure

```
├── idt_mac_app/                # 🍏 macOS Desktop Application source & PyInstaller builder
├── idt_win_app/                # 🪟 Windows Desktop Application source & PyInstaller builder
├── idt_android_app/            # 📱 Native Android Studio project (Kotlin + Jetpack Compose)
├── all_platform/               # 📦 Unified local multi-platform workspace folder
└── .github/workflows/          # ⚙️ GitHub Actions CI/CD to auto-compile binaries on push
```

---

## 🛠️ Local Development & Running

### macOS
```bash
python3 -m venv venv
./venv/bin/pip install -r idt_mac_app/requirements.txt
./venv/bin/python idt_mac_app/main.py
```

### Windows
```cmd
python -m venv venv
venv\Scripts\pip install -r idt_win_app\requirements.txt
python idt_win_app\main.py
```

### Android
Open `idt_android_app` in **Android Studio** and click **Run** or **Build > Build APK(s)**.

---

## 📄 License
MIT License.
