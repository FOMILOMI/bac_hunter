from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ProgressSnapshot:
	start_time: float
	total_tasks: int
	completed: int
	running: int
	pending: int


class ProgressTracker:
	"""Tracks job progress metrics (for CLI/reporting visibility)."""

	def __init__(self):
		self.start_time = time.time()
		self.totals = {
			"total_tasks": 0,
			"completed": 0,
			"running": 0,
			"pending": 0,
		}

	def update(self, total_tasks: int | None = None, completed: int | None = None, running: int | None = None, pending: int | None = None):
		if total_tasks is not None:
			self.totals["total_tasks"] = total_tasks
		if completed is not None:
			self.totals["completed"] = completed
		if running is not None:
			self.totals["running"] = running
		if pending is not None:
			self.totals["pending"] = pending

	def snapshot(self) -> ProgressSnapshot:
		return ProgressSnapshot(
			start_time=self.start_time,
			total_tasks=self.totals["total_tasks"],
			completed=self.totals["completed"],
			running=self.totals["running"],
			pending=self.totals["pending"],
		)

	def as_dict(self) -> Dict[str, Any]:
		s = self.snapshot()
		return {
			"runtime_seconds": time.time() - s.start_time,
			"total_tasks": s.total_tasks,
			"completed": s.completed,
			"running": s.running,
			"pending": s.pending,
		}