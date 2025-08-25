from __future__ import annotations
import logging
import re
from typing import Dict, Optional, Tuple

log = logging.getLogger("safety.waf")


class WAFDetector:
    WAF_SIGNATURES = {
        'cloudflare': [r'cf-ray', r'cloudflare', r'__cfduid', r'cf-cache-status'],
        'akamai': [r'akamai-ghost', r'x-akamai', r'aka-', r'reference #\d+\.\w+'],
        'aws_waf': [r'x-amzn-', r'awselb', r'x-amz-cf-id'],
        'incapsula': [r'incap_ses', r'visid_incap', r'incapsula'],
        'sucuri': [r'x-sucuri', r'sucuri', r'cloudproxy'],
        'barracuda': [r'barra', r'barracuda'],
        'f5_bigip': [r'f5-', r'bigip', r'x-waf-event-info'],
        'imperva': [r'imperva', r'x-iinfo'],
    }

    BLOCK_PATTERNS = [
        r'access denied',
        r'blocked by security policy',
        r'suspicious activity',
        r'request has been blocked',
        r'security violation',
        r'forbidden.*request',
        r'waf.*blocked',
        r'firewall.*detected'
    ]

    def __init__(self):
        self.detected_wafs: Dict[str, str] = {}
        self.block_count = 0
        self.last_block_time = 0

    def analyze_response(self, url: str, status: int, headers: Dict[str, str], body: str = "") -> Optional[Tuple[str, float]]:
        import time
        waf_detected = None
        danger_level = 0.0
        headers_lower = {k.lower(): v.lower() for k, v in headers.items()}
        for waf_name, patterns in self.WAF_SIGNATURES.items():
            for pattern in patterns:
                for header_name, header_value in headers_lower.items():
                    if re.search(pattern, header_name + " " + header_value, re.IGNORECASE):
                        waf_detected = waf_name
                        danger_level = max(danger_level, 0.3)
                        break
                if waf_detected:
                    break
            if waf_detected:
                break
        if status in [403, 406, 429, 503]:
            danger_level = max(danger_level, 0.6)
            self.block_count += 1
            self.last_block_time = time.time()
            if body:
                for pattern in self.BLOCK_PATTERNS:
                    if re.search(pattern, body, re.IGNORECASE):
                        danger_level = max(danger_level, 0.9)
                        log.warning(f"WAF block pattern detected in response: {pattern}")
                        break
        if self.block_count > 3:
            danger_level = min(1.0, danger_level + 0.2)
        if waf_detected or danger_level > 0.5:
            self.detected_wafs[url] = waf_detected or "unknown"
            log.info(f"WAF detected: {waf_detected} (danger: {danger_level:.2f}) for {url}")
            return waf_detected or "unknown", danger_level
        return None

    def should_throttle_heavily(self) -> bool:
        import time
        recent_block = (time.time() - self.last_block_time) < 300
        return self.block_count > 2 or recent_block

    def get_recommended_delay(self) -> float:
        if self.block_count == 0:
            return 1.0
        elif self.block_count <= 2:
            return 2.5
        elif self.block_count <= 5:
            return 5.0
        else:
            return 10.0

