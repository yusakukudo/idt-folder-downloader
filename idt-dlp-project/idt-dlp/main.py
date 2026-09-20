import os
import re
import time
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from tqdm import tqdm

stop_event = asyncio.Event()


def sanitize(name):
    return unquote(name).replace("/", "_").strip()


def extract_link(tag):
    href = tag.get("href")
    onclick = tag.get("onclick")

    if href and "index.php?q=f&f=" in href:
        return href

    if onclick:
        match = re.search(r"index\.php\?q=f&f=[^']+", onclick)
        if match:
            return match.group(0)

    if href and href.endswith(".mp3"):
        return href

    return None


def is_mp3(link):
    return link.lower().endswith(".mp3")


def get_path_part(url):
    return url.split("f=")[-1]


def get_name(link):
    if is_mp3(link):
        return sanitize(link.split("/")[-1])
    part = link.split("f=")[-1]
    part = unquote(part)
    return sanitize(part.strip("/").split("/")[-1])


def is_child_link(parent_url, child_link):
    parent_part = get_path_part(parent_url)
    child_part = get_path_part(child_link)
    return child_part.startswith(parent_part + "%2F")


def crawl(BASE_URL):
    import requests

    visited = set()
    files = set()

    session = requests.Session()

    def _crawl(url, current_path):
        if url in visited:
            return
        visited.add(url)

        os.makedirs(current_path, exist_ok=True)

        try:
            r = session.get(url, timeout=(5, 15))
            r.raise_for_status()
        except:
            return

        soup = BeautifulSoup(r.text, "html.parser")

        for tag in soup.find_all("a"):
            link = extract_link(tag)
            if not link:
                continue

            full_url = urljoin(url, link)

            if is_mp3(link):
                filename = get_name(link)
                filepath = os.path.join(current_path, filename)
                files.add((full_url, filepath))

            elif "index.php?q=f&f=" in link:
                if not is_child_link(url, link):
                    continue

                folder_name = get_name(link)
                new_path = os.path.join(current_path, folder_name)
                _crawl(full_url, new_path)

    root = sanitize(get_name(BASE_URL))
    print(f"\n📁 Root folder: {root}")

    _crawl(BASE_URL, root)

    return sorted(list(files))


async def download_file(session, url, path, sem):
    if stop_event.is_set():
        return 0

    if os.path.exists(path):
        return os.path.getsize(path)

    temp_path = path + ".part"

    async with sem:
        for _ in range(3):
            if stop_event.is_set():
                return 0

            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=None, sock_read=60)
                ) as resp:
                    resp.raise_for_status()

                    total = 0

                    with open(temp_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            if stop_event.is_set():
                                return total

                            if not chunk:
                                continue

                            f.write(chunk)
                            total += len(chunk)

                os.replace(temp_path, path)
                return total

            except Exception as e:
                await asyncio.sleep(1)

    return 0

async def run_async(BASE_URL):
    files_list = crawl(BASE_URL)
    print(f"📦 Files found: {len(files_list)}")

    print("\nStarting download...\n")

    start_time = time.time()
    downloaded_bytes = 0
    completed_files = 0
    total_files = len(files_list)

    speed_samples = []

    sem = asyncio.Semaphore(10)  # 🔥 concurrency control

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:

        tasks = [
            download_file(session, url, path, sem)
            for url, path in files_list
        ]

        with tqdm(total=total_files, unit="file") as pbar:
            for coro in asyncio.as_completed(tasks):

                if stop_event.is_set():
                    break

                size = await coro

                completed_files += 1
                downloaded_bytes += size
                pbar.update(1)

                elapsed = time.time() - start_time

                current_speed = downloaded_bytes / elapsed if elapsed > 0 else 0
                speed_samples.append(current_speed)

                if len(speed_samples) > 5:
                    speed_samples.pop(0)

                speed = sum(speed_samples) / len(speed_samples)

                pbar.set_postfix({
                    "files": f"{completed_files}/{total_files}",
                    "size": f"{round(downloaded_bytes/(1024*1024),2)} MB",
                    "speed": f"{round(speed/(1024*1024),2)} MB/s",
                    "time": f"{round(elapsed/60,1)} min"
                })


def main():
    import multiprocessing
    multiprocessing.freeze_support()
    import sys

    print("\n📥 IDT-DLP Async Downloader\n")

    if len(sys.argv) < 2:
        url = input("Enter URL: ").strip()
    else:
        url = sys.argv[1]

    if not url.startswith("http"):
        print("❌ Invalid URL")
        return

    try:
        asyncio.run(run_async(url))
    except KeyboardInterrupt:
        print("\n⛔ Stopping immediately...")
        stop_event.set()

    print("\n🛑 Stopped." if stop_event.is_set() else "\n✅ Done.")


if __name__ == "__main__":
    main()