from __future__ import annotations
import logging
from typing import List
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

from ...core.storage import Storage
from ...core.http_client import HttpClient
from ...config import Settings
from ..base import Plugin

log = logging.getLogger("recon.sitemap")


class SitemapRecon(Plugin):
    name = "sitemap"
    category = "recon"

    async def run(self, base_url: str, target_id: int) -> List[str]:
        url = urljoin(base_url, "/sitemap.xml")
        r = await self.http.get(url)
        self.db.save_page(target_id, url, r.status_code, r.headers.get("content-type"), r.content)
        out: List[str] = []
        if r.status_code == 200 and r.text:
            try:
                root = ET.fromstring(r.text)
                for loc in root.findall("{*}url/{*}loc"):
                    if loc.text:
                        out.append(loc.text.strip())
            except Exception:
                pass
        for u in out:
            self.db.add_finding(target_id, "endpoint", u, evidence="sitemap", score=0.25)
        log.info("%s -> %d endpoints", self.name, len(out))
        return out

