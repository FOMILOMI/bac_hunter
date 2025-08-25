from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _env(key: str, default: Optional[str] = None) -> str:
    return os.environ.get(key, default) if os.environ.get(key) is not None else (default or "")


@dataclass
class Identity:
    name: str
    base_headers: Dict[str, str] = field(default_factory=dict)
    cookie: Optional[str] = None
    auth_bearer: Optional[str] = None

    def headers(self) -> Dict[str, str]:
        h = {"User-Agent": self.base_headers.get("User-Agent", "bac-hunter/1.0 (+respectful)")}
        if self.cookie:
            h["Cookie"] = self.cookie
        if self.auth_bearer:
            h["Authorization"] = f"Bearer {self.auth_bearer}"
        for k, v in self.base_headers.items():
            h[k] = v
        return h


@dataclass
class Settings:
    max_concurrency: int = int(_env("BH_MAX_CONCURRENCY", "6"))
    max_rps: float = float(_env("BH_MAX_RPS", "3.0"))
    per_host_rps: float = float(_env("BH_PER_HOST_RPS", "1.5"))
    timeout_seconds: float = float(_env("BH_TIMEOUT", "15"))
    retry_times: int = int(_env("BH_RETRY_TIMES", "2"))
    proxy: Optional[str] = _env("BH_PROXY") or None
    random_jitter_ms: int = int(_env("BH_JITTER_MS", "250"))

    db_path: str = _env("BH_DB", "bac_hunter.db")

    obey_robots: bool = _env("BH_OBEY_ROBOTS", "true").lower() == "true"

    allowed_domains: List[str] = field(default_factory=lambda: [])
    blocked_url_patterns: List[str] = field(default_factory=lambda: [])

    identities: List[Identity] = field(default_factory=lambda: [
        Identity(name="anon", base_headers={"User-Agent": "Mozilla/5.0 bac-hunter"}),
    ])

    targets: List[str] = field(default_factory=list)

    enable_recon_robots: bool = True
    enable_recon_sitemap: bool = True
    enable_recon_js_endpoints: bool = True

    enable_adaptive_throttle: bool = _env("BH_ADAPTIVE_THROTTLE", "true").lower() == "true"
    enable_waf_detection: bool = _env("BH_WAF_DETECT", "true").lower() == "true"

    enable_ua_rotation: bool = _env("BH_UA_ROTATE", "true").lower() == "true"
    ua_rotate_per_request: bool = _env("BH_UA_ROTATE_PER_REQ", "false").lower() == "true"

    cache_enabled: bool = _env("BH_CACHE", "true").lower() == "true"
    cache_ttl_seconds: int = int(_env("BH_CACHE_TTL", "300"))
    cache_max_entries: int = int(_env("BH_CACHE_MAX", "2000"))

    enable_cors_probe: bool = _env("BH_CORS_PROBE", "false").lower() == "true"
    cors_probe_origin: str = _env("BH_CORS_ORIGIN", "https://evil.bac-hunter.invalid")

    generic_webhook: Optional[str] = _env("BH_GENERIC_WEBHOOK") or None
    slack_webhook: Optional[str] = _env("BH_SLACK_WEBHOOK") or None
    discord_webhook: Optional[str] = _env("BH_DISCORD_WEBHOOK") or None
    notify_min_severity: float = float(_env("BH_NOTIFY_MIN", "0.75"))

