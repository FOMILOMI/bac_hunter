from __future__ import annotations
import json
import os
import time
from typing import Any, Dict, Optional, Tuple


DEFAULT_AUTH_PATH = os.path.abspath(os.environ.get("BH_AUTH_DATA", "auth_data.json"))


def _now() -> float:
    return time.time()


def _cookie_is_valid(cookie: dict) -> bool:
    try:
        exp = cookie.get("expires")
        if exp is None:
            exp = cookie.get("expiry")
        if exp in (None, 0, "0", ""):
            return True
        try:
            expf = float(exp)
        except Exception:
            return True
        return expf > _now()
    except Exception:
        return True


def read_auth(path: Optional[str] = None) -> Dict[str, Any]:
    p = os.path.abspath(path or DEFAULT_AUTH_PATH)
    if not os.path.exists(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        # normalize structure
        if not isinstance(data.get("cookies"), list):
            data["cookies"] = []
        return data
    except Exception:
        return {}


def write_auth(data: Dict[str, Any], path: Optional[str] = None) -> None:
    p = os.path.abspath(path or DEFAULT_AUTH_PATH)
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def auth_headers_from_store(data: Dict[str, Any], base_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h: Dict[str, str] = {}
    if base_headers:
        h.update(base_headers)
    # cookie header
    cookies = [c for c in (data.get("cookies") or []) if isinstance(c, dict) and _cookie_is_valid(c)]
    pairs = []
    for c in cookies:
        name = c.get("name")
        val = c.get("value")
        if name and (val is not None):
            pairs.append(f"{name}={val}")
    if pairs:
        h["Cookie"] = "; ".join(pairs)
    # bearer
    bearer = data.get("bearer") or data.get("token") or None
    if isinstance(bearer, str) and bearer:
        h["Authorization"] = f"Bearer {bearer}"
    # optional csrf
    csrf = data.get("csrf")
    if csrf and isinstance(csrf, str):
        # do not force header name here; callers can merge
        h.setdefault("X-CSRF-Token", csrf)
    # merge extra headers snapshot if present
    extra = data.get("headers")
    if isinstance(extra, dict):
        for k, v in extra.items():
            if v is not None:
                h[k] = v
    return h


def is_auth_still_valid(data: Dict[str, Any]) -> bool:
    # valid if any non-expired auth cookie exists or bearer present and not past optional exp
    try:
        cookies = data.get("cookies") or []
        if cookies:
            # Check if any cookie is valid (not expired)
            for c in cookies:
                if _cookie_is_valid(c):
                    # If we have any valid cookie, consider session valid
                    return True
    except Exception:
        pass
    
    # bearer exp support
    try:
        bearer = data.get("bearer") or data.get("token")
        if bearer and isinstance(bearer, str):
            # check optional exp fields
            exp = data.get("bearer_exp") or data.get("token_exp")
            if exp is None:
                return True
            try:
                return float(exp) > _now()
            except Exception:
                return True
    except Exception:
        pass
    
    # Check if we have any headers that might indicate a valid session
    try:
        headers = data.get("headers") or {}
        if headers:
            # If we have any headers, consider it potentially valid
            return True
    except Exception:
        pass
    
    return False


async def probe_auth_valid(http_client, url: str, data: Dict[str, Any]) -> Tuple[bool, Optional[int]]:
    """Perform a lightweight GET to validate auth. Returns (ok, status_code)."""
    try:
        from .utils import normalize_url
    except Exception:
        from utils import normalize_url
    try:
        u = normalize_url(url)
    except Exception:
        u = url
    headers = auth_headers_from_store(data, base_headers={"X-BH-Identity": "auth-probe"})
    try:
        r = await http_client.get(u, headers=headers, context="auth:probe")
        if r.status_code in (401, 403):
            return False, r.status_code
        return True, r.status_code
    except Exception:
        return False, None

