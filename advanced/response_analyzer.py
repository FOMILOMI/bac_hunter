from __future__ import annotations
import logging
from typing import Dict, Optional

from ..storage import Storage

log = logging.getLogger("advanced.analyzer")


class ResponseAnalyzer:
	"""Lightweight helpers to classify responses and extract simple signals."""

	def __init__(self, db: Storage):
		self.db = db

	def is_json(self, content_type: Optional[str]) -> bool:
		return (content_type or "").lower().startswith("application/json")

	def is_html(self, content_type: Optional[str]) -> bool:
		ct = (content_type or "").lower()
		return ct.startswith("text/html") or "html" in ct

	def classify(self, status: int, length: int, content_type: Optional[str]) -> str:
		if status in (401, 403):
			return "forbidden"
		if status in (500, 502, 503, 504):
			return "server_error"
		if status in (200, 201, 202, 204, 206):
			if self.is_json(content_type):
				return "json_ok"
			if self.is_html(content_type):
				return "html_ok"
			return "ok"
		if status == 404:
			return "not_found"
		return "other"

	def summarize(self, url: str, status: int, length: int, content_type: Optional[str]) -> Dict[str, str | int]:
		return {
			"url": url,
			"status": status,
			"length": length,
			"type": content_type or "",
			"class": self.classify(status, length, content_type),
		}