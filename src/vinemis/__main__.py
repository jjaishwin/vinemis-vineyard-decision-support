"""Module entry point so ``python -m vinemis`` works."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
