from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set
from abc import ABC, abstractmethod


@dataclass
class CrawlReport:
    discovered: Dict[str, List[str]] = field(default_factory=dict)  # domain -> product URLs
    visited_count: int = 0


class CrawlEngine(ABC):
    """
    Abstract engine interface. Implementations own the crawl lifecycle.
    """
    @abstractmethod
    async def crawl(self) -> CrawlReport:  # pragma: no cover - interface
        ...
