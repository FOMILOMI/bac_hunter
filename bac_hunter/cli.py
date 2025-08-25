from __future__ import annotations

# Import top-level cli module as a submodule to expose Typer app under bac_hunter.cli
import importlib

_cli = importlib.import_module("cli")
app = getattr(_cli, "app")

__all__ = ["app"]

