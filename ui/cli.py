from __future__ import annotations

import argparse
import asyncio
import logging
from typing import List

from ..config import CrawlConfig
from ..utils.logging import setup_logging
from ..utils.loader import load_symbol
from ..adapters.registry import AdapterRegistry
from ..engines.base import CrawlReport


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="E-commerce crawler CLI")
    p.add_argument("urls", nargs="*", help="Start URLs (space-separated)")
    p.add_argument("--config", type=str, help="Path to config JSON", default=None)
    p.add_argument("--max-depth", type=int, default=None, help="Max crawl depth (default from config)")
    p.add_argument("--max-concurrency", type=int, default=None, help="Max concurrency (default from config)")
    p.add_argument("--allowed-domains", type=str, default=None,
                   help="Comma-separated list of allowed domains (default restricts to each start URL domain)")
    p.add_argument("--engine", type=str, default=None, help="Engine dotted path (module:ClassName)")
    p.add_argument("--exporter", type=str, default=None, help="Exporter dotted path (module:ClassName)")
    p.add_argument("--extra-adapters", type=str, default=None,
                   help="Comma-separated dotted paths for additional adapters")
    p.add_argument("--output", type=str, default=None, help="Output file path")
    p.add_argument("--log-level", type=str, default=None, help="Log level (DEBUG, INFO, WARNING, ERROR)")
    p.add_argument("--serve", action="store_true", help="Run REST API server instead of CLI crawl")
    p.add_argument("--host", type=str, default="127.0.0.1", help="API host (when --serve)")
    p.add_argument("--port", type=int, default=8000, help="API port (when --serve)")
    return p


def _load_config(args: argparse.Namespace) -> CrawlConfig:
    if args.config:
        cfg = CrawlConfig.from_file(args.config)
    else:
        cfg = CrawlConfig.from_env()

    if args.urls:
        cfg.start_urls = list(args.urls)
    if args.max_depth is not None:
        cfg.max_depth = args.max_depth
    if args.max_concurrency is not None:
        cfg.max_concurrency = args.max_concurrency
    if args.allowed_domains:
        cfg.allowed_domains = [d.strip() for d in args.allowed_domains.split(",") if d.strip()]
    if args.engine:
        cfg.engine = args.engine
    if args.exporter:
        cfg.exporter = args.exporter
    if args.extra_adapters:
        cfg.extra_adapters = [a.strip() for a in args.extra_adapters.split(",") if a.strip()]
    if args.output:
        cfg.output_path = args.output

    cfg.validate()
    return cfg


def run_server(host: str, port: int) -> None:
    try:
        import uvicorn  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dep
        raise SystemExit("To run the API, install dependencies: pip install fastapi uvicorn pydantic") from exc
    uvicorn.run("apis.app:app", host=host, port=port, reload=True)


def run_cli(argv: List[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    setup_logging(args.log_level)

    if args.serve:
        run_server(args.host, args.port)
        return 0

    cfg = _load_config(args)

    # Dynamic engine + exporter loading so upgrades don't require code edits.
    engine_cls = load_symbol(cfg.engine)
    exporter_cls = load_symbol(cfg.exporter)

    registry = AdapterRegistry()
    # Allow runtime registration of additional adapters
    for dotted in cfg.extra_adapters:
        try:
            adapter_cls = load_symbol(dotted)
            registry.register(adapter_cls())
        except Exception as exc:
            logging.getLogger(__name__).warning("Failed to load adapter %s: %r", dotted, exc)

    async def _run() -> CrawlReport:
        engine = engine_cls(cfg, registry=registry)
        return await engine.crawl()

    report: CrawlReport = asyncio.run(_run())

    exporter = exporter_cls()
    exporter.export(report.discovered, cfg.output_path)

    logging.getLogger(__name__).info("Visited: %s | Products: %s | Output: %s",
                                     report.visited_count,
                                     sum(len(v) for v in report.discovered.values()),
                                     cfg.output_path)
    return 0
