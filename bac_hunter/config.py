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
    cookie: Optional[str] = None  # raw Cookie header (optional)
    auth_bearer: Optional[str] = None  # JWT/Token (optional)

    def headers(self) -> Dict[str, str]:
        h = {"User-Agent": self.base_headers.get("User-Agent", "bac-hunter/1.0 (+respectful)")}
        if self.cookie:
            h["Cookie"] = self.cookie
        if self.auth_bearer:
            h["Authorization"] = f"Bearer {self.auth_bearer}"
        # Allow user extras to override
        for k, v in self.base_headers.items():
            h[k] = v
        return h


@dataclass
class Settings:
    # Networking / safety
    max_concurrency: int = int(_env("BH_MAX_CONCURRENCY", "6"))
    max_rps: float = float(_env("BH_MAX_RPS", "3.0"))  # global cap (req/sec)
    per_host_rps: float = float(_env("BH_PER_HOST_RPS", "1.5"))
    timeout_seconds: float = float(_env("BH_TIMEOUT", "15"))
    retry_times: int = int(_env("BH_RETRY_TIMES", "2"))
    proxy: Optional[str] = _env("BH_PROXY") or None  # e.g. http://127.0.0.1:8080 for Burp
    random_jitter_ms: int = int(_env("BH_JITTER_MS", "250"))

    # Storage
    db_path: str = _env("BH_DB", "bac_hunter.db")
    # Sessions storage directory (per-domain JSON files)
    sessions_dir: str = _env("BH_SESSIONS_DIR", "sessions")

    # Respectful modes
    obey_robots: bool = _env("BH_OBEY_ROBOTS", "true").lower() == "true"

    # Scope policy
    allowed_domains: List[str] = field(default_factory=lambda: [])
    blocked_url_patterns: List[str] = field(default_factory=lambda: [])

    # Identities (lightweight; extended via session_manager)
    identities: List[Identity] = field(default_factory=lambda: [
        Identity(name="anon", base_headers={"User-Agent": "Mozilla/5.0 bac-hunter"}),
    ])

    # Target(s)
    targets: List[str] = field(default_factory=list)  # domains or URLs

    # Feature flags
    enable_recon_robots: bool = True
    enable_recon_sitemap: bool = True
    enable_recon_js_endpoints: bool = True

    # Adaptive throttling and safety
    enable_adaptive_throttle: bool = _env("BH_ADAPTIVE_THROTTLE", "true").lower() == "true"
    enable_waf_detection: bool = _env("BH_WAF_DETECT", "true").lower() == "true"

    # User-Agent rotation / request randomization
    enable_ua_rotation: bool = _env("BH_UA_ROTATE", "true").lower() == "true"
    ua_rotate_per_request: bool = _env("BH_UA_ROTATE_PER_REQ", "false").lower() == "true"
    enable_request_randomization: bool = _env("BH_REQ_RANDOMIZE", "false").lower() == "true"
    enable_encoding_bypass: bool = _env("BH_ENCODING_BYPASS", "false").lower() == "true"

    # Caching (in-memory, GET only)
    cache_enabled: bool = _env("BH_CACHE", "true").lower() == "true"
    cache_ttl_seconds: int = int(_env("BH_CACHE_TTL", "300"))
    cache_max_entries: int = int(_env("BH_CACHE_MAX", "2000"))

    # CORS probing (extra single GET with Origin header)
    enable_cors_probe: bool = _env("BH_CORS_PROBE", "false").lower() == "true"
    cors_probe_origin: str = _env("BH_CORS_ORIGIN", "https://evil.bac-hunter.invalid")

    # Notifications / webhooks
    generic_webhook: Optional[str] = _env("BH_GENERIC_WEBHOOK") or None
    slack_webhook: Optional[str] = _env("BH_SLACK_WEBHOOK") or None
    discord_webhook: Optional[str] = _env("BH_DISCORD_WEBHOOK") or None
    notify_min_severity: float = float(_env("BH_NOTIFY_MIN", "0.75"))

    # Smart discovery controls (default off to preserve backward compatibility)
    smart_dedup_enabled: bool = _env("BH_SMART_DEDUP", "false").lower() == "true"
    smart_backoff_enabled: bool = _env("BH_SMART_BACKOFF", "false").lower() == "true"

    # Intelligent output verbosity: debug|smart|results
    verbosity: str = _env("BH_VERBOSITY", "smart")
    # Context-aware deduplication toggle (separate from smart_dedup_enabled to maintain legacy behavior)
    context_aware_dedup: bool = _env("BH_CONTEXT_DEDUP", "true").lower() == "true"

    # Semi-automatic authentication flow
    enable_semi_auto_login: bool = _env("BH_SEMI_AUTO_LOGIN", "true").lower() == "true"
    login_timeout_seconds: int = int(_env("BH_LOGIN_TIMEOUT", "180"))
    browser_driver: str = _env("BH_BROWSER", "playwright")  # playwright|selenium
