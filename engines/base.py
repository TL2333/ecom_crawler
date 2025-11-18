from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set
from abc import ABC, abstractmethod

from ..adapters.base import ProductInfo


@dataclass
class CrawlReport:
    discovered: Dict[str, List[ProductInfo]] = field(default_factory=dict)  # domain -> product metadata
    visited_count: int = 0


class CrawlEngine(ABC):
    """
    Abstract engine interface. Implementations own the crawl lifecycle.
    """
    @abstractmethod
    async def crawl(self) -> CrawlReport:  # pragma: no cover - interface
        ...
