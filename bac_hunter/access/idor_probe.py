from __future__ import annotations
import logging
import re
import asyncio
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl, urlsplit, urlunsplit
from typing import List, Dict, Tuple, Iterable

try:
	from ..config import Identity, Settings
	from ..http_client import HttpClient
	from ..storage import Storage
	from ..utils import normalize_url, is_recursive_duplicate_path
	from .comparator import ResponseComparator
except Exception:
	from config import Identity, Settings
	from http_client import HttpClient
	from storage import Storage
	from utils import normalize_url, is_recursive_duplicate_path
	from access.comparator import ResponseComparator

log = logging.getLogger("access.idor")

ID_RE = re.compile(r"(?P<id>\b\d{1,10}\b)")
UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b")
# Broad hex-like identifier (e.g., Mongo/ObjectId-like or tokens), conservative to avoid noise
HEXLIKE_RE = re.compile(r"\b[0-9a-fA-F]{8,32}\b")

# Heuristic parameter scoring for IDOR-likelihood
PARAM_HINTS = (
	("id", 0.6), ("user", 0.5), ("account", 0.5), ("owner", 0.45), ("tenant", 0.45),
	("customer", 0.4), ("client", 0.4), ("org", 0.4), ("project", 0.35), ("company", 0.35),
)


class IDORProbe:
    def __init__(self, settings: Settings, http: HttpClient, db: Storage):
        self.s = settings
        self.http = http
        self.db = db
        self.cmp = ResponseComparator()

    # --- Internal helpers ---
    def _score_param(self, name: str) -> float:
        ln = name.lower()
        score = 0.1
        for hint, w in PARAM_HINTS:
            if hint in ln:
                score = max(score, w)
        return score

    def _collect_correlated_values(self, base_url: str) -> Tuple[Dict[str, List[str]], Dict[int, List[str]]]:
        """Collect observed values per query parameter name and per path segment index.
        Returns (param_name_to_values, path_index_to_values)
        """
        try:
            tid = self.db.ensure_target(base_url)
        except Exception:
            return {}, {}
        param_values: Dict[str, List[str]] = {}
        path_values: Dict[int, List[str]] = {}
        seen_pairs: set[Tuple[str, str]] = set()
        seen_path: set[Tuple[int, str]] = set()
        # Iterate known URLs for this target
        try:
            urls: Iterable[str] = self.db.iter_target_urls(tid)
        except Exception:
            urls = []
        for u in urls:
            try:
                sp = urlsplit(u)
                # query params
                for k, v in parse_qsl(sp.query, keep_blank_values=True):
                    key = k.strip()
                    val = v.strip()
                    if not key or not val:
                        continue
                    if (key, val) in seen_pairs:
                        continue
                    if ID_RE.fullmatch(val) or UUID_RE.fullmatch(val) or HEXLIKE_RE.fullmatch(val):
                        param_values.setdefault(key, []).append(val)
                        seen_pairs.add((key, val))
                # path segments (only last 6 segments to reduce noise)
                segs = [s for s in sp.path.split('/') if s]
                for idx, seg in enumerate(segs[-6:]):
                    if (idx, seg) in seen_path:
                        continue
                    if ID_RE.fullmatch(seg) or UUID_RE.fullmatch(seg) or HEXLIKE_RE.fullmatch(seg):
                        path_values.setdefault(idx, []).append(seg)
                        seen_path.add((idx, seg))
            except Exception:
                continue
        # dedup lists
        for k in list(param_values.keys()):
            seen = set()
            uniq = []
            for v in param_values[k]:
                if v not in seen:
                    seen.add(v)
                    uniq.append(v)
            param_values[k] = uniq
        for i in list(path_values.keys()):
            seen = set()
            uniq = []
            for v in path_values[i]:
                if v not in seen:
                    seen.add(v)
                    uniq.append(v)
            path_values[i] = uniq
        return param_values, path_values

    def _fuzzy_mutations_for_id(self, value: str) -> List[str]:
        outs: List[str] = []
        if ID_RE.fullmatch(value):
            try:
                n = int(value)
                for delta in (-10, -1, 1, 10):
                    m = max(0, n + delta)
                    if str(m) != value:
                        outs.append(str(m))
                # zero-pad variant if looks padded
                if value.startswith('0') and len(value) > 1:
                    outs.append(value.lstrip('0') or '0')
            except Exception:
                pass
        elif UUID_RE.fullmatch(value):
            # flip last nibble and another random earlier nibble deterministically (pos -2)
            try:
                u = list(value)
                # last nibble
                u[-1] = 'f' if u[-1].lower() != 'f' else 'e'
                outs.append(''.join(u))
                # second last hex of last group (ensure hex)
                v = list(value)
                if re.match(r"[0-9a-fA-F]", v[-2] or ''):
                    v[-2] = 'a' if v[-2].lower() != 'a' else 'b'
                    outs.append(''.join(v))
            except Exception:
                pass
        elif HEXLIKE_RE.fullmatch(value):
            try:
                h = list(value)
                pos = -1
                if re.match(r"[0-9a-fA-F]", h[pos] or ''):
                    h[pos] = 'f' if h[pos].lower() != 'f' else 'e'
                    outs.append(''.join(h))
                pos = -2
                if len(value) > 2 and re.match(r"[0-9a-fA-F]", h[pos] or ''):
                    h2 = list(value)
                    h2[pos] = 'a' if h2[pos].lower() != 'a' else 'b'
                    outs.append(''.join(h2))
            except Exception:
                pass
        return outs[:4]

    def _rank_params(self, params: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        return sorted(params, key=lambda kv: self._score_param(kv[0]), reverse=True)

    def variants(self, base_url: str, url: str, max_variants: int = 8) -> List[str]:
        parsed = urlparse(url)
        path = parsed.path
        out: List[str] = []
        # numeric path ids (simple + fuzzy)
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
        # duplicate last path segment only for numeric/UUID segments (avoid /admin/admin)
        segs = [s for s in path.split('/') if s]
        if segs:
            last = segs[-1]
            is_numeric = bool(re.fullmatch(r"\b\d{1,10}\b", last))
            is_uuid = bool(UUID_RE.fullmatch(last))
            if is_numeric or is_uuid:
                dup = '/' + '/'.join(segs + [last])
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
        # --- Advanced: correlation-based substitutions and fuzzy IDs ---
        try:
            param_values, path_values = self._collect_correlated_values(base_url)
        except Exception:
            param_values, path_values = {}, {}
        # Use ranked params to prefer likely IDOR fields
        ranked_params = self._rank_params(params)
        for (name, value) in ranked_params[:3]:
            candidates = (param_values.get(name) or [])
            # Add fuzzy variants around current value
            candidates = list(dict.fromkeys(candidates + self._fuzzy_mutations_for_id(value)))
            for cand in candidates[:3]:
                if cand and cand != value:
                    new_params = []
                    for (pk, pv) in params:
                        if pk == name:
                            new_params.append((pk, cand))
                        else:
                            new_params.append((pk, pv))
                    newp = parsed._replace(query=urlencode(new_params, doseq=True))
                    out.append(urlunparse(newp))
        # Path segment substitutions using correlated values by position (from the end)
        segs = [s for s in parsed.path.split('/') if s]
        if segs:
            for rel_idx in range(1, min(4, len(segs)) + 1):
                seg = segs[-rel_idx]
                if ID_RE.fullmatch(seg) or UUID_RE.fullmatch(seg) or HEXLIKE_RE.fullmatch(seg):
                    candidates = path_values.get(len(segs[-6:]) - rel_idx) or []
                    candidates = list(dict.fromkeys(candidates + self._fuzzy_mutations_for_id(seg)))
                    for cand in candidates[:3]:
                        if cand and cand != seg:
                            new_segs = list(segs)
                            new_segs[-rel_idx] = cand
                            out.append(urlunparse(parsed._replace(path='/' + '/'.join(new_segs))))
        # normalize, drop recursive duplicates and dedup
        uniq: List[str] = []
        seen = set()
        for u in out:
            try:
                nu = normalize_url(u)
            except Exception:
                nu = u
            if is_recursive_duplicate_path(urlparse(nu).path):
                if getattr(self.s, 'smart_dedup_enabled', False):
                    log.info("[!] Skipping nonsensical path expansion: %s", nu)
                continue
            if nu not in seen:
                seen.add(nu); uniq.append(nu)
        return uniq[:max_variants]

    async def test(self, base_url: str, url: str, low_priv: Identity, other_priv: Identity) -> None:
        base_n = normalize_url(url)
        r0 = await self.http.get(base_n, headers=low_priv.headers(), context="idor:baseline:low")
        self.db.save_probe(url=base_n, identity=low_priv.name, status=r0.status_code, length=len(r0.content), content_type=r0.headers.get("content-type"), body=b"")
        if getattr(self.s, 'smart_backoff_enabled', False) and r0.status_code == 429:
            log.warning("[!] Rate limited (429) on %s, backing off", base_n)
            await asyncio.sleep(2.0)
        for v in self.variants(base_url, base_n):
            rv = await self.http.get(v, headers=low_priv.headers(), context="idor:variant:low")
            self.db.save_probe(url=v, identity=low_priv.name, status=rv.status_code, length=len(rv.content), content_type=rv.headers.get("content-type"), body=b"")
            if getattr(self.s, 'smart_backoff_enabled', False) and rv.status_code == 429:
                log.warning("[!] Rate limited (429) on %s, backing off", v)
                await asyncio.sleep(2.0)
            ro = await self.http.get(v, headers=other_priv.headers(), context="idor:variant:other")
            self.db.save_probe(url=v, identity=other_priv.name, status=ro.status_code, length=len(ro.content), content_type=ro.headers.get("content-type"), body=b"")
            if getattr(self.s, 'smart_backoff_enabled', False) and ro.status_code == 429:
                log.warning("[!] Rate limited (429) on %s (other), backing off", v)
                await asyncio.sleep(2.0)
            diff = self.cmp.compare(r0.status_code, len(r0.content), r0.headers.get("content-type"), None,
                                    rv.status_code, len(rv.content), rv.headers.get("content-type"), None)
            # persist comparison for later ML/analytics
            try:
                self.db.save_comparison(url=v, id_a=low_priv.name, id_b=other_priv.name, same_status=diff.same_status, same_length_bucket=diff.same_length_bucket, json_keys_overlap=diff.json_keys_overlap, hint=diff.hint)
            except Exception:
                pass
            if rv.status_code in (200, 206) and (not diff.same_status or not diff.same_length_bucket):
                hint = f"baseline->{rv.status_code} diff={diff.hint} other={ro.status_code}"
                self.db.add_finding_for_url(v, type_="idor_suspect", evidence=hint, score=0.85 if ro.status_code in (401,403) else 0.75)
                log.info("IDOR candidate: %s", v)