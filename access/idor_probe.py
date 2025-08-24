from __future__ import annotations
import logging
import re
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl
from typing import List

from ..config import Identity, Settings
from ..http_client import HttpClient
from ..storage import Storage
from .comparator import ResponseComparator

log = logging.getLogger("access.idor")

ID_RE = re.compile(r"(?P<id>\b\d{1,10}\b)")
UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b")

class IDORProbe:
    def __init__(self, settings: Settings, http: HttpClient, db: Storage):
        self.s = settings
        self.http = http
        self.db = db
        self.cmp = ResponseComparator()

    def variants(self, url: str, max_variants: int = 3) -> List[str]:
        parsed = urlparse(url)
        path = parsed.path
        out: List[str] = []
        # numeric path ids
        def repl_num(m: re.Match):
            n = int(m.group("id"))
            return str(max(0, n + 1))
        p2 = ID_RE.sub(repl_num, path, count=1)
        if p2 != path:
            out.append(urlunparse(parsed._replace(path=p2)))
        # uuid flip last nibble
        def repl_uuid(m: re.Match):
            u = m.group(0)
            return u[:-1] + ("f" if u[-1].lower() != "f" else "e")
        p3 = UUID_RE.sub(repl_uuid, path, count=1)
        if p3 != path:
            out.append(urlunparse(parsed._replace(path=p3)))
        # query numeric bump
        q = parsed.query
        q2 = ID_RE.sub(lambda m: str(max(0, int(m.group("id")) + 1)), q, count=1)
        if q2 != q:
            out.append(urlunparse(parsed._replace(query=q2)))
        # duplicate last path segment (common list/detail pattern)
        segs = [s for s in path.split('/') if s]
        if segs:
            dup = '/' + '/'.join(segs + [segs[-1]])
            if dup != path:
                out.append(urlunparse(parsed._replace(path=dup)))
        # boolean flips in query
        params = parse_qsl(parsed.query, keep_blank_values=True)
        for i, (k, v) in enumerate(params):
            lv = (v or '').lower()
            if lv in ("true", "false", "1", "0", "yes", "no"):
                new = params.copy()
                new[i] = (k, "false" if lv in ("true", "1", "yes") else "true")
                out.append(urlunparse(parsed._replace(query=urlencode(new, doseq=True))))
                break
        # uniq and cap
        uniq = []
        seen = set()
        for u in out:
            if u not in seen:
                seen.add(u); uniq.append(u)
        return uniq[:max_variants]

    async def test(self, base_url: str, url: str, low_priv: Identity, other_priv: Identity) -> None:
        r0 = await self.http.get(url, headers=low_priv.headers())
        self.db.save_probe(url=url, identity=low_priv.name, status=r0.status_code, length=len(r0.content), content_type=r0.headers.get("content-type"), body=b"")
        for v in self.variants(url):
            rv = await self.http.get(v, headers=low_priv.headers())
            self.db.save_probe(url=v, identity=low_priv.name, status=rv.status_code, length=len(rv.content), content_type=rv.headers.get("content-type"), body=b"")
            ro = await self.http.get(v, headers=other_priv.headers())
            self.db.save_probe(url=v, identity=other_priv.name, status=ro.status_code, length=len(ro.content), content_type=ro.headers.get("content-type"), body=b"")
            diff = self.cmp.compare(r0.status_code, len(r0.content), r0.headers.get("content-type"), None,
                                    rv.status_code, len(rv.content), rv.headers.get("content-type"), None)
            if rv.status_code in (200, 206) and (not diff.same_status or not diff.same_length_bucket):
                hint = f"baseline->{rv.status_code} diff={diff.hint} other={ro.status_code}"
                self.db.add_finding_for_url(v, type_="idor_suspect", evidence=hint, score=0.75)
                log.info("IDOR candidate: %s", v)