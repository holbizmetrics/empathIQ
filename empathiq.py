#!/usr/bin/env python3
"""empathIQ launcher — run the engine straight from the repo root.

So you don't have to go hunting for it: from the repo root just run

    python empathiq.py run --personality sol --input "I keep starting things and not finishing"

This forwards to the Forge engine CLI in ./forge (see forge/README.md for the
full command reference). Everything `forge/eer.py` accepts works here too.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_ROOT, "forge"))

from eer.cli import main  # noqa: E402  (path must be set before import)

if __name__ == "__main__":
    main(sys.argv[1:])
