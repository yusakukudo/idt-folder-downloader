import os
import sys
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(BASE_DIR, "main.py")
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
CACHE_DIR = os.path.join(BASE_DIR, ".pyinstaller_cache")
APP_NAME = "IDT_Downloader_Windows"

os.environ["PYINSTALLER_CONFIG_DIR"] = CACHE_DIR


def build():
    print("🚀 Building standalone Windows Application (.exe)...")

    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR, ignore_errors=True)
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR, ignore_errors=True)

    pyinstaller_cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=" + APP_NAME,
        "--windowed",
        "--onedir",
        "--noconfirm",
        "--collect-all", "aiohttp",
        "--collect-all", "bs4",
        "--exclude-module", "PySide6.QtWebEngineCore",
        "--exclude-module", "PySide6.QtWebEngineWidgets",
        "--exclude-module", "PySide6.QtWebEngineQuick",
        "--exclude-module", "PySide6.QtQml",
        "--exclude-module", "PySide6.QtQuick",
        "--exclude-module", "PySide6.QtQuickWidgets",
        "--exclude-module", "PySide6.Qt3DCore",
        "--exclude-module", "PySide6.Qt3DRender",
        "--exclude-module", "PySide6.QtMultimedia",
        "--exclude-module", "PySide6.QtPdf",
        "--exclude-module", "PySide6.QtSql",
        MAIN_SCRIPT
    ]

    print("Running command:", " ".join(pyinstaller_cmd))
    result = subprocess.run(pyinstaller_cmd, cwd=BASE_DIR)

    if result.returncode == 0:
        exe_path = os.path.join(DIST_DIR, APP_NAME, f"{APP_NAME}.exe")
        print("\n✨ Windows Build successful!")
        print(f"📦 Executable folder generated at:\n   {os.path.join(DIST_DIR, APP_NAME)}")
    else:
        print("\n❌ Build failed with exit code:", result.returncode)


if __name__ == "__main__":
    build()
