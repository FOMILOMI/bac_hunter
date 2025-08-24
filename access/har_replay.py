from __future__ import annotations
import json
import logging
from typing import Dict, List, Optional, Tuple

from ..config import Identity, Settings
from ..http_client import HttpClient
from ..storage import Storage
from .comparator import ResponseComparator

log = logging.getLogger("access.har")


class HARReplayAnalyzer:
    """Replays requests from a HAR file across different identities and compares responses.
    Only replays safe GET requests by default; optional POST replay can be enabled.
    """

    def __init__(self, settings: Settings, http: HttpClient, db: Storage):
        self.s = settings
        self.http = http
        self.db = db
        self.cmp = ResponseComparator()

    def _iter_har_get_urls(self, har_path: str, max_urls: int = 100) -> List[str]:
        try:
            with open(har_path, "r", encoding="utf-8") as f:
                har = json.load(f)
        except Exception as e:
            log.error("Failed to load HAR: %s", e)
            return []
        urls: List[str] = []
        for entry in (har.get("log", {}).get("entries", []) or []):
            req = entry.get("request", {})
            method = (req.get("method") or "").upper()
            url = req.get("url")
            if method == "GET" and url:
                urls.append(url)
            if len(urls) >= max_urls:
                break
        # de-duplicate preserving order
        seen = set(); out = []
        for u in urls:
            if u not in seen:
                seen.add(u); out.append(u)
        return out

    async def analyze(self, har_path: str, identities: List[Identity], max_urls: int = 100):
        urls = self._iter_har_get_urls(har_path, max_urls=max_urls)
        if len(identities) < 2:
            log.warning("Need at least two identities for HAR replay comparison")
            return
        base = identities[0]
        for other in identities[1:]:
            for u in urls:
                try:
                    ra = await self.http.get(u, headers=base.headers())
                    rb = await self.http.get(u, headers=other.headers())
                except Exception:
                    continue
                self.db.save_probe(url=u, identity=base.name, status=ra.status_code, length=len(ra.content), content_type=ra.headers.get("content-type"), body=b"")
                self.db.save_probe(url=u, identity=other.name, status=rb.status_code, length=len(rb.content), content_type=rb.headers.get("content-type"), body=b"")
                diff = self.cmp.compare(ra.status_code, len(ra.content), ra.headers.get("content-type"), None,
                                        rb.status_code, len(rb.content), rb.headers.get("content-type"), None)
                self.db.save_comparison(url=u, id_a=base.name, id_b=other.name, same_status=diff.same_status, same_length_bucket=diff.same_length_bucket, json_keys_overlap=diff.json_keys_overlap, hint=diff.hint)
                if not diff.same_status or (not diff.same_length_bucket and diff.json_keys_overlap < 0.5):
                    score = 0.65 if not diff.same_status else 0.45
                    self.db.add_finding_for_url(u, type_="har_diff", evidence=f"{base.name} vs {other.name}: {diff.hint}", score=score)

