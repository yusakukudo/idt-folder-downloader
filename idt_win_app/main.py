import sys
import os

# Ensure src package is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.gui import MainWindowWin


def main():
    # Enable High DPI scaling on Windows
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("IDT Audio Downloader Windows")
    app.setOrganizationName("Antigravity")

    window = MainWindowWin()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
