# 🌐 IDT Audio Downloader — Multi-Platform Package (`all_platform`)

This folder contains the complete multi-platform release suite for downloading audio folders from the ISKCON Desire Tree website:

---

## 🍏 1. macOS Desktop App
- **Directory**: [`IDT Downloader.app`](file:///Users/anshrajdhakad/Scripts/01_Projects/idt_link_folder_downloader/all_platform/IDT%20Downloader.app)
- **Features**: Standalone native macOS App bundle with PySide6 (Qt6), real-time Dark/Light theme toggle, auto-URL scheme detection, live metrics, and collapsible diagnostic logs.
- **Launch Command**:
  ```bash
  open "all_platform/IDT Downloader.app"
  ```

---

## 🪟 2. Windows Desktop App
- **Directory**: [`IDT_Downloader_Windows/`](file:///Users/anshrajdhakad/Scripts/01_Projects/idt_link_folder_downloader/all_platform/IDT_Downloader_Windows)
- **Features**: Windows standalone desktop executable package with High-DPI scaling enabled, Windows illegal character sanitization (`< > : " / \ | ? *`), and Windows `Downloads\IDT_Downloads` default destination folder.
- **Launch Command (on Windows)**:
  Double-click `IDT_Downloader_Windows.exe` inside `IDT_Downloader_Windows/`.

---

## 📱 3. Native Android App
- **Directory**: [`IDT_Downloader_Android_Project/`](file:///Users/anshrajdhakad/Scripts/01_Projects/idt_link_folder_downloader/all_platform/IDT_Downloader_Android_Project)
- **Features**: Kotlin + Jetpack Compose Material 3 UI with Coroutine parallel downloader engine, OkHttp range resumption, and mobile log console.
- **Build / Run**: Open `IDT_Downloader_Android_Project` in Android Studio and click **Build APK** or **Run** to deploy to any Android device.
