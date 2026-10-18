"""Module entrypoint for `python3 -m borealis`."""

import sys

from borealis.cli import main

if __name__ == "__main__":
    sys.exit(main())
