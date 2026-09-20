import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

BASE_URL = "https://audio.iskcondesiretree.com/index.php?q=f&f=%2F02_-_ISKCON_Swamis%2FISKCON_Swamis_-_R_to_Y%2FHis_Holiness_Radhanath_Swami%2FLectures%2F00_-_Year_wise"

ROOT_SAVE_DIR = "Radhanath_Swami_Lectures"

visited = set()

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})


def sanitize(name):
    return unquote(name).replace("/", "_").strip()


def download_file(url, path):
    if os.path.exists(path):
        return
    try:
        r = session.get(url, stream=True, timeout=20)
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)
        print("Downloaded:", path)
    except Exception as e:
        print("Failed:", url)


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


def get_name(link):
    if is_mp3(link):
        return sanitize(link.split("/")[-1])
    part = link.split("f=")[-1]
    part = unquote(part)
    return sanitize(part.strip("/").split("/")[-1])


def is_child_link(parent_url, child_link):
    parent_part = parent_url.split("f=")[-1]
    child_part = child_link.split("f=")[-1]
    return child_part.startswith(parent_part) and child_part != parent_part


def crawl(url, current_path):
    if url in visited:
        return
    visited.add(url)

    print("\nVisiting:", url)

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
            download_file(full_url, filepath)

        elif "index.php?q=f&f=" in link:
            if not is_child_link(url, link):
                continue

            folder_name = get_name(link)
            new_path = os.path.join(current_path, folder_name)

            if len(new_path) > 200:
                continue

            print("Entering:", new_path)
            crawl(full_url, new_path)


crawl(BASE_URL, ROOT_SAVE_DIR)