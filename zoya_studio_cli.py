#!/usr/bin/env python3
"""Zoya Studio launcher.

Usage:
    python zoya_studio_cli.py [project_path]
    zoya studio
    zoya-studio
"""

import sys

from zoya_studio.core.app import main

if __name__ == "__main__":
    sys.exit(main())
