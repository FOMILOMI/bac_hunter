from __future__ import annotations
import logging
from typing import List
from urllib.parse import urljoin

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

log = logging.getLogger("recon.robots")


class RobotsRecon(Plugin):
    name = "robots.txt"
    category = "recon"

    async def run(self, base_url: str, target_id: int) -> List[str]:
        url = urljoin(base_url, "/robots.txt")
        r = await self.http.get(url)
        self.db.save_page(target_id, url, r.status_code, r.headers.get("content-type"), r.content)
        found_set = set()
        if r.status_code == 200 and r.text:
            for line in r.text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.lower().startswith("allow:") or line.lower().startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()
                    if not path or path == "/":
                        continue
                    candidate = urljoin(base_url, path)
                    try:
                        from ...utils import normalize_url, is_recursive_duplicate_path
                    except Exception:
                        from utils import normalize_url, is_recursive_duplicate_path
                    candidate_n = normalize_url(candidate)
                    # Skip recursive nonsense
                    if is_recursive_duplicate_path(candidate_n.split('://',1)[-1].split('/',1)[-1] if '://' in candidate_n else candidate_n):
                        if getattr(self.settings, 'smart_dedup_enabled', False):
                            log.info("[SKIP] Duplicate endpoint %s", candidate_n)
                        continue
                    if candidate_n in found_set:
                        if getattr(self.settings, 'smart_dedup_enabled', False):
                            log.info("[SKIP] Duplicate endpoint %s", candidate_n)
                        continue
                    found_set.add(candidate_n)
                    # store as potential sensitive path (force-browse candidate)
                    self.db.add_finding(target_id, "robots_path", candidate_n, evidence=line, score=0.2)
        found = sorted(found_set)
        log.info("%s -> %d paths", self.name, len(found))
        return found

