from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class DiffResult:
    same_status: bool
    same_length_bucket: bool
    json_keys_overlap: float
    hint: str

class ResponseComparator:
    """Lightweight, privacy‑aware comparator (no full body storage)."""

    def __init__(self, bucket_pct: float = 0.05):
        self.bucket_pct = max(0.01, min(bucket_pct, 0.25))

    def _bucket(self, n: int) -> int:
        if n <= 0:
            return 0
        step = max(50, int(n * self.bucket_pct))
        return (n // step) * step

    def compare(self, r1_status: int, r1_len: int, r1_ct: Optional[str], r1_body: Optional[bytes],
                      r2_status: int, r2_len: int, r2_ct: Optional[str], r2_body: Optional[bytes]) -> DiffResult:
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
        if not same_status:
            hint = "status-diff"
        elif not same_len_bucket and overlap < 0.5:
            hint = "shape-diff"
        else:
            hint = "similar"
        return DiffResult(same_status, same_len_bucket, overlap, hint)

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

