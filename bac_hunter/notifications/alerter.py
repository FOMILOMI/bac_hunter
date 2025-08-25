from __future__ import annotations
import json
import logging
from typing import Optional
import httpx

log = logging.getLogger("notify.alerter")


class AlertManager:
    """Simple webhook-based alerter for high-severity findings."""

    def __init__(self, generic_webhook: Optional[str] = None, slack_webhook: Optional[str] = None, discord_webhook: Optional[str] = None):
        self.generic = generic_webhook
        self.slack = slack_webhook
        self.discord = discord_webhook

    async def send(self, title: str, text: str, severity: float, url: Optional[str] = None):
        payload = {
            "title": title,
            "text": text,
            "severity": severity,
            "url": url,
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            if self.generic:
                try:
                    await client.post(self.generic, json=payload)
                except Exception as e:
                    log.debug("generic webhook failed: %s", e)
            if self.slack:
                try:
                    await client.post(self.slack, json={"text": f"[{severity:.2f}] {title} — {text} {url or ''}"})
                except Exception as e:
                    log.debug("slack webhook failed: %s", e)
            if self.discord:
                try:
                    await client.post(self.discord, json={"content": f"[{severity:.2f}] {title} — {text} {url or ''}"})
                except Exception as e:
                    log.debug("discord webhook failed: %s", e)

