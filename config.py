from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import json

from version import __version__, CONFIG_SCHEMA_VERSION


@dataclass
class CrawlConfig:
    """
    Canonical configuration object passed throughout the system.
    Keep it dataclass-only (no heavy deps) to stay upgrade-friendly.
    """
    schema_version: int = CONFIG_SCHEMA_VERSION
    start_urls: List[str] = field(default_factory=list)
    allowed_domains: Optional[List[str]] = None
    max_depth: int = 2
    max_concurrency: int = 10
    request_timeout: float = 15.0
    retries: int = 2
    user_agent: str = f"ecom_crawler/{__version__}"
    # Dotted paths for engine/exporter to allow runtime swapping without code changes.
    engine: str = "engines.simple_engine:SimpleCrawlEngine"
    exporter: str = "export.json_exporter:JSONExporter"
    # Extra adapters (dotted class paths) to register at startup
    extra_adapters: List[str] = field(default_factory=list)
    # Where to write results
    output_path: str = "output/product_urls.json"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    # ---------- Loaders ----------

    @classmethod
    def from_env(cls) -> "CrawlConfig":
        """
        Build config from environment variables (all optional).
        """
        urls = os.getenv("CRAWLER_START_URLS", "")
        start_urls = [u.strip() for u in urls.split(",") if u.strip()]

        allowed = os.getenv("CRAWLER_ALLOWED_DOMAINS", "")
        allowed_domains = [d.strip() for d in allowed.split(",") if d.strip()] or None

        def _get(name: str, default: str) -> str:
            return os.getenv(name, default)

        return cls(
            start_urls=start_urls,
            allowed_domains=allowed_domains,
            max_depth=int(_get("CRAWLER_MAX_DEPTH", "2")),
            max_concurrency=int(_get("CRAWLER_MAX_CONCURRENCY", "10")),
            request_timeout=float(_get("CRAWLER_REQUEST_TIMEOUT", "15.0")),
            retries=int(_get("CRAWLER_RETRIES", "2")),
            user_agent=_get("CRAWLER_USER_AGENT", f"ecom_crawler/{__version__}"),
            engine=_get("CRAWLER_ENGINE", "engines.simple_engine:SimpleCrawlEngine"),
            exporter=_get("CRAWLER_EXPORTER", "export.json_exporter:JSONExporter"),
            extra_adapters=[a.strip() for a in _get("CRAWLER_EXTRA_ADAPTERS", "").split(",") if a.strip()],
            output_path=_get("CRAWLER_OUTPUT_PATH", "output/product_urls.json"),
        )

    @classmethod
    def from_file(cls, path: str | os.PathLike[str]) -> "CrawlConfig":
        """
        Load configuration from a JSON file. Supports schema migration for future versions.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data = migrate_config(data)
        return cls(**data)

    # ---------- Validation ----------

    def validate(self) -> None:
        if not self.start_urls:
            raise ValueError("start_urls cannot be empty; provide at least one URL.")
        if self.max_depth < 0:
            raise ValueError("max_depth must be >= 0")
        if self.max_concurrency <= 0:
            raise ValueError("max_concurrency must be > 0")
        # Validate output path parent exists or is creatable
        parent = Path(self.output_path).parent
        parent.mkdir(parents=True, exist_ok=True)


def migrate_config(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate config dict to the latest schema version.
    Keep this pure and additive. Add migrations here as you bump schema.
    """
    schema = raw.get("schema_version", 1)

    # Example placeholder for future migrations:
    # if schema == 0:
    #     raw["schema_version"] = 1
    #     # Map/rename old fields here

    # Ensure a schema_version is present
    raw.setdefault("schema_version", CONFIG_SCHEMA_VERSION)
    return raw
