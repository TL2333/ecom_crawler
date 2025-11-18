from __future__ import annotations

import csv
from typing import Dict, List
from pathlib import Path

from .base import Exporter
from ..adapters.base import ProductInfo


class CSVExporter:
    """
    Writes per-product rows enriched with structured metadata.
    """

    _headers = [
        "domain",
        "url",
        "title",
        "price",
        "currency",
        "availability",
        "seller",
        "category",
        "type",
        "sales",
    ]

    def export(self, data: Dict[str, List[ProductInfo]], path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(self._headers)
            for domain, products in data.items():
                for product in products:
                    w.writerow(
                        [
                            domain,
                            product.url,
                            product.title or "",
                            product.price or "",
                            product.currency or "",
                            product.availability or "",
                            product.seller or "",
                            product.category or "",
                            product.item_type or "",
                            product.sales or "",
                        ]
                    )
