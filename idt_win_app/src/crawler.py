import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote


def sanitize_win(name: str) -> str:
    """Sanitizes names specifically for Windows filesystem reserved chars (<>:\"/\\|?*)."""
    if not name:
        return "IDT_Folder"
    cleaned = unquote(name)
    # Replace illegal Windows characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', cleaned).strip()
    return cleaned if cleaned else "IDT_Folder"


def extract_link(tag) -> str:
    href = tag.get("href")
    onclick = tag.get("onclick")

    if href and "index.php?q=f&f=" in href:
        return href

    if onclick:
        match = re.search(r"index\.php\?q=f&f=[^']+", onclick)
        if match:
            return match.group(0)

    if href and href.lower().endswith(".mp3"):
        return href

    return None


def is_mp3(link: str) -> bool:
    return link.lower().endswith(".mp3") if link else False


def get_path_part(url: str) -> str:
    return url.split("f=")[-1] if "f=" in url else url


def get_name(link: str) -> str:
    if is_mp3(link):
        return sanitize_win(link.split("/")[-1])
    part = link.split("f=")[-1] if "f=" in link else link
    part = unquote(part)
    return sanitize_win(part.strip("/").split("/")[-1])


def is_child_link(parent_url: str, child_link: str) -> bool:
    parent_part = get_path_part(parent_url)
    child_part = get_path_part(child_link)
    return child_part.startswith(parent_part + "%2F") or child_part.startswith(parent_part + "/")


class IDTCrawlerWin:
    def __init__(self, base_url: str, output_root: str, progress_callback=None, cancel_check=None):
        self.base_url = base_url
        self.output_root = output_root
        self.progress_callback = progress_callback
        self.cancel_check = cancel_check
        self.visited = set()
        self.files = set()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def crawl(self):
        root_folder_name = sanitize_win(get_name(self.base_url))
        target_dir = os.path.join(self.output_root, root_folder_name)
        self._crawl(self.base_url, target_dir)
        return target_dir, sorted(list(self.files))

    def _crawl(self, url: str, current_path: str):
        if self.cancel_check and self.cancel_check():
            return

        if url in self.visited:
            return
        self.visited.add(url)

        os.makedirs(current_path, exist_ok=True)

        try:
            resp = self.session.get(url, timeout=(5, 15))
            resp.raise_for_status()
        except Exception:
            return

        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup.find_all("a"):
            if self.cancel_check and self.cancel_check():
                return

            link = extract_link(tag)
            if not link:
                continue

            full_url = urljoin(url, link)

            if is_mp3(link):
                filename = get_name(link)
                filepath = os.path.join(current_path, filename)
                self.files.add((full_url, filepath))
                if self.progress_callback:
                    self.progress_callback(len(self.visited), len(self.files), filepath)

            elif "index.php?q=f&f=" in link:
                if not is_child_link(url, link):
                    continue

                folder_name = get_name(link)
                new_path = os.path.join(current_path, folder_name)
                self._crawl(full_url, new_path)
