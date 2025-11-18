# ecom_crawler (upgrade-friendly skeleton)

A modular crawler designed to be **easy to extend and upgrade**.

## Quick start

```bash
# (Recommended) Create a virtualenv / conda env first
pip install -r requirements.txt

# Basic crawl (writes output/product_urls.json)
python main.py https://example.com --max-depth 1

# Keep only "headphone" or "book" results and include structured metadata
python main.py https://example.com --keywords "headphone,book" --exporter export.csv_exporter:CSVExporter

# Crawl GitHub trending repositories and capture stars/owner/topic info
python main.py https://github.com/trending --allowed-domains github.com --exporter export.json_exporter:JSONExporter

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
- **Structured results**: Crawls now emit `url`, `title`, `price`, `currency`, `availability`, `seller`, `category/type`, and `sales` counts when available (GitHub repositories map stars to the sales field).
- **Keyword filters**: Limit crawls to products that match comma-separated keywords (e.g. `--keywords "laptop,tablet"`).
- **Dynamic loading**: choose engine/exporter/adapters with dotted paths (no code edits).
- **Plugin discovery**: entry-point group `ecom_crawler.adapters` supported for 3rd‑party adapters. A dedicated GitHub adapter ships in-tree so you can crawl repository metadata (owner, language, stars, topics) without writing custom code.
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

The JSON and CSV exporters automatically include structured product metadata (sales, seller/owner, type/category, price, etc.). The CSV exporter writes headers so you can filter/sort in spreadsheets immediately.

## Testing

Add pytest-based tests under `tests/`. The core is designed so engines and adapters can be unit tested in isolation.

