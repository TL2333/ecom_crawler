from __future__ import annotations

from typing import Iterable, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .base import ParseResult, ProductInfo
from ..utils.parsing import extract_links


class GitHubRepoAdapter:
    """Adapter that treats GitHub repositories as crawlable products."""

    name = "github"
    domains = ["github.com", "www.github.com"]

    def matches(self, url: str) -> bool:
        netloc = urlparse(url).netloc.lower()
        return netloc.endswith("github.com")

    def parse(self, url: str, html: str) -> ParseResult:
        soup = BeautifulSoup(html, "html.parser")
        links = extract_links(html, url)
        repo_links = [link for link in links if self._is_repo_url(link)]

        products: List[ProductInfo] = []
        if self._is_repo_url(url):
            product = self._extract_repo_page(url, soup)
            if product:
                products.append(product)
        else:
            products.extend(self._extract_listing_cards(url, soup))

        if not products and repo_links:
            # Provide lightweight records so downstream exporters see repo URLs.
            products = [self._product_from_url(link) for link in repo_links if self._product_from_url(link)]

        next_links = list({*repo_links, *self._listing_links(links)})
        return ParseResult(product_urls=repo_links, next_links=next_links, products=products)

    # ---- Extraction helpers -------------------------------------------------

    def _extract_repo_page(self, url: str, soup: BeautifulSoup) -> Optional[ProductInfo]:
        owner_repo = self._split_repo(url)
        if not owner_repo:
            return None
        owner, repo = owner_repo

        title_meta = soup.find("meta", attrs={"property": "og:title"})
        description_meta = soup.find("meta", attrs={"property": "og:description"})
        canonical_meta = soup.find("meta", attrs={"property": "og:url"})
        repo_url = canonical_meta.get("content") if canonical_meta else url
        title = title_meta.get("content") if title_meta else f"{owner}/{repo}"
        description = description_meta.get("content") if description_meta else None

        language = self._text_or_none(soup.select_one("[itemprop='programmingLanguage']"))
        topics = [self._text_or_none(tag) for tag in soup.select("a.topic-tag")]
        topics = [t for t in topics if t]

        stars = self._stat_from_href(soup, "stargazers")
        forks = self._stat_from_href(soup, "network/members")
        watchers = self._stat_from_href(soup, "watchers")

        extra = {
            key: value
            for key, value in {
                "description": description,
                "topics": topics or None,
                "stars": stars,
                "forks": forks,
                "watchers": watchers,
            }.items()
            if value
        }

        return ProductInfo(
            url=repo_url,
            title=title,
            seller=owner,
            category=language,
            item_type="repository",
            sales=stars,
            extra=extra or None,
        )

    def _extract_listing_cards(self, base_url: str, soup: BeautifulSoup) -> List[ProductInfo]:
        products: List[ProductInfo] = []
        selectors = ["article.Box-row", "li.repo-list-item"]
        for selector in selectors:
            for card in soup.select(selector):
                anchor = card.select_one("h2 a") or card.select_one("a.v-align-middle")
                if not anchor:
                    continue
                href = anchor.get("href")
                if not href:
                    continue
                repo_url = urljoin(base_url, href)
                owner_repo = self._split_repo(repo_url)
                if not owner_repo:
                    continue
                owner, repo = owner_repo
                title = anchor.get_text(strip=True) or f"{owner}/{repo}"
                description = self._text_or_none(card.select_one("p"))
                language = self._text_or_none(card.select_one("[itemprop='programmingLanguage']"))
                stars = self._text_or_none(card.select_one("a[href*='stargazers']"))
                sales = self._normalize_count(stars) if stars else None
                topics = [self._text_or_none(tag) for tag in card.select("a.topic-tag")]
                topics = [t for t in topics if t]

                extra = {
                    key: value
                    for key, value in {
                        "description": description,
                        "topics": topics or None,
                        "stars": sales,
                    }.items()
                    if value
                }

                products.append(
                    ProductInfo(
                        url=repo_url,
                        title=title,
                        seller=owner,
                        category=language,
                        item_type="repository",
                        sales=sales,
                        extra=extra or None,
                    )
                )
        return products

    # ---- URL helpers --------------------------------------------------------

    def _split_repo(self, url: str) -> Optional[tuple[str, str]]:
        parsed = urlparse(url)
        if not parsed.netloc.endswith("github.com"):
            return None
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2:
            return None
        owner, repo = parts[0], parts[1]
        blocked_prefixes = {
            "topics",
            "collections",
            "search",
            "marketplace",
            "orgs",
            "apps",
            "enterprise",
            "features",
        }
        if owner in blocked_prefixes:
            return None
        return owner, repo.rstrip(".git")

    def _is_repo_url(self, url: str) -> bool:
        return self._split_repo(url) is not None

    def _product_from_url(self, url: str) -> Optional[ProductInfo]:
        owner_repo = self._split_repo(url)
        if not owner_repo:
            return None
        owner, repo = owner_repo
        return ProductInfo(
            url=url,
            title=f"{owner}/{repo}",
            seller=owner,
            item_type="repository",
        )

    def _listing_links(self, links: Iterable[str]) -> List[str]:
        prefixes = ("/topics", "/collections", "/search", "/trending", "/explore")
        out: List[str] = []
        for link in links:
            parsed = urlparse(link)
            if not parsed.netloc.endswith("github.com"):
                continue
            path = parsed.path
            if any(path.startswith(prefix) for prefix in prefixes) or self._is_repo_url(link):
                out.append(link)
        return out

    # ---- Text helpers -------------------------------------------------------

    def _stat_from_href(self, soup: BeautifulSoup, suffix: str) -> Optional[str]:
        selector = f"a[href$='/{suffix}']"
        node = soup.select_one(selector)
        if not node:
            return None
        return self._normalize_count(node.get_text(strip=True))

    def _text_or_none(self, node) -> Optional[str]:
        if not node:
            return None
        text = node.get_text(strip=True)
        return text or None

    def _normalize_count(self, text: str) -> Optional[str]:
        if not text:
            return None
        value = text.strip().lower().replace(",", "")
        try:
            if value.endswith("k"):
                return str(int(float(value[:-1]) * 1000))
            if value.endswith("m"):
                return str(int(float(value[:-1]) * 1_000_000))
            return str(int(float(value)))
        except ValueError:
            return text.strip()

