import os
import sys
import subprocess
from PySide6.QtCore import Qt, Slot, QUrl
from PySide6.QtGui import QIcon, QFont, QDesktopServices, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QProgressBar, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QSpinBox,
    QSplitter, QMessageBox, QGroupBox
)
from src.worker import IDTWorkerThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("IDT Audio Downloader — macOS")
        self.resize(980, 760)
        self.setMinimumSize(850, 640)

        self.worker = None
        self.file_row_map = {}
        self.default_output_dir = os.path.expanduser("~/Downloads/IDT_Downloads")
        self.is_dark_mode = True

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # ---------------- 1. Header Bar ----------------
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(18, 14, 18, 14)

        title_vbox = QVBoxLayout()
        header_title = QLabel("🎵 IDT Audio Downloader")
        header_title.setObjectName("headerTitle")

        header_subtitle = QLabel("High-Speed Asynchronous Downloader for ISKCON Desire Tree")
        header_subtitle.setObjectName("headerSubtitle")

        title_vbox.addWidget(header_title)
        title_vbox.addWidget(header_subtitle)
        title_vbox.setSpacing(2)

        # Theme Toggle Switch Button
        self.theme_btn = QPushButton("🌙 Dark Mode")
        self.theme_btn.setObjectName("themeToggleBtn")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)

        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        header_layout.addWidget(self.theme_btn)

        main_layout.addWidget(header_frame)

        # ---------------- 2. Configuration Panel ----------------
        config_group = QGroupBox("Download Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(12)
        config_layout.setContentsMargins(16, 16, 16, 16)

        # URL Input Row
        url_layout = QHBoxLayout()
        url_label = QLabel("IDT Folder URL:")
        url_label.setFixedWidth(120)
        url_label.setObjectName("fieldLabel")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste IDT URL (e.g., audio.iskcondesiretree.com/index.php?q=f&f=...)")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)

        # Output Folder Row
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Save Location:")
        dir_label.setFixedWidth(120)
        dir_label.setObjectName("fieldLabel")
        self.dir_input = QLineEdit(self.default_output_dir)
        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("browseBtn")
        browse_btn.setFixedWidth(100)
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(self._on_browse_folder)
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(browse_btn)

        # Concurrency & Controls Row
        settings_layout = QHBoxLayout()
        conc_label = QLabel("Parallel Threads:")
        conc_label.setObjectName("fieldLabel")
        self.conc_spinner = QSpinBox()
        self.conc_spinner.setRange(1, 20)
        self.conc_spinner.setValue(10)
        self.conc_spinner.setFixedWidth(85)
        self.conc_spinner.setObjectName("customSpinBox")

        settings_layout.addWidget(conc_label)
        settings_layout.addWidget(self.conc_spinner)
        settings_layout.addStretch()

        config_layout.addLayout(url_layout)
        config_layout.addLayout(dir_layout)
        config_layout.addLayout(settings_layout)

        main_layout.addWidget(config_group)

        # ---------------- 3. Action Button Bar ----------------
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)

        self.start_btn = QPushButton("▶  Start Download")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self._on_start_clicked)

        self.pause_btn = QPushButton("⏸  Pause")
        self.pause_btn.setObjectName("pauseBtn")
        self.pause_btn.setCursor(Qt.PointingHandCursor)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self._on_pause_clicked)

        self.cancel_btn = QPushButton("⏹  Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)

        self.open_folder_btn = QPushButton("📁 Open Destination")
        self.open_folder_btn.setObjectName("openFolderBtn")
        self.open_folder_btn.setCursor(Qt.PointingHandCursor)
        self.open_folder_btn.clicked.connect(self._on_open_folder_clicked)

        btn_bar.addWidget(self.start_btn)
        btn_bar.addWidget(self.pause_btn)
        btn_bar.addWidget(self.cancel_btn)
        btn_bar.addStretch()
        btn_bar.addWidget(self.open_folder_btn)

        main_layout.addLayout(btn_bar)

        # ---------------- 4. Dashboard & Metrics Cards ----------------
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.card_files = self._create_card("FILES DISCOVERED", "0 / 0", "Completed audio files")
        self.card_size = self._create_card("DOWNLOADED SIZE", "0.0 MB", "Total data transferred")
        self.card_speed = self._create_card("TRANSFER SPEED", "0.0 MB/s", "Current bandwidth")
        self.card_time = self._create_card("ELAPSED TIME", "00:00", "Total duration")

        cards_layout.addWidget(self.card_files["frame"])
        cards_layout.addWidget(self.card_size["frame"])
        cards_layout.addWidget(self.card_speed["frame"])
        cards_layout.addWidget(self.card_time["frame"])

        main_layout.addLayout(cards_layout)

        # Main Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Ready (%p%)")
        main_layout.addWidget(self.progress_bar)

        # ---------------- 5. Log & File Status Table ----------------
        self.splitter = QSplitter(Qt.Vertical)

        # File Table Container
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(6)

        table_header = QHBoxLayout()
        table_title = QLabel("📄 Audio Files Queue")
        table_title.setObjectName("sectionHeaderTitle")
        table_header.addWidget(table_title)
        table_header.addStretch()

        self.toggle_log_btn = QPushButton("📋 Hide Live Logs")
        self.toggle_log_btn.setObjectName("toggleLogBtn")
        self.toggle_log_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_log_btn.clicked.connect(self._toggle_logs)
        table_header.addWidget(self.toggle_log_btn)

        table_layout.addLayout(table_header)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Audio File", "Size", "Status", "Progress"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        table_layout.addWidget(self.table)

        self.splitter.addWidget(table_container)

        # Log Console Container
        self.log_container = QWidget()
        log_layout = QVBoxLayout(self.log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(6)

        log_title = QLabel("💻 Live System Diagnostics Log")
        log_title.setObjectName("sectionHeaderTitle")
        log_layout.addWidget(log_title)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setPlaceholderText("Live logs and diagnostic output will stream here...")
        log_layout.addWidget(self.log_console)

        self.splitter.addWidget(self.log_container)

        self.splitter.setSizes([340, 140])
        main_layout.addWidget(self.splitter, stretch=1)

    def _create_card(self, title: str, initial_val: str, subtitle: str) -> dict:
        frame = QFrame()
        frame.setObjectName("metricCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(3)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("cardTitle")

        lbl_val = QLabel(initial_val)
        lbl_val.setObjectName("cardValue")

        lbl_sub = QLabel(subtitle)
        lbl_sub.setObjectName("cardSubtitle")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_sub)

        return {"frame": frame, "val": lbl_val, "sub": lbl_sub}

    def _toggle_logs(self):
        is_visible = self.log_container.isVisible()
        self.log_container.setVisible(not is_visible)
        if is_visible:
            self.toggle_log_btn.setText("📋 Show Live Logs")
        else:
            self.toggle_log_btn.setText("📋 Hide Live Logs")
            self.splitter.setSizes([340, 140])

    def _toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.theme_btn.setText("🌙 Dark Mode" if self.is_dark_mode else "☀️ Light Mode")
        self._apply_theme()

    def _apply_theme(self):
        if self.is_dark_mode:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #0F172A;
                }
                QWidget {
                    color: #F8FAFC;
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
                    font-size: 13px;
                }
                QFrame#headerFrame {
                    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
                    border-radius: 12px;
                    border: 1px solid #334155;
                }
                QLabel#headerTitle {
                    font-size: 21px;
                    font-weight: 700;
                    color: #38BDF8;
                }
                QLabel#headerSubtitle {
                    font-size: 12px;
                    color: #94A3B8;
                }
                QLabel#sectionHeaderTitle {
                    font-size: 13px;
                    font-weight: 700;
                    color: #CBD5E1;
                }
                QPushButton#themeToggleBtn, QPushButton#toggleLogBtn {
                    background-color: #1E293B;
                    border: 1px solid #334155;
                    border-radius: 8px;
                    padding: 6px 14px;
                    font-weight: 600;
                    color: #F8FAFC;
                }
                QPushButton#themeToggleBtn:hover, QPushButton#toggleLogBtn:hover {
                    background-color: #334155;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #334155;
                    border-radius: 10px;
                    margin-top: 8px;
                    padding-top: 14px;
                    background-color: #1E293B;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 14px;
                    padding: 0 6px;
                    color: #38BDF8;
                }
                QLabel#fieldLabel {
                    font-weight: 600;
                    color: #CBD5E1;
                }
                QLineEdit {
                    background-color: #0F172A;
                    border: 1px solid #334155;
                    border-radius: 7px;
                    padding: 7px 12px;
                    color: #F8FAFC;
                }
                QLineEdit:focus {
                    border: 1px solid #38BDF8;
                }
                QSpinBox {
                    background-color: #0F172A;
                    border: 1px solid #334155;
                    border-radius: 7px;
                    padding: 5px 8px;
                    color: #F8FAFC;
                    font-weight: 600;
                }
                QSpinBox:focus {
                    border: 1px solid #38BDF8;
                }
                QSpinBox::up-button {
                    subcontrol-origin: border;
                    subcontrol-position: top right;
                    width: 22px;
                    border-left: 1px solid #334155;
                    border-bottom: 1px solid #334155;
                    border-top-right-radius: 6px;
                    background-color: #1E293B;
                }
                QSpinBox::up-button:hover {
                    background-color: #334155;
                }
                QSpinBox::up-arrow {
                    width: 0;
                    height: 0;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-bottom: 6px solid #38BDF8;
                }
                QSpinBox::down-button {
                    subcontrol-origin: border;
                    subcontrol-position: bottom right;
                    width: 22px;
                    border-left: 1px solid #334155;
                    border-bottom-right-radius: 6px;
                    background-color: #1E293B;
                }
                QSpinBox::down-button:hover {
                    background-color: #334155;
                }
                QSpinBox::down-arrow {
                    width: 0;
                    height: 0;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 6px solid #38BDF8;
                }
                QPushButton {
                    background-color: #334155;
                    border: none;
                    border-radius: 7px;
                    padding: 8px 18px;
                    font-weight: 600;
                    color: #F8FAFC;
                }
                QPushButton:hover {
                    background-color: #475569;
                }
                QPushButton#startBtn {
                    background-color: #0284C7;
                }
                QPushButton#startBtn:hover {
                    background-color: #0369A1;
                }
                QPushButton#pauseBtn {
                    background-color: #D97706;
                }
                QPushButton#pauseBtn:hover {
                    background-color: #B45309;
                }
                QPushButton#cancelBtn {
                    background-color: #DC2626;
                }
                QPushButton#cancelBtn:hover {
                    background-color: #B91C1C;
                }
                QPushButton#openFolderBtn {
                    background-color: #059669;
                }
                QPushButton#openFolderBtn:hover {
                    background-color: #047857;
                }
                QFrame#metricCard {
                    background-color: #1E293B;
                    border: 1px solid #334155;
                    border-radius: 10px;
                }
                QLabel#cardTitle {
                    font-size: 11px;
                    color: #94A3B8;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                }
                QLabel#cardValue {
                    font-size: 20px;
                    font-weight: 700;
                    color: #38BDF8;
                }
                QLabel#cardSubtitle {
                    font-size: 11px;
                    color: #64748B;
                }
                QProgressBar {
                    border: 1px solid #334155;
                    border-radius: 7px;
                    text-align: center;
                    background-color: #0F172A;
                    color: #F8FAFC;
                    font-weight: 600;
                    height: 24px;
                }
                QProgressBar::chunk {
                    background: linear-gradient(90deg, #0EA5E9 0%, #10B981 100%);
                    border-radius: 6px;
                }
                QTableWidget {
                    background-color: #0F172A;
                    border: 1px solid #334155;
                    border-radius: 8px;
                    gridline-color: #1E293B;
                    alternate-background-color: #1E293B;
                }
                QHeaderView::section {
                    background-color: #1E293B;
                    padding: 8px;
                    border: none;
                    font-weight: bold;
                    color: #94A3B8;
                }
                QTextEdit {
                    background-color: #0F172A;
                    border: 1px solid #334155;
                    border-radius: 8px;
                    color: #38BDF8;
                    font-family: "SF Mono", Menlo, Monaco, Consolas, monospace;
                    font-size: 11px;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #F1F5F9;
                }
                QWidget {
                    color: #0F172A;
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
                    font-size: 13px;
                }
                QFrame#headerFrame {
                    background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
                    border-radius: 12px;
                    border: 1px solid #E2E8F0;
                }
                QLabel#headerTitle {
                    font-size: 21px;
                    font-weight: 700;
                    color: #0284C7;
                }
                QLabel#headerSubtitle {
                    font-size: 12px;
                    color: #64748B;
                }
                QLabel#sectionHeaderTitle {
                    font-size: 13px;
                    font-weight: 700;
                    color: #334155;
                }
                QPushButton#themeToggleBtn, QPushButton#toggleLogBtn {
                    background-color: #FFFFFF;
                    border: 1px solid #CBD5E1;
                    border-radius: 8px;
                    padding: 6px 14px;
                    font-weight: 600;
                    color: #0F172A;
                }
                QPushButton#themeToggleBtn:hover, QPushButton#toggleLogBtn:hover {
                    background-color: #F1F5F9;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #E2E8F0;
                    border-radius: 10px;
                    margin-top: 8px;
                    padding-top: 14px;
                    background-color: #FFFFFF;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 14px;
                    padding: 0 6px;
                    color: #0284C7;
                }
                QLabel#fieldLabel {
                    font-weight: 600;
                    color: #334155;
                }
                QLineEdit {
                    background-color: #F8FAFC;
                    border: 1px solid #CBD5E1;
                    border-radius: 7px;
                    padding: 7px 12px;
                    color: #0F172A;
                }
                QLineEdit:focus {
                    border: 1px solid #0284C7;
                }
                QSpinBox {
                    background-color: #F8FAFC;
                    border: 1px solid #CBD5E1;
                    border-radius: 7px;
                    padding: 5px 8px;
                    color: #0F172A;
                    font-weight: 600;
                }
                QSpinBox:focus {
                    border: 1px solid #0284C7;
                }
                QSpinBox::up-button {
                    subcontrol-origin: border;
                    subcontrol-position: top right;
                    width: 22px;
                    border-left: 1px solid #CBD5E1;
                    border-bottom: 1px solid #CBD5E1;
                    border-top-right-radius: 6px;
                    background-color: #E2E8F0;
                }
                QSpinBox::up-button:hover {
                    background-color: #CBD5E1;
                }
                QSpinBox::up-arrow {
                    width: 0;
                    height: 0;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-bottom: 6px solid #0284C7;
                }
                QSpinBox::down-button {
                    subcontrol-origin: border;
                    subcontrol-position: bottom right;
                    width: 22px;
                    border-left: 1px solid #CBD5E1;
                    border-bottom-right-radius: 6px;
                    background-color: #E2E8F0;
                }
                QSpinBox::down-button:hover {
                    background-color: #CBD5E1;
                }
                QSpinBox::down-arrow {
                    width: 0;
                    height: 0;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 6px solid #0284C7;
                }
                QPushButton {
                    background-color: #E2E8F0;
                    border: none;
                    border-radius: 7px;
                    padding: 8px 18px;
                    font-weight: 600;
                    color: #0F172A;
                }
                QPushButton:hover {
                    background-color: #CBD5E1;
                }
                QPushButton#startBtn {
                    background-color: #0284C7;
                    color: #FFFFFF;
                }
                QPushButton#startBtn:hover {
                    background-color: #0369A1;
                }
                QPushButton#pauseBtn {
                    background-color: #D97706;
                    color: #FFFFFF;
                }
                QPushButton#pauseBtn:hover {
                    background-color: #B45309;
                }
                QPushButton#cancelBtn {
                    background-color: #DC2626;
                    color: #FFFFFF;
                }
                QPushButton#cancelBtn:hover {
                    background-color: #B91C1C;
                }
                QPushButton#openFolderBtn {
                    background-color: #059669;
                    color: #FFFFFF;
                }
                QPushButton#openFolderBtn:hover {
                    background-color: #047857;
                }
                QFrame#metricCard {
                    background-color: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 10px;
                }
                QLabel#cardTitle {
                    font-size: 11px;
                    color: #64748B;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                }
                QLabel#cardValue {
                    font-size: 20px;
                    font-weight: 700;
                    color: #0284C7;
                }
                QLabel#cardSubtitle {
                    font-size: 11px;
                    color: #94A3B8;
                }
                QProgressBar {
                    border: 1px solid #CBD5E1;
                    border-radius: 7px;
                    text-align: center;
                    background-color: #FFFFFF;
                    color: #0F172A;
                    font-weight: 600;
                    height: 24px;
                }
                QProgressBar::chunk {
                    background: linear-gradient(90deg, #0284C7 0%, #059669 100%);
                    border-radius: 6px;
                }
                QTableWidget {
                    background-color: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                    gridline-color: #F1F5F9;
                    alternate-background-color: #F8FAFC;
                }
                QHeaderView::section {
                    background-color: #F1F5F9;
                    padding: 8px;
                    border: none;
                    font-weight: bold;
                    color: #475569;
                }
                QTextEdit {
                    background-color: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                    color: #0284C7;
                    font-family: "SF Mono", Menlo, Monaco, Consolas, monospace;
                    font-size: 11px;
                }
            """)

    @Slot()
    def _on_browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Directory", self.dir_input.text())
        if folder:
            self.dir_input.setText(folder)

    @Slot()
    def _on_start_clicked(self):
        url = self.url_input.text().strip()
        if url and not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            self.url_input.setText(url)

        output_dir = self.dir_input.text().strip()
        concurrency = self.conc_spinner.value()

        if not url.startswith("http://") and not url.startswith("https://"):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid URL (e.g. audio.iskcondesiretree.com/...).")
            return

        if not output_dir:
            QMessageBox.warning(self, "Invalid Path", "Please select a target download folder.")
            return

        self.table.setRowCount(0)
        self.file_row_map.clear()
        self.log_console.clear()

        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Scanning website structure...")

        self.worker = IDTWorkerThread(url=url, output_dir=output_dir, concurrency=concurrency)
        self.worker.crawl_progress.connect(self._on_crawl_progress)
        self.worker.crawl_finished.connect(self._on_crawl_finished)
        self.worker.file_progress.connect(self._on_file_progress)
        self.worker.overall_progress.connect(self._on_overall_progress)
        self.worker.finished_signal.connect(self._on_worker_finished)
        self.worker.log_signal.connect(self._log)
        self.worker.start()

    @Slot()
    def _on_pause_clicked(self):
        if not self.worker:
            return

        if self.worker.is_paused():
            self.worker.resume()
            self.pause_btn.setText("⏸  Pause")
            self._log("▶ Resumed downloading.")
        else:
            self.worker.pause()
            self.pause_btn.setText("▶  Resume")
            self._log("⏸ Download paused.")

    @Slot()
    def _on_cancel_clicked(self):
        if self.worker:
            self.worker.cancel()
            self._log("🛑 Cancelling download...")
            self.cancel_btn.setEnabled(False)

    @Slot()
    def _on_open_folder_clicked(self):
        folder = self.dir_input.text().strip()
        if os.path.exists(folder):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        else:
            os.makedirs(folder, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    @Slot(int, int, str)
    def _on_crawl_progress(self, visited, files_count, current_file):
        self.card_files["val"].setText(f"Found {files_count}")
        self._log(f"Scanning: {visited} pages scanned | {files_count} audio files discovered")

    @Slot(str, list)
    def _on_crawl_finished(self, target_dir, files_list):
        self.dir_input.setText(target_dir)
        self.table.setRowCount(len(files_list))

        for idx, (url, path) in enumerate(files_list):
            filename = os.path.basename(path)
            self.file_row_map[path] = idx

            self.table.setItem(idx, 0, QTableWidgetItem(filename))
            self.table.setItem(idx, 1, QTableWidgetItem("Waiting..."))
            self.table.setItem(idx, 2, QTableWidgetItem("Queued"))
            self.table.setItem(idx, 3, QTableWidgetItem("0%"))

    @Slot(str, int, int, str)
    def _on_file_progress(self, path, downloaded, total, status):
        row = self.file_row_map.get(path)
        if row is None:
            return

        size_mb = f"{downloaded / (1024*1024):.2f} MB"
        if total > 0:
            pct = int((downloaded / total) * 100)
            size_mb = f"{downloaded / (1024*1024):.2f} / {total / (1024*1024):.2f} MB"
        else:
            pct = 0

        self.table.setItem(row, 1, QTableWidgetItem(size_mb))
        self.table.setItem(row, 2, QTableWidgetItem(status.capitalize()))
        self.table.setItem(row, 3, QTableWidgetItem(f"{pct}%"))

    @Slot(int, int, int, float, float)
    def _on_overall_progress(self, completed, total, total_bytes, speed, elapsed):
        pct = int((completed / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)
        self.progress_bar.setFormat(f"Downloading: {completed}/{total} files ({pct}%)")

        self.card_files["val"].setText(f"{completed} / {total}")
        self.card_size["val"].setText(f"{total_bytes / (1024*1024):.1f} MB")
        self.card_speed["val"].setText(f"{speed / (1024*1024):.2f} MB/s")

        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        self.card_time["val"].setText(f"{mins:02d}:{secs:02d}")

    @Slot(bool, str)
    def _on_worker_finished(self, success, message):
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.pause_btn.setText("⏸  Pause")

        if success:
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("Complete! ✅")
            self._log(f"✅ {message}")
            QMessageBox.information(self, "Download Complete", message)
        else:
            self.progress_bar.setFormat("Stopped 🛑")
            self._log(f"🛑 {message}")
            QMessageBox.warning(self, "Status", message)

    def _log(self, text: str):
        self.log_console.append(text)
