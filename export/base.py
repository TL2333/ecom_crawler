from __future__ import annotations

from typing import Dict, List, Protocol


class Exporter(Protocol):
    def export(self, data: Dict[str, List[str]], path: str) -> None:
        ...
