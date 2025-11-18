from __future__ import annotations

from typing import Iterable, List, Set, Tuple, Any
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup
import json

from ..adapters.base import ProductInfo


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


def extract_product_metadata(html: str, base_url: str) -> List[ProductInfo]:
    """Extract structured product details from JSON-LD and microdata blocks."""

    soup = BeautifulSoup(html, "html.parser")
    products: List[ProductInfo] = []

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        payload = script.string or ""
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue

        for item in _iter_jsonld_items(data):
            product = _product_from_jsonld(item, base_url)
            if product:
                products.append(product)

    if products:
        return products

    # Fallback: attempt to gather OpenGraph/meta hints for pages lacking JSON-LD.
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_price = soup.find("meta", attrs={"property": "product:price:amount"})
    og_currency = soup.find("meta", attrs={"property": "product:price:currency"})
    og_availability = soup.find("meta", attrs={"property": "product:availability"})
    if og_title:
        products.append(
            ProductInfo(
                url=base_url,
                title=og_title.get("content"),
                price=og_price.get("content") if og_price else None,
                currency=og_currency.get("content") if og_currency else None,
                availability=og_availability.get("content") if og_availability else None,
            )
        )

    return products


def _iter_jsonld_items(data: Any) -> Iterable[Any]:
    if isinstance(data, list):
        for item in data:
            yield from _iter_jsonld_items(item)
    elif isinstance(data, dict):
        if "@graph" in data:
            yield from _iter_jsonld_items(data["@graph"])
        else:
            yield data


def _product_from_jsonld(item: Any, base_url: str) -> ProductInfo | None:
    if not isinstance(item, dict):
        return None

    type_field = item.get("@type")
    if isinstance(type_field, list):
        is_product = any(t.lower() == "product" for t in type_field if isinstance(t, str))
        primary_type = next((t for t in type_field if isinstance(t, str)), None)
    elif isinstance(type_field, str):
        is_product = type_field.lower() == "product"
        primary_type = type_field
    else:
        is_product = False
        primary_type = None

    if not is_product:
        return None

    offers = item.get("offers", {}) if isinstance(item.get("offers"), dict) else {}
    if isinstance(item.get("offers"), list) and item["offers"]:
        offers = item["offers"][0]

    seller = None
    if isinstance(offers, dict):
        seller_info = offers.get("seller")
        if isinstance(seller_info, dict):
            seller = seller_info.get("name") or seller_info.get("@id")

    aggregate_rating = item.get("aggregateRating")
    if isinstance(aggregate_rating, dict):
        sales = aggregate_rating.get("ratingCount") or aggregate_rating.get("reviewCount")
    else:
        sales = None

    price = None
    currency = None
    availability = None
    if isinstance(offers, dict):
        price = offers.get("price") or offers.get("lowPrice")
        currency = offers.get("priceCurrency")
        availability = offers.get("availability")

    category = item.get("category") or item.get("type")
    title = item.get("name")
    url = item.get("url") or base_url

    extra: dict[str, Any] = {}
    for key in ("brand", "sku", "gtin13", "mpn"):
        if key in item:
            extra[key] = item[key]

    return ProductInfo(
        url=url,
        title=title,
        price=str(price) if price is not None else None,
        currency=currency,
        availability=availability,
        seller=seller,
        category=category,
        item_type=primary_type,
        sales=str(sales) if sales is not None else None,
        extra=extra or None,
    )

