from __future__ import annotations
import logging
from typing import Optional

log = logging.getLogger("safety.cdn")


class CDNDetector:
    CDN_INDICATORS = {
        'cloudflare': ['cf-ray', 'cf-cache-status', '__cfduid'],
        'fastly': ['fastly-debug-digest', 'x-served-by'],
        'cloudfront': ['x-amz-cf-id', 'x-amz-cf-pop'],
        'akamai': ['akamai-ghost-ip', 'x-akamai-'],
        'maxcdn': ['x-cache', 'x-edge-'],
        'keycdn': ['x-edge-location', 'x-cache'],
    }

    def detect_cdn(self, response_headers: dict) -> Optional[str]:
        headers_lower = {k.lower(): v.lower() for k, v in response_headers.items()}
        for cdn_name, indicators in self.CDN_INDICATORS.items():
            for indicator in indicators:
                if any(indicator in header for header in headers_lower.keys()):
                    log.info(f"Detected {cdn_name} CDN")
                    return cdn_name
        server = headers_lower.get('server', '')
        if 'cloudflare' in server:
            return 'cloudflare'
        elif 'fastly' in server:
            return 'fastly'
        return None

    def should_throttle_more(self, cdn_type: Optional[str]) -> bool:
        if not cdn_type:
            return False
        aggressive_cdns = ['cloudflare', 'akamai']
        return cdn_type in aggressive_cdns

