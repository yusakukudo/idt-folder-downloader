import asyncio
from PySide6.QtCore import QThread, Signal
from src.crawler import IDTCrawlerWin
from src.downloader import IDTDownloaderWin


class IDTWorkerThreadWin(QThread):
    crawl_progress = Signal(int, int, str)
    crawl_finished = Signal(str, list)
    file_progress = Signal(str, int, int, str)
    overall_progress = Signal(int, int, int, float, float)
    finished_signal = Signal(bool, str)
    log_signal = Signal(str)

    def __init__(self, url: str, output_dir: str, concurrency: int = 10, parent=None):
        super().__init__(parent)
        self.url = url
        self.output_dir = output_dir
        self.concurrency = concurrency
        self.downloader = None
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True
        if self.downloader:
            self.downloader.cancel()

    def pause(self):
        if self.downloader:
            self.downloader.pause()

    def resume(self):
        if self.downloader:
            self.downloader.resume()

    def is_paused(self) -> bool:
        return self.downloader.is_paused() if self.downloader else False

    def run(self):
        try:
            self.log_signal.emit("🔍 Phase 1: Scanning IDT website hierarchy...")

            crawler = IDTCrawlerWin(
                base_url=self.url,
                output_root=self.output_dir,
                progress_callback=self._on_crawl_progress,
                cancel_check=lambda: self._is_cancelled
            )

            target_dir, files_list = crawler.crawl()

            if self._is_cancelled:
                self.finished_signal.emit(False, "Cancelled during scanning.")
                return

            self.crawl_finished.emit(target_dir, files_list)
            self.log_signal.emit(f"📦 Discovery complete: {len(files_list)} audio files found.")

            if not files_list:
                self.finished_signal.emit(True, "No files found to download.")
                return

            self.log_signal.emit(f"⚡ Phase 2: Starting async download ({self.concurrency} workers)...")
            self.downloader = IDTDownloaderWin(concurrency=self.concurrency)

            if self._is_cancelled:
                self.downloader.cancel()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.downloader.run(
                    files_list,
                    file_callback=self._on_file_progress,
                    overall_callback=self._on_overall_progress
                )
            )
            loop.close()

            if self._is_cancelled:
                self.finished_signal.emit(False, "Download cancelled by user.")
            else:
                self.finished_signal.emit(True, "All downloads completed successfully!")

        except Exception as e:
            self.finished_signal.emit(False, f"Error: {str(e)}")

    def _on_crawl_progress(self, visited: int, files_count: int, current_file: str):
        self.crawl_progress.emit(visited, files_count, current_file)

    def _on_file_progress(self, path: str, bytes_dl: int, total_bytes: int, status: str):
        self.file_progress.emit(path, bytes_dl, total_bytes, status)

    def _on_overall_progress(self, completed: int, total: int, total_bytes: int, speed: float, elapsed: float):
        self.overall_progress.emit(completed, total, total_bytes, speed, elapsed)
