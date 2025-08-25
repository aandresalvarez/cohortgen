from __future__ import annotations

import sys

from . import __version__


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Simple banner; extend with real CLI later
    print(f"cohortgen {__version__}")
    if argv and argv[0] in {"-h", "--help"}:
        print("Usage: python -m cohortgen")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

