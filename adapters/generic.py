from __future__ import annotations

from typing import List
from .base import SiteAdapter, ParseResult, ProductInfo
from ..utils.parsing import extract_links, is_product_like, extract_product_metadata


class GenericAdapter:
    """
    A generic, domain-agnostic adapter that uses simple heuristics.
    Acts as a safe fallback when no specific adapter matches a URL.
    """
    name = "generic"
    domains: List[str] = []  # matches any

    def matches(self, url: str) -> bool:  # pragma: no cover - trivial
        return True

    def parse(self, url: str, html: str) -> ParseResult:
        links = extract_links(html, base_url=url)
        product = [u for u in links if is_product_like(u)]
        products = extract_product_metadata(html, url)
        if not products:
            products = [ProductInfo(url=u) for u in product]
        # For the generic adapter, next links are simply all extracted links.
        return ParseResult(product_urls=product, next_links=list(links), products=products)
