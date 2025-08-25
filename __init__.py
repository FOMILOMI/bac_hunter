"""Top-level package shim.

Avoid importing heavy CLI modules during test collection.
Expose light utilities only.
"""

from .config import Settings  # noqa: F401

__all__ = ["Settings"]
