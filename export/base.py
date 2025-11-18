from __future__ import annotations

from typing import Dict, List, Protocol

from ..adapters.base import ProductInfo

class Exporter(Protocol):
    def export(self, data: Dict[str, List[ProductInfo]], path: str) -> None:
        ...
