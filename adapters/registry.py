from __future__ import annotations

from typing import List, Optional, Iterable
from importlib import metadata

from .base import SiteAdapter
from .generic import GenericAdapter
from .github import GitHubRepoAdapter


class AdapterRegistry:
    """
    Registry for available adapters.
    Supports built-ins, config-defined dotted classes, and entry-point plugins.
    """
    def __init__(self) -> None:
        self._adapters: List[SiteAdapter] = [GenericAdapter(), GitHubRepoAdapter()]

    # ---- Introspection / Management ----

    def register(self, adapter: SiteAdapter) -> None:
        self._adapters.append(adapter)

    @property
    def adapters(self) -> List[SiteAdapter]:
        return list(self._adapters)

    def match(self, url: str) -> SiteAdapter:
        # Prefer specific adapters over generic fallback (kept first in list).
        for a in self._adapters[1:]:
            if a.matches(url):
                return a
        return self._adapters[0]  # generic

    # ---- Discovery ----

    def discover_entry_points(self, group: str = "ecom_crawler.adapters") -> int:
        """
        Discover third-party adapters installed as entry points.
        Returns count of newly registered adapters.
        """
        added = 0
        try:
            eps = metadata.entry_points()
            # Modern syntax (Py3.10+)
            for ep in eps.select(group=group):
                adapter_cls = ep.load()
                self.register(adapter_cls())
                added += 1
        except Exception:
            # Be permissive—plugins are optional
            pass
        return added
