import os
import sys
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(BASE_DIR, "main.py")
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
CACHE_DIR = os.path.join(BASE_DIR, ".pyinstaller_cache")
APP_NAME = "IDT Downloader"

os.environ["PYINSTALLER_CONFIG_DIR"] = CACHE_DIR


def build():
    print("🚀 Building standalone macOS Application (.app bundle)...")

    # Clean build directories
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR, ignore_errors=True)
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR, ignore_errors=True)

    pyinstaller_bin = os.path.join(os.path.dirname(sys.executable), "pyinstaller")
    if not os.path.exists(pyinstaller_bin):
        pyinstaller_bin = "pyinstaller"

    pyinstaller_cmd = [
        pyinstaller_bin,
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
        "--exclude-module", "PySide6.Qt3DInput",
        "--exclude-module", "PySide6.Qt3DLogic",
        "--exclude-module", "PySide6.Qt3DExtras",
        "--exclude-module", "PySide6.QtMultimedia",
        "--exclude-module", "PySide6.QtMultimediaWidgets",
        "--exclude-module", "PySide6.QtPdf",
        "--exclude-module", "PySide6.QtPdfWidgets",
        "--exclude-module", "PySide6.QtSql",
        "--exclude-module", "PySide6.QtBluetooth",
        "--exclude-module", "PySide6.QtNfc",
        "--exclude-module", "PySide6.QtPositioning",
        "--exclude-module", "PySide6.QtLocation",
        "--exclude-module", "PySide6.QtSensors",
        "--exclude-module", "PySide6.QtSpatialAudio",
        "--exclude-module", "PySide6.QtDesigner",
        "--exclude-module", "PySide6.QtHelp",
        "--exclude-module", "PySide6.QtTest",
        "--exclude-module", "PySide6.QtCharts",
        "--exclude-module", "PySide6.QtDataVisualization",
        "--exclude-module", "PySide6.QtRemoteObjects",
        "--exclude-module", "PySide6.QtScxml",
        "--exclude-module", "PySide6.QtStateMachine",
        "--exclude-module", "PySide6.QtTextToSpeech",
        "--exclude-module", "PySide6.QtVirtualKeyboard",
        "--exclude-module", "PySide6.QtWebChannel",
        "--exclude-module", "PySide6.QtWebSockets",
        "--exclude-module", "PySide6.QtXml",
        MAIN_SCRIPT
    ]

    print("Running command:", " ".join(pyinstaller_cmd))
    result = subprocess.run(pyinstaller_cmd, cwd=BASE_DIR)

    if result.returncode == 0:
        app_path = os.path.join(DIST_DIR, f"{APP_NAME}.app")
        print("\n✨ Build successful!")
        print(f"📦 Native macOS App Bundle generated at:\n   {app_path}")
    else:
        print("\n❌ Build failed with exit code:", result.returncode)


if __name__ == "__main__":
    build()
