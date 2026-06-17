#!/usr/bin/env python3
"""Launcher so you can run `python eer.py <cmd>` from the repo root."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eer.cli import main

if __name__ == "__main__":
    main(sys.argv[1:])
