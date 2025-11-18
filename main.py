from __future__ import annotations

import sys

from ui.cli import run_cli


def main() -> int:
    # Entry point only: delegate to the CLI layer.
    return run_cli(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
