"""Zoya Studio main entry point.

Launch with:
    python -m zoya_studio
    zoya studio
    zoya
"""

from __future__ import annotations

import sys

from zoya_studio.core.app import main

if __name__ == "__main__":
    sys.exit(main())
