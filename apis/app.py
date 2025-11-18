from __future__ import annotations

from typing import Any, Dict, List, Optional
import asyncio
import logging

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except Exception as exc:  # pragma: no cover - optional dependency
    raise RuntimeError(
        "FastAPI not installed. Install with `pip install fastapi pydantic uvicorn` "
        "or avoid using the API server."
    ) from exc

from ..config import CrawlConfig
from ..utils.loader import load_symbol
from ..engines.base import CrawlReport
from ..adapters.registry import AdapterRegistry

logger = logging.getLogger(__name__)

app = FastAPI(title="ecom_crawler API", version="0.1.0")


class CrawlRequest(BaseModel):
    start_urls: List[str]
    max_depth: Optional[int] = None
    max_concurrency: Optional[int] = None
    allowed_domains: Optional[List[str]] = None
    engine: Optional[str] = None
    exporter: Optional[str] = None  # ignored by API; returning JSON
    extra_adapters: Optional[List[str]] = None


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/crawl")
async def crawl(req: CrawlRequest) -> Dict[str, Any]:
    cfg = CrawlConfig.from_env()
    cfg.start_urls = req.start_urls or cfg.start_urls
    if req.max_depth is not None:
        cfg.max_depth = req.max_depth
    if req.max_concurrency is not None:
        cfg.max_concurrency = req.max_concurrency
    if req.allowed_domains is not None:
        cfg.allowed_domains = req.allowed_domains
    if req.engine:
        cfg.engine = req.engine
    if req.extra_adapters:
        cfg.extra_adapters = req.extra_adapters

    cfg.validate()

    # Load engine dynamically
    engine_cls = load_symbol(cfg.engine)
    registry = AdapterRegistry()
    # Dynamically register additional adapters
    for dotted in cfg.extra_adapters:
        try:
            adapter_cls = load_symbol(dotted)
            registry.register(adapter_cls())
        except Exception as exc:
            logger.warning("Failed to load adapter %s: %r", dotted, exc)

    engine = engine_cls(cfg, registry=registry)
    report: CrawlReport = await engine.crawl()
    return {"visited": report.visited_count, "discovered": report.discovered}
