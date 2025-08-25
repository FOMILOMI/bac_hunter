from __future__ import annotations
import logging
from typing import List
from urllib.parse import urlparse
import re

log = logging.getLogger("safety.scope")


class ScopeGuard:
    def __init__(self, allowed_domains: List[str] = None, blocked_patterns: List[str] = None):
        self.allowed_domains = set(allowed_domains or [])
        self.blocked_patterns = [re.compile(p) for p in (blocked_patterns or [])]
        self.auto_blocked = {
            'cdnjs.cloudflare.com', 'cdn.jsdelivr.net', 'unpkg.com',
            'googleapis.com', 'gstatic.com', 'facebook.com', 'twitter.com',
            'linkedin.com', 'instagram.com', 'youtube.com', 'youtu.be',
            'google-analytics.com', 'googletagmanager.com', 'doubleclick.net'
        }

    def is_in_scope(self, url: str) -> bool:
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc
            if ':' in domain:
                domain = domain.split(':')[0]
            if domain in self.auto_blocked:
                log.debug(f"Blocked CDN domain: {domain}")
                return False
            if self.allowed_domains:
                allowed = any(
                    domain == allowed or domain.endswith(f'.{allowed}')
                    for allowed in self.allowed_domains
                )
                if not allowed:
                    log.debug(f"Domain not in allowed list: {domain}")
                    return False
            for pattern in self.blocked_patterns:
                if pattern.search(url):
                    log.debug(f"URL matches blocked pattern: {url}")
                    return False
            return True
        except Exception as e:
            log.warning(f"Error checking scope for {url}: {e}")
            return False

