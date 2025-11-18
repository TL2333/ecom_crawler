from __future__ import annotations

from typing import Iterable, List, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup


def normalize_url(url: str) -> str:
    """
    Normalize URL by removing fragments, resolving dot segments, etc.
    """
    parts = list(urlparse(url))
    parts[5] = ""  # strip fragment
    # Optionally we could normalize query params here.
    return urlunparse(parts)


def extract_links(html: str, base_url: str) -> Set[str]:
    """
    Extract absolute links from an HTML string.
    """
    soup = BeautifulSoup(html, "html.parser")
    out: Set[str] = set()
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue
        out.add(normalize_url(urljoin(base_url, href)))
    return out


def is_product_like(url: str) -> bool:
    """
    A simple, extensible heuristic to detect product pages.
    Upgrade by adding regexes or ML classifiers later.
    """
    path = urlparse(url).path.lower()
    return any(p in path for p in ("/product", "/products", "/p/", "/item", "/sku", "/shop/"))

