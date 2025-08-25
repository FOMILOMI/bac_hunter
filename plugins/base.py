from __future__ import annotations
import abc
from typing import List

from ..bac_hunter.config import Settings
from ..bac_hunter.core.http_client import HttpClient
from ..bac_hunter.core.storage import Storage


class Plugin(abc.ABC):
	name: str = "plugin"
	category: str = "misc"

	def __init__(self, settings: Settings, http: HttpClient, db: Storage):
		self.settings = settings
		self.http = http
		self.db = db

	@abc.abstractmethod
	async def run(self, base_url: str, target_id: int) -> List[str]:
		"""Run plugin work; returns list of discovered URLs/endpoints."""
		raise NotImplementedError
