from __future__ import annotations
import logging
from typing import List
from urllib.parse import urljoin

from ...storage import Storage
from ...http_client import HttpClient
from ...config import Settings
from ..base import Plugin

log = logging.getLogger("recon.robots")


class RobotsRecon(Plugin):
    name = "robots.txt"
    category = "recon"

    async def run(self, base_url: str, target_id: int) -> List[str]:
        url = urljoin(base_url, "/robots.txt")
        r = await self.http.get(url)
        self.db.save_page(target_id, url, r.status_code, r.headers.get("content-type"), r.content)
        found: List[str] = []
        if r.status_code == 200 and r.text:
            for line in r.text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.lower().startswith("allow:") or line.lower().startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()
                    if path and path != "/":
                        candidate = urljoin(base_url, path)
                        found.append(candidate)
                        # store as potential sensitive path (force-browse candidate)
                        self.db.add_finding(target_id, "robots_path", candidate, evidence=line, score=0.2)
        log.info("%s -> %d paths", self.name, len(found))
        return found

