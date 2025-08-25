# engines/browser_engine.py
from pathlib import Path
import os, sys

def app_data_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / ".ecom-crawler")
    p = Path(base) / "ecom-crawler"
    p.mkdir(parents=True, exist_ok=True)
    return p

BROWSERS_DIR = app_data_dir() / "ms-playwright"
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(BROWSERS_DIR))
