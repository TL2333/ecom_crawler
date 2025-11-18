from __future__ import annotations

import csv
from typing import Dict, List
from pathlib import Path

from .base import Exporter


class CSVExporter:
    """
    Writes "domain,product_url" rows to a CSV file.
    """
    def export(self, data: Dict[str, List[str]], path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["domain", "product_url"])
            for domain, urls in data.items():
                for u in urls:
                    w.writerow([domain, u])
