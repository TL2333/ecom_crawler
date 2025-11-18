from __future__ import annotations

import json
from typing import Dict, List
from pathlib import Path

from .base import Exporter


class JSONExporter:
    def export(self, data: Dict[str, List[str]], path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
