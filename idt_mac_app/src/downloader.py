import os
import asyncio
import aiohttp
import time


class IDTDownloader:
    def __init__(self, concurrency: int = 10):
        self.concurrency = max(1, min(concurrency, 30))
        self.stop_event = asyncio.Event()
        self.pause_event = asyncio.Event()
        self.pause_event.set()

    def cancel(self):
        self.stop_event.set()

    def pause(self):
        self.pause_event.clear()

    def resume(self):
        self.pause_event.set()

    def is_paused(self) -> bool:
        return not self.pause_event.is_set()

    async def download_file(self, session, url: str, path: str, sem: asyncio.Semaphore, file_callback=None):
        if self.stop_event.is_set():
            return 0, "cancelled"

        while not self.pause_event.is_set():
            if self.stop_event.is_set():
                return 0, "cancelled"
            await asyncio.sleep(0.3)

        if os.path.exists(path):
            existing_size = os.path.getsize(path)
            if file_callback:
                file_callback(path, existing_size, existing_size, "skipped")
            return existing_size, "skipped"

        temp_path = path + ".part"
        dir_name = os.path.dirname(path)
        os.makedirs(dir_name, exist_ok=True)

        async with sem:
            for attempt in range(3):
                if self.stop_event.is_set():
                    return 0, "cancelled"

                try:
                    resume_header = {}
                    downloaded = 0
                    if os.path.exists(temp_path):
                        downloaded = os.path.getsize(temp_path)
                        resume_header = {"Range": f"bytes={downloaded}-"}

                    async with session.get(
                        url,
                        headers=resume_header,
                        timeout=aiohttp.ClientTimeout(total=None, sock_read=60)
                    ) as resp:
                        if resp.status in (200, 206):
                            content_len = int(resp.headers.get("Content-Length", 0))
                            total_size = downloaded + content_len if resp.status == 206 else content_len
                            mode = "ab" if resp.status == 206 else "wb"
                            if resp.status == 200:
                                downloaded = 0

                            with open(temp_path, mode) as f:
                                async for chunk in resp.content.iter_chunked(16384):
                                    while not self.pause_event.is_set():
                                        if self.stop_event.is_set():
                                            return downloaded, "cancelled"
                                        await asyncio.sleep(0.3)

                                    if self.stop_event.is_set():
                                        return downloaded, "cancelled"

                                    if not chunk:
                                        continue
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if file_callback:
                                        file_callback(path, downloaded, total_size, "downloading")

                            os.replace(temp_path, path)
                            if file_callback:
                                file_callback(path, downloaded, total_size, "completed")
                            return downloaded, "completed"
                        else:
                            await asyncio.sleep(1)
                except Exception:
                    await asyncio.sleep(1)

        if file_callback:
            file_callback(path, 0, 0, "failed")
        return 0, "failed"

    async def run(self, files_list, file_callback=None, overall_callback=None):
        sem = asyncio.Semaphore(self.concurrency)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        start_time = time.time()
        total_files = len(files_list)
        completed_files = 0
        total_downloaded_bytes = 0

        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = [
                self.download_file(session, url, path, sem, file_callback)
                for url, path in files_list
            ]

            for coro in asyncio.as_completed(tasks):
                if self.stop_event.is_set():
                    break

                bytes_dl, status = await coro
                completed_files += 1
                if status in ("completed", "downloading", "skipped"):
                    total_downloaded_bytes += bytes_dl

                elapsed = time.time() - start_time
                speed = total_downloaded_bytes / elapsed if elapsed > 0 else 0

                if overall_callback:
                    overall_callback(
                        completed_files,
                        total_files,
                        total_downloaded_bytes,
                        speed,
                        elapsed
                    )
