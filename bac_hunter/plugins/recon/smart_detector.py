from __future__ import annotations
import logging
import re
from typing import List, Set
from urllib.parse import urljoin

from ...core.storage import Storage
from ...core.http_client import HttpClient
from ...config import Settings
from ..base import Plugin

log = logging.getLogger("recon.smart")

API_HINT = re.compile(r"/(api|v1|v2)/", re.IGNORECASE)


class SmartEndpointDetector(Plugin):
    name = "smart-detector"
    category = "recon"

    async def run(self, base_url: str, target_id: int) -> List[str]:
        start = base_url if base_url.endswith("/") else base_url + "/"
        found: Set[str] = set()
        try:
            r = await self.http.get(start)
            self.db.save_page(target_id, start, r.status_code, r.headers.get("content-type"), r.content)
            if r.status_code == 200 and r.text:
                for m in re.finditer(r"href=\"([^\"]+)\"", r.text, flags=re.I):
                    href = m.group(1)
                    if API_HINT.search(href):
                        found.add(urljoin(base_url, href))
        except Exception:
            pass
        for u in sorted(found):
            self.db.add_finding(target_id, "endpoint", u, evidence="smart", score=0.35)
        log.info("%s -> %d endpoints", self.name, len(found))
        return sorted(found)

