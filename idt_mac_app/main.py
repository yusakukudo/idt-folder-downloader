import sys
import os

# Ensure src module is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.gui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("IDT Audio Downloader")
    app.setOrganizationName("Antigravity")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
