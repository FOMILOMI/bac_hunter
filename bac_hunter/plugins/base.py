from __future__ import annotations
import abc
from typing import List

try:
	from ..config import Settings
	from ..http_client import HttpClient
	from ..storage import Storage
except Exception:
	from config import Settings
	from http_client import HttpClient
	from storage import Storage


class Plugin(abc.ABC):
	name: str = "plugin"
	category: str = "misc"

	def __init__(self, settings: Settings, http: HttpClient, db: Storage):
		"""Base plugin initializer.

		Parameters:
		- settings: Global `Settings` object
		- http: Shared `HttpClient`
		- db: Persistent `Storage`
		"""
		self.settings = settings
		self.http = http
		self.db = db

	@abc.abstractmethod
	async def run(self, base_url: str, target_id: int) -> List[str]:
		"""Run the plugin and return a list of discovered URLs/endpoints.

		Implementations should handle their own error cases and return
		an empty list on failure in order to keep the scan resilient.
		"""
		raise NotImplementedError
