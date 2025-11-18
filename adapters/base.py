from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Protocol
from urllib.parse import urlparse


@dataclass
class ParseResult:
    product_urls: List[str]
    next_links: List[str]


class SiteAdapter(Protocol):
    """
    Interface for site-specific parsing logic.
    Keep this small and stable so adapters rarely break across upgrades.
    """

    name: str
    domains: List[str]  # e.g. ["example.com", "www.example.com"]

    def matches(self, url: str) -> bool:
        """Return True if this adapter should handle the given URL."""
        ...

    def parse(self, url: str, html: str) -> ParseResult:
        """
        Given page URL and HTML, return product URLs and candidate next links.
        Engine owns the HTTP, queueing, and depth control.
        """
        ...


def domain_of(url: str) -> str:
    return urlparse(url).netloc
