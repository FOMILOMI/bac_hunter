from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
	from ..config import Settings, Identity
	from ..http_client import HttpClient
	from ..storage import Storage
except Exception:
	from config import Settings, Identity
	from http_client import HttpClient
	from storage import Storage


@dataclass
class AuthDiscoveryResult:
    login_urls: List[str]
    register_urls: List[str]
    reset_urls: List[str]
    oauth_urls: List[str]
    session_token_hint: Optional[str]
    role_map: Dict[str, Dict[str, int]]
    framework_hint: Optional[str]


class AutonomousAuthEngine:
    """Autonomous Authentication Discovery and Analysis.

    - Discovers auth-related endpoints via light heuristics
    - Infers session token style (cookie vs bearer)
    - Builds a minimal role impact map using provided identities
    """

    LOGIN_RE = re.compile(r"\b(login|signin|sign-in|/auth/|/account/login|/user/login)\b", re.IGNORECASE)
    REGISTER_RE = re.compile(r"\b(register|signup|sign-up|create[-_ ]?account)\b", re.IGNORECASE)
    RESET_RE = re.compile(r"\b(reset|forgot[-_ ]?password|recover)\b", re.IGNORECASE)
    OAUTH_RE = re.compile(r"\b(oauth|openid|sso|saml)\b", re.IGNORECASE)

    def __init__(self, settings: Settings, http: HttpClient, db: Storage):
        self.s = settings
        self.http = http
        self.db = db

    async def discover(self, base_url: str, unauth: Identity, auth: Optional[Identity]) -> AuthDiscoveryResult:
        from urllib.parse import urljoin

        start = base_url if base_url.endswith('/') else base_url + '/'
        try:
            r = await self.http.get(start, headers=unauth.headers())
            text = r.text or ""
        except Exception:
            text = ""

        links = re.findall(r"href=[\"']([^\"'#>\s]+)[\"']", text, flags=re.IGNORECASE)
        login_urls = sorted({urljoin(start, u) for u in links if self.LOGIN_RE.search(u)})
        register_urls = sorted({urljoin(start, u) for u in links if self.REGISTER_RE.search(u)})
        reset_urls = sorted({urljoin(start, u) for u in links if self.RESET_RE.search(u)})
        oauth_urls = sorted({urljoin(start, u) for u in links if self.OAUTH_RE.search(u)} | {
            urljoin(start, "/.well-known/openid-configuration"),
            urljoin(start, "/.well-known/oauth-authorization-server"),
        })

        # Probe and persist lightweight
        for group, urls in ("auth_login", login_urls), ("auth_registration", register_urls), ("auth_password_reset", reset_urls), ("auth_oauth_endpoint", oauth_urls):
            for u in urls:
                try:
                    resp = await self.http.get(u, headers=unauth.headers())
                except Exception:
                    continue
                ctype = resp.headers.get("content-type", "")
                body_bytes = resp.content if (resp.status_code < 400 and ctype.lower().startswith("text/")) else b""
                # find target id by URL
                self.db.save_page(self.db.ensure_target(base_url), u, resp.status_code, ctype, body_bytes)
                if resp.status_code in (200, 302, 401, 403):
                    self.db.add_finding(self.db.ensure_target(base_url), group, u, evidence="autonomous-auth", score=0.55)

        # Session token style
        session_token_hint: Optional[str] = None
        try:
            home = await self.http.get(start, headers=unauth.headers())
            set_cookie = (home.headers.get("set-cookie") or "").lower()
            if any(t in set_cookie for t in ("session", "sid", "token", "jwt", "auth")):
                session_token_hint = "cookie"
            if (home.headers.get("www-authenticate") or "").lower().find("bearer") >= 0:
                session_token_hint = session_token_hint or "bearer"
        except Exception:
            pass
        if auth and auth.auth_bearer:
            session_token_hint = "bearer"
        if auth and auth.cookie:
            session_token_hint = session_token_hint or "cookie"

        # Role impact mapping on a few common paths
        role_map: Dict[str, Dict[str, int]] = {}
        candidates = ["/admin", "/dashboard", "/api/", "/settings"]
        for path in candidates:
            url = start.rstrip('/') + path
            try:
                st_un = (await self.http.get(url, headers=unauth.headers())).status_code
            except Exception:
                st_un = 0
            st_auth = 0
            if auth:
                try:
                    st_auth = (await self.http.get(url, headers=auth.headers())).status_code
                except Exception:
                    st_auth = 0
            role_map[path] = {"unauth": st_un, "auth": st_auth}

        # Framework hinting based on minimal signals already captured in pages
        framework_hint = None
        try:
            if "wordpress" in (text[:2000] or "").lower():
                framework_hint = "wordpress"
        except Exception:
            pass

        return AuthDiscoveryResult(
            login_urls=login_urls,
            register_urls=register_urls,
            reset_urls=reset_urls,
            oauth_urls=oauth_urls,
            session_token_hint=session_token_hint,
            role_map=role_map,
            framework_hint=framework_hint,
        )


class CredentialInferenceEngine:
    """Generate zero-config test identities heuristically.

    Non-intrusive: only suggests likely usernames; does not brute-force.
    """

    USERNAME_PATTERNS = [
        "admin", "administrator", "test", "tester", "dev", "qa",
    ]

    def __init__(self, settings: Settings, db: Storage):
        self.s = settings
        self.db = db

    def infer_usernames(self, base_url: str) -> List[str]:
        # Extract hinted usernames from stored pages (errors, forms)
        hints: List[str] = []
        for _, url, status, ctype, body in self._iter_pages(base_url):
            if status >= 400 or (ctype or "").lower().startswith("text/"):
                text = (body or b"").decode(errors="ignore")
                hints.extend(re.findall(r"(?:user(?:name)?|email)\W+([a-zA-Z0-9._%+-]{3,32})", text, flags=re.IGNORECASE))
        # add common patterns
        candidates = list(dict.fromkeys([*hints, *self.USERNAME_PATTERNS]))
        return candidates[:10]

    def fabricate_identities(self, usernames: List[str]) -> List[Identity]:
        out: List[Identity] = []
        for name in usernames[:3]:
            out.append(Identity(name=f"guess-{name}", base_headers={"X-BH-Guess": name}))
        return out

    def _iter_pages(self, base_url: str):
        with self.db.conn() as c:
            cur = c.execute(
                "SELECT target_id, url, status, content_type, body FROM pages WHERE url LIKE ? ORDER BY id DESC",
                (f"{base_url}%",),
            )
            for row in cur:
                yield row

