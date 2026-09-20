import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

BASE_URL = input("Enter folder URL: ").strip()

visited = set()
files = []

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})


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
    return child_part.startswith(parent_part) and child_part != parent_part


def crawl(url, current_path):
    if url in visited:
        return
    visited.add(url)

    os.makedirs(current_path, exist_ok=True)

    try:
        r = session.get(url, timeout=20)
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
            files.append((full_url, filepath))

        elif "index.php?q=f&f=" in link:
            if not is_child_link(url, link):
                continue

            folder_name = get_name(link)
            new_path = os.path.join(current_path, folder_name)
            crawl(full_url, new_path)


def download_file(task):
    url, path = task

    if os.path.exists(path):
        return os.path.getsize(path)

    try:
        r = session.get(url, stream=True, timeout=20)
        r.raise_for_status()

        total = 0
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)
                    total += len(chunk)

        return total

    except:
        return 0


# ROOT FOLDER NAME
ROOT_SAVE_DIR = sanitize(get_name(BASE_URL))
print("Root folder:", ROOT_SAVE_DIR)

# PHASE 1: SCAN
crawl(BASE_URL, ROOT_SAVE_DIR)

print(f"\nFiles found: {len(files)}")

# LOG FILES
with open("files_log.txt", "w") as f:
    for url, path in files:
        f.write(f"{url} -> {path}\n")

print("Starting download...\n")

# PHASE 2: DOWNLOAD WITH FILE-BASED PROGRESS
start_time = time.time()
downloaded_bytes = 0
completed_files = 0
total_files = len(files)

with ThreadPoolExecutor(max_workers=10) as executor:
    with tqdm(total=total_files, unit="file") as pbar:
        for size in executor.map(download_file, files):

            completed_files += 1
            downloaded_bytes += size
            pbar.update(1)

            elapsed = time.time() - start_time
            speed = downloaded_bytes / elapsed if elapsed > 0 else 0

            pbar.set_postfix({
                "files": f"{completed_files}/{total_files}",
                "size": f"{round(downloaded_bytes/(1024*1024),2)} MB",
                "speed": f"{round(speed/(1024*1024),2)} MB/s",
                "time": f"{round(elapsed/60,1)} min"
            })

print("\nDownload complete!")