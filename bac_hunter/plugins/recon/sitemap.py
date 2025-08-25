from __future__ import annotations
import logging
from typing import List
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

try:
	from ...storage import Storage
	from ...http_client import HttpClient
	from ...config import Settings
	from ..base import Plugin
except Exception:
	from storage import Storage
	from http_client import HttpClient
	from config import Settings
	from plugins.base import Plugin

log = logging.getLogger("recon.sitemap")


class SitemapRecon(Plugin):
    name = "sitemap.xml"
    category = "recon"

    async def run(self, base_url: str, target_id: int) -> List[str]:
        urls = [urljoin(base_url, "/sitemap.xml"), urljoin(base_url, "/sitemap_index.xml")]
        found: List[str] = []
        for url in urls:
            r = await self.http.get(url)
            self.db.save_page(target_id, url, r.status_code, r.headers.get("content-type"), r.content)
            if r.status_code != 200 or not r.content:
                continue
            try:
                root = ET.fromstring(r.content)
                ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
                # Either index or urlset
                for loc in root.findall(f".//{ns}loc"):
                    loc_text = (loc.text or "").strip()
                    if loc_text:
                        found.append(loc_text)
            except ET.ParseError:
                continue
        log.info("%s -> %d URLs", self.name, len(found))
        return found

