from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

try:
	from ..monitoring.stats_collector import StatsCollector
	from ..storage import Storage
except Exception:
	from monitoring.stats_collector import StatsCollector
	from storage import Storage


@dataclass
class GuidanceEvent:
	phase: str
	message: str
	progress: Optional[float] = None


class InteractiveGuidanceSystem:
	"""Minimal interactive guidance: yields concise progress messages and suggestions."""

	def __init__(self, stats: StatsCollector, storage: Storage):
		self.stats = stats
		self.db = storage

	def emit(self, phase: str, message: str, progress: Optional[float] = None) -> GuidanceEvent:
		# In future, plug into web UI or TUI. For now, return a struct the CLI can print.
		return GuidanceEvent(phase=phase, message=message, progress=progress)

