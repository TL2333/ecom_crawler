from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse

from .base import CrawlEngine, CrawlReport
from ..config import CrawlConfig
from ..adapters.registry import AdapterRegistry
from ..adapters.base import ProductInfo
from ..utils.http import create_session, fetch_text
from ..utils.parsing import normalize_url

logger = logging.getLogger(__name__)


@dataclass
class _QueueItem:
    url: str
    depth: int


class SimpleCrawlEngine(CrawlEngine):
    """
    A pragmatic, upgrade-friendly async crawler.
    - Engine owns HTTP and queueing.
    - Adapters own page parsing.
    - Concurrency capped by a semaphore.
    """
    def __init__(self, config: CrawlConfig, registry: AdapterRegistry | None = None) -> None:
        self.config = config
        self.registry = registry or AdapterRegistry()
        # Try entry-point discovery; silently ignore if none found.
        self.registry.discover_entry_points()

    async def crawl(self) -> CrawlReport:
        cfg = self.config
        discovered: Dict[str, List[ProductInfo]] = defaultdict(list)
        visited: Set[str] = set()

        # Allowed domains: if not set, restrict each start URL to its own domain.
        allowed_domains: Set[str] = set(cfg.allowed_domains or [])
        if not allowed_domains:
            for u in cfg.start_urls:
                allowed_domains.add(urlparse(u).netloc)

        sem = asyncio.Semaphore(cfg.max_concurrency)
        q: asyncio.Queue[_QueueItem] = asyncio.Queue()

        for u in cfg.start_urls:
            await q.put(_QueueItem(url=normalize_url(u), depth=0))

        session = create_session()
        try:
            async def worker() -> None:
                while True:
                    try:
                        item = await asyncio.wait_for(q.get(), timeout=0.1)
                    except asyncio.TimeoutError:
                        # Periodically allow tasks to finish when queue is empty
                        if q.empty():
                            return
                        continue

                    if item.url in visited:
                        q.task_done()
                        continue
                    visited.add(item.url)

                    # Depth control
                    if item.depth > cfg.max_depth:
                        q.task_done()
                        continue

                    domain = urlparse(item.url).netloc
                    if domain not in allowed_domains:
                        q.task_done()
                        continue

                    async with sem:
                        html = await fetch_text(
                            session,
                            item.url,
                            timeout=cfg.request_timeout,
                            user_agent=cfg.user_agent,
                            retries=cfg.retries,
                        )

                    if not html:
                        q.task_done()
                        continue

                    adapter = self.registry.match(item.url)
                    try:
                        parsed = adapter.parse(item.url, html)
                    except Exception as exc:
                        logger.debug("Adapter %s failed on %s: %r", getattr(adapter, "name", adapter), item.url, exc)
                        q.task_done()
                        continue

                    # Record products per domain
                    products = list(parsed.products)
                    if not products and parsed.product_urls:
                        products = [ProductInfo(url=u) for u in parsed.product_urls]

                    if cfg.keywords:
                        products = [p for p in products if p.matches_keywords(cfg.keywords or [])]

                    if products:
                        discovered[domain].extend(products)

                    # Enqueue next links
                    next_depth = item.depth + 1
                    for link in parsed.next_links:
                        link_norm = normalize_url(link)
                        if link_norm not in visited:
                            # Only queue if still within allowed domains
                            if urlparse(link_norm).netloc in allowed_domains:
                                await q.put(_QueueItem(url=link_norm, depth=next_depth))

                    q.task_done()

            workers = [asyncio.create_task(worker()) for _ in range(cfg.max_concurrency)]
            await asyncio.gather(*workers)
        finally:
            await session.close()

        # De-duplicate product URLs per domain
        deduped: Dict[str, List[ProductInfo]] = {}
        for domain, products in discovered.items():
            seen: Dict[str, ProductInfo] = {}
            for product in products:
                if product.url not in seen:
                    seen[product.url] = product
            deduped[domain] = list(seen.values())
        return CrawlReport(discovered=deduped, visited_count=len(visited))
