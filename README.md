# ecom_crawler (upgrade-friendly skeleton)

A modular crawler designed to be **easy to extend and upgrade**.

## Quick start

```bash
# (Recommended) Create a virtualenv / conda env first
pip install -r requirements.txt

# Basic crawl (writes output/product_urls.json)
python main.py https://example.com --max-depth 1

# Use CSV exporter and deeper crawl
python main.py https://example.com --max-depth 2 --exporter export.csv_exporter:CSVExporter --output output/products.csv
```

## Run API (optional)

```bash
pip install fastapi uvicorn pydantic
python main.py --serve --host 0.0.0.0 --port 8000
# Then: POST http://localhost:8000/crawl with JSON body { "start_urls": ["https://example.com"] }
```

## Design for easy upgrades

- **Stable interfaces**: `engines.CrawlEngine`, `adapters.SiteAdapter`, `export.Exporter` are tiny protocols.
- **Dynamic loading**: choose engine/exporter/adapters with dotted paths (no code edits).
- **Plugin discovery**: entry-point group `ecom_crawler.adapters` supported for 3rd‑party adapters.
- **Config schema**: `config.CrawlConfig` includes `schema_version` with a `migrate_config()` hook.
- **Dependency-light core**: only standard library + `aiohttp` and `bs4` for crawling/parsing.
- **Separation of concerns**:
  - Engine = concurrency, queue, retries
  - Adapter = HTML → product links, next links
  - Exporter = serialization only
  - UI/API = orchestration

## Adding a new adapter

Create a class implementing `SiteAdapter`:

```python
from adapters.base import SiteAdapter, ParseResult
from utils.parsing import extract_links, is_product_like

class MyShopAdapter:
    name = "myshop"
    domains = ["myshop.com"]

    def matches(self, url: str) -> bool:
        return any(d in url for d in self.domains)

    def parse(self, url: str, html: str) -> ParseResult:
        links = extract_links(html, base_url=url)
        product = [u for u in links if is_product_like(u)]
        # Optionally narrow next links to category pages, etc.
        return ParseResult(product_urls=product, next_links=list(links))
```

Register at runtime (no code edits):

```bash
python main.py https://myshop.com --extra-adapters "my_package.my_module:MyShopAdapter"
```

## Exporters

Swap exporter at runtime:

```bash
python main.py https://example.com --exporter export.csv_exporter:CSVExporter --output out.csv
```

## Testing

Add pytest-based tests under `tests/`. The core is designed so engines and adapters can be unit tested in isolation.

