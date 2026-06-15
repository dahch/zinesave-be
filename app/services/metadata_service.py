from datetime import datetime, timezone
from urllib.parse import urlparse

from bs4 import BeautifulSoup


def extract_metadata(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    def meta(name=None, prop=None):
        if name:
            tag = soup.find("meta", attrs={"name": name})
        else:
            tag = soup.find("meta", attrs={"property": prop})
        return tag["content"].strip() if tag and tag.get("content") else None
    
    # 1. Title Strategy
    title = (
        meta(prop="og:title")
        or meta(name="twitter:title")
        or meta(name="title")
        or (soup.title.text.strip() if soup.title else None)
    )

    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
    
    if not title:
        title = "Untitled Article"

    # 2. Author Strategy
    author = (
        meta(name="author")
        or meta(prop="article:author")
        or meta(name="twitter:creator")
        or meta(prop="og:site_name")
        or urlparse(url).netloc
    )

    lang = soup.html.get("lang") if soup.html else "en"

    # 3. Date Strategy
    published = (
        meta(prop="article:published_time")
        or meta(prop="og:published_time")
        or meta(name="date")
        or meta(name="publish-date")
        or datetime.now(timezone.utc).isoformat()
    )

    return {
        "title": title,
        "author": author,
        "language": lang or "en",
        "published": published,
        "publisher": meta(prop="og:site_name") or "DahchApp",
        "source": urlparse(url).netloc
    }