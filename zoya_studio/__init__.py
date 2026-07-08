"""Zoya Studio - AI-Powered Terminal IDE for the Zoya Programming Language."""

__version__ = "1.0.0"
__author__ = "Zoya Team"
__description__ = "Complete terminal-based IDE for Zoya development"

from zoya_studio.core.app import ZoyaStudioApp
from zoya_studio.core.config import Config

__all__ = ["ZoyaStudioApp", "Config"]