from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, Optional, Dict

@dataclass
class DiffResult:
    same_status: bool
    same_length_bucket: bool
    json_keys_overlap: float
    hint: str
    # Extended attributes for deeper analysis
    header_similarity: float = 0.0
    set_cookie_changed: bool = False
    time_bucket_same: bool = True

class ResponseComparator:
    """Lightweight, privacy‑aware comparator (no full body storage).
    - status: exact match
    - length bucket: 5% bucket to avoid noise
    - json keys Jaccard: schema-ish overlap for APIs
    - headers: coarse similarity using normalized subset
    - timing: coarse buckets to detect throttling/time-based gates
    """

    def __init__(self, bucket_pct: float = 0.05):
        self.bucket_pct = max(0.01, min(bucket_pct, 0.25))

    def _bucket(self, n: int) -> int:
        if n <= 0:
            return 0
        step = max(50, int(n * self.bucket_pct))
        return (n // step) * step

    def _time_bucket(self, ms: Optional[float]) -> int:
        try:
            t = float(ms or 0.0)
        except Exception:
            t = 0.0
        # 100ms buckets up to 2s, then 500ms
        if t <= 2000:
            step = 100
        else:
            step = 500
        return int(t // step) * step

    def _header_similarity(self, h1: Optional[Dict[str, str]], h2: Optional[Dict[str, str]]) -> float:
        if not h1 and not h2:
            return 1.0
        if not h1 or not h2:
            return 0.0
        def norm(d: Dict[str, str]) -> Dict[str, str]:
            return {str(k).lower(): str(v).lower() for k, v in d.items() if k and v}
        a = norm(h1)
        b = norm(h2)
        # focus on security-relevant headers
        keys = set([
            'content-type','cache-control','pragma','expires','vary','server','x-frame-options','content-security-policy',
            'x-content-type-options','referrer-policy','set-cookie','www-authenticate','location'
        ])
        a_f = {k: a.get(k, '') for k in keys}
        b_f = {k: b.get(k, '') for k in keys}
        match = sum(1 for k in keys if a_f.get(k,'') == b_f.get(k,''))
        return match / max(1, len(keys))

    def _set_cookie_changed(self, h1: Optional[Dict[str, str]], h2: Optional[Dict[str, str]]) -> bool:
        if not h1 and not h2:
            return False
        a = (h1 or {}).get('set-cookie') or ''
        b = (h2 or {}).get('set-cookie') or ''
        return (a != b) and (a or b)

    def compare(self, r1_status: int, r1_len: int, r1_ct: Optional[str], r1_body: Optional[bytes],
                      r2_status: int, r2_len: int, r2_ct: Optional[str], r2_body: Optional[bytes],
                      *, r1_headers: Optional[Dict[str, str]] = None, r2_headers: Optional[Dict[str, str]] = None,
                      r1_elapsed_ms: Optional[float] = None, r2_elapsed_ms: Optional[float] = None) -> DiffResult:
        same_status = (r1_status == r2_status)
        same_len_bucket = (self._bucket(r1_len) == self._bucket(r2_len))
        overlap = 0.0
        hint = ""
        if r1_ct and r2_ct and "json" in (r1_ct + r2_ct).lower():
            k1 = self._json_keys(r1_body)
            k2 = self._json_keys(r2_body)
            if k1 or k2:
                inter = len(k1 & k2)
                union = len(k1 | k2) or 1
                overlap = inter / union
        hdr_sim = self._header_similarity(r1_headers, r2_headers)
        cookie_changed = self._set_cookie_changed(r1_headers, r2_headers)
        time_bucket_same = (self._time_bucket(r1_elapsed_ms) == self._time_bucket(r2_elapsed_ms))
        if not same_status:
            hint = "status-diff"
        elif not same_len_bucket and overlap < 0.5:
            hint = "shape-diff"
        elif cookie_changed and same_status:
            hint = "cookie-changed"
        elif hdr_sim < 0.6:
            hint = "header-diff"
        elif not time_bucket_same:
            hint = "timing-diff"
        else:
            hint = "similar"
        return DiffResult(same_status, same_len_bucket, overlap, hint, header_similarity=hdr_sim, set_cookie_changed=cookie_changed, time_bucket_same=time_bucket_same)

    def _json_keys(self, body: Optional[bytes]) -> set[str]:
        try:
            if not body:
                return set()
            data = json.loads(body.decode(errors="ignore"))
            return self._collect_keys(data)
        except Exception:
            return set()

    def _collect_keys(self, obj: Any, prefix: str = "") -> set[str]:
        keys = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                tag = f"{prefix}.{k}" if prefix else str(k)
                keys.add(tag)
                keys |= self._collect_keys(v, tag)
        elif isinstance(obj, list) and obj:
            keys |= self._collect_keys(obj[0], prefix)
        return keys
