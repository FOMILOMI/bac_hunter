from __future__ import annotations
import logging
from typing import Dict, Optional, List, Any

from ..storage import Storage


log = logging.getLogger("advanced.response")


class ResponseAnalyzer:
	"""Lightweight classifier for responses to hint sensitivity."""

	def __init__(self, storage: Storage):
		self.db = storage

	def classify(self, status: int, length: int, content_type: Optional[str]) -> str:
		if status in (401, 403):
			return "protected"
		if status == 200 and content_type and "json" in content_type.lower():
			return "api-json"
		if status == 200 and length > 150000:
			return "large"
		return "normal"

	def analyze_record(self, status: int, length: int, content_type: Optional[str]) -> Dict[str, str | int]:
		return {
			"status": status,
			"length": length,
			"type": content_type or "",
			"class": self.classify(status, length, content_type),
		}


class VulnerabilityAnalyzer:
	"""Heuristic/AI-assisted analyzer that scores and prioritizes findings.
	Currently a lightweight placeholder performing simple score normalization.
	"""

	def __init__(self, storage: Storage):
		self.db = storage

	def analyze(self) -> List[Dict[str, Any]]:
		results: List[Dict[str, Any]] = []
		for target_id, ftype, url, evidence, score in self.db.iter_findings():
			priority = min(1.0, max(0.0, score))
			results.append({
				"target_id": target_id,
				"type": ftype,
				"url": url,
				"evidence": evidence,
				"priority": priority,
			})
		return results