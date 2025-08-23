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

    # Respectful modes
    obey_robots: bool = _env("BH_OBEY_ROBOTS", "true").lower() == "true"

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
