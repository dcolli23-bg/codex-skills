#!/usr/bin/env python3
"""Compatibility entry point for the shared PR collection and posting helper."""

from pathlib import Path
import sys


sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "github-pr-comments" / "scripts")
)
from pr_comments import main


if __name__ == "__main__":
    sys.exit(main())
