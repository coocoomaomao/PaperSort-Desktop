"""PyInstaller entry point that imports PaperSort as an installed package."""

from papersort.main import main

if __name__ == "__main__":
    raise SystemExit(main())
