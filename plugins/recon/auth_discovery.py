from __future__ import annotations
import logging
import re
from typing import List, Set
from urllib.parse import urljoin

from ...storage import Storage
from ...http_client import HttpClient
from ...config import Settings
from ..base import Plugin


log = logging.getLogger("recon.auth")


LOGIN_HINT_RE = re.compile(r"\b(login|signin|sign-in|auth|account/login|user/login)\b", re.IGNORECASE)
REGISTER_HINT_RE = re.compile(r"\b(register|signup|sign-up|create[-_ ]?account)\b", re.IGNORECASE)
RESET_HINT_RE = re.compile(r"\b(reset|forgot[-_ ]?password|recover)\b", re.IGNORECASE)
OAUTH_HINT_RE = re.compile(r"\b(oauth|openid|sso|saml)\b", re.IGNORECASE)

# Extract form actions that likely relate to authentication
FORM_ACTION_RE = re.compile(r"<form[^>]*action=[\"']([^\"'>\s]+)[\"'][^>]*>([\s\S]*?)</form>", re.IGNORECASE)
PASSWORD_INPUT_RE = re.compile(r"<input[^>]*type=[\"']password[\"']", re.IGNORECASE)

# Well-known discovery endpoints
WELL_KNOWN = [
    "/.well-known/openid-configuration",
    "/.well-known/oauth-authorization-server",
]


class AuthDiscoveryRecon(Plugin):
    name = "auth-discovery"
    category = "recon"

    async def run(self, base_url: str, target_id: int) -> List[str]:
        collected: Set[str] = set()
        start_url = base_url if base_url.endswith("/") else base_url + "/"

        # 1) Fetch homepage and heuristically extract auth-related links/forms
        try:
            r = await self.http.get(start_url)
            self.db.save_page(target_id, start_url, r.status_code, r.headers.get("content-type"), r.content)
            text = r.text or ""
        except Exception as e:
            log.debug("homepage fetch failed: %s", e)
            text = ""

        # Anchor/URL pattern hints
        for m in re.finditer(r"href=[\"']([^\"'#>\s]+)[\"'][^>]*>([^<]{0,80})", text, re.IGNORECASE):
            href, label = m.group(1), m.group(2)
            label = label or ""
            if LOGIN_HINT_RE.search(href) or LOGIN_HINT_RE.search(label):
                collected.add(urljoin(base_url, href))
            elif REGISTER_HINT_RE.search(href) or REGISTER_HINT_RE.search(label):
                collected.add(urljoin(base_url, href))
            elif RESET_HINT_RE.search(href) or RESET_HINT_RE.search(label):
                collected.add(urljoin(base_url, href))
            elif OAUTH_HINT_RE.search(href) or OAUTH_HINT_RE.search(label):
                collected.add(urljoin(base_url, href))

        # Form action detection where a password input exists
        for m in FORM_ACTION_RE.finditer(text):
            action, inner = m.group(1), m.group(2) or ""
            if PASSWORD_INPUT_RE.search(inner):
                collected.add(urljoin(base_url, action))

        # Client-side storage token hints (basic scan)
        try:
            if text:
                if re.search(r"localStorage\.(get|set)Item\(['\"](token|jwt|auth|session)['\"]", text, re.IGNORECASE):
                    self.db.add_auth_hint(target_id, kind="jwt_client_storage", url=start_url, evidence="localStorage token pattern", score=0.4)
                if re.search(r"sessionStorage\.(get|set)Item\(['\"](token|jwt|auth|session)['\"]", text, re.IGNORECASE):
                    self.db.add_auth_hint(target_id, kind="jwt_client_storage", url=start_url, evidence="sessionStorage token pattern", score=0.35)
        except Exception:
            pass

        # Well-known endpoints probing
        for path in WELL_KNOWN:
            collected.add(urljoin(base_url, path))

        # 2) Probe collected candidates conservatively and persist hints
        confirmed: Set[str] = set()
        for url in sorted(collected):
            try:
                resp = await self.http.get(url)
            except Exception:
                continue
            ctype = resp.headers.get("content-type", "")
            body_bytes = resp.content if (resp.status_code < 400 and ctype.lower().startswith("text/")) else b""
            self.db.save_page(target_id, url, resp.status_code, ctype, body_bytes)
            if resp.status_code in (200, 302, 401, 403):
                confirmed.add(url)

        # 3) Record findings with basic categorization
        for u in sorted(confirmed):
            lt = u.lower()
            if any(x in lt for x in ("openid-configuration", "oauth-authorization-server", "/oauth", "/sso", "/auth/")):
                self.db.add_finding(target_id, "auth_oauth_endpoint", u, evidence="auth-discovery", score=0.7)
                self.db.add_auth_hint(target_id, kind="auth_oauth", url=u, evidence="discovered oauth/oidc", score=0.7)
            elif any(x in lt for x in ("reset", "forgot")):
                self.db.add_finding(target_id, "auth_password_reset", u, evidence="auth-discovery", score=0.5)
                self.db.add_auth_hint(target_id, kind="auth_reset", url=u, evidence="password reset path", score=0.5)
            elif any(x in lt for x in ("register", "signup")):
                self.db.add_finding(target_id, "auth_registration", u, evidence="auth-discovery", score=0.45)
                self.db.add_auth_hint(target_id, kind="auth_register", url=u, evidence="registration path", score=0.45)
            else:
                self.db.add_finding(target_id, "auth_login", u, evidence="auth-discovery", score=0.6)
                self.db.add_auth_hint(target_id, kind="auth_login", url=u, evidence="login-like path", score=0.6)

        log.info("%s -> %d auth endpoints", self.name, len(confirmed))
        return sorted(confirmed)

