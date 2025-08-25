from __future__ import annotations
import logging
from typing import List
from urllib.parse import urljoin
import json

from ...core.http_client import HttpClient
from ...core.storage import Storage
from ...config import Settings
from ..base import Plugin

log = logging.getLogger("recon.graphql")


class GraphQLRecon(Plugin):
    name = "graphql"
    category = "recon"

    async def run(self, base_url: str, target_id: int) -> List[str]:
        endpoints = ["/graphql", "/api/graphql"]
        found: List[str] = []
        for path in endpoints:
            url = urljoin(base_url, path)
            try:
                r = await self.http.post(url, json={"query": "{ __typename }"})
                self.db.save_page(target_id, url, r.status_code, r.headers.get("content-type"), r.content)
                if r.status_code in (200, 400) and ("application/json" in r.headers.get("content-type", "").lower()):
                    found.append(url)
                    self.db.add_finding(target_id, "graphql_endpoint", url, evidence="recon", score=0.5)
            except Exception:
                continue
        log.info("%s -> %d endpoints", self.name, len(found))
        return found

