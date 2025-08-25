"""BAC Hunter package.

Public exports:
- Settings, Identity from .config
- app (Typer application) from .cli
"""

from .config import Settings, Identity
from .cli import app

__version__ = "2.0.0"

__all__ = ["Settings", "Identity", "app", "__version__"]

