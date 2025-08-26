from __future__ import annotations

# Lazy, relative-only exports to avoid circular imports during package initialization
# and keep intra-package imports consistent.

__all__ = [
    "ResponseComparator",
    "DiffResult",
    "DifferentialTester",
    "IDORProbe",
    "ForceBrowser",
    "HARReplayAnalyzer",
    "RequestMutator",
]


def __getattr__(name: str):
    if name in {"ResponseComparator", "DiffResult"}:
        from .comparator import ResponseComparator, DiffResult  # type: ignore
        return {"ResponseComparator": ResponseComparator, "DiffResult": DiffResult}[name]
    if name == "DifferentialTester":
        from .differential import DifferentialTester  # type: ignore
        return DifferentialTester
    if name == "IDORProbe":
        from .idor_probe import IDORProbe  # type: ignore
        return IDORProbe
    if name == "ForceBrowser":
        from .force_browse import ForceBrowser  # type: ignore
        return ForceBrowser
    if name == "HARReplayAnalyzer":
        from .har_replay import HARReplayAnalyzer  # type: ignore
        return HARReplayAnalyzer
    if name == "RequestMutator":
        from .mutator import RequestMutator  # type: ignore
        return RequestMutator
    raise AttributeError(name)