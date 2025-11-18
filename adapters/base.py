from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol
from urllib.parse import urlparse


@dataclass
class ParseResult:
    product_urls: List[str]
    next_links: List[str]
    products: List["ProductInfo"] = field(default_factory=list)


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


@dataclass
class ProductInfo:
    """Structured metadata for a discovered product."""

    url: str
    title: Optional[str] = None
    price: Optional[str] = None
    currency: Optional[str] = None
    availability: Optional[str] = None
    seller: Optional[str] = None
    category: Optional[str] = None
    item_type: Optional[str] = None
    sales: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "url": self.url,
            "title": self.title,
            "price": self.price,
            "currency": self.currency,
            "availability": self.availability,
            "seller": self.seller,
            "category": self.category,
            "type": self.item_type,
            "sales": self.sales,
        }
        # Drop unset keys for a cleaner export while retaining extras for future-proofing.
        clean = {k: v for k, v in data.items() if v is not None}
        if self.extra:
            clean["extra"] = self.extra
        return clean

    def matches_keywords(self, keywords: List[str]) -> bool:
        if not keywords:
            return True
        haystack = " ".join(filter(None, [self.title, self.category, self.item_type, self.url]))
        haystack_lower = haystack.lower()
        return any(kw.lower() in haystack_lower for kw in keywords)
