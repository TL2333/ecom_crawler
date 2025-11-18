from __future__ import annotations

import json
from typing import Dict, List
from pathlib import Path

from .base import Exporter
from ..adapters.base import ProductInfo


class JSONExporter:
    def export(self, data: Dict[str, List[ProductInfo]], path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            serializable = {domain: [p.to_dict() for p in products] for domain, products in data.items()}
            json.dump(serializable, f, indent=2, ensure_ascii=False)
