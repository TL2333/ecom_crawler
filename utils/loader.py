from __future__ import annotations

import importlib
from typing import Any


def load_symbol(dotted: str) -> Any:
    """
    Load a class or function from a dotted path.
    Supports both "package.module:ClassName" and "package.module.ClassName".
    """
    if ":" in dotted:
        module_name, symbol_name = dotted.split(":", 1)
    else:
        module_name, symbol_name = dotted.rsplit(".", 1)

    module = importlib.import_module(module_name)
    return getattr(module, symbol_name)
